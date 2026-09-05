import 'package:apptesting/models/landmark_frame.dart';

/// Deterministic inputs at the Harold/MediaPipe -> tracking-state boundary.
///
/// The shapes mirror MediaPipe Tasks output: 33 pose slots, 21 slots per
/// detected hand, and a 468-slot face group. The application retains only a
/// documented brow/mouth subset of the face, so unselected face slots are
/// deliberately null rather than filled with made-up coordinates.
abstract final class LandmarkFrameFixtures {
  static final DateTime epoch = DateTime.utc(2026, 9, 6, 12);
  static const Duration frameInterval = Duration(microseconds: 33333);
  static const String defaultSubjectId = 'subject-harold-001';

  /// INPUT: complete pose/face groups and two 21-point hands at high
  /// confidence. Raw handedness is left/right at 0.95; lifetime fields are at
  /// their pre-tracking defaults (unknown, 0.5, zero observations).
  /// TRACKING: tracked, quality 0.97, no issues, canNormalise=true.
  /// NORMALISATION: origin=(0.5, 0.35), scale=0.2; shoulders map to +/-0.5,
  /// wrists to (-1, 1.15) and (1, 1.15); first-frame velocity/acceleration null.
  static LandmarkFrame fullyTrackedFrame({
    int frameIndex = 100,
    DateTime? timestamp,
    String? subjectId = defaultSubjectId,
  }) => mediaPipeFrame(
    frameIndex: frameIndex,
    timestamp: timestamp,
    subjectId: subjectId,
  );

  /// INPUT: MediaPipe reports every group absent and supplies no coordinates.
  /// TRACKING: absent, quality 0, issues noLandmarks/noHands/missingShoulders.
  /// NORMALISATION (fresh service): canNormalise=false, no anchor and no
  /// coordinates. Nothing can be fabricated.
  static LandmarkFrame noSubjectFrame({
    int frameIndex = 101,
    DateTime? timestamp,
    String? subjectId = defaultSubjectId,
  }) => mediaPipeFrame(
    frameIndex: frameIndex,
    timestamp: timestamp ?? atFrame(1),
    subjectId: subjectId,
    pose: const LandmarkGroup.absent(),
    face: const LandmarkGroup.absent(),
    hands: const <HandLandmarkGroup>[],
  );

  /// INPUT: pose slot 12 (right shoulder) is null; all other observations are
  /// high confidence.
  /// TRACKING: degraded, quality 0.90875, issue missingShoulders,
  /// canNormalise=false.
  /// NORMALISATION (fresh service): every normalised coordinate is null.
  static LandmarkFrame oneShoulderMissingFrame({
    int frameIndex = 100,
    DateTime? timestamp,
  }) => mediaPipeFrame(
    frameIndex: frameIndex,
    timestamp: timestamp,
    pose: realisticPose(missingIndices: const <int>{12}),
  );

  /// INPUT: usable shoulders are only 0.000099 image units apart, just below
  /// the implementation-defined 0.0001 minimum.
  /// TRACKING: degraded despite quality 0.97; issue missingShoulders and
  /// canNormalise=false.
  /// NORMALISATION: no anchor and no derived coordinates, avoiding division by
  /// an unstable scale.
  static LandmarkFrame tinyShoulderScaleFrame({
    int frameIndex = 100,
    DateTime? timestamp,
  }) => mediaPipeFrame(
    frameIndex: frameIndex,
    timestamp: timestamp,
    pose: realisticPose(
      imageOverrides: const <int, LandmarkCoordinates>{
        11: LandmarkCoordinates(x: 0.5, y: 0.35, z: -0.05),
        12: LandmarkCoordinates(x: 0.500099, y: 0.35, z: -0.05),
      },
    ),
  );

  /// INPUT: shoulder width is exactly the accepted minimum, 0.0001.
  /// TRACKING: tracked, quality 0.97, canNormalise=true.
  /// NORMALISATION: finite origin=(0.00005, 0.35), scale=0.0001 and shoulder
  /// x values -0.5/+0.5. There is no configured maximum normalisation scale.
  static LandmarkFrame minimumShoulderScaleFrame({
    int frameIndex = 100,
    DateTime? timestamp,
  }) => mediaPipeFrame(
    frameIndex: frameIndex,
    timestamp: timestamp,
    pose: realisticPose(
      imageOverrides: const <int, LandmarkCoordinates>{
        11: LandmarkCoordinates(x: 0, y: 0.35, z: -0.05),
        12: LandmarkCoordinates(x: 0.0001, y: 0.35, z: -0.05),
      },
    ),
  );

