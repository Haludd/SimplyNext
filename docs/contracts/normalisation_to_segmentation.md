# Normalisation → Segmentation Contract

## 1. Purpose

This document defines the internal frontend handoff from SignBridge's
tracking-state and normalisation stage to the segmentation stage.

- **Producer:** `frontend_state_norm` — receives tracked MediaPipe landmarks,
  assesses tracking health, and adds body-relative and temporal values.
- **Consumer:** `frontend_segment_classify` — receives the processed frame
  stream, detects utterance boundaries, and later emits a `FeatureWindow` plus
  a boundary event.

Esther's segmentation implementation begins **after** the `LandmarkFrame`
described here has been produced. This contract does not define or implement a
segmentation algorithm, classifier, network message, or backend payload.

### Authority labels

This draft uses the following labels so that planning requirements are not
confused with choices made by the current Dart implementation:

- **PLN-defined:** stated by `PLN_plan.md`.
- **Implementation-defined:** observable behaviour of the current
  `frontend_state_norm` Dart implementation where the PLN leaves the detail
  open.
- **Gap:** an unresolved mismatch or an item that still needs agreement.

## 2. Pipeline Position

```text
MediaPipe
    ↓
LandmarkFrame
    ↓
Tracking State
    ↓
Normalisation
    ↓
[NORMALISATION → SEGMENTATION CONTRACT (this document)]
    ↓
Esther's Segmentation
    ↓
FeatureWindow + utterance-boundary event
    ↓
Classification
```

**PLN-defined:** `LandmarkFrame` contains grouped landmark observations,
per-point confidence, handedness information, group presence, and
representable absence. The segmenter consumes a `LandmarkFrame` and produces a
`FeatureWindow` plus a boundary event.

**Current frontend boundary:** the same Dart `LandmarkFrame` type is passed
through tracking state and normalisation. Normalisation adds body-relative
coordinates, velocity, acceleration, and anchor metadata to its landmark
points before handing the frame to segmentation.

## 3. Input to Normalisation

Normalisation receives the `LandmarkFrame` emitted by `TrackingStateService`.
It does not call MediaPipe itself.

At minimum, the input carries:

| Input | Meaning |
|---|---|
| `timestamp`, `frameIndex`, `subjectId` | Capture identity propagated from the upstream frame. |
| `pose`, `face`, `hands` | Index-addressable landmark groups. A slot may be `null`; a group also has `isPresent`. |
| `LandmarkPoint.imageCoordinates` | Original MediaPipe image-space observation when one was measured. |
| `LandmarkPoint.confidence` | Per-point confidence in `[0, 1]`. |
| Hand identity and handedness fields | Stable `trackId`, raw label, stable label, score, running average, observation count, and uncertainty. |
| Tracking metadata | `trackingStatus`, `trackingQuality`, `trackingIssues`, and the tracking-stage value of `canNormalise`. |

Normalisation recomputes whether a usable body anchor exists. Consequently,
the **output** value of `canNormalise` is authoritative for Esther.

## 4. Output Produced by Normalisation

The output is one Dart `LandmarkFrame`. It preserves raw observations except
for the explicitly sourced measured pose-wrist substitution described below,
preserves tracking metadata, and adds normalised and temporal data where those
values can be calculated safely.

### 4.1 `LandmarkFrame`

