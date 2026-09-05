import 'dart:math' as math;

import 'face_tracking_models.dart';

const handLandmarkEdges = <List<int>>[
  <int>[0, 1],
  <int>[1, 2],
  <int>[2, 3],
  <int>[3, 4],
  <int>[0, 5],
  <int>[5, 6],
  <int>[6, 7],
  <int>[7, 8],
  <int>[5, 9],
  <int>[9, 10],
  <int>[10, 11],
  <int>[11, 12],
  <int>[9, 13],
  <int>[13, 14],
  <int>[14, 15],
  <int>[15, 16],
  <int>[13, 17],
  <int>[17, 18],
  <int>[18, 19],
  <int>[19, 20],
  <int>[0, 17],
];

enum Handedness { left, right, unknown }

Handedness handednessFromString(String? value) {
  switch (value?.toLowerCase()) {
    case 'left':
      return Handedness.left;
    case 'right':
      return Handedness.right;
    default:
      return Handedness.unknown;
  }
}

String handednessToString(Handedness value) => switch (value) {
  Handedness.left => 'left',
  Handedness.right => 'right',
  Handedness.unknown => 'unknown',
};

class HandLandmark {
  const HandLandmark({
    required this.x,
    required this.y,
    required this.z,
    this.worldX,
    this.worldY,
    this.worldZ,
    this.visibility = 1,
  });

  final double x;
  final double y;
  final double z;
  final double? worldX;
  final double? worldY;
  final double? worldZ;
  final double visibility;

  Map<String, dynamic> toJson() => <String, dynamic>{
    'x': x,
    'y': y,
    'z': z,
    if (worldX != null) 'world_x': worldX,
    if (worldY != null) 'world_y': worldY,
    if (worldZ != null) 'world_z': worldZ,
    'visibility': visibility,
  };

  factory HandLandmark.fromJson(Map<String, dynamic> json) => HandLandmark(
    x: (json['x'] as num).toDouble(),
    y: (json['y'] as num).toDouble(),
    z: (json['z'] as num?)?.toDouble() ?? 0,
    worldX: (json['world_x'] as num?)?.toDouble(),
    worldY: (json['world_y'] as num?)?.toDouble(),
    worldZ: (json['world_z'] as num?)?.toDouble(),
    visibility: (json['visibility'] as num?)?.toDouble() ?? 1,
  );
}

class TrackedHand {
  const TrackedHand({
    required this.handedness,
    required this.confidence,
    required this.landmarks,
    this.boundingBox = const <double>[],
  });

  final Handedness handedness;
  final double confidence;
  final List<HandLandmark> landmarks;
  final List<double> boundingBox;

  HandLandmark? get wrist => landmarks.isEmpty ? null : landmarks.first;

  double get openness {
    if (landmarks.length < 21) return 0;
    final wrist = landmarks[0];
    final tips = <int>[4, 8, 12, 16, 20];
    final mcps = <int>[2, 5, 9, 13, 17];
    final extended = <bool>[];
    for (var index = 0; index < tips.length; index += 1) {
      final tip = landmarks[tips[index]];
      final mcp = landmarks[mcps[index]];
      final tipDistance = _distance(tip, wrist);
      final mcpDistance = _distance(mcp, wrist);
      extended.add(tipDistance > mcpDistance * 1.18);
    }
    return extended.where((value) => value).length / extended.length;
  }

  Map<String, dynamic> toJson() => <String, dynamic>{
    'handedness': handednessToString(handedness),
    'confidence': confidence,
    'bounding_box': boundingBox,
    'landmarks': landmarks.map((landmark) => landmark.toJson()).toList(),
  };

  factory TrackedHand.fromJson(Map<String, dynamic> json) => TrackedHand(
    handedness: handednessFromString(json['handedness'] as String?),
    confidence: (json['confidence'] as num?)?.toDouble() ?? 0,
    boundingBox: (json['bounding_box'] as List<dynamic>? ?? <dynamic>[])
        .map((value) => (value as num).toDouble())
        .toList(),
    landmarks: (json['landmarks'] as List<dynamic>? ?? <dynamic>[])
        .map((value) => HandLandmark.fromJson(value as Map<String, dynamic>))
        .toList(),
  );
}

class HandMotionFeatures {
  const HandMotionFeatures({
    this.averageSpeed = 0,
    this.averageAcceleration = 0,
    this.averageOpenness = 0,
    this.direction = 'still',
    this.dominantHand = Handedness.unknown,
  });

  final double averageSpeed;
  final double averageAcceleration;
  final double averageOpenness;
  final String direction;
  final Handedness dominantHand;

  Map<String, dynamic> toJson() => <String, dynamic>{
    'average_speed': averageSpeed,
    'average_acceleration': averageAcceleration,
    'average_openness': averageOpenness,
    'direction': direction,
    'dominant_hand': handednessToString(dominantHand),
  };
}

class HandTrackingFrame {
  const HandTrackingFrame({
    required this.timestamp,
    required this.hands,
    this.face,
    this.leftShoulder,
    this.rightShoulder,
    this.processingConfidence = 0,
  });

  final DateTime timestamp;
  final List<TrackedHand> hands;
  final FaceExpressionFeatures? face;
  final HandLandmark? leftShoulder;
  final HandLandmark? rightShoulder;
  final double processingConfidence;

  Map<String, dynamic> toJson() => <String, dynamic>{
    'timestamp': timestamp.toUtc().toIso8601String(),
    'processing_confidence': processingConfidence,
    'hands': hands.map((hand) => hand.toJson()).toList(),
    'face': face?.toJson(),
    'left_shoulder': leftShoulder?.toJson(),
    'right_shoulder': rightShoulder?.toJson(),
  };

  factory HandTrackingFrame.fromJson(Map<String, dynamic> json) =>
      HandTrackingFrame(
        timestamp: DateTime.fromMillisecondsSinceEpoch(
          (json['timestamp_ms'] as num?)?.toInt() ??
              DateTime.now().millisecondsSinceEpoch,
        ),
        processingConfidence:
            (json['processing_confidence'] as num?)?.toDouble() ?? 0,
        face: _faceFromJson(json['face']),
        leftShoulder: _landmarkFromJson(json['left_shoulder']),
        rightShoulder: _landmarkFromJson(json['right_shoulder']),
        hands: (json['hands'] as List<dynamic>? ?? <dynamic>[])
            .map((value) => TrackedHand.fromJson(value as Map<String, dynamic>))
            .toList(),
      );
}

HandLandmark? _landmarkFromJson(Object? value) =>
    value is Map<String, dynamic> ? HandLandmark.fromJson(value) : null;

FaceExpressionFeatures? _faceFromJson(Object? value) =>
    value is Map<String, dynamic>
    ? FaceExpressionFeatures.fromJson(value)
    : null;

double _distance(HandLandmark a, HandLandmark b) =>
    math.sqrt(math.pow(a.x - b.x, 2) + math.pow(a.y - b.y, 2));