  /// INPUT: shoulders span almost the full image width (0.01 to 0.99).
  /// TRACKING: tracked, quality 0.97, no issues.
  /// NORMALISATION: origin=(0.5, 0.35), scale=0.98; hand wrists map to
  /// approximately (-0.2040816, 0.2346939) and (0.2040816, 0.2346939).
  static LandmarkFrame largeShoulderScaleFrame({
    int frameIndex = 100,
    DateTime? timestamp,
  }) => mediaPipeFrame(
    frameIndex: frameIndex,
    timestamp: timestamp,
    pose: realisticPose(
      imageOverrides: const <int, LandmarkCoordinates>{
        11: LandmarkCoordinates(x: 0.01, y: 0.35, z: -0.05),
        12: LandmarkCoordinates(x: 0.99, y: 0.35, z: -0.05),
      },
    ),
  );

  /// INPUT: face is confidently observed, but every pose and hand point has
  /// confidence 0.1 (below 0.5).
  /// TRACKING: degraded, quality 0, issues noHands/missingShoulders/
  /// lowConfidence. The confident face prevents an absent state.
  /// NORMALISATION: no anchor; all pose/hand derived coordinates stay null.
  static LandmarkFrame lowConfidenceFrame({
    int frameIndex = 100,
    DateTime? timestamp,
  }) => mediaPipeFrame(
    frameIndex: frameIndex,
    timestamp: timestamp,
    pose: realisticPose(confidence: 0.1),
    hands: <HandLandmarkGroup>[
      realisticHand(rawHandedness: Handedness.left, confidence: 0.1),
      realisticHand(rawHandedness: Handedness.right, confidence: 0.1),
    ],
  );

  /// INPUT: only shoulders are usable in pose (2 * 0.98 / 8), while hand
  /// indices 0..10 are 0.96 and 11..20 are 0.01.
  /// TRACKING: poseQuality=0.245, handQuality=0.502857142857,
  /// totalQuality=0.373928571429, degraded with lowConfidence.
  /// NORMALISATION: shoulders and hand 0..10 are normalised; all low-confidence
  /// points retain raw coordinates but have null normalised/velocity values.
  static LandmarkFrame mixedConfidenceFrame({
    int frameIndex = 100,
    DateTime? timestamp,
  }) {
    final poseConfidence = <int, double>{
      for (var index = 0; index < 33; index += 1) index: 0.01,
      11: 0.98,
      12: 0.98,
    };
    final handConfidence = <int, double>{
      for (var index = 0; index < 21; index += 1)
        index: index <= 10 ? 0.96 : 0.01,
    };
    return mediaPipeFrame(
      frameIndex: frameIndex,
      timestamp: timestamp,
      pose: realisticPose(confidenceOverrides: poseConfidence),
      hands: <HandLandmarkGroup>[
        realisticHand(
          rawHandedness: Handedness.right,
          confidenceOverrides: handConfidence,
        ),
      ],
    );
  }

  /// INPUT: high-confidence pose/face groups and MediaPipe's normal empty hand
  /// result list.
  /// TRACKING: degraded, quality 0.49, issue noHands, canNormalise=true.
  /// NORMALISATION: pose/face values are normalised; no hand is invented.
  static LandmarkFrame missingHandsFrame({
    int frameIndex = 100,
    DateTime? timestamp,
  }) => mediaPipeFrame(
    frameIndex: frameIndex,
    timestamp: timestamp,
    hands: const <HandLandmarkGroup>[],
  );

  /// INPUT: pose group absent while both complete hands and curated face are
  /// present.
  /// TRACKING: degraded, quality 0.48, issue missingShoulders,
  /// canNormalise=false.
  /// NORMALISATION (fresh service): hand coordinates remain unnormalised.
  static LandmarkFrame missingPoseFrame({
    int frameIndex = 100,
    DateTime? timestamp,
  }) => mediaPipeFrame(
    frameIndex: frameIndex,
    timestamp: timestamp,
    pose: const LandmarkGroup.absent(),
  );

