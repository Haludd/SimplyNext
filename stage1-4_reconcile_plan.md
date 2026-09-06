# Stage 1–4 Schema Reconciliation Plan

| Item | Value |
|---|---|
| Status | Draft — plan only; no production changes are authorized by this document |
| Stage 1 | Subject tracking |
| Stage 2 | MediaPipe landmark extraction and Stage 1/2 `LandmarkFrame` production |
| Stage 3 | Tracking state |
| Stage 4 | Normalisation |
| Authoritative branch | `origin/frontend_track` |
| Authoritative commit inspected | `dacf5bc823bd069e5e82fa9baf91db550368a744` |
| Attached schema inspected | `C:\Users\Kezmond\Downloads\tracking-schema.md` |
| Stage 3/4 branch inspected | `frontend_state_norm` at `f4c8ceccc2477f3b23a8d6406d9b0210bd58e792` |
| Last reviewed | 2026-09-06 |

## 1. Purpose and Authority

This document updates the Stage 1/2 versus Stage 3/4 schema comparison and
defines a plan for making Stage 3 and Stage 4 consume Stage 1/2 data without
renaming, reinterpreting, or discarding Harold's authoritative fields.

The precedence rule for this reconciliation is:

1. Stage 1/2's executable Dart model and producer behaviour on
   `origin/frontend_track` are authoritative for runtime types and semantics.
2. Stage 1/2's `LandmarkFrame.toJson()` is authoritative for the exact JSON
   serialization currently produced by the repository.
3. The attached `tracking-schema.md` is authoritative for the intended public
   key family, but it is an illustrative JSON instance rather than a formal
   JSON Schema. Contradictions between that example and the executable Stage
   1/2 serializer require Harold's confirmation; Stage 3/4 must not silently
   choose a different meaning.
4. Any overlapping Stage 3/4 name, structure, score, or missing-data decision
   must change to match Stage 1/2.
5. Stage 3/4 may retain genuinely new derived information only as an additive,
   clearly identified downstream result. It must never overwrite or
   reinterpret an authoritative Stage 1/2 field.

This is a planning document. It does not modify either implementation.

## 2. Authoritative Stage 1/2 Handoff

The actual Stage 1/2 runtime path is:

```text
web/hand_tracking.js::dispatchFrame
  → signbridge-hand-frame browser event
  → HandTrackingFrame.fromJson
  → WebTrackingService.ingestRaw
  → HandPoseNormalizer.normalize
  → tracking_models.dart::LandmarkFrame
  → TrackingService.frames (live frames)
    or AppController.lastUtteranceFrames (captured utterance frames)
  → Stage 3 Tracking State
```

The primary next-stage boundary is an in-memory Dart object:

```dart
Stream<LandmarkFrame> get frames;
List<LandmarkFrame> get lastUtteranceFrames;
```

Stage 3 should consume that object directly. It should not serialize it to JSON
and parse it back merely to connect two services in the same Flutter process.
Stage 1/2's final `LandmarkFrame` has `toJson()` but no `fromJson()`; the parser
named `HandTrackingFrame.fromJson()` belongs to the earlier JavaScript-to-Dart
bridge.

### 2.1 Canonical runtime fields

The Stage 1/2 Dart `LandmarkFrame` contains:

| Dart field | Type | JSON representation | Stage 1/2 meaning and absence |
|---|---|---|---|
| `timestamp` | `DateTime` | `timestamp`: UTC ISO-8601 string | Required capture time, sourced from browser epoch milliseconds. |
| `trackingConfidence` | `double` | `tracking_confidence` | Final aggregate frame-quality value. Always serialized. |
| `leftShoulder` | `NormalizedPoint?` | `left_shoulder`: object or `null` | Unmirrored image-normalized shoulder point; null when unavailable. |
| `rightShoulder` | `NormalizedPoint?` | `right_shoulder`: object or `null` | Same convention as the left shoulder. |
| `leftWrist`, `rightWrist` | `NormalizedPoint?` | Not serialized | Convenience values derived from retained hands. |
| `leftHandVisible`, `rightHandVisible` | `bool` | Not serialized | Runtime convenience flags. |
| `lightingScore` | `double` | Not serialized | Legacy/runtime field, not part of the attached wire schema. |
| `featureVector` | `List<double>` | Not serialized | Stage 1/2 local flattened feature vector. It is not Stage 4 output. |
| `hands` | `List<TrackedHand>` | `hands` | Zero to two retained hand objects in the live producer. |
| `handCoordinateAnalysis` | `List<HandCoordinateAnalysis>` | `hand_coordinate_analysis` | Derived wrist-centred summaries; not the authoritative point list. |
| `faceExpression` | `FaceExpressionFeatures?` | `face_expression`: object or `null` | Optional external expression-model result. |
| `poseLandmarks` | `List<PoseLandmark>` | `landmark_worlds.pose.landmarks` | Sparse curated pose list with explicit point indices. |
| `faceUpperLandmarks` | `List<FaceLandmark>` | `landmark_worlds.face.upper` | Sparse curated 24-point upper-face list. |
| `faceMouthLandmarks` | `List<FaceLandmark>` | `landmark_worlds.face.mouth` | Sparse curated 12-point mouth list. |
| `subjectTracking` | `SubjectTracking?` | `subject_tracking`: object or `null` | Subject-lock state. No stable subject identifier is supplied. |

