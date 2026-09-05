import 'package:apptesting/models/landmark_frame.dart';
import 'package:apptesting/services/tracking_state_normalisation_service.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('LandmarkNormalisationService', () {
    test('is invariant to image translation and scale', () {
      final firstService = LandmarkNormalisationService();
      final secondService = LandmarkNormalisationService();

      final first = firstService.process(
        _frame(
          frameIndex: 1,
          pose: _pose(leftX: 0.40, rightX: 0.60, shoulderY: 0.50),
          hands: <HandLandmarkGroup>[
            _hand(x: 0.50, y: 0.40, handedness: Handedness.right),
          ],
        ),
      );
      final second = secondService.process(
        _frame(
          frameIndex: 1,
          pose: _pose(leftX: 0.20, rightX: 0.60, shoulderY: 0.50),
          hands: <HandLandmarkGroup>[
            _hand(x: 0.40, y: 0.30, handedness: Handedness.right),
          ],
        ),
      );

      final firstPoint = first.hands.single.pointAt(0)!.normalisedCoordinates!;
      final secondPoint = second.hands.single
          .pointAt(0)!
          .normalisedCoordinates!;
      expect(firstPoint.x, closeTo(0, 1e-9));
      expect(firstPoint.y, closeTo(-0.5, 1e-9));
      expect(secondPoint.x, closeTo(firstPoint.x, 1e-9));
      expect(secondPoint.y, closeTo(firstPoint.y, 1e-9));
      expect(first.coordinateSpace, LandmarkCoordinateSpace.bodyNormalised);
      expect(first.normalisationScale, closeTo(0.20, 1e-9));
    });

    test('maps shoulder midpoint to zero without flipping MediaPipe y', () {
      final service = LandmarkNormalisationService();

      final output = service.process(
        _frame(
          frameIndex: 1,
          pose: _pose(leftX: 0.40, rightX: 0.60, shoulderY: 0.50),
          hands: <HandLandmarkGroup>[
            _hand(x: 0.50, y: 0.40, handedness: Handedness.right),
          ],
        ),
      );

      final left = output.pose.pointAt(11)!.normalisedCoordinates!;
      final right = output.pose.pointAt(12)!.normalisedCoordinates!;
      final wrist = output.hands.single.pointAt(0)!.normalisedCoordinates!;
      expect(left.x, closeTo(-0.5, 1e-9));
      expect(right.x, closeTo(0.5, 1e-9));
      expect((left.x + right.x) / 2, closeTo(0, 1e-9));
      expect(wrist.y, lessThan(0));
    });

    test('gates low-confidence points and preserves explicit absence', () {
      final service = LandmarkNormalisationService();
      final points = <LandmarkPoint?>[
        _point(0, 0.50, 0.40, confidence: 0.2),
        null,
      ];

      final output = service.process(
        _frame(
          frameIndex: 1,
          pose: _pose(),
          hands: <HandLandmarkGroup>[
            HandLandmarkGroup(isPresent: true, landmarks: points),
          ],
        ),
      );

      final gated = output.hands.single.landmarks[0]!;
      expect(gated.imageCoordinates, isNotNull);
      expect(gated.confidence, 0.2);
      expect(gated.normalisedCoordinates, isNull);
      expect(gated.velocity, isNull);
      expect(output.hands.single.landmarks[1], isNull);
    });

    test('does not normalise stale points from absent groups', () {
      final service = LandmarkNormalisationService();
      final stalePose = _pose();
      final staleHand = _hand(x: 0.50, y: 0.40, handedness: Handedness.right);

      final output = service.process(
        _frame(
          frameIndex: 1,
          pose: LandmarkGroup(isPresent: false, landmarks: stalePose.landmarks),
          hands: <HandLandmarkGroup>[staleHand.copyWith(isPresent: false)],
        ),
      );

      expect(output.canNormalise, isFalse);
      expect(output.pose.pointAt(11)!.normalisedCoordinates, isNull);
      expect(output.hands.single.pointAt(0)!.normalisedCoordinates, isNull);
    });

    test('computes velocity and acceleration from capture timestamps', () {
      final service = LandmarkNormalisationService(
        config: const TrackingStateNormalisationConfig(
          smoothingCutoffHz: 1000000000,
          normalisationAnchorTimeConstant: Duration.zero,
        ),
      );

      final first = service.process(_motionFrame(1, 0, 0.50));
      final second = service.process(_motionFrame(2, 100, 0.52));
      final third = service.process(_motionFrame(3, 200, 0.56));

      expect(first.hands.single.pointAt(0)!.velocity, isNull);
      expect(second.hands.single.pointAt(0)!.acceleration, isNull);
      expect(second.hands.single.pointAt(0)!.velocity!.x, closeTo(1, 1e-5));
      expect(third.hands.single.pointAt(0)!.velocity!.x, closeTo(2, 1e-5));
      expect(third.hands.single.pointAt(0)!.acceleration!.x, closeTo(10, 1e-4));
    });

    test('resets temporal history after a missing point', () {
      final service = LandmarkNormalisationService();
      service.process(_motionFrame(1, 0, 0.50));
      service.process(
        _frame(
          frameIndex: 2,
          milliseconds: 33,
          pose: _pose(),
          hands: const <HandLandmarkGroup>[HandLandmarkGroup(isPresent: false)],
        ),
      );

      final returned = service.process(_motionFrame(3, 66, 0.55));

      expect(returned.hands.single.pointAt(0)!.velocity, isNull);
      expect(returned.hands.single.pointAt(0)!.acceleration, isNull);
    });

    test('resets derivatives after a long timestamp gap', () {
      final service = LandmarkNormalisationService();
      service.process(_motionFrame(1, 0, 0.50));

      final returned = service.process(_motionFrame(2, 300, 0.55));

      expect(
        returned.hands.single.pointAt(0)!.normalisedCoordinates,
        isNotNull,
      );
      expect(returned.hands.single.pointAt(0)!.velocity, isNull);
      expect(returned.hands.single.pointAt(0)!.acceleration, isNull);
    });

    test('briefly reuses but eventually expires a shoulder anchor', () {
      final service = LandmarkNormalisationService();
      service.process(_motionFrame(1, 0, 0.50));

      final stale = service.process(
        _frame(
          frameIndex: 2,
          milliseconds: 100,
          hands: <HandLandmarkGroup>[
            _hand(x: 0.52, y: 0.40, handedness: Handedness.right),
          ],
        ),
      );
      expect(stale.canNormalise, isTrue);
      expect(stale.normalisationAnchorIsStale, isTrue);
      expect(
        stale.trackingIssues,
        contains(TrackingIssue.staleNormalisationAnchor),
      );

      LandmarkFrame expired = stale;
      for (var step = 2; step <= 6; step += 1) {
        expired = service.process(
          _frame(
            frameIndex: step + 1,
            milliseconds: step * 100,
            hands: <HandLandmarkGroup>[
              _hand(x: 0.52, y: 0.40, handedness: Handedness.right),
            ],
          ),
        );
      }
      expect(expired.canNormalise, isFalse);
      expect(expired.hands.single.pointAt(0)!.normalisedCoordinates, isNull);
    });

    test('does not smooth face coordinates', () {
      final service = LandmarkNormalisationService(
        config: const TrackingStateNormalisationConfig(
          smoothingCutoffHz: 0.1,
          normalisationAnchorTimeConstant: Duration.zero,
        ),
      );
      service.process(
        _frame(
          frameIndex: 1,
          pose: _pose(),
          face: _face(x: 0.50),
          hands: <HandLandmarkGroup>[
            _hand(x: 0.50, y: 0.40, handedness: Handedness.right),
          ],
        ),
      );

      final output = service.process(
        _frame(
          frameIndex: 2,
          milliseconds: 100,
          pose: _pose(),
          face: _face(x: 0.54),
          hands: <HandLandmarkGroup>[
            _hand(x: 0.54, y: 0.40, handedness: Handedness.right),
          ],
        ),
      );

      expect(
        output.face.pointAt(0)!.normalisedCoordinates!.x,
        closeTo(0.2, 1e-9),
      );
      expect(
        output.hands.single.pointAt(0)!.normalisedCoordinates!.x,
        lessThan(0.2),
      );
    });

    test('canonical hand world coordinates are rotation invariant', () {
      final original = LandmarkNormalisationService().process(
        _worldHandFrame(<int, LandmarkCoordinates>{
          0: const LandmarkCoordinates(x: 0, y: 0, z: 0),
          5: const LandmarkCoordinates(x: 1, y: 1, z: 0),
          8: const LandmarkCoordinates(x: 1, y: 2, z: 0),
          17: const LandmarkCoordinates(x: -1, y: 1, z: 0),
        }),
      );
      final rotated = LandmarkNormalisationService().process(
        _worldHandFrame(<int, LandmarkCoordinates>{
          0: const LandmarkCoordinates(x: 0, y: 0, z: 0),
          5: const LandmarkCoordinates(x: -1, y: 1, z: 0),
          8: const LandmarkCoordinates(x: -2, y: 1, z: 0),
          17: const LandmarkCoordinates(x: -1, y: -1, z: 0),
        }),
      );

      for (final index in <int>[0, 5, 8, 17]) {
        final first = original.hands.single
            .pointAt(index)!
            .canonicalWorldCoordinates!;
        final second = rotated.hands.single
            .pointAt(index)!
            .canonicalWorldCoordinates!;
        expect(second.x, closeTo(first.x, 1e-9));
        expect(second.y, closeTo(first.y, 1e-9));
        expect(second.z, closeTo(first.z!, 1e-9));
      }
    });
  });
}