| Field | Dart type / requiredness | Meaning, units, and range | Absence and interpretation | Data kind |
|---|---|---|---|---|
| `timestamp` | `DateTime`, required | Capture time, propagated unchanged. Temporal calculations use this value, not `frameIndex`. JSON uses UTC ISO-8601 under `capture_timestamp`. | Never null. Ordering is expected but not validated by the model. | Raw metadata; implementation-defined on Dart `LandmarkFrame`. PLN explicitly puts capture time on the earlier `Frame` but does not explicitly repeat it in `LandmarkFrame`. |
| `frameIndex` | `int`, present; default `0` | Upstream frame sequence metadata. No unit. | Never null. The model does not enforce non-negative or consecutive values. | Raw metadata; implementation-defined. |
| `subjectId` | `String?`, optional | Identifier of the selected signer. A change resets all normalisation history. | `null` means upstream supplied no subject identifier. | Raw metadata; PLN architecture requires a subject identifier on the earlier `Frame`. |
| `pose` | `LandmarkGroup`, required object | Pose landmark slots. Typical MediaPipe input has 33 slots, but the Dart model does not enforce a length. | The group remains present as an object; check `isPresent` and each nullable slot. | Mixed raw and derived point data. |
| `face` | `LandmarkGroup`, required object | Face landmark slots. The PLN expects a curated brow/mouth subset downstream; the Dart model does not enforce the subset or array length. | Same absence rules as `pose`. | Mixed raw and derived point data. |
| `hands` | `List<HandLandmarkGroup>`, required list | Zero or more hand groups. MediaPipe normally supplies 21 indexed points per detected hand; the Dart model does not enforce 21 or a two-hand maximum. | Empty means no hand group. A listed group may also have `isPresent == false`. | Mixed raw and derived point data. |
| `coordinateSpace` | `LandmarkCoordinateSpace`, required | Normalisation always emits `bodyNormalised`. | Never null. `bodyNormalised` does **not** guarantee every point has a normalised coordinate; check the point and `canNormalise`. | Derived metadata. |
| `trackingStatus` | `TrackingStatus`, required | `absent`, `degraded`, or `tracked`; see section 7. | Never null. | Tracking-state result. |
| `trackingQuality` | `double`, required | Overall tracking quality in `[0, 1]`. | Never null. It is not a classifier confidence. | Tracking-state result; formula implementation-defined. |
| `trackingIssues` | `List<TrackingIssue>`, required list | Zero or more diagnostic conditions. Treat it as a set; ordering is not contractual. | Empty means no recorded issue. | Tracking/normalisation diagnostics. |
| `canNormalise` | `bool`, required | Whether the output currently has a usable fresh or permitted stale shoulder anchor. | `false` means body-relative 2D output cannot be produced for the current frame. | Derived metadata; implementation-defined policy. |
| `normalisationOrigin` | `LandmarkCoordinates?` | Running anchor centre derived from shoulder-midpoint measurements, in raw MediaPipe image coordinates. `z` is null. | Null exactly when no anchor is available. | Raw-space anchor metadata. |
| `normalisationScale` | `double?` | Running anchor scale derived from Euclidean inter-shoulder distance, in raw image-coordinate units; positive when present. | Null exactly when no anchor is available. | Raw-space anchor metadata. |
| `normalisationAnchorIsStale` | `bool`, required | `true` when the most recent accepted shoulder anchor is being reused because the current frame has no usable shoulder pair. | Never null. `false` means fresh anchor or no anchor. | Derived metadata; implementation-defined. |

`lightingScore` and `featureVector` exist in the current Dart class only for
legacy UI compatibility. They are not serialized by `LandmarkFrame.toJson()`,
are not written by this service, and are **not part of this handoff**. Esther
must not use them as segmentation inputs.

### 4.2 `LandmarkGroup`

| Field | Type / requiredness | Contract |
|---|---|---|
| `isPresent` | `bool`, required | Authoritative group-presence flag. If false, the group's attached point values must not be consumed, even if stale coordinates are present. |
| `landmarks` | `List<LandmarkPoint?>`, required list | Index-addressable array. A `null` element means that exact landmark was not observed. Array length is preserved by normalisation but is not validated by the Dart model. Use `pointAt(index)` rather than unchecked direct indexing. |

**PLN-defined:** group presence and missing observations must be
representable.

### 4.3 `HandLandmarkGroup`

| Field | Type / requiredness | Meaning and range | Absence |
|---|---|---|---|
| `isPresent` | `bool`, required | Authoritative hand-group presence. | False means do not consume that group's geometry. |
| `landmarks` | `List<LandmarkPoint?>`, required | Indexed hand observations, normally MediaPipe indices `0..20`. | Individual slots may be null. |
| `trackId` | `String?` | Best-effort hand identity across continuous frames. Generated values currently look like `hand-1`; a track expires after more than 15 missed processed frames, and an upstream-requested ID is accepted when available. | Nullable and may be retained on an absent group. It is not globally unique and may be reused after reset; never use it to consume geometry when `isPresent` is false. |
| `rawHandedness` | `Handedness` | Per-frame `left`, `right`, or `unknown` observation received from upstream. | `unknown` represents no usable label. |
| `handedness` | `Handedness` | Stable lifetime label derived by tracking state. | `unknown` means the running evidence is not decisive. |
| `handednessScore` | `double` | Confidence in the raw label. Required input range is `[0, 1]`; the constructor uses a debug assertion rather than release-mode validation. | Never null; default `0.5`. |
| `handednessRunningAverage` | `double` | Running probability of the tracked hand being right-handed. Required range is `[0, 1]`; the constructor uses a debug assertion. | Never null; `0.5` is neutral/no evidence. |
| `handednessObservationCount` | `int` | Number of labelled observations included in the running average. | `0` means no labelled observation. |
| `handednessUncertain` | `bool` | True for undecided or conflicting/duplicate handedness. Both duplicate hands are retained. | Never null. |

**Implementation-defined:** a right probability of at least `0.6` settles to
right and at most `0.4` settles to left. Values strictly between those limits
remain unknown. Normalisation preserves these fields; it does not recalculate
them.

The hand list preserves upstream list order, but order is not a continuity
identifier. Esther must use `trackId` when associating the same hand across
frames.

### 4.4 `LandmarkPoint`