Every top-level key shown in the attached example is always emitted by
`LandmarkFrame.toJson()`. `left_shoulder`, `right_shoulder`,
`face_expression`, and `subject_tracking` may have a JSON `null` value.

### 2.2 Confidence fields are different signals

These values must remain distinct:

| Stage 1/2 field | Exact meaning |
|---|---|
| `trackingConfidence` / `tracking_confidence` | Final aggregate frame quality. The browser first averages point quality over each active world's expected point budget; the Dart normalizer then combines that value with the mean visibility of emitted points. |
| `TrackedHand.confidence` / `hands[].confidence` | MediaPipe handedness-category score for that hand. |
| `HandLandmark.visibility` | Per-point quality/confidence estimate, clamped to `[0,1]`. Hand values combine the hand-category score with local image detail. |
| `PoseLandmark.visibility` | Per-point quality/confidence estimate combining MediaPipe pose evidence with local image detail. |
| `PoseLandmark.presence` | Numeric per-pose-point signal. The current producer sets it to the same custom point-confidence value, but it remains a point scalar rather than a group Boolean. |
| `FaceLandmark.visibility` | Per-point quality estimate combining a fixed `0.75` baseline with local image detail. It is not a face-detector confidence supplied by MediaPipe. |
| `FingerTrackingStatus.confidence` | Rolling per-finger quality average over at most eight evidence frames. |
| `FaceExpressionFeatures.confidence` | Confidence from the optional face-expression model. |

Stage 3 must not replace one of these values with another merely because all
of them are numbers in approximately the same range.

### 2.3 Coordinate conventions

- Hand, pose, face, and shoulder `x/y` values are MediaPipe normalized image
  coordinates from the original, unmirrored camera stream.
- The preview may be mirrored, but the API data is not.
- `x` increases right and `y` increases downward from the top-left.
- Image `z` is model-relative and is not metric camera depth.
- `worldX/worldY/worldZ` are optional MediaPipe hand-world values. Their exact
  origin and unit are not frozen by this contract; Stage 3/4 must preserve
  them and must not use them as room/camera position.
- `handCoordinateAnalysis.coordinateSpace` is either
  `world_wrist_centered` when every hand point has a complete world triple, or
  `image_normalized_wrist_centered` when the analysis falls back to image
  coordinates. It does not describe the coordinate space of the whole frame.

### 2.4 Authoritative absence rules

| Data | Stage 1/2 absence representation |
|---|---|
| Entire hand | The hand is omitted from top-level `hands`. The fixed left/right serialization under `landmark_worlds` remains present with confidence `0`, an empty status map, and an empty landmark list. |
| Point inside an accepted hand | The live producer keeps exactly 21 non-null list positions. An unusable point is `x=0, y=0, z=0, visibility=0`; optional world keys are omitted. |
| Real point at `(0,0)` | Valid when `visibility > 0`; zero coordinates alone never mean absence. |
| Pose point | Missing curated points are omitted from the sparse list. |
| Shoulder | The relevant top-level shoulder is `null`, and its curated pose point is omitted. |
| Face point | Missing curated points are omitted; upper/mouth lists may be empty. |
| Face expression | `faceExpression == null` and JSON `face_expression: null`. |
| Subject centre | `centerX/centerY == null`; JSON keys are omitted. |
| Subject before lock | `locked == false`. `visible` may default to true after JavaScript-to-Dart parsing, so `visible` alone is not evidence of a usable locked subject. |
| Previously locked subject currently lost | `locked == true`, `visible == false`, centres absent, area `0`, and `missingFrames > 0`. |

The positive subject condition is `subjectTracking.locked &&
subjectTracking.visible`, followed by normal per-point quality checks.

## 3. Corrected Stage 1/2 → Stage 3/4 Comparison

The earlier comparison treated several Stage 1/2 values as unclear because
the attached example contains no definitions. The repository resolves those
semantics. The table below uses the executable Stage 1/2 implementation as
the authority.

