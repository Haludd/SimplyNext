/// The shared frontend boundary between landmark extraction, tracking state,
/// normalisation, and segmentation.
///
/// Missing landmarks are represented by null entries. A low-confidence
/// observation may retain its measured image coordinate, but its normalised
/// coordinate and temporal derivatives are null after confidence gating.
enum LandmarkCoordinateSpace { mediaPipeImage, bodyNormalised }

enum Handedness { left, right, unknown }

enum TrackingStatus { absent, degraded, tracked }

enum TrackingIssue {
  noLandmarks,
  noHands,
  missingShoulders,
  lowConfidence,
  staleNormalisationAnchor,
  handednessUncertain,
}

enum LandmarkSource { mediaPipe, poseWristSubstitution }

class LandmarkCoordinates {
  const LandmarkCoordinates({required this.x, required this.y, this.z});

  final double x;
  final double y;

  /// MediaPipe image z is relative ordering, not metric camera depth.
  final double? z;

  bool get isFinite => x.isFinite && y.isFinite && (z?.isFinite ?? true);

  Map<String, dynamic> toJson() => <String, dynamic>{
    'x': x,
    'y': y,
    if (z != null) 'z': z,
  };

  factory LandmarkCoordinates.fromJson(Map<String, dynamic> json) =>
      LandmarkCoordinates(
        x: (json['x'] as num).toDouble(),
        y: (json['y'] as num).toDouble(),
        z: (json['z'] as num?)?.toDouble(),
      );
}

/// Compatibility view used by the existing calibration and overlay code.
/// It always exposes image-space coordinates, never body-normalised values.
class NormalizedPoint {
  const NormalizedPoint({
    required this.x,
    required this.y,
    this.z = 0,
    this.visibility = 1,
  });

  final double x;
  final double y;
  final double z;
  final double visibility;

  bool get isVisible => visibility >= 0.5;
}

class LandmarkPoint {
  const LandmarkPoint({
    required this.index,
    required this.confidence,
    this.imageCoordinates,
    this.normalisedCoordinates,
    this.worldCoordinates,
    this.canonicalWorldCoordinates,
    this.velocity,
    this.acceleration,
    this.source = LandmarkSource.mediaPipe,
  }) : assert(confidence >= 0 && confidence <= 1);

  final int index;
  final double confidence;

  /// Original MediaPipe image-normalised coordinate. This is never y-flipped.
  final LandmarkCoordinates? imageCoordinates;

  /// Shoulder-relative 2D coordinate emitted by the normalisation stage.
  final LandmarkCoordinates? normalisedCoordinates;

  /// Original per-hand MediaPipe world coordinate, when supplied upstream.
  final LandmarkCoordinates? worldCoordinates;

  /// Wrist-centred, palm-rotation-canonical world coordinate when available.
  final LandmarkCoordinates? canonicalWorldCoordinates;

  /// Body-normalised units per second.
  final LandmarkCoordinates? velocity;

  /// Body-normalised units per second squared.
  final LandmarkCoordinates? acceleration;

  final LandmarkSource source;

  Map<String, dynamic> toJson() => <String, dynamic>{
    'index': index,
    'confidence': confidence,
    'source': source.name,
    if (imageCoordinates != null) 'image': imageCoordinates!.toJson(),
    if (normalisedCoordinates != null)
      'normalised': normalisedCoordinates!.toJson(),
    if (worldCoordinates != null) 'world': worldCoordinates!.toJson(),
    if (canonicalWorldCoordinates != null)
      'canonical_world': canonicalWorldCoordinates!.toJson(),
    if (velocity != null) 'velocity': velocity!.toJson(),
    if (acceleration != null) 'acceleration': acceleration!.toJson(),
  };

  factory LandmarkPoint.fromJson(Map<String, dynamic> json) => LandmarkPoint(
    index: (json['index'] as num).toInt(),
    confidence: (json['confidence'] as num).toDouble(),
    imageCoordinates: _coordinatesFromJson(json['image']),
    normalisedCoordinates: _coordinatesFromJson(json['normalised']),
    worldCoordinates: _coordinatesFromJson(json['world']),
    canonicalWorldCoordinates: _coordinatesFromJson(json['canonical_world']),
    velocity: _coordinatesFromJson(json['velocity']),
    acceleration: _coordinatesFromJson(json['acceleration']),
    source: _landmarkSourceFromName(json['source'] as String?),
  );
}

class LandmarkGroup {
  const LandmarkGroup({
    required this.isPresent,
    this.landmarks = const <LandmarkPoint?>[],
  });

  const LandmarkGroup.absent()
    : isPresent = false,
      landmarks = const <LandmarkPoint?>[];

