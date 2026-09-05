import 'package:apptesting/models/landmark_frame.dart';
import 'package:apptesting/services/tracking_state_normalisation_service.dart';
import 'package:flutter_test/flutter_test.dart';

import 'fixtures/landmark_frame_fixtures.dart';

// Normalisation boundary under test:
// Harold/MediaPipe LandmarkFrame -> already-assessed tracking output
// -> LandmarkNormalisationService -> LandmarkFrame for segmentation.
//
// TrackingStateService is deliberately not invoked in this file. Its tests are
// separate, so a failure here identifies the normalisation stage.
void main() {
  group('LandmarkNormalisationService - spatial normalisation', () {
    test('perfect tracking maps exact shoulder-relative coordinates', () {
      // Harold: complete high-confidence pose, face, and two hands at t=0.
      // Tracking: tracked, quality 0.97, stable hand IDs and handedness.
      // Normalisation: centre=(0.5, 0.35), scale=0.2.
      final input = _trackingOutput(LandmarkFrameFixtures.fullyTrackedFrame());

      final output = LandmarkNormalisationService().process(input);

      expect(output.frameIndex, 100);
      expect(output.timestamp, LandmarkFrameFixtures.epoch);
      expect(output.subjectId, LandmarkFrameFixtures.defaultSubjectId);
      expect(output.coordinateSpace, LandmarkCoordinateSpace.bodyNormalised);
      expect(output.trackingStatus, TrackingStatus.tracked);
      expect(output.trackingQuality, closeTo(0.97, 1e-12));
      expect(output.trackingIssues, isEmpty);
      expect(output.canNormalise, isTrue);
      expect(output.normalisationAnchorIsStale, isFalse);
      _expectCoordinates(output.normalisationOrigin, x: 0.5, y: 0.35);
      expect(output.normalisationScale, closeTo(0.2, 1e-12));
      _expectCoordinates(
        output.pose.pointAt(11)!.normalisedCoordinates,
        x: -0.5,
        y: 0,
      );
      _expectCoordinates(
        output.pose.pointAt(12)!.normalisedCoordinates,
        x: 0.5,
        y: 0,
      );
      _expectCoordinates(
        output.hands[0].pointAt(0)!.normalisedCoordinates,
        x: -1,
        y: 1.15,
      );
      _expectCoordinates(
        output.hands[1].pointAt(0)!.normalisedCoordinates,
        x: 1,
        y: 1.15,
      );
      _expectCoordinates(
        output.hands[1].pointAt(0)!.imageCoordinates,
        x: 0.7,
        y: 0.58,
        z: -0.01,
      );
    });

    test('body coordinates are invariant to image translation and scale', () {
      // The second Harold frame is the same observation scaled by 0.5 and
      // translated so the shoulder centre moves from (0.5,0.35) to (0.45,0.4).
      final raw = LandmarkFrameFixtures.fullyTrackedFrame();
      final transformedRaw = _transformImageFrame(
        raw,
        factor: 0.5,
        fromOrigin: const LandmarkCoordinates(x: 0.5, y: 0.35),
        toOrigin: const LandmarkCoordinates(x: 0.45, y: 0.4),
      );
      final first = LandmarkNormalisationService().process(
        _trackingOutput(raw),
      );
      final transformed = LandmarkNormalisationService().process(
        _trackingOutput(transformedRaw),
      );

      expect(first.normalisationScale, closeTo(0.2, 1e-12));
      expect(transformed.normalisationScale, closeTo(0.1, 1e-12));
      _expectCoordinates(transformed.normalisationOrigin, x: 0.45, y: 0.4);
      for (final index in <int>[11, 12, 15, 16, 23, 24]) {
        _expectSameCoordinates(
          transformed.pose.pointAt(index)!.normalisedCoordinates,
          first.pose.pointAt(index)!.normalisedCoordinates,
        );
      }
      for (var handIndex = 0; handIndex < 2; handIndex += 1) {
        for (final pointIndex in <int>[0, 4, 8, 12, 16, 20]) {
          _expectSameCoordinates(
            transformed.hands[handIndex]
                .pointAt(pointIndex)!
                .normalisedCoordinates,
            first.hands[handIndex].pointAt(pointIndex)!.normalisedCoordinates,
          );
        }
      }
    });

    test('a completely missing subject produces no anchor or coordinates', () {
      final input = _trackingOutput(
        LandmarkFrameFixtures.noSubjectFrame(),
        status: TrackingStatus.absent,
        quality: 0,
        issues: const <TrackingIssue>[
          TrackingIssue.noLandmarks,
          TrackingIssue.noHands,
          TrackingIssue.missingShoulders,
        ],
        canNormalise: false,
      );

      final output = LandmarkNormalisationService().process(input);

      expect(output.coordinateSpace, LandmarkCoordinateSpace.bodyNormalised);
      expect(output.trackingStatus, TrackingStatus.absent);
      expect(output.trackingQuality, 0);
      expect(output.pose.isPresent, isFalse);
      expect(output.face.isPresent, isFalse);
      expect(output.hands, isEmpty);
      expect(output.canNormalise, isFalse);
      expect(output.normalisationOrigin, isNull);
      expect(output.normalisationScale, isNull);
      expect(output.normalisationAnchorIsStale, isFalse);
      expect(
        output.trackingIssues,
        unorderedEquals(<TrackingIssue>[
          TrackingIssue.noLandmarks,
          TrackingIssue.noHands,
          TrackingIssue.missingShoulders,
        ]),
      );
    });

    test('one shoulder cannot create a fresh body anchor', () {
      final input = _trackingOutput(
        LandmarkFrameFixtures.oneShoulderMissingFrame(),
        status: TrackingStatus.degraded,
        quality: 0.90875,
        issues: const <TrackingIssue>[TrackingIssue.missingShoulders],
        canNormalise: false,
      );

      final output = LandmarkNormalisationService().process(input);

      expect(output.trackingStatus, TrackingStatus.degraded);
      _expectCoordinates(
        output.pose.pointAt(11)!.imageCoordinates,
        x: 0.4,
        y: 0.35,
        z: -0.05,
      );
      expect(output.pose.pointAt(12), isNull);
      expect(output.canNormalise, isFalse);
      expect(output.normalisationOrigin, isNull);
      expect(output.normalisationScale, isNull);
      _expectNoBodyDerived(output);
    });

    test('shoulders just below minimum scale are rejected safely', () {
      final input = _trackingOutput(
        LandmarkFrameFixtures.tinyShoulderScaleFrame(),
        status: TrackingStatus.degraded,
        issues: const <TrackingIssue>[TrackingIssue.missingShoulders],
        canNormalise: false,
      );

      final output = LandmarkNormalisationService().process(input);

      expect(output.canNormalise, isFalse);
      expect(output.normalisationOrigin, isNull);
      expect(output.normalisationScale, isNull);
      expect(output.normalisationAnchorIsStale, isFalse);
      _expectNoBodyDerived(output);
    });

    test('shoulders exactly at minimum scale are accepted and finite', () {
      final input = _trackingOutput(
        LandmarkFrameFixtures.minimumShoulderScaleFrame(),
      );

      final output = LandmarkNormalisationService().process(input);

      expect(output.canNormalise, isTrue);
      _expectCoordinates(output.normalisationOrigin, x: 0.00005, y: 0.35);
      expect(output.normalisationScale, closeTo(0.0001, 1e-15));
      _expectCoordinates(
        output.pose.pointAt(11)!.normalisedCoordinates,
        x: -0.5,
        y: 0,
      );
      _expectCoordinates(
        output.pose.pointAt(12)!.normalisedCoordinates,
        x: 0.5,
        y: 0,
      );
      _expectAllDerivedCoordinatesFinite(output);
    });

    test('almost full-image shoulder scale is accepted without a max gate', () {
      // Implementation-defined: only a minimum shoulder scale is configured.
      final input = _trackingOutput(
        LandmarkFrameFixtures.largeShoulderScaleFrame(),
      );

      final output = LandmarkNormalisationService().process(input);

      expect(output.canNormalise, isTrue);
      _expectCoordinates(output.normalisationOrigin, x: 0.5, y: 0.35);
      expect(output.normalisationScale, closeTo(0.98, 1e-12));
      _expectCoordinates(
        output.hands[0].pointAt(0)!.normalisedCoordinates,
        x: -0.20408163265306123,
        y: 0.23469387755102042,
      );
      _expectCoordinates(
        output.hands[1].pointAt(0)!.normalisedCoordinates,
        x: 0.20408163265306123,
        y: 0.23469387755102042,
      );
      _expectAllDerivedCoordinatesFinite(output);
    });

    test('image-boundary coordinate extremes remain finite', () {
      final input = _trackingOutput(
        LandmarkFrameFixtures.coordinateExtremesFrame(),
      );

      final output = LandmarkNormalisationService().process(input);

      _expectCoordinates(output.normalisationOrigin, x: 0.5, y: 0.5);
      expect(output.normalisationScale, closeTo(1, 1e-12));
      _expectCoordinates(
        output.pose.pointAt(11)!.normalisedCoordinates,
        x: -0.5,
        y: 0,
      );
      _expectCoordinates(
        output.pose.pointAt(12)!.normalisedCoordinates,
        x: 0.5,
        y: 0,
      );
      _expectCoordinates(
        output.hands.single.pointAt(0)!.normalisedCoordinates,
        x: -0.5,
        y: -0.5,
      );
      _expectCoordinates(
        output.hands.single.pointAt(8)!.normalisedCoordinates,
        x: 0.5,
        y: 0.5,
      );
      _expectAllDerivedCoordinatesFinite(output);
    });
  });

  group('LandmarkNormalisationService - confidence and absence gates', () {
    test(
      'very low confidence retains raw measurements but derives nothing',
      () {
        final input = _trackingOutput(
          LandmarkFrameFixtures.lowConfidenceFrame(),
          status: TrackingStatus.degraded,
          quality: 0,
          issues: const <TrackingIssue>[
            TrackingIssue.noHands,
            TrackingIssue.missingShoulders,
            TrackingIssue.lowConfidence,
          ],
          canNormalise: false,
        );

        final output = LandmarkNormalisationService().process(input);

        expect(output.trackingStatus, TrackingStatus.degraded);
        expect(output.canNormalise, isFalse);
        final shoulder = output.pose.pointAt(11)!;
        expect(shoulder.confidence, closeTo(0.1, 1e-12));
        _expectCoordinates(
          shoulder.imageCoordinates,
          x: 0.4,
          y: 0.35,
          z: -0.05,
        );
        expect(shoulder.normalisedCoordinates, isNull);
        expect(shoulder.velocity, isNull);
        expect(shoulder.acceleration, isNull);
        expect(output.hands[0].pointAt(0)!.normalisedCoordinates, isNull);
        expect(output.hands[1].pointAt(20)!.normalisedCoordinates, isNull);
        _expectNoBodyDerived(output);
      },
    );

    test('mixed confidence gates each point independently', () {
      final input = _trackingOutput(
        LandmarkFrameFixtures.mixedConfidenceFrame(),
        status: TrackingStatus.degraded,
        quality: 0.37392857142857144,
        issues: const <TrackingIssue>[TrackingIssue.lowConfidence],
      );

      final output = LandmarkNormalisationService().process(input);

      expect(output.canNormalise, isTrue);
      _expectCoordinates(
        output.pose.pointAt(11)!.normalisedCoordinates,
        x: -0.5,
        y: 0,
      );
      expect(output.pose.pointAt(0)!.confidence, closeTo(0.01, 1e-12));
      expect(output.pose.pointAt(0)!.normalisedCoordinates, isNull);
      for (var index = 0; index <= 10; index += 1) {
        final inputPoint = input.hands.single.pointAt(index)!;
        final inputImage = inputPoint.imageCoordinates!;
        final outputPoint = output.hands.single.pointAt(index)!;
        expect(outputPoint.confidence, 0.96);
        _expectCoordinates(
          outputPoint.normalisedCoordinates,
          x: (inputImage.x - 0.5) / 0.2,
          y: (inputImage.y - 0.35) / 0.2,
        );
      }
      for (var index = 11; index < 21; index += 1) {
        final point = output.hands.single.pointAt(index)!;
        expect(point.confidence, 0.01);
        expect(point.imageCoordinates, isNotNull);
        expect(point.normalisedCoordinates, isNull);
        expect(point.velocity, isNull);
        expect(point.acceleration, isNull);
      }
      _expectCoordinates(
        output.hands.single.pointAt(0)!.normalisedCoordinates,
        x: 1,
        y: 1.15,
      );
    });

    test('missing hand group leaves pose normalised and invents no hand', () {
      final input = _trackingOutput(
        LandmarkFrameFixtures.missingHandsFrame(),
        status: TrackingStatus.degraded,
        quality: 0.49,
        issues: const <TrackingIssue>[TrackingIssue.noHands],
      );

      final output = LandmarkNormalisationService().process(input);

      expect(output.trackingStatus, TrackingStatus.degraded);
      expect(output.canNormalise, isTrue);
      expect(output.hands, isEmpty);
      _expectCoordinates(
        output.pose.pointAt(11)!.normalisedCoordinates,
        x: -0.5,
        y: 0,
      );
      _expectCoordinates(
        output.face.pointAt(13)!.normalisedCoordinates,
        x: 0,
        y: -0.625,
      );
    });

    test(
      'missing pose on a fresh service leaves hand coordinates raw only',
      () {
        final input = _trackingOutput(
          LandmarkFrameFixtures.missingPoseFrame(),
          status: TrackingStatus.degraded,
          quality: 0.48,
          issues: const <TrackingIssue>[TrackingIssue.missingShoulders],
          canNormalise: false,
        );

        final output = LandmarkNormalisationService().process(input);

        expect(output.pose.isPresent, isFalse);
        expect(output.canNormalise, isFalse);
        expect(output.normalisationOrigin, isNull);
        expect(output.normalisationScale, isNull);
        _expectCoordinates(
          output.hands[1].pointAt(0)!.imageCoordinates,
          x: 0.7,
          y: 0.58,
          z: -0.01,
        );
        expect(output.hands[1].pointAt(0)!.normalisedCoordinates, isNull);
        expect(output.hands[1].pointAt(0)!.velocity, isNull);
        expect(output.hands[1].pointAt(0)!.acceleration, isNull);
      },
    );

    for (final boundaryCase
        in <({String name, double confidence, bool accepted})>[
          (name: 'just below 0.5', confidence: 0.499999, accepted: false),
          (name: 'exactly 0.5', confidence: 0.5, accepted: true),
          (name: 'just above 0.5', confidence: 0.500001, accepted: true),
        ]) {
      test('confidence gate ${boundaryCase.name} is inclusive', () {
        final raw = LandmarkFrameFixtures.confidenceBoundaryFrame(
          boundaryCase.confidence,
        );
        final input = _trackingOutput(
          raw,
          status: boundaryCase.accepted
              ? TrackingStatus.tracked
              : TrackingStatus.absent,
          quality: boundaryCase.accepted ? boundaryCase.confidence : 0,
          issues: boundaryCase.accepted
              ? const <TrackingIssue>[]
              : const <TrackingIssue>[
                  TrackingIssue.noLandmarks,
                  TrackingIssue.noHands,
                  TrackingIssue.missingShoulders,
                  TrackingIssue.lowConfidence,
                ],
          canNormalise: boundaryCase.accepted,
        );

        final output = LandmarkNormalisationService().process(input);
        final rightWrist = output.hands[1].pointAt(0)!;

        expect(rightWrist.confidence, boundaryCase.confidence);
        expect(output.canNormalise, boundaryCase.accepted);
        if (boundaryCase.accepted) {
          expect(output.normalisationScale, closeTo(0.2, 1e-12));
          _expectCoordinates(rightWrist.normalisedCoordinates, x: 1, y: 1.15);
          expect(rightWrist.velocity, isNull);
          expect(rightWrist.acceleration, isNull);
        } else {
          expect(output.normalisationScale, isNull);
          expect(rightWrist.normalisedCoordinates, isNull);
          expect(rightWrist.velocity, isNull);
          expect(rightWrist.acceleration, isNull);
        }
      });
    }

    test('false presence flags override attached stale coordinates', () {
      final input = _trackingOutput(
        LandmarkFrameFixtures.absentGroupsWithStaleCoordinatesFrame(),
        status: TrackingStatus.absent,
        quality: 0,
        issues: const <TrackingIssue>[
          TrackingIssue.noLandmarks,
          TrackingIssue.noHands,
          TrackingIssue.missingShoulders,
        ],
        canNormalise: false,
      );

      final output = LandmarkNormalisationService().process(input);

      expect(output.pose.isPresent, isFalse);
      expect(output.face.isPresent, isFalse);
      expect(output.hands.single.isPresent, isFalse);
      _expectCoordinates(
        output.pose.pointAt(11)!.imageCoordinates,
        x: 0.4,
        y: 0.35,
        z: -0.05,
      );
      expect(output.pose.pointAt(11)!.normalisedCoordinates, isNull);
      expect(output.face.pointAt(13)!.normalisedCoordinates, isNull);
      expect(output.hands.single.pointAt(0)!.normalisedCoordinates, isNull);
      expect(output.canNormalise, isFalse);
    });

    test('ambiguous handedness metadata does not remove valid geometry', () {
      final input = _trackingOutput(
        LandmarkFrameFixtures.ambiguousHandednessFrame(),
        issues: const <TrackingIssue>[TrackingIssue.handednessUncertain],
      );

      final output = LandmarkNormalisationService().process(input);
      final hand = output.hands.single;

      expect(hand.rawHandedness, Handedness.right);
      expect(hand.handedness, Handedness.unknown);
      expect(hand.handednessRunningAverage, closeTo(0.599999, 1e-12));
      expect(hand.handednessObservationCount, 1);
      expect(hand.handednessUncertain, isTrue);
      expect(
        output.trackingIssues,
        unorderedEquals(<TrackingIssue>[TrackingIssue.handednessUncertain]),
      );
      _expectCoordinates(hand.pointAt(0)!.normalisedCoordinates, x: 1, y: 1.15);
    });

    test('duplicate handedness retains and normalises all 42 hand points', () {
      final input = _trackingOutput(
        LandmarkFrameFixtures.duplicateHandednessFrame(),
        issues: const <TrackingIssue>[TrackingIssue.handednessUncertain],
      );

      final output = LandmarkNormalisationService().process(input);

      expect(output.hands, hasLength(2));
      expect(output.hands.every((hand) => hand.isPresent), isTrue);
      expect(output.hands.every((hand) => hand.handednessUncertain), isTrue);
      expect(
        output.hands
            .expand((hand) => hand.landmarks)
            .whereType<LandmarkPoint>()
            .length,
        42,
      );
      for (var handIndex = 0; handIndex < output.hands.length; handIndex += 1) {
        for (var pointIndex = 0; pointIndex < 21; pointIndex += 1) {
          final inputImage = input.hands[handIndex]
              .pointAt(pointIndex)!
              .imageCoordinates!;
          _expectCoordinates(
            output.hands[handIndex].pointAt(pointIndex)!.normalisedCoordinates,
            x: (inputImage.x - 0.5) / 0.2,
            y: (inputImage.y - 0.35) / 0.2,
          );
        }
      }
    });

    test('a completely unusable frame fails safely without NaN output', () {
      final input = _trackingOutput(
        LandmarkFrameFixtures.completelyUnusableFrame(),
        status: TrackingStatus.absent,
        quality: 0,
        issues: const <TrackingIssue>[
          TrackingIssue.noLandmarks,
          TrackingIssue.noHands,
          TrackingIssue.missingShoulders,
          TrackingIssue.lowConfidence,
          TrackingIssue.handednessUncertain,
        ],
        canNormalise: false,
      );

      final output = LandmarkNormalisationService().process(input);

      expect(output.trackingStatus, TrackingStatus.absent);
      expect(output.trackingQuality, 0);
      expect(output.canNormalise, isFalse);
      expect(output.normalisationOrigin, isNull);
      expect(output.normalisationScale, isNull);
      expect(output.normalisationAnchorIsStale, isFalse);
      expect(output.pose.pointAt(11), isNull);
      expect(output.pose.pointAt(12)!.imageCoordinates!.x.isNaN, isTrue);
      expect(output.pose.pointAt(12)!.normalisedCoordinates, isNull);
      expect(output.hands.single.pointAt(0)!.imageCoordinates!.x.isNaN, isTrue);
      expect(output.hands.single.pointAt(0)!.normalisedCoordinates, isNull);
      _expectNoBodyDerived(output);
    });
  });

  group('LandmarkNormalisationService - temporal output', () {
    test('first frame has exact position and no derivatives', () {
      final output = LandmarkNormalisationService().process(
        _trackingOutput(LandmarkFrameFixtures.fullyTrackedFrame()),
      );

      final wrist = output.hands[1].pointAt(0)!;
      _expectCoordinates(wrist.normalisedCoordinates, x: 1, y: 1.15);
      expect(wrist.velocity, isNull);
      expect(wrist.acceleration, isNull);
    });

    test('30 FPS motion has precise velocity and acceleration', () {
      const cutoff = 1000000000.0;
      final service = LandmarkNormalisationService(
        config: const TrackingStateNormalisationConfig(
          smoothingCutoffHz: cutoff,
          normalisationAnchorTimeConstant: Duration.zero,
        ),
      );
      final first = service.process(_trackingOutput(_rightWristFrame(0.70, 0)));
      final second = service.process(
        _trackingOutput(_rightWristFrame(0.72, 1)),
      );
      final third = service.process(_trackingOutput(_rightWristFrame(0.76, 2)));

      final firstPoint = first.hands[1].pointAt(0)!;
      final secondPoint = second.hands[1].pointAt(0)!;
      final thirdPoint = third.hands[1].pointAt(0)!;
      _expectCoordinates(firstPoint.normalisedCoordinates, x: 1, y: 1.15);
      expect(firstPoint.velocity, isNull);
      expect(firstPoint.acceleration, isNull);
      _expectCoordinates(
        secondPoint.normalisedCoordinates,
        x: 1.09999999952253,
        y: 1.15,
        tolerance: 1e-9,
      );
      _expectCoordinates(
        secondPoint.velocity,
        x: 3.00002998597577,
        y: 0,
        tolerance: 1e-6,
      );
      expect(secondPoint.acceleration, isNull);
      _expectCoordinates(
        thirdPoint.normalisedCoordinates,
        x: 1.29999999904506,
        y: 1.15,
        tolerance: 1e-9,
      );
      _expectCoordinates(
        thirdPoint.velocity,
        x: 6.00005998627577,
        y: 0,
        tolerance: 1e-6,
      );
      _expectCoordinates(
        thirdPoint.acceleration,
        x: 90.0018000270002,
        y: 0,
        tolerance: 1e-4,
      );
    });

    test('a sudden teleport remains finite and exposes the velocity spike', () {
      // Implementation-defined: normalisation has no teleport rejection. The
      // tracking-state fixture remains tracked, so this stage reports the
      // filtered jump rather than inventing a discontinuity status.
      final service = LandmarkNormalisationService();
      service.process(
        _trackingOutput(LandmarkFrameFixtures.fullyTrackedFrame()),
      );

      final output = service.process(
        _trackingOutput(LandmarkFrameFixtures.discontinuityFrame()),
      );
      final wrist = output.hands[1].pointAt(0)!;

      expect(output.trackingStatus, TrackingStatus.tracked);
      _expectCoordinates(
        wrist.normalisedCoordinates,
        x: -0.809795833508423,
        y: 1.15,
        tolerance: 1e-9,
      );
      _expectCoordinates(
        wrist.velocity,
        x: -54.2944179494322,
        y: 0,
        tolerance: 1e-8,
      );
      expect(wrist.acceleration, isNull);
      expect(wrist.normalisedCoordinates!.isFinite, isTrue);
      expect(wrist.velocity!.isFinite, isTrue);
    });

    for (final timeCase in <({String name, Duration offset})>[
      (name: 'zero', offset: Duration.zero),
      (name: 'negative', offset: Duration(microseconds: -1)),
    ]) {
      test('${timeCase.name} time delta resets derivatives safely', () {
        final service = LandmarkNormalisationService();
        service.process(
          _trackingOutput(LandmarkFrameFixtures.fullyTrackedFrame()),
        );
        final raw = _rightWristFrame(
          0.72,
          1,
          timestamp: LandmarkFrameFixtures.epoch.add(timeCase.offset),
        );

        final output = service.process(_trackingOutput(raw));
        final wrist = output.hands[1].pointAt(0)!;

        _expectCoordinates(wrist.normalisedCoordinates, x: 1.1, y: 1.15);
        expect(wrist.velocity, isNull);
        expect(wrist.acceleration, isNull);
        expect(wrist.normalisedCoordinates!.isFinite, isTrue);
      });
    }

    test('a 250 ms gap retains history while 251 ms resets it', () {
      const config = TrackingStateNormalisationConfig(
        smoothingCutoffHz: 1000000000,
        normalisationAnchorTimeConstant: Duration.zero,
      );
      final exactService = LandmarkNormalisationService(config: config);
      exactService.process(
        _trackingOutput(LandmarkFrameFixtures.fullyTrackedFrame()),
      );
      final exact = exactService.process(
        _trackingOutput(
          _rightWristFrame(
            0.72,
            1,
            timestamp: LandmarkFrameFixtures.epoch.add(
              const Duration(milliseconds: 250),
            ),
          ),
        ),
      );

      final overService = LandmarkNormalisationService(config: config);
      overService.process(
        _trackingOutput(LandmarkFrameFixtures.fullyTrackedFrame()),
      );
      final over = overService.process(
        _trackingOutput(
          _rightWristFrame(
            0.72,
            1,
            timestamp: LandmarkFrameFixtures.epoch.add(
              const Duration(milliseconds: 251),
            ),
          ),
        ),
      );

      _expectCoordinates(
        exact.hands[1].pointAt(0)!.velocity,
        x: 0.3999999997453514,
        y: 0,
        tolerance: 1e-8,
      );
      expect(exact.hands[1].pointAt(0)!.acceleration, isNull);
      _expectCoordinates(
        over.hands[1].pointAt(0)!.normalisedCoordinates,
        x: 1.1,
        y: 1.15,
      );
      expect(over.hands[1].pointAt(0)!.velocity, isNull);
      expect(over.hands[1].pointAt(0)!.acceleration, isNull);
    });

    test('a missing landmark is not reused and reappears without velocity', () {
      final service = LandmarkNormalisationService();
      service.process(
        _trackingOutput(LandmarkFrameFixtures.fullyTrackedFrame()),
      );

      final missing = service.process(
        _trackingOutput(LandmarkFrameFixtures.missingLandmarkFrame()),
      );
      final recovered = service.process(
        _trackingOutput(LandmarkFrameFixtures.reappearingLandmarkFrame()),
      );

      expect(missing.hands[1].landmarks[8], isNull);
      final point = recovered.hands[1].pointAt(8)!;
      _expectCoordinates(point.normalisedCoordinates, x: 0.95, y: 0.225);
      expect(point.velocity, isNull);
      expect(point.acceleration, isNull);
    });

    test('consecutive lost frames keep only a stale anchor then recover', () {
      final service = LandmarkNormalisationService();
      service.process(
        _trackingOutput(LandmarkFrameFixtures.fullyTrackedFrame()),
      );

      LandmarkFrame? lastLost;
      for (var offset = 1; offset <= 3; offset += 1) {
        lastLost = service.process(
          _trackingOutput(
            LandmarkFrameFixtures.noSubjectFrame(
              frameIndex: 100 + offset,
              timestamp: LandmarkFrameFixtures.atFrame(offset),
            ),
            status: TrackingStatus.absent,
            quality: 0,
            issues: const <TrackingIssue>[
              TrackingIssue.noLandmarks,
              TrackingIssue.noHands,
              TrackingIssue.missingShoulders,
            ],
            canNormalise: false,
          ),
        );
      }

      expect(lastLost!.trackingStatus, TrackingStatus.absent);
      expect(lastLost.canNormalise, isTrue);
      expect(lastLost.normalisationAnchorIsStale, isTrue);
      _expectCoordinates(lastLost.normalisationOrigin, x: 0.5, y: 0.35);
      expect(lastLost.normalisationScale, closeTo(0.2, 1e-12));
      expect(lastLost.pose.landmarks, isEmpty);
      expect(lastLost.hands, isEmpty);
      expect(
        lastLost.trackingIssues,
        contains(TrackingIssue.staleNormalisationAnchor),
      );

      final recovered = service.process(
        _trackingOutput(LandmarkFrameFixtures.recoveryFrame()),
      );
      final recoveredWrist = recovered.hands[1].pointAt(0)!;

      expect(recovered.trackingStatus, TrackingStatus.tracked);
      expect(recovered.canNormalise, isTrue);
      expect(recovered.normalisationAnchorIsStale, isFalse);
      expect(
        recovered.trackingIssues,
        isNot(contains(TrackingIssue.staleNormalisationAnchor)),
      );
      _expectCoordinates(recoveredWrist.normalisedCoordinates, x: 1, y: 1.15);
      expect(recoveredWrist.velocity, isNull);
      expect(recoveredWrist.acceleration, isNull);
    });

    test('stale anchor is valid at 500 ms and expires at 501 ms', () {
      final service = LandmarkNormalisationService();
      service.process(
        _trackingOutput(LandmarkFrameFixtures.fullyTrackedFrame()),
      );

      LandmarkFrame? exactBoundary;
      for (final milliseconds in <int>[200, 400, 500]) {
        exactBoundary = service.process(
          _trackingOutput(
            LandmarkFrameFixtures.missingPoseFrame(
              frameIndex: 100 + milliseconds,
              timestamp: LandmarkFrameFixtures.epoch.add(
                Duration(milliseconds: milliseconds),
              ),
            ),
            status: TrackingStatus.degraded,
            quality: 0.48,
            issues: const <TrackingIssue>[TrackingIssue.missingShoulders],
            canNormalise: false,
          ),
        );
      }

      expect(exactBoundary!.canNormalise, isTrue);
      expect(exactBoundary.normalisationAnchorIsStale, isTrue);
      expect(exactBoundary.normalisationScale, closeTo(0.2, 1e-12));
      _expectCoordinates(
        exactBoundary.hands[1].pointAt(0)!.normalisedCoordinates,
        x: 1,
        y: 1.15,
      );

      final expired = service.process(
        _trackingOutput(
          LandmarkFrameFixtures.missingPoseFrame(
            frameIndex: 602,
            timestamp: LandmarkFrameFixtures.epoch.add(
              const Duration(milliseconds: 501),
            ),
          ),
          status: TrackingStatus.degraded,
          quality: 0.48,
          issues: const <TrackingIssue>[TrackingIssue.missingShoulders],
          canNormalise: false,
        ),
      );

      expect(expired.canNormalise, isFalse);
      expect(expired.normalisationAnchorIsStale, isFalse);
      expect(expired.normalisationOrigin, isNull);
      expect(expired.normalisationScale, isNull);
      expect(expired.hands[1].pointAt(0)!.normalisedCoordinates, isNull);
      expect(
        expired.trackingIssues,
        isNot(contains(TrackingIssue.staleNormalisationAnchor)),
      );
    });

    test('face is unsmoothed while the hand uses the configured filter', () {
      const cutoff = 0.1;
      final service = LandmarkNormalisationService(
        config: const TrackingStateNormalisationConfig(
          smoothingCutoffHz: cutoff,
          normalisationAnchorTimeConstant: Duration.zero,
        ),
      );
      service.process(
        _trackingOutput(LandmarkFrameFixtures.fullyTrackedFrame()),
      );
      final raw = LandmarkFrameFixtures.mediaPipeFrame(
        frameIndex: 101,
        timestamp: LandmarkFrameFixtures.atFrame(1),
        face: LandmarkFrameFixtures.realisticFace(
          imageOverrides: const <int, LandmarkCoordinates>{
            13: LandmarkCoordinates(x: 0.54, y: 0.225, z: -0.165),
          },
        ),
        hands: <HandLandmarkGroup>[
          LandmarkFrameFixtures.realisticHand(rawHandedness: Handedness.left),
          LandmarkFrameFixtures.realisticHand(
            rawHandedness: Handedness.right,
            wristX: 0.74,
          ),
        ],
      );

      final output = service.process(_trackingOutput(raw));

      _expectCoordinates(
        output.face.pointAt(13)!.normalisedCoordinates,
        x: 0.2,
        y: -0.625,
      );
      _expectCoordinates(
        output.hands[1].pointAt(0)!.normalisedCoordinates,
        x: 1.00410281991678,
        y: 1.15,
        tolerance: 1e-9,
      );
    });
  });

  group('LandmarkNormalisationService - hand world coordinates', () {
    test('palm canonicalisation is rotation invariant with exact axes', () {
      final original = LandmarkNormalisationService().process(
        _trackingOutput(
          _worldHandFrame(const <int, LandmarkCoordinates>{
            0: LandmarkCoordinates(x: 0, y: 0, z: 0),
            5: LandmarkCoordinates(x: 1, y: 1, z: 0),
            8: LandmarkCoordinates(x: 1, y: 2, z: 0),
            17: LandmarkCoordinates(x: -1, y: 1, z: 0),
          }),
        ),
      );
      final rotated = LandmarkNormalisationService().process(
        _trackingOutput(
          _worldHandFrame(const <int, LandmarkCoordinates>{
            0: LandmarkCoordinates(x: 0, y: 0, z: 0),
            5: LandmarkCoordinates(x: -1, y: 1, z: 0),
            8: LandmarkCoordinates(x: -2, y: 1, z: 0),
            17: LandmarkCoordinates(x: -1, y: -1, z: 0),
          }),
        ),
      );

      for (final index in <int>[0, 5, 8, 17]) {
        _expectSameCoordinates(
          rotated.hands.single.pointAt(index)!.canonicalWorldCoordinates,
          original.hands.single.pointAt(index)!.canonicalWorldCoordinates,
        );
      }
      _expectCoordinates(
        original.hands.single.pointAt(0)!.canonicalWorldCoordinates,
        x: 0,
        y: 0,
        z: 0,
      );
      _expectCoordinates(
        original.hands.single.pointAt(5)!.canonicalWorldCoordinates,
        x: 1,
        y: 1,
        z: 0,
      );
      _expectCoordinates(
        original.hands.single.pointAt(8)!.canonicalWorldCoordinates,
        x: 1,
        y: 2,
        z: 0,
      );
      _expectCoordinates(
        original.hands.single.pointAt(17)!.canonicalWorldCoordinates,
        x: -1,
        y: 1,
        z: 0,
      );
    });
  });
}

