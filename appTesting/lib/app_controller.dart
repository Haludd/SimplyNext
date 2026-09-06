import 'dart:async';

import 'package:flutter/foundation.dart';

import 'models/face_tracking_models.dart';
import 'models/tracking_models.dart';
import 'models/hand_tracking_models.dart';
import 'services/device_access_service.dart';
import 'services/local_state_service.dart';
import 'services/api_client.dart';
import 'services/sign_analysis_service.dart';
import 'services/tracking_service.dart';
import 'services/utterance_stillness_detector.dart';

enum SignBridgePage { onboarding, live, dictionary, settings }

enum ViewMode { raw, wireframe, clean }

class AppController extends ChangeNotifier {
  AppController(
    this._localState,
    this.tracking,
    this.devices, {
    this.apiClient,
  }) {
    backendStatus = apiClient == null
        ? 'Offline simulation · no backend configured'
        : 'Backend configured';
    _trackingSubscription = tracking.frames.listen(_onTrackingFrame);
    unawaited(_restoreState());
  }

  final LocalStateService _localState;
  final TrackingService tracking;
  final DeviceAccessService devices;
  final SignSequenceApiClient? apiClient;
  final SignAnalysisService signAnalyzer = SignAnalysisService();
  final SimulatedSignSequenceApiClient simulator =
      SimulatedSignSequenceApiClient();
  final UtteranceStillnessDetector _utteranceStillnessDetector =
      UtteranceStillnessDetector();
  final String sessionId = 'session-${DateTime.now().millisecondsSinceEpoch}';

  late final StreamSubscription<LandmarkFrame> _trackingSubscription;
  Timer? _frameNotifyTimer;
  SignBridgePage page = SignBridgePage.onboarding;
  ViewMode viewMode = ViewMode.wireframe;
  int calibrationStep = 1;
  bool calibrated = false;
  bool audioEnabled = true;
  bool isPaused = false;
  bool isUnregisteredSign = false;
  List<CustomSign> customSigns = <CustomSign>[];
  SignAnalysisResult? latestAnalysis;

  /// The most recently completed utterance. Each item is one LandmarkFrame;
  /// this is the handoff for the next processing stage.
  ///
  /// NEXT TEAMMATE: after the user presses "Analyse utterance", access the
  /// captured sequence with:
  ///
  ///   final frames = controller.lastUtteranceFrames;
  ///
  /// Then read coordinates from `frame.hands`, `frame.poseLandmarks`, and
  /// `frame.faceUpperLandmarks`/`frame.faceMouthLandmarks`. If serialized data
  /// is needed, use `controller.lastUtteranceJson` or `frame.toJson()`.
  List<LandmarkFrame> lastUtteranceFrames = const <LandmarkFrame>[];
  bool analysisInFlight = false;
  bool _automaticFinishInFlight = false;
  String backendStatus = 'Offline simulation · no backend configured';
  String selectedLanguage = 'ASL';

  void _onTrackingFrame(LandmarkFrame frame) {
    if (tracking.isCapturingUtterance && !_automaticFinishInFlight) {
      if (_utteranceStillnessDetector.update(frame)) {
        unawaited(analyzeSign(automatic: true));
      }
    } else if (!tracking.isCapturingUtterance) {
      _utteranceStillnessDetector.reset();
    }

    // The camera stream can be continuous, but rebuilding the entire Flutter
    // page for every detector frame is expensive on the web. Keep the latest
    // frame immediately in the tracking service and repaint the UI at a
    // steady 20 FPS.
    if (_frameNotifyTimer != null) return;
    _frameNotifyTimer = Timer(const Duration(milliseconds: 33), () {
      _frameNotifyTimer = null;
      notifyListeners();
    });
  }

  LandmarkFrame? get latestFrame => tracking.latestFrame;
  AlignmentResult get alignment => AlignmentEvaluator().evaluate(
    latestFrame ??
        LandmarkFrame(timestamp: DateTime.fromMillisecondsSinceEpoch(0)),
  );
  double get confidence => latestFrame?.trackingConfidence ?? 0;
  String get confidenceWindowLabel => tracking.confidenceWindow.windowLabel;
  String get trackingStatus => tracking.status;
  int get utteranceFrameCount => tracking.utteranceFrameCount;
  bool get isCapturingUtterance => tracking.isCapturingUtterance;