  /// INPUT: one 30 FPS frame after [fullyTrackedFrame], the right wrist jumps
  /// from x=0.70 to x=0.05 while all confidence values remain high.
  /// TRACKING: implementation-defined tracked/0.97 and the same label-matched
  /// track ID; no teleport issue exists in the contract.
  /// NORMALISATION: raw candidate changes from x=1 to x=-2.25. With default
  /// 6 Hz smoothing at 33,333 us it becomes about -0.8097958 and velocity
  /// about -54.294418 body units/s; acceleration is null on this second frame.
  static LandmarkFrame discontinuityFrame({
    int frameIndex = 101,
    DateTime? timestamp,
  }) => mediaPipeFrame(
    frameIndex: frameIndex,
    timestamp: timestamp ?? atFrame(1),
    hands: <HandLandmarkGroup>[
      realisticHand(rawHandedness: Handedness.left),
      realisticHand(
        rawHandedness: Handedness.right,
        imageOverrides: const <int, LandmarkCoordinates>{
          0: LandmarkCoordinates(x: 0.05, y: 0.58, z: -0.01),
        },
      ),
    ],
  );

  /// INPUT: complete frame after several [noSubjectFrame] inputs, within the
  /// 15-frame hand-track expiry.
  /// TRACKING: immediately tracked/0.97 and prior IDs recover; there is no
  /// status hysteresis in this service (subject hysteresis is upstream).
  /// NORMALISATION: exact base coordinates return; per-point derivatives are
  /// null because missing frames clear point history.
  static LandmarkFrame recoveryFrame({
    int frameIndex = 104,
    DateTime? timestamp,
  }) => fullyTrackedFrame(
    frameIndex: frameIndex,
    timestamp: timestamp ?? atFrame(4),
  );

  /// INPUT: every retained point has exactly [confidence].
  /// TRACKING: at 0.5 the result is tracked with quality 0.5 (inclusive); just
  /// above is tracked at that quality; just below is absent/quality 0 with
  /// noLandmarks/noHands/missingShoulders/lowConfidence.
  /// NORMALISATION: exactly 0.5 is accepted; below 0.5 derives no coordinates.
  static LandmarkFrame confidenceBoundaryFrame(
    double confidence, {
    int frameIndex = 100,
    DateTime? timestamp,
  }) => mediaPipeFrame(
    frameIndex: frameIndex,
    timestamp: timestamp,
    pose: realisticPose(confidence: confidence),
    face: realisticFace(confidence: confidence),
    hands: <HandLandmarkGroup>[
      realisticHand(rawHandedness: Handedness.left, confidence: confidence),
      realisticHand(rawHandedness: Handedness.right, confidence: confidence),
    ],
  );

  /// INPUT: spatially changed complete frame with the same timestamp as the
  /// previous base frame (delta=0).
  /// TRACKING: temporal state resets safely; tracked/0.97 and handedness count
  /// restarts at one.
  /// NORMALISATION: position is valid but velocity/acceleration are null; no
  /// NaN or infinity is derived.
  static LandmarkFrame invalidTimestampFrame({
    int frameIndex = 101,
    DateTime? timestamp,
  }) => mediaPipeFrame(
    frameIndex: frameIndex,
    timestamp: timestamp ?? epoch,
    hands: <HandLandmarkGroup>[
      realisticHand(rawHandedness: Handedness.left),
      realisticHand(rawHandedness: Handedness.right, wristX: 0.72),
    ],
  );

  /// INPUT: otherwise complete frame with right index-tip slot 8 explicitly
  /// null after it was previously valid.
  /// TRACKING: tracked, quality 0.958571428571, no low-confidence issue (null
  /// is absence, not a low score).
  /// NORMALISATION: slot 8 remains null and its history is discarded.
  static LandmarkFrame missingLandmarkFrame({
    int frameIndex = 101,
    DateTime? timestamp,
  }) => mediaPipeFrame(
    frameIndex: frameIndex,
    timestamp: timestamp ?? atFrame(1),
    hands: <HandLandmarkGroup>[
      realisticHand(rawHandedness: Handedness.left),
      realisticHand(
        rawHandedness: Handedness.right,
        missingIndices: const <int>{8},
      ),
    ],
  );

  /// INPUT: the missing right index tip returns one frame later.
  /// TRACKING: tracked/0.97 and the hand track remains stable.
  /// NORMALISATION: slot 8 is normalised again, but velocity and acceleration
  /// are null because its prior history was explicitly removed.
  static LandmarkFrame reappearingLandmarkFrame({
    int frameIndex = 102,
    DateTime? timestamp,
  }) => fullyTrackedFrame(
    frameIndex: frameIndex,
    timestamp: timestamp ?? atFrame(2),
  );

