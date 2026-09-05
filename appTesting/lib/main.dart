import 'package:permission_handler/permission_handler.dart';
import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'app_controller.dart';
import 'models/face_tracking_models.dart';
import 'models/hand_tracking_models.dart';
import 'models/tracking_models.dart';
import 'services/device_access_service.dart';
import 'services/local_state_service.dart';
import 'services/api_client.dart';
import 'services/sign_analysis_service.dart';
import 'services/web_tracking_service.dart';
import 'services/tracking_service.dart';
import 'ui/web_camera_preview.dart';

const _background = Color(0xFF07111F);
const _surface = Color(0xFF102235);
const _surfaceRaised = Color(0xFF162B3D);
const _cyan = Color(0xFF4EDDEA);
const _mint = Color(0xFF70E2B3);
const _yellow = Color(0xFFFFC857);
const _red = Color(0xFFFF718A);
const _muted = Color(0xFF91A6B8);
const _subtle = Color(0xFF657B8D);

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final preferences = await SharedPreferences.getInstance();
  const backendEnabled = bool.fromEnvironment(
    'SIGNBRIDGE_ENABLE_BACKEND',
    defaultValue: false,
  );
  final backendUrl = const String.fromEnvironment('SIGNBRIDGE_API_URL');
  final apiClient = !backendEnabled || backendUrl.isEmpty
      ? null
      : SignSequenceApiClient(baseUri: Uri.parse(backendUrl));
  runApp(
    SignBridgeApp(
      controller: AppController(
        LocalStateService(preferences),
        kIsWeb ? WebTrackingService() : DemoTrackingService(),
        DeviceAccessService(),
        apiClient: apiClient,
      ),
    ),
  );
}

class SignBridgeApp extends StatelessWidget {
  const SignBridgeApp({super.key, required this.controller});

  final AppController controller;

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) => MaterialApp(
        debugShowCheckedModeBanner: false,
        title: 'SignBridge',
        theme: ThemeData(
          brightness: Brightness.dark,
          scaffoldBackgroundColor: _background,
          colorScheme: const ColorScheme.dark(
            primary: _cyan,
            secondary: _mint,
            surface: _surface,
          ),
          fontFamily: 'Avenir Next',
          useMaterial3: true,
          appBarTheme: const AppBarTheme(
            backgroundColor: _background,
            elevation: 0,
          ),
          inputDecorationTheme: InputDecorationTheme(
            filled: true,
            fillColor: _background,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.all(Radius.circular(12)),
              borderSide: BorderSide(color: Colors.white12),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.all(Radius.circular(12)),
              borderSide: BorderSide(color: Colors.white12),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.all(Radius.circular(12)),
              borderSide: BorderSide(color: _cyan),
            ),
          ),
        ),
        home: AppShell(controller: controller),
      ),
    );
  }
}

class AppShell extends StatelessWidget {
  const AppShell({super.key, required this.controller});

  final AppController controller;

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge(<Listenable>[controller, controller.devices]),
      builder: (context, _) {
        final isMobile = MediaQuery.sizeOf(context).width < 760;
        final screens = <Widget>[
          OnboardingScreen(controller: controller),
          LiveTranslatorScreen(controller: controller),
          DictionaryScreen(controller: controller),
          SettingsScreen(controller: controller),
        ];
        final index = controller.page == SignBridgePage.onboarding
            ? 0
            : controller.page == SignBridgePage.live
            ? 1
            : controller.page == SignBridgePage.dictionary
            ? 2
            : 3;
        return Scaffold(
          body: SafeArea(
            child: Row(
              children: <Widget>[
                if (!isMobile) _SideRail(controller: controller),
                Expanded(
                  child: Column(
                    children: <Widget>[
                      const _TopBar(),
                      Expanded(
                        child: IndexedStack(index: index, children: screens),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          bottomNavigationBar: isMobile && controller.calibrated
              ? NavigationBar(
                  selectedIndex: index == 0 ? 0 : index - 1,
                  onDestinationSelected: (value) => controller.navigate(
                    <SignBridgePage>[
                      SignBridgePage.live,
                      SignBridgePage.dictionary,
                      SignBridgePage.settings,
                    ][value],
                  ),
                  destinations: const <NavigationDestination>[
                    NavigationDestination(
                      icon: Icon(Icons.center_focus_strong),
                      label: 'Live',
                    ),
                    NavigationDestination(
                      icon: Icon(Icons.auto_awesome),
                      label: 'My signs',
                    ),
                    NavigationDestination(
                      icon: Icon(Icons.tune),
                      label: 'Settings',
                    ),
                  ],
                )
              : null,
        );
      },
    );
  }
}

class _SideRail extends StatelessWidget {
  const _SideRail({required this.controller});
  final AppController controller;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 244,
      padding: const EdgeInsets.fromLTRB(18, 28, 18, 20),
      decoration: const BoxDecoration(
        border: Border(right: BorderSide(color: Colors.white12)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          const SignBridgeLogo(),
          const SizedBox(height: 56),
          const _Eyebrow('Workspace'),
          const SizedBox(height: 12),
          _RailItem(
            icon: Icons.center_focus_strong,
            label: 'Live translator',
            selected: controller.page == SignBridgePage.live,
            onTap: () => controller.navigate(SignBridgePage.live),
          ),
          _RailItem(
            icon: Icons.auto_awesome,
            label: 'My signs',
            selected: controller.page == SignBridgePage.dictionary,
            onTap: () => controller.navigate(SignBridgePage.dictionary),
          ),
          _RailItem(
            icon: Icons.tune,
            label: 'Settings',
            selected: controller.page == SignBridgePage.settings,
            onTap: () => controller.navigate(SignBridgePage.settings),
          ),
          const Spacer(),
          const _PrivacyNote(),
          const SizedBox(height: 12),
          TextButton.icon(
            onPressed: () => controller.navigate(SignBridgePage.settings),
            icon: const CircleAvatar(
              radius: 15,
              backgroundColor: Color(0xFF91DCD7),
              child: Text(
                'E',
                style: TextStyle(
                  color: _background,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
            label: const Align(
              alignment: Alignment.centerLeft,
              child: Text(
                'Esther\nPersonal workspace',
                style: TextStyle(fontSize: 11, height: 1.5),
              ),
            ),
            style: TextButton.styleFrom(foregroundColor: Colors.white),
          ),
        ],
      ),
    );
  }
}

class _RailItem extends StatelessWidget {
  const _RailItem({
    required this.icon,
    required this.label,
    required this.selected,
    required this.onTap,
  });
  final IconData icon;
  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 5),
    child: ListTile(
      onTap: onTap,
      dense: true,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      selected: selected,
      selectedTileColor: _cyan.withValues(alpha: .1),
      iconColor: selected ? _cyan : _subtle,
      textColor: selected ? Colors.white : _muted,
      leading: Icon(icon, size: 19),
      title: Text(
        label,
        style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
      ),
    ),
  );
}

class _TopBar extends StatelessWidget {
  const _TopBar();

  @override
  Widget build(BuildContext context) => Container(
    height: 76,
    padding: const EdgeInsets.symmetric(horizontal: 28),
    decoration: const BoxDecoration(
      border: Border(bottom: BorderSide(color: Colors.white12)),
    ),
    child: LayoutBuilder(
      builder: (context, constraints) {
        final compact = constraints.maxWidth < 600;
        return Row(
          children: <Widget>[
            const SignBridgeLogo(compact: true),
            const Spacer(),
            if (!compact) ...<Widget>[
              const Text(
                'Workspace  /  ',
                style: TextStyle(color: _subtle, fontSize: 12),
              ),
              const Text(
                'SignBridge',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(width: 18),
            ],
            IconButton(
              onPressed: () {},
              icon: const Icon(Icons.help_outline, size: 18, color: _muted),
              tooltip: 'Help',
            ),
            const CircleAvatar(
              radius: 14,
              backgroundColor: Color(0xFF91DCD7),
              child: Text(
                'E',
                style: TextStyle(
                  color: _background,
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
          ],
        );
      },
    ),
  );
}

class SignBridgeLogo extends StatelessWidget {
  const SignBridgeLogo({super.key, this.compact = false});
  final bool compact;

  @override
  Widget build(BuildContext context) => FittedBox(
    fit: BoxFit.scaleDown,
    alignment: Alignment.centerLeft,
    child: Row(
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        Container(
          width: compact ? 28 : 34,
          height: compact ? 28 : 34,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(10),
            color: _cyan.withValues(alpha: .12),
            border: Border.all(color: _cyan.withValues(alpha: .45)),
          ),
          child: const Icon(Icons.sign_language, color: _cyan, size: 20),
        ),
        const SizedBox(width: 9),
        Text.rich(
          TextSpan(
            text: 'Sign',
            style: TextStyle(
              fontSize: compact ? 16 : 19,
              fontWeight: FontWeight.w800,
              letterSpacing: -0.8,
            ),
            children: const <TextSpan>[
              TextSpan(
                text: 'Bridge',
                style: TextStyle(color: _cyan),
              ),
            ],
          ),
        ),
      ],
    ),
  );
}

class _PrivacyNote extends StatelessWidget {
  const _PrivacyNote();

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(12),
    decoration: BoxDecoration(
      color: _mint.withValues(alpha: .05),
      borderRadius: BorderRadius.circular(12),
      border: Border.all(color: _mint.withValues(alpha: .18)),
    ),
    child: const Row(
      children: <Widget>[
        Icon(Icons.verified_user_outlined, size: 18, color: _mint),
        SizedBox(width: 9),
        Expanded(
          child: Text(
            'Private by default\nOn-device inference enabled',
            style: TextStyle(color: _mint, fontSize: 10, height: 1.5),
          ),
        ),
      ],
    ),
  );
}

class _Eyebrow extends StatelessWidget {
  const _Eyebrow(this.text);
  final String text;

  @override
  Widget build(BuildContext context) => Text(
    text.toUpperCase(),
    style: const TextStyle(
      color: _subtle,
      fontSize: 10,
      letterSpacing: 1.5,
      fontFamily: 'monospace',
    ),
  );
}

class _ScreenFrame extends StatelessWidget {
  const _ScreenFrame({
    required this.child,
    required this.eyebrow,
    required this.title,
    required this.subtitle,
    this.action,
  });
  final Widget child;
  final String eyebrow;
  final String title;
  final String subtitle;
  final Widget? action;

  @override
  Widget build(BuildContext context) => SingleChildScrollView(
    padding: const EdgeInsets.fromLTRB(28, 38, 28, 44),
    child: Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 1120),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: <Widget>[
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(
                        eyebrow.toUpperCase(),
                        style: const TextStyle(
                          color: _subtle,
                          fontSize: 10,
                          letterSpacing: 1.4,
                          fontFamily: 'monospace',
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        title,
                        style: const TextStyle(
                          fontSize: 34,
                          fontWeight: FontWeight.w800,
                          letterSpacing: -1.6,
                        ),
                      ),
                      const SizedBox(height: 9),
                      Text(
                        subtitle,
                        style: const TextStyle(color: _muted, fontSize: 14),
                      ),
                    ],
                  ),
                ),
                ?action,
              ],
            ),
            const SizedBox(height: 30),
            child,
          ],
        ),
      ),
    ),
  );
}