  /// Starts a fresh utterance buffer. Tracking itself remains continuous;
  /// only frames collected after this point belong to the utterance.
  void startUtterance() {
    if (analysisInFlight || tracking.isCapturingUtterance) return;
    if (latestFrame == null) {
      backendStatus = 'Start the camera before capturing an utterance';
      notifyListeners();
      return;
    }
    _utteranceStillnessDetector.reset();
    tracking.beginUtterance();
    latestAnalysis = null;
    backendStatus = 'Capturing LandmarkFrame data locally';
    notifyListeners();
  }

  /// JSON-ready handoff for the next processing stage. The source of truth is
  /// still [lastUtteranceFrames], not this serialized convenience view.
  List<Map<String, dynamic>> get lastUtteranceJson => lastUtteranceFrames
      .map((frame) => frame.toJson())
      .toList(growable: false);

  void setLanguage(String language) {
    selectedLanguage = language;
    notifyListeners();
  }

  Future<void> _restoreState() async {
    calibrated = await _localState.isCalibrated();
    final savedSigns = await _localState.loadCustomSigns();
    customSigns = savedSigns;
    if (calibrated) {
      page = SignBridgePage.live;
    }
    notifyListeners();
  }

  void navigate(SignBridgePage destination) {
    if (!calibrated && destination != SignBridgePage.onboarding) {
      page = SignBridgePage.onboarding;
    } else {
      page = destination;
    }
    notifyListeners();
  }

  Future<void> requestCamera() async {
    await devices.enableCamera();
    if (devices.cameraReady) {
      try {
        await tracking.start();
      } catch (_) {
        if (kIsWeb) {
          devices.markWebCameraUnavailable(
            'Camera unavailable · allow access and retry',
          );
        }
      }
    }
    notifyListeners();
  }

  Future<void> analyzeSign({bool automatic = false}) async {
    if (automatic) _automaticFinishInFlight = true;
    if (_automaticFinishInFlight && !automatic) return;
    if (!tracking.isCapturingUtterance) {
      _automaticFinishInFlight = false;
      backendStatus = 'Press Start utterance before analysing';
      notifyListeners();
      return;
    }
    final frames = await tracking.finishUtterance();
    _utteranceStillnessDetector.reset();
    lastUtteranceFrames = frames;
    latestAnalysis = signAnalyzer.analyze(frames);
    backendStatus = automatic
        ? 'Pause detected · processing captured LandmarkFrames'
        : apiClient == null
        ? 'Preparing offline backend simulation'
        : 'Preparing utterance chunk for backend';
    notifyListeners();
    if (frames.isEmpty) {
      _automaticFinishInFlight = false;
      backendStatus = 'Waiting for tracked frames';
      notifyListeners();
      return;
    }

    analysisInFlight = true;
    notifyListeners();
    final payload = SignSequencePayload(
      sessionId: sessionId,
      sequenceId: 'sequence-${DateTime.now().millisecondsSinceEpoch}',
      language: selectedLanguage,
      startedAt: frames.first.timestamp,
      endedAt: frames.last.timestamp,
      frames: frames,
      lexiconVersion: SignLexicon.version,
    );
    try {
      if (apiClient == null) {
        latestAnalysis = await simulator.analyze(payload);
        backendStatus = 'Offline simulation · payload not sent';
      } else {
        latestAnalysis = await apiClient!.analyze(payload);
        backendStatus = 'Backend analysis returned';
      }
    } catch (_) {
      backendStatus = 'Backend unavailable · local readout shown';
    } finally {
      analysisInFlight = false;
      _automaticFinishInFlight = false;
      notifyListeners();
    }
  }

  Future<void> completeCalibrationStep() async {
    if (calibrationStep < 3) {
      calibrationStep += 1;
      notifyListeners();
      return;
    }
    calibrated = true;
    await _localState.setCalibrated(true);
    page = SignBridgePage.live;
    notifyListeners();
  }

  Future<void> recalibrate() async {
    calibrated = false;
    calibrationStep = 1;
    page = SignBridgePage.onboarding;
    await _localState.setCalibrated(false);
    notifyListeners();
  }