LandmarkFrame _trackingOutput(
  LandmarkFrame raw, {
  TrackingStatus status = TrackingStatus.tracked,
  double quality = 0.97,
  List<TrackingIssue> issues = const <TrackingIssue>[],
  bool canNormalise = true,
}) => LandmarkFrameFixtures.asTrackingOutput(
  raw,
  status: status,
  quality: quality,
  issues: issues,
  canNormalise: canNormalise,
);

LandmarkFrame _rightWristFrame(
  double wristX,
  int frameOffset, {
  DateTime? timestamp,
}) => LandmarkFrameFixtures.mediaPipeFrame(
  frameIndex: 100 + frameOffset,
  timestamp: timestamp ?? LandmarkFrameFixtures.atFrame(frameOffset),
  hands: <HandLandmarkGroup>[
    LandmarkFrameFixtures.realisticHand(rawHandedness: Handedness.left),
    LandmarkFrameFixtures.realisticHand(
      rawHandedness: Handedness.right,
      wristX: wristX,
    ),
  ],
);

LandmarkFrame _worldHandFrame(Map<int, LandmarkCoordinates> worldOverrides) =>
    LandmarkFrameFixtures.mediaPipeFrame(
      hands: <HandLandmarkGroup>[
        LandmarkFrameFixtures.realisticHand(
          rawHandedness: Handedness.right,
          worldOverrides: worldOverrides,
        ),
      ],
    );