class GlassCard extends StatelessWidget {
  const GlassCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(20),
    this.margin,
  });
  final Widget child;
  final EdgeInsets padding;
  final EdgeInsets? margin;

  @override
  Widget build(BuildContext context) => Container(
    margin: margin,
    padding: padding,
    decoration: BoxDecoration(
      gradient: const LinearGradient(
        colors: <Color>[_surfaceRaised, _surface],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ),
      borderRadius: BorderRadius.circular(18),
      border: Border.all(color: Colors.white.withValues(alpha: .12)),
      boxShadow: <BoxShadow>[
        BoxShadow(
          color: Colors.black.withValues(alpha: .16),
          blurRadius: 35,
          offset: const Offset(0, 16),
        ),
      ],
    ),
    child: child,
  );
}

class PrimaryButton extends StatelessWidget {
  const PrimaryButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon = Icons.arrow_forward,
  });
  final String label;
  final VoidCallback? onPressed;
  final IconData icon;

  @override
  Widget build(BuildContext context) => FilledButton.icon(
    onPressed: onPressed,
    icon: Icon(icon, size: 17),
    label: Text(label),
    style: FilledButton.styleFrom(
      backgroundColor: _cyan,
      foregroundColor: _background,
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(11)),
      textStyle: const TextStyle(fontWeight: FontWeight.w800, fontSize: 12),
    ),
  );
}

class OutlineButton extends StatelessWidget {
  const OutlineButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
  });
  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;

  @override
  Widget build(BuildContext context) => OutlinedButton.icon(
    onPressed: onPressed,
    icon: icon == null ? const SizedBox.shrink() : Icon(icon, size: 16),
    label: Text(label),
    style: OutlinedButton.styleFrom(
      foregroundColor: _muted,
      side: const BorderSide(color: Colors.white12),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      textStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
    ),
  );
}

class OnboardingScreen extends StatelessWidget {
  const OnboardingScreen({super.key, required this.controller});
  final AppController controller;