| Stage 1/2 variable | Current Stage 3/4 variable | Match status | Type match? | Semantic match? | Corrected decision |
|---|---|---|---|---|---|
| `timestamp` (`DateTime`; JSON `timestamp`) | `timestamp` (`DateTime`; JSON `capture_timestamp`) | EXACT MATCH in memory; JSON name differs | Yes in memory | Yes | Keep Harold's Dart field and JSON name `timestamp`. |
| `trackingConfidence` | `trackingQuality` / `trackingConfidence` getter | SEMANTIC DIFFERENCE | Both `double` | No | Preserve Harold's value and formula. Do not overwrite it with Stage 3's pose/hand-only calculation. |
| `leftShoulder` | `pose.pointAt(11)` exposed through a getter | TYPE/STRUCTURE DIFFERENCE | `NormalizedPoint?` versus `LandmarkPoint?` | Yes | Use Harold's top-level `leftShoulder` as the Stage 4 anchor source; verify the pose duplicate is consistent. |
| `rightShoulder` | `pose.pointAt(12)` exposed through a getter | TYPE/STRUCTURE DIFFERENCE | Different point classes | Yes | Same decision as left shoulder. |
| `hands` | `hands` | TYPE/STRUCTURE DIFFERENCE | `List<TrackedHand>` versus `List<HandLandmarkGroup>` | Yes at group level | Adopt `List<TrackedHand>`. |
| `TrackedHand.handedness` | `rawHandedness`; current stable output is also called `handedness` | NAME/SEMANTIC COLLISION | Enum labels align, ownership differs | Harold field is the raw per-frame observation | Keep `handedness` unchanged. Give Stage 3's stable result a different derived name. |
| `TrackedHand.confidence` | `handednessScore` | NAME DIFFERENCE ONLY | Both `double` | Yes | Adopt Harold's name `confidence`; interpret only as handedness confidence. |
| `TrackedHand.boundingBox` | None | STAGE 1/2 ONLY | N/A | N/A | Preserve losslessly even though Stage 3 does not use it. Live producer currently leaves it empty and its ordering is not frozen. |
| `TrackedHand.fingerStatus` | None | STAGE 1/2 ONLY | N/A | N/A | Preserve all entries; do not recompute or discard them. |
| `TrackedHand.landmarks` | `HandLandmarkGroup.landmarks` | TYPE/STRUCTURE DIFFERENCE | Non-null fixed positions versus nullable point objects | Same anatomical points | Adopt Harold's list and absence convention. |
| Hand landmark list position | `LandmarkPoint.index` | TYPE/STRUCTURE DIFFERENCE | Implicit integer position versus explicit field | Yes | For top-level hand points, use list position `0..20`; stop requiring Harold to send `index`. |
| `HandLandmark.x/y/z` | `LandmarkPoint.imageCoordinates.x/y/z` | TYPE/STRUCTURE DIFFERENCE | Flat fields versus nested object | Yes | Read Harold's direct fields; do not rename or move the raw source fields. |
| `HandLandmark.worldX/Y/Z` | `worldCoordinates.x/y/z` | TYPE/STRUCTURE DIFFERENCE | Independently nullable fields versus nullable nested object | Yes | Preserve independent optional fields; require a complete finite triple only for a derived world operation. |
| `HandLandmark.visibility` | `LandmarkPoint.confidence` | NAME DIFFERENCE ONLY | Both `double` | Yes | Adopt `visibility`; it is Harold's per-point confidence signal. |
| Hand missing point `(0,0,0), visibility=0` | Nullable landmark slot | SEMANTIC/STRUCTURE DIFFERENCE | Sentinel object versus `null` | Both represent unavailable evidence | Preserve Harold's object publicly; private Stage 3 logic must gate on visibility before reading coordinates. |
| `handCoordinateAnalysis` | `canonicalWorldCoordinates` or frame `coordinateSpace` | SEMANTIC DIFFERENCE | Summary records versus per-point/whole-frame fields | No | Preserve the Stage 1/2 summary. Do not use it as raw points or relabel it as Stage 4 canonical output. |
| `handCoordinateAnalysis[].handedness` | Stable/raw hand labels | PARTIAL MATCH | Same enum family | Partial | Preserve as the label attached to Harold's summary; do not use it as a hand-track ID. |
| `handCoordinateAnalysis[].coordinateSpace` | `LandmarkCoordinateSpace` | SEMANTIC DIFFERENCE | String versus enum | No | Keep the per-analysis string and its two authoritative values. |
| `jointCount`, centroid, bounds, `depthRange`, `span` | None | STAGE 1/2 ONLY | N/A | N/A | Preserve as derived Stage 1/2 summary fields. |
| `faceExpression` | Current combined `face` landmark group | TYPE/SEMANTIC DIFFERENCE | Expression object versus geometry group | Partial | Preserve expression confidence, label, source, scores, and landmarks separately. |
| `faceExpression.source` | `LandmarkSource` | SEMANTIC DIFFERENCE | String versus enum | No | Expression-model provenance is not point provenance. |
| `poseLandmarks` | `pose.landmarks` | TYPE/STRUCTURE DIFFERENCE | Sparse `List<PoseLandmark>` versus nullable slot array | Yes | Adopt Harold's sparse list and locate points by `PoseLandmark.index`, never list offset. |
| `PoseLandmark.index` | `LandmarkPoint.index` | NAME/TYPE MATCH inside different structures | Both `int` | Yes | Preserve Harold's explicit pose index. |
| `PoseLandmark.name` | None | STAGE 1/2 ONLY | N/A | N/A | Preserve it. |
| `PoseLandmark.x/y/z` | `imageCoordinates.x/y/z` | TYPE/STRUCTURE DIFFERENCE | Flat versus nested | Yes | Adopt Harold's flat raw fields. |
| `PoseLandmark.visibility` | `LandmarkPoint.confidence` | NAME DIFFERENCE ONLY | Both `double` | Yes | Gate pose points using Harold's visibility. |
| `PoseLandmark.presence` | Group `isPresent` | SEMANTIC DIFFERENCE | `double?` versus `bool` | No | Preserve it as a point score; do not convert it into a group flag. |
| `faceUpperLandmarks` | Part of combined `face.landmarks` | TYPE/STRUCTURE DIFFERENCE | Sparse curated list versus one nullable/index-addressable list; current fixtures use 468 slots | Yes | Preserve the separate upper-face list and explicit indices. |
| `faceMouthLandmarks` | Part of combined `face.landmarks` | TYPE/STRUCTURE DIFFERENCE | Sparse curated list versus one nullable/index-addressable list; current fixtures use 468 slots | Yes | Preserve the separate mouth list and explicit indices. |
| `FaceLandmark.visibility` | `LandmarkPoint.confidence` | NAME DIFFERENCE ONLY | Both `double` | Yes | Use Harold's visibility for confidence gating. |
| `subjectTracking` | `subjectId` and implicit reset rules | SEMANTIC DIFFERENCE | State object versus nullable string | No | Adopt Harold's lock/visibility state. Do not fabricate a subject ID. |
| `subjectTracking.locked` | None | STAGE 1/2 ONLY | N/A | N/A | Use with `visible` to decide whether a locked signer is currently available. |
| `subjectTracking.visible` | Group `isPresent` | SEMANTIC DIFFERENCE | Whole-subject bool versus per-group bool | No | Do not treat it as pose/hand/face presence. |
| `centerX/centerY`, `area`, `missingFrames` | None | STAGE 1/2 ONLY | N/A | N/A | Preserve; use only according to subject-tracking semantics. |
| `landmark_worlds.left_hand/right_hand` | Current hand groups | SERIALIZATION PROJECTION | JSON-only duplicate versus runtime list | Duplicate of canonical hand data | Do not create a second in-memory source. Top-level `hands` is authoritative. |
| `landmark_worlds.pose.landmarks` | Current pose group | SERIALIZATION PROJECTION | JSON wrapper versus runtime sparse list | Duplicate of `poseLandmarks` | Consume runtime `poseLandmarks`; preserve serializer behaviour. |
| `landmark_worlds.face.upper/mouth` | Current face group | SERIALIZATION PROJECTION | JSON wrapper versus runtime separate lists | Duplicates face geometry | Consume the two runtime lists. |
| `landmark_worlds.face.emotion` | None/current face geometry | SERIALIZATION PROJECTION | JSON value | Duplicate of `faceExpression` | Preserve duplicate serialization; never treat it as a second observation. |
| Runtime `leftWrist/rightWrist` | Current wrist getters | PARTIAL MATCH | Similar nullable point view | Yes | Preserve Harold's runtime conveniences; do not make them a new wire requirement. |
| Runtime `leftHandVisible/rightHandVisible` | Current visibility getters | PARTIAL MATCH | Both Boolean | Similar | Preserve but determine usable evidence from actual hand/point quality. |
| Runtime `lightingScore` | `lightingScore` | EXACT RUNTIME MATCH, NOT WIRE CONTRACT | Yes | Yes | Preserve but keep outside the Stage 3/4 public wire contract. |
| Runtime `featureVector` | `featureVector` | EXACT RUNTIME NAME, SEMANTIC RISK | Yes | Stage 1/2 local feature vector only | Preserve but do not consume as Stage 4 output or add temporal features into it. |
| No Stage 1/2 field | `frameIndex` | STAGE 3/4 ONLY | N/A | N/A | Stop requiring it as upstream input. If an internal sequence is needed, derive and label it as Stage 3 state. |
| No Stage 1/2 field | `subjectId` | STAGE 3/4 ONLY | N/A | N/A | Remove as an upstream requirement; do not synthesize identity from lock state. |
| No Stage 1/2 field | Frame `coordinateSpace` | STAGE 3/4 ONLY | N/A | N/A | Remove from upstream requirements; Stage 1/2 coordinate meaning is defined by its concrete fields. |
| No Stage 1/2 field | Group `isPresent` | STAGE 3/4 ONLY | N/A | N/A | Replace with Harold's structural absence, nullable objects, subject state, and visibility rules. |
| No Stage 1/2 field | Upstream `trackId` | STAGE 3/4 ONLY | N/A | N/A | Treat any stable ID as Stage 3-derived and tracking-epoch scoped. |
| No Stage 1/2 field | `handednessUncertain` | STAGE 3/4 ONLY | N/A | N/A | It may remain a derived result but cannot be required from Harold. |
| No Stage 1/2 field | `LandmarkSource` | STAGE 3/4 ONLY | N/A | N/A | Do not require per-point source metadata from Harold. Provenance for a later measured wrist substitution must be Stage 3-derived. |
| No Stage 1/2 field | `trackingStatus`, `trackingIssues` | STAGE 3/4 DERIVED | N/A | New downstream concepts | Keep only as additive Stage 3 results. |
| No Stage 1/2 field | `canNormalise`, anchor origin/scale/stale | STAGE 4 DERIVED | N/A | New downstream concepts | Keep only as additive Stage 4 results. |
| No Stage 1/2 field | body-normalised coordinates, canonical world values, velocity, acceleration | STAGE 4 DERIVED | N/A | New downstream concepts | Add without overwriting Harold's raw point fields. |

