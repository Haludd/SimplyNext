import 'dart:async';
import 'dart:convert';

import 'package:web_socket_channel/web_socket_channel.dart';

import '../contracts/gloss_lattice.dart';

/// Small testable text-channel boundary used by the lattice sender.
///
/// Production code can wrap an already connected and authenticated
/// [WebSocketChannel]. Tests can supply an in-memory implementation without
/// opening a network connection.
abstract interface class GlossLatticeTextChannel {
  Future<void> get ready;
  Stream<dynamic> get stream;
  void sendText(String message);
  Future<void> close();
}

final class WebSocketGlossLatticeTextChannel
    implements GlossLatticeTextChannel {
  WebSocketGlossLatticeTextChannel(this._channel);

  final WebSocketChannel _channel;

  @override
  Future<void> get ready => _channel.ready;

  @override
  Stream<dynamic> get stream => _channel.stream;

  @override
  void sendText(String message) => _channel.sink.add(message);

  @override
  Future<void> close() async {
    await _channel.sink.close();
  }
}

/// One backend acknowledgement followed by its terminal result or repair.
final class GlossLatticeSubmissionReceipt {
  GlossLatticeSubmissionReceipt({
    required Map<String, dynamic> acknowledgement,
    required Map<String, dynamic> terminalEvent,
  }) : acknowledgement = Map<String, dynamic>.unmodifiable(acknowledgement),
       terminalEvent = Map<String, dynamic>.unmodifiable(terminalEvent);

  final Map<String, dynamic> acknowledgement;
  final Map<String, dynamic> terminalEvent;

  int get latticeSeq => acknowledgement['lattice_seq'] as int;
  String get utteranceId => acknowledgement['utterance_id'] as String;
  bool get wasCached => acknowledgement['disposition'] == 'cached';
  bool get requiresRepair => terminalEvent['type'] == 'lattice_repair_required';
}

/// A typed failure reported by the lattice WebSocket or its local protocol
/// guard.
final class GlossLatticeWebSocketException implements Exception {
  const GlossLatticeWebSocketException({
    required this.code,
    required this.message,
    this.retryable = false,
  });

  final String code;
  final String message;
  final bool retryable;

  @override
  String toString() =>
      'GlossLatticeWebSocketException($code, retryable: $retryable): '
      '$message';
}

/// Sends a completed [GlossLattice] without changing its wire representation.
///
/// The channel must already be connected to the negotiated lattice endpoint
/// and authenticated for [sessionId]. `GlossLatticeFrontendSession` composes
/// session creation and this sender; direct construction remains useful for
/// tests and for applications that own authentication elsewhere.
final class GlossLatticeWebSocketClient {
  factory GlossLatticeWebSocketClient({
    required GlossLatticeTextChannel channel,
    required String sessionId,
    Duration responseTimeout = const Duration(seconds: 60),
  }) {
    if (!GlossLatticeContract.isValidUuid(sessionId)) {
      throw const GlossLatticeValidationException(
        'session_id must be a canonical UUID string',
      );
    }
    if (responseTimeout <= Duration.zero) {
      throw ArgumentError.value(
        responseTimeout,
        'responseTimeout',
        'must be greater than zero',
      );
    }
    return GlossLatticeWebSocketClient._(channel, sessionId, responseTimeout);
  }

  GlossLatticeWebSocketClient._(
    this._channel,
    this.sessionId,
    this.responseTimeout,
  );

  factory GlossLatticeWebSocketClient.fromWebSocketChannel({
    required WebSocketChannel channel,
    required String sessionId,
    Duration responseTimeout = const Duration(seconds: 60),
  }) => GlossLatticeWebSocketClient(
    channel: WebSocketGlossLatticeTextChannel(channel),
    sessionId: sessionId,
    responseTimeout: responseTimeout,
  );

  final String sessionId;
  final Duration responseTimeout;
  final GlossLatticeTextChannel _channel;
  StreamIterator<dynamic>? _messages;

  bool _closed = false;
  bool _submissionInProgress = false;

  bool get isClosed => _closed;