  @override
  Widget build(BuildContext context) {
    final step = controller.calibrationStep;
    final isCameraReady = controller.devices.cameraReady;
    final alignment = controller.alignment;
    final canContinue =
        isCameraReady &&
        (alignment.isAligned || controller.latestFrame?.handsVisible == true) &&
        (step < 2 ||
            controller.latestFrame?.armsVisible == true ||
            controller.latestFrame?.handsVisible == true) &&
        (step < 3 || controller.latestFrame?.handsVisible == true);
    final steps = <({String label, String detail})>[
      (
        label: 'Position shoulders inside frame',
        detail: 'Keep your shoulders centred and about an arm\'s length from the camera.',
      ),
      (
        label: 'Keep your signing space visible',
        detail: 'Raise both hands into frame so we can establish your movement area.',
      ),
      (
        label: 'Hold still for a moment',
        detail: 'We\'re saving your personal camera baseline. This takes only a few seconds.',
      ),
    ];
    return _ScreenFrame(
      eyebrow: 'Welcome to SignBridge',
      title: 'Get started now',
      subtitle: 'Translate your movements into text in real time',
      child: GlassCard(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            const _Eyebrow('Quick calibration'),
            const SizedBox(height: 8),
            const Text(
              'Before you start, we\'ll calibrate the camera to your position so SignBridge can accurately track your movements.',
              style: TextStyle(color: _muted, fontSize: 13, height: 1.5),
            ),
            const SizedBox(height: 22),
            Row(
              children: <Widget>[
                Text(
                  'STEP $step OF 3',
                  style: const TextStyle(
                    color: _cyan,
                    fontSize: 12,
                    letterSpacing: 1.2,
                    fontWeight: FontWeight.w800,
                    fontFamily: 'monospace',
                  ),
                ),
                const Spacer(),
                Text(
                  'One-time setup',
                  style: const TextStyle(color: _subtle, fontSize: 11),
                ),
              ],
            ),
            const SizedBox(height: 9),
            LinearProgressIndicator(
              value: step / 3,
              minHeight: 4,
              backgroundColor: const Color(0xFF294052),
              color: _cyan,
              borderRadius: BorderRadius.circular(8),
            ),
            const SizedBox(height: 23),
            if (step == 1) ...<Widget>[
              const Text(
                'Sign language options',
                style: TextStyle(
                  color: _subtle,
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 7),
              DropdownButtonFormField<String>(
                initialValue: controller.selectedLanguage,
                isExpanded: true,
                items: const <DropdownMenuItem<String>>[
                  DropdownMenuItem(
                    value: 'ASL',
                    child: Text('ASL · American Sign Language'),
                  ),
                  DropdownMenuItem(
                    value: 'SgSL',
                    child: Text('SgSL · Singapore Sign Language'),
                  ),
                  DropdownMenuItem(
                    value: 'BSL',
                    child: Text('BSL · British Sign Language'),
                  ),
                ],
                onChanged: (value) {
                  if (value != null) controller.setLanguage(value);
                },
                icon: const Icon(Icons.keyboard_arrow_down, color: _cyan),
                decoration: const InputDecoration(
                  contentPadding: EdgeInsets.symmetric(
                    horizontal: 14,
                    vertical: 2,
                  ),
                ),
              ),
              const SizedBox(height: 20),
            ],
            Row(
              children: <Widget>[
                Icon(
                  alignment.isAligned ? Icons.check_circle : Icons.info_outline,
                  size: 17,
                  color: alignment.isAligned ? _mint : _yellow,
                ),
                const SizedBox(width: 7),
                Expanded(
                  child: Text(
                    step == 1 ? alignment.message : steps[step - 1].label,
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
                      color: alignment.isAligned ? _mint : Colors.white,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 5),
            Text(
              step == 1 ? alignment.detail : steps[step - 1].detail,
              style: const TextStyle(color: _muted, fontSize: 12),
            ),
            const SizedBox(height: 14),
            TrackingPreview(
              controller: controller,
              height: 300,
              showLabels: true,
              showCalibrationGuide: true,
            ),
            const SizedBox(height: 14),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: <Widget>[
                _CheckChip(
                  label: 'Shoulders detected',
                  checked: controller.latestFrame?.shouldersVisible == true,
                ),
                _CheckChip(
                  label: 'Arms visible',
                  checked: controller.latestFrame?.armsVisible == true,
                ),
                _CheckChip(
                  label: 'Lighting: Good',
                  checked:
                      controller.latestFrame?.lightingScore == null ||
                      controller.latestFrame!.lightingScore > .6,
                ),
              ],
            ),
            if (!isCameraReady) ...<Widget>[
              const SizedBox(height: 14),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: _yellow.withValues(alpha: .06),
                  borderRadius: BorderRadius.circular(11),
                  border: Border.all(color: _yellow.withValues(alpha: .2)),
                ),
                child: const Row(
                  children: <Widget>[
                    Icon(Icons.videocam_outlined, color: _yellow, size: 18),
                    SizedBox(width: 9),
                    Expanded(
                      child: Text(
                        'Camera permission is needed for calibration and translation.',
                        style: TextStyle(color: _muted, fontSize: 11),
                      ),
                    ),
                  ],
                ),
              ),
            ],
            const SizedBox(height: 18),
            PrimaryButton(
              label: isCameraReady
                  ? (step == 3 ? 'Complete calibration' : 'Continue')
                  : 'Enable camera',
              icon: isCameraReady
                  ? Icons.arrow_forward
                  : Icons.videocam_outlined,
              onPressed: !isCameraReady
                  ? () async {
                      await controller.requestCamera();
                    }
                  : canContinue
                  ? () async {
                      await controller.completeCalibrationStep();
                    }
                  : null,
            ),
          ],
        ),
      ),
    );
  }
}

class _CheckChip extends StatelessWidget {
  const _CheckChip({required this.label, required this.checked});
  final String label;
  final bool checked;

  @override
  Widget build(BuildContext context) => Chip(
    avatar: Icon(
      checked ? Icons.check : Icons.remove,
      size: 13,
      color: checked ? _mint : _subtle,
    ),
    label: Text(label),
    labelStyle: TextStyle(color: checked ? _mint : _muted, fontSize: 10),
    backgroundColor: (checked ? _mint : _subtle).withValues(alpha: .08),
    side: BorderSide(color: (checked ? _mint : _subtle).withValues(alpha: .2)),
  );
}

class TrackingPreview extends StatelessWidget {
  const TrackingPreview({
    super.key,
    required this.controller,
    this.height = 390,
    this.showLabels = false,
    this.showCalibrationGuide = false,
  });
  final AppController controller;
  final double height;
  final bool showLabels;
  final bool showCalibrationGuide;

  @override
  Widget build(BuildContext context) => ClipRRect(
    borderRadius: BorderRadius.circular(14),
    child: SizedBox(
      height: height,
      child: Stack(
        fit: StackFit.expand,
        children: <Widget>[
          if (controller.devices.cameraReady)
            kIsWeb
                ? WebCameraPreview()
                : CameraPreview(controller.devices.cameraController!)
          else
            const CustomPaint(painter: _PreviewBackgroundPainter()),
          if (controller.viewMode != ViewMode.raw &&
              controller.devices.cameraReady)
            CustomPaint(
              painter: LandmarkPainter(
                controller.latestFrame,
                showCalibrationGuide: showCalibrationGuide,
              ),
            ),
          if (controller.viewMode == ViewMode.wireframe &&
              controller.devices.cameraReady)
            CustomPaint(painter: HandSkeletonPainter(controller.latestFrame)),
          if (showLabels)
            const Positioned(
              left: 15,
              top: 14,
              child: Text(
                'CALIBRATION VIEW',
                style: TextStyle(
                  color: Color(0xB3DDFBFC),
                  fontSize: 9,
                  letterSpacing: 1.2,
                  fontFamily: 'monospace',
                ),
              ),
            ),
        ],
      ),
    ),
  );
}

class _PreviewBackgroundPainter extends CustomPainter {
  const _PreviewBackgroundPainter();
  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    canvas.drawRect(rect, Paint()..color = const Color(0xFF0C2030));
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class LandmarkPainter extends CustomPainter {
  LandmarkPainter(this.frame, {this.showCalibrationGuide = false});
  final LandmarkFrame? frame;
  final bool showCalibrationGuide;

  @override
  void paint(Canvas canvas, Size size) {
    final pointPaint = Paint()
      ..color = _cyan
      ..style = PaintingStyle.fill;
    final linePaint = Paint()
      ..color = _cyan.withValues(alpha: .55)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.2;
    final points = <NormalizedPoint?>[
      frame?.leftShoulder,
      frame?.rightShoulder,
      frame?.leftWrist,
      frame?.rightWrist,
    ];
    final personDetected =
        frame != null &&
        (frame!.poseLandmarks.isNotEmpty ||
            frame!.hands.isNotEmpty ||
            frame!.faceUpperLandmarks.isNotEmpty ||
            frame!.faceMouthLandmarks.isNotEmpty);
    if (showCalibrationGuide &&
        personDetected &&
        points.every((point) => point == null)) {
      points.addAll(const <NormalizedPoint>[
        NormalizedPoint(x: .39, y: .35),
        NormalizedPoint(x: .61, y: .35),
        NormalizedPoint(x: .25, y: .72),
        NormalizedPoint(x: .75, y: .72),
      ]);
    }
    final visiblePoints = points.whereType<NormalizedPoint>().toList();
    if (visiblePoints.length >= 2) {
      final shoulderLeft = _offset(visiblePoints[0], size);
      final shoulderRight = _offset(visiblePoints[1], size);
      canvas.drawLine(shoulderLeft, shoulderRight, linePaint);
      if (visiblePoints.length >= 4) {
        canvas.drawLine(
          shoulderLeft,
          _offset(visiblePoints[2], size),
          linePaint,
        );
        canvas.drawLine(
          shoulderRight,
          _offset(visiblePoints[3], size),
          linePaint,
        );
      }
    }
    for (final point in visiblePoints) {
      final offset = _offset(point, size);
      canvas.drawCircle(offset, 5, pointPaint);
      canvas.drawCircle(
        offset,
        10,
        Paint()..color = _cyan.withValues(alpha: .15),
      );
    }

    // Draw the curated pose world as a connected upper-body skeleton.
    final pose = frame?.poseLandmarks ?? const <PoseLandmark>[];
    final poseByIndex = <int, PoseLandmark>{
      for (final landmark in pose) landmark.index: landmark,
    };
    final poseEdges = <List<int>>[
      <int>[11, 13],
      <int>[13, 15],
      <int>[12, 14],
      <int>[14, 16],
      <int>[11, 12],
      <int>[11, 23],
      <int>[12, 24],
      <int>[23, 24],
      <int>[23, 25],
      <int>[24, 26],
    ];
    for (final edge in poseEdges) {
      final first = poseByIndex[edge[0]];
      final second = poseByIndex[edge[1]];
      if (first == null || second == null) continue;
      canvas.drawLine(
        _worldOffset(first.x, first.y, size),
        _worldOffset(second.x, second.y, size),
        linePaint,
      );
    }
    for (final landmark in pose) {
      canvas.drawCircle(
        _worldOffset(landmark.x, landmark.y, size),
        3.5,
        pointPaint,
      );
    }

    // Face points use different colours so it is obvious which points belong
    // to the upper-face and mouth worlds.
    for (final landmark
        in frame?.faceUpperLandmarks ?? const <FaceLandmark>[]) {
      canvas.drawCircle(
        _worldOffset(landmark.x, landmark.y, size),
        2.5,
        Paint()..color = _yellow,
      );
    }
    for (final landmark
        in frame?.faceMouthLandmarks ?? const <FaceLandmark>[]) {
      canvas.drawCircle(
        _worldOffset(landmark.x, landmark.y, size),
        2.5,
        Paint()..color = _mint,
      );
    }
  }

  Offset _offset(NormalizedPoint point, Size size) =>
      Offset((1 - point.x) * size.width, point.y * size.height);

  Offset _worldOffset(double x, double y, Size size) =>
      Offset((1 - x) * size.width, y * size.height);
  @override
  bool shouldRepaint(covariant LandmarkPainter oldDelegate) =>
      oldDelegate.frame != frame;
}

class HandSkeletonPainter extends CustomPainter {
  HandSkeletonPainter(this.frame);
  final LandmarkFrame? frame;

