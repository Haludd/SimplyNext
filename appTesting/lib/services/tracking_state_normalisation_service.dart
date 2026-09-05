/// Tracking-state ideas are independently reimplemented from the
/// MIT-licensed depthai-hand-tracker reference described by PLN T1.4. No
/// source code is copied or imported from that project.
library;

import 'dart:math' as math;

import '../models/landmark_frame.dart';

/// Tunable choices for the 30 FPS state and normalisation stages.
///
/// The PLN specifies the behaviour but not these numeric policies. Defaults
/// are deliberately explicit: confidence is gated at 0.5, histories reset
/// after 250 ms, a body anchor may bridge at most 500 ms of missing shoulders,
/// and hand/body coordinates use a causal 6 Hz low-pass filter. Face points
/// are never smoothed.
class TrackingStateNormalisationConfig {
  const TrackingStateNormalisationConfig({
    this.confidenceThreshold = 0.5,
    this.minimumTrackingQuality = 0.5,
    this.handednessDecisionThreshold = 0.6,
    this.handednessMismatchPenalty = 0.5,
    this.maximumHandMatchDistance = 0.35,
    this.trackExpiryFrames = 15,
    this.poseQualityIndices = const <int>[11, 12, 13, 14, 15, 16, 23, 24],
    this.expectedHandLandmarkCount = 21,
    this.maximumTemporalGap = const Duration(milliseconds: 250),
    this.normalisationAnchorTimeConstant = const Duration(milliseconds: 250),
    this.maximumNormalisationAnchorAge = const Duration(milliseconds: 500),
    this.minimumShoulderWidth = 0.0001,
    this.smoothingCutoffHz = 6,
  }) : assert(confidenceThreshold >= 0 && confidenceThreshold <= 1),
       assert(minimumTrackingQuality >= 0 && minimumTrackingQuality <= 1),
       assert(
         handednessDecisionThreshold > 0.5 && handednessDecisionThreshold <= 1,
       ),
       assert(handednessMismatchPenalty >= 0),
       assert(maximumHandMatchDistance > 0),
       assert(trackExpiryFrames >= 0),
       assert(expectedHandLandmarkCount > 0),
       assert(minimumShoulderWidth > 0),
       assert(smoothingCutoffHz > 0);

  final double confidenceThreshold;
  final double minimumTrackingQuality;
  final double handednessDecisionThreshold;
  final double handednessMismatchPenalty;
  final double maximumHandMatchDistance;
  final int trackExpiryFrames;

  /// Upper-body points used only to assess completeness, not to curate data.
  final List<int> poseQualityIndices;
  final int expectedHandLandmarkCount;
  final Duration maximumTemporalGap;
  final Duration normalisationAnchorTimeConstant;
  final Duration maximumNormalisationAnchorAge;
  final double minimumShoulderWidth;
  final double smoothingCutoffHz;
}

/// Adds stable hand identity, lifetime handedness, and frame tracking health.
///
/// This class consumes MediaPipe results through [LandmarkFrame]; it neither
/// invokes nor configures MediaPipe. In particular, the PLN detector
/// rate-limiter needs an upstream hook owned by `frontend_track` and is not
/// faked here.
class TrackingStateService {
  TrackingStateService({
    this.config = const TrackingStateNormalisationConfig(),
  });

  final TrackingStateNormalisationConfig config;
  final Map<String, _HandTrack> _tracks = <String, _HandTrack>{};

  DateTime? _lastTimestamp;
  String? _subjectId;
  var _hasProcessedFrame = false;
  var _sequence = 0;
  var _nextTrackId = 1;

