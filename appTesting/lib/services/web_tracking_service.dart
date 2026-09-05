import 'dart:async';

import '../models/hand_tracking_models.dart';
import '../models/tracking_models.dart';
import 'hand_pose_normalizer.dart';
import 'tracking_service.dart';
import 'web_hand_tracker_bridge.dart';

class WebTrackingService implements TrackingService {
  WebTrackingService({WebHandTrackerBridge? bridge})
    : _bridge = bridge ?? WebHandTrackerBridge();

  final WebHandTrackerBridge _bridge;
  final HandPoseNormalizer _normalizer = HandPoseNormalizer();
  final StreamController<LandmarkFrame> _controller =
      StreamController<LandmarkFrame>.broadcast();
  final TrackingSampleBuffer _confidenceWindow = TrackingSampleBuffer();
  final List<LandmarkFrame> _recentFrames = <LandmarkFrame>[];
  final List<LandmarkFrame> _utteranceFrames = <LandmarkFrame>[];
  LandmarkFrame? _latestFrame;
  StreamSubscription<HandTrackingFrame>? _subscription;
  bool _started = false;
  String _status = 'Waiting for camera';

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
  int get utteranceFrameCount => _utteranceFrames.length;

  @override
  String get status => _status;

  @override
  Future<void> start() async {
    if (_started) return;
    _status = 'Starting hand tracker';
    _utteranceFrames.clear();
    _subscription = _bridge.frames.listen(ingestRaw);
    try {
      await _bridge.start();
      _started = true;
      _status = 'MediaPipe four-world tracking';
    } catch (_) {
      _status = 'Camera permission needed';
      await _subscription?.cancel();
      _subscription = null;
      rethrow;
    }
  }

  void ingestRaw(HandTrackingFrame raw) => ingest(_normalizer.normalize(raw));

  @override
  Future<List<LandmarkFrame>> finishUtterance() async {
    final frames = List<LandmarkFrame>.unmodifiable(_utteranceFrames);
    _utteranceFrames.clear();
    await _bridge.endUtterance();
    _status = 'MediaPipe four-world tracking · next utterance';
    return frames;
  }

  @override
  void ingest(LandmarkFrame frame) {
    _latestFrame = frame;
    _recentFrames.add(frame);
    _utteranceFrames.add(frame);
    if (_recentFrames.length > 180) _recentFrames.removeAt(0);
    if (_utteranceFrames.length > 600) _utteranceFrames.removeAt(0);
    _confidenceWindow.add(frame.trackingConfidence, frame.timestamp);
    if (!_controller.isClosed) _controller.add(frame);
  }

  @override
  void dispose() {
    _subscription?.cancel();
    _bridge.stop();
    _bridge.dispose();
    _controller.close();
  }
}
