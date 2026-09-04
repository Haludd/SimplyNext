import 'dart:math' as math;

class NormalizedPoint {
  const NormalizedPoint({
    required this.x,
    required this.y,
    this.z = 0,
    this.visibility = 1,
  });

  final double x;
  final double y;
  final double z;
  final double visibility;

  bool get isVisible => visibility >= 0.5;
}

class LandmarkFrame {
  const LandmarkFrame({
    required this.timestamp,
    this.leftShoulder,
    this.rightShoulder,
    this.leftWrist,
    this.rightWrist,
    this.leftHandVisible = false,
    this.rightHandVisible = false,
    this.lightingScore = 0.9,
    this.trackingConfidence = 0.98,
    this.featureVector = const <double>[],
  });

  final DateTime timestamp;
  final NormalizedPoint? leftShoulder;
  final NormalizedPoint? rightShoulder;
  final NormalizedPoint? leftWrist;
  final NormalizedPoint? rightWrist;
  final bool leftHandVisible;
  final bool rightHandVisible;
  final double lightingScore;
  final double trackingConfidence;
  final List<double> featureVector;

  bool get shouldersVisible =>
      leftShoulder?.isVisible == true && rightShoulder?.isVisible == true;
  bool get armsVisible =>
      leftWrist?.isVisible == true && rightWrist?.isVisible == true;
  bool get handsVisible => leftHandVisible && rightHandVisible;
}

class AlignmentConfig {
  const AlignmentConfig({
    this.targetCenter = const NormalizedPoint(x: 0.5, y: 0.56),
    this.horizontalTolerance = 0.07,
    this.verticalTolerance = 0.08,
    this.minimumShoulderWidth = 0.18,
    this.maximumShoulderWidth = 0.48,
  });

  final NormalizedPoint targetCenter;
  final double horizontalTolerance;
  final double verticalTolerance;
  final double minimumShoulderWidth;
  final double maximumShoulderWidth;
}

class AlignmentResult {
  const AlignmentResult({
    required this.isAligned,
    required this.message,
    required this.detail,
    this.shoulderWidth = 0,
    this.horizontalError = 0,
    this.verticalError = 0,
  });

  final bool isAligned;
  final String message;
  final String detail;
  final double shoulderWidth;
  final double horizontalError;
  final double verticalError;
}

class AlignmentEvaluator {
  const AlignmentEvaluator({this.config = const AlignmentConfig()});

  final AlignmentConfig config;

  AlignmentResult evaluate(LandmarkFrame frame) {
    final left = frame.leftShoulder;
    final right = frame.rightShoulder;
    if (left == null || right == null || !left.isVisible || !right.isVisible) {
      return const AlignmentResult(
        isAligned: false,
        message: 'Show both shoulders',
        detail: 'Keep your shoulders and upper body visible in the frame.',
      );
    }

    final midpoint = NormalizedPoint(
      x: (left.x + right.x) / 2,
      y: (left.y + right.y) / 2,
    );
    final width = math.sqrt(
      math.pow(right.x - left.x, 2) + math.pow(right.y - left.y, 2),
    );
    final horizontalError = (midpoint.x - config.targetCenter.x).abs();
    final verticalError = (midpoint.y - config.targetCenter.y).abs();

    if (width < config.minimumShoulderWidth) {
      return AlignmentResult(
        isAligned: false,
        message: 'Move closer',
        detail: 'Your shoulders are too far from the camera.',
        shoulderWidth: width,
        horizontalError: horizontalError,
        verticalError: verticalError,
      );
    }
    if (width > config.maximumShoulderWidth) {
      return AlignmentResult(
        isAligned: false,
        message: 'Move back',
        detail: 'Give your hands and shoulders more room in the frame.',
        shoulderWidth: width,
        horizontalError: horizontalError,
        verticalError: verticalError,
      );
    }
    if (horizontalError >= config.horizontalTolerance) {
      final direction = midpoint.x < config.targetCenter.x ? 'right' : 'left';
      return AlignmentResult(
        isAligned: false,
        message: 'Move slightly to the $direction',
        detail: 'Centre your shoulders on the guide line.',
        shoulderWidth: width,
        horizontalError: horizontalError,
        verticalError: verticalError,
      );
    }
    if (verticalError >= config.verticalTolerance) {
      final direction = midpoint.y < config.targetCenter.y ? 'Lower' : 'Raise';
      return AlignmentResult(
        isAligned: false,
        message: '$direction your shoulders into frame',
        detail: 'Match your shoulders to the horizontal guide.',
        shoulderWidth: width,
        horizontalError: horizontalError,
        verticalError: verticalError,
      );
    }
    return AlignmentResult(
      isAligned: true,
      message: 'Position looks good ✓',
      detail: 'You are ready to continue.',
      shoulderWidth: width,
      horizontalError: horizontalError,
      verticalError: verticalError,
    );
  }
}

class TrackingSampleBuffer {
  TrackingSampleBuffer({this.window = const Duration(seconds: 30)});

  final Duration window;
  final List<_ConfidenceSample> _samples = <_ConfidenceSample>[];

  void add(double confidence, [DateTime? now]) {
    final timestamp = now ?? DateTime.now();
    _samples.add(_ConfidenceSample(timestamp, confidence));
    _prune(timestamp);
  }

  double get average => averageAt();

  double averageAt([DateTime? now]) {
    _prune(now ?? DateTime.now());
    if (_samples.isEmpty) return 0;
    return _samples.map((sample) => sample.value).reduce((a, b) => a + b) /
        _samples.length;
  }

  DateTime? get latestTimestamp =>
      _samples.isEmpty ? null : _samples.last.timestamp;

  String get windowLabel {
    final latest = latestTimestamp;
    if (latest == null) return '[last 30 seconds]';
    final age = DateTime.now().difference(latest).inSeconds.clamp(0, 30);
    return '[last 30 seconds · updated ${age}s ago]';
  }

  void _prune(DateTime now) => _samples.removeWhere(
    (sample) => now.difference(sample.timestamp) > window,
  );
}

class _ConfidenceSample {
  const _ConfidenceSample(this.timestamp, this.value);
  final DateTime timestamp;
  final double value;
}

class CustomSign {
  const CustomSign({
    required this.label,
    required this.samples,
    required this.createdAt,
  });

  final String label;
  final List<List<double>> samples;
  final DateTime createdAt;

  bool get hasEnoughSamples => samples.length >= 5;

  Map<String, dynamic> toJson() => <String, dynamic>{
    'label': label,
    'samples': samples,
    'createdAt': createdAt.toIso8601String(),
  };

  factory CustomSign.fromJson(Map<String, dynamic> json) => CustomSign(
    label: json['label'] as String,
    samples: (json['samples'] as List<dynamic>)
        .map(
          (sample) => (sample as List<dynamic>)
              .map((value) => (value as num).toDouble())
              .toList(),
        )
        .toList(),
    createdAt: DateTime.parse(json['createdAt'] as String),
  );
}
