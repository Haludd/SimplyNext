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
      ingest(
        LandmarkFrame(
          timestamp: now,
          leftShoulder: const NormalizedPoint(x: 0.39, y: 0.56),
          rightShoulder: const NormalizedPoint(x: 0.61, y: 0.56),
          leftWrist: const NormalizedPoint(x: 0.27, y: 0.74),
          rightWrist: const NormalizedPoint(x: 0.73, y: 0.74),
          leftHandVisible: true,
          rightHandVisible: true,
          trackingConfidence: 0.98,
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
        ),
      );
    });
  }

  final StreamController<LandmarkFrame> _controller =
      StreamController<LandmarkFrame>.broadcast();
  final TrackingSampleBuffer _confidenceWindow = TrackingSampleBuffer();
  LandmarkFrame? _latestFrame;
  late final Timer _timer;

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
