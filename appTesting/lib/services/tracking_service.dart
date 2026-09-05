import 'dart:async';

import '../models/tracking_models.dart';

abstract class TrackingService {
  Stream<LandmarkFrame> get frames;
  LandmarkFrame? get latestFrame;
  TrackingSampleBuffer get confidenceWindow;
  void ingest(LandmarkFrame frame);
  void dispose();
}

/// The UI consumes this interface, so MediaPipe Tasks can be connected without
/// duplicating alignment, confidence, or custom-sign logic.
class DemoTrackingService implements TrackingService {
  DemoTrackingService() {
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      final now = DateTime.now();
      ingest(_demoFrame(now, _frameIndex++));
    });
  }

  final StreamController<LandmarkFrame> _controller =
      StreamController<LandmarkFrame>.broadcast();
  final TrackingSampleBuffer _confidenceWindow = TrackingSampleBuffer();
  LandmarkFrame? _latestFrame;
  late final Timer _timer;
  var _frameIndex = 0;

  @override
  Stream<LandmarkFrame> get frames => _controller.stream;

  @override
  LandmarkFrame? get latestFrame => _latestFrame;

  @override
  TrackingSampleBuffer get confidenceWindow => _confidenceWindow;

  @override
  void ingest(LandmarkFrame frame) {
    _latestFrame = frame;
    _confidenceWindow.add(frame.trackingConfidence, frame.timestamp);
    if (!_controller.isClosed) _controller.add(frame);
  }

  @override
  void dispose() {
    _timer.cancel();
    _controller.close();
  }
}

LandmarkFrame _demoFrame(DateTime timestamp, int frameIndex) {
  final pose = List<LandmarkPoint?>.filled(17, null);
  pose[11] = _demoPoint(11, 0.39, 0.56);
  pose[12] = _demoPoint(12, 0.61, 0.56);
  pose[15] = _demoPoint(15, 0.27, 0.74);
  pose[16] = _demoPoint(16, 0.73, 0.74);

  return LandmarkFrame(
    timestamp: timestamp,
    frameIndex: frameIndex,
    subjectId: 'demo-subject',
    pose: LandmarkGroup(isPresent: true, landmarks: pose),
    hands: <HandLandmarkGroup>[
      HandLandmarkGroup(
        isPresent: true,
        landmarks: <LandmarkPoint?>[_demoPoint(0, 0.27, 0.74)],
        rawHandedness: Handedness.left,
        handedness: Handedness.left,
        handednessScore: 0.98,
        handednessRunningAverage: 0.02,
        handednessObservationCount: 1,
        handednessUncertain: false,
      ),
      HandLandmarkGroup(
        isPresent: true,
        landmarks: <LandmarkPoint?>[_demoPoint(0, 0.73, 0.74)],
        rawHandedness: Handedness.right,
        handedness: Handedness.right,
        handednessScore: 0.98,
        handednessRunningAverage: 0.98,
        handednessObservationCount: 1,
        handednessUncertain: false,
      ),
    ],
    trackingStatus: TrackingStatus.tracked,
    trackingQuality: 0.98,
    canNormalise: true,
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

LandmarkPoint _demoPoint(int index, double x, double y) => LandmarkPoint(
  index: index,
  confidence: 0.98,
  imageCoordinates: LandmarkCoordinates(x: x, y: y),
);
