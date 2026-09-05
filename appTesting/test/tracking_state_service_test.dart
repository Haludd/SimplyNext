import 'package:apptesting/models/landmark_frame.dart';
import 'package:apptesting/services/tracking_state_normalisation_service.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('TrackingStateService', () {
    test('represents an entirely absent observation without throwing', () {
      final service = TrackingStateService();

      final output = service.process(_frame(frameIndex: 1));

      expect(output.trackingStatus, TrackingStatus.absent);
      expect(output.trackingQuality, 0);
      expect(output.hands, isEmpty);
      expect(output.trackingIssues, contains(TrackingIssue.noLandmarks));
      expect(output.trackingIssues, contains(TrackingIssue.noHands));
      expect(output.trackingIssues, contains(TrackingIssue.missingShoulders));
    });

    test('keeps identity when MediaPipe hand order changes', () {
      final service = TrackingStateService();
      final first = service.process(
        _frame(
          frameIndex: 1,
          pose: _pose(),
          hands: <HandLandmarkGroup>[
            _hand(x: 0.30, handedness: Handedness.left),
            _hand(x: 0.70, handedness: Handedness.right),
          ],
        ),
      );
      final second = service.process(
        _frame(
          frameIndex: 2,
          milliseconds: 33,
          pose: _pose(),
          hands: <HandLandmarkGroup>[
            _hand(x: 0.69, handedness: Handedness.right),
            _hand(x: 0.31, handedness: Handedness.left),
          ],
        ),
      );

      expect(second.hands[0].trackId, first.hands[1].trackId);
      expect(second.hands[1].trackId, first.hands[0].trackId);
    });

    test('uses global handedness-aware matching when hands cross', () {
      final service = TrackingStateService();
      final first = service.process(
        _frame(
          frameIndex: 1,
          pose: _pose(),
          hands: <HandLandmarkGroup>[
            _hand(x: 0.30, handedness: Handedness.left),
            _hand(x: 0.70, handedness: Handedness.right),
          ],
        ),
      );
      final crossed = service.process(
        _frame(
          frameIndex: 2,
          milliseconds: 33,
          pose: _pose(),
          hands: <HandLandmarkGroup>[
            _hand(x: 0.55, handedness: Handedness.left),
            _hand(x: 0.45, handedness: Handedness.right),
          ],
        ),
      );

      expect(crossed.hands[0].trackId, first.hands[0].trackId);
      expect(crossed.hands[1].trackId, first.hands[1].trackId);
    });

    test('a single contradictory observation does not flip handedness', () {
      final service = TrackingStateService();
      final first = service.process(
        _frame(
          frameIndex: 1,
          pose: _pose(),
          hands: <HandLandmarkGroup>[
            _hand(x: 0.70, handedness: Handedness.right),
          ],
        ),
      );
      final second = service.process(
        _frame(
          frameIndex: 2,
          milliseconds: 33,
          pose: _pose(),
          hands: <HandLandmarkGroup>[
            _hand(x: 0.69, handedness: Handedness.left),
          ],
        ),
      );

      expect(first.hands.single.handedness, Handedness.right);
      expect(second.hands.single.trackId, first.hands.single.trackId);
      expect(second.hands.single.handedness, Handedness.right);
      expect(second.hands.single.handednessRunningAverage, closeTo(0.5, 1e-9));
      expect(second.hands.single.handednessObservationCount, 2);
    });

    test('retains duplicate handedness observations and marks uncertainty', () {
      final service = TrackingStateService();

      final output = service.process(
        _frame(
          frameIndex: 1,
          pose: _pose(),
          hands: <HandLandmarkGroup>[
            _hand(x: 0.30, handedness: Handedness.right),
            _hand(x: 0.70, handedness: Handedness.right),
          ],
        ),
      );

      expect(output.hands, hasLength(2));
      expect(output.hands.map((hand) => hand.trackId).toSet(), hasLength(2));
      expect(output.hands.every((hand) => hand.handednessUncertain), isTrue);
      expect(
        output.trackingIssues,
        contains(TrackingIssue.handednessUncertain),
      );
    });

    test('uses only an observed pose wrist to repair a hand wrist', () {
      final service = TrackingStateService();
      final pose = _pose(includeWrists: true);
      final lowConfidenceWrist = HandLandmarkGroup(
        isPresent: true,
        rawHandedness: Handedness.left,
        handednessScore: 0.9,
        landmarks: <LandmarkPoint?>[_point(0, 0.10, 0.10, confidence: 0.1)],
      );

      final repaired = service.process(
        _frame(
          frameIndex: 1,
          pose: pose,
          hands: <HandLandmarkGroup>[lowConfidenceWrist],
        ),
      );

      final wrist = repaired.hands.single.pointAt(0)!;
      expect(wrist.source, LandmarkSource.poseWristSubstitution);
      expect(wrist.imageCoordinates!.x, closeTo(0.30, 1e-9));
      expect(wrist.imageCoordinates!.y, closeTo(0.70, 1e-9));
      expect(wrist.worldCoordinates, isNull);
    });

    test('uses stable identity for wrist repair after a raw label flip', () {
      final service = TrackingStateService();
      final firstPoints = List<LandmarkPoint?>.filled(6, null);
      firstPoints[0] = _point(0, 0.30, 0.70);
      firstPoints[5] = _point(5, 0.32, 0.60);
      final first = service.process(
        _frame(
          frameIndex: 1,
          pose: _pose(includeWrists: true),
          hands: <HandLandmarkGroup>[
            HandLandmarkGroup(
              isPresent: true,
              rawHandedness: Handedness.left,
              handednessScore: 0.9,
              landmarks: firstPoints,
            ),
          ],
        ),
      );

      final flippedPoints = List<LandmarkPoint?>.filled(6, null);
      flippedPoints[0] = _point(0, 0.70, 0.70, confidence: 0.1);
      flippedPoints[5] = _point(5, 0.33, 0.60);
      final second = service.process(
        _frame(
          frameIndex: 2,
          milliseconds: 33,
          pose: _pose(includeWrists: true),
          hands: <HandLandmarkGroup>[
            HandLandmarkGroup(
              isPresent: true,
              rawHandedness: Handedness.right,
              handednessScore: 0.9,
              landmarks: flippedPoints,
            ),
          ],
        ),
      );

      expect(second.hands.single.trackId, first.hands.single.trackId);
      expect(second.hands.single.handedness, Handedness.left);
      expect(
        second.hands.single.pointAt(0)!.source,
        LandmarkSource.poseWristSubstitution,
      );
      expect(second.hands.single.pointAt(0)!.imageCoordinates!.x, 0.30);
    });

    test('does not invent a wrist when no measured substitute exists', () {
      final service = TrackingStateService();
      final hand = HandLandmarkGroup(
        isPresent: true,
        rawHandedness: Handedness.left,
        handednessScore: 0.9,
        landmarks: <LandmarkPoint?>[_point(0, 0.10, 0.10, confidence: 0.1)],
      );

      final output = service.process(
        _frame(frameIndex: 1, pose: _pose(), hands: <HandLandmarkGroup>[hand]),
      );

      final wrist = output.hands.single.pointAt(0)!;
      expect(wrist.source, LandmarkSource.mediaPipe);
      expect(wrist.confidence, 0.1);
      expect(wrist.imageCoordinates!.x, 0.10);
    });

    test('treats group presence flags as authoritative', () {
      final service = TrackingStateService();
      final stalePose = _pose();
      final staleHand = _hand(x: 0.3, handedness: Handedness.left);

      final output = service.process(
        _frame(
          frameIndex: 1,
          pose: LandmarkGroup(isPresent: false, landmarks: stalePose.landmarks),
          hands: <HandLandmarkGroup>[staleHand.copyWith(isPresent: false)],
        ),
      );

      expect(output.trackingStatus, TrackingStatus.absent);
      expect(output.canNormalise, isFalse);
      expect(output.hands.single.trackId, isNull);
    });

    test('penalises incomplete landmark groups in tracking quality', () {
      final service = TrackingStateService();

      final output = service.process(
        _frame(
          frameIndex: 1,
          pose: _pose(),
          hands: <HandLandmarkGroup>[
            _hand(x: 0.3, handedness: Handedness.left),
          ],
        ),
      );

      expect(output.trackingQuality, lessThan(0.5));
      expect(output.trackingStatus, TrackingStatus.degraded);
    });

    test(
      'reports tracked for complete high-confidence pose and hand groups',
      () {
        final service = TrackingStateService();

        final output = service.process(
          _frame(
            frameIndex: 1,
            pose: _completePose(),
            hands: <HandLandmarkGroup>[
              _completeHand(x: 0.3, handedness: Handedness.left),
            ],
          ),
        );

        expect(output.trackingQuality, closeTo(1, 1e-9));
        expect(output.trackingStatus, TrackingStatus.tracked);
      },
    );

    test('expires a missing hand track after the configured frame count', () {
      final service = TrackingStateService();
      final first = service.process(
        _frame(
          frameIndex: 1,
          pose: _pose(),
          hands: <HandLandmarkGroup>[
            _hand(x: 0.3, handedness: Handedness.left),
          ],
        ),
      );
      for (var index = 2; index <= 17; index += 1) {
        service.process(
          _frame(
            frameIndex: index,
            milliseconds: (index - 1) * 33,
            pose: _pose(),
          ),
        );
      }

      final returned = service.process(
        _frame(
          frameIndex: 18,
          milliseconds: 17 * 33,
          pose: _pose(),
          hands: <HandLandmarkGroup>[
            _hand(x: 0.3, handedness: Handedness.left),
          ],
        ),
      );

      expect(returned.hands.single.trackId, isNot(first.hands.single.trackId));
    });
  });

  test('LandmarkFrame JSON preserves grouped absence and metadata', () {
    final input = _frame(
      frameIndex: 7,
      pose: LandmarkGroup(
        isPresent: true,
        landmarks: <LandmarkPoint?>[_point(0, 0.1, 0.2), null],
      ),
      hands: <HandLandmarkGroup>[_hand(x: 0.3, handedness: Handedness.left)],
    );

    final decoded = LandmarkFrame.fromJson(input.toJson());

    expect(decoded.frameIndex, 7);
    expect(decoded.timestamp, input.timestamp.toUtc());
    expect(decoded.pose.isPresent, isTrue);
    expect(decoded.pose.landmarks, hasLength(2));
    expect(decoded.pose.landmarks[1], isNull);
    expect(decoded.hands.single.rawHandedness, Handedness.left);
  });
}