  LandmarkFrame process(LandmarkFrame input) {
    _prepareFor(input);

    final identityTrackedHands = _assignTracks(input.hands);
    final wristCorrectedHands = identityTrackedHands
        .map((hand) => _substituteMeasuredPoseWrist(hand, input.pose))
        .toList(growable: false);

    final hasShoulders = _hasUsableShoulderPair(input.pose);
    final hasHand = wristCorrectedHands.any(
      (hand) => hand.isPresent && _hasUsablePoint(hand.landmarks),
    );
    final hasAnyLandmark =
        (input.pose.isPresent && _hasUsablePoint(input.pose.landmarks)) ||
        (input.face.isPresent && _hasUsablePoint(input.face.landmarks)) ||
        hasHand;
    final handQuality = _handTrackingQuality(wristCorrectedHands);
    final quality = _trackingQuality(input.pose, handQuality);
    final hasUncertainHandedness = wristCorrectedHands
        .where((hand) => hand.isPresent)
        .any((hand) => hand.handednessUncertain);

    final issues = <TrackingIssue>{};
    if (!hasAnyLandmark) issues.add(TrackingIssue.noLandmarks);
    if (!hasHand) issues.add(TrackingIssue.noHands);
    if (!hasShoulders) issues.add(TrackingIssue.missingShoulders);
    if (_hasLowConfidencePoint(input, wristCorrectedHands)) {
      issues.add(TrackingIssue.lowConfidence);
    }
    if (hasUncertainHandedness) {
      issues.add(TrackingIssue.handednessUncertain);
    }

    final status = !hasAnyLandmark
        ? TrackingStatus.absent
        : hasShoulders &&
              hasHand &&
              handQuality >= config.minimumTrackingQuality &&
              quality >= config.minimumTrackingQuality
        ? TrackingStatus.tracked
        : TrackingStatus.degraded;

    return input.copyWith(
      hands: wristCorrectedHands,
      trackingStatus: status,
      trackingQuality: quality,
      trackingIssues: issues.toList(growable: false),
      canNormalise: hasShoulders,
    );
  }

  void reset() {
    _tracks.clear();
    _lastTimestamp = null;
    _subjectId = null;
    _hasProcessedFrame = false;
    _sequence = 0;
    _nextTrackId = 1;
  }

  void _prepareFor(LandmarkFrame input) {
    if (_hasProcessedFrame) {
      final elapsed = input.timestamp.difference(_lastTimestamp!);
      final discontinuity =
          input.subjectId != _subjectId ||
          elapsed <= Duration.zero ||
          elapsed > config.maximumTemporalGap;
      if (discontinuity) reset();
    }

    _hasProcessedFrame = true;
    _subjectId = input.subjectId;
    _lastTimestamp = input.timestamp;
    _sequence += 1;
    _tracks.removeWhere(
      (_, track) =>
          _sequence - track.lastSeenSequence > config.trackExpiryFrames,
    );
  }

  HandLandmarkGroup _substituteMeasuredPoseWrist(
    HandLandmarkGroup hand,
    LandmarkGroup pose,
  ) {
    if (!hand.isPresent ||
        !pose.isPresent ||
        hand.handednessUncertain ||
        _isUsable(hand.pointAt(0))) {
      return hand;
    }

    final stableHandedness = hand.handedness != Handedness.unknown
        ? hand.handedness
        : _observedHandedness(hand);
    final poseIndex = switch (stableHandedness) {
      Handedness.left => 15,
      Handedness.right => 16,
      Handedness.unknown => null,
    };
    if (poseIndex == null) return hand;

    final poseWrist = pose.pointAt(poseIndex);
    if (!_isUsable(poseWrist)) return hand;

    final replacement = LandmarkPoint(
      index: 0,
      confidence: poseWrist!.confidence,
      imageCoordinates: poseWrist.imageCoordinates,
      source: LandmarkSource.poseWristSubstitution,
    );
    final points = List<LandmarkPoint?>.from(hand.landmarks);
    while (points.isEmpty) {
      points.add(null);
    }
    points[0] = replacement;
    return hand.copyWith(landmarks: points);
  }

