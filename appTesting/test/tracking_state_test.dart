import 'package:apptesting/models/landmark_frame.dart';
import 'package:apptesting/services/tracking_state_normalisation_service.dart';
import 'package:flutter_test/flutter_test.dart';

import 'fixtures/landmark_frame_fixtures.dart';

void main() {
  group('TrackingStateService - current-frame health', () {
    test('perfect Harold frame is fully tracked with exact quality', () {
      // Harold/MediaPipe input: 33 pose points at 0.98, two complete 21-point
      // hands at 0.96, a curated face group, and confident left/right labels.
      final input = LandmarkFrameFixtures.fullyTrackedFrame();
      final result = TrackingStateService().process(input);

      expect(input.coordinateSpace, LandmarkCoordinateSpace.mediaPipeImage);
      expect(input.pose.landmarks, hasLength(33));
      expect(input.face.landmarks, hasLength(468));
      expect(input.hands, hasLength(2));
      expect(input.hands.every((hand) => hand.landmarks.length == 21), isTrue);
      expect(input.hands.first.handedness, Handedness.unknown);
      expect(input.hands.first.handednessRunningAverage, 0.5);
      expect(input.hands.first.handednessObservationCount, 0);

      expect(result.timestamp, LandmarkFrameFixtures.epoch);
      expect(result.frameIndex, 100);
      expect(result.trackingStatus, TrackingStatus.tracked);
      expect(result.trackingQuality, closeTo(0.97, 1e-12));
      expect(result.trackingIssues, isEmpty);
      expect(result.canNormalise, isTrue);
      expect(result.coordinateSpace, LandmarkCoordinateSpace.mediaPipeImage);
      expect(result.hands[0].trackId, isNotNull);
      expect(result.hands[1].trackId, isNotNull);
      expect(result.hands[0].trackId, isNot(result.hands[1].trackId));
      expect(result.hands[0].handedness, Handedness.left);
      expect(result.hands[0].handednessRunningAverage, closeTo(0.05, 1e-12));
      expect(result.hands[1].handedness, Handedness.right);
      expect(result.hands[1].handednessRunningAverage, closeTo(0.95, 1e-12));
      expect(
        result.hands.every((hand) => hand.handednessObservationCount == 1),
        isTrue,
      );
    });

    test('completely missing subject is absent and remains empty', () {
      // Harold/MediaPipe input: normal empty results with every group absent.
      final input = LandmarkFrameFixtures.noSubjectFrame();
      final result = TrackingStateService().process(input);

      expect(input.pose.isPresent, isFalse);
      expect(input.face.isPresent, isFalse);
      expect(input.hands, isEmpty);
      expect(result.trackingStatus, TrackingStatus.absent);
      expect(result.trackingQuality, 0);
      expect(
        result.trackingIssues,
        unorderedEquals(<TrackingIssue>[
          TrackingIssue.noLandmarks,
          TrackingIssue.noHands,
          TrackingIssue.missingShoulders,
        ]),
      );
      expect(result.canNormalise, isFalse);
      expect(result.pose.landmarks, isEmpty);
      expect(result.hands, isEmpty);
    });

    test('one missing shoulder degrades despite high numeric quality', () {
      // One null shoulder removes the body reference. A null is absence, not a
      // low-confidence sample, so it must not create lowConfidence.
      final input = LandmarkFrameFixtures.oneShoulderMissingFrame();
      final result = TrackingStateService().process(input);

      expect(input.pose.pointAt(11), isNotNull);
      expect(input.pose.pointAt(12), isNull);
      expect(result.trackingQuality, closeTo(0.90875, 1e-12));
      expect(result.trackingStatus, TrackingStatus.degraded);
      expect(
        result.trackingIssues,
        unorderedEquals(<TrackingIssue>[TrackingIssue.missingShoulders]),
      );
      expect(result.canNormalise, isFalse);
      expect(result.pose.pointAt(12), isNull);
    });

    test('sub-minimum shoulder scale fails safely without losing quality', () {
      // Both shoulder observations are confident, but their 0.000099 distance
      // is below the implementation-defined 0.0001 scale floor.
      final result = TrackingStateService().process(
        LandmarkFrameFixtures.tinyShoulderScaleFrame(),
      );

      expect(result.trackingQuality, closeTo(0.97, 1e-12));
      expect(result.trackingStatus, TrackingStatus.degraded);
      expect(result.trackingIssues, <TrackingIssue>[
        TrackingIssue.missingShoulders,
      ]);
      expect(result.canNormalise, isFalse);
    });

    test('minimum shoulder scale is inclusive', () {
      // Width exactly 0.0001 is accepted; this is the lower normalization
      // boundary selected by the implementation, not a number fixed by PLN.
      final result = TrackingStateService().process(
        LandmarkFrameFixtures.minimumShoulderScaleFrame(),
      );

      expect(result.trackingStatus, TrackingStatus.tracked);
      expect(result.trackingQuality, closeTo(0.97, 1e-12));
      expect(result.trackingIssues, isEmpty);
      expect(result.canNormalise, isTrue);
    });

    test('very large finite shoulder scale has no artificial upper cap', () {
      // Harold input spans x=0.01..0.99. The implementation has no maximum
      // shoulder-width threshold, so valid large people remain tracked.
      final result = TrackingStateService().process(
        LandmarkFrameFixtures.largeShoulderScaleFrame(),
      );

      expect(result.trackingStatus, TrackingStatus.tracked);
      expect(result.trackingQuality, closeTo(0.97, 1e-12));
      expect(result.trackingIssues, isEmpty);
      expect(result.canNormalise, isTrue);
    });

    test('very low pose and hand confidence degrades around a valid face', () {
      // Pose/hands are all 0.1. The curated face remains 0.94, so the subject
      // is not absent, but face confidence deliberately does not boost quality.
      final result = TrackingStateService().process(
        LandmarkFrameFixtures.lowConfidenceFrame(),
      );

      expect(result.trackingStatus, TrackingStatus.degraded);
      expect(result.trackingQuality, 0);
      expect(
        result.trackingIssues,
        unorderedEquals(<TrackingIssue>[
          TrackingIssue.noHands,
          TrackingIssue.missingShoulders,
          TrackingIssue.lowConfidence,
        ]),
      );
      expect(result.trackingIssues, isNot(contains(TrackingIssue.noLandmarks)));
      expect(result.canNormalise, isFalse);
    });

    test('mixed confidence uses completeness and ignores rejected scores', () {
      // Only two pose quality points and eleven of 21 hand points clear 0.5.
      // Rejected 0.01 points contribute zero rather than 0.01 to quality.
      final input = LandmarkFrameFixtures.mixedConfidenceFrame();
      final result = TrackingStateService().process(input);

      const expectedPoseQuality = 2 * 0.98 / 8;
      const expectedHandQuality = 11 * 0.96 / 21;
      const expectedQuality = (expectedPoseQuality + expectedHandQuality) / 2;
      expect(expectedPoseQuality, closeTo(0.245, 1e-12));
      expect(expectedHandQuality, closeTo(0.5028571428571429, 1e-12));
      expect(result.trackingQuality, closeTo(expectedQuality, 1e-12));
      expect(result.trackingQuality, closeTo(0.37392857142857144, 1e-12));
      expect(result.trackingStatus, TrackingStatus.degraded);
      expect(result.trackingIssues, <TrackingIssue>[
        TrackingIssue.lowConfidence,
      ]);
      expect(result.canNormalise, isTrue);
      expect(result.hands.single.pointAt(10)!.confidence, 0.96);
      expect(result.hands.single.pointAt(11)!.confidence, 0.01);
      expect(result.hands.single.pointAt(11)!.imageCoordinates, isNotNull);
    });

    test('missing hands degrades without inventing a hand group', () {
      // Complete pose quality is 0.98, hand quality is exactly zero, and the
      // total is therefore 0.49.
      final result = TrackingStateService().process(
        LandmarkFrameFixtures.missingHandsFrame(),
      );

      expect(result.trackingStatus, TrackingStatus.degraded);
      expect(result.trackingQuality, closeTo(0.49, 1e-12));
      expect(result.trackingIssues, <TrackingIssue>[TrackingIssue.noHands]);
      expect(result.canNormalise, isTrue);
      expect(result.hands, isEmpty);
    });

    test('missing pose cannot be fully tracked even with complete hands', () {
      // Complete hand quality is 0.96 but absent pose quality is zero, so the
      // total is 0.48 and no shoulder body reference exists.
      final result = TrackingStateService().process(
        LandmarkFrameFixtures.missingPoseFrame(),
      );

      expect(result.trackingStatus, TrackingStatus.degraded);
      expect(result.trackingQuality, closeTo(0.48, 1e-12));
      expect(result.trackingIssues, <TrackingIssue>[
        TrackingIssue.missingShoulders,
      ]);
      expect(result.canNormalise, isFalse);
      expect(result.pose.isPresent, isFalse);
      expect(result.hands, hasLength(2));
    });

    test('finite coordinate extremes remain fully tracked', () {
      // Image-boundary coordinates (0,0) and (1,1) are legitimate finite
      // MediaPipe values. Tracking does not clamp or reject them.
      final input = LandmarkFrameFixtures.coordinateExtremesFrame();
      final result = TrackingStateService().process(input);

      expect(input.hands.single.pointAt(0)!.imageCoordinates!.x, 0);
      expect(input.hands.single.pointAt(0)!.imageCoordinates!.y, 0);
      expect(input.hands.single.pointAt(8)!.imageCoordinates!.x, 1);
      expect(input.hands.single.pointAt(8)!.imageCoordinates!.y, 1);
      expect(result.trackingStatus, TrackingStatus.tracked);
      expect(result.trackingQuality, closeTo(0.97, 1e-12));
      expect(result.trackingIssues, isEmpty);
      expect(result.canNormalise, isTrue);
    });

    test('completely unusable mixed data returns a precise safe failure', () {
      // Present flags coexist with null, 0.01-confidence, and NaN coordinates.
      // None clears the confidence-and-finiteness gate.
      final input = LandmarkFrameFixtures.completelyUnusableFrame();
      final result = TrackingStateService().process(input);

      expect(input.pose.pointAt(11), isNull);
      expect(input.pose.pointAt(12)!.imageCoordinates!.x.isNaN, isTrue);
      expect(input.hands.single.pointAt(0)!.imageCoordinates!.x.isNaN, isTrue);
      expect(result.trackingStatus, TrackingStatus.absent);
      expect(result.trackingQuality, 0);
      expect(
        result.trackingIssues,
        unorderedEquals(<TrackingIssue>[
          TrackingIssue.noLandmarks,
          TrackingIssue.noHands,
          TrackingIssue.missingShoulders,
          TrackingIssue.lowConfidence,
          TrackingIssue.handednessUncertain,
        ]),
      );
      expect(result.canNormalise, isFalse);
      expect(result.hands.single.pointAt(0)!.imageCoordinates!.x.isNaN, isTrue);
    });

    test('presence flags override stale coordinate arrays', () {
      // MediaPipe group-presence flags are authoritative even when a caller
      // accidentally carries an old coordinate array beside them.
      final result = TrackingStateService().process(
        LandmarkFrameFixtures.absentGroupsWithStaleCoordinatesFrame(),
      );

      expect(result.trackingStatus, TrackingStatus.absent);
      expect(result.trackingQuality, 0);
      expect(
        result.trackingIssues,
        unorderedEquals(<TrackingIssue>[
          TrackingIssue.noLandmarks,
          TrackingIssue.noHands,
          TrackingIssue.missingShoulders,
        ]),
      );
      expect(result.canNormalise, isFalse);
      expect(result.hands.single.trackId, isNull);
      expect(result.pose.pointAt(11)!.imageCoordinates, isNotNull);
    });
  });

  group('TrackingStateService - confidence boundaries', () {
    test('point gate accepts exactly 0.5', () {
      final result = TrackingStateService().process(
        LandmarkFrameFixtures.confidenceBoundaryFrame(0.5),
      );

      expect(result.trackingQuality, closeTo(0.5, 1e-12));
      expect(result.trackingStatus, TrackingStatus.tracked);
      expect(result.trackingIssues, isEmpty);
      expect(result.canNormalise, isTrue);
    });

    test('point gate rejects the value immediately below 0.5', () {
      final result = TrackingStateService().process(
        LandmarkFrameFixtures.confidenceBoundaryFrame(0.499999),
      );

      expect(result.trackingQuality, 0);
      expect(result.trackingStatus, TrackingStatus.absent);
      expect(
        result.trackingIssues,
        unorderedEquals(<TrackingIssue>[
          TrackingIssue.noLandmarks,
          TrackingIssue.noHands,
          TrackingIssue.missingShoulders,
          TrackingIssue.lowConfidence,
        ]),
      );
      expect(result.canNormalise, isFalse);
    });

    test('point gate accepts the value immediately above 0.5', () {
      final result = TrackingStateService().process(
        LandmarkFrameFixtures.confidenceBoundaryFrame(0.500001),
      );

      expect(result.trackingQuality, closeTo(0.500001, 1e-12));
      expect(result.trackingStatus, TrackingStatus.tracked);
      expect(result.trackingIssues, isEmpty);
      expect(result.canNormalise, isTrue);
    });

    test('minimum tracking quality itself is inclusive', () {
      // Set the point gate to zero to isolate the separate 0.5 health-quality
      // threshold from the 0.5 per-point confidence gate.
      const config = TrackingStateNormalisationConfig(confidenceThreshold: 0);
      final exact = TrackingStateService(config: config)
          .process(LandmarkFrameFixtures.confidenceBoundaryFrame(0.5));
      final below = TrackingStateService(config: config)
          .process(LandmarkFrameFixtures.confidenceBoundaryFrame(0.499999));

      expect(exact.trackingQuality, closeTo(0.5, 1e-12));
      expect(exact.trackingStatus, TrackingStatus.tracked);
      expect(below.trackingQuality, closeTo(0.499999, 1e-12));
      expect(below.trackingStatus, TrackingStatus.degraded);
      expect(below.trackingIssues, isEmpty);
    });
  });

  group('TrackingStateService - temporal state and identity', () {
    test('teleport remains tracked because no outlier gate is specified', () {
      // Implementation-defined expectation: current tracking health is based
      // on confidence/completeness, not displacement. A unique settled label
      // also reconnects a hand beyond the 0.35 spatial-match distance.
      final service = TrackingStateService();
      final first = service.process(LandmarkFrameFixtures.fullyTrackedFrame());
      final teleported = service.process(
        LandmarkFrameFixtures.discontinuityFrame(),
      );

      expect(teleported.hands[1].pointAt(0)!.imageCoordinates!.x, 0.05);
      expect(teleported.trackingStatus, TrackingStatus.tracked);
      expect(teleported.trackingQuality, closeTo(0.97, 1e-12));
      expect(teleported.trackingIssues, isEmpty);
      expect(teleported.hands[1].trackId, first.hands[1].trackId);
      expect(teleported.hands[1].handedness, Handedness.right);
      expect(teleported.hands[1].handednessObservationCount, 2);
    });

    test('lost frames change state immediately and recover identity', () {
      // There is no tracking-health hysteresis in this stage: subject
      // selection hysteresis is upstream. Hand identity is retained for the
      // implementation-defined 15-frame lifetime.
      final service = TrackingStateService();
      final tracked = service.process(
        LandmarkFrameFixtures.fullyTrackedFrame(),
      );
      final lost1 = service.process(LandmarkFrameFixtures.noSubjectFrame());
      final lost2 = service.process(
        LandmarkFrameFixtures.noSubjectFrame(
          frameIndex: 102,
          timestamp: LandmarkFrameFixtures.atFrame(2),
        ),
      );
      final lost3 = service.process(
        LandmarkFrameFixtures.noSubjectFrame(
          frameIndex: 103,
          timestamp: LandmarkFrameFixtures.atFrame(3),
        ),
      );
      final recovered = service.process(LandmarkFrameFixtures.recoveryFrame());

      expect(tracked.trackingStatus, TrackingStatus.tracked);
      expect(lost1.trackingStatus, TrackingStatus.absent);
      expect(lost2.trackingStatus, TrackingStatus.absent);
      expect(lost3.trackingStatus, TrackingStatus.absent);
      expect(recovered.trackingStatus, TrackingStatus.tracked);
      expect(recovered.trackingQuality, closeTo(0.97, 1e-12));
      expect(recovered.trackingIssues, isEmpty);
      expect(recovered.hands[0].trackId, tracked.hands[0].trackId);
      expect(recovered.hands[1].trackId, tracked.hands[1].trackId);
      expect(
        recovered.hands.every((hand) => hand.handednessObservationCount == 2),
        isTrue,
      );
    });

    test('zero and negative time deltas reset lifetime state safely', () {
      // The frame index is metadata; capture timestamp controls temporal state.
      final service = TrackingStateService();
      service.process(LandmarkFrameFixtures.fullyTrackedFrame());
      final second = service.process(
        LandmarkFrameFixtures.fullyTrackedFrame(
          frameIndex: 101,
          timestamp: LandmarkFrameFixtures.atFrame(1),
        ),
      );
      final zeroDelta = service.process(
        LandmarkFrameFixtures.invalidTimestampFrame(
          frameIndex: 102,
          timestamp: LandmarkFrameFixtures.atFrame(1),
        ),
      );
      final negativeDelta = service.process(
        LandmarkFrameFixtures.fullyTrackedFrame(
          frameIndex: 103,
          timestamp: LandmarkFrameFixtures.epoch,
        ),
      );

      expect(second.hands.first.handednessObservationCount, 2);
      expect(zeroDelta.trackingStatus, TrackingStatus.tracked);
      expect(zeroDelta.trackingQuality, closeTo(0.97, 1e-12));
      expect(zeroDelta.trackingQuality.isFinite, isTrue);
      expect(
        zeroDelta.hands.every((hand) => hand.handednessObservationCount == 1),
        isTrue,
      );
      expect(negativeDelta.trackingStatus, TrackingStatus.tracked);
      expect(negativeDelta.trackingQuality.isFinite, isTrue);
      expect(
        negativeDelta.hands.every(
          (hand) => hand.handednessObservationCount == 1,
        ),
        isTrue,
      );
    });

    test('missing non-wrist landmark stays null and can reappear', () {
      // Right index tip 8 vanishes; tracking must not copy its previous
      // coordinate. It returns on the next real MediaPipe observation.
      final service = TrackingStateService();
      final first = service.process(LandmarkFrameFixtures.fullyTrackedFrame());
      final missing = service.process(
        LandmarkFrameFixtures.missingLandmarkFrame(),
      );
      final reappeared = service.process(
        LandmarkFrameFixtures.reappearingLandmarkFrame(),
      );

      expect(missing.hands[1].pointAt(8), isNull);
      expect(missing.trackingQuality, closeTo(0.9585714285714285, 1e-12));
      expect(missing.trackingStatus, TrackingStatus.tracked);
      expect(missing.trackingIssues, isEmpty);
      expect(reappeared.hands[1].pointAt(8), isNotNull);
      expect(
        reappeared.hands[1].pointAt(8)!.imageCoordinates!.x,
        closeTo(0.69, 1e-12),
      );
      expect(reappeared.trackingQuality, closeTo(0.97, 1e-12));
      expect(reappeared.hands[1].trackId, first.hands[1].trackId);
    });

    test('spatial matching accepts its exact distance boundary', () {
      const config = TrackingStateNormalisationConfig(
        maximumHandMatchDistance: 0.25,
      );
      final service = TrackingStateService(config: config);
      final first = service.process(_unknownHandFrame(wristX: 0.25));
      final boundary = service.process(
        _unknownHandFrame(
          wristX: 0.50,
          frameIndex: 101,
          timestamp: LandmarkFrameFixtures.atFrame(1),
        ),
      );

      expect(boundary.hands.single.trackId, first.hands.single.trackId);
      expect(boundary.hands.single.handedness, Handedness.unknown);
      expect(boundary.hands.single.handednessUncertain, isTrue);
    });

    test('spatial matching rejects a distance just above its boundary', () {
      const config = TrackingStateNormalisationConfig(
        maximumHandMatchDistance: 0.25,
      );
      final service = TrackingStateService(config: config);
      final first = service.process(_unknownHandFrame(wristX: 0.25));
      final above = service.process(
        _unknownHandFrame(
          wristX: 0.500001,
          frameIndex: 101,
          timestamp: LandmarkFrameFixtures.atFrame(1),
        ),
      );

      expect(above.hands.single.trackId, isNot(first.hands.single.trackId));
      expect(above.hands.single.trackId, 'hand-2');
    });

    test('track expiry is inclusive at the configured frame boundary', () {
      const config = TrackingStateNormalisationConfig(trackExpiryFrames: 2);

      final retainedService = TrackingStateService(config: config);
      final retainedFirst = retainedService.process(
        LandmarkFrameFixtures.fullyTrackedFrame(),
      );
      retainedService.process(LandmarkFrameFixtures.noSubjectFrame());
      final retained = retainedService.process(
        LandmarkFrameFixtures.fullyTrackedFrame(
          frameIndex: 102,
          timestamp: LandmarkFrameFixtures.atFrame(2),
        ),
      );

      final expiredService = TrackingStateService(config: config);
      final expiredFirst = expiredService.process(
        LandmarkFrameFixtures.fullyTrackedFrame(),
      );
      expiredService.process(LandmarkFrameFixtures.noSubjectFrame());
      expiredService.process(
        LandmarkFrameFixtures.noSubjectFrame(
          frameIndex: 102,
          timestamp: LandmarkFrameFixtures.atFrame(2),
        ),
      );
      final expired = expiredService.process(
        LandmarkFrameFixtures.fullyTrackedFrame(
          frameIndex: 103,
          timestamp: LandmarkFrameFixtures.atFrame(3),
        ),
      );

      expect(retained.hands[0].trackId, retainedFirst.hands[0].trackId);
      expect(retained.hands[1].trackId, retainedFirst.hands[1].trackId);
      expect(expired.hands[0].trackId, isNot(expiredFirst.hands[0].trackId));
      expect(expired.hands[1].trackId, isNot(expiredFirst.hands[1].trackId));
    });
  });

  group('TrackingStateService - handedness and measured wrist correction', () {
    test('ambiguous handedness remains represented without dropping hand', () {
      final result = TrackingStateService().process(
        LandmarkFrameFixtures.ambiguousHandednessFrame(),
      );

      expect(result.trackingStatus, TrackingStatus.tracked);
      expect(result.trackingQuality, closeTo(0.97, 1e-12));
      expect(result.hands, hasLength(1));
      expect(result.hands.single.rawHandedness, Handedness.right);
      expect(result.hands.single.handedness, Handedness.unknown);
      expect(
        result.hands.single.handednessRunningAverage,
        closeTo(0.599999, 1e-12),
      );
      expect(result.hands.single.handednessObservationCount, 1);
      expect(result.hands.single.handednessUncertain, isTrue);
      expect(result.trackingIssues, <TrackingIssue>[
        TrackingIssue.handednessUncertain,
      ]);
    });

    test(
      'duplicate handedness retains both hands and marks both uncertain',
      () {
        final result = TrackingStateService().process(
          LandmarkFrameFixtures.duplicateHandednessFrame(),
        );

        expect(result.trackingStatus, TrackingStatus.tracked);
        expect(result.trackingQuality, closeTo(0.97, 1e-12));
        expect(result.hands, hasLength(2));
        expect(result.hands.map((hand) => hand.trackId).toSet(), hasLength(2));
        expect(result.hands.every((hand) => hand.isPresent), isTrue);
        expect(
          result.hands.every((hand) => hand.handedness == Handedness.right),
          isTrue,
        );
        expect(result.hands.every((hand) => hand.handednessUncertain), isTrue);
        expect(result.trackingIssues, <TrackingIssue>[
          TrackingIssue.handednessUncertain,
        ]);
      },
    );

    test('right handedness decision threshold is inclusive', () {
      final below = TrackingStateService().process(
        _handednessFrame(Handedness.right, 0.599999),
      );
      final exact = TrackingStateService().process(
        _handednessFrame(Handedness.right, 0.6),
      );
      final above = TrackingStateService().process(
        _handednessFrame(Handedness.right, 0.600001),
      );

      expect(below.hands.single.handedness, Handedness.unknown);
      expect(below.hands.single.handednessRunningAverage, 0.599999);
      expect(below.hands.single.handednessUncertain, isTrue);
      expect(exact.hands.single.handedness, Handedness.right);
      expect(exact.hands.single.handednessRunningAverage, 0.6);
      expect(exact.hands.single.handednessUncertain, isFalse);
      expect(above.hands.single.handedness, Handedness.right);
      expect(above.hands.single.handednessRunningAverage, 0.600001);
      expect(above.hands.single.handednessUncertain, isFalse);
    });

    test('left handedness decision threshold is inclusive at 0.4', () {
      final belowScore = TrackingStateService().process(
        _handednessFrame(Handedness.left, 0.599999),
      );
      final exactScore = TrackingStateService().process(
        _handednessFrame(Handedness.left, 0.6),
      );
      final aboveScore = TrackingStateService().process(
        _handednessFrame(Handedness.left, 0.600001),
      );

      expect(belowScore.hands.single.handedness, Handedness.unknown);
      expect(
        belowScore.hands.single.handednessRunningAverage,
        closeTo(0.400001, 1e-12),
      );
      expect(exactScore.hands.single.handedness, Handedness.left);
      expect(
        exactScore.hands.single.handednessRunningAverage,
        closeTo(0.4, 1e-12),
      );
      expect(aboveScore.hands.single.handedness, Handedness.left);
      expect(
        aboveScore.hands.single.handednessRunningAverage,
        closeTo(0.399999, 1e-12),
      );
    });

    test('one contradictory observation does not flip lifetime handedness', () {
      final service = TrackingStateService();
      final first = service.process(
        LandmarkFrameFixtures.mediaPipeFrame(
          hands: <HandLandmarkGroup>[
            LandmarkFrameFixtures.realisticHand(rawHandedness: Handedness.left),
          ],
        ),
      );
      final contradicted = service.process(
        LandmarkFrameFixtures.mediaPipeFrame(
          frameIndex: 101,
          timestamp: LandmarkFrameFixtures.atFrame(1),
          hands: <HandLandmarkGroup>[
            LandmarkFrameFixtures.realisticHand(
              rawHandedness: Handedness.right,
              wristX: 0.31,
            ),
          ],
        ),
      );

      expect(contradicted.hands.single.trackId, first.hands.single.trackId);
      expect(contradicted.hands.single.rawHandedness, Handedness.right);
      expect(contradicted.hands.single.handedness, Handedness.left);
      expect(
        contradicted.hands.single.handednessRunningAverage,
        closeTo(0.5, 1e-12),
      );
      expect(contradicted.hands.single.handednessObservationCount, 2);
    });

    test('measured pose wrist replaces a rejected hand wrist', () {
      // This is the one PLN correction that fills a hand slot: it copies an
      // actually observed pose wrist and records its source; it is not guessed.
      final input = LandmarkFrameFixtures.mediaPipeFrame(
        hands: <HandLandmarkGroup>[
          LandmarkFrameFixtures.realisticHand(
            rawHandedness: Handedness.left,
            confidenceOverrides: const <int, double>{0: 0.1},
          ),
        ],
      );
      final result = TrackingStateService().process(input);
      final wrist = result.hands.single.pointAt(0)!;
      const expectedHandQuality = (20 * 0.96 + 0.98) / 21;
      const expectedQuality = (0.98 + expectedHandQuality) / 2;

      expect(wrist.source, LandmarkSource.poseWristSubstitution);
      expect(wrist.confidence, 0.98);
      expect(wrist.imageCoordinates!.x, 0.30);
      expect(wrist.imageCoordinates!.y, 0.58);
      expect(wrist.worldCoordinates, isNull);
      expect(result.trackingQuality, closeTo(expectedQuality, 1e-12));
      expect(result.trackingStatus, TrackingStatus.tracked);
      expect(result.trackingIssues, isEmpty);
    });

    test('missing hand and pose wrists are never fabricated', () {
      final input = LandmarkFrameFixtures.mediaPipeFrame(
        pose: LandmarkFrameFixtures.realisticPose(
          missingIndices: const <int>{15},
        ),
        hands: <HandLandmarkGroup>[
          LandmarkFrameFixtures.realisticHand(
            rawHandedness: Handedness.left,
            missingIndices: const <int>{0},
          ),
        ],
      );
      final result = TrackingStateService().process(input);
      const expectedPoseQuality = 7 * 0.98 / 8;
      const expectedHandQuality = 20 * 0.96 / 21;
      const expectedQuality = (expectedPoseQuality + expectedHandQuality) / 2;

      expect(result.hands.single.pointAt(0), isNull);
      expect(result.pose.pointAt(15), isNull);
      expect(result.trackingQuality, closeTo(expectedQuality, 1e-12));
      expect(result.trackingStatus, TrackingStatus.tracked);
      expect(result.trackingIssues, isEmpty);
    });
  });
}

LandmarkFrame _unknownHandFrame({
  required double wristX,
  int frameIndex = 100,
  DateTime? timestamp,
}) => LandmarkFrameFixtures.mediaPipeFrame(
  frameIndex: frameIndex,
  timestamp: timestamp,
  hands: <HandLandmarkGroup>[
    LandmarkFrameFixtures.realisticHand(
      rawHandedness: Handedness.unknown,
      handednessScore: 0.5,
      wristX: wristX,
    ),
  ],
);

LandmarkFrame _handednessFrame(Handedness handedness, double score) =>
    LandmarkFrameFixtures.mediaPipeFrame(
      hands: <HandLandmarkGroup>[
        LandmarkFrameFixtures.realisticHand(
          rawHandedness: handedness,
          handednessScore: score,
        ),
      ],
    );