  final bool isPresent;

  /// Index-addressable MediaPipe array. Null entries preserve absence.
  final List<LandmarkPoint?> landmarks;

  LandmarkPoint? pointAt(int index) {
    if (index >= 0 && index < landmarks.length) {
      final direct = landmarks[index];
      if (direct == null || direct.index == index) return direct;
    }
    for (final point in landmarks) {
      if (point?.index == index) return point;
    }
    return null;
  }

  Map<String, dynamic> toJson() => <String, dynamic>{
    'is_present': isPresent,
    'landmarks': landmarks
        .map((point) => point?.toJson())
        .toList(growable: false),
  };

  factory LandmarkGroup.fromJson(Map<String, dynamic> json) => LandmarkGroup(
    isPresent: json['is_present'] as bool? ?? false,
    landmarks: _landmarkListFromJson(json['landmarks']),
  );
}

class HandLandmarkGroup {
  const HandLandmarkGroup({
    required this.isPresent,
    this.landmarks = const <LandmarkPoint?>[],
    this.trackId,
    this.rawHandedness = Handedness.unknown,
    this.handedness = Handedness.unknown,
    this.handednessScore = 0.5,
    this.handednessRunningAverage = 0.5,
    this.handednessObservationCount = 0,
    this.handednessUncertain = false,
  }) : assert(handednessScore >= 0 && handednessScore <= 1),
       assert(handednessRunningAverage >= 0 && handednessRunningAverage <= 1);

  final bool isPresent;
  final List<LandmarkPoint?> landmarks;
  final String? trackId;

  /// Per-frame label received from MediaPipe.
  final Handedness rawHandedness;

  /// Stable label derived from the track-lifetime running average.
  final Handedness handedness;

  /// Confidence of [rawHandedness].
  final double handednessScore;

  /// Track-lifetime probability of the hand being right-handed.
  final double handednessRunningAverage;
  final int handednessObservationCount;
  final bool handednessUncertain;

  LandmarkPoint? pointAt(int index) {
    if (index >= 0 && index < landmarks.length) {
      final direct = landmarks[index];
      if (direct == null || direct.index == index) return direct;
    }
    for (final point in landmarks) {
      if (point?.index == index) return point;
    }
    return null;
  }

  HandLandmarkGroup copyWith({
    bool? isPresent,
    List<LandmarkPoint?>? landmarks,
    String? trackId,
    Handedness? rawHandedness,
    Handedness? handedness,
    double? handednessScore,
    double? handednessRunningAverage,
    int? handednessObservationCount,
    bool? handednessUncertain,
  }) => HandLandmarkGroup(
    isPresent: isPresent ?? this.isPresent,
    landmarks: landmarks ?? this.landmarks,
    trackId: trackId ?? this.trackId,
    rawHandedness: rawHandedness ?? this.rawHandedness,
    handedness: handedness ?? this.handedness,
    handednessScore: handednessScore ?? this.handednessScore,
    handednessRunningAverage:
        handednessRunningAverage ?? this.handednessRunningAverage,
    handednessObservationCount:
        handednessObservationCount ?? this.handednessObservationCount,
    handednessUncertain: handednessUncertain ?? this.handednessUncertain,
  );

  Map<String, dynamic> toJson() => <String, dynamic>{
    'is_present': isPresent,
    if (trackId != null) 'track_id': trackId,
    'raw_handedness': rawHandedness.name,
    'handedness': handedness.name,
    'handedness_score': handednessScore,
    'handedness_running_average': handednessRunningAverage,
    'handedness_observation_count': handednessObservationCount,
    'handedness_uncertain': handednessUncertain,
    'landmarks': landmarks
        .map((point) => point?.toJson())
        .toList(growable: false),
  };

  factory HandLandmarkGroup.fromJson(Map<String, dynamic> json) =>
      HandLandmarkGroup(
        isPresent: json['is_present'] as bool? ?? false,
        trackId: json['track_id'] as String?,
        rawHandedness: _handednessFromName(json['raw_handedness'] as String?),
        handedness: _handednessFromName(json['handedness'] as String?),
        handednessScore: (json['handedness_score'] as num?)?.toDouble() ?? 0.5,
        handednessRunningAverage:
            (json['handedness_running_average'] as num?)?.toDouble() ?? 0.5,
        handednessObservationCount:
            (json['handedness_observation_count'] as num?)?.toInt() ?? 0,
        handednessUncertain: json['handedness_uncertain'] as bool? ?? false,
        landmarks: _landmarkListFromJson(json['landmarks']),
      );
}