  List<HandLandmarkGroup> _assignTracks(List<HandLandmarkGroup> hands) {
    if (hands.isEmpty) return const <HandLandmarkGroup>[];

    final anchors = hands.map(_handAnchor).toList(growable: false);
    final assignments = List<_HandTrack?>.filled(hands.length, null);
    final usedTrackIds = <String>{};

    for (var index = 0; index < hands.length; index += 1) {
      if (!hands[index].isPresent) continue;
      final requestedId = hands[index].trackId;
      final existing = requestedId == null ? null : _tracks[requestedId];
      if (existing != null && usedTrackIds.add(existing.id)) {
        assignments[index] = existing;
      }
    }

    final spatialAssignments = _bestSpatialAssignments(
      hands,
      anchors,
      assignments,
      usedTrackIds,
    );
    for (final assignment in spatialAssignments.entries) {
      assignments[assignment.key] = assignment.value;
      usedTrackIds.add(assignment.value.id);
    }

    for (var index = 0; index < hands.length; index += 1) {
      if (!hands[index].isPresent || assignments[index] != null) continue;
      final observed = _observedHandedness(hands[index]);
      if (observed == Handedness.unknown) continue;
      final labelMatches = _tracks.values
          .where(
            (track) =>
                !usedTrackIds.contains(track.id) &&
                track.settledHandedness == observed,
          )
          .toList(growable: false);
      if (labelMatches.length == 1) {
        assignments[index] = labelMatches.single;
        usedTrackIds.add(labelMatches.single.id);
      }
    }

    final trackedHands = <HandLandmarkGroup>[];
    for (var index = 0; index < hands.length; index += 1) {
      final hand = hands[index];
      if (!hand.isPresent) {
        trackedHands.add(hand.copyWith(handednessUncertain: false));
        continue;
      }
      final track = assignments[index] ?? _createTrack(hand);
      usedTrackIds.add(track.id);
      track.lastSeenSequence = _sequence;
      if (anchors[index] != null) track.lastAnchor = anchors[index];

      final observed = _observedHandedness(hand);
      _updateHandedness(track, observed, hand.handednessScore);
      trackedHands.add(
        hand.copyWith(
          trackId: track.id,
          rawHandedness: observed,
          handedness: track.settledHandedness,
          handednessRunningAverage: track.runningRightProbability,
          handednessObservationCount: track.handednessObservationCount,
          handednessUncertain:
              hand.handednessUncertain ||
              track.settledHandedness == Handedness.unknown,
        ),
      );
    }

    final presentHands = trackedHands.where((hand) => hand.isPresent);
    final rawCounts = _handednessCounts(
      presentHands.map((hand) => hand.rawHandedness),
    );
    final settledCounts = _handednessCounts(
      presentHands.map((hand) => hand.handedness),
    );
    return trackedHands
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
  }

  Map<int, _HandTrack> _bestSpatialAssignments(
    List<HandLandmarkGroup> hands,
    List<LandmarkCoordinates?> anchors,
    List<_HandTrack?> existingAssignments,
    Set<String> alreadyUsedTrackIds,
  ) {
    final handIndices = <int>[
      for (var index = 0; index < hands.length; index += 1)
        if (hands[index].isPresent &&
            existingAssignments[index] == null &&
            anchors[index] != null)
          index,
    ];
    final tracks = _tracks.values
        .where(
          (track) =>
              !alreadyUsedTrackIds.contains(track.id) &&
              track.lastAnchor != null,
        )
        .toList(growable: false);
    if (handIndices.isEmpty || tracks.isEmpty) {
      return const <int, _HandTrack>{};
    }

    var bestMatchCount = -1;
    var bestCost = double.infinity;
    var best = <int, _HandTrack>{};
    late void Function(
      int offset,
      Map<int, _HandTrack> selected,
      Set<String> usedIds,
      double cost,
    )
    search;
    search = (offset, selected, usedIds, cost) {
      if (offset == handIndices.length) {
        if (selected.length > bestMatchCount ||
            (selected.length == bestMatchCount && cost < bestCost)) {
          bestMatchCount = selected.length;
          bestCost = cost;
          best = Map<int, _HandTrack>.from(selected);
        }
        return;
      }

      final handIndex = handIndices[offset];
      search(offset + 1, selected, usedIds, cost);
      for (final track in tracks) {
        if (usedIds.contains(track.id)) continue;
        final distance = _distance2d(anchors[handIndex]!, track.lastAnchor!);
        if (distance > config.maximumHandMatchDistance) continue;
        selected[handIndex] = track;
        usedIds.add(track.id);
        search(
          offset + 1,
          selected,
          usedIds,
          cost + _handMatchCost(hands[handIndex], track, distance),
        );
        usedIds.remove(track.id);
        selected.remove(handIndex);
      }
    };
    search(0, <int, _HandTrack>{}, <String>{}, 0);
    return best;
  }

  double _handMatchCost(
    HandLandmarkGroup hand,
    _HandTrack track,
    double distance,
  ) {
    final observed = _observedHandedness(hand);
    final isConfidentMismatch =
        hand.handednessScore >= config.handednessDecisionThreshold &&
        observed != Handedness.unknown &&
        track.settledHandedness != Handedness.unknown &&
        observed != track.settledHandedness;
    return distance +
        (isConfidentMismatch ? config.handednessMismatchPenalty : 0);
  }