  /// INPUT: shoulder coordinates lie exactly on x=0 and x=1, and right-hand
  /// points 0 and 8 use the opposite image corners (0,0) and (1,1).
  /// TRACKING: tracked/0.97; finite boundary coordinates are accepted.
  /// NORMALISATION: origin=(0.5,0.5), scale=1; points map to (-0.5,-0.5)
  /// and (0.5,0.5), all finite.
  static LandmarkFrame coordinateExtremesFrame({
    int frameIndex = 100,
    DateTime? timestamp,
  }) => mediaPipeFrame(
    frameIndex: frameIndex,
    timestamp: timestamp,
    pose: realisticPose(
      imageOverrides: const <int, LandmarkCoordinates>{
        11: LandmarkCoordinates(x: 0, y: 0.5, z: -0.05),
        12: LandmarkCoordinates(x: 1, y: 0.5, z: -0.05),
      },
    ),
    hands: <HandLandmarkGroup>[
      realisticHand(
        rawHandedness: Handedness.right,
        imageOverrides: const <int, LandmarkCoordinates>{
          0: LandmarkCoordinates(x: 0, y: 0, z: -0.01),
          8: LandmarkCoordinates(x: 1, y: 1, z: -0.02),
        },
      ),
    ],
  );

  /// INPUT: a complete right hand has raw handedness score 0.599999, just
  /// below the 0.6 lifetime decision threshold.
  /// TRACKING: tracked/0.97, stable handedness unknown, running average
  /// 0.599999, observation count 1, issue handednessUncertain.
  /// NORMALISATION: coordinates are still valid; handedness uncertainty is
  /// metadata and does not fabricate or remove points.
  static LandmarkFrame ambiguousHandednessFrame({
    int frameIndex = 100,
    DateTime? timestamp,
    double handednessScore = 0.599999,
  }) => mediaPipeFrame(
    frameIndex: frameIndex,
    timestamp: timestamp,
    hands: <HandLandmarkGroup>[
      realisticHand(
        rawHandedness: Handedness.right,
        handednessScore: handednessScore,
      ),
    ],
  );

  /// INPUT: two complete hands are both labelled right at score 0.95.
  /// TRACKING: both are retained, tracked/0.97, and both are marked uncertain;
  /// issue handednessUncertain. Neither hand is dropped.
  /// NORMALISATION: all 42 hand slots remain present and normalisable.
  static LandmarkFrame duplicateHandednessFrame({
    int frameIndex = 100,
    DateTime? timestamp,
  }) => mediaPipeFrame(
    frameIndex: frameIndex,
    timestamp: timestamp,
    hands: <HandLandmarkGroup>[
      realisticHand(rawHandedness: Handedness.right, wristX: 0.30),
      realisticHand(rawHandedness: Handedness.right),
    ],
  );

  /// INPUT: present flags accompany mostly missing data, one non-finite and
  /// confidence-0.01 shoulder, and an unknown confidence-0.01 hand.
  /// TRACKING: absent/quality 0 with noLandmarks, noHands, missingShoulders,
  /// lowConfidence and handednessUncertain.
  /// NORMALISATION: no anchor and every derived field null; input nulls and
  /// measured raw values remain representable without a crash.
  static LandmarkFrame completelyUnusableFrame({
    int frameIndex = 100,
    DateTime? timestamp,
  }) => mediaPipeFrame(
    frameIndex: frameIndex,
    timestamp: timestamp,
    pose: realisticPose(
      confidence: 0.01,
      missingIndices: const <int>{11},
      imageOverrides: const <int, LandmarkCoordinates>{
        12: LandmarkCoordinates(x: double.nan, y: 0.35, z: -0.05),
      },
    ),
    face: const LandmarkGroup.absent(),
    hands: <HandLandmarkGroup>[
      realisticHand(
        rawHandedness: Handedness.unknown,
        handednessScore: 0.5,
        confidence: 0.01,
        missingIndices: const <int>{
          1,
          2,
          3,
          4,
          5,
          6,
          7,
          8,
          9,
          10,
          11,
          12,
          13,
          14,
          15,
          16,
          17,
          18,
          19,
          20,
        },
        imageOverrides: const <int, LandmarkCoordinates>{
          0: LandmarkCoordinates(x: double.nan, y: 0.58, z: -0.01),
        },
      ),
    ],
  );

  /// INPUT: presence flags are false even though stale coordinate arrays are
  /// attached.
  /// TRACKING: flags are authoritative, so absent/quality 0 and no track IDs.
  /// NORMALISATION: stale raw values survive for diagnosis but receive no
  /// normalised coordinates.
  static LandmarkFrame absentGroupsWithStaleCoordinatesFrame({
    int frameIndex = 100,
    DateTime? timestamp,
  }) => mediaPipeFrame(
    frameIndex: frameIndex,
    timestamp: timestamp,
    pose: realisticPose(isPresent: false),
    face: realisticFace(isPresent: false),
    hands: <HandLandmarkGroup>[
      realisticHand(rawHandedness: Handedness.left, isPresent: false),
    ],
  );