  @override
  void paint(Canvas canvas, Size size) {
    final hands = frame?.hands ?? const <TrackedHand>[];
    for (final hand in hands) {
      final color = hand.handedness == Handedness.left ? _mint : _cyan;
      final linePaint = Paint()
        ..color = color.withValues(alpha: .8)
        ..strokeWidth = 2
        ..style = PaintingStyle.stroke;
      final pointPaint = Paint()..color = color;
      for (final edge in handLandmarkEdges) {
        if (edge.any((index) => index >= hand.landmarks.length)) continue;
        canvas.drawLine(
          _project(hand.landmarks[edge[0]], size),
          _project(hand.landmarks[edge[1]], size),
          linePaint,
        );
      }
      for (final landmark in hand.landmarks) {
        final point = _project(landmark, size);
        final radius = (4.5 - landmark.z.abs() * 8).clamp(2.5, 5.5);
        canvas.drawCircle(point, radius, pointPaint);
        canvas.drawCircle(
          point,
          radius + 4,
          Paint()..color = color.withValues(alpha: .12),
        );
      }
    }
  }

  Offset _project(HandLandmark landmark, Size size) => Offset(
    (1 - landmark.x - landmark.z * .12) * size.width,
    (landmark.y - landmark.z * .08) * size.height,
  );

  @override
  bool shouldRepaint(covariant HandSkeletonPainter oldDelegate) =>
      oldDelegate.frame != frame;
}

class LiveTranslatorScreen extends StatelessWidget {
  const LiveTranslatorScreen({super.key, required this.controller});
  final AppController controller;

  @override
  Widget build(BuildContext context) {
    if (!controller.calibrated) {
      return _ScreenFrame(
        eyebrow: 'Camera access required',
        title: 'Live translator',
        subtitle: 'Complete the one-time calibration before translating.',
        child: GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              const Icon(Icons.center_focus_strong, color: _cyan, size: 34),
              const SizedBox(height: 16),
              const Text(
                'Let\'s set up your camera position first.',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 8),
              const Text(
                'Your calibration is saved locally and won\'t be required again on your next launch.',
                style: TextStyle(color: _muted),
              ),
              const SizedBox(height: 22),
              PrimaryButton(
                label: 'Start calibration',
                onPressed: () => controller.navigate(SignBridgePage.onboarding),
              ),
            ],
          ),
        ),
      );
    }
    return _ScreenFrame(
      eyebrow: 'Good afternoon, Esther',
      title: 'Live translator',
      subtitle: 'Sign naturally. We\'ll take care of the words.',
      action: Wrap(
        spacing: 10,
        children: <Widget>[
          _StatusPill(
            label: controller.trackingStatus,
            color: controller.trackingStatus.contains('MediaPipe')
                ? _mint
                : _yellow,
          ),
          OutlineButton(
            label: 'Practice mode',
            icon: Icons.open_in_new,
            onPressed: null,
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          GlassCard(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                Padding(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 6,
                    vertical: 5,
                  ),
                  child: Wrap(
                    alignment: WrapAlignment.spaceBetween,
                    crossAxisAlignment: WrapCrossAlignment.center,
                    spacing: 12,
                    runSpacing: 10,
                    children: <Widget>[
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: <Widget>[
                          const Icon(Icons.circle, color: _mint, size: 10),
                          const SizedBox(width: 9),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: <Widget>[
                              const Text(
                                'Tracking ready',
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                              Text(
                                'Pose + hands + face · ${controller.confidence == 0 ? 'Starting' : '${(controller.confidence * 100).round()}% confidence'}',
                                style: const TextStyle(
                                  color: _subtle,
                                  fontSize: 10,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                      Wrap(
                        spacing: 12,
                        crossAxisAlignment: WrapCrossAlignment.center,
                        children: <Widget>[
                          const _FpsBadge(),
                          _ViewToggle(controller: controller),
                        ],
                      ),
                    ],
                  ),
                ),
                TrackingPreview(controller: controller, height: 410),
                const SizedBox(height: 12),
                _HandAnalysisCard(controller: controller),
                const SizedBox(height: 12),
                _CaptionCard(controller: controller),
              ],
            ),
          ),
          const SizedBox(height: 18),
          _ActionDock(controller: controller),
          const SizedBox(height: 16),
          _SessionInsight(controller: controller),
        ],
      ),
    );
  }
}

class _HandAnalysisCard extends StatelessWidget {
  const _HandAnalysisCard({required this.controller});
  final AppController controller;

  @override
  Widget build(BuildContext context) {
    final frame = controller.latestFrame;
    final motion = frame?.handMotion;
    final face = frame?.faceExpression;
    int handPointCount(Handedness side) {
      for (final hand in frame?.hands ?? const <TrackedHand>[]) {
        if (hand.handedness == side) return hand.landmarks.length;
      }
      return 0;
    }

    final leftHandPoints = handPointCount(Handedness.left);
    final rightHandPoints = handPointCount(Handedness.right);
    final posePoints = frame?.poseLandmarks.length ?? 0;
    final upperFacePoints = frame?.faceUpperLandmarks.length ?? 0;
    final mouthPoints = frame?.faceMouthLandmarks.length ?? 0;
    final subject = frame?.subjectTracking;
    final faceModel = face?.source == 'hsemotion'
        ? 'HSEmotion'
        : face?.source == 'deepface'
        ? 'DeepFace'
        : 'Face model';
    final analysis = controller.latestAnalysis;
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 13),
      decoration: BoxDecoration(
        color: _mint.withValues(alpha: .045),
        borderRadius: BorderRadius.circular(13),
        border: Border.all(color: _mint.withValues(alpha: .18)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Row(
            children: <Widget>[
              const Icon(Icons.pan_tool_outlined, color: _mint, size: 17),
              const SizedBox(width: 8),
              const _Eyebrow('Hand signal'),
              const Spacer(),
              Text(
                '${frame?.hands.length ?? 0} / 2 hands · ${controller.utteranceFrameCount} utterance frames',
                style: const TextStyle(
                  color: _subtle,
                  fontSize: 10,
                  fontFamily: 'monospace',
                ),
              ),
            ],
          ),
          const SizedBox(height: 9),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: <Widget>[
              _WorldReadout(
                label: 'L hand',
                value: '$leftHandPoints / 21',
                active: leftHandPoints == 21,
              ),
              _WorldReadout(
                label: 'R hand',
                value: '$rightHandPoints / 21',
                active: rightHandPoints == 21,
              ),
              _WorldReadout(
                label: 'Pose',
                value: '$posePoints / 11',
                active: posePoints == 11,
              ),
              _WorldReadout(
                label: 'Face',
                value: '$upperFacePoints + $mouthPoints',
                active: upperFacePoints > 0 || mouthPoints > 0,
              ),
              _WorldReadout(
                label: 'Subject',
                value: subject?.locked != true
                    ? 'searching'
                    : subject?.visible == true
                    ? 'locked'
                    : 'locked · hidden',
                active: subject?.locked == true,
              ),
            ],
          ),
          const SizedBox(height: 11),
          Wrap(
            spacing: 12,
            runSpacing: 10,
            children: <Widget>[
              _Metric(
                label: 'Shape',
                value: analysis?.gestureLabel ?? 'Not read',
              ),
              _Metric(label: 'Motion', value: motion?.direction ?? 'Still'),
              _Metric(
                label: 'Open',
                value: '${((motion?.averageOpenness ?? 0) * 100).round()}%',
              ),
              _Metric(
                label: 'Velocity',
                value: (motion?.averageSpeed ?? 0).toStringAsFixed(2),
              ),
              _Metric(
                label: 'Accel.',
                value: (motion?.averageAcceleration ?? 0).toStringAsFixed(2),
              ),
              PrimaryButton(
                label: controller.analysisInFlight
                    ? 'Sending…'
                    : 'Analyse utterance',
                icon: Icons.insights_outlined,
                onPressed: controller.analysisInFlight
                    ? null
                    : controller.analyzeSign,
              ),
            ],
          ),
          const SizedBox(height: 9),
          Text(
            analysis?.detail ?? 'The front end groups one utterance into motion chunks before analysis.',
            style: const TextStyle(color: _muted, fontSize: 10, height: 1.35),
          ),
          const SizedBox(height: 9),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
            decoration: BoxDecoration(
              color: _cyan.withValues(alpha: .045),
              borderRadius: BorderRadius.circular(9),
              border: Border.all(color: _cyan.withValues(alpha: .12)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                Row(
                  children: <Widget>[
                    const Icon(
                      Icons.face_retouching_natural,
                      color: _cyan,
                      size: 16,
                    ),
                    const SizedBox(width: 7),
                    const Text(
                      'Face signal',
                      style: TextStyle(
                        color: _subtle,
                        fontSize: 9,
                        fontFamily: 'monospace',
                      ),
                    ),
                    const Spacer(),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: <Widget>[
                        Text(
                          face == null
                              ? 'waiting'
                              : '$faceModel: ${face.label} · ${(face.confidence * 100).round()}%',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 10,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 4),
          Text(
            controller.backendStatus,
            style: const TextStyle(
              color: _subtle,
              fontSize: 9,
              fontFamily: 'monospace',
            ),
          ),
        ],
      ),
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric({required this.label, required this.value});
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(right: 22),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          label.toUpperCase(),
          style: const TextStyle(
            color: _subtle,
            fontSize: 8,
            fontFamily: 'monospace',
            letterSpacing: .6,
          ),
        ),
        const SizedBox(height: 3),
        Text(
          value,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 11,
            fontWeight: FontWeight.w700,
          ),
        ),
      ],
    ),
  );
}