  void setViewMode(ViewMode mode) {
    viewMode = mode;
    notifyListeners();
  }

  void toggleAudio() {
    audioEnabled = !audioEnabled;
    notifyListeners();
  }

  void togglePause() {
    isPaused = !isPaused;
    notifyListeners();
  }

  void clearCaption() {
    isUnregisteredSign = false;
    notifyListeners();
  }

  void setUnregisteredSign(bool value) {
    isUnregisteredSign = value;
    notifyListeners();
  }

  Future<void> saveCustomSign(String label, List<List<double>> samples) async {
    final frame = latestFrame;
    final sign = CustomSign(
      label: label,
      samples: samples,
      createdAt: DateTime.now(),
      language: selectedLanguage,
      vectorSize: samples.isEmpty ? 0 : samples.first.length,
      coordinateSpace: _coordinateSpace(frame),
      faceSignal: frame?.faceExpression?.label ?? 'not captured',
    );
    customSigns = <CustomSign>[...customSigns, sign];
    await _localState.saveCustomSigns(customSigns);
    notifyListeners();
  }

  /// Builds one fixed-width sample for personal-sign matching.
  ///
  /// The live API keeps every raw landmark. My Signs additionally stores the
  /// fixed-width local sample: wrist-centred left/right hands, a
  /// shoulder-centred pose subset, curated face geometry, and facial-
  /// expression scores. The network contract remains LandmarkFrame JSON.
  List<double>? captureCurrentSignSample() {
    final frame = latestFrame;
    if (frame == null ||
        frame.trackingConfidence < .70 ||
        frame.hands.isEmpty) {
      return null;
    }

    // Frames produced by HandPoseNormalizer already contain the same fixed
    // four-world vector that the backend receives.
    if (frame.featureVector.isNotEmpty) {
      return List<double>.unmodifiable(frame.featureVector);
    }

    final vector = <double>[];
    for (final handedness in <Handedness>[Handedness.left, Handedness.right]) {
      TrackedHand? hand;
      for (final candidate in frame.hands) {
        if (candidate.handedness == handedness) {
          hand = candidate;
          break;
        }
      }
      if (hand == null || hand.landmarks.length < 21) {
        vector.addAll(List<double>.filled(63, 0));
        continue;
      }
      final wrist = hand.landmarks.first;
      final span = _handSpan(hand);
      for (final landmark in hand.landmarks) {
        vector.addAll(<double>[
          (landmark.x - wrist.x) / span,
          (landmark.y - wrist.y) / span,
          (landmark.z - wrist.z) / span,
        ]);
      }
    }

    final face = frame.faceExpression;
    for (final emotion in deepFaceEmotionLabels) {
      vector.add(face?.emotionScores[emotion] ?? 0);
    }
    return vector;
  }

  Future<void> deleteCustomSign(CustomSign sign) async {
    customSigns = customSigns.where((item) => item != sign).toList();
    await _localState.saveCustomSigns(customSigns);
    notifyListeners();
  }

  String _coordinateSpace(LandmarkFrame? frame) {
    if (frame == null || frame.handCoordinateAnalysis.isEmpty) {
      return 'normalized_3d';
    }
    final hasWorld = frame.handCoordinateAnalysis.any(
      (analysis) => analysis.coordinateSpace == 'world_wrist_centered',
    );
    return hasWorld
        ? 'world_3d_wrist_centered'
        : 'image_normalized_wrist_centered';
  }

  double _handSpan(TrackedHand hand) {
    final wrist = hand.landmarks.first;
    final middleMcp = hand.landmarks[9];
    final indexMcp = hand.landmarks[5];
    final pinkyMcp = hand.landmarks[17];
    final span =
        ((middleMcp.x - wrist.x).abs() +
            (middleMcp.y - wrist.y).abs() +
            (indexMcp.x - pinkyMcp.x).abs()) /
        3;
    return span.clamp(.08, 1.0);
  }

  @override
  void dispose() {
    _frameNotifyTimer?.cancel();
    _trackingSubscription.cancel();
    tracking.dispose();
    devices.dispose();
    apiClient?.close();
    super.dispose();
  }
}