  /// General raw-boundary builder. Defaults form [fullyTrackedFrame].
  static LandmarkFrame mediaPipeFrame({
    int frameIndex = 100,
    DateTime? timestamp,
    String? subjectId = defaultSubjectId,
    LandmarkGroup? pose,
    LandmarkGroup? face,
    List<HandLandmarkGroup>? hands,
  }) => LandmarkFrame(
    timestamp: timestamp ?? epoch,
    frameIndex: frameIndex,
    subjectId: subjectId,
    pose: pose ?? realisticPose(),
    face: face ?? realisticFace(),
    hands:
        hands ??
        <HandLandmarkGroup>[
          realisticHand(rawHandedness: Handedness.left),
          realisticHand(rawHandedness: Handedness.right),
        ],
  );

  /// Builds all 33 MediaPipe Pose Landmarker slots using a plausible standing
  /// upper-body observation. Null overrides model detector absence explicitly.
  static LandmarkGroup realisticPose({
    bool isPresent = true,
    double confidence = 0.98,
    Set<int> missingIndices = const <int>{},
    Map<int, LandmarkCoordinates> imageOverrides =
        const <int, LandmarkCoordinates>{},
    Map<int, double> confidenceOverrides = const <int, double>{},
  }) => LandmarkGroup(
    isPresent: isPresent,
    landmarks: List<LandmarkPoint?>.generate(33, (index) {
      if (missingIndices.contains(index)) return null;
      return mediaPipePoint(
        index,
        imageOverrides[index] ?? _poseImageCoordinates[index]!,
        confidence: confidenceOverrides[index] ?? confidence,
      );
    }, growable: false),
  );

  /// Builds a complete 21-slot MediaPipe hand with image and per-hand world
  /// coordinates. Stable handedness fields default to their raw-boundary
  /// values and are intentionally not precomputed here.
  static HandLandmarkGroup realisticHand({
    required Handedness rawHandedness,
    bool isPresent = true,
    double handednessScore = 0.95,
    double confidence = 0.96,
    double? wristX,
    double wristY = 0.58,
    String? trackId,
    Handedness handedness = Handedness.unknown,
    double handednessRunningAverage = 0.5,
    int handednessObservationCount = 0,
    bool handednessUncertain = false,
    Set<int> missingIndices = const <int>{},
    Map<int, LandmarkCoordinates> imageOverrides =
        const <int, LandmarkCoordinates>{},
    Map<int, LandmarkCoordinates> worldOverrides =
        const <int, LandmarkCoordinates>{},
    Map<int, double> confidenceOverrides = const <int, double>{},
  }) {
    final isLeft = rawHandedness == Handedness.left;
    final templateWristX = isLeft ? 0.30 : 0.70;
    final targetWristX = wristX ?? templateWristX;
    final points = List<LandmarkPoint?>.generate(21, (index) {
      if (missingIndices.contains(index)) return null;
      final template = _leftHandImageCoordinates[index]!;
      final templateX = isLeft ? template.x : 1 - template.x;
      final image =
          imageOverrides[index] ??
          LandmarkCoordinates(
            x: targetWristX + templateX - templateWristX,
            y: wristY + template.y - 0.58,
            z: template.z,
          );
      final templateWorld = _rightHandWorldCoordinates[index]!;
      final world =
          worldOverrides[index] ??
          LandmarkCoordinates(
            x: isLeft ? -templateWorld.x : templateWorld.x,
            y: templateWorld.y,
            z: templateWorld.z,
          );
      return mediaPipePoint(
        index,
        image,
        confidence: confidenceOverrides[index] ?? confidence,
        worldCoordinates: world,
      );
    }, growable: false);
    return HandLandmarkGroup(
      isPresent: isPresent,
      landmarks: points,
      trackId: trackId,
      rawHandedness: rawHandedness,
      handedness: handedness,
      handednessScore: handednessScore,
      handednessRunningAverage: handednessRunningAverage,
      handednessObservationCount: handednessObservationCount,
      handednessUncertain: handednessUncertain,
    );
  }