final _epoch = DateTime.utc(2026, 9, 6);

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

LandmarkGroup _pose({bool includeWrists = false}) {
  final points = List<LandmarkPoint?>.filled(17, null);
  points[11] = _point(11, 0.40, 0.50);
  points[12] = _point(12, 0.60, 0.50);
  if (includeWrists) {
    points[15] = _point(15, 0.30, 0.70);
    points[16] = _point(16, 0.70, 0.70);
  }
  return LandmarkGroup(isPresent: true, landmarks: points);
}

LandmarkGroup _completePose() {
  final points = List<LandmarkPoint?>.filled(25, null);
  for (final index in <int>[11, 12, 13, 14, 15, 16, 23, 24]) {
    points[index] = _point(
      index,
      index == 11
          ? 0.40
          : index == 12
          ? 0.60
          : 0.50,
      0.50 + index * 0.001,
    );
  }
  return LandmarkGroup(isPresent: true, landmarks: points);
}

HandLandmarkGroup _hand({required double x, required Handedness handedness}) =>
    HandLandmarkGroup(
      isPresent: true,
      rawHandedness: handedness,
      handednessScore: 0.9,
      landmarks: <LandmarkPoint?>[_point(0, x, 0.40)],
    );

HandLandmarkGroup _completeHand({
  required double x,
  required Handedness handedness,
}) => HandLandmarkGroup(
  isPresent: true,
  rawHandedness: handedness,
  handednessScore: 0.9,
  landmarks: List<LandmarkPoint?>.generate(
    21,
    (index) => _point(index, x + index * 0.001, 0.40),
  ),
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