  _HandTrack _createTrack(HandLandmarkGroup hand) {
    final requestedId = hand.trackId?.trim();
    final id =
        requestedId != null &&
            requestedId.isNotEmpty &&
            !_tracks.containsKey(requestedId)
        ? requestedId
        : _nextGeneratedTrackId();
    final track = _HandTrack(id: id, lastSeenSequence: _sequence);
    _tracks[id] = track;
    return track;
  }

  String _nextGeneratedTrackId() {
    String candidate;
    do {
      candidate = 'hand-${_nextTrackId++}';
    } while (_tracks.containsKey(candidate));
    return candidate;
  }

  void _updateHandedness(
    _HandTrack track,
    Handedness observed,
    double confidence,
  ) {
    if (observed == Handedness.unknown) return;
    final boundedConfidence = _unit(confidence);
    final rightProbability = observed == Handedness.right
        ? boundedConfidence
        : 1 - boundedConfidence;
    track.rightProbabilityTotal += rightProbability;
    track.handednessObservationCount += 1;

    final average = track.runningRightProbability;
    final lowerThreshold = 1 - config.handednessDecisionThreshold;
    if (track.settledHandedness == Handedness.unknown) {
      if (average >= config.handednessDecisionThreshold) {
        track.settledHandedness = Handedness.right;
      } else if (average <= lowerThreshold) {
        track.settledHandedness = Handedness.left;
      }
    } else if (track.settledHandedness == Handedness.right &&
        average <= lowerThreshold) {
      track.settledHandedness = Handedness.left;
    } else if (track.settledHandedness == Handedness.left &&
        average >= config.handednessDecisionThreshold) {
      track.settledHandedness = Handedness.right;
    }
  }

  Handedness _observedHandedness(HandLandmarkGroup hand) =>
      hand.rawHandedness != Handedness.unknown
      ? hand.rawHandedness
      : hand.handedness;

  Map<Handedness, int> _handednessCounts(Iterable<Handedness> values) {
    final counts = <Handedness, int>{};
    for (final value in values) {
      counts[value] = (counts[value] ?? 0) + 1;
    }
    return counts;
  }

  LandmarkCoordinates? _handAnchor(HandLandmarkGroup hand) {
    if (!hand.isPresent) return null;
    final wrist = hand.pointAt(0);
    if (_isUsable(wrist)) return wrist!.imageCoordinates;

    final usable = hand.landmarks.whereType<LandmarkPoint>().where(_isUsable);
    var count = 0;
    var x = 0.0;
    var y = 0.0;
    for (final point in usable) {
      x += point.imageCoordinates!.x;
      y += point.imageCoordinates!.y;
      count += 1;
    }
    return count == 0 ? null : LandmarkCoordinates(x: x / count, y: y / count);
  }

  bool _hasUsableShoulderPair(LandmarkGroup pose) {
    if (!pose.isPresent) return false;
    final left = pose.pointAt(11);
    final right = pose.pointAt(12);
    if (!_isUsable(left) || !_isUsable(right)) return false;
    return _distance2d(left!.imageCoordinates!, right!.imageCoordinates!) >=
        config.minimumShoulderWidth;
  }

  bool _hasUsablePoint(List<LandmarkPoint?> points) => points.any(_isUsable);

  bool _isUsable(LandmarkPoint? point) =>
      point != null &&
      point.confidence >= config.confidenceThreshold &&
      point.imageCoordinates?.isFinite == true;

  bool _hasLowConfidencePoint(
    LandmarkFrame frame,
    List<HandLandmarkGroup> hands,
  ) =>
      <LandmarkPoint?>[
        if (frame.pose.isPresent) ...frame.pose.landmarks,
        if (frame.face.isPresent) ...frame.face.landmarks,
        for (final hand in hands)
          if (hand.isPresent) ...hand.landmarks,
      ].whereType<LandmarkPoint>().any(
        (point) => point.confidence < config.confidenceThreshold,
      );

  double _trackingQuality(LandmarkGroup pose, double handQuality) {
    final poseQuality = _indexedGroupQuality(
      pose.isPresent,
      pose.pointAt,
      config.poseQualityIndices,
    );
    return _unit((poseQuality + handQuality) / 2);
  }