  /// A 468-slot group preserving original Face Mesh indices. Only the agreed
  /// brow/mouth-style subset is retained; other slots are explicit nulls.
  static LandmarkGroup realisticFace({
    bool isPresent = true,
    double confidence = 0.94,
    Set<int> missingIndices = const <int>{},
    Map<int, LandmarkCoordinates> imageOverrides =
        const <int, LandmarkCoordinates>{},
    Map<int, double> confidenceOverrides = const <int, double>{},
  }) {
    final points = List<LandmarkPoint?>.filled(468, null);
    for (final entry in _curatedFaceImageCoordinates.entries) {
      if (missingIndices.contains(entry.key)) continue;
      points[entry.key] = mediaPipePoint(
        entry.key,
        imageOverrides[entry.key] ?? entry.value,
        confidence: confidenceOverrides[entry.key] ?? confidence,
      );
    }
    return LandmarkGroup(isPresent: isPresent, landmarks: points);
  }

  static LandmarkPoint mediaPipePoint(
    int index,
    LandmarkCoordinates imageCoordinates, {
    double confidence = 0.98,
    LandmarkCoordinates? worldCoordinates,
  }) => LandmarkPoint(
    index: index,
    confidence: confidence,
    imageCoordinates: imageCoordinates,
    worldCoordinates: worldCoordinates,
  );

  /// Produces a deterministic test-only tracking-state handoff without
  /// invoking tracking. This lets normalisation failures be attributed only
  /// to [LandmarkNormalisationService].
  ///
  /// Present hands receive stable IDs, settled labels, lifetime averages and
  /// one observation. Callers provide edge-case status/quality metadata when
  /// it differs from the complete-frame defaults.
  static LandmarkFrame asTrackingOutput(
    LandmarkFrame raw, {
    TrackingStatus status = TrackingStatus.tracked,
    double quality = 0.97,
    List<TrackingIssue> issues = const <TrackingIssue>[],
    bool canNormalise = true,
  }) {
    final initiallyLabelledHands = raw.hands
        .asMap()
        .entries
        .map((entry) {
          final hand = entry.value;
          if (!hand.isPresent) return hand;
          final observed = hand.rawHandedness != Handedness.unknown
              ? hand.rawHandedness
              : hand.handedness;
          final rightProbability = switch (observed) {
            Handedness.right => hand.handednessScore,
            Handedness.left => 1 - hand.handednessScore,
            Handedness.unknown => 0.5,
          };
          final settled = rightProbability >= 0.6
              ? Handedness.right
              : rightProbability <= 0.4
              ? Handedness.left
              : Handedness.unknown;
          return hand.copyWith(
            trackId: hand.trackId ?? 'fixture-hand-${entry.key + 1}',
            handedness: settled,
            handednessRunningAverage: rightProbability,
            handednessObservationCount: observed == Handedness.unknown ? 0 : 1,
            handednessUncertain:
                hand.handednessUncertain || settled == Handedness.unknown,
          );
        })
        .toList(growable: false);
    final rawCounts = <Handedness, int>{};
    final settledCounts = <Handedness, int>{};
    for (final hand in initiallyLabelledHands.where(
      (candidate) => candidate.isPresent,
    )) {
      rawCounts[hand.rawHandedness] = (rawCounts[hand.rawHandedness] ?? 0) + 1;
      settledCounts[hand.handedness] =
          (settledCounts[hand.handedness] ?? 0) + 1;
    }
    final labelledHands = initiallyLabelledHands
        .map(
          (hand) => !hand.isPresent
              ? hand
              : hand.copyWith(
                  handednessUncertain:
                      hand.handednessUncertain ||
                      (hand.rawHandedness != Handedness.unknown &&
                          (rawCounts[hand.rawHandedness] ?? 0) > 1) ||
                      (hand.handedness != Handedness.unknown &&
                          (settledCounts[hand.handedness] ?? 0) > 1),
                ),
        )
        .toList(growable: false);
    return raw.copyWith(
      hands: labelledHands,
      trackingStatus: status,
      trackingQuality: quality,
      trackingIssues: issues,
      canNormalise: canNormalise,
    );
  }

