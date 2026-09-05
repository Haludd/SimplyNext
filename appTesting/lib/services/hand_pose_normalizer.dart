import 'dart:math' as math;

import '../models/face_tracking_models.dart';
import '../models/hand_tracking_models.dart';
import '../models/hand_coordinate_analysis.dart';
import '../models/tracking_models.dart';

/// Converts detector coordinates into a stable body/signing-space frame.
///
/// Image-space x/y are kept for drawing. The per-landmark world values and z
/// are retained for the classifier, while the feature vector is centred on
/// the wrist and scaled by the hand span so distance from the camera does not
/// dominate the model.
class HandPoseNormalizer {
  static const List<int> _poseIndices = <int>[
    0,
    11,
    12,
    13,
    14,
    15,
    16,
    23,
    24,
    25,
    26,
  ];
  static const int _faceUpperCount = 24;
  static const int _faceMouthCount = 12;

  HandTrackingFrame? _previous;
  HandMotionFeatures _previousMotion = const HandMotionFeatures();
  final HandCoordinateAnalyzer _coordinateAnalyzer =
      const HandCoordinateAnalyzer();

  LandmarkFrame normalize(HandTrackingFrame source) {
    final hands = source.hands
        .where((hand) => hand.landmarks.length >= 21)
        .toList(growable: false);
    final left = _byHandedness(hands, Handedness.left);
    final right = _byHandedness(hands, Handedness.right);
    final motion = _motion(source, hands);
    final featureVector = <double>[
      ..._normalizedHandVector(left),
      ..._normalizedHandVector(right),
      ..._normalizedPoseVector(source.poseLandmarks),
      ..._normalizedFaceVector(
        source.faceUpperLandmarks,
        source.faceMouthLandmarks,
      ),
      motion.averageSpeed,
      motion.averageAcceleration,
      motion.averageOpenness,
      for (final emotion in deepFaceEmotionLabels)
        source.face?.emotionScores[emotion] ?? 0,
    ];

    _previous = source;
    _previousMotion = motion;

    return LandmarkFrame(
      timestamp: source.timestamp,
      leftShoulder: _point(source.leftShoulder),
      rightShoulder: _point(source.rightShoulder),
      leftWrist: _wrist(left),
      rightWrist: _wrist(right),
      leftHandVisible: left != null,
      rightHandVisible: right != null,
      trackingConfidence: _confidence(source, hands),
      featureVector: featureVector,
      hands: hands,
      handCoordinateAnalysis: _coordinateAnalyzer.analyze(hands),
      faceExpression: source.face,
      handMotion: motion,
      poseLandmarks: source.poseLandmarks,
      faceUpperLandmarks: source.faceUpperLandmarks,
      faceMouthLandmarks: source.faceMouthLandmarks,
      subjectTracking: source.subjectTracking,
    );
  }

  TrackedHand? _byHandedness(List<TrackedHand> hands, Handedness side) {
    for (final hand in hands) {
      if (hand.handedness == side) return hand;
    }
    return null;
  }

  NormalizedPoint? _wrist(TrackedHand? hand) {
    final wrist = hand?.wrist;
    if (wrist == null) return null;
    return NormalizedPoint(
      x: wrist.x,
      y: wrist.y,
      z: wrist.z,
      visibility: hand!.confidence,
    );
  }

  NormalizedPoint? _point(HandLandmark? landmark) {
    if (landmark == null) return null;
    return NormalizedPoint(
      x: landmark.x,
      y: landmark.y,
      z: landmark.z,
      visibility: landmark.visibility,
    );
  }

  double _confidence(HandTrackingFrame source, List<TrackedHand> hands) {
    if (hands.isEmpty) return source.processingConfidence;
    final handConfidence =
        hands
            .map((hand) => hand.confidence)
            .reduce((left, right) => left + right) /
        hands.length;
    return (handConfidence + source.processingConfidence) / 2;
  }

  List<double> _normalizedHandVector(TrackedHand? hand) {
    if (hand == null || hand.landmarks.length < 21) {
      return List<double>.filled(21 * 3, 0);
    }
    final wrist = hand.landmarks.first;
    final span = _handSpan(hand).clamp(0.08, 1.0);
    return <double>[
      for (final landmark in hand.landmarks) ...<double>[
        (landmark.x - wrist.x) / span,
        (landmark.y - wrist.y) / span,
        (landmark.z - wrist.z) / span,
      ],
    ];
  }

  double _handSpan(TrackedHand hand) {
    final wrist = hand.landmarks.first;
    final middleMcp = hand.landmarks[9];
    final indexMcp = hand.landmarks[5];
    final pinkyMcp = hand.landmarks[17];
    return ((middleMcp.x - wrist.x).abs() +
            (middleMcp.y - wrist.y).abs() +
            (indexMcp.x - pinkyMcp.x).abs()) /
        3;
  }

