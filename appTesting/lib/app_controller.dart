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
    _trackingSubscription = tracking.frames.listen((_) => notifyListeners());
    unawaited(_restoreState());
  }

  final LocalStateService _localState;
  final TrackingService tracking;
  final DeviceAccessService devices;
  final SignSequenceApiClient? apiClient;
  final SignAnalysisService signAnalyzer = SignAnalysisService();
  final SimulatedSignSequenceApiClient simulator =
      SimulatedSignSequenceApiClient();
  final String sessionId = 'session-${DateTime.now().millisecondsSinceEpoch}';

  late final StreamSubscription<LandmarkFrame> _trackingSubscription;
  SignBridgePage page = SignBridgePage.onboarding;
  ViewMode viewMode = ViewMode.wireframe;
  int calibrationStep = 1;
  bool calibrated = false;
  bool audioEnabled = true;
  bool isPaused = false;
  bool isUnregisteredSign = false;
  List<CustomSign> customSigns = <CustomSign>[];
  SignAnalysisResult? latestAnalysis;
  bool analysisInFlight = false;
  String backendStatus = 'Offline simulation · no backend configured';
  String selectedLanguage = 'ASL';

  LandmarkFrame? get latestFrame => tracking.latestFrame;
  AlignmentResult get alignment => AlignmentEvaluator().evaluate(
    latestFrame ??
        LandmarkFrame(timestamp: DateTime.fromMillisecondsSinceEpoch(0)),
  );
  double get confidence => latestFrame?.trackingConfidence ?? 0;
  String get confidenceWindowLabel => tracking.confidenceWindow.windowLabel;
  String get trackingStatus => tracking.status;

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
        // The UI keeps the camera permission state visible; the web bridge
        // reports a more specific browser error in its own console.
      }
    }
    notifyListeners();
  }

  Future<void> analyzeSign() async {
    final frames = tracking.recentFrames;
    latestAnalysis = signAnalyzer.analyze(frames);
    backendStatus = apiClient == null
        ? 'Preparing offline backend simulation'
        : 'Preparing sequence for backend';
    notifyListeners();
    if (frames.isEmpty) {
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
  /// The live API keeps every raw landmark. My Signs additionally stores a
  /// stable wrist-centred vector for each left/right hand, motion features,
  /// and facial-expression scores so a later sequence model can compare a
  /// user's examples without depending on camera position.
  List<double>? captureCurrentSignSample() {
    final frame = latestFrame;
    if (frame == null ||
        frame.trackingConfidence < .70 ||
        frame.hands.isEmpty) {
      return null;
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

    final motion = frame.handMotion;
    final face = frame.faceExpression;
    vector.addAll(<double>[
      motion?.averageSpeed ?? 0,
      motion?.averageAcceleration ?? 0,
      motion?.averageOpenness ?? 0,
    ]);
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
    _trackingSubscription.cancel();
    tracking.dispose();
    devices.dispose();
    apiClient?.close();
    super.dispose();
  }
}