  double _handTrackingQuality(List<HandLandmarkGroup> hands) {
    final presentHands = hands.where((hand) => hand.isPresent).toList();
    final expectedIndices = List<int>.generate(
      config.expectedHandLandmarkCount,
      (index) => index,
    );
    return presentHands.isEmpty
        ? 0.0
        : presentHands
                  .map(
                    (hand) => _indexedGroupQuality(
                      hand.isPresent,
                      hand.pointAt,
                      expectedIndices,
                    ),
                  )
                  .reduce((left, right) => left + right) /
              presentHands.length;
  }

  double _indexedGroupQuality(
    bool isPresent,
    LandmarkPoint? Function(int) pointAt,
    List<int> expectedIndices,
  ) {
    if (!isPresent || expectedIndices.isEmpty) return 0;
    var qualityTotal = 0.0;
    for (final index in expectedIndices) {
      final point = pointAt(index);
      if (_isUsable(point)) qualityTotal += _unit(point!.confidence);
    }
    return _unit(qualityTotal / expectedIndices.length);
  }
}

/// Converts image coordinates to a stable shoulder-relative signing space and
/// adds per-point velocity and acceleration.
class LandmarkNormalisationService {
  LandmarkNormalisationService({
    this.config = const TrackingStateNormalisationConfig(),
  });

  final TrackingStateNormalisationConfig config;
  final Map<String, _PointHistory> _history = <String, _PointHistory>{};
  final Set<String> _seenHistoryKeys = <String>{};

  _BodyAnchor? _anchor;
  DateTime? _lastTimestamp;
  String? _subjectId;
  var _hasProcessedFrame = false;

  LandmarkFrame process(LandmarkFrame input) {
    _prepareFor(input);

    final measurement = _shoulderMeasurement(input.pose);
    if (measurement != null) _updateAnchor(measurement, input.timestamp);

    var anchorIsStale = measurement == null && _anchor != null;
    if (_anchor != null &&
        input.timestamp.difference(_anchor!.measuredAt) >
            config.maximumNormalisationAnchorAge) {
      _anchor = null;
      anchorIsStale = false;
    }

    _seenHistoryKeys.clear();
    final pose = LandmarkGroup(
      isPresent: input.pose.isPresent,
      landmarks: _normalisePoints(
        input.pose.landmarks,
        isPresent: input.pose.isPresent,
        keyPrefix: 'pose',
        timestamp: input.timestamp,
        smooth: true,
      ),
    );
    final face = LandmarkGroup(
      isPresent: input.face.isPresent,
      landmarks: _normalisePoints(
        input.face.landmarks,
        isPresent: input.face.isPresent,
        keyPrefix: 'face',
        timestamp: input.timestamp,
        smooth: false,
      ),
    );
    final hands = input.hands
        .asMap()
        .entries
        .map((entry) => _normaliseHand(entry.value, entry.key, input.timestamp))
        .toList(growable: false);
    _history.removeWhere((key, _) => !_seenHistoryKeys.contains(key));

    final issues = input.trackingIssues.toSet();
    if (anchorIsStale) {
      issues.add(TrackingIssue.staleNormalisationAnchor);
    } else {
      issues.remove(TrackingIssue.staleNormalisationAnchor);
    }
    final canNormalise = _anchor != null;
    final status =
        input.trackingStatus == TrackingStatus.tracked && !canNormalise
        ? TrackingStatus.degraded
        : input.trackingStatus;

    return input.copyWith(
      pose: pose,
      face: face,
      hands: hands,
      coordinateSpace: LandmarkCoordinateSpace.bodyNormalised,
      trackingStatus: status,
      trackingIssues: issues.toList(growable: false),
      canNormalise: canNormalise,
      normalisationOrigin: _anchor?.centre,
      normalisationScale: _anchor?.shoulderWidth,
      clearNormalisation: !canNormalise,
      normalisationAnchorIsStale: anchorIsStale,
    );
  }

  void reset() {
    _history.clear();
    _seenHistoryKeys.clear();
    _anchor = null;
    _lastTimestamp = null;
    _subjectId = null;
    _hasProcessedFrame = false;
  }

