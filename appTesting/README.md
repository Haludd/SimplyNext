# SignBridge Flutter frontend

SignBridge is an uncertainty-aware sign-language communication prototype. The Flutter frontend now focuses on one live translation page:

1. The camera is opened from the **Open camera** button inside the video feed.
2. Live Translator shows the camera, landmark overlay, captions, tracking confidence, and view modes (Raw / Mesh / Clean).
3. Capture starts automatically when a usable hand is detected; the signer does not press a Start button.
4. A sustained pause, or hands leaving the frame after movement, automatically ends the utterance and prepares it for the next processing stage.

The older calibration, My signs, and Settings widgets remain in the source for
future work, but they are not part of the current single-page UI.

## Run

Install Flutter, then from this directory run:

```bash
flutter pub get
flutter run
```

The project includes generated Android, iOS, and web platform scaffolding. Verify the setup with `flutter analyze`, `flutter test`, or `flutter run`.

The generated platform files already include the permission descriptions required by the `camera` and `permission_handler` packages: `NSCameraUsageDescription` and `NSMicrophoneUsageDescription` in iOS `Info.plist`, plus camera and record-audio permissions in Android `AndroidManifest.xml`.

## Hand tracking and sign analysis

Chrome uses MediaPipe Hand Landmarker through `web/hand_tracking.js`. It requests camera permission, tracks up to two hands, and emits 21 points per hand: normalized `x/y`, relative `z`, handedness, confidence, and world-landmark values when available. MediaPipe Pose Landmarker supplies the left and right shoulder points. The preview is mirrored like a selfie camera, and the skeleton overlay applies the same flip so it stays aligned with the displayed hand; the wire format keeps the original unmirrored coordinates. `HandPoseNormalizer` converts those points into the shared `LandmarkFrame` contract. The frame contains coordinate groups, point confidence, subject tracking, and optional face-expression data for the next processing stage.

The first stable pose becomes the subject for the current camera session. The
tracker compares torso/head anchor shape and recent position, ignores other
pose candidates, and holds the original subject as hidden if detection is
temporarily lost. If two people are equally plausible, it refuses to guess
and keeps the original lock. Use the refresh icon in the video overlay to
deliberately stop the old session and choose a new first subject.

Each accepted hand also includes `finger_status` for `thumb`, `index`, `middle`, `ring`, and `pinky`. Each entry is a smoothed landmark-quality signal: `observed`, `uncertain`, or `not_visible`, with a confidence and evidence-frame count. It does not claim that a finger is anatomically missing; a hidden or occluded finger can look the same as an absent finger in a single camera frame. The existing subject lock is unchanged, so these per-finger signals still belong only to the locked signer.

Every emitted landmark's `visibility` is also used as a point-confidence estimate. For hand and face points, the browser combines the detector confidence with local image detail from a small camera patch; for pose points, it also uses MediaPipe's visibility/presence value. `processing_confidence` (and the wire-level `tracking_confidence`) is the average over the active worlds, with missing points counted as zero within their world's expected landmark budget. It is a quality score for deciding whether to trust the frame, not a probability that the point is anatomically present.

The overlay is a 3D-style skeleton projection. It is not pretending that a webcam can recover precise metric depth: `z` is relative depth from the hand model, projected onto the 2D camera view. This is the same compact representation that can be used by a later sequence classifier. Native Apple builds can use Vision's `VNDetectHumanHandPoseRequest` behind the same `TrackingService` interface.

The current local analyzer intentionally reports a useful feature readout (`open hand`, `closed hand`, movement, confidence) instead of claiming that four dictionary entries are a complete ASL translator. The seed lexicon is in `assets/sign_lexicon.json`. It stores the ASL labels and Handspeak reference links for `hello`, `help`, `water`, and `please`, plus the sign parameters to compare: handshape, movement, location, and handedness. Add a licensed dataset and a trained temporal model before presenting a word-level result as reliable.

Chrome also supports an optional facial-expression signal. The Flutter web
camera remains in the browser for hand and shoulder tracking. About once per
second, `web/hand_tracking.js` sends a compressed still image to
`POST /v1/emotions/analyze`; the Python service uses HSEmotion's EfficientNet
ONNX model and falls back to the OpenCV + DeepFace flow from the referenced
GitHub project if HSEmotion is unavailable. It returns the dominant emotion
and class scores. If the local service is unavailable, hand and shoulder
tracking continue but the face signal is left empty.

