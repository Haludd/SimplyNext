import 'dart:async';

import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:permission_handler/permission_handler.dart';

class DeviceAccessService extends ChangeNotifier {
  CameraController? cameraController;
  PermissionStatus microphonePermission = PermissionStatus.denied;
  bool isTestingMicrophone = false;
  String cameraName = 'Default camera';
  String cameraStatus = 'Not enabled';

  bool get cameraReady => cameraController?.value.isInitialized == true;
  String get microphoneStatus =>
      microphonePermission == PermissionStatus.granted
      ? 'Ready'
      : 'Permission needed';

  Future<void> enableCamera() async {
    final permission = await Permission.camera.request();
    if (!permission.isGranted) {
      cameraStatus = 'Permission needed';
      notifyListeners();
      return;
    }

    try {
      final available = await availableCameras();
      if (available.isEmpty) {
        cameraStatus = 'No camera found';
        notifyListeners();
        return;
      }
      final selected = available.firstWhere(
        (camera) => camera.lensDirection == CameraLensDirection.front,
        orElse: () => available.first,
      );
      await cameraController?.dispose();
      final controller = CameraController(
        selected,
        ResolutionPreset.medium,
        enableAudio: false,
      );
      await controller.initialize();
      cameraController = controller;
      cameraName = selected.name;
      cameraStatus = 'Ready';
    } on CameraException catch (error) {
      cameraStatus = error.description ?? error.code;
    } catch (_) {
      cameraStatus = 'Camera unavailable';
    }
    notifyListeners();
  }

  Future<void> enableMicrophone() async {
    microphonePermission = await Permission.microphone.request();
    notifyListeners();
  }

  Future<void> testMicrophone() async {
    if (!microphonePermission.isGranted) {
      await enableMicrophone();
    }
    if (!microphonePermission.isGranted) return;
    isTestingMicrophone = true;
    notifyListeners();
    await Future<void>.delayed(const Duration(seconds: 2));
    isTestingMicrophone = false;
    notifyListeners();
  }

  @override
  void dispose() {
    unawaited(cameraController?.dispose());
    cameraController = null;
    super.dispose();
  }
}