class _WorldReadout extends StatelessWidget {
  const _WorldReadout({
    required this.label,
    required this.value,
    required this.active,
  });

  final String label;
  final String value;
  final bool active;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 5),
    decoration: BoxDecoration(
      color: (active ? _mint : _subtle).withValues(alpha: .06),
      borderRadius: BorderRadius.circular(6),
      border: Border.all(
        color: (active ? _mint : _subtle).withValues(alpha: .18),
      ),
    ),
    child: Text(
      '$label  $value',
      style: TextStyle(
        color: active ? _mint : _subtle,
        fontSize: 9,
        fontFamily: 'monospace',
      ),
    ),
  );
}

class _StatusPill extends StatelessWidget {
  const _StatusPill({required this.label, required this.color});
  final String label;
  final Color color;
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 7),
    decoration: BoxDecoration(
      color: color.withValues(alpha: .06),
      borderRadius: BorderRadius.circular(50),
      border: Border.all(color: color.withValues(alpha: .25)),
    ),
    child: Row(
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        Icon(Icons.circle, size: 6, color: color),
        const SizedBox(width: 7),
        Text(
          label.toUpperCase(),
          style: TextStyle(
            color: color,
            fontSize: 10,
            fontFamily: 'monospace',
            letterSpacing: .5,
          ),
        ),
      ],
    ),
  );
}

class _FpsBadge extends StatelessWidget {
  const _FpsBadge();
  @override
  Widget build(BuildContext context) => const Row(
    mainAxisSize: MainAxisSize.min,
    children: <Widget>[
      Icon(Icons.circle, color: _mint, size: 7),
      SizedBox(width: 5),
      Text(
        '30 FPS',
        style: TextStyle(color: _mint, fontSize: 10, fontFamily: 'monospace'),
      ),
    ],
  );
}

class _ViewToggle extends StatelessWidget {
  const _ViewToggle({required this.controller});
  final AppController controller;
  @override
  Widget build(BuildContext context) => SegmentedButton<ViewMode>(
    segments: const <ButtonSegment<ViewMode>>[
      ButtonSegment(value: ViewMode.raw, label: Text('Raw')),
      ButtonSegment(value: ViewMode.wireframe, label: Text('Mesh')),
      ButtonSegment(value: ViewMode.clean, label: Text('Clean')),
    ],
    selected: <ViewMode>{controller.viewMode},
    onSelectionChanged: (selection) => controller.setViewMode(selection.first),
    style: ButtonStyle(
      textStyle: const WidgetStatePropertyAll(TextStyle(fontSize: 9)),
      padding: const WidgetStatePropertyAll(
        EdgeInsets.symmetric(horizontal: 7),
      ),
    ),
  );
}

class _CaptionCard extends StatelessWidget {
  const _CaptionCard({required this.controller});
  final AppController controller;