LandmarkFrame _transformImageFrame(
  LandmarkFrame source, {
  required double factor,
  required LandmarkCoordinates fromOrigin,
  required LandmarkCoordinates toOrigin,
}) => LandmarkFrameFixtures.cloneFrame(
  source,
  pose: _transformGroup(
    source.pose,
    factor: factor,
    fromOrigin: fromOrigin,
    toOrigin: toOrigin,
  ),
  face: _transformGroup(
    source.face,
    factor: factor,
    fromOrigin: fromOrigin,
    toOrigin: toOrigin,
  ),
  hands: source.hands
      .map(
        (hand) => hand.copyWith(
          landmarks: hand.landmarks
              .map(
                (point) => _transformPoint(
                  point,
                  factor: factor,
                  fromOrigin: fromOrigin,
                  toOrigin: toOrigin,
                ),
              )
              .toList(growable: false),
        ),
      )
      .toList(growable: false),
);

LandmarkGroup _transformGroup(
  LandmarkGroup group, {
  required double factor,
  required LandmarkCoordinates fromOrigin,
  required LandmarkCoordinates toOrigin,
}) => LandmarkGroup(
  isPresent: group.isPresent,
  landmarks: group.landmarks
      .map(
        (point) => _transformPoint(
          point,
          factor: factor,
          fromOrigin: fromOrigin,
          toOrigin: toOrigin,
        ),
      )
      .toList(growable: false),
);

