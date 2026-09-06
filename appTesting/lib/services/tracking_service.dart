import 'dart:async';

import '../models/hand_tracking_models.dart'
    show
        FingerTrackingStatus,
        HandLandmark,
        Handedness,
        PoseLandmark,
        SubjectTracking,
        TrackedHand;
import '../models/tracking_models.dart'
    show LandmarkFrame, NormalizedPoint, TrackingSampleBuffer;

abstract class TrackingService {
  Stream<LandmarkFrame> get frames;
  LandmarkFrame? get latestFrame;
  TrackingSampleBuffer get confidenceWindow;
  List<LandmarkFrame> get recentFrames;
  List<LandmarkFrame> get utteranceFrames;
  int get utteranceFrameCount;
  bool get isCapturingUtterance;
  String get status;
  Future<void> start();
  void beginUtterance();
  Future<List<LandmarkFrame>> finishUtterance();
  void ingest(LandmarkFrame frame);
  void dispose();
}

/// The UI consumes this interface, so MediaPipe Tasks can be connected without
/// duplicating alignment, confidence, or custom-sign logic.
class DemoTrackingService implements TrackingService {
  DemoTrackingService() {
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      final now = DateTime.now();
      ingest(_demoFrame(now));
    });
  }

  final StreamController<LandmarkFrame> _controller =
      StreamController<LandmarkFrame>.broadcast();
  final TrackingSampleBuffer _confidenceWindow = TrackingSampleBuffer();
  final List<LandmarkFrame> _recentFrames = <LandmarkFrame>[];
  final List<LandmarkFrame> _utteranceFrames = <LandmarkFrame>[];
  LandmarkFrame? _latestFrame;
  bool _capturingUtterance = false;
  String _status = 'Demo tracking';
  late final Timer _timer;

  @override
  Stream<LandmarkFrame> get frames => _controller.stream;

  @override
  LandmarkFrame? get latestFrame => _latestFrame;

  @override
  TrackingSampleBuffer get confidenceWindow => _confidenceWindow;

  @override
  List<LandmarkFrame> get recentFrames =>
      List<LandmarkFrame>.unmodifiable(_recentFrames);

  @override
  List<LandmarkFrame> get utteranceFrames =>
      List<LandmarkFrame>.unmodifiable(_utteranceFrames);

  @override
  int get utteranceFrameCount => _utteranceFrames.length;

  @override
  bool get isCapturingUtterance => _capturingUtterance;

  @override
  String get status => _status;

  @override
  Future<void> start() async {}

  @override
  void beginUtterance() {
    _utteranceFrames.clear();
    _capturingUtterance = true;
    _status = 'Capturing LandmarkFrame data';
  }

  @override
  Future<List<LandmarkFrame>> finishUtterance() async {
    final frames = List<LandmarkFrame>.unmodifiable(_utteranceFrames);
    _utteranceFrames.clear();
    _capturingUtterance = false;
    _status = 'Demo tracking · ready for next utterance';
    return frames;
  }

  @override
  void ingest(LandmarkFrame frame) {
    _latestFrame = frame;
    _recentFrames.add(frame);
    if (_capturingUtterance) _utteranceFrames.add(frame);
    if (_recentFrames.length > 180) _recentFrames.removeAt(0);
    if (_utteranceFrames.length > 600) _utteranceFrames.removeAt(0);
    _confidenceWindow.add(frame.trackingConfidence, frame.timestamp);
    if (!_controller.isClosed) _controller.add(frame);
  }

  @override
  void dispose() {
    _timer.cancel();
    _controller.close();
  }
}

LandmarkFrame _demoFrame(DateTime timestamp) {
  const leftShoulder = PoseLandmark(
    index: 11,
    name: 'left_shoulder',
    x: 0.39,
    y: 0.56,
    z: -0.02,
    visibility: 0.98,
    presence: 0.98,
  );
  const rightShoulder = PoseLandmark(
    index: 12,
    name: 'right_shoulder',
    x: 0.61,
    y: 0.56,
    z: -0.02,
    visibility: 0.98,
    presence: 0.98,
  );
  const leftPoseWrist = PoseLandmark(
    index: 15,
    name: 'left_wrist',
    x: 0.27,
    y: 0.74,
    z: -0.04,
    visibility: 0.98,
    presence: 0.98,
  );
  const rightPoseWrist = PoseLandmark(
    index: 16,
    name: 'right_wrist',
    x: 0.73,
    y: 0.74,
    z: -0.04,
    visibility: 0.98,
    presence: 0.98,
  );
  const poseLandmarks = <PoseLandmark>[
    PoseLandmark(
      index: 0,
      name: 'nose',
      x: 0.50,
      y: 0.28,
      z: -0.08,
      visibility: 0.97,
      presence: 0.97,
    ),
    leftShoulder,
    rightShoulder,
    PoseLandmark(
      index: 13,
      name: 'left_elbow',
      x: 0.33,
      y: 0.65,
      z: -0.03,
      visibility: 0.98,
      presence: 0.98,
    ),
    PoseLandmark(
      index: 14,
      name: 'right_elbow',
      x: 0.67,
      y: 0.65,
      z: -0.03,
      visibility: 0.98,
      presence: 0.98,
    ),
    leftPoseWrist,
    rightPoseWrist,
    PoseLandmark(
      index: 23,
      name: 'left_hip',
      x: 0.43,
      y: 0.82,
      z: 0,
      visibility: 0.96,
      presence: 0.96,
    ),
    PoseLandmark(
      index: 24,
      name: 'right_hip',
      x: 0.57,
      y: 0.82,
      z: 0,
      visibility: 0.96,
      presence: 0.96,
    ),
    PoseLandmark(
      index: 25,
      name: 'left_knee',
      x: 0.44,
      y: 0.96,
      z: 0.01,
      visibility: 0.94,
      presence: 0.94,
    ),
    PoseLandmark(
      index: 26,
      name: 'right_knee',
      x: 0.56,
      y: 0.96,
      z: 0.01,
      visibility: 0.94,
      presence: 0.94,
    ),
  ];

  final leftHand = _demoHand(
    handedness: Handedness.left,
    wristX: leftPoseWrist.x,
    wristY: leftPoseWrist.y,
  );
  final rightHand = _demoHand(
    handedness: Handedness.right,
    wristX: rightPoseWrist.x,
    wristY: rightPoseWrist.y,
  );

  return LandmarkFrame(
    timestamp: timestamp,
    leftShoulder: _normalisedPosePoint(leftShoulder),
    rightShoulder: _normalisedPosePoint(rightShoulder),
    leftWrist: _normalisedHandPoint(leftHand.landmarks.first),
    rightWrist: _normalisedHandPoint(rightHand.landmarks.first),
    leftHandVisible: true,
    rightHandVisible: true,
    trackingConfidence: 0.98,
    hands: <TrackedHand>[leftHand, rightHand],
    poseLandmarks: poseLandmarks,
    subjectTracking: const SubjectTracking(
      locked: true,
      visible: true,
      centerX: 0.50,
      centerY: 0.61,
      area: 0.24,
      missingFrames: 0,
    ),
    featureVector: const <double>[
      0.39,
      0.56,
      0.61,
      0.56,
      0.27,
      0.74,
      0.73,
      0.74,
    ],
  );
}