  @override
  Widget build(BuildContext context) {
    if (controller.isUnregisteredSign) {
      return Container(
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: _yellow.withValues(alpha: .07),
          borderRadius: BorderRadius.circular(13),
          border: Border.all(color: _yellow.withValues(alpha: .3)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            const _Eyebrow('Live caption'),
            const SizedBox(height: 10),
            const Text(
              'Sign not recognised',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 7),
            const Text(
              'We don\'t have this sign in your vocabulary yet. Would you like to add a custom sign?',
              style: TextStyle(color: _muted, fontSize: 13, height: 1.45),
            ),
            const SizedBox(height: 15),
            Wrap(
              spacing: 10,
              children: <Widget>[
                PrimaryButton(
                  label: 'Add custom sign',
                  icon: Icons.add,
                  onPressed: () => _openCustomFlow(context, controller),
                ),
                TextButton(
                  onPressed: () => controller.setUnregisteredSign(false),
                  child: const Text('Not now'),
                ),
              ],
            ),
          ],
        ),
      );
    }
    return Container(
      padding: const EdgeInsets.fromLTRB(19, 17, 19, 13),
      decoration: BoxDecoration(
        color: const Color(0xB30F172A),
        borderRadius: BorderRadius.circular(13),
        border: Border.all(color: _cyan.withValues(alpha: .25)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Row(
            children: <Widget>[
              const Icon(Icons.graphic_eq, color: _cyan, size: 17),
              const SizedBox(width: 7),
              const Text(
                'LIVE CAPTION',
                style: TextStyle(
                  color: _cyan,
                  fontSize: 10,
                  fontFamily: 'monospace',
                  letterSpacing: 1,
                ),
              ),
              const Spacer(),
              TextButton.icon(
                onPressed: () {},
                icon: const Icon(Icons.volume_up_outlined, size: 15),
                label: const Text('Read aloud'),
                style: TextButton.styleFrom(
                  foregroundColor: _muted,
                  textStyle: const TextStyle(fontSize: 10),
                ),
              ),
            ],
          ),
          const SizedBox(height: 9),
          const Text.rich(
            TextSpan(
              text: 'I would like some ',
              style: TextStyle(
                color: Colors.white,
                fontSize: 24,
                height: 1.3,
                fontWeight: FontWeight.w800,
              ),
              children: <TextSpan>[
                TextSpan(
                  text: 'water, please.',
                  style: TextStyle(color: Color(0x804EDDEA)),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          const Divider(color: Colors.white12, height: 1),
          const SizedBox(height: 9),
          const Row(
            children: <Widget>[
              Icon(Icons.circle, size: 6, color: _cyan),
              SizedBox(width: 5),
              Text(
                'Confirmed',
                style: TextStyle(
                  color: _subtle,
                  fontSize: 10,
                  fontFamily: 'monospace',
                ),
              ),
              Spacer(),
              Text(
                'Unconfirmed words appear in cyan',
                style: TextStyle(color: _subtle, fontSize: 10),
              ),
            ],
          ),
        ],
      ),
    );
  }

  static void _openCustomFlow(BuildContext context, AppController controller) =>
      Navigator.push(
        context,
        MaterialPageRoute<void>(
          builder: (_) => CustomSignFlowScreen(controller: controller),
        ),
      );
}

class _ActionDock extends StatelessWidget {
  const _ActionDock({required this.controller});
  final AppController controller;
  @override
  Widget build(BuildContext context) => GlassCard(
    padding: const EdgeInsets.all(8),
    child: Row(
      children: <Widget>[
        _DockAction(
          icon: Icons.volume_off_outlined,
          label: 'Audio',
          value: controller.audioEnabled ? 'On' : 'Off',
          active: controller.audioEnabled,
          onTap: controller.toggleAudio,
        ),
        _DockAction(
          icon: controller.isPaused ? Icons.play_arrow : Icons.pause,
          label: 'Pause',
          value: 'Translation',
          active: controller.isPaused,
          onTap: controller.togglePause,
        ),
        _DockAction(
          icon: Icons.cleaning_services_outlined,
          label: 'Clear',
          value: 'Caption',
          onTap: controller.clearCaption,
        ),
        _DockAction(
          icon: Icons.bolt,
          label: 'Quick phrases',
          value: '',
          accent: _yellow,
          onTap: () => ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Quick phrases opened.')),
          ),
        ),
      ],
    ),
  );
}

class _DockAction extends StatelessWidget {
  const _DockAction({
    required this.icon,
    required this.label,
    required this.value,
    required this.onTap,
    this.active = false,
    this.accent = _cyan,
  });
  final IconData icon;
  final String label;
  final String value;
  final VoidCallback onTap;
  final bool active;
  final Color accent;
  @override
  Widget build(BuildContext context) => Expanded(
    child: InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(11),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 11),
        decoration: BoxDecoration(
          color: active
              ? Colors.white.withValues(alpha: .05)
              : Colors.transparent,
          borderRadius: BorderRadius.circular(11),
        ),
        child: Column(
          children: <Widget>[
            Icon(icon, color: accent, size: 19),
            const SizedBox(height: 5),
            Text(
              label,
              style: const TextStyle(
                color: _muted,
                fontSize: 10,
                fontWeight: FontWeight.w700,
              ),
            ),
            if (value.isNotEmpty)
              Text(
                value,
                style: const TextStyle(
                  color: _subtle,
                  fontSize: 9,
                  fontFamily: 'monospace',
                ),
              ),
          ],
        ),
      ),
    ),
  );
}

class _SessionInsight extends StatelessWidget {
  const _SessionInsight({required this.controller});
  final AppController controller;
  Color get confidenceColor {
    final value = controller.confidence == 0 ? .98 : controller.confidence;
    if (value > .85) return _mint;
    if (value >= .70) return _yellow;
    return _red;
  }

  @override
  Widget build(BuildContext context) {
    final value = controller.confidence == 0 ? .98 : controller.confidence;
    final visibleValue = value;
    final color = confidenceColor;
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Row(
            children: <Widget>[
              const _Eyebrow('Session insight'),
              const Spacer(),
              Text(
                'Tracking confidence ${controller.confidenceWindowLabel}',
                style: const TextStyle(
                  color: _subtle,
                  fontSize: 10,
                  fontFamily: 'monospace',
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: <Widget>[
              Text(
                '${(visibleValue * 100).round()}',
                style: TextStyle(
                  fontSize: 42,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -2,
                  color: color,
                ),
              ),
              Padding(
                padding: const EdgeInsets.only(bottom: 7, left: 4),
                child: Text(
                  '%',
                  style: TextStyle(
                    color: color,
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
              const Spacer(),
              Text(
                value < .70 && value > 0
                    ? 'Tracking confidence too low'
                    : 'Stable',
                style: TextStyle(
                  color: color,
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: LinearProgressIndicator(
              value: visibleValue,
              minHeight: 6,
              backgroundColor: Colors.white12,
              color: color,
            ),
          ),
          if (value < .70) ...<Widget>[
            const SizedBox(height: 12),
            const Text(
              'Please reposition yourself and make sure your hands and upper body are clearly visible.',
              style: TextStyle(color: _red, fontSize: 11),
            ),
          ],
          const SizedBox(height: 15),
          Wrap(
            spacing: 30,
            runSpacing: 8,
            children: <Widget>[
              const _Signal(label: 'Lighting', value: 'Good'),
              _Signal(
                label: 'Hands in frame',
                value: controller.latestFrame?.handsVisible == true
                    ? '2 / 2'
                    : 'Checking',
              ),
              const _Signal(label: 'Connection', value: 'On-device'),
            ],
          ),
        ],
      ),
    );
  }
}

class _Signal extends StatelessWidget {
  const _Signal({required this.label, required this.value});
  final String label;
  final String value;
  @override
  Widget build(BuildContext context) => Row(
    mainAxisSize: MainAxisSize.min,
    children: <Widget>[
      Text(label, style: const TextStyle(color: _muted, fontSize: 11)),
      const SizedBox(width: 8),
      Text(
        value,
        style: const TextStyle(
          color: _mint,
          fontSize: 11,
          fontWeight: FontWeight.w700,
        ),
      ),
    ],
  );
}

class DictionaryScreen extends StatelessWidget {
  const DictionaryScreen({super.key, required this.controller});
  final AppController controller;

  @override
  Widget build(BuildContext context) => _ScreenFrame(
    eyebrow: 'Personal vocabulary',
    title: 'My signs',
    subtitle: 'Teach SignBridge the words that matter to you.',
    action: PrimaryButton(
      label: 'Add custom sign',
      icon: Icons.add,
      onPressed: () => _openFlow(context),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        if (controller.customSigns.isEmpty)
          GlassCard(
            child: Column(
              children: <Widget>[
                const Icon(Icons.auto_awesome, color: _cyan, size: 32),
                const SizedBox(height: 14),
                const Text(
                  'No personal signs yet',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 7),
                const Text(
                  'Add five clear samples of a sign to create a personal vocabulary entry that the recognition model can use.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: _muted, fontSize: 12, height: 1.5),
                ),
                const SizedBox(height: 18),
                OutlineButton(
                  label: 'Teach a new sign',
                  icon: Icons.add,
                  onPressed: () => _openFlow(context),
                ),
              ],
            ),
          )
        else
          Wrap(
            spacing: 14,
            runSpacing: 14,
            children: controller.customSigns
                .map(
                  (sign) => SizedBox(
                    width: 250,
                    child: _SignCard(
                      sign: sign,
                      onDelete: () => controller.deleteCustomSign(sign),
                    ),
                  ),
                )
                .toList(),
          ),
        const SizedBox(height: 30),
        const _Eyebrow('Reference vocabulary'),
        const SizedBox(height: 8),
        Text(
          'Use these language-specific references when naming a personal sign. The browser records your examples; it does not claim that ASL, BSL, and SgSL are interchangeable.',
          style: const TextStyle(color: _muted, fontSize: 12, height: 1.5),
        ),
        const SizedBox(height: 14),
        if (SignLexicon.entriesFor(controller.selectedLanguage).isEmpty)
          GlassCard(
            padding: const EdgeInsets.all(16),
            child: Text(
              '${controller.selectedLanguage} is available as a language profile. Add community-approved examples before using it as a training lexicon.',
              style: const TextStyle(color: _muted, fontSize: 12, height: 1.5),
            ),
          )
        else
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: SignLexicon.entriesFor(controller.selectedLanguage)
                .map((entry) => _ReferenceSignCard(entry: entry))
                .toList(),
          ),
      ],
    ),
  );

  void _openFlow(BuildContext context) {
    if (!controller.calibrated) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Complete camera calibration before recording a custom sign.',
          ),
        ),
      );
      controller.navigate(SignBridgePage.onboarding);
      return;
    }
    Navigator.push(
      context,
      MaterialPageRoute<void>(
        builder: (_) => CustomSignFlowScreen(controller: controller),
      ),
    );
  }
}