| Field | Type / requiredness | Meaning, units, coordinate system, and range | Null meaning | Raw/derived |
|---|---|---|---|---|
| `index` | `int`, required | MediaPipe landmark index within its group. | Never null. | Raw identity. |
| `confidence` | `double`, required | Upstream per-point confidence. Required input range is `[0, 1]`; the constructor uses a debug assertion rather than release-mode validation. | Never null. | Raw measurement. |
| `imageCoordinates` | `LandmarkCoordinates?` | Original MediaPipe image coordinates. `x` grows right; `y` grows down from the top-left. `z`, when present, is MediaPipe-relative ordering and is not metric depth. The Dart contract does not enforce `x/y` to `[0, 1]`. | No image measurement was supplied. | Raw and preserved. |
| `normalisedCoordinates` | `LandmarkCoordinates?` | Shoulder-relative 2D position in shoulder-width units. `x/y` are intended to be finite for normal MediaPipe-scale input but are unbounded; `z` is null. | The group is absent, point is missing/rejected, or no anchor exists. | Derived. |
| `worldCoordinates` | `LandmarkCoordinates?` | Original per-hand MediaPipe world coordinate when supplied. Its scale/unit is inherited from upstream and is not validated by this Dart model. | Upstream supplied no world coordinate. | Raw and preserved. |
| `canonicalWorldCoordinates` | `LandmarkCoordinates?` | Wrist-centred, palm-rotation-canonical coordinate. Unit/scale remains that of `worldCoordinates`. | Required world basis or the point itself was unavailable/rejected. | Derived. |
| `velocity` | `LandmarkCoordinates?` | Change in emitted normalised `x/y` per second. `z` is null. | First valid observation, reset, missing/rejected point, or invalid anchor. | Derived. |
| `acceleration` | `LandmarkCoordinates?` | Change in emitted velocity per second, therefore shoulder-width units per second squared. `z` is null. | Fewer than three continuous valid observations, reset, or missing/rejected data. | Derived. |
| `source` | `LandmarkSource`, required | `mediaPipe` or `poseWristSubstitution`. | Never null. | Provenance metadata. |

`LandmarkCoordinates` contains required finite-intended `double x`, `double y`,
and optional `double? z`. The model itself permits non-finite doubles; the
service rejects non-finite coordinates before deriving normalised values.

### 4.5 Tracking issues

| Value | Meaning |
|---|---|
| `noLandmarks` | No usable point exists in any present pose, face, or hand group. |
| `noHands` | No present hand contains a usable point. |
| `missingShoulders` | A usable two-shoulder reference is unavailable in the current tracking input. |
| `lowConfidence` | At least one non-null `LandmarkPoint` object in a present group has confidence below the gate, even if that object's image coordinate is itself null. |
| `staleNormalisationAnchor` | The current shoulders are unusable, but a permitted previous anchor is being reused. |
| `handednessUncertain` | At least one present hand has undecided or conflicting handedness. |

## 5. Coordinate / Normalisation Convention

### 5.1 Body-relative 2D coordinates

For usable left and right shoulder image coordinates `L` and `R`:

```text
origin C = (L + R) / 2
scale  S = EuclideanDistance(L, R)

normalised_x = (image_x - C_x) / S
normalised_y = (image_y - C_y) / S
```

Therefore, for horizontal shoulders:

```text
left shoulder  = (-0.5, 0)
right shoulder = ( 0.5, 0)
```

Esther may rely on these properties when `canNormalise == true` and the point's
`normalisedCoordinates != null`:

- The retained anchor centre maps to the origin `(0, 0)`.
- One retained anchor-scale distance equals one coordinate unit.
- Translation and uniform image-scale differences are removed.
- `x` retains the input image direction: positive is to the right.
- `y` retains MediaPipe's top-left convention: positive is downward. There is
  **no y-flip**.
- Body coordinates are translated and scaled but are not rotated to make the
  shoulder line horizontal.
- Normalised `x/y` are not clamped; values outside `[-1, 1]` are valid.
- Body-normalised `z` is not produced (`z == null`). Raw image `z` must not be
  treated as metric depth.
- A missing non-wrist point stays null. Hand wrist `0` is the only exception:
  tracking state may copy an actually measured corresponding pose wrist and
  mark its source `poseWristSubstitution`. Zero is a real coordinate and must
  never be used as a missing-value marker.

Because the anchor is a running estimate, a current shoulder midpoint need not
map to exactly `(0, 0)`, and current horizontal shoulders need not be exactly
`-0.5/+0.5`, after the signer or camera moves. Those exact values hold for a
fresh horizontal measurement or when the running anchor already equals the
current measurement.

### 5.2 Anchor behaviour

**Implementation-defined:** both shoulder points must be present, finite, and
have confidence `>= 0.5`; their distance must be `>= 0.0001`.

The first valid pair becomes the anchor directly. Later valid measurements
update the running anchor using the elapsed time since the previous accepted
shoulder measurement:

```text
alpha = 1 - exp(-delta_since_previous_accepted_measurement / 0.250)
anchor = previous_anchor + alpha * (measurement - previous_anchor)
```