  /// Sends exactly one compact JSON text message, then waits for the matching
  /// acknowledgement and terminal result.
  ///
  /// Calls are intentionally sequential because one socket is an ordered
  /// session stream. Exact retransmissions remain allowed; the backend owns
  /// `(session_id, lattice_seq)` idempotency and returns `disposition=cached`.
  Future<GlossLatticeSubmissionReceipt> send(GlossLattice lattice) async {
    if (_closed) {
      throw StateError('The GlossLattice WebSocket client is closed.');
    }
    if (_submissionInProgress) {
      throw StateError(
        'Only one GlossLattice submission may be in progress per socket.',
      );
    }
    if (lattice.sessionId != sessionId) {
      throw GlossLatticeWebSocketException(
        code: 'session_mismatch',
        message:
            'The lattice session_id does not match the authenticated channel.',
      );
    }

    _submissionInProgress = true;
    try {
      await _channel.ready;
      final wireJson = lattice.toWireJson();
      _channel.sendText(wireJson);

      Map<String, dynamic>? acknowledgement;
      while (true) {
        final event = await _nextEvent();
        final type = event['type'];
        if (type is! String) {
          throw const GlossLatticeWebSocketException(
            code: 'invalid_response',
            message: 'The backend event is missing a string type.',
          );
        }
        _validateOptionalEnvelope(event);

        switch (type) {
          case 'activity':
          case 'pong':
            // Informational events do not alter or complete the submission.
            continue;
          case 'error':
            throw _serverException(event);
          case 'lattice_ack':
            _validateCorrelation(event, lattice, eventName: 'lattice_ack');
            if (acknowledgement != null) {
              throw const GlossLatticeWebSocketException(
                code: 'invalid_response',
                message: 'The backend sent more than one lattice_ack.',
              );
            }
            final disposition = event['disposition'];
            if (disposition != 'accepted' && disposition != 'cached') {
              throw const GlossLatticeWebSocketException(
                code: 'invalid_response',
                message: 'lattice_ack disposition must be accepted or cached.',
              );
            }
            acknowledgement = event;
            continue;
          case 'lattice_result':
          case 'lattice_repair_required':
            if (acknowledgement == null) {
              throw GlossLatticeWebSocketException(
                code: 'invalid_response',
                message: '$type arrived before lattice_ack.',
              );
            }
            _validateCorrelation(event, lattice, eventName: type);
            return GlossLatticeSubmissionReceipt(
              acknowledgement: acknowledgement,
              terminalEvent: event,
            );
          default:
            throw GlossLatticeWebSocketException(
              code: 'invalid_response',
              message: 'Unexpected backend event type "$type".',
            );
        }
      }
    } finally {
      _submissionInProgress = false;
    }
  }

  Future<Map<String, dynamic>> _nextEvent() async {
    final messages = _messages ??= StreamIterator<dynamic>(_channel.stream);
    late bool hasMessage;
    try {
      hasMessage = await messages.moveNext().timeout(responseTimeout);
    } on TimeoutException {
      throw const GlossLatticeWebSocketException(
        code: 'response_timeout',
        message: 'The backend did not answer the lattice in time.',
        retryable: true,
      );
    } on Object {
      throw const GlossLatticeWebSocketException(
        code: 'connection_failed',
        message: 'The WebSocket failed while waiting for a backend event.',
        retryable: true,
      );
    }
    if (!hasMessage) {
      throw const GlossLatticeWebSocketException(
        code: 'connection_closed',
        message: 'The WebSocket closed before the lattice result arrived.',
        retryable: true,
      );
    }
    final value = messages.current;
    Object? decoded;
    try {
      if (value is String) {
        decoded = jsonDecode(value);
      } else if (value is List<int>) {
        decoded = jsonDecode(utf8.decode(value));
      } else if (value is Map) {
        decoded = value;
      } else {
        throw const FormatException('event is not text, bytes, or an object');
      }
    } on FormatException catch (error) {
      throw GlossLatticeWebSocketException(
        code: 'invalid_response',
        message: 'The backend returned invalid JSON: ${error.message}',
      );
    }
    if (decoded is! Map || decoded.keys.any((key) => key is! String)) {
      throw const GlossLatticeWebSocketException(
        code: 'invalid_response',
        message: 'The backend event must be a JSON object.',
      );
    }
    return Map<String, dynamic>.from(decoded);
  }

  void _validateCorrelation(
    Map<String, dynamic> event,
    GlossLattice lattice, {
    required String eventName,
  }) {
    if (event['lattice_seq'] is! int ||
        event['lattice_seq'] != lattice.latticeSeq ||
        event['utterance_id'] is! String ||
        event['utterance_id'] != lattice.utteranceId) {
      throw GlossLatticeWebSocketException(
        code: 'correlation_mismatch',
        message:
            '$eventName does not match lattice_seq and utterance_id of the '
            'submitted lattice.',
      );
    }
  }

  void _validateOptionalEnvelope(Map<String, dynamic> event) {
    if (event.containsKey('event_schema_version') &&
        event['event_schema_version'] != GlossLatticeContract.schemaVersion) {
      throw const GlossLatticeWebSocketException(
        code: 'invalid_response',
        message: 'The backend event_schema_version is unsupported.',
      );
    }
    if (event.containsKey('session_id') && event['session_id'] != sessionId) {
      throw const GlossLatticeWebSocketException(
        code: 'correlation_mismatch',
        message: 'The backend event session_id does not match this session.',
      );
    }
  }

  GlossLatticeWebSocketException _serverException(
    Map<String, dynamic> event,
  ) => GlossLatticeWebSocketException(
    code: event['code'] is String ? event['code'] as String : 'backend_error',
    message: event['message'] is String
        ? event['message'] as String
        : 'The backend rejected the lattice.',
    retryable: event['retryable'] is bool ? event['retryable'] as bool : false,
  );

  Future<void> close() async {
    if (_closed) return;
    _closed = true;
    // A synchronous test/platform channel may complete send() from inside its
    // own event callback. Yield before closing so the controller can finish
    // dispatching that event safely.
    await Future<void>.delayed(Duration.zero);
    final messages = _messages;
    if (messages == null) {
      await _channel.close();
      return;
    }
    // Start both operations before awaiting either. Some channels finish a
    // paused stream cancellation only while their sink is also closing.
    await Future.wait<void>(<Future<void>>[
      messages.cancel(),
      _channel.close(),
    ]);
  }
}