class _SignCard extends StatelessWidget {
  const _SignCard({required this.sign, required this.onDelete});
  final CustomSign sign;
  final VoidCallback onDelete;
  @override
  Widget build(BuildContext context) => GlassCard(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Container(
          height: 110,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            color: _cyan.withValues(alpha: .08),
          ),
          child: const Center(
            child: Icon(Icons.sign_language, color: _cyan, size: 48),
          ),
        ),
        const SizedBox(height: 14),
        Text(
          sign.label,
          style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 8),
        Row(
          children: <Widget>[
            Expanded(
              child: Text(
                '${sign.language} · ${sign.samples.length}/5 samples',
                style: const TextStyle(color: _muted, fontSize: 11),
              ),
            ),
            IconButton(
              tooltip: 'Delete personal sign',
              onPressed: onDelete,
              icon: const Icon(Icons.delete_outline, size: 17),
              color: _subtle,
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(),
            ),
          ],
        ),
        const SizedBox(height: 9),
        Text(
          sign.hasEnoughSamples
              ? 'Hand coordinates + face signal stored for matching.'
              : 'More live samples are needed before recognition.',
          style: const TextStyle(color: _subtle, fontSize: 10, height: 1.4),
        ),
        const SizedBox(height: 7),
        Text(
          'Face: ${sign.faceSignal} · ${sign.coordinateSpace}',
          style: const TextStyle(color: _subtle, fontSize: 9, height: 1.35),
        ),
      ],
    ),
  );
}

class _ReferenceSignCard extends StatelessWidget {
  const _ReferenceSignCard({required this.entry});
  final SignLexiconEntry entry;

  @override
  Widget build(BuildContext context) => SizedBox(
    width: 210,
    child: GlassCard(
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              const Icon(Icons.menu_book_outlined, color: _cyan, size: 17),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  entry.label,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            entry.parameters.join(' · '),
            style: const TextStyle(color: _muted, fontSize: 10, height: 1.4),
          ),
          const SizedBox(height: 8),
          Text(
            'Reference: ${entry.sourceUrl}',
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(color: _subtle, fontSize: 9, height: 1.3),
          ),
        ],
      ),
    ),
  );
}

class CustomSignFlowScreen extends StatefulWidget {
  const CustomSignFlowScreen({super.key, required this.controller});
  final AppController controller;
  @override
  State<CustomSignFlowScreen> createState() => _CustomSignFlowScreenState();
}

class _CustomSignFlowScreenState extends State<CustomSignFlowScreen> {
  final TextEditingController _labelController = TextEditingController();
  final List<List<double>> _samples = <List<double>>[];
  bool _recording = false;
  bool _saved = false;
  String? _error;

  AppController get controller => widget.controller;
  bool get ready =>
      controller.devices.cameraReady &&
      controller.alignment.isAligned &&
      controller.latestFrame?.shouldersVisible == true &&
      controller.latestFrame?.handsVisible == true &&
      (controller.latestFrame?.trackingConfidence ?? 0) >= .70;

  @override
  void dispose() {
    _labelController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_saved) {
      return Scaffold(
        appBar: AppBar(title: const SignBridgeLogo(compact: true)),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(28),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 480),
              child: GlassCard(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: <Widget>[
                    const Icon(Icons.check_circle, color: _mint, size: 52),
                    const SizedBox(height: 18),
                    const Text(
                      'Custom sign added ✓',
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 9),
                    Text(
                      '${_labelController.text.trim()} is now part of your personal vocabulary.',
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: _muted),
                    ),
                    const SizedBox(height: 22),
                    PrimaryButton(
                      label: 'Back to My signs',
                      onPressed: () => Navigator.pop(context),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Add custom sign',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
        ),
        leading: IconButton(
          onPressed: () => Navigator.pop(context),
          icon: const Icon(Icons.arrow_back),
        ),
      ),
      body: AnimatedBuilder(
        animation: Listenable.merge(<Listenable>[
          controller,
          controller.devices,
        ]),
        builder: (context, _) => SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(22, 14, 22, 38),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 880),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  const _Eyebrow('Personal sign recording'),
                  const SizedBox(height: 7),
                  const Text(
                    'Teach SignBridge a sign',
                    style: TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.w800,
                      letterSpacing: -1,
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'This is personal vocabulary, not an official sign-language dictionary entry. We store landmark sequences from five valid examples.',
                    style: TextStyle(color: _muted, fontSize: 13, height: 1.5),
                  ),
                  const SizedBox(height: 22),
                  if (_samples.isEmpty)
                    TextField(
                      controller: _labelController,
                      decoration: const InputDecoration(
                        labelText: 'Word or phrase',
                        hintText: 'e.g. Mum, kopi, my name',
                      ),
                    ),
                  const SizedBox(height: 18),
                  TrackingPreview(
                    controller: controller,
                    height: 340,
                    showLabels: true,
                  ),
                  const SizedBox(height: 15),
                  _PositionChecklist(controller: controller, ready: ready),
                  if (!controller.devices.cameraReady) ...<Widget>[
                    const SizedBox(height: 12),
                    Align(
                      alignment: Alignment.centerLeft,
                      child: OutlineButton(
                        label: 'Enable camera',
                        icon: Icons.videocam_outlined,
                        onPressed: () => controller.requestCamera(),
                      ),
                    ),
                  ],
                  if (_error != null) ...<Widget>[
                    const SizedBox(height: 12),
                    Text(
                      _error!,
                      style: const TextStyle(color: _red, fontSize: 11),
                    ),
                  ],
                  const SizedBox(height: 18),
                  if (_samples.isNotEmpty) ...<Widget>[
                    const _Eyebrow('Sign samples'),
                    const SizedBox(height: 9),
                    Row(
                      children: List<Widget>.generate(
                        5,
                        (index) => Expanded(
                          child: Container(
                            height: 5,
                            margin: const EdgeInsets.only(right: 6),
                            decoration: BoxDecoration(
                              color: index < _samples.length
                                  ? _cyan
                                  : Colors.white12,
                              borderRadius: BorderRadius.circular(4),
                            ),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 9),
                    Text(
                      '${_samples.length} OF 5 VALID SAMPLES',
                      style: const TextStyle(
                        color: _cyan,
                        fontSize: 10,
                        fontFamily: 'monospace',
                        letterSpacing: 1,
                      ),
                    ),
                    const SizedBox(height: 14),
                  ],
                  PrimaryButton(
                    label: _samples.isEmpty
                        ? 'Ready to record'
                        : _samples.length == 5
                        ? 'Save personal sign'
                        : 'Record sample ${_samples.length + 1} of 5',
                    icon: _samples.length == 5
                        ? Icons.save_outlined
                        : Icons.fiber_manual_record,
                    onPressed:
                        ready &&
                            !_recording &&
                            (_samples.isNotEmpty ||
                                _labelController.text.trim().isNotEmpty)
                        ? _record
                        : null,
                  ),
                  if (_samples.isNotEmpty && _samples.length < 5)
                    const Padding(
                      padding: EdgeInsets.only(top: 10),
                      child: Text(
                        'Now perform the same sign again. Repeat this movement five times so the model has enough landmark data.',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: _muted, fontSize: 11),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _record() async {
    if (_samples.length == 5) {
      await controller.saveCustomSign(_labelController.text.trim(), _samples);
      setState(() => _saved = true);
      return;
    }
    setState(() {
      _recording = true;
      _error = null;
    });
    await Future<void>.delayed(const Duration(seconds: 1));
    final sample = controller.captureCurrentSignSample();
    if (sample == null) {
      setState(() {
        _recording = false;
        _error = 'This sample was not clear enough. Reposition yourself and repeat it.';
      });
      return;
    }
    setState(() {
      _samples.add(sample);
      _recording = false;
    });
  }
}

class _PositionChecklist extends StatelessWidget {
  const _PositionChecklist({required this.controller, required this.ready});
  final AppController controller;
  final bool ready;
  @override
  Widget build(BuildContext context) => GlassCard(
    padding: const EdgeInsets.all(16),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          ready
              ? 'READY TO RECORD'
              : controller.alignment.message.toUpperCase(),
          style: TextStyle(
            color: ready ? _mint : _yellow,
            fontSize: 11,
            fontWeight: FontWeight.w800,
            letterSpacing: 1,
            fontFamily: 'monospace',
          ),
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 9,
          runSpacing: 8,
          children: <Widget>[
            _CheckChip(
              label: 'Shoulders detected',
              checked: controller.latestFrame?.shouldersVisible == true,
            ),
            _CheckChip(
              label: 'Arms detected',
              checked: controller.latestFrame?.armsVisible == true,
            ),
            _CheckChip(
              label: 'Hands visible',
              checked: controller.latestFrame?.handsVisible == true,
            ),
            _CheckChip(
              label: 'Lighting: Good',
              checked:
                  controller.latestFrame?.lightingScore == null ||
                  controller.latestFrame!.lightingScore > .6,
            ),
            _CheckChip(
              label: 'Position: Good',
              checked: controller.alignment.isAligned,
            ),
          ],
        ),
      ],
    ),
  );
}

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key, required this.controller});
  final AppController controller;
  @override
  Widget build(BuildContext context) => _ScreenFrame(
    eyebrow: 'Your data, your control',
    title: 'Settings',
    subtitle: 'Manage camera, microphone, privacy, and calibration.',
    child: LayoutBuilder(
      builder: (context, constraints) {
        final stack = constraints.maxWidth < 720;
        final left = Column(
          children: <Widget>[
            _CameraSettings(controller: controller),
            const SizedBox(height: 15),
            _MicrophoneSettings(controller: controller),
          ],
        );
        final right = Column(
          children: <Widget>[
            _PrivacySettings(controller: controller),
            const SizedBox(height: 15),
            GlassCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  const _Eyebrow('Calibration'),
                  const SizedBox(height: 8),
                  const Text(
                    'Camera baseline',
                    style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 7),
                  const Text(
                    'Re-run setup if your camera position or signing environment changes.',
                    style: TextStyle(color: _muted, fontSize: 11, height: 1.4),
                  ),
                  const SizedBox(height: 14),
                  OutlineButton(
                    label: 'Recalibrate camera',
                    icon: Icons.center_focus_strong,
                    onPressed: () async {
                      await controller.recalibrate();
                    },
                  ),
                ],
              ),
            ),
          ],
        );
        return stack
            ? Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[left, const SizedBox(height: 15), right],
              )
            : Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Expanded(child: left),
                  const SizedBox(width: 20),
                  Expanded(child: right),
                ],
              );
      },
    ),
  );
}