  /// Rebuilds an immutable frame while allowing timestamp/frame/group changes.
  static LandmarkFrame cloneFrame(
    LandmarkFrame source, {
    int? frameIndex,
    DateTime? timestamp,
    String? subjectId,
    LandmarkGroup? pose,
    LandmarkGroup? face,
    List<HandLandmarkGroup>? hands,
    TrackingStatus? trackingStatus,
    double? trackingQuality,
    List<TrackingIssue>? trackingIssues,
    bool? canNormalise,
  }) => LandmarkFrame(
    timestamp: timestamp ?? source.timestamp,
    frameIndex: frameIndex ?? source.frameIndex,
    subjectId: subjectId ?? source.subjectId,
    pose: pose ?? source.pose,
    face: face ?? source.face,
    hands: hands ?? source.hands,
    coordinateSpace: source.coordinateSpace,
    trackingStatus: trackingStatus ?? source.trackingStatus,
    trackingQuality: trackingQuality ?? source.trackingQuality,
    trackingIssues: trackingIssues ?? source.trackingIssues,
    canNormalise: canNormalise ?? source.canNormalise,
    normalisationOrigin: source.normalisationOrigin,
    normalisationScale: source.normalisationScale,
    normalisationAnchorIsStale: source.normalisationAnchorIsStale,
    lightingScore: source.lightingScore,
    featureVector: source.featureVector,
  );

  static DateTime atFrame(int offset) =>
      epoch.add(Duration(microseconds: frameInterval.inMicroseconds * offset));

  static const Map<int, LandmarkCoordinates> _poseImageCoordinates =
      <int, LandmarkCoordinates>{
        0: LandmarkCoordinates(x: 0.50, y: 0.16, z: -0.15),
        1: LandmarkCoordinates(x: 0.485, y: 0.145, z: -0.15),
        2: LandmarkCoordinates(x: 0.475, y: 0.145, z: -0.15),
        3: LandmarkCoordinates(x: 0.465, y: 0.15, z: -0.14),
        4: LandmarkCoordinates(x: 0.515, y: 0.145, z: -0.15),
        5: LandmarkCoordinates(x: 0.525, y: 0.145, z: -0.15),
        6: LandmarkCoordinates(x: 0.535, y: 0.15, z: -0.14),
        7: LandmarkCoordinates(x: 0.44, y: 0.18, z: -0.10),
        8: LandmarkCoordinates(x: 0.56, y: 0.18, z: -0.10),
        9: LandmarkCoordinates(x: 0.48, y: 0.205, z: -0.13),
        10: LandmarkCoordinates(x: 0.52, y: 0.205, z: -0.13),
        11: LandmarkCoordinates(x: 0.40, y: 0.35, z: -0.05),
        12: LandmarkCoordinates(x: 0.60, y: 0.35, z: -0.05),
        13: LandmarkCoordinates(x: 0.32, y: 0.47, z: -0.04),
        14: LandmarkCoordinates(x: 0.68, y: 0.47, z: -0.04),
        15: LandmarkCoordinates(x: 0.30, y: 0.58, z: -0.03),
        16: LandmarkCoordinates(x: 0.70, y: 0.58, z: -0.03),
        17: LandmarkCoordinates(x: 0.285, y: 0.60, z: -0.04),
        18: LandmarkCoordinates(x: 0.715, y: 0.60, z: -0.04),
        19: LandmarkCoordinates(x: 0.29, y: 0.59, z: -0.05),
        20: LandmarkCoordinates(x: 0.71, y: 0.59, z: -0.05),
        21: LandmarkCoordinates(x: 0.305, y: 0.575, z: -0.03),
        22: LandmarkCoordinates(x: 0.695, y: 0.575, z: -0.03),
        23: LandmarkCoordinates(x: 0.44, y: 0.66, z: 0),
        24: LandmarkCoordinates(x: 0.56, y: 0.66, z: 0),
        25: LandmarkCoordinates(x: 0.44, y: 0.82, z: 0.03),
        26: LandmarkCoordinates(x: 0.56, y: 0.82, z: 0.03),
        27: LandmarkCoordinates(x: 0.44, y: 0.97, z: 0.05),
        28: LandmarkCoordinates(x: 0.56, y: 0.97, z: 0.05),
        29: LandmarkCoordinates(x: 0.43, y: 0.99, z: 0.02),
        30: LandmarkCoordinates(x: 0.57, y: 0.99, z: 0.02),
        31: LandmarkCoordinates(x: 0.45, y: 1.00, z: -0.04),
        32: LandmarkCoordinates(x: 0.55, y: 1.00, z: -0.04),
      };