final _epoch = DateTime.utc(2026, 9, 6);

LandmarkFrame _motionFrame(int frameIndex, int milliseconds, double handX) =>
    _frame(
      frameIndex: frameIndex,
      milliseconds: milliseconds,
      pose: _pose(),
      hands: <HandLandmarkGroup>[
        _hand(x: handX, y: 0.40, handedness: Handedness.right),
      ],
    );

LandmarkFrame _worldHandFrame(Map<int, LandmarkCoordinates> worldPoints) {
  final points = List<LandmarkPoint?>.filled(18, null);
  for (final entry in worldPoints.entries) {
    points[entry.key] = _point(
      entry.key,
      0.50 + entry.key * 0.001,
      0.40,
      world: entry.value,
    );
  }
  return _frame(
    frameIndex: 1,
    pose: _pose(),
    hands: <HandLandmarkGroup>[
      HandLandmarkGroup(isPresent: true, landmarks: points),
    ],
  );
}

LandmarkFrame _frame({
  required int frameIndex,
  int milliseconds = 0,
  LandmarkGroup pose = const LandmarkGroup.absent(),
  LandmarkGroup face = const LandmarkGroup.absent(),
  List<HandLandmarkGroup> hands = const <HandLandmarkGroup>[],
}) => LandmarkFrame(
  timestamp: _epoch.add(Duration(milliseconds: milliseconds)),
  frameIndex: frameIndex,
  subjectId: 'subject-a',
  pose: pose,
  face: face,
  hands: hands,
);

LandmarkGroup _pose({
  double leftX = 0.40,
  double rightX = 0.60,
  double shoulderY = 0.50,
}) {
  final points = List<LandmarkPoint?>.filled(17, null);
  points[11] = _point(11, leftX, shoulderY);
  points[12] = _point(12, rightX, shoulderY);
  return LandmarkGroup(isPresent: true, landmarks: points);
}

LandmarkGroup _face({required double x}) => LandmarkGroup(
  isPresent: true,
  landmarks: <LandmarkPoint?>[_point(0, x, 0.30)],
);

HandLandmarkGroup _hand({
  required double x,
  required double y,
  required Handedness handedness,
}) => HandLandmarkGroup(
  isPresent: true,
  trackId: 'test-hand',
  rawHandedness: handedness,
  handedness: handedness,
  handednessScore: 0.9,
  landmarks: <LandmarkPoint?>[_point(0, x, y)],
);

LandmarkPoint _point(
  int index,
  double x,
  double y, {
  double confidence = 1,
  LandmarkCoordinates? world,
}) => LandmarkPoint(
  index: index,
  confidence: confidence,
  imageCoordinates: LandmarkCoordinates(x: x, y: y),
  worldCoordinates: world,
);