class LandmarkFrame {
  const LandmarkFrame({
    required this.timestamp,
    this.frameIndex = 0,
    this.subjectId,
    this.pose = const LandmarkGroup.absent(),
    this.face = const LandmarkGroup.absent(),
    this.hands = const <HandLandmarkGroup>[],
    this.coordinateSpace = LandmarkCoordinateSpace.mediaPipeImage,
    this.trackingStatus = TrackingStatus.absent,
    this.trackingQuality = 0,
    this.trackingIssues = const <TrackingIssue>[],
    this.canNormalise = false,
    this.normalisationOrigin,
    this.normalisationScale,
    this.normalisationAnchorIsStale = false,
    this.lightingScore = 0.9,
    this.featureVector = const <double>[],
  }) : assert(trackingQuality >= 0 && trackingQuality <= 1);

  /// Capture time propagated from the upstream camera frame.
  final DateTime timestamp;
  final int frameIndex;
  final String? subjectId;
  final LandmarkGroup pose;
  final LandmarkGroup face;
  final List<HandLandmarkGroup> hands;
  final LandmarkCoordinateSpace coordinateSpace;
  final TrackingStatus trackingStatus;
  final double trackingQuality;
  final List<TrackingIssue> trackingIssues;
  final bool canNormalise;
  final LandmarkCoordinates? normalisationOrigin;
  final double? normalisationScale;
  final bool normalisationAnchorIsStale;

  /// Retained for the existing calibration UI; not used by this service.
  final double lightingScore;

  /// Legacy UI storage only. Feature assembly belongs to the downstream stage.
  final List<double> featureVector;

  double get trackingConfidence => trackingQuality;

  NormalizedPoint? get leftShoulder =>
      pose.isPresent ? _imagePoint(pose.pointAt(11)) : null;
  NormalizedPoint? get rightShoulder =>
      pose.isPresent ? _imagePoint(pose.pointAt(12)) : null;

  NormalizedPoint? get leftWrist =>
      _imagePoint(_handFor(Handedness.left)?.pointAt(0)) ??
      (pose.isPresent ? _imagePoint(pose.pointAt(15)) : null);

  NormalizedPoint? get rightWrist =>
      _imagePoint(_handFor(Handedness.right)?.pointAt(0)) ??
      (pose.isPresent ? _imagePoint(pose.pointAt(16)) : null);

  bool get leftHandVisible => _handFor(Handedness.left)?.isPresent == true;
  bool get rightHandVisible => _handFor(Handedness.right)?.isPresent == true;

  bool get shouldersVisible =>
      leftShoulder?.isVisible == true && rightShoulder?.isVisible == true;

  bool get armsVisible =>
      leftWrist?.isVisible == true && rightWrist?.isVisible == true;

  /// Preserves the calibration screen's original two-hand requirement.
  bool get handsVisible => leftHandVisible && rightHandVisible;

  LandmarkFrame copyWith({
    LandmarkGroup? pose,
    LandmarkGroup? face,
    List<HandLandmarkGroup>? hands,
    LandmarkCoordinateSpace? coordinateSpace,
    TrackingStatus? trackingStatus,
    double? trackingQuality,
    List<TrackingIssue>? trackingIssues,
    bool? canNormalise,
    LandmarkCoordinates? normalisationOrigin,
    double? normalisationScale,
    bool clearNormalisation = false,
    bool? normalisationAnchorIsStale,
  }) => LandmarkFrame(
    timestamp: timestamp,
    frameIndex: frameIndex,
    subjectId: subjectId,
    pose: pose ?? this.pose,
    face: face ?? this.face,
    hands: hands ?? this.hands,
    coordinateSpace: coordinateSpace ?? this.coordinateSpace,
    trackingStatus: trackingStatus ?? this.trackingStatus,
    trackingQuality: trackingQuality ?? this.trackingQuality,
    trackingIssues: trackingIssues ?? this.trackingIssues,
    canNormalise: canNormalise ?? this.canNormalise,
    normalisationOrigin: clearNormalisation
        ? null
        : normalisationOrigin ?? this.normalisationOrigin,
    normalisationScale: clearNormalisation
        ? null
        : normalisationScale ?? this.normalisationScale,
    normalisationAnchorIsStale:
        normalisationAnchorIsStale ?? this.normalisationAnchorIsStale,
    lightingScore: lightingScore,
    featureVector: featureVector,
  );