  void _prepareFor(LandmarkFrame input) {
    if (_hasProcessedFrame) {
      final elapsed = input.timestamp.difference(_lastTimestamp!);
      final discontinuity =
          input.subjectId != _subjectId ||
          elapsed <= Duration.zero ||
          elapsed > config.maximumTemporalGap;
      if (discontinuity) reset();
    }
    _hasProcessedFrame = true;
    _subjectId = input.subjectId;
    _lastTimestamp = input.timestamp;
  }

  _ShoulderMeasurement? _shoulderMeasurement(LandmarkGroup pose) {
    if (!pose.isPresent) return null;
    final left = pose.pointAt(11);
    final right = pose.pointAt(12);
    if (!_isUsable(left) || !_isUsable(right)) return null;
    final leftCoordinates = left!.imageCoordinates!;
    final rightCoordinates = right!.imageCoordinates!;
    final width = _distance2d(leftCoordinates, rightCoordinates);
    if (width < config.minimumShoulderWidth) return null;
    return _ShoulderMeasurement(
      centre: LandmarkCoordinates(
        x: (leftCoordinates.x + rightCoordinates.x) / 2,
        y: (leftCoordinates.y + rightCoordinates.y) / 2,
      ),
      shoulderWidth: width,
    );
  }

  void _updateAnchor(_ShoulderMeasurement measurement, DateTime timestamp) {
    final current = _anchor;
    if (current == null) {
      _anchor = _BodyAnchor(
        centre: measurement.centre,
        shoulderWidth: measurement.shoulderWidth,
        measuredAt: timestamp,
      );
      return;
    }

    final elapsedSeconds =
        timestamp.difference(current.measuredAt).inMicroseconds /
        Duration.microsecondsPerSecond;
    final timeConstantSeconds =
        config.normalisationAnchorTimeConstant.inMicroseconds /
        Duration.microsecondsPerSecond;
    final alpha = timeConstantSeconds <= 0
        ? 1.0
        : 1 - math.exp(-elapsedSeconds / timeConstantSeconds);
    _anchor = _BodyAnchor(
      centre: _lerp2d(current.centre, measurement.centre, alpha),
      shoulderWidth:
          current.shoulderWidth +
          (measurement.shoulderWidth - current.shoulderWidth) * alpha,
      measuredAt: timestamp,
    );
  }

  HandLandmarkGroup _normaliseHand(
    HandLandmarkGroup hand,
    int listIndex,
    DateTime timestamp,
  ) {
    final canonicalWorld = hand.isPresent
        ? _canonicaliseHandWorldCoordinates(hand)
        : const <int, LandmarkCoordinates>{};
    final stableId = hand.trackId ?? 'untracked-$listIndex';
    return hand.copyWith(
      landmarks: _normalisePoints(
        hand.landmarks,
        isPresent: hand.isPresent,
        keyPrefix: 'hand:$stableId',
        timestamp: timestamp,
        smooth: true,
        canonicalWorld: canonicalWorld,
      ),
    );
  }

  List<LandmarkPoint?> _normalisePoints(
    List<LandmarkPoint?> points, {
    required bool isPresent,
    required String keyPrefix,
    required DateTime timestamp,
    required bool smooth,
    Map<int, LandmarkCoordinates> canonicalWorld =
        const <int, LandmarkCoordinates>{},
  }) => points
      .map(
        (point) => point == null
            ? null
            : _normalisePoint(
                point,
                groupIsPresent: isPresent,
                key: '$keyPrefix:${point.index}',
                timestamp: timestamp,
                smooth: smooth,
                canonicalWorld: canonicalWorld[point.index],
              ),
      )
      .toList(growable: false);