TrackedHand _demoHand({
  required Handedness handedness,
  required double wristX,
  required double wristY,
}) {
  final direction = handedness == Handedness.left ? 1.0 : -1.0;
  final landmarks = _demoHandShape
      .map(
        (point) => HandLandmark(
          x: wristX + point.x * direction,
          y: wristY + point.y,
          z: point.z,
          worldX: point.x * direction * 0.55,
          worldY: point.y * 0.55,
          worldZ: point.z * 0.55,
          visibility: 0.98,
        ),
      )
      .toList(growable: false);

  return TrackedHand(
    handedness: handedness,
    confidence: 0.98,
    landmarks: landmarks,
    fingerStatus: _observedFingerStatus,
  );
}

NormalizedPoint _normalisedPosePoint(PoseLandmark point) => NormalizedPoint(
  x: point.x,
  y: point.y,
  z: point.z,
  visibility: point.visibility,
);

NormalizedPoint _normalisedHandPoint(HandLandmark point) => NormalizedPoint(
  x: point.x,
  y: point.y,
  z: point.z,
  visibility: point.visibility,
);

const _observedFingerStatus = <String, FingerTrackingStatus>{
  'thumb': FingerTrackingStatus(
    status: 'observed',
    confidence: 0.98,
    evidenceFrames: 6,
  ),
  'index': FingerTrackingStatus(
    status: 'observed',
    confidence: 0.98,
    evidenceFrames: 6,
  ),
  'middle': FingerTrackingStatus(
    status: 'observed',
    confidence: 0.98,
    evidenceFrames: 6,
  ),
  'ring': FingerTrackingStatus(
    status: 'observed',
    confidence: 0.98,
    evidenceFrames: 6,
  ),
  'pinky': FingerTrackingStatus(
    status: 'observed',
    confidence: 0.98,
    evidenceFrames: 6,
  ),
};

/// MediaPipe hand-landmark list order: wrist, thumb, then four joints for
/// index, middle, ring, and pinky. Values are image-space offsets from wrist.
const _demoHandShape = <_DemoHandPoint>[
  _DemoHandPoint(0, 0, 0),
  _DemoHandPoint(-0.025, -0.025, -0.004),
  _DemoHandPoint(-0.045, -0.052, -0.009),
  _DemoHandPoint(-0.058, -0.078, -0.014),
  _DemoHandPoint(-0.065, -0.101, -0.018),
  _DemoHandPoint(-0.025, -0.073, -0.010),
  _DemoHandPoint(-0.027, -0.116, -0.018),
  _DemoHandPoint(-0.029, -0.154, -0.025),
  _DemoHandPoint(-0.030, -0.187, -0.031),
  _DemoHandPoint(0.010, -0.079, -0.011),
  _DemoHandPoint(0.011, -0.128, -0.020),
  _DemoHandPoint(0.012, -0.169, -0.028),
  _DemoHandPoint(0.013, -0.204, -0.035),
  _DemoHandPoint(0.043, -0.072, -0.009),
  _DemoHandPoint(0.049, -0.115, -0.016),
  _DemoHandPoint(0.053, -0.150, -0.022),
  _DemoHandPoint(0.057, -0.180, -0.027),
  _DemoHandPoint(0.072, -0.057, -0.006),
  _DemoHandPoint(0.083, -0.089, -0.011),
  _DemoHandPoint(0.090, -0.116, -0.016),
  _DemoHandPoint(0.096, -0.139, -0.020),
];

class _DemoHandPoint {
  const _DemoHandPoint(this.x, this.y, this.z);

  final double x;
  final double y;
  final double z;
}