LandmarkPoint? _transformPoint(
  LandmarkPoint? point, {
  required double factor,
  required LandmarkCoordinates fromOrigin,
  required LandmarkCoordinates toOrigin,
}) {
  if (point == null) return null;
  final image = point.imageCoordinates;
  return LandmarkPoint(
    index: point.index,
    confidence: point.confidence,
    imageCoordinates: image == null
        ? null
        : LandmarkCoordinates(
            x: toOrigin.x + (image.x - fromOrigin.x) * factor,
            y: toOrigin.y + (image.y - fromOrigin.y) * factor,
            z: image.z,
          ),
    worldCoordinates: point.worldCoordinates,
    source: point.source,
  );
}

Iterable<LandmarkPoint> _allPoints(LandmarkFrame frame) sync* {
  yield* frame.pose.landmarks.whereType<LandmarkPoint>();
  yield* frame.face.landmarks.whereType<LandmarkPoint>();
  for (final hand in frame.hands) {
    yield* hand.landmarks.whereType<LandmarkPoint>();
  }
}

void _expectNoBodyDerived(LandmarkFrame frame) {
  for (final point in _allPoints(frame)) {
    expect(point.normalisedCoordinates, isNull, reason: 'point ${point.index}');
    expect(point.velocity, isNull, reason: 'point ${point.index}');
    expect(point.acceleration, isNull, reason: 'point ${point.index}');
  }
}

void _expectAllDerivedCoordinatesFinite(LandmarkFrame frame) {
  for (final point in _allPoints(frame)) {
    final position = point.normalisedCoordinates;
    if (position != null) expect(position.isFinite, isTrue);
    final velocity = point.velocity;
    if (velocity != null) expect(velocity.isFinite, isTrue);
    final acceleration = point.acceleration;
    if (acceleration != null) expect(acceleration.isFinite, isTrue);
  }
}

void _expectSameCoordinates(
  LandmarkCoordinates? actual,
  LandmarkCoordinates? expected, {
  double tolerance = 1e-9,
}) {
  expect(expected, isNotNull);
  _expectCoordinates(
    actual,
    x: expected!.x,
    y: expected.y,
    z: expected.z,
    tolerance: tolerance,
  );
}

void _expectCoordinates(
  LandmarkCoordinates? actual, {
  required double x,
  required double y,
  double? z,
  double tolerance = 1e-9,
}) {
  expect(actual, isNotNull);
  expect(actual!.x, closeTo(x, tolerance));
  expect(actual.y, closeTo(y, tolerance));
  if (z == null) {
    expect(actual.z, isNull);
  } else {
    expect(actual.z, closeTo(z, tolerance));
  }
}
