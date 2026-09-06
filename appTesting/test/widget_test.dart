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

  testWidgets('shows the single live page with an open-camera action', (
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

    await tester.pumpAndSettle();

    expect(find.text('Live translator'), findsOneWidget);
    expect(find.text('Open camera'), findsOneWidget);
    expect(find.text('My signs'), findsNothing);
    expect(find.text('Settings'), findsNothing);

    await tester.pumpWidget(const SizedBox.shrink());
    controller.dispose();
  });
}