If the current shoulders are unavailable, the last anchor may be reused for
at most `500 ms`. Reuse sets `normalisationAnchorIsStale == true` and adds
`staleNormalisationAnchor`. At an age greater than `500 ms`, the anchor is
removed.

### 5.3 Canonical hand world coordinates

Canonical world processing uses a separate validity rule from body-relative
2D processing. A world point is valid here when its confidence is `>= 0.5`,
its `worldCoordinates.x/y/z` are finite, and `z` is present. It does not need a
valid `imageCoordinates` or shoulder anchor.

When hand world points `0` (wrist), `5` (index MCP), and `17` (pinky MCP) all
meet that rule, normalisation constructs a palm coordinate basis. Each
available valid world point is translated so the wrist is `(0, 0, 0)` and
rotated into that basis. This removes palm rotation but does not rescale the
hand or convert its units. Canonical world output may therefore exist even
when `canNormalise == false` for body-relative 2D coordinates.

If the basis is missing or degenerate, `canonicalWorldCoordinates` is null;
raw `worldCoordinates` remain untouched.

## 6. Temporal Semantics

### 6.1 Ordering and frame rate

- The frontend target is approximately `30 FPS`.
- `timestamp` is the source of elapsed time. `frameIndex` is propagated
  metadata and is not used to calculate derivatives.
- Frames should arrive in capture order for the same `subjectId`.
- The synchronous service does not queue frames. Upstream may drop old frames
  under load, so frame indices need not be consecutive.

### 6.2 Smoothing

**PLN-defined:** smooth pose/body and hands, but do not smooth the face.

**Implementation-defined:** pose and hand normalised positions use a causal
first-order `6 Hz` low-pass filter:

```text
RC    = 1 / (2 * pi * 6)
alpha = delta_seconds / (RC + delta_seconds)
position = previous_position + alpha * (candidate - previous_position)
```

Face positions use the current candidate directly. Face velocity and
acceleration, when available, are consequently derived from unsmoothed face
positions.

### 6.3 Velocity and acceleration

For a continuously usable point:

```text
velocity     = (position_now - position_previous) / delta_seconds
acceleration = (velocity_now - velocity_previous) / delta_seconds
```

- Velocity uses the emitted position (filtered for pose/hands; unfiltered for
  face).
- The first valid observation has null velocity and null acceleration.
- The second continuous valid observation may have velocity but has null
  acceleration.
- Acceleration normally begins on the third continuous valid observation.
- Values use seconds even though capture timestamps may have millisecond or
  microsecond resolution.

### 6.4 Resets and discontinuities

**Implementation-defined:** the combined service resets its running anchor,
per-point temporal histories, tracked-hand identities, handedness running
averages/observation counts, and generated hand-ID counter when:

- `subjectId` changes;
- `timestamp` does not increase (`delta <= 0`); or
- the gap between processed frames is greater than `250 ms`.

The current frame is still processed after a reset. If it has a valid anchor,
it receives a normalised position, but velocity and acceleration restart as
null. Exactly `250 ms` does not trigger this reset.

These three conditions define the end of a continuous **tracking epoch**. A
generated string such as `hand-1` may be reused in a later epoch, so the
consumer must not join hand history across an epoch boundary merely because
the `trackId` text matches.

There is no teleport/outlier rejection. A large position jump within the time
limit is processed normally and may produce a large velocity. For ordinary
MediaPipe-scale inputs the result is finite, but the service does not perform a
post-transform overflow/finite check on derived arithmetic.

### 6.5 Disappearance and reappearance

After the explicit pose-wrist correction has run, when a remaining point is
null, its group is absent, its confidence falls below the gate, its image
coordinate is non-finite, or no anchor exists, normalisation:

1. preserves the raw measurement/null representation;
2. emits null normalised coordinates, velocity, and acceleration; and
3. removes that point's temporal history.

If the point later reappears, it starts as a new first observation with a
normalised position and null velocity/acceleration. Previous coordinates are
not copied forward.

## 7. Tracking-State Semantics

### 7.1 Usable point and quality

**Implementation-defined:** a point is usable when it is non-null, has a
finite `imageCoordinates`, and has confidence `>= 0.5`.

```text
pose_quality = sum(usable confidence at pose indices
                   11,12,13,14,15,16,23,24) / 8

one_hand_quality = sum(usable confidence at hand indices 0..20) / 21
hand_quality     = mean(one_hand_quality for each present hand)
                   or 0 when no hand is present

tracking_quality = clamp((pose_quality + hand_quality) / 2, 0, 1)
```

Face confidence can prevent the state from being `absent`, but it does not
increase `trackingQuality` in the current implementation.

### 7.2 States received by segmentation