## 4. Corrections to the Earlier Comparison

The repository changes the earlier report in these important ways:

1. **`visibility` is resolved.** It is Stage 1/2's per-point confidence
   estimate and replaces the current Stage 3/4 input name `confidence`.
2. **Hand `confidence` is resolved.** It is MediaPipe's handedness-category
   confidence and maps semantically to the current `handednessScore`.
3. **Image coordinates are resolved.** They are unmirrored MediaPipe
   normalized image `x/y` plus relative non-metric `z`.
4. **Hand index is resolved.** The index of a top-level hand point is its list
   position; Harold does not send a separate `index` there.
5. **Missing hand points are resolved.** An accepted hand has 21 positions;
   an unusable position has zero coordinates and `visibility == 0`.
6. **Pose/face absence is resolved.** Their curated lists are sparse, and
   missing indices are omitted instead of represented by null array slots.
7. **The direct boundary is resolved.** Stage 3 receives Harold's Dart
   `LandmarkFrame` in memory. The previous attempt to parse the attached JSON
   with Stage 3's incompatible `LandmarkFrame.fromJson()` is not the desired
   integration path.
8. **Frame confidence remains different.** Harold's `trackingConfidence`
   cannot be renamed to current `trackingQuality`, because their formulas and
   represented evidence differ.

