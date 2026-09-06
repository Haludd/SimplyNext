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

## Hand tracking and sign analysis

Chrome uses MediaPipe Hand Landmarker through `web/hand_tracking.js`. It requests camera permission, tracks up to two hands, and emits 21 points per hand: normalized `x/y`, relative `z`, handedness, confidence, and world-landmark values when available. MediaPipe Pose Landmarker supplies the left and right shoulder points. The preview is mirrored like a selfie camera, and the skeleton overlay applies the same flip so it stays aligned with the displayed hand; the API keeps the original unmirrored coordinates. `HandPoseNormalizer` converts those points into the shared `LandmarkFrame` contract. The frame contains coordinate groups, point confidence, subject tracking, and optional face-expression data for the next processing stage.

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
  → handoff to the next processing stage
```

### Capture boundaries and handoff

Tracking and camera detection run continuously after the camera starts. They
do not automatically decide that a word or sentence has begun, because a
pause can occur inside a sign or between signs. The reliable first version
uses an explicit boundary:

1. Press **Start utterance**. The frontend clears its utterance buffer and
   starts storing new frames.
2. Sign one word or sentence. Every accepted frame is stored as one
   `LandmarkFrame` while the live preview continues.
3. Press **Analyse utterance** when the utterance is complete. The frontend
   also has an automatic safety boundary: after movement has been observed,
   a visible, locked subject whose hands remain still for about one second is
   automatically finished. The manual button remains available because a
   still hand position can be meaningful in sign language.
4. The frontend stops storing frames and exposes the completed
   `List<LandmarkFrame>` as `AppController.lastUtteranceFrames`.

Frames received before Start or after Analyse are still available for the
live preview, but are not included in that utterance. The next stage should
consume `lastUtteranceFrames` (or the list returned by
`TrackingService.finishUtterance()`) and then use `LandmarkFrame.toJson()` for
serialization. `AppController.lastUtteranceJson` is also available as a
convenience view. There is no WebSocket in this capture handoff and this
change does not require editing the backend folder.

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

## Sending tracking data to the backend

`SignSequenceApiClient` sends a sequence to:

```text
POST {SIGNBRIDGE_API_URL}/v1/sign-sequences/analyze
Content-Type: application/json
```

Start the frontend with an API base URL:

```bash
flutter run -d chrome \
  --dart-define=SIGNBRIDGE_API_URL=https://api.example.com
```

For local backend development, the repository includes a dependency-free
Python service. Start it from the repository root with `python3 backend/run.py`,
then use `--dart-define=SIGNBRIDGE_API_URL=http://127.0.0.1:8000` when launching
Chrome. The service validates and stores the exact sequence contract and
returns a conservative heuristic candidate until a trained classifier is
plugged in. See `backend/README.md` for the endpoint and test commands.

The app can optionally post the completed sequence if a later integration
enables `SIGNBRIDGE_ENABLE_BACKEND`; this is separate from capture and is not
needed for the `appTesting` handoff. Selecting **Analyse utterance** creates
the payload below from the completed LandmarkFrame list:

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

The same frame can include `face_expression`. Chrome uses the local combined
endpoint for seven HSEmotion/DeepFace emotion scores—angry, disgust, fear,
happy, sad, surprise, and neutral. The backend receives these fields automatically because
`SignSequencePayload` serializes each `LandmarkFrame` before
`SignSequenceApiClient` posts it.

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
  → POST /v1/sign-sequences/analyze
```

DeepFace's output is a generic facial-expression estimate, not a declaration
of a person's emotion or intent. A sign-language model should use it as a
non-manual feature alongside hand and body motion, with consent and an
appropriate model for the selected language.

The backend should validate the schema, store the sequence and model version, resample or normalize the frames, run a language-specific temporal classifier, and return a response such as:

```json
{
  "status": "confident",
  "gesture_label": "water",
  "caption": "water",
  "confidence": 0.91,
  "gloss_trace": ["WATER"],
  "detail": "Sequence classified by asl-model-2026-01."
}
```

For uncertain output, return `status: "needs_review"` or `status: "unknown"` with top candidates rather than inventing a sentence. The Flutter controller falls back to its local feature result when the API is not configured or is unavailable.

When `SIGNBRIDGE_API_URL` is not supplied, **Analyse utterance** uses an offline
simulation. It builds the same `SignSequencePayload`, waits briefly to mimic a
service call, runs the local feature readout, and returns a clearly labelled
`simulated` result. No camera frame or coordinate is sent over the network.
Once the backend is ready, supplying `SIGNBRIDGE_API_URL` automatically swaps
in the real HTTP client without changing the capture flow.

For browser testing, serve the API over HTTPS (or localhost), allow the Flutter dev origin in CORS, and never upload raw video unless the user has explicitly opted into it. DeepFace requires a still image, so the optional local service receives compressed snapshots; it does not store them. Store landmarks and the consent/session ID instead of camera frames by default.

`AlignmentEvaluator` remains independent of the UI. It receives normalized shoulder points, computes midpoint, width, horizontal error, and vertical error, and returns feedback such as “Move back” or “Position looks good ✓”.
