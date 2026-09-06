import 'package:apptesting/main.dart';
import 'package:apptesting/app_controller.dart';
import 'package:apptesting/services/device_access_service.dart';
import 'package:apptesting/services/local_state_service.dart';
import 'package:apptesting/services/tracking_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('shows the first calibration step on a fresh launch', (
    tester,
  ) async {
    SharedPreferences.setMockInitialValues(<String, Object>{});
    final preferences = await SharedPreferences.getInstance();
    final controller = AppController(
      LocalStateService(preferences),
      DemoTrackingService(),
      DeviceAccessService(),
    );
    await tester.pumpWidget(SignBridgeApp(controller: controller));

    expect(find.text('Get started now'), findsOneWidget);
    expect(find.text('STEP 1 OF 3'), findsOneWidget);

    await tester.pumpWidget(const SizedBox.shrink());
    controller.dispose();
  });

  testWidgets('opens voice captions without camera calibration', (
    tester,
  ) async {
    SharedPreferences.setMockInitialValues(<String, Object>{});
    final preferences = await SharedPreferences.getInstance();
    final controller = AppController(
      LocalStateService(preferences),
      DemoTrackingService(),
      DeviceAccessService(),
    );
    await tester.pumpWidget(SignBridgeApp(controller: controller));

    expect(controller.calibrated, isFalse);
    final voiceCaptionsAction = find.byKey(
      const ValueKey<String>('open-voice-captions'),
    );
    await tester.ensureVisible(voiceCaptionsAction);
    await tester.pump();
    await tester.tap(voiceCaptionsAction);
    await tester.pump();

    expect(controller.page, SignBridgePage.live);
    expect(controller.calibrated, isFalse);
    expect(
      find.byKey(const ValueKey<String>('speech-caption-card')),
      findsOneWidget,
    );
    expect(find.text('Start listening'), findsOneWidget);
    expect(find.text('Start camera calibration'), findsOneWidget);

    await tester.pumpWidget(const SizedBox.shrink());
    controller.dispose();
  });
}