## 5. Stage 1/2 Internal Schema Issues Requiring Confirmation

These are inconsistencies inside the supplied Stage 1/2 sources, not reasons
for Stage 3/4 to invent its own contract:

1. The attached example has a populated top-level `face_expression` but
   `landmark_worlds.face.emotion: null`. The executable serializer writes the
   same `faceExpression` value in both places.
2. The attached top-level hand point contains `world_x/y/z`, while its
   `landmark_worlds.right_hand` duplicate omits them. The serializer includes
   the optional world values in both projections when they are present.
3. The attached top-level hand has populated `finger_status`, while its fixed
   right-hand duplicate has an empty map. The serializer duplicates the same
   status map.
4. The attachment demonstrates only `thumb` and `index`. The live producer
   emits `thumb`, `index`, `middle`, `ring`, and `pinky`.
5. The attachment demonstrates a four-value `bounding_box`; the current live
   browser producer does not calculate one, so the runtime default is an
   empty list. Its element order and units are not documented.
6. README wording describes `tracking_confidence` as the active-world
   expected-budget average. Actual Dart code further combines that browser
   value with the average visibility of emitted points. The final
   `trackingConfidence` value produced by Dart is authoritative unless Harold
   changes the implementation.

Before writing golden tests, Harold should confirm whether the attachment is
intended to permit abbreviated duplicate fields or whether it should exactly
match `LandmarkFrame.toJson()`.

## 6. Target Reconciled Architecture

### 6.1 Non-negotiable target

- There must be one public Dart type named `LandmarkFrame`.
- That type must be Harold's Stage 1/2 type from
  `appTesting/lib/models/tracking_models.dart`.
- Stage 3's public input must accept that exact Dart object without JSON
  conversion.
- Stage 3/4 must preserve every Stage 1/2 field losslessly, including fields
  it does not currently use.
- Stage 3/4 must not overwrite raw coordinates, point visibility, hand
  confidence, frame tracking confidence, expression data, subject state,
  finger status, bounding boxes, or coordinate analyses.
- Stage 3/4's duplicate public `models/landmark_frame.dart` must not remain as
  a second incompatible contract.

### 6.2 Private algorithm view

Stage 3/4 may use a private internal view to reduce rewrite risk. That view may
provide indexed lookups and nullable usable points to the existing algorithms,
but it must obey these rules:

- Its public input is Harold's `LandmarkFrame`.
- It never becomes a second exported `LandmarkFrame`.
- It treats `visibility` as confidence.
- It rejects a zero-filled hand placeholder before reading its coordinates.
- It treats `(0,0)` with positive visibility as a real observation.
- It finds hand indices by list position.
- It finds pose/face indices by their explicit `.index` fields.
- It retains separate upper-face and mouth groups.
- It retains all optional world components and never invents a missing one.
- It keeps a reference to, or losslessly reconstructs, the complete canonical
  Stage 1/2 frame.

### 6.3 Required design gate for Stage 3/4 output

Harold's current `LandmarkFrame` has no fields for stable hand identity,
tracking state/issues, a normalisation anchor, body-normalised point values,
velocity, or acceleration. Those results cannot be expressed in the unchanged
Stage 1/2 schema.

Before implementation, the team must approve one of these options:

#### Option A — additive canonical `LandmarkFrame` extension (recommended)

Keep every Harold field exactly named, typed, and interpreted. Add only
optional/defaulted Stage 3/4-owned data to the same canonical class:

- Stage 3 metadata: status, issues, derived tracking epoch/hand identity,
  stable handedness, running average/count, and uncertainty.
- Stage 4 metadata: anchor availability/origin/scale/staleness and derived
  body-normalised coordinates, velocity, acceleration, and optional canonical
  hand-world coordinates.

Use clearly namespaced or clearly derived names. In particular:

- keep Harold's `handedness` as the raw observation;
- keep Harold's hand `confidence` as handedness confidence;
- keep Harold's point `visibility` as point confidence;
- keep Harold's `trackingConfidence` unchanged;
- do not reuse `handCoordinateAnalysis`, `featureVector`, or raw `x/y/z` for a
  different Stage 4 meaning.

This option best preserves the existing plan requirement that Stage 3,
normalisation, and segmentation exchange the same `LandmarkFrame` type. It
requires an agreed additive edit to the canonical model; it must not be made
only in a duplicate Stage 3 file.

#### Option B — lossless processed-frame envelope

Keep Harold's `LandmarkFrame` structurally and value-for-value unchanged
inside a Stage 3/4-owned result containing derived metadata. This has the
cleanest ownership boundary,
but it changes the earlier architectural statement that the next handoff uses
the exact same `LandmarkFrame` type. It therefore requires an explicit shared
contract/PLN decision before use.

No production refactor should begin until Option A or Option B is approved.

## 7. Reconciliation Rules by Stage

### 7.1 Stage 3 — Tracking State

Stage 3 must be refactored to:

1. Accept Harold's canonical `LandmarkFrame` directly.
2. Use `timestamp` for temporal continuity. Do not require `frameIndex`.
3. Use service start/stop/reset as the tracking-session boundary.
4. Treat `subjectTracking.locked && subjectTracking.visible` as positive
   subject evidence; never treat `visible` alone as sufficient.
5. Preserve lock identity across a temporary `visible == false` interval, but
   clear affected point-derivative history when observations disappear.
6. Avoid claiming a stable person identifier because Harold supplies no
   `subjectId`.
7. Use top-level `leftShoulder` and `rightShoulder` for shoulder availability.
8. Validate that their values agree with pose indices 11 and 12 when both
   representations are present; diagnose disagreement instead of averaging or
   silently choosing mixed coordinates.
9. Use hand `visibility` for per-point usability.
10. Use hand `confidence` only as handedness-label confidence.
11. Preserve hand `handedness` as the current raw observation.
12. Derive any stable hand identity and stable handedness in Stage 3-owned
    metadata. The identity is scoped to one tracking epoch and is not upstream
    data.
13. Treat missing hands, zero-visibility hand positions, sparse pose points,
    and sparse face points according to Stage 1/2's rules.
14. Preserve Harold's `trackingConfidence`; do not write Stage 3's existing
    quality formula into that field.
15. Preserve bounding boxes, finger status, coordinate analysis, face
    expression, subject tracking, and all raw point/world values even when
    Stage 3 does not use them.

### 7.2 Stage 4 — Normalisation

Stage 4 must be refactored to:

1. Consume the Stage 3 result built around the canonical Stage 1/2 frame.
2. Use top-level shoulders as the running body anchor.
3. Read raw direct `x/y/z` values rather than current nested
   `imageCoordinates` fields.
4. Gate each raw point using Harold's `visibility` before normalization.
5. Never normalize a `visibility == 0` zero placeholder as a real point.
6. Never treat a genuine zero coordinate with positive visibility as absent.
7. Preserve Harold's raw image coordinates and optional world coordinates
   unchanged.
8. Preserve sparse pose indexing and separate upper-face/mouth lists.
9. Key pose/face temporal history by explicit point index.
10. Key hand point history by Stage 3-derived hand identity plus the
    landmark's position/index `0..20`; do not key it by the hand object's
    unstable position in the frame's `hands` list.
11. Require all three finite `worldX/Y/Z` values before calculating any
    derived world-space operation; do not fabricate an incomplete triple.
12. Do not normalize `handCoordinateAnalysis` again. It is already a derived
    summary and is not the authoritative landmark source.
13. Do not consume or overwrite the Stage 1/2 `featureVector`; Stage 4 must
    derive its own documented output from raw canonical fields.
14. Calculate body-normalised coordinates and temporal derivatives only in
    the approved additive output area from section 6.3.
15. Keep missing/reappearing-point and invalid-time behaviour explicit and
    finite without changing Stage 1/2's public absence representation.

## 8. Ordered Implementation Plan

### Phase 0 — Freeze the authority and approve the output shape

1. Record `dacf5bc823bd069e5e82fa9baf91db550368a744` as the Stage 1/2 baseline.
2. Ask Harold to resolve the six attachment-versus-serializer questions in
   section 5.
3. Decide whether the runtime Dart object or JSON is the integration boundary.
   The repository currently specifies the Dart object, which is recommended.
4. Approve Option A or Option B from section 6.3.
5. Freeze expected Stage 1/2 golden frames before changing Stage 3/4.

### Phase 1 — Integrate Stage 1/2 into `frontend_state_norm`

1. Merge the approved `frontend_track` commit into `frontend_state_norm`.
2. Do not modify or rewrite Harold's branch.
3. Resolve shared schema files in Stage 1/2's favour.
4. Retain Harold's model files:
   - `appTesting/lib/models/tracking_models.dart`
   - `appTesting/lib/models/hand_tracking_models.dart`
   - `appTesting/lib/models/face_tracking_models.dart`
   - `appTesting/lib/models/hand_coordinate_analysis.dart`
5. Preserve Harold's tracking producer and bridge behaviour.
6. Confirm Harold's existing tests pass before adapting Stage 3.

### Phase 2 — Establish one canonical model

1. Change Stage 3/4 imports to Harold's `tracking_models.dart` and related
   canonical model types.
2. Retire `appTesting/lib/models/landmark_frame.dart` as an independent model.
3. If a short migration window is necessary, turn it into a deprecated
   re-export only; it must not declare a second `LandmarkFrame`.
4. Remove Stage 3/4 upstream assumptions that Harold does not supply:
   `frameIndex`, `subjectId`, group `isPresent`, upstream `trackId`, nullable
   hand slots, nested raw coordinate objects, and input point provenance.
5. Add the approved additive output representation without renaming or
   reinterpreting Harold's fields.

### Phase 3 — Add a private Stage 3/4 input view

1. Build an internal adapter/view from Harold's canonical object.
2. Give existing algorithms safe indexed lookups without exporting a new
   contract type.
3. Implement the exact absence and confidence rules from sections 2.2–2.4.
4. Preserve all canonical data for lossless output.

### Phase 4 — Refactor Tracking State

1. Migrate confidence gates from current point `confidence` to Harold's
   `visibility`.
2. Migrate hand-label confidence from `handednessScore` to Harold's
   `TrackedHand.confidence`.
3. Migrate pose lookup from nullable array positions to explicit pose indices.
4. Migrate hand lookup to the 21 list positions.
5. Replace `subjectId` reset assumptions with tracking-session lifecycle,
   timestamps, and subject lock/visibility transitions.