My signs uses the live tracker rather than placeholder samples. Each valid capture
stores five examples of a fixed local coordinate sample: wrist-centred x/y/z values
for the left and right hands, curated pose/face coordinates, and facial-expression
scores. The saved entry also
keeps its selected language, coordinate-space label, and face signal for audit
and later matching. One-handed signs are accepted; both hands are not required.
The My signs page includes the ASL reference cards from the seed lexicon and
keeps BSL/SgSL as separate profiles until approved, consented examples are
available.

The live pipeline is:

```text
Chrome camera
  → MediaPipe 21-point hand tracker
  → body/hand normalizer + 3D-style skeleton
  → LandmarkFrame JSON
  → local utterance buffer: List<LandmarkFrame>
  → WebSocket utterance chunks
  → next processing stage
```

### Capture boundaries and handoff

Tracking and camera detection run continuously after the camera starts. The
frontend automatically decides the boundaries using the current lightweight
pause detector:

1. When a usable hand from the locked subject appears, the frontend clears
   the utterance buffer and starts storing new frames.
2. Sign one word or sentence. Every accepted frame is stored as one
   `LandmarkFrame` while the live preview continues.
3. After movement has been observed, a visible, locked subject whose hands
   remain still for about one second is automatically finished. If hands leave
   the frame, that absence also starts the same pause timer.
4. The frontend stops storing frames and exposes the completed
   `List<LandmarkFrame>` as `AppController.lastUtteranceFrames`.

Frames received before a hand appears or after an utterance ends are still
available for the live preview, but are not included in that utterance. The next stage should
consume `lastUtteranceFrames` (or the list returned by
`TrackingService.finishUtterance()`) and then use `LandmarkFrame.toJson()` for
serialization. `AppController.lastUtteranceJson` is also available as a
convenience view. When WebSocket mode is enabled, the same completed list is
sent as bounded JSON chunks; the camera does not send individual HTTP frame
requests.

The schema deliberately stores landmarks, not a guessed translation:

```dart
final List<LandmarkFrame> utteranceFrames = <LandmarkFrame>[];
```

Each `LandmarkFrame` contains its timestamp, frame/point confidence,
left/right hand worlds (21 landmarks per detected hand), curated pose points,
curated upper-face and mouth points, handedness/finger quality, and subject
tracking information. A word or sentence is therefore a time-ordered list of
these frames. Velocity, acceleration, classifier labels, and camera images
are not part of this frontend handoff schema.

## Sending tracking data over WebSocket

The active frontend transport is `SignTrackingWebSocketClient`. It connects to:

```text
ws://127.0.0.1:8001/v1/tracking
```

Run the frontend with WebSocket mode enabled:

```bash
flutter run -d chrome \
  --dart-define=SIGNBRIDGE_ENABLE_WEBSOCKET=true \
  --dart-define=SIGNBRIDGE_WEBSOCKET_URL=ws://127.0.0.1:8001/v1/tracking
```

When the automatic pause detector finishes an utterance, the client sends this sequence:

```text
ready ← server
start →
utterance_start →
chunk → (one or more bounded groups of LandmarkFrame JSON)
utterance_end →
utterance_ended ← server
```

The current tracking server acknowledges each chunk and reports the total
number of frames received. If it also sends an `utterance_result` message, the
frontend parses that JSON into `SignAnalysisResult` and updates the caption.
Until the classifier is connected to the socket, the frontend keeps showing
its local readout after the server acknowledgement. A socket failure never
stops the camera; it shows the local readout and a WebSocket-unavailable
status instead.

Automatic utterance completion creates the payload below from the completed
LandmarkFrame list and splits its `frames` list into chunks:

```json
{
  "session_id": "session-123",
  "sequence_id": "sequence-008",
  "language": "ASL",
  "started_at": "2026-09-05T08:14:02Z",
  "ended_at": "2026-09-05T08:14:03Z",
  "frame_count": 36,
  "lexicon_version": "2026-09-seed-2",
  "frames": [
    {
      "timestamp": "2026-09-05T08:14:02.000Z",
      "tracking_confidence": 0.95,
      "hands": [
        {
          "handedness": "right",
          "confidence": 0.98,
          "landmarks": [
            {"x": 0.48, "y": 0.52, "z": -0.02, "world_x": 0.01, "world_y": -0.02, "world_z": 0.00}
          ]
        }
      ],
      "hand_coordinate_analysis": [
        {
          "handedness": "right",
          "coordinate_space": "world_wrist_centered",
          "joint_count": 21,
          "centroid": {"x": 0.02, "y": -0.04, "z": 0.01},
          "bounds": {
            "min_x": -0.08,
            "max_x": 0.11,
            "min_y": -0.18,
            "max_y": 0.03,
            "min_z": -0.04,
            "max_z": 0.02
          },
          "depth_range": 0.06,
          "span": 0.29
        }
      ]
    }
  ]
}
```

The `hands[].landmarks` array remains the source of truth: it contains all 21
landmarks and their x/y/z values. `hand_coordinate_analysis` is a derived,
wrist-centred summary for a backend model. `world_wrist_centered` is used when
MediaPipe provides world landmarks; otherwise the app labels the summary
`image_normalized_wrist_centered`. This distinction prevents the backend from
treating webcam-relative depth as absolute physical measurements.

The same frame can include `face_expression`. Chrome can still use the
optional local face-expression snapshot endpoint for seven HSEmotion/DeepFace
scores—angry, disgust, fear, happy, sad, surprise, and neutral. That optional
face signal is separate from the LandmarkFrame WebSocket handoff; the
coordinate utterance itself is not sent through HTTPS.

The requested [OpenCV + DeepFace repository](https://github.com/manish-9245/Facial-Emotion-Recognition-using-OpenCV-and-Deepface)
is not a drop-in Flutter dependency: its `emotion.py` owns an OpenCV desktop
webcam loop. The backend adapter keeps its face-cascade → RGB face crop →
`DeepFace.analyze(actions=['emotion'])` logic, but returns JSON for the Flutter
browser instead of opening an OpenCV window. It should still be treated as a
generic emotion signal, not as a declaration of a person's intent or a
complete sign-language translation.

The request path is:

```text
camera frame
  → MediaPipe hand + pose landmarkers
  → optional JPEG snapshot → /v1/emotions/analyze → HSEmotion (DeepFace fallback)
  → HandTrackingFrame
  → HandPoseNormalizer
  → LandmarkFrame.toJson()
  → SignSequencePayload.toJson()
  → WebSocket `chunk` messages
```

DeepFace's output is a generic facial-expression estimate, not a declaration
of a person's emotion or intent. A sign-language model should use it as a
non-manual feature alongside hand and body motion, with consent and an
appropriate model for the selected language.

The backend should validate the schema, store the sequence and model version, resample or normalize the frames, run a language-specific temporal classifier, and return a response such as:

```json
{
  "type": "utterance_result",
  "utterance_id": "utt-123",
  "status": "confident",
  "caption": "water, please.",
  "tts_text": "water, please.",
  "confidence": 0.91,
  "gloss_trace": ["WATER", "PLEASE"],
  "hypotheses": [],
  "model_version": "classifier-v1",
  "latency_ms": {"total": 125}
}
```

For uncertain output, return `status: "needs_review"` or `status: "unknown"` with top candidates rather than inventing a sentence. The Flutter controller falls back to its local feature result when WebSocket mode is not configured or is unavailable.

When WebSocket mode is not enabled, automatic utterance completion uses an
offline simulation. It builds the same `SignSequencePayload`, waits briefly to
mimic a service call, runs the local feature readout, and returns a clearly
labelled `simulated` result. No camera frame or coordinate is sent over the
network.

The older `SignSequenceApiClient` remains in `services/api_client.dart` only
for compatibility with existing tests and experiments; the live
`AppController` no longer uses it.

For browser testing, use `ws://` on localhost or `wss://` for a secure deployed
socket, allow the Flutter dev origin in the WebSocket server, and never upload
raw video unless the user has explicitly opted into it. DeepFace requires a
still image, so the optional local service receives compressed snapshots; it
does not store them. Store landmarks and the consent/session ID instead of
camera frames by default.

`AlignmentEvaluator` remains independent of the UI. It receives normalized shoulder points, computes midpoint, width, horizontal error, and vertical error, and returns feedback such as “Move back” or “Position looks good ✓”.
