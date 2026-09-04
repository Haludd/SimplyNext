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