6. Keep stable hand identity and stable handedness clearly derived.
7. Preserve `trackingConfidence` rather than replacing it.
8. Make Stage 3 tests pass before changing normalisation calculations.

### Phase 5 — Refactor Normalisation

1. Migrate the shoulder anchor to Harold's top-level shoulder fields.
2. Read raw flat image/world fields through the private view.
3. Preserve the existing body-relative formula only where it does not conflict
   with Stage 1/2's source representation.
4. Migrate history keys for sparse pose/face and positional hand indices.
5. Emit derived normalization/velocity/acceleration through the approved
   additive result.
6. Prove that all Harold fields remain value-for-value unchanged and that the
   original Stage 1/2 JSON projection remains unchanged apart from approved
   additive keys after Stage 3/4 processing.

### Phase 6 — Wire the stages without changing Harold's implementation

1. Compose Stage 3/4 after `TrackingService.frames` or at the application
   composition layer.
2. Do not insert Stage 3/4 algorithms into Harold's
   `web_tracking_service.dart`, JavaScript MediaPipe loop, or model extractor.
3. Maintain a long-lived Stage 3/4 service instance so temporal state is not
   lost between frames.
4. Keep the Stage 1/2 stream and utterance capture usable independently.
5. Do not modify the segmentation branch during this reconciliation.

### Phase 7 — Remove migration scaffolding and validate

1. Remove the old duplicate model and any temporary aliases after all imports
   use the canonical type.
2. Run Dart formatting.
3. Run Stage 1/2 regression tests unchanged.
4. Run all isolated Stage 3 and Stage 4 tests.
5. Run the full Flutter test suite.
6. Run `flutter analyze`.
7. Obtain Harold's sign-off on the direct handoff and raw-field preservation.
8. Only then freeze the downstream normalisation-to-segmentation contract.

## 9. Planned File Impact

No production files are changed by this document. A later approved
implementation is expected to affect:

| File | Planned treatment |
|---|---|
| `appTesting/lib/models/tracking_models.dart` | Keep Stage 1/2 as the canonical `LandmarkFrame`; apply only the approved additive Stage 3/4 output mechanism. |
| `appTesting/lib/models/hand_tracking_models.dart` | Keep Harold's `TrackedHand`, `HandLandmark`, pose, and subject semantics; add only approved derived extensions if Option A is selected. |
| `appTesting/lib/models/face_tracking_models.dart` | Preserve Stage 1/2 face expression and curated face types. |
| `appTesting/lib/models/hand_coordinate_analysis.dart` | Preserve as Stage 1/2-derived summary; do not repurpose it. |
| `appTesting/lib/models/landmark_frame.dart` | Retire as an independent duplicate; temporary deprecated re-export only if needed. |
| `appTesting/lib/services/tracking_state_normalisation_service.dart` | Refactor to consume canonical Stage 1/2 models and emit only approved additive results. |
| Stage 3/4 private adapter/view | New internal implementation may be introduced after design approval; it must not be a public replacement contract. |
| `appTesting/lib/services/tracking_service.dart` | Resolve merge conflicts in Stage 1/2's favour; compose Stage 3/4 outside the producer. |
| `appTesting/lib/services/web_tracking_service.dart` | Preserve Harold's producer; do not insert Stage 3/4 logic into it. |
| `appTesting/test/fixtures/landmark_frame_fixtures.dart` | Replace custom-model fixtures with canonical Stage 1/2 object fixtures. |
| `appTesting/test/tracking_state_test.dart` | Migrate to Stage 1/2 fields and absence semantics. |
| `appTesting/test/normalization_test.dart` | Migrate to canonical inputs and additive derived output. |
| `appTesting/test/tracking_state_service_test.dart` | Migrate service-level tests. |
| `appTesting/test/landmark_normalisation_service_test.dart` | Migrate normalisation tests. |
| `appTesting/test/hand_tracking_test.dart` | Retain and run Harold's regression tests unchanged. |

Files with likely merge conflicts include `app_controller.dart`, `main.dart`,
`tracking_models.dart`, `tracking_service.dart`, `api_client.dart`,
`device_access_service.dart`, `widget_test.dart`, and `web/index.html`.
Stage 1/2-owned behaviour must win first; Stage 3/4 should then be composed
around it.

## 10. Required Test Matrix

### 10.1 Contract and preservation tests

- An actual Stage 1/2 Dart `LandmarkFrame` passes directly into Stage 3 without
  JSON conversion or a second public model.
- Golden serialization matches the executable Stage 1/2 serializer.
- A separate fixture records the attached example and any Harold-approved
  abbreviation rules.
- Every canonical raw field remains unchanged after Stage 3/4.
- Optional and runtime-only values are preserved even when Stage 3/4 does not
  consume them.

### 10.2 Confidence-separation tests

- Low frame `trackingConfidence` with high individual point visibility.
- High frame `trackingConfidence` with one zero-visibility point.
- High handedness confidence with low point visibility.
- Low handedness confidence with high point visibility.
- Pose `presence` and `visibility` varied independently in a constructed Dart
  fixture.
- Finger-status confidence does not affect the point-confidence gate unless an
  explicit future policy says so.
- Face-expression confidence is preserved but not treated as point quality.

### 10.3 Missing-data tests

