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

Chrome uses MediaPipe Hand Landmarker through `web/hand_tracking.js`. It requests camera permission, tracks up to two hands, and emits 21 points per hand: normalized `x/y`, relative `z`, handedness, confidence, and world-landmark values when available. MediaPipe Pose Landmarker supplies the left and right shoulder points. The preview is mirrored like a selfie camera, and the skeleton overlay applies the same flip so it stays aligned with the displayed hand; the API keeps the original unmirrored coordinates. `HandPoseNormalizer` converts those points into the shared `LandmarkFrame` contract and derives hand openness, movement speed, acceleration, direction, and the dominant hand.

The overlay is a 3D-style skeleton projection. It is not pretending that a webcam can recover precise metric depth: `z` is relative depth from the hand model, projected onto the 2D camera view. This is the same compact representation that can be used by a later sequence classifier. Native Apple builds can use Vision's `VNDetectHumanHandPoseRequest` behind the same `TrackingService` interface.

The current local analyzer intentionally reports a useful feature readout (`open hand`, `closed hand`, movement, confidence) instead of claiming that four dictionary entries are a complete ASL translator. The seed lexicon is in `assets/sign_lexicon.json`. It stores the ASL labels and Handspeak reference links for `hello`, `help`, `water`, and `please`, plus the sign parameters to compare: handshape, movement, location, and handedness. Add a licensed dataset and a trained temporal model before presenting a word-level result as reliable.

Chrome also supports an optional DeepFace emotion signal. The Flutter web
camera remains in the browser for hand and shoulder tracking. About once per
second, `web/hand_tracking.js` sends a compressed still image to
`POST /v1/emotions/analyze`; the Python service follows the OpenCV + DeepFace
flow from the referenced GitHub project and returns the dominant emotion and
class scores. If the local DeepFace service is unavailable, hand and shoulder
tracking continue but the face emotion signal is left empty.

My signs uses the live tracker rather than placeholder samples. Each valid capture
stores five examples of a fixed 136-value sample: 63 wrist-centred x/y/z values
for the left hand, 63 for the right hand (zero-filled when that hand is absent),
three motion values, and seven DeepFace emotion scores. The saved entry also
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
  → local feature readout
  → POST captured sequence to the sign model API
  → validated gloss/caption + confidence
```

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

The app buffers the recent normalized frames. Selecting **Analyse sign** posts this payload:

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
      "hand_motion": {
        "average_speed": 0.08,
        "average_acceleration": 0.03,
        "average_openness": 0.74,
        "direction": "up-right",
        "dominant_hand": "right"
      },
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

The same frame can include `face_expression`. Chrome uses the local DeepFace
endpoint for seven emotion scores: angry, disgust, fear, happy, sad, surprise,
and neutral. DeepFace supplies the emotion result; it does not provide hand or
shoulder landmarks. The backend receives these fields automatically because
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
  → optional JPEG snapshot → /v1/emotions/analyze → DeepFace emotion
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

When `SIGNBRIDGE_API_URL` is not supplied, **Analyse sign** uses an offline
simulation. It builds the same `SignSequencePayload`, waits briefly to mimic a
service call, runs the local feature readout, and returns a clearly labelled
`simulated` result. No camera frame or coordinate is sent over the network.
Once the backend is ready, supplying `SIGNBRIDGE_API_URL` automatically swaps
in the real HTTP client without changing the capture flow.

For browser testing, serve the API over HTTPS (or localhost), allow the Flutter dev origin in CORS, and never upload raw video unless the user has explicitly opted into it. DeepFace requires a still image, so the optional local service receives compressed snapshots; it does not store them. Store landmarks and the consent/session ID instead of camera frames by default.

`AlignmentEvaluator` remains independent of the UI. It receives normalized shoulder points, computes midpoint, width, horizontal error, and vertical error, and returns feedback such as “Move back” or “Position looks good ✓”.