| State | Current producer meaning | Data safe to consume | Segmentation action |
|---|---|---|---|
| `tracked` | A valid shoulder pair exists; at least one usable hand point exists; `handQuality >= 0.5`; and total quality `>= 0.5`. | Consume only present groups and non-null per-point derived fields. Check `canNormalise` as well. | The contract does not mandate a start/continue/stop decision. This is normal evidence for the segmenter. |
| `degraded` | Some usable landmark exists, but one or more `tracked` conditions fail; or normalisation received `tracked` but cannot establish an anchor. | Any individual non-null normalised/temporal values remain valid. Inspect `trackingIssues`; do not assume all groups are complete. | PLN does not define whether to buffer, pause, or discard. Esther's segmentation policy must decide and document it. |
| `absent` | No usable point exists in any present pose, face, or hand group. | Metadata, presence flags, and explicit absence only. Do not interpret missing geometry as zeros. | PLN does not define the boundary action here. It may be temporal evidence for Esther's missing-hand/inactivity policy. |

There is no tracking-status hysteresis in this service. State changes are
immediate. The PLN's subject-selection hysteresis belongs upstream, and
utterance-boundary hysteresis belongs to segmentation.

`canNormalise` and `trackingStatus` answer different questions. For example,
an absent current frame may temporarily retain a stale anchor and therefore
have `canNormalise == true`, while still containing no current landmark
coordinates to consume.

## 8. Missing / Invalid Data

| Situation | Guaranteed output behaviour |
|---|---|
| Missing point | Its array slot remains `null`; no coordinate is fabricated, except that missing/rejected hand wrist `0` may be replaced by the corresponding actually measured pose wrist under the guarded rule below. |
| `isPresent == false` group with old coordinates | Presence flag is authoritative; attached points receive no normalised or temporal fields. |
| Confidence below `0.5` | Raw point/confidence is preserved; normalised coordinate, velocity, and acceleration are null, except when the guarded hand-wrist substitution replaces hand wrist `0` with measured pose-wrist evidence. |
| Non-finite image coordinate | No normalised or temporal value is derived and raw evidence is retained for diagnosis, except when the guarded hand-wrist substitution replaces hand wrist `0`. |
| One missing/invalid shoulder or shoulder width below `0.0001` | No new anchor is created. A permitted earlier anchor may be marked stale and reused; otherwise `canNormalise` is false. |
| No anchor | `normalisationOrigin` and `normalisationScale` are null. All body-relative `normalisedCoordinates`, velocity, and acceleration are null. |
| Zero/negative time delta | Anchor/temporal history and hand tracking identity/averages reset; current valid positions may be emitted, derivatives restart as null. |
| Gap greater than `250 ms` or subject change | Same full reset behaviour and a new tracking epoch begins. |
| Point reappears | Current position is calculated; velocity and acceleration are null until sufficient continuous history exists. |
| Low/missing hand wrist | Tracking substitutes only when the hand and pose groups are present, the hand wrist is unusable, the corresponding pose wrist is usable, and stable handedness is known and not uncertain. It replaces the hand wrist's image coordinate/confidence only, marks `source: poseWristSubstitution`, and supplies no hand-world coordinate. No guessed wrist is created. |

**No interpolation is currently performed.** Apart from the measured
pose-wrist substitution, missing points are not copied, zero-filled, or
guessed.

## 9. Expected Downstream Use

The producer exposes only synchronous
`LandmarkFrame process(LandmarkFrame input)`. It does not itself deliver a
stream or guarantee that every captured frame reaches Esther. The integration
caller must pass processed frames in capture order; gaps are allowed. For every
frame delivered, Esther should:

1. preserve `timestamp`, `frameIndex`, and `subjectId` association;
2. use group presence plus nullable point fields rather than assuming complete
   arrays;
3. use `normalisedCoordinates` for body-relative geometric/motion decisions,
   not raw `imageCoordinates`;
4. use velocity/acceleration directly when non-null rather than recomputing
   them with a different convention;
5. retain confidence, presence flags, and null-slot absence when assembling a
   downstream window;
6. use tracking metadata as input evidence without treating it as an
   utterance-boundary decision; and
7. avoid treating raw or canonical `z` as metric camera depth.

**Segmentation owns:** temporal boundary state, hysteresis/debounce,
buffer-and-replay or sliding-window policy, utterance start/end decisions,
frame-window assembly, and emission of `FeatureWindow` plus the boundary event.

**Tracking State owns:** hand identity/handedness and the initial tracking
status, quality, and issues.

**Normalisation owns:** body-anchor availability/staleness, per-point
confidence gating, body-relative positions, canonical hand-world coordinates,
and available per-point velocity/acceleration. It preserves tracking metadata,
adds/removes the stale-anchor issue, and may downgrade `tracked` to `degraded`
when no anchor exists.

## 10. Segmentation Handoff

```text
NORMALISATION OUTPUT
        ↓
 processed LandmarkFrame
        ↓
ESTHER'S SEGMENTATION
```

The current producer API is:

```dart
import 'package:apptesting/models/landmark_frame.dart';
import 'package:apptesting/services/tracking_state_normalisation_service.dart';

final service = TrackingStateNormalisationService();
LandmarkFrame output = service.process(mediaPipeLandmarkFrame);
```