  List<double> _normalizedPoseVector(List<PoseLandmark> landmarks) {
    PoseLandmark? byIndex(int index) {
      for (final landmark in landmarks) {
        if (landmark.index == index) return landmark;
      }
      return null;
    }

    final leftShoulder = byIndex(11);
    final rightShoulder = byIndex(12);
    final centerX = leftShoulder != null && rightShoulder != null
        ? (leftShoulder.x + rightShoulder.x) / 2
        : 0.5;
    final centerY = leftShoulder != null && rightShoulder != null
        ? (leftShoulder.y + rightShoulder.y) / 2
        : 0.5;
    final shoulderSpan = leftShoulder != null && rightShoulder != null
        ? math
              .sqrt(
                math.pow(rightShoulder.x - leftShoulder.x, 2) +
                    math.pow(rightShoulder.y - leftShoulder.y, 2),
              )
              .clamp(.1, 1.0)
        : 1.0;
    final vector = <double>[];
    for (final index in _poseIndices) {
      final landmark = byIndex(index);
      if (landmark == null) {
        vector.addAll(const <double>[0, 0, 0, 0]);
        continue;
      }
      vector.addAll(<double>[
        (landmark.x - centerX) / shoulderSpan,
        (landmark.y - centerY) / shoulderSpan,
        landmark.z / shoulderSpan,
        landmark.visibility,
      ]);
    }
    return vector;
  }

  List<double> _normalizedFaceVector(
    List<FaceLandmark> upper,
    List<FaceLandmark> mouth,
  ) {
    final landmarks = <FaceLandmark>[...upper, ...mouth];
    if (landmarks.isEmpty) {
      return List<double>.filled((_faceUpperCount + _faceMouthCount) * 4, 0);
    }
    final minX = landmarks.map((landmark) => landmark.x).reduce(math.min);
    final maxX = landmarks.map((landmark) => landmark.x).reduce(math.max);
    final minY = landmarks.map((landmark) => landmark.y).reduce(math.min);
    final maxY = landmarks.map((landmark) => landmark.y).reduce(math.max);
    final centerX = (minX + maxX) / 2;
    final centerY = (minY + maxY) / 2;
    final span = math.max(maxX - minX, maxY - minY).clamp(.08, 1.0);
    final vector = <double>[];
    for (final landmark in <FaceLandmark>[...upper, ...mouth]) {
      vector.addAll(<double>[
        (landmark.x - centerX) / span,
        (landmark.y - centerY) / span,
        landmark.z / span,
        landmark.visibility,
      ]);
    }
    final expected = (_faceUpperCount + _faceMouthCount) * 4;
    if (vector.length < expected) {
      vector.addAll(List<double>.filled(expected - vector.length, 0));
    }
    return vector.take(expected).toList(growable: false);
  }

  HandMotionFeatures _motion(
    HandTrackingFrame source,
    List<TrackedHand> hands,
  ) {
    final previous = _previous;
    if (previous == null || hands.isEmpty || previous.hands.isEmpty) {
      return HandMotionFeatures(
        averageOpenness: _averageOpenness(hands),
        dominantHand: _dominantHand(hands),
      );
    }
    final elapsed = source.timestamp
        .difference(previous.timestamp)
        .inMilliseconds;
    final seconds = (elapsed <= 0 ? 33 : elapsed) / 1000;
    final speeds = <double>[];
    final directions = <String>[];
    for (final hand in hands) {
      final old = _byHandedness(previous.hands, hand.handedness);
      if (old == null || old.landmarks.isEmpty || hand.landmarks.isEmpty) {
        continue;
      }
      final dx = hand.wrist!.x - old.wrist!.x;
      final dy = hand.wrist!.y - old.wrist!.y;
      speeds.add((dx.abs() + dy.abs()) / seconds);
      directions.add(_direction(dx, dy));
    }
    final speed = speeds.isEmpty
        ? 0.0
        : speeds.reduce((left, right) => left + right) / speeds.length;
    final acceleration = ((speed - _previousMotion.averageSpeed) / seconds)
        .abs();
    return HandMotionFeatures(
      averageSpeed: speed,
      averageAcceleration: acceleration,
      averageOpenness: _averageOpenness(hands),
      direction: _mostCommon(directions),
      dominantHand: _dominantHand(hands),
    );
  }

  double _averageOpenness(List<TrackedHand> hands) => hands.isEmpty
      ? 0
      : hands
                .map((hand) => hand.openness)
                .reduce((left, right) => left + right) /
            hands.length;

  Handedness _dominantHand(List<TrackedHand> hands) {
    if (hands.isEmpty) return Handedness.unknown;
    return hands.first.confidence >=
            (hands.length > 1 ? hands[1].confidence : 0)
        ? hands.first.handedness
        : hands[1].handedness;
  }

  String _direction(double dx, double dy) {
    if (dx.abs() < .015 && dy.abs() < .015) return 'still';
    if (dx.abs() > dy.abs()) return dx > 0 ? 'right' : 'left';
    return dy > 0 ? 'down' : 'up';
  }

  String _mostCommon(List<String> values) {
    if (values.isEmpty) return 'still';
    final counts = <String, int>{};
    for (final value in values) {
      counts[value] = (counts[value] ?? 0) + 1;
    }
    return counts.entries
        .reduce((left, right) => left.value >= right.value ? left : right)
        .key;
  }
}