  Map<String, dynamic> toJson() => <String, dynamic>{
    'frame_index': frameIndex,
    'capture_timestamp': timestamp.toUtc().toIso8601String(),
    if (subjectId != null) 'subject_id': subjectId,
    'pose': pose.toJson(),
    'face': face.toJson(),
    'hands': hands.map((hand) => hand.toJson()).toList(growable: false),
    'coordinate_space': coordinateSpace.name,
    'tracking_status': trackingStatus.name,
    'tracking_quality': trackingQuality,
    'tracking_issues': trackingIssues
        .map((issue) => issue.name)
        .toList(growable: false),
    'can_normalise': canNormalise,
    if (normalisationOrigin != null)
      'normalisation_origin': normalisationOrigin!.toJson(),
    if (normalisationScale != null) 'normalisation_scale': normalisationScale,
    'normalisation_anchor_is_stale': normalisationAnchorIsStale,
  };

  factory LandmarkFrame.fromJson(Map<String, dynamic> json) => LandmarkFrame(
    timestamp: DateTime.parse(
      (json['capture_timestamp'] ?? json['timestamp']) as String,
    ),
    frameIndex: (json['frame_index'] as num?)?.toInt() ?? 0,
    subjectId: json['subject_id'] as String?,
    pose: _groupFromJson(json['pose']),
    face: _groupFromJson(json['face']),
    hands: (json['hands'] as List<dynamic>? ?? <dynamic>[])
        .whereType<Map<String, dynamic>>()
        .map(HandLandmarkGroup.fromJson)
        .toList(growable: false),
    coordinateSpace: _coordinateSpaceFromName(
      json['coordinate_space'] as String?,
    ),
    trackingStatus: _trackingStatusFromName(json['tracking_status'] as String?),
    trackingQuality: (json['tracking_quality'] as num?)?.toDouble() ?? 0,
    trackingIssues: (json['tracking_issues'] as List<dynamic>? ?? <dynamic>[])
        .whereType<String>()
        .map(_trackingIssueFromName)
        .toList(growable: false),
    canNormalise: json['can_normalise'] as bool? ?? false,
    normalisationOrigin: _coordinatesFromJson(json['normalisation_origin']),
    normalisationScale: (json['normalisation_scale'] as num?)?.toDouble(),
    normalisationAnchorIsStale:
        json['normalisation_anchor_is_stale'] as bool? ?? false,
  );

  HandLandmarkGroup? _handFor(Handedness side) {
    for (final hand in hands) {
      if (hand.isPresent &&
          (hand.handedness == side ||
              (hand.handedness == Handedness.unknown &&
                  hand.rawHandedness == side))) {
        return hand;
      }
    }
    return null;
  }
}

NormalizedPoint? _imagePoint(LandmarkPoint? point) {
  final coordinates = point?.imageCoordinates;
  if (coordinates == null) return null;
  return NormalizedPoint(
    x: coordinates.x,
    y: coordinates.y,
    z: coordinates.z ?? 0,
    visibility: point!.confidence,
  );
}

LandmarkCoordinates? _coordinatesFromJson(Object? value) =>
    value is Map<String, dynamic> ? LandmarkCoordinates.fromJson(value) : null;

List<LandmarkPoint?> _landmarkListFromJson(Object? value) =>
    (value as List<dynamic>? ?? <dynamic>[])
        .map(
          (point) => point is Map<String, dynamic>
              ? LandmarkPoint.fromJson(point)
              : null,
        )
        .toList(growable: false);

LandmarkGroup _groupFromJson(Object? value) => value is Map<String, dynamic>
    ? LandmarkGroup.fromJson(value)
    : const LandmarkGroup.absent();

Handedness _handednessFromName(String? name) => switch (name) {
  'left' => Handedness.left,
  'right' => Handedness.right,
  _ => Handedness.unknown,
};

LandmarkSource _landmarkSourceFromName(String? name) => switch (name) {
  'poseWristSubstitution' => LandmarkSource.poseWristSubstitution,
  _ => LandmarkSource.mediaPipe,
};

LandmarkCoordinateSpace _coordinateSpaceFromName(String? name) =>
    switch (name) {
      'bodyNormalised' => LandmarkCoordinateSpace.bodyNormalised,
      _ => LandmarkCoordinateSpace.mediaPipeImage,
    };

TrackingStatus _trackingStatusFromName(String? name) => switch (name) {
  'degraded' => TrackingStatus.degraded,
  'tracked' => TrackingStatus.tracked,
  _ => TrackingStatus.absent,
};

TrackingIssue _trackingIssueFromName(String name) => switch (name) {
  'noHands' => TrackingIssue.noHands,
  'missingShoulders' => TrackingIssue.missingShoulders,
  'lowConfidence' => TrackingIssue.lowConfidence,
  'staleNormalisationAnchor' => TrackingIssue.staleNormalisationAnchor,
  'handednessUncertain' => TrackingIssue.handednessUncertain,
  _ => TrackingIssue.noLandmarks,
};