  LandmarkPoint _normalisePoint(
    LandmarkPoint point, {
    required bool groupIsPresent,
    required String key,
    required DateTime timestamp,
    required bool smooth,
    LandmarkCoordinates? canonicalWorld,
  }) {
    final anchor = _anchor;
    if (!groupIsPresent || anchor == null || !_isUsable(point)) {
      _history.remove(key);
      return _copyPoint(
        point,
        canonicalWorld:
            groupIsPresent && point.confidence >= config.confidenceThreshold
            ? canonicalWorld
            : null,
      );
    }

    final image = point.imageCoordinates!;
    final candidate = LandmarkCoordinates(
      x: (image.x - anchor.centre.x) / anchor.shoulderWidth,
      y: (image.y - anchor.centre.y) / anchor.shoulderWidth,
    );
    final previous = _history[key];
    final elapsedSeconds = previous == null
        ? null
        : timestamp.difference(previous.timestamp).inMicroseconds /
              Duration.microsecondsPerSecond;
    final position = smooth && previous != null && elapsedSeconds! > 0
        ? _lowPass(previous.position, candidate, elapsedSeconds)
        : candidate;

    LandmarkCoordinates? velocity;
    LandmarkCoordinates? acceleration;
    if (previous != null && elapsedSeconds! > 0) {
      velocity = _divide2d(
        _subtract2d(position, previous.position),
        elapsedSeconds,
      );
      if (previous.velocity != null) {
        acceleration = _divide2d(
          _subtract2d(velocity, previous.velocity!),
          elapsedSeconds,
        );
      }
    }

    _history[key] = _PointHistory(
      position: position,
      velocity: velocity,
      timestamp: timestamp,
    );
    _seenHistoryKeys.add(key);
    return _copyPoint(
      point,
      normalised: position,
      velocity: velocity,
      acceleration: acceleration,
      canonicalWorld: canonicalWorld,
    );
  }

  LandmarkPoint _copyPoint(
    LandmarkPoint source, {
    LandmarkCoordinates? normalised,
    LandmarkCoordinates? velocity,
    LandmarkCoordinates? acceleration,
    LandmarkCoordinates? canonicalWorld,
  }) => LandmarkPoint(
    index: source.index,
    confidence: source.confidence,
    imageCoordinates: source.imageCoordinates,
    normalisedCoordinates: normalised,
    worldCoordinates: source.worldCoordinates,
    canonicalWorldCoordinates: canonicalWorld,
    velocity: velocity,
    acceleration: acceleration,
    source: source.source,
  );

  LandmarkCoordinates _lowPass(
    LandmarkCoordinates previous,
    LandmarkCoordinates current,
    double elapsedSeconds,
  ) {
    final rc = 1 / (2 * math.pi * config.smoothingCutoffHz);
    final alpha = elapsedSeconds / (rc + elapsedSeconds);
    return _lerp2d(previous, current, alpha);
  }

  Map<int, LandmarkCoordinates> _canonicaliseHandWorldCoordinates(
    HandLandmarkGroup hand,
  ) {
    final wrist = _usableWorldPoint(hand.pointAt(0));
    final indexMcp = _usableWorldPoint(hand.pointAt(5));
    final pinkyMcp = _usableWorldPoint(hand.pointAt(17));
    if (wrist == null || indexMcp == null || pinkyMcp == null) {
      return const <int, LandmarkCoordinates>{};
    }

    final xAxis = _normalise3d(_subtract3d(indexMcp, pinkyMcp));
    final palmDirection = _subtract3d(
      _scale3d(_add3d(indexMcp, pinkyMcp), 0.5),
      wrist,
    );
    if (xAxis == null) return const <int, LandmarkCoordinates>{};
    final zAxis = _normalise3d(_cross3d(xAxis, palmDirection));
    if (zAxis == null) return const <int, LandmarkCoordinates>{};
    final yAxis = _normalise3d(_cross3d(zAxis, xAxis));
    if (yAxis == null) return const <int, LandmarkCoordinates>{};

    final result = <int, LandmarkCoordinates>{};
    for (final point in hand.landmarks.whereType<LandmarkPoint>()) {
      final world = _usableWorldPoint(point);
      if (world == null) continue;
      final relative = _subtract3d(world, wrist);
      result[point.index] = LandmarkCoordinates(
        x: _dot3d(relative, xAxis),
        y: _dot3d(relative, yAxis),
        z: _dot3d(relative, zAxis),
      );
    }
    return result;
  }

  LandmarkCoordinates? _usableWorldPoint(LandmarkPoint? point) {
    final world = point?.worldCoordinates;
    return point != null &&
            point.confidence >= config.confidenceThreshold &&
            world != null &&
            world.z != null &&
            world.isFinite
        ? world
        : null;
  }

  bool _isUsable(LandmarkPoint? point) =>
      point != null &&
      point.confidence >= config.confidenceThreshold &&
      point.imageCoordinates?.isFinite == true;
}

