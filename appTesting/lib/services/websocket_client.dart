import 'dart:async';
import 'dart:convert';

import 'package:web_socket_channel/web_socket_channel.dart';

import 'api_client.dart';
import 'sign_analysis_service.dart';

/// The result of sending one completed utterance over the tracking socket.
///
/// The current backend returns an acknowledgement after [utterance_end]. A
/// future classifier can additionally send an `utterance_result` message;
/// [analysis] will contain that parsed result when it is present.
class WebSocketUtteranceReceipt {
  const WebSocketUtteranceReceipt({
    required this.sessionId,
    required this.utteranceId,
    required this.chunksReceived,
    required this.framesReceived,
    this.analysis,
  });

  final String sessionId;
  final String utteranceId;
  final int chunksReceived;
  final int framesReceived;
  final SignAnalysisResult? analysis;
}

/// Sends the frontend's LandmarkFrame utterance handoff through WebSocket.
///
/// Protocol:
/// `ready` → `start` → `utterance_start` → one or more `chunk` messages
/// → `utterance_end`.
///
/// A new socket is used for each completed utterance. This keeps one broken
/// connection from stopping the camera and makes reconnecting after a page
/// reload predictable.
class SignTrackingWebSocketClient {
  SignTrackingWebSocketClient({required this.uri, this.chunkSize = 30})
    : assert(chunkSize > 0);

  final Uri uri;
  final int chunkSize;
  WebSocketChannel? _activeChannel;

  Future<WebSocketUtteranceReceipt> sendUtterance(
    SignSequencePayload payload,
  ) async {
    if (payload.frames.isEmpty) {
      throw StateError('Cannot send an utterance with no LandmarkFrames.');
    }

    final channel = WebSocketChannel.connect(uri);
    _activeChannel = channel;
    final messages = StreamIterator<dynamic>(channel.stream);
    final utteranceId = payload.sequenceId;

    try {
      await channel.ready;
      await _expectType(messages, 'ready');

      channel.sink.add(
        jsonEncode(<String, dynamic>{
          'type': 'start',
          'session_id': payload.sessionId,
          'language': payload.language,
        }),
      );
      await _expectType(messages, 'started');

      channel.sink.add(
        jsonEncode(<String, dynamic>{
          'type': 'utterance_start',
          'utterance_id': utteranceId,
          'sequence_id': payload.sequenceId,
          'language': payload.language,
          'lexicon_version': payload.lexiconVersion,
          'started_at': payload.startedAt.toUtc().toIso8601String(),
        }),
      );
      await _expectType(messages, 'utterance_started');

      var chunkNumber = 0;
      for (
        var offset = 0;
        offset < payload.frames.length;
        offset += chunkSize
      ) {
        final end = offset + chunkSize < payload.frames.length
            ? offset + chunkSize
            : payload.frames.length;
        final frames = payload.frames.sublist(offset, end);
        final chunkId = '$utteranceId-chunk-${++chunkNumber}';

        channel.sink.add(
          jsonEncode(<String, dynamic>{
            'type': 'chunk',
            'session_id': payload.sessionId,
            'utterance_id': utteranceId,
            'chunk_id': chunkId,
            'sequence_id': payload.sequenceId,
            'language': payload.language,
            'lexicon_version': payload.lexiconVersion,
            'started_at': frames.first.timestamp.toUtc().toIso8601String(),
            'ended_at': frames.last.timestamp.toUtc().toIso8601String(),
            'frame_count': frames.length,
            'frames': frames.map((frame) => frame.toJson()).toList(),
          }),
        );
        await _expectType(messages, 'chunk_ack');
      }

      channel.sink.add(
        jsonEncode(<String, dynamic>{
          'type': 'utterance_end',
          'utterance_id': utteranceId,
        }),
      );

      SignAnalysisResult? analysis;
      Map<String, dynamic>? ended;
      while (ended == null) {
        final message = await _nextJson(messages);
        final type = message['type'];
        if (type == 'error') {
          throw StateError(_serverError(message));
        }
        if (type == 'utterance_result') {
          analysis = SignAnalysisResult.fromJson(message);
          // A result is a valid final response even if the server does not
          // send the optional `utterance_ended` acknowledgement afterward.
          break;
        }
        if (type == 'utterance_ended') {
          ended = message;
        }
      }

      final response = ended;
      return WebSocketUtteranceReceipt(
        sessionId: _stringValue(response?['session_id']) ?? payload.sessionId,
        utteranceId: _stringValue(response?['utterance_id']) ?? utteranceId,
        chunksReceived: _intValue(response?['chunks_received']) ?? chunkNumber,
        framesReceived:
            _intValue(response?['frames_received']) ?? payload.frames.length,
        analysis: analysis,
      );
    } finally {
      await messages.cancel();
      await _closeChannel(channel);
      if (identical(_activeChannel, channel)) {
        _activeChannel = null;
      }
    }
  }

  Future<void> _expectType(
    StreamIterator<dynamic> messages,
    String expectedType,
  ) async {
    final message = await _nextJson(messages);
    final type = message['type'];
    if (type == 'error') {
      throw StateError(_serverError(message));
    }
    if (type != expectedType) {
      throw StateError(
        'WebSocket expected "$expectedType" but received "${type ?? 'unknown'}".',
      );
    }
  }

  Future<Map<String, dynamic>> _nextJson(
    StreamIterator<dynamic> messages,
  ) async {
    if (!await messages.moveNext()) {
      throw StateError('The tracking WebSocket closed before replying.');
    }
    final value = messages.current;
    final text = value is String
        ? value
        : value is List<int>
        ? utf8.decode(value)
        : value.toString();
    final decoded = jsonDecode(text);
    if (decoded is! Map) {
      throw StateError('The tracking WebSocket returned non-object JSON.');
    }
    return Map<String, dynamic>.from(decoded);
  }

  String _serverError(Map<String, dynamic> message) {
    final detail = message['detail'] ?? message['error'] ?? 'unknown error';
    return 'Tracking WebSocket error: $detail';
  }

  String? _stringValue(Object? value) => value is String ? value : null;

  int? _intValue(Object? value) => value is num ? value.toInt() : null;

  Future<void> _closeChannel(WebSocketChannel channel) async {
    try {
      await channel.sink.close();
    } catch (_) {
      // The socket may already have been closed by the browser or server.
    }
  }

  Future<void> close() async {
    final channel = _activeChannel;
    if (channel != null) {
      await _closeChannel(channel);
      _activeChannel = null;
    }
  }
}
