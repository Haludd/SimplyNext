import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:apptesting/models/hand_tracking_models.dart';
import 'package:apptesting/models/face_tracking_models.dart';
import 'package:apptesting/models/tracking_models.dart';
import 'package:apptesting/services/api_client.dart';
import 'package:apptesting/services/hand_pose_normalizer.dart';

void main() {
  test('normalizes a detected hand into a skeleton frame', () {
    final hand = TrackedHand(
      handedness: Handedness.right,
      confidence: .92,
      landmarks: List<HandLandmark>.generate(
        21,
        (index) => HandLandmark(
          x: .4 + index * .005,
          y: .5 - index * .004,
          z: -.01 * index,
        ),
      ),
    );
    final frame = HandPoseNormalizer().normalize(
      HandTrackingFrame(
        timestamp: DateTime.utc(2026, 9, 5),
        processingConfidence: .95,
        leftShoulder: const HandLandmark(x: .35, y: .42, z: 0, visibility: .9),
        rightShoulder: const HandLandmark(x: .65, y: .42, z: 0, visibility: .9),
        hands: <TrackedHand>[hand],
      ),
    );

    expect(frame.hands, hasLength(1));
    expect(frame.hands.single.landmarks, hasLength(21));
    expect(frame.rightHandVisible, isTrue);
    expect(frame.shouldersVisible, isTrue);
    expect(frame.handMotion?.dominantHand, Handedness.right);
    expect(frame.handCoordinateAnalysis.single.jointCount, 21);
    expect(
      frame.handCoordinateAnalysis.single.coordinateSpace,
      'image_normalized_wrist_centered',
    );
    expect(frame.toJson()['hands'], hasLength(1));
    expect(frame.toJson()['hand_coordinate_analysis'], hasLength(1));
  });

  test('serializes a sign sequence for the analysis API', () {
    final frame = LandmarkFrame(
      timestamp: DateTime.utc(2026, 9, 5),
      hands: <TrackedHand>[],
    );
    final payload = SignSequencePayload(
      sessionId: 'session-test',
      sequenceId: 'sequence-test',
      language: 'ASL',
      startedAt: frame.timestamp,
      endedAt: frame.timestamp,
      frames: <LandmarkFrame>[frame],
      lexiconVersion: 'test-1',
    ).toJson();

    expect(payload['language'], 'ASL');
    expect(payload['frame_count'], 1);
    expect(payload['frames'], hasLength(1));
  });

  test(
    'posts 21-point coordinates and derived geometry to the backend',
    () async {
      final hand = TrackedHand(
        handedness: Handedness.right,
        confidence: .95,
        landmarks: List<HandLandmark>.generate(
          21,
          (index) => HandLandmark(
            x: .4 + index * .005,
            y: .5 - index * .004,
            z: -.01 * index,
          ),
        ),
      );
      final frame = HandPoseNormalizer().normalize(
        HandTrackingFrame(
          timestamp: DateTime.utc(2026, 9, 5),
          processingConfidence: .95,
          hands: <TrackedHand>[hand],
        ),
      );
      final client = MockClient((request) async {
        final body = jsonDecode(request.body) as Map<String, dynamic>;
        final frames = body['frames'] as List<dynamic>;
        final sentFrame = frames.single as Map<String, dynamic>;
        final sentHands = sentFrame['hands'] as List<dynamic>;
        final sentHand = sentHands.single as Map<String, dynamic>;
        final geometry = sentFrame['hand_coordinate_analysis'] as List<dynamic>;

        expect(request.method, 'POST');
        expect(request.url.path, '/v1/sign-sequences/analyze');
        expect(sentHand['landmarks'], hasLength(21));
        expect((geometry.single as Map<String, dynamic>)['joint_count'], 21);
        return http.Response(
          jsonEncode(<String, dynamic>{
            'status': 'confident',
            'gesture_label': 'water',
            'caption': 'water',
            'confidence': .9,
            'gloss_trace': <String>['WATER'],
          }),
          200,
        );
      });
      final api = SignSequenceApiClient(
        baseUri: Uri.parse('https://api.example.test'),
        client: client,
      );

      final result = await api.analyze(
        SignSequencePayload(
          sessionId: 'session-test',
          sequenceId: 'sequence-test',
          language: 'ASL',
          startedAt: frame.timestamp,
          endedAt: frame.timestamp,
          frames: <LandmarkFrame>[frame],
          lexiconVersion: 'test-1',
        ),
      );

      expect(result.gestureLabel, 'water');
      api.close();
    },
  );

  test('keeps facial expression features in the frame payload', () {
    const face = FaceExpressionFeatures(
      confidence: .9,
      label: 'smile',
      smile: .8,
      frown: .02,
      browRaise: .1,
      browFurrow: .01,
      eyeWide: .2,
      jawOpen: .05,
      mouthPucker: .03,
      landmarks: <FaceLandmark>[FaceLandmark(index: 1, x: .5, y: .3, z: -.02)],
      blendshapes: <String, double>{'mouthSmileLeft': .8},
    );
    final frame = HandPoseNormalizer().normalize(
      HandTrackingFrame(
        timestamp: DateTime.utc(2026, 9, 5),
        hands: const <TrackedHand>[],
        face: face,
      ),
    );

    expect(frame.faceExpression?.label, 'smile');
    expect(frame.toJson()['face_expression'], isNotNull);
    expect(
      (frame.toJson()['face_expression'] as Map<String, dynamic>)['landmarks'],
      hasLength(1),
    );
  });

  test('simulates backend analysis without making a network request', () async {
    final frame = LandmarkFrame(
      timestamp: DateTime.utc(2026, 9, 5),
      hands: <TrackedHand>[
        TrackedHand(
          handedness: Handedness.right,
          confidence: .9,
          landmarks: List<HandLandmark>.generate(
            21,
            (index) => HandLandmark(
              x: .4 + index * .005,
              y: .5 - index * .004,
              z: -.01 * index,
            ),
          ),
        ),
      ],
    );
    final result = await SimulatedSignSequenceApiClient().analyze(
      SignSequencePayload(
        sessionId: 'session-test',
        sequenceId: 'sequence-test',
        language: 'ASL',
        startedAt: frame.timestamp,
        endedAt: frame.timestamp,
        frames: <LandmarkFrame>[frame],
        lexiconVersion: 'test-1',
      ),
    );

    expect(result.status, 'simulated');
    expect(result.detail, contains('no network request sent'));
  });
}