class _CameraSettings extends StatelessWidget {
  const _CameraSettings({required this.controller});
  final AppController controller;
  @override
  Widget build(BuildContext context) => GlassCard(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        const _Eyebrow('Camera'),
        const SizedBox(height: 8),
        const Text(
          'Camera input',
          style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 16),
        _SettingLine(
          label: 'Camera source',
          value: controller.devices.cameraName,
          icon: Icons.videocam_outlined,
        ),
        _SettingLine(
          label: 'Camera status',
          value: controller.devices.cameraStatus,
          icon: Icons.circle,
          valueColor: controller.devices.cameraReady ? _mint : _yellow,
        ),
        const SizedBox(height: 10),
        Row(
          children: <Widget>[
            Expanded(
              child: OutlineButton(
                label: controller.devices.cameraReady
                    ? 'Camera enabled'
                    : 'Enable camera',
                icon: Icons.videocam_outlined,
                onPressed: controller.devices.cameraReady
                    ? null
                    : () => controller.requestCamera(),
              ),
            ),
            const SizedBox(width: 8),
            IconButton(
              onPressed: () => controller.recalibrate(),
              icon: const Icon(Icons.center_focus_strong, color: _cyan),
              tooltip: 'Recalibrate camera',
            ),
          ],
        ),
      ],
    ),
  );
}

class _MicrophoneSettings extends StatelessWidget {
  const _MicrophoneSettings({required this.controller});
  final AppController controller;
  @override
  Widget build(BuildContext context) {
    final isGranted =
        controller.devices.microphonePermission == PermissionStatus.granted;
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const _Eyebrow('Microphone'),
          const SizedBox(height: 8),
          const Text(
            'Voice input',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 16),
          _SettingLine(
            label: 'Microphone source',
            value: 'Default device',
            icon: Icons.mic_none,
          ),
          _SettingLine(
            label: 'Microphone status',
            value: controller.devices.microphoneStatus,
            icon: Icons.circle,
            valueColor: isGranted ? _mint : _yellow,
          ),
          const SizedBox(height: 10),
          Row(
            children: <Widget>[
              Expanded(
                child: OutlineButton(
                  label: isGranted ? 'Microphone enabled' : 'Enable microphone',
                  icon: Icons.mic_none,
                  onPressed: isGranted
                      ? null
                      : () => controller.devices.enableMicrophone(),
                ),
              ),
              const SizedBox(width: 8),
              IconButton(
                onPressed: () => controller.devices.testMicrophone(),
                icon: Icon(
                  controller.devices.isTestingMicrophone
                      ? Icons.graphic_eq
                      : Icons.mic,
                  color: _cyan,
                ),
                tooltip: 'Test microphone',
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _PrivacySettings extends StatelessWidget {
  const _PrivacySettings({required this.controller});
  final AppController controller;
  @override
  Widget build(BuildContext context) => GlassCard(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        const _Eyebrow('Data & privacy'),
        const SizedBox(height: 8),
        const Text(
          'Your data, your choice',
          style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 10),
        SwitchListTile.adaptive(
          contentPadding: EdgeInsets.zero,
          value: true,
          onChanged: (_) {},
          title: const Text(
            'On-device inference only',
            style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700),
          ),
          subtitle: const Text(
            'Keep camera processing on this device.',
            style: TextStyle(color: _subtle, fontSize: 10),
          ),
        ),
        SwitchListTile.adaptive(
          contentPadding: EdgeInsets.zero,
          value: false,
          onChanged: (_) {},
          title: const Text(
            'Frame sampling for training',
            style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700),
          ),
          subtitle: const Text(
            'Off by default. Enable only with consent.',
            style: TextStyle(color: _subtle, fontSize: 10),
          ),
        ),
      ],
    ),
  );
}

class _SettingLine extends StatelessWidget {
  const _SettingLine({
    required this.label,
    required this.value,
    required this.icon,
    this.valueColor = _muted,
  });
  final String label;
  final String value;
  final IconData icon;
  final Color valueColor;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 12),
    child: Row(
      children: <Widget>[
        Icon(icon, size: 16, color: value == 'Ready' ? _mint : _subtle),
        const SizedBox(width: 9),
        Text(label, style: const TextStyle(color: _muted, fontSize: 11)),
        const Spacer(),
        Flexible(
          child: Text(
            value,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              color: valueColor,
              fontSize: 11,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
      ],
    ),
  );
}