- No hands: empty top-level list and empty fixed-side serialization.
- One hand and two hands.
- Exactly 21 valid hand positions.
- A zero-filled, zero-visibility hand position is rejected as evidence.
- A real `(0,0)` point with positive visibility remains valid.
- Missing optional `worldX`, `worldY`, or `worldZ` prevents only the derived
  world operation, not image-space normalization.
- Sparse pose with one missing shoulder.
- Empty and partially populated upper-face/mouth lists.
- Null face expression.
- Null subject tracking.

### 10.4 Subject and temporal tests

- Pre-lock state: `locked == false`, including `visible == true` default.
- Locked and visible subject.
- Locked but temporarily invisible subject with increasing `missingFrames`.
- Recovery of the same Stage 1 subject lock.
- Explicit tracker/service restart starts a new Stage 3 tracking epoch.
- Reordered hand list and duplicate/unknown handedness.
- First frame, increasing timestamp, zero/negative delta, and excessive gap.
- No dependency on an upstream frame index.
- Missing/reappearing point clears and restarts derivatives correctly.

### 10.5 Normalisation tests

- Translation invariance using Harold's top-level shoulders.
- Scale invariance using shoulder separation.
- Missing, overlapping, and extremely separated shoulders.
- First-frame velocity and acceleration behaviour.
- Subsequent exact velocity/acceleration using timestamp deltas.
- No NaN or infinity for rejected/invalid input.
- Raw image/world coordinates remain unchanged.
- Existing `handCoordinateAnalysis` and `featureVector` remain untouched.

### 10.6 Scope and performance tests

- Tests do not call MediaPipe, camera, UI, network, backend, segmentation, or
  classification.
- Stage 1/2 tests, Stage 3 tests, Stage 4 tests, full Flutter tests, and static
  analysis all pass.
- A separate non-flaky benchmark checks that the composed service is suitable
  for the target 30 FPS pipeline; CI correctness tests should not use a brittle
  wall-clock deadline.

## 11. Acceptance Criteria

Reconciliation is complete only when:

- [ ] Harold's canonical Dart `LandmarkFrame` is the only public class with
      that name.
- [ ] Stage 3 accepts a real Stage 1/2 `LandmarkFrame` directly.
- [ ] No Stage 1/2 public field has been renamed, removed, or reinterpreted.
- [ ] `visibility` is used as point confidence.
- [ ] Hand `confidence` is used only as handedness confidence.
- [ ] Harold's `trackingConfidence` is preserved unchanged.
- [ ] Zero-confidence hand placeholders are not treated as measured points.
- [ ] Sparse pose and face lists are handled by explicit index.
- [ ] Stage 3 does not require `frameIndex`, `subjectId`, `isPresent`, or an
      upstream `trackId`.
- [ ] Subject logic distinguishes lock, current visibility, and missing-frame
      count.
- [ ] Raw image coordinates, world coordinates, finger status, bounding boxes,
      face expression, subject tracking, and coordinate summaries are
      losslessly preserved.
- [ ] Stage 3/4-derived data uses the approved additive representation.
- [ ] The duplicate Stage 3/4 `LandmarkFrame` implementation is retired.
- [ ] Harold's tests still pass unchanged.
- [ ] Stage 3 and Stage 4 isolated tests pass.
- [ ] The full test suite and `flutter analyze` pass.
- [ ] No MediaPipe, segmentation, classifier, backend, or network logic is
      implemented as part of the reconciliation.

## 12. Risks and Unresolved Decisions

| Risk or decision | Required resolution |
|---|---|
| Two incompatible classes currently use the name `LandmarkFrame`. | Stage 1/2 model must become the only public type before integration. |
| Stage 1/2 has no location for Stage 3/4 output. | Approve Option A or Option B before code changes. |
| Attached example contradicts actual duplicate serialization. | Harold must freeze whether the example is abbreviated or serializer-exact. |
| No upstream `subjectId`. | Use Stage 1 session lifecycle and subject lock state; document residual inability to prove person identity changed. |
| No upstream stable hand ID. | Keep derived identity internal/additive and scope it to a tracking epoch. |
| Hand order may change. | Match hands temporally using Stage 3-derived state without changing Harold's raw list. |
| Zero-filled missing hand points look like real zero coordinates. | Always gate on visibility before reading coordinates. |
| Top-level shoulders and pose indices 11/12 are duplicates. | Add an invariant test and diagnostic policy; do not blend inconsistent values. |
| `landmark_worlds` name suggests all values are world coordinates. | Treat hand `world_*` as optional world data, but pose/face `x/y/z` as image-normalized data. |
| Stage 1/2 already supplies a feature vector and wrist-centred analysis. | Preserve them but do not use them as substitutes for Stage 4 body normalization and temporal derivatives. |
| Current Stage 3 `copyWith` enrichment depends on its custom immutable model. | Replace it only after the additive output design is approved. |

## 13. Planned Handoff Result

After reconciliation, the intended flow is:

```text
Harold's canonical Stage 1/2 LandmarkFrame
  → Stage 3 private view (no public schema replacement)
  → derived tracking state added without altering Harold's data
  → Stage 4 body normalisation and temporal derivatives added
  → one approved processed-frame contract for segmentation
```

The invariant across the entire flow is:

> Every Stage 1/2 field remains present with its original name, type, value,
> coordinate meaning, and missing-data meaning. Stage 3/4 adds information; it
> does not rewrite Harold's contract.
