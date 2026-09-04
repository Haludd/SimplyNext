import 'dart:convert';

import 'package:http/http.dart' as http;

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