/// Synchronous pipeline facade for Harold's output and Esther's future input.
///
/// It intentionally exposes no queueing stream adapter. The 30 FPS capture
/// owner can call [process] only for its newest frame and drop older frames
/// under load, as required by the PLN.
class TrackingStateNormalisationService {
  TrackingStateNormalisationService({
    TrackingStateNormalisationConfig config =
        const TrackingStateNormalisationConfig(),
  }) : trackingState = TrackingStateService(config: config),
       normalisation = LandmarkNormalisationService(config: config);

  final TrackingStateService trackingState;
  final LandmarkNormalisationService normalisation;

  LandmarkFrame process(LandmarkFrame input) =>
      normalisation.process(trackingState.process(input));

  void reset() {
    trackingState.reset();
    normalisation.reset();
  }
}

class _HandTrack {
  _HandTrack({required this.id, required this.lastSeenSequence});

  final String id;
  int lastSeenSequence;
  LandmarkCoordinates? lastAnchor;
  double rightProbabilityTotal = 0;
  int handednessObservationCount = 0;
  Handedness settledHandedness = Handedness.unknown;

  double get runningRightProbability => handednessObservationCount == 0
      ? 0.5
      : rightProbabilityTotal / handednessObservationCount;
}

class _ShoulderMeasurement {
  const _ShoulderMeasurement({
    required this.centre,
    required this.shoulderWidth,
  });

  final LandmarkCoordinates centre;
  final double shoulderWidth;
}

class _BodyAnchor {
  const _BodyAnchor({
    required this.centre,
    required this.shoulderWidth,
    required this.measuredAt,
  });

  final LandmarkCoordinates centre;
  final double shoulderWidth;
  final DateTime measuredAt;
}

class _PointHistory {
  const _PointHistory({
    required this.position,
    required this.velocity,
    required this.timestamp,
  });

  final LandmarkCoordinates position;
  final LandmarkCoordinates? velocity;
  final DateTime timestamp;
}

double _unit(double value) => value.clamp(0.0, 1.0).toDouble();

double _distance2d(LandmarkCoordinates left, LandmarkCoordinates right) =>
    math.sqrt(math.pow(left.x - right.x, 2) + math.pow(left.y - right.y, 2));

LandmarkCoordinates _lerp2d(
  LandmarkCoordinates from,
  LandmarkCoordinates to,
  double amount,
) => LandmarkCoordinates(
  x: from.x + (to.x - from.x) * amount,
  y: from.y + (to.y - from.y) * amount,
);

LandmarkCoordinates _subtract2d(
  LandmarkCoordinates left,
  LandmarkCoordinates right,
) => LandmarkCoordinates(x: left.x - right.x, y: left.y - right.y);

LandmarkCoordinates _divide2d(LandmarkCoordinates value, double divisor) =>
    LandmarkCoordinates(x: value.x / divisor, y: value.y / divisor);

LandmarkCoordinates _add3d(
  LandmarkCoordinates left,
  LandmarkCoordinates right,
) => LandmarkCoordinates(
  x: left.x + right.x,
  y: left.y + right.y,
  z: (left.z ?? 0) + (right.z ?? 0),
);

LandmarkCoordinates _subtract3d(
  LandmarkCoordinates left,
  LandmarkCoordinates right,
) => LandmarkCoordinates(
  x: left.x - right.x,
  y: left.y - right.y,
  z: (left.z ?? 0) - (right.z ?? 0),
);

LandmarkCoordinates _scale3d(LandmarkCoordinates value, double scale) =>
    LandmarkCoordinates(
      x: value.x * scale,
      y: value.y * scale,
      z: (value.z ?? 0) * scale,
    );

LandmarkCoordinates _cross3d(
  LandmarkCoordinates left,
  LandmarkCoordinates right,
) => LandmarkCoordinates(
  x: left.y * (right.z ?? 0) - (left.z ?? 0) * right.y,
  y: (left.z ?? 0) * right.x - left.x * (right.z ?? 0),
  z: left.x * right.y - left.y * right.x,
);

double _dot3d(LandmarkCoordinates left, LandmarkCoordinates right) =>
    left.x * right.x + left.y * right.y + (left.z ?? 0) * (right.z ?? 0);

LandmarkCoordinates? _normalise3d(LandmarkCoordinates value) {
  final length = math.sqrt(_dot3d(value, value));
  return length <= 1e-12 ? null : _scale3d(value, 1 / length);
}
