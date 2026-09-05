# SignBridge Flutter frontend

SignBridge is an uncertainty-aware sign-language communication prototype. The Flutter frontend contains the product flow described in the repository architecture:

1. First launch opens one-time camera calibration (`STEP 1 OF 3` → `STEP 3 OF 3`).
2. Successful calibration is stored locally and routes to Live Translator.
3. Live Translator shows the camera, reusable normalized landmark overlay, large buffered captions, tracking confidence, and view modes (Raw / Mesh / Clean).
4. Unknown signs have a separate “Sign not recognised” state that opens a five-valid-sample personal vocabulary flow.
5. Settings exposes real camera/microphone permission and device controls, privacy switches, and camera recalibration. There is no obsolete conversation screen or saved-transcripts settings panel.

## Run

Install Flutter, then from this directory run:

```bash
flutter pub get
flutter run
```

The project includes generated Android, iOS, and web platform scaffolding. Verify the setup with `flutter analyze`, `flutter test`, or `flutter run`.

The generated platform files already include the permission descriptions required by the `camera` and `permission_handler` packages: `NSCameraUsageDescription` and `NSMicrophoneUsageDescription` in iOS `Info.plist`, plus camera and record-audio permissions in Android `AndroidManifest.xml`.

## Frontend → backend boundary

The architecture document recommends keeping the 30 FPS perception loop at the edge. Flutter owns the camera and UI. A MediaPipe Tasks integration (via a Flutter plugin or platform channel) should emit normalized landmark frames into the shared tracking interface in `lib/services/tracking_service.dart`. The typed HTTP seam is in `lib/services/api_client.dart`.

## Tracking state and normalisation

`lib/models/landmark_frame.dart` is the provisional Dart form of the PLN
`LandmarkFrame` boundary. The same type enters tracking state, leaves
normalisation, and can be consumed by the future segmenter. A point retains
its measured MediaPipe image coordinate and confidence alongside optional
body-normalised coordinates, hand-world coordinates, velocity, and
acceleration. Null array entries represent landmarks that were not observed;
missing data is never encoded as a zero coordinate.

`TrackingStateNormalisationService` in
`lib/services/tracking_state_normalisation_service.dart` exposes synchronous
`process` and `reset` methods. The upstream capture owner calls `process` for
its newest frame and can drop stale frames instead of building a queue. The
service has no widget, camera, network, segmentation, or classifier dependency.

The PLN leaves several live-processing policies open. This implementation
records the following configurable defaults:

- confidence gate: `0.5`; a rejected point keeps its measurement and score but
  has no normalised coordinate or derivative;
- stable hand identity: nearest valid wrist/palm observation, with tracks
  expiring after 15 missed frames; matching uses a global minimum for the two
  hands and a handedness-mismatch cost to survive hand crossings;
- handedness: lifetime mean of right-hand probability with a `0.6` decision
  threshold; duplicate labels retain both hands and mark uncertainty;
- body frame: running shoulder midpoint and shoulder width with a 250 ms time
  constant, retained for at most 500 ms when shoulders disappear;
- motion: timestamp-based body-relative units/second and units/second squared;
  initial and post-gap derivatives are null, and histories reset after 250 ms,
  a subject change, or a non-increasing timestamp;
- smoothing: causal 6 Hz low-pass for hands/body and no face smoothing;
- tracking quality: completeness over pose shoulders/elbows/wrists/hips and
  the 21 expected points of each present hand, so sparse arrays cannot report
  full quality;
- orientation: MediaPipe's top-left y-axis is preserved; image z is not treated
  as metric depth; available hand-world points get a separate palm-canonical
  representation.

No missing point is interpolated. The sole correction copies an actually
observed, above-gate pose wrist when the corresponding hand wrist failed and
marks `LandmarkSource.poseWristSubstitution`. Detector rate-limiting must be
connected at the upstream MediaPipe invocation boundary by `frontend_track`;
this post-MediaPipe service deliberately does not imitate that control.

The frame pipeline should be:

```text
Flutter camera
  → subject tracker
  → MediaPipe Tasks landmarks
  → body-relative normalizer
  → geometry / hysteresis segmenter
  → small closed-vocabulary classifier
  → compact utterance JSON over HTTPS/WebSocket
  → Python API / assembler + critic
  → caption + TTS response
```

Do not send raw camera frames or 543 landmarks to Bedrock. At an utterance boundary, the Flutter client should send a small typed payload such as:

```json
{
  "session_id": "session-123",
  "utterance_id": "utt-008",
  "language": "sgsl",
  "started_at": "2026-09-04T08:14:02Z",
  "ended_at": "2026-09-04T08:14:03Z",
  "hypotheses": [
    {"gloss": "WATER", "confidence": 0.96},
    {"gloss": "PLEASE", "confidence": 0.91}
  ],
  "features": {
    "shoulder_width": 0.22,
    "hands_visible": true,
    "mean_confidence": 0.94,
    "frame_count": 36
  }
}
```

The Python backend returns a typed result, for example:

```json
{
  "utterance_id": "utt-008",
  "status": "confident",
  "caption": "I would like some water, please.",
  "tts_text": "I would like some water, please.",
  "gloss_trace": ["WATER", "PLEASE"],
  "confidence": 0.91
}
```

When the critic cannot support a sentence, it should return a repair action instead of a guessed caption. The Flutter UI can map that response to “Please repeat”, fingerspelling, top-k choices, or “Sign not recognised”. The `AppController.setUnregisteredSign` method is the frontend seam for that response.

`AlignmentEvaluator` is independent of the UI. It receives normalized `leftShoulder` and `rightShoulder` points, computes midpoint, width, horizontal error, and vertical error with configurable tolerances, and returns precise feedback such as “Move back” or “Position looks good ✓”. The same `LandmarkFrame` contract can later receive the curated hands, upper-body pose, and face subset required by the repository architecture.
