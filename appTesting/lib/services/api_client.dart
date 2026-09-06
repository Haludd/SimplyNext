import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/tracking_models.dart';
import 'sign_analysis_service.dart';

// Legacy HTTP clients retained for compatibility with older tests and
// experiments. The live AppController uses websocket_client.dart instead.
class UtteranceApiClient {
  UtteranceApiClient({required this.baseUri, http.Client? client})
    : _client = client ?? http.Client();

  final Uri baseUri;
  final http.Client _client;

  Future<TranslationResult> translate(UtterancePayload payload) async {
    final response = await _client.post(
      baseUri.resolve('/v1/utterances'),
      headers: <String, String>{'content-type': 'application/json'},
      body: jsonEncode(payload.toJson()),
    );
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception('Translation API returned ${response.statusCode}.');
    }
    return TranslationResult.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  void close() => _client.close();
}

class UtterancePayload {
  const UtterancePayload({
    required this.sessionId,
    required this.utteranceId,
    required this.language,
    required this.startedAt,
    required this.endedAt,
    required this.hypotheses,
    required this.features,
  });

  final String sessionId;
  final String utteranceId;
  final String language;
  final DateTime startedAt;
  final DateTime endedAt;
  final List<GlossHypothesis> hypotheses;
  final Map<String, dynamic> features;

  Map<String, dynamic> toJson() => <String, dynamic>{
    'session_id': sessionId,
    'utterance_id': utteranceId,
    'language': language,
    'started_at': startedAt.toUtc().toIso8601String(),
    'ended_at': endedAt.toUtc().toIso8601String(),
    'hypotheses': hypotheses.map((item) => item.toJson()).toList(),
    'features': features,
  };
}

class GlossHypothesis {
  const GlossHypothesis({required this.gloss, required this.confidence});
  final String gloss;
  final double confidence;
  Map<String, dynamic> toJson() => <String, dynamic>{
    'gloss': gloss,
    'confidence': confidence,
  };
}

class TranslationResult {
  const TranslationResult({
    required this.utteranceId,
    required this.status,
    required this.caption,
    required this.ttsText,
    required this.glossTrace,
    required this.confidence,
  });

  final String utteranceId;
  final String status;
  final String? caption;
  final String? ttsText;
  final List<String> glossTrace;
  final double confidence;

  bool get needsRepair => status != 'confident' || caption == null;

  factory TranslationResult.fromJson(Map<String, dynamic> json) =>
      TranslationResult(
        utteranceId: json['utterance_id'] as String,
        status: json['status'] as String,
        caption: json['caption'] as String?,
        ttsText: json['tts_text'] as String?,
        glossTrace: (json['gloss_trace'] as List<dynamic>? ?? <dynamic>[])
            .cast<String>(),
        confidence: (json['confidence'] as num?)?.toDouble() ?? 0,
      );
}

class SignSequenceApiClient {
  SignSequenceApiClient({required this.baseUri, http.Client? client})
    : _client = client ?? http.Client();

  final Uri baseUri;
  final http.Client _client;

  Future<SignAnalysisResult> analyze(SignSequencePayload payload) async {
    final response = await _client.post(
      baseUri.resolve('/v1/sign-sequences/analyze'),
      headers: <String, String>{'content-type': 'application/json'},
      body: jsonEncode(payload.toJson()),
    );
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception('Sign analysis API returned ${response.statusCode}.');
    }
    return SignAnalysisResult.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  void close() => _client.close();
}

/// Offline stand-in for the future sign-analysis service.
///
/// It consumes the exact payload that the HTTP client will send later, but
/// classifies it with the local feature readout and never opens a network
/// connection. This keeps the capture → payload → result UI testable while
/// the backend is still being built.
class SimulatedSignSequenceApiClient {
  SimulatedSignSequenceApiClient({SignAnalysisService? analyzer})
    : _analyzer = analyzer ?? SignAnalysisService();

  final SignAnalysisService _analyzer;

  Future<SignAnalysisResult> analyze(SignSequencePayload payload) async {
    await Future<void>.delayed(const Duration(milliseconds: 450));
    final local = _analyzer.analyze(payload.frames);
    return SignAnalysisResult(
      status: local.status == 'no_signal' ? 'no_signal' : 'simulated',
      gestureLabel: local.gestureLabel,
      caption: local.status == 'no_signal'
          ? local.caption
          : 'Simulated ${payload.language} result · ${local.gestureLabel}.',
      confidence: local.confidence,
      glossTrace: local.glossTrace,
      detail: local.status == 'no_signal'
          ? local.detail
          : '${local.detail} · ${payload.frames.length} frames queued locally; no network request sent.',
    );
  }
}

/// The JSON-ready utterance model shared by the offline simulator and the
/// active WebSocket transport. The live app does not call the HTTP client
/// above; `SignTrackingWebSocketClient` sends this payload's frames in chunks.
class SignSequencePayload {
  const SignSequencePayload({
    required this.sessionId,
    required this.sequenceId,
    required this.language,
    required this.startedAt,
    required this.endedAt,
    required this.frames,
    required this.lexiconVersion,
  });

  final String sessionId;
  final String sequenceId;
  final String language;
  final DateTime startedAt;
  final DateTime endedAt;
  final List<LandmarkFrame> frames;
  final String lexiconVersion;

  Map<String, dynamic> toJson() => <String, dynamic>{
    'session_id': sessionId,
    'sequence_id': sequenceId,
    'language': language,
    'started_at': startedAt.toUtc().toIso8601String(),
    'ended_at': endedAt.toUtc().toIso8601String(),
    'frame_count': frames.length,
    'lexicon_version': lexiconVersion,
    'frames': frames.map((frame) => frame.toJson()).toList(),
  };
}