`process` returns synchronously. No queue, stream, callback, or transport
adapter is supplied by this stage; the integration caller owns delivery to
Esther.

The caller must reuse the same `TrackingStateNormalisationService` instance
for consecutive frames in one tracking stream/session. Constructing a new
instance per frame discards hand identity, handedness averages, anchor
smoothing, velocity, and acceleration history. Calling `reset()` deliberately
starts a new tracking epoch.

### Minimum data needed to begin segmentation

At minimum, the consumer needs:

- `timestamp` and `frameIndex`;
- `subjectId` when available;
- `trackingStatus`, `trackingQuality`, `trackingIssues`;
- `canNormalise` and `normalisationAnchorIsStale`;
- group `isPresent` flags;
- hand `trackId`, stable handedness, running average, and uncertainty;
- each point's `index`, `confidence`, nullable `normalisedCoordinates`, and
  nullable velocity/acceleration;
- each point's available raw `worldCoordinates`, derived
  `canonicalWorldCoordinates`, and `source` provenance. Whether and how these
  enter the future `FeatureWindow` remains a shared-contract decision; Esther
  must not silently discard them before that decision is made.

PLN T2.2's prescribed geometric segmentation arm logically needs the available
pose shoulders (`11`, `12`), pose wrists (`15`, `16`) or hand wrists (`0`),
hips (`23`, `24`), point confidence/absence, and elapsed capture time. This
statement identifies required input evidence; it does not define Esther's
algorithm or its output schema.

### Not provided by this stage

Normalisation does not provide:

- an utterance start/end decision;
- a boundary event;
- a `FeatureWindow` implementation or frame-index range;
- a segmenter-arm identifier;
- pre-roll/replay buffers, inactivity timers, or segmentation hysteresis;
- classifier features, logits, glosses, or class scores;
- a `GlossLattice`;
- raw camera frames;
- a network/WebSocket call; or
- guaranteed contiguous frame indices.

## 11. Contract Examples

The following are readable excerpts. Keys such as `pose[11]` identify an array
slot for clarity; the actual Dart JSON uses `pose.landmarks` and
`hands[n].landmarks` arrays containing objects or nulls.

### Example A — normal valid frame

Input from tracking state includes pose confidence `0.98`, two 21-point hands
at `0.96`, and left/right handedness score `0.95` at frame 100:

```text
INPUT
timestamp = 2026-09-06T12:00:00.000Z
pose[11].image = (0.40, 0.35, -0.05), confidence = 0.98
pose[12].image = (0.60, 0.35, -0.05), confidence = 0.98
hands[0].landmarks[0].image = (0.30, 0.58, -0.01), confidence = 0.96
hands[1].landmarks[0].image = (0.70, 0.58, -0.01), confidence = 0.96
trackingStatus = tracked, trackingQuality = 0.97
```

Normalisation produces this readable output excerpt:

```json
{
  "frame_index": 100,
  "capture_timestamp": "2026-09-06T12:00:00.000Z",
  "subject_id": "subject-harold-001",
  "coordinate_space": "bodyNormalised",
  "tracking_status": "tracked",
  "tracking_quality": 0.97,
  "tracking_issues": [],
  "can_normalise": true,
  "normalisation_origin": {"x": 0.5, "y": 0.35},
  "normalisation_scale": 0.2,
  "normalisation_anchor_is_stale": false,
  "pose[11]": {
    "index": 11,
    "confidence": 0.98,
    "image": {"x": 0.4, "y": 0.35, "z": -0.05},
    "normalised": {"x": -0.5, "y": 0.0},
    "source": "mediaPipe"
  },
  "pose[12]": {
    "index": 12,
    "confidence": 0.98,
    "image": {"x": 0.6, "y": 0.35, "z": -0.05},
    "normalised": {"x": 0.5, "y": 0.0},
    "source": "mediaPipe"
  },
  "hands[0]": {
    "track_id": "hand-1",
    "raw_handedness": "left",
    "handedness": "left",
    "handedness_score": 0.95,
    "handedness_running_average": 0.05,
    "handedness_observation_count": 1,
    "handedness_uncertain": false
  },
  "hands[0].landmarks[0]": {
    "index": 0,
    "confidence": 0.96,
    "image": {"x": 0.3, "y": 0.58, "z": -0.01},
    "normalised": {"x": -1.0, "y": 1.15},
    "canonical_world": {"x": 0.0, "y": 0.0, "z": 0.0},
    "source": "mediaPipe"
  }
}
```

Because this is the point's first continuous observation, `velocity` and
`acceleration` keys are absent/null.

### Example B — partial/missing landmark

The right-hand index fingertip (`index 8`) disappears one frame after a valid
frame. Its exact array slot stays null:

```text
INPUT
frameIndex = 101, timestamp = 2026-09-06T12:00:00.033333Z
hands[1].isPresent = true
hands[1].landmarks[8] = null
all other fixture pose/hand observations remain present and confident
```

Normalisation produces this readable output excerpt:

```json
{
  "frame_index": 101,
  "capture_timestamp": "2026-09-06T12:00:00.033333Z",
  "tracking_status": "tracked",
  "tracking_quality": 0.9585714285714285,
  "can_normalise": true,
  "hands[1].is_present": true,
  "hands[1].landmarks[8]": null
}
```

No earlier coordinate, zero, velocity, or acceleration is inserted. When the
point reappears, its normalised coordinate is emitted but its velocity and
acceleration restart as null.

### Example C — degraded tracking / invalid body reference

The right shoulder (`pose[12]`) is missing on a fresh service while all other
fixture observations remain confident:

```text
INPUT
frameIndex = 100, timestamp = 2026-09-06T12:00:00.000Z
pose.isPresent = true
pose[11].image = (0.40, 0.35, -0.05), confidence = 0.98
pose[12] = null
trackingStatus = degraded, trackingQuality = 0.90875
trackingIssues = [missingShoulders]
```

Normalisation produces this readable output excerpt:

```json
{
  "frame_index": 100,
  "capture_timestamp": "2026-09-06T12:00:00.000Z",
  "coordinate_space": "bodyNormalised",
  "tracking_status": "degraded",
  "tracking_quality": 0.90875,
  "tracking_issues": ["missingShoulders"],
  "can_normalise": false,
  "normalisation_origin": null,
  "normalisation_scale": null,
  "normalisation_anchor_is_stale": false,
  "pose[11].image": {"x": 0.4, "y": 0.35, "z": -0.05},
  "pose[11].normalised": null,
  "pose[12]": null,
  "hands[0].landmarks[0].normalised": null
}
```

The actual serializer omits nullable point/anchor keys instead of writing all
of the shown null-valued explanatory keys. If an earlier valid anchor is at
most `500 ms` old, the alternative output is `can_normalise: true`,
`normalisation_anchor_is_stale: true`, and issue
`staleNormalisationAnchor`; any current usable points may then be normalised
against that explicitly stale anchor.

## 12. Acceptance Criteria

Esther can use this checklist when integrating segmentation:

- [ ] Consumes the processed Dart `LandmarkFrame`, not a raw camera frame or a
      second MediaPipe implementation.
- [ ] Preserves `timestamp`, `frameIndex`, and `subjectId` while buffering
      frames.
- [ ] Does not assume frame indices are contiguous.
- [ ] Checks `isPresent` and nullable point fields before reading geometry.
- [ ] Does not use `0`, the previous coordinate, or a made-up coordinate to
      replace a missing point; recognises the explicitly sourced measured
      pose-wrist substitution as the only current exception.
- [ ] Uses `normalisedCoordinates` and the documented positive-down `y`
      convention for body-relative segmentation geometry.
- [ ] Checks `canNormalise`; does not rely on `coordinateSpace` alone.
- [ ] Handles null first-frame/recovery velocity and acceleration.
- [ ] Treats `trackingIssues` as an unordered set of diagnostics.
- [ ] Preserves both hands when handedness is uncertain or duplicated.
- [ ] Does not treat image/world `z` as metric camera depth unless a separately
      agreed upstream unit contract is added.
- [ ] Owns utterance hysteresis, buffering, start/end decisions, and boundary
      events rather than expecting normalisation to provide them.
- [ ] Emits the PLN-defined `FeatureWindow` plus utterance-boundary event for
      the classifier, once that shared Dart contract is available.
- [ ] Makes no backend call and sends no raw landmark/camera payload merely to
      perform segmentation.

## 13. Open Issues / Contract Gaps

1. **`LandmarkFrame` versus `FeatureWindow` ownership.** PLN section 3.4
   assigns normalised coordinates, velocity, and acceleration to
   `FeatureWindow`, while PLN T2.1 says the segmenter consumes
   `LandmarkFrame`. The current Dart implementation follows the agreed
   frontend pipeline by carrying derived values on `LandmarkFrame`. William's
   frozen-contract work must ratify this internal extension or define an
   adapter.
2. **No consumer implementation is present yet.** At the time of this draft,
   `origin/frontend_segment_classify` points to the repository baseline and
   contains no Flutter segmentation interface, model, or delivery adapter to
   compare. The service currently exposes only a synchronous method, so the
   caller-to-consumer wiring also remains to be agreed. This is why the status
   is Draft.
3. **The shared Python contract is different.** The current
   `origin/front_back_contract` Python `LandmarkFrame` is a compact backend
   schema with `seq`, `capture_ms`, fixed tuples, confidence-zero missing
   points, and no Dart tracking/normalisation fields. It is not directly
   compatible with this internal frontend handoff. The two types must not be
   treated as interchangeable without an agreed mapping.
4. **Missing-point interpolation conflict.** PLN T1.5 mentions interpolation,
   but the current implementation and explicit producer requirement forbid
   fabricating missing landmarks. Current non-wrist output leaves them null;
   the only exception is the explicitly sourced, measured pose-wrist
   substitution. If
   interpolation is later approved, it needs explicit provenance and a
   contract revision.
