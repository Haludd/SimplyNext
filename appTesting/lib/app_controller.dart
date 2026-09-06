import 'dart:async';

import 'package:flutter/foundation.dart';

import 'models/tracking_models.dart';
import 'services/device_access_service.dart';
import 'services/local_state_service.dart';
import 'services/tracking_service.dart';

enum SignBridgePage { onboarding, live, dictionary, settings }

enum ViewMode { raw, wireframe, clean }

class AppController extends ChangeNotifier {
  AppController(this._localState, this.tracking, this.devices) {
    _trackingSubscription = tracking.frames.listen((_) => notifyListeners());
    devices.addListener(_onDeviceStateChanged);
    unawaited(_restoreState());
  }

  final LocalStateService _localState;
  final TrackingService tracking;
  final DeviceAccessService devices;

  late final StreamSubscription<LandmarkFrame> _trackingSubscription;
  SignBridgePage page = SignBridgePage.onboarding;
  ViewMode viewMode = ViewMode.wireframe;
  int calibrationStep = 1;
  bool calibrated = false;
  bool audioEnabled = true;
  bool isPaused = false;
  bool isUnregisteredSign = false;
  List<CustomSign> customSigns = <CustomSign>[];

  LandmarkFrame? get latestFrame => tracking.latestFrame;
  AlignmentResult get alignment => AlignmentEvaluator().evaluate(
    latestFrame ??
        LandmarkFrame(timestamp: DateTime.fromMillisecondsSinceEpoch(0)),
  );
  double get confidence => latestFrame?.trackingConfidence ?? 0;
  String get confidenceWindowLabel => tracking.confidenceWindow.windowLabel;

  void _onDeviceStateChanged() => notifyListeners();

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

  /// Resets the MediaPipe and temporal Stage 3/4 state before starting a new
  /// camera stream.
  Future<void> restartCamera() async {
    try {
      await tracking.stop();
    } catch (_) {
      // A browser may already have closed a suspended camera stream.
    }
    if (kIsWeb) {
      devices.markWebCameraUnavailable('Restarting camera...');
    }
    await requestCamera();
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
    final sign = CustomSign(
      label: label,
      samples: samples,
      createdAt: DateTime.now(),
    );
    customSigns = <CustomSign>[...customSigns, sign];
    await _localState.saveCustomSigns(customSigns);
    notifyListeners();
  }

  @override
  void dispose() {
    _trackingSubscription.cancel();
    devices.removeListener(_onDeviceStateChanged);
    tracking.dispose();
    devices.dispose();
    super.dispose();
  }
}