  static const Map<int, LandmarkCoordinates> _leftHandImageCoordinates =
      <int, LandmarkCoordinates>{
        0: LandmarkCoordinates(x: 0.300, y: 0.580, z: -0.010),
        1: LandmarkCoordinates(x: 0.283, y: 0.555, z: -0.012),
        2: LandmarkCoordinates(x: 0.266, y: 0.535, z: -0.014),
        3: LandmarkCoordinates(x: 0.250, y: 0.515, z: -0.015),
        4: LandmarkCoordinates(x: 0.232, y: 0.500, z: -0.016),
        5: LandmarkCoordinates(x: 0.310, y: 0.520, z: -0.012),
        6: LandmarkCoordinates(x: 0.310, y: 0.475, z: -0.016),
        7: LandmarkCoordinates(x: 0.310, y: 0.435, z: -0.019),
        8: LandmarkCoordinates(x: 0.310, y: 0.395, z: -0.021),
        9: LandmarkCoordinates(x: 0.330, y: 0.515, z: -0.012),
        10: LandmarkCoordinates(x: 0.335, y: 0.465, z: -0.017),
        11: LandmarkCoordinates(x: 0.340, y: 0.420, z: -0.021),
        12: LandmarkCoordinates(x: 0.345, y: 0.380, z: -0.024),
        13: LandmarkCoordinates(x: 0.350, y: 0.520, z: -0.010),
        14: LandmarkCoordinates(x: 0.360, y: 0.480, z: -0.014),
        15: LandmarkCoordinates(x: 0.370, y: 0.445, z: -0.017),
        16: LandmarkCoordinates(x: 0.380, y: 0.415, z: -0.019),
        17: LandmarkCoordinates(x: 0.370, y: 0.535, z: -0.008),
        18: LandmarkCoordinates(x: 0.385, y: 0.505, z: -0.010),
        19: LandmarkCoordinates(x: 0.398, y: 0.480, z: -0.012),
        20: LandmarkCoordinates(x: 0.410, y: 0.460, z: -0.013),
      };

  /// Approximate Hand Landmarker world coordinates in metres, relative to the
  /// palm region. Mirroring is applied for the left-hand fixture.
  static const Map<int, LandmarkCoordinates> _rightHandWorldCoordinates =
      <int, LandmarkCoordinates>{
        0: LandmarkCoordinates(x: 0, y: 0, z: 0),
        1: LandmarkCoordinates(x: -0.018, y: -0.015, z: -0.004),
        2: LandmarkCoordinates(x: -0.034, y: -0.031, z: -0.006),
        3: LandmarkCoordinates(x: -0.049, y: -0.047, z: -0.006),
        4: LandmarkCoordinates(x: -0.064, y: -0.061, z: -0.005),
        5: LandmarkCoordinates(x: -0.030, y: -0.050, z: 0),
        6: LandmarkCoordinates(x: -0.033, y: -0.080, z: -0.002),
        7: LandmarkCoordinates(x: -0.035, y: -0.108, z: -0.003),
        8: LandmarkCoordinates(x: -0.036, y: -0.136, z: -0.004),
        9: LandmarkCoordinates(x: 0, y: -0.055, z: 0),
        10: LandmarkCoordinates(x: 0, y: -0.090, z: -0.002),
        11: LandmarkCoordinates(x: 0, y: -0.120, z: -0.003),
        12: LandmarkCoordinates(x: 0, y: -0.150, z: -0.004),
        13: LandmarkCoordinates(x: 0.025, y: -0.050, z: 0.001),
        14: LandmarkCoordinates(x: 0.029, y: -0.082, z: 0),
        15: LandmarkCoordinates(x: 0.032, y: -0.108, z: -0.001),
        16: LandmarkCoordinates(x: 0.034, y: -0.133, z: -0.002),
        17: LandmarkCoordinates(x: 0.045, y: -0.040, z: 0.002),
        18: LandmarkCoordinates(x: 0.052, y: -0.067, z: 0.001),
        19: LandmarkCoordinates(x: 0.057, y: -0.089, z: 0),
        20: LandmarkCoordinates(x: 0.061, y: -0.110, z: -0.001),
      };

  static const Map<int, LandmarkCoordinates> _curatedFaceImageCoordinates =
      <int, LandmarkCoordinates>{
        13: LandmarkCoordinates(x: 0.500, y: 0.225, z: -0.165),
        14: LandmarkCoordinates(x: 0.500, y: 0.238, z: -0.162),
        61: LandmarkCoordinates(x: 0.470, y: 0.231, z: -0.150),
        70: LandmarkCoordinates(x: 0.462, y: 0.184, z: -0.152),
        105: LandmarkCoordinates(x: 0.485, y: 0.180, z: -0.160),
        291: LandmarkCoordinates(x: 0.530, y: 0.231, z: -0.150),
        300: LandmarkCoordinates(x: 0.538, y: 0.184, z: -0.152),
        334: LandmarkCoordinates(x: 0.515, y: 0.180, z: -0.160),
      };
}