5. **Filter implementation.** PLN cites a zero-phase fourth-order Butterworth
   filter as a reference. A live zero-phase filter requires future samples;
   the current producer uses a causal first-order `6 Hz` low-pass filter. This
   is implementation-defined and visible in velocity/acceleration values.
6. **Unfrozen numeric policies.** The PLN does not fix the `0.5` confidence and
   quality gates, `0.6/0.4` handedness thresholds, `0.0001` minimum shoulder
   scale, `250 ms` temporal reset, `500 ms` stale-anchor lifetime, `15`-frame
   track expiry, or `0.35` hand-match distance. They are current defaults, not
   permanent consumer constants. Esther should consume the emitted metadata
   rather than duplicate these calculations.
7. **No maximum scale or teleport policy.** The current producer accepts every
   finite shoulder scale at or above the minimum and does not reject sudden
   landmark jumps. The PLN does not settle these policies.
8. **No output schema version in Dart.** `LandmarkFrame.toJson()` has no
   contract version. A frozen cross-branch interface should add versioning
   through William's contract process rather than an isolated producer edit.
9. **Array budgets are not enforced.** The current Dart model does not validate
   33 pose slots, 21 points per hand, the maximum hand count, or the curated
   face subset. Esther must code defensively until the shared contract freezes
   those layouts.
10. **Input orientation and world units.** Normalisation preserves upstream
    image orientation and world scale. Mirroring/canonical camera orientation
    and the exact world-coordinate unit are not declared by the current Dart
    contract.
11. **No mandated degraded/absent segmentation policy.** The producer reports
    state and issues, but the PLN leaves the consumer's buffer/pause/discard
    decision to the segmenter design.
12. **No Dart `FeatureWindow` or boundary-event type is available on either
    frontend branch yet.** Their exact fields, serialization, and segmenter-arm
    enum remain shared-contract work; this document does not invent them.
13. **The object mixes coordinate spaces.** Although `coordinateSpace` is
    `bodyNormalised`, every point still exposes raw `imageCoordinates`, and
    anchor metadata also remains in image space. ARC says downstream modules
    should see signing-space data. Esther should consume the explicitly named
    normalised fields and treat the retained raw fields as diagnostic until the
    team decides whether a stricter view/DTO is required.
14. **Curated landmark ownership is unresolved.** The PLN/ARC expects a
    curated pose/face budget, but the current producer preserves every input
    slot and does not enforce 33 pose, 21-per-hand, or selected-face layouts.
    The shared contract must decide whether normalisation or downstream feature
    assembly performs curation.
15. **Derived arithmetic is not post-validated.** Raw coordinates are checked
    for finiteness before use, but the current implementation does not reject
    overflow or non-finite velocity/acceleration produced from extreme yet
    finite inputs. Normal MediaPipe-scale inputs are expected; a hard output
    validation policy remains to be agreed.
16. **Input numeric ranges are debug-asserted only.** Confidence, handedness
    score, and handedness running average are intended to be in `[0, 1]`, but
    Dart constructor assertions do not provide release-mode validation. The
    shared contract must decide where malformed upstream values are rejected.
17. **World-field survival into `FeatureWindow` is unresolved.** The PLN
    requires per-hand image and world representations at the frontend handoff,
    while the future `FeatureWindow` schema is not available. Until that mapping
    is frozen, Esther should preserve the input world and canonical-world
    fields rather than silently dropping or interpreting their units.

## 14. Versioning

| Item | Value |
|---|---|
| Contract name | Normalisation → Segmentation Contract |
| Version | `v0.1` |
| Producer | `frontend_state_norm` |
| Consumer | `frontend_segment_classify` |
| Last updated | 2026-09-06 |
| Status | **Draft** |

This contract can be marked Frozen only after the producer, Esther's consumer
interface, and William's shared contract agree on the same Dart shape,
including the `LandmarkFrame`/`FeatureWindow` boundary and a versioning rule.

## Source Traceability

- PLN frozen interfaces: `PLN_plan.md` §3.4 and T0.5.
- PLN tracking state: `PLN_plan.md` T1.4.
- PLN normalisation: `PLN_plan.md` T1.5.
- PLN segmentation input/output: `PLN_plan.md` T2.1; segmentation behaviour is
  further assigned to T2.2/T2.3.
- Current Dart model:
  `appTesting/lib/models/landmark_frame.dart`.
- Current producer implementation:
  `appTesting/lib/services/tracking_state_normalisation_service.dart`.
- Consumer branch inspected read-only:
  `origin/frontend_segment_classify` at `9d9cf2e`.
- Shared-contract branch inspected read-only:
  `origin/front_back_contract` at `71e9d7a`.
- Executable boundary examples:
  `appTesting/test/fixtures/landmark_frame_fixtures.dart`,
  `appTesting/test/tracking_state_test.dart`, and
  `appTesting/test/normalization_test.dart`.
