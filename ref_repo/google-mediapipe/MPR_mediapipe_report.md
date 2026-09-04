**GOOGLE MEDIAPIPE — FULL REPOSITORY REPORT**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field                   | Value                                                         |
| :---------------------- | :------------------------------------------------------------ |
| **Code**                | `MPR`                                                         |
| **Status**              | Live                                                          |
| **Last reviewed**       | 2026-08-30                                                    |
| **Source of truth for** | Analysis of the MediaPipe reference clone                     |
| **Parent**              | [`RIX_S2.1`](../../ref_index.md#21-live-documents)            |
| **Short version**       | [`MPS`](../../doc/MPS_mediapipe_synthesis.md)                 |
| **Subject**             | `RMP` — `ref_repo/google-mediapipe/mediapipe/` at `251c0cb96` |

**For the team.** The full technical analysis of the repository the pipeline is built on. The
**Hand Landmarker** task is the focus: [`MPR_S4`](#4-the-hand-landmarker-pipeline) is the
algorithm, [`MPR_S5`](#5-the-python-api-in-detail) is the API the code will actually call, and
[`MPR_S11`](#11-relevance-to-simplynext) is the port table and the trap list. MediaPipe is a very
large repository built for many purposes; [`MPR_S8`](#8-the-rest-of-the-repository-in-brief)
summarises the ~90% that is irrelevant here so that nobody spends a day reading it.

**For the assistant.** Every constant, threshold and wiring claim in
[`MPR_S4`](#4-the-hand-landmarker-pipeline) carries a `file:line` citation into the clone at the
commit named above. Re-verify before citing, because this repository moves — it took 5,617 commits
to reach this state. Nothing inside `ref_repo/google-mediapipe/mediapipe/` may be edited: it is an
unmodified third-party clone, excluded from version control. This document sits beside it and is
tracked.

</details>

---





# 1. EXECUTIVE SUMMARY
## 1.1. What This Repository Is
`ref_repo/google-mediapipe/mediapipe/` is Google's **MediaPipe** — an open-source framework for
building on-device perception pipelines, plus a catalogue of ready-made ML **Tasks** built on it.
It is developed by Google AI Edge and licensed Apache 2.0 `[S1]`. The clone is `master` at
`251c0cb96` (2026-08-28); `mediapipe/version.bzl` declares the in-development version as
**1.0.1**.

Two distinct things share the name, and confusing them is the most common error made about this
repository:

1. **The framework** · *What it is:* A C++ graph engine. Nodes are *calculators*; edges are
   timestamped *streams*. Graphs are declared in `.pbtxt` or built with a C++ builder API
   *Relevance here:* Read about it, do not build with it
2. **The Tasks API** · *What it is:* A thin, per-problem wrapper — `HandLandmarker`,
   `PoseLandmarker`, `HolisticLandmarker` — that hides the graph behind an options object and a
   `detect()` call, in Python, Java, Swift, C and JavaScript
   *Relevance here:* **This is the product SimplyNext consumes**

The distinction matters for the schedule. Building the framework requires Bazel, a C++ toolchain,
and — for the desktop examples — a source build of OpenCV. Consuming the Tasks API requires
`pip install` and a model file.




## 1.2. Why It Matters to SimplyNext
[`ARC_S7.2`](../../plan/ARC_architecture.md#72-the-four-reference-repositories-compared) names
MediaPipe as the perception layer. This repository is therefore not a reference to learn from at
leisure, like [`APR`](../apple/APR_apple_report.md) — it is a **dependency**, and the report exists
so that the team knows what it is depending on.

Mapped onto the four MVP steps in [`SCR`](../../plan/scribbles.md):

1. **1. Isolate the subject from environment noise**
   *MediaPipe:* `num_hands` caps detections; `PoseLandmarker` has `num_poses`;
   `HolisticLandmarker` is hard-limited to one person
   *Verdict:* Partially solved. Selecting *which* person is still the application's job
2. **2. Track many points on hands and face**
   *MediaPipe:* 21 landmarks per hand plus handedness; 33 pose; 468 face; all real-time on CPU
   *Verdict:* **Solved, and this is the reason to depend on it**
3. **3. Turn the points into a skeleton**
   *MediaPipe:* Normalised image-space landmarks *and* metric world landmarks — and in
   `HolisticLandmarker`, hand world landmarks **already translated into the pose coordinate
   system**
   *Verdict:* Solved further than
   [`ARC_S4.3`](../../plan/ARC_architecture.md#43-recommended-representation) assumed. See
   [`MPR_S7.1`](#71-holistic-landmarker)
4. **4. Turn skeleton motion into conversational text**
   *MediaPipe:* Not attempted. `GestureRecognizer` classifies **single-frame static** hand shapes
   and nothing more
   *Verdict:* The project's entire contribution, unchanged

The repository's own legacy documentation states the ambition plainly: hand perception *"can form
the basis for sign language understanding and hand gesture control"* `[S2]`. It provides the basis.
It provides nothing above it.




## 1.3. Summary
A 192×192 single-shot detector finds **palms**, not hands, because a palm is a near-rigid square
object and a hand is not. Each detection is expanded 2.6× and rotated upright to crop a region of
interest; a second network regresses 21 landmarks, a presence score, a handedness score and a
metric world-coordinate set from that crop. If the presence score clears the threshold the
landmarks are emitted and re-used to predict the next frame's crop directly, so the detector is
skipped entirely; if it does not clear, **nothing at all is emitted downstream** and the detector
runs again. That loop — detect once, track thereafter, gate on presence — is the whole design, and
it is why the pipeline runs at video rate on a CPU.

---





# 2. PROVENANCE, LICENCE AND REQUIREMENTS
## 2.1. Provenance
1. **Publisher**
   Google (Google AI Edge). Remote: `https://github.com/google-ai-edge/mediapipe.git`
2. **Clone state**
   `master` at `251c0cb96`, dated 2026-08-28, subject *"No public description"*
3. **History**
   5,617 commits. First commit 2019-06-16, *"Project import generated by Copybara"*
4. **Development model**
   Google-internal, exported by Copybara. Most commit messages are `Internal` or
   *"No public description"*
5. **Declared version**
   `mediapipe/version.bzl` → `MEDIAPIPE_FULL_VERSION = "1.0.1"`. Release branches present on the
   remote include `1.0.0`, `0.10.35` and `0.10.32`
6. **Language mix**
   C++ core, with Python, Java/Kotlin, Objective-C/Swift, TypeScript and Bazel build files

> **Note — an actively developed dependency, not a frozen artefact.** This is the opposite of
> [`RAP`](../apple/APR_apple_report.md), whose four-commit history makes it a teaching sample. The
> practical consequence is that **the version must be pinned**. See
> [`MPR_S2.3`](#23-python-packaging-and-the-legacy-solutions-api).




## 2.2. Licence
Apache License 2.0 (`LICENSE`, 12,549 bytes) `[S1]`. Permissive: commercial use, modification and
redistribution are allowed, subject to attribution and the notice requirements. There is no
non-commercial clause and no copyleft.

This is a material advantage over `ROP` — see
[`OPR_S2.2`](../openpose/OPR_openpose_report.md#22-licence), where the licence is a hard blocker.

> **Note — model licences are separate from the code licence.** The `.tflite` and `.task` model
> bundles are downloaded from `storage.googleapis.com/mediapipe-assets/` at runtime or build time
> and are not in the repository. ⚠ Their licence terms were not read as part of this review and
> must be checked before any redistribution of a model file inside a submission bundle.




## 2.3. Python Packaging and the Legacy Solutions API
`setup.py:371–389` declares:

```python
packages=setuptools.find_packages(
    include=['mediapipe', 'mediapipe.tasks', 'mediapipe.tasks.*'],
    exclude=['mediapipe.modules', 'mediapipe.modules.*', ...],
),
```

The directory `mediapipe/python/solutions/` still exists in the tree and still contains
`hands.py`, `holistic.py`, `pose.py` and `face_mesh.py` — the **legacy Solutions API**, the
`mp.solutions.hands.Hands(...)` interface that most tutorials, blog posts and StackOverflow
answers on the internet use. At this commit it is **not in the `include` list**, and is therefore
not packaged into the wheel built from this source.

The repository's own README states the position: support for the legacy solutions ended
**1 March 2023**; the code and prebuilt binaries continue *"on an as-is basis"* `[S3]`.

> **Warning — the single most likely source of wasted hours.** Almost every hand-tracking tutorial
> found by search uses `mp.solutions.hands`. Code written against it will import cleanly on an
> older release and fail on a 1.0-line release. The project writes against the **Tasks API**
> (`mediapipe.tasks.python.vision`) exclusively —
> [`ARC_S9`](../../plan/ARC_architecture.md#9-decisions), decision 13 — and pins the version in
> `requirements.txt`.

⚠ Which versions are published on PyPI, and under which names, was **not verified** during this
review; no network access was used. The pin must be chosen against the live index before the build
starts. What is verified is the packaging rule in this clone's `setup.py`, quoted above.




## 2.4. Runtime Requirements
`requirements.txt` at the repository root lists the wheel's runtime dependencies:

```text
absl-py~=2.3
certifi
numpy
sounddevice~=0.5
flatbuffers~=25.9
opencv-contrib-python
matplotlib
```

All are pure-pip installable. **No GPU, no CUDA and no compiler are needed to consume the Tasks
API** — the wheel ships prebuilt native binaries. That single fact is the C1 scalability argument
in [`JCR_S2.1`](../../plan/JCR_judging_criteria.md#21-c1--benefits-delivered-by-the-solution-20),
and it is what separates MediaPipe from `ROP`.

Building *from source* is a different proposition: Bazel (`.bazelversion` pins the toolchain),
`MODULE.bazel`, a 33 KB `WORKSPACE`, `setup_opencv.sh`, `setup_android_sdk_and_ndk.sh` and three
`Dockerfile`s. **The team has no reason to do this.**




## 2.5. The Python Binding Layer Changed
At this commit `mediapipe/tasks/python/vision/hand_landmarker.py` is implemented with **`ctypes`
against a C shared library**: `MpHandLandmarkerCreate`, `MpHandLandmarkerDetectImage`,
`MpHandLandmarkerDetectForVideo`, `MpHandLandmarkerDetectAsync`, `MpHandLandmarkerCloseResult`,
`MpHandLandmarkerClose` (`hand_landmarker.py:106–160`). Results cross the boundary as C structs
(`MpHandLandmarkerResultC`) and are converted by `HandLandmarkerResult.from_ctypes`
(`hand_landmarker.py:258–288`).

Historically the Tasks bindings were pybind11 over the graph. The **public Python signatures are
unchanged** by this rewrite, so it does not affect application code. It is recorded here because
it explains two things: why `close()` and the context-manager protocol matter more than usual
(`hand_landmarker.py:583–612` frees a C handle), and why stack traces from inside the task are
opaque.

> **Note — always use the context manager.** `HandLandmarker` implements `__enter__`/`__exit__`
> and a `__del__` that calls `close()`. Leaking the handle leaks native memory. Every use in the
> project's source opens it with `with`.

---





# 3. REPOSITORY MAP
## 3.1. Where the Bulk Is
The clone is 681 MB on disk, most of which is git history and platform examples. Directory sizes
under `mediapipe/`:

| Directory     | Size   | Relevance to SimplyNext                      |
| :------------ | :----- | :------------------------------------------- |
| `calculators` | 22 MB  | Indirect — the graph node library            |
| `examples`    | 20 MB  | **None** — Android/iOS/desktop apps          |
| `tasks`       | 17 MB  | **This is the one**                          |
| `util`        | 7.1 MB | Indirect                                     |
| `framework`   | 6.6 MB | Background reading                           |
| `model_maker` | 2.6 MB | Possible — see [`MPR_S7.4`](#74-model-maker) |
| `modules`     | 2.4 MB | Legacy graphs; excluded from the wheel       |
| `graphs`      | 2.4 MB | Legacy `.pbtxt` pipelines                    |
| `java`        | 1.2 MB | **None**                                     |
| `objc`        | 1.1 MB | **None**                                     |
| `gpu`         | 874 KB | **None** — CPU path only                     |
| `python`      | 572 KB | Framework bindings + legacy solutions        |
| `web`         | 189 KB | **None**                                     |

The honest summary: **about 90% of this repository is irrelevant to the project**, and
[`MPR_S8`](#8-the-rest-of-the-repository-in-brief) says why in one paragraph each rather than
pretending otherwise.




## 3.2. The Files That Matter
Everything the project depends on lives in eleven files.

1. **`mediapipe/tasks/python/vision/hand_landmarker.py`** · *Lines:* 612
   *Contents:* **Start here.** The entire public Python surface: `HandLandmarkerOptions`,
   `HandLandmarkerResult`, `HandLandmark`, `HandLandmarksConnections`, and the three detect methods
2. **`mediapipe/tasks/python/vision/core/vision_task_running_mode.py`** · *Lines:* 79
   *Contents:* The three running modes and the callback validation rule
3. **`mediapipe/tasks/cc/vision/hand_landmarker/hand_landmarker_graph.cc`** · *Lines:* ~400
   *Contents:* **The most instructive file.** The detect-then-track loop, the back edge, the
   association and deduplication wiring
4. **`mediapipe/tasks/cc/vision/hand_landmarker/hand_landmarks_detector_graph.cc`** · *Lines:* ~490
   *Contents:* The presence gate, the ROI-from-landmarks computation, the handedness labels
5. **`mediapipe/tasks/cc/vision/hand_detector/hand_detector_graph.cc`** · *Lines:* ~320
   *Contents:* The palm detector: anchors, decoding, NMS, palm → hand ROI expansion
6. **`mediapipe/tasks/cc/vision/hand_landmarker/calculators/hand_association_calculator.cc`**
   *Contents:* What `min_tracking_confidence` actually does — [`MPR_S4.5`](#45-the-misnamed-option)
7. **`hand_landmarker/calculators/hand_landmarks_deduplication_calculator.cc`**
   *Contents:* Same-hand suppression by IoU plus landmark distance, scaled by a hand-size
   baseline
8. **`mediapipe/tasks/cc/vision/hand_landmarker/hand_topology.h`** · *Lines:* 40
   *Contents:* The canonical 21-landmark naming, C++ side
9. **`mediapipe/tasks/python/vision/holistic_landmarker.py`** · *Lines:* 600
   *Contents:* The single-person face + pose + two-hands task —
    [`MPR_S7.1`](#71-holistic-landmarker)
10. **`mediapipe/tasks/cc/vision/holistic_landmarker/holistic_landmarker_graph.cc`**
    *Contents:* The output contract, including the pose-aligned hand world landmarks
11. **`docs/solutions/hands.md`** · *Lines:* ~670
    *Contents:* The published model card and design rationale. Marked **legacy**, still the best
    prose explanation of *why* the two-model design exists

---





# 4. THE HAND LANDMARKER PIPELINE
This section is the substance of the report. Every constant is cited to a line in the clone.




## 4.1. The Two-Model Design
```text
                         ┌──────────────────────────────────────┐
   full frame ──────────►│  PALM DETECTOR   192 × 192           │  runs rarely
                         │  SSD, 2016 anchors, 7 keypoints      │
                         └──────────────┬───────────────────────┘
                                        │ palm box + keypoints
                                        ▼
                         expand ×2.6, shift_y −0.5, square,
                         rotate upright                  ── the ROI
                                        │
                         ┌──────────────▼───────────────────────┐
   crop ────────────────►│  LANDMARK MODEL                      │  runs every frame
                         │  4 output tensors:                   │
                         │   ① 21 landmarks  ② presence         │
                         │   ③ handedness    ④ world landmarks  │
                         └──────────────┬───────────────────────┘
                                        │
                         GATE: presence ≥ min_hand_presence_confidence
                           below → emit NOTHING, drop the track
                           above → emit, and …
                                        │
                         ROI for next frame from the landmarks
                         expand ×2.0, shift_y −0.1, square
                                        │
                                        └──────► back edge, skip the detector
```

The rationale is stated in the repository's own documentation `[S2]`:

- A palm is a **near-rigid, roughly square** object; a hand with articulated fingers is not.
  Training a palm detector rather than a hand detector *"is significantly simpler"*, and square
  anchors *"reduce the number of anchors by a factor of 3–5"*.
- Because palms are small, **non-maximum suppression still works for two-hand self-occlusion**,
  *"like handshakes"*.
- Providing an accurately cropped, rotation-normalised hand image to the second model
  *"drastically reduces the need for data augmentation"* and lets the network *"dedicate most of
  its capacity towards coordinate prediction accuracy"*.

Reported palm-detection average precision is **95.7%**, against an **86.22%** baseline using
regular cross-entropy loss and no decoder `[S2]`.

> **Note — ⚠ the figures in `[S2]` come from a legacy documentation page** that carries a
> deprecation banner and forwards to the current Solutions site. The design description is
> unchanged and matches the code read below; the two accuracy numbers should be re-checked against
> the current model card before either appears on a slide.




## 4.2. The Palm Detector, Exactly
From `mediapipe/tasks/cc/vision/hand_detector/hand_detector_graph.cc`:

1. **Input resolution** · *Value:* 192 × 192 · *Line:* `89`
   *Note:* `set_x_scale(192.0)`; the model is fed a letterboxed square
2. **Anchor count** · *Value:* 2016 boxes · *Line:* `79`
   *Note:* `set_num_boxes(2016)`
3. **Keypoints per detection** · *Value:* 7 · *Line:* `83`
   *Note:* Used to derive the palm's rotation before cropping
4. **SSD layers** · *Value:* 4 · *Line:* `110`
   *Note:* `set_num_layers(4)`
5. **Strides** · *Value:* 8, 16, 16, 16 · *Lines:* `117–120`
   *Note:* One fine level and three coarse — small hands are handled at stride 8
6. **Anchor scale range** · *Value:* 0.1484375 → 0.75 · *Lines:* `111–112`
   *Note:* The scale span the detector is trained to cover
7. **Score threshold** · *Value:* `min_hand_detection_confidence` · *Line:* `88`
   *Note:* The Python option is wired straight through to `min_score_thresh`
8. **NMS** · *Value:* IoU 0.3, weighted · *Lines:* `97–101`
   *Note:* `INTERSECTION_OVER_UNION`, `WEIGHTED`
9. **Palm → hand ROI** · *Value:* scale 2.6 ×, shift_y −0.5, `square_long` · *Lines:* `137–140`
   *Note:* The palm box is expanded and shifted **up the hand axis** to cover the fingers

Item 9 is the number to remember. A palm box is roughly the palm; multiplying it by 2.6 and
shifting it half a box-height along the hand's own axis is what turns "I found a palm" into "here
is where the whole hand is".




## 4.3. The Landmark Model, Exactly
From `mediapipe/tasks/cc/vision/hand_landmarker/hand_landmarks_detector_graph.cc`:

1. **Output tensors** · *Value:* 4 · *Line:* `74`
   *Note:* `kModelOutputTensorSplitNum = 4` — landmarks, presence flag, handedness, world landmarks
2. **Landmark count** · *Value:* 21 · *Line:* `72`
   *Note:* `kLandmarksNum = 21`
3. **Z normalisation** · *Value:* 0.4 · *Line:* `73`
   *Note:* `kLandmarksNormalizeZ = 0.4`. The normalised `z` is scaled relative to the **crop
   width**, not to anything in the room — see [`MPR_S5.4`](#54-coordinate-spaces--four-of-them)
4. **Presence → boolean** · *Value:* `ThresholdingCalculator` · *Lines:* `314–319`
   *Note:* Threshold is the subgraph's `min_detection_confidence`, fed from the Python option
   `min_hand_presence_confidence` (`hand_landmarker.cc:121–122`)
5. **Handedness labels** · *Value:* index 0 = `Right`, index 1 = `Left` · *Lines:* `129–142`
   *Note:* Binary classification, `top_k = 1`. **The index order is counter-intuitive** and is a
   real source of bugs
6. **Landmarks → next ROI** · *Value:* scale 2.0 ×, shift_y −0.1, `square_long` · *Lines:* `144–151`
   *Note:* Tighter than the palm expansion, because landmarks locate the hand far better than a
   palm box does



### 4.3.1. The presence gate is a hard gate
The four outputs are each wrapped in `AllowIf(..., hand_presence, graph)` — landmarks
(`hand_landmarks_detector_graph.cc:331`), world landmarks (`:364`), handedness (`:352`) and the
next-frame ROI (`:384`). `AllowIf` does not emit a low-confidence packet with a low score
attached. **It emits nothing.** The downstream calculators simply receive no packet for that
timestamp.

> **Decision support.** This is Google's C++ implementation of the same rule
> [`APR_S6.3`](../apple/APR_apple_report.md#63-confidence-is-a-gate-not-a-weight) extracted from
> Apple's Swift, and the same rule [`ARC_S9`](../../plan/ARC_architecture.md#9-decisions) decision
> 8 makes a design invariant for the whole product. Two independent industrial teams reached it
> from opposite directions. That convergence is worth one line on the architecture slide.




## 4.4. The Tracking Loop
The graph's own header comment states the design (`hand_landmarker_graph.cc:139–145`):

> *"HandLandmarkerGraph tracks the landmarks over time, and skips the HandDetectorGraph. If the
> tracking is lost or the detectd hands are less than configured max number hands,
> HandDetectorGraph would be triggered to detect hands."* — sic, including the typo.

The wiring, from `BuildHandLandmarkerGraph`:

```text
image_in ──► PreviousLoopbackCalculator ──► prev_hand_rects   (from last frame's landmarks)
                                                  │
             NormalizedRectVectorHasMinSizeCalculator(min_size = num_hands)
                                                  │
                                          has_enough_hands : bool
                                                  │
   ┌──────────────────────────────────────────────┴──────────────┐
   │  use_stream_mode == true                                    │
   │    image_for_detector = DisallowIf(image_in, has_enough_hands)
   │      → the detector sees NO FRAME while tracking holds      │
   │    HandAssociationCalculator(BASE_RECTS = prev, RECTS = new)│
   │    ClipNormalizedRectVectorSizeCalculator(max = num_hands)  │
   │                                                             │
   │  use_stream_mode == false                                   │
   │    the detector runs on every frame; no association         │
   └─────────────────────────────────────────────────────────────┘
                                                  │
                             MultipleHandLandmarksDetectorGraph
                                                  │
                             HandLandmarksDeduplicationCalculator
                                                  │
                             filtered next-frame ROIs ──► back edge ──► PreviousLoopback
```

Three consequences follow, and all three matter.



### 4.4.1. Tracking exists only in stream mode
`use_stream_mode` is false in `IMAGE` running mode and true in `VIDEO` and `LIVE_STREAM`. In
`IMAGE` mode the detector runs on every call and there is no temporal state at all — the comment
in the graph is explicit that inputs *"are not guaranteed to be in series"*. Feeding video frames
one at a time through `detect()` therefore silently discards the entire tracking optimisation.



### 4.4.2. The `num_hands = 2` pathology
`min_size` is set to `max_num_hands` (`hand_landmarker_graph.cc:283–286`), so `has_enough_hands`
is true **only when the number of tracked hands equals `num_hands`**. With `num_hands = 2` and one
hand in frame, `has_enough_hands` is false on every frame, so `DisallowIf` never blocks the image,
so **the 192×192 palm detector runs on every single frame** for as long as the second hand is
absent.

This is not a bug; it is the price of noticing a second hand promptly. But for sign language it is
the *common* case, not an edge case: signers routinely drop to one hand mid-utterance. The frame
rate will fall exactly when the signer is mid-sentence.

> **Warning — measure this before the demo.** The fix is not in MediaPipe. `RDH` solves it in
> application code with a tolerance counter; see
> [`DHR_S5.2`](../depthai-hand-tracker/DHR_depthai_report.md#52-the-single-hand-tolerance-threshold)
> and [`ARC_S6.5`](../../plan/ARC_architecture.md#65-perception-engineering-rules).



### 4.4.3. Deduplication is not free
`HandLandmarksDeduplicationCalculator` suppresses two detections of the same physical hand using
IoU **and** the distances between corresponding landmarks, normalised by a per-hand baseline
distance computed as the maximum of the wrist→index-MCP, index-MCP→pinky-MCP and pinky-MCP→wrist
spans (`hand_landmarks_deduplication_calculator.cc:73–127`). Scaling by hand size is what makes
the threshold work at different distances from the camera. It is a good idea worth copying.




## 4.5. The Misnamed Option
`min_tracking_confidence` is documented in the Python dataclass as *"The minimum confidence score
for the hand tracking to be considered successful"* (`hand_landmarker.py:311–313`), and in the
proto as *"Minimum confidence for hand landmarks tracking to be considered successfully"*
(`hand_landmarker_graph_options.proto:45–47`).

Following the wiring:

1. `hand_landmarker.cc:118` — `options_proto->set_min_tracking_confidence(...)`
2. `hand_landmarker_graph.cc:310–313` — the value is passed to
   `HandAssociationCalculator::set_min_similarity_threshold`
3. `hand_association_calculator.cc:103–104` — that threshold is the third argument to
   `mediapipe::DoesRectOverlap`
4. `mediapipe/util/rectangle_util.h:28–37` — `DoesRectOverlap` returns true when a new rectangle
   overlaps an existing one; the neighbouring declaration is `CalculateIou`

> **Warning.** `min_tracking_confidence` is **not a confidence at all**. It is an
> **intersection-over-union threshold** used to decide whether a freshly detected palm rectangle
> is the same hand as one already being tracked, and should therefore be discarded. Raising it
> does not make tracking stricter — it makes the graph *more* willing to accept a new detection as
> a second, distinct hand. Anyone tuning it as a quality knob will get the opposite of what they
> expect. Tune it against observed duplicate-hand behaviour, and record what the value does in a
> comment.

---





# 5. THE PYTHON API IN DETAIL
## 5.1. Options
`HandLandmarkerOptions`, `hand_landmarker.py:291–325`:

| Field                           | Default      | Wired to                                    |
| :------------------------------ | :----------- | :------------------------------------------ |
| `base_options`                  | *(required)* | Model path or buffer, delegate              |
| `running_mode`                  | `IMAGE`      | `use_stream_mode`, tracking on or off       |
| `num_hands`                     | `1`          | Detector cap **and** the tracking gate      |
| `min_hand_detection_confidence` | `0.5`        | Palm detector `min_score_thresh`            |
| `min_hand_presence_confidence`  | `0.5`        | Presence `ThresholdingCalculator`           |
| `min_tracking_confidence`       | `0.5`        | **IoU** in `HandAssociationCalculator`      |
| `result_callback`               | `None`       | Required in `LIVE_STREAM`, banned otherwise |

Note the default `num_hands = 1`. Sign language needs 2, which activates the pathology in
[`MPR_S4.4.2`](#442-the-num_hands--2-pathology).




## 5.2. Running Modes
`vision_task_running_mode.py:30–52` defines three, and `validate_running_mode` (`:55–79`) enforces
one rule: a `result_callback` **must** be supplied in `LIVE_STREAM` and **must not** be supplied
otherwise.

1. **`IMAGE`** · *Method:* `detect(image)`
   *Behaviour:* Stateless. Detector every call. No timestamps
2. **`VIDEO`** · *Method:* `detect_for_video(image, timestamp_ms)`
   *Behaviour:* Tracking on. **Synchronous** — blocks and returns the result. Timestamps must be
   monotonically increasing
3. **`LIVE_STREAM`** · *Method:* `detect_async(image, timestamp_ms)`
   *Behaviour:* Tracking on. Returns immediately; results arrive on `result_callback`. The
   docstring is explicit: *"To lower the overall latency, hand landmarker may drop the input images
   if needed. In other words, it's not guaranteed to have output per input image."*
   (`hand_landmarker.py:544–551`)

> **Decision support.** `LIVE_STREAM` mode implements
> [`APR_S6.7`](../apple/APR_apple_report.md#67-drop-frames-never-queue-them) — Apple's lesson L7,
> drop frames under load rather than queue them — **inside the library**. Choosing `LIVE_STREAM`
> therefore buys the drop-oldest behaviour for free, at the cost of an asynchronous callback that
> the segmenter must be built to tolerate. Choosing `VIDEO` keeps the code straight-line and
> synchronous but makes back-pressure the application's problem. See
> [`ARC_S6.5`](../../plan/ARC_architecture.md#65-perception-engineering-rules).




## 5.3. The Result
`HandLandmarkerResult`, `hand_landmarker.py:245–257`. Three parallel lists, **one entry per
detected hand**:

1. **`handedness`** · *Type:* `List[List[Category]]`
   *Contents:* One-element inner list. `Category` carries `index`, `score`, `category_name`
   (`"Left"` / `"Right"`)
2. **`hand_landmarks`** · *Type:* `List[List[NormalizedLandmark]]`
   *Contents:* 21 per hand. `x`, `y` in `[0, 1]` image space; `z` relative, scaled by 0.4 × crop
   width
3. **`hand_world_landmarks`** · *Type:* `List[List[Landmark]]`
   *Contents:* 21 per hand, **in metres**, origin at the hand's approximate geometric centre

> **Warning — an empty result is the normal case, not an error.** When no hand clears the presence
> gate, all three lists are empty. Code that indexes `result.hand_landmarks[0]` without checking
> will crash on the first frame the signer's hands leave the frame. This is the same discipline as
> [`APR_S6.3`](../apple/APR_apple_report.md#63-confidence-is-a-gate-not-a-weight): absence is a
> value, and it must be handled as one.

> **Warning — handedness is from the camera's point of view, and it is unreliable.** The label
> refers to the physical hand, but the model infers it from appearance in a single crop, and it
> flips. `RDH` averages it across the tracked lifetime of a hand precisely because a single frame's
> answer is not trustworthy — see
> [`DHR_S5.3`](../depthai-hand-tracker/DHR_depthai_report.md#53-handedness-averaging). Since
> dominant and non-dominant hand carry different grammatical roles
> ([`ARC_S3.2`](../../plan/ARC_architecture.md#32-the-landmark-budget)), a flip is a linguistic
> error, not a cosmetic one.




## 5.4. Coordinate Spaces — Four of Them
| Space            | Origin                  | Units             | Source                 |
| :--------------- | :---------------------- | :---------------- | :--------------------- |
| Normalised image | Top-left of the image   | `[0, 1]`          | `hand_landmarks` x, y  |
| Relative depth   | Wrist ≈ 0               | Scaled 0.4 × crop | `hand_landmarks` z     |
| Hand world       | Hand's geometric centre | Metres            | `hand_world_landmarks` |
| Pose world       | Mid-hip                 | Metres            | Holistic only          |

> **Warning — the y-flip trap, restated.** MediaPipe's normalised origin is the **top-left**.
> Apple's Vision origin is the **bottom-left**. Copying the line
> `y = 1 - thumbTipPoint.location.y` out of
> [`APR_S5.2`](../apple/APR_apple_report.md#52-coordinate-spaces--three-of-them) into a MediaPipe
> pipeline flips the image. This is called out in
> [`CLD_S5.4`](../../CLAUDE.md#54-working-with-the-reference-repositories) because it is the single
> most likely bug to come out of reading both repositories in one week.

The normalised `z` deserves one more sentence, because it is routinely over-trusted: it is scaled
by the **crop** width (`kLandmarksNormalizeZ = 0.4`), and the crop is whatever the ROI happened to
be that frame. It is a weak within-hand depth ordering. It is not a distance from the camera, and
it must not be fed to a classifier as though it were.




## 5.5. A Complete Call
Assembled from the API as read; ⚠ **not executed** — no MediaPipe wheel was installed during this
review, and the model bundle was not downloaded.

```python
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

MODEL_PATH = "models/hand_landmarker.task"   # read from a constant — D3 stack slide

def on_result(result: vision.HandLandmarkerResult, image: mp.Image, timestamp_ms: int) -> None:
    if not result.hand_landmarks:
        return                                # absence is a value; do not guess
    for hand, handedness in zip(result.hand_landmarks, result.handedness):
        label = handedness[0].category_name   # "Left" / "Right", camera's point of view
        wrist = hand[vision.HandLandmark.WRIST]
        ...

options = vision.HandLandmarkerOptions(
    base_options=mp_python.BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=vision.RunningMode.LIVE_STREAM,
    num_hands=2,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5,              # an IoU threshold — see MPR_S4.5
    result_callback=on_result,
)

with vision.HandLandmarker.create_from_options(options) as landmarker:
    landmarker.detect_async(mp_image, timestamp_ms)
```

The model bundle name `hand_landmarker.task` is the one the repository's own tests use
(`mediapipe/tasks/python/test/vision/hand_landmarker_test.py:52`).

---





# 6. WORKING PHILOSOPHY
The design principles this codebase encodes, stated as principles rather than as API notes.




## 6.1. Detect Rarely, Track Constantly
The expensive model runs when the cheap loop cannot answer. Everything in
[`MPR_S4.4`](#44-the-tracking-loop) — the loopback, the min-size gate, the `DisallowIf` — exists to
avoid running a detector. `RDH` reports the practical effect bluntly: **frame rate is higher when
a hand is present than when it is absent**, because absence means the detector runs every frame
`[S4]`.




## 6.2. Crop, Rotate, Then Regress
The landmark model never sees a raw frame. It sees an upright, square, generously padded crop.
This is why a 21-point regressor works at all on a hand that can appear at any rotation: the
rotation was removed before the model ran, using seven cheap keypoints from the detector.




## 6.3. Confidence Is a Gate
`AllowIf(..., hand_presence)`. Below the threshold, no packet. Identical in effect to Apple's
`confidence > 0.3` guard clause, and to
[`ARC_S9`](../../plan/ARC_architecture.md#9-decisions) decision 8.




## 6.4. Predict the Next Frame's Region From This Frame's Answer
`hand_landmarks_to_rect` → expand 2.0 × → back edge. The assumption is that a hand does not move
far between consecutive frames. `RDH` calls it *"a very good bet"* `[S4]`. It fails on fast
movement — which is exactly what fingerspelling is.




## 6.5. Normalise Thresholds by Object Size
The deduplication calculator computes a baseline hand span and expresses landmark distances
relative to it. A fixed pixel threshold would work at one distance from the camera and nowhere
else.




## 6.6. Make the Boundary a Data Structure, Not a Call
`HandLandmarkerResult` is a plain dataclass of plain lists. Nothing downstream of it needs to know
that a C library, a TFLite interpreter or a calculator graph produced it. This is the same
boundary discipline as
[`APR_S10.3`](../apple/APR_apple_report.md#103-the-architectural-boundary-to-preserve), and it is
what makes the classifier and the segmenter unit-testable without a camera.

---





# 7. ADJACENT TASKS
## 7.1. Holistic Landmarker
`mediapipe/tasks/python/vision/holistic_landmarker.py` and
`mediapipe/tasks/cc/vision/holistic_landmarker/holistic_landmarker_graph.cc`.

**Outputs**, per the graph's own header comment (`:215–262`):

1. `face_landmarks` — **468**, normalised
2. `pose_landmarks` — 33, normalised; `pose_world_landmarks` in **metres, origin at the hip
   centre**
3. `left_hand_landmarks` / `right_hand_landmarks` — 21 each, normalised
4. `left_hand_world_landmarks` / `right_hand_world_landmarks` — 21 each, metres, and — the
   important part — *"translated so that wrist from hand matches wrist from pose in pose
   coordinates system"*
5. `face_blendshapes` — optional
6. `segmentation_mask` — optional, person vs background

**Options** (`holistic_landmarker.py:260–273`): seven separate confidence and suppression
thresholds, `output_face_blendshapes`, `output_segmentation_mask`, and the same three running
modes with `detect` / `detect_for_video` / `detect_async`.

> **Decision support — this changes
> [`ARC_S4.3`](../../plan/ARC_architecture.md#43-recommended-representation).** That section
> specifies re-expressing hand positions relative to the signer's own body, with the
> origin at mid-shoulder. Holistic already delivers hand world landmarks **translated into the pose
> coordinate system**, and pose world landmarks with the origin at the hip centre. A large part of
> the normaliser the project planned to write is already written, tested and shipped. The
> remaining work is scale normalisation by shoulder width and the velocity/acceleration features.

Three limits, all hard:

1. **One person only.** `holistic_landmarker_graph.cc:377–379` forces `num_faces` to 1, with the
   comment *"holistic landmarker only supports a single person"*. There is no `num_poses`. For a
   two-way conversation between a signer and a hearing person in one frame, this is a real
   constraint — see [`RSK_S5`](../../plan/RSK_risk_register.md#5-multi-person-and-conversation)
2. **No handedness classification.** Left and right are separate output streams derived from the
   pose skeleton rather than a per-crop classifier. This is arguably *better* — it is the same
   trick `RDH` uses to make handedness robust — but it is not the same field, and code written
   against `HandLandmarkerResult.handedness` does not port across
3. **468 face landmarks, not 478.** The refined-iris variant is not what this graph documents.
   [`ARC_S3.2`](../../plan/ARC_architecture.md#32-the-landmark-budget) rejects the full mesh as a
   model input regardless; the count matters only for indexing the curated subset




## 7.2. Pose Landmarker
`mediapipe/tasks/python/vision/pose_landmarker.py`, 611 lines. 33 body landmarks, normalised and
world; supports **multiple people** via `num_poses`; optional segmentation masks. The route to
multi-person signing-space geometry if `HolisticLandmarker`'s single-person limit becomes binding.




## 7.3. Gesture Recognizer
`mediapipe/tasks/python/vision/gesture_recognizer.py`, 504 lines. Wraps the hand landmarker and
adds two classifier heads: `canned_gestures_classifier_options` and
`custom_gestures_classifier_options` (`:66–71`), each with score thresholds and allow/deny lists.
It exposes the same `num_hands` and three confidence options as the hand landmarker.

> **Warning — it is single-frame.** The recogniser classifies a hand *shape* in one frame. It has
> no temporal model, no notion of movement, and therefore cannot represent the movement parameter
> that distinguishes many signs. It is not a sign recogniser and must never be described as one in
> a submission — [`CLD_S5.2`](../../CLAUDE.md#52-honesty-about-the-product). It is, however, a
> legitimate baseline for the subset of signs that are static handshapes, and a very cheap one.




## 7.4. Model Maker
`mediapipe/model_maker/python/vision/gesture_recognizer/`. Trains a custom gesture classifier from
labelled images. `constants.py:19–37` shows the architecture:

- `gesture_embedder.tflite` — a **frozen embedder** that maps hand landmarks to a feature vector
- `canned_gesture_classifier.tflite` — the stock head
- the trained artefact is `custom_gesture_classifier.tflite`, a small head over that embedding

> **Decision support.** The frozen embedder is a pre-trained landmark feature extractor, produced
> by Google, that the project could use **as a feature stage under its own temporal classifier**
> instead of hand-designing features from raw coordinates. That is a genuine option for
> [`ARC_S7.3`](../../plan/ARC_architecture.md#73-p1--the-recommendation-in-detail) stage 5, and it
> is cheap to test. ⚠ The embedder's input format and output dimensionality were **not verified**
> in this review; that verification is a prerequisite before the option is planned against.

---





# 8. THE REST OF THE REPOSITORY IN BRIEF
Deliberately short. None of the following is on the project's path, and this section exists so
that nobody re-derives that conclusion by reading 600 MB.

1. **`mediapipe/framework/`** — the calculator graph engine: scheduler, packets, timestamps,
   calculator contracts. Worth reading only to understand *why* the Tasks API behaves as it does
2. **`mediapipe/calculators/`** — the node library, ~22 MB. Consumed indirectly through the task
   graphs
3. **`mediapipe/examples/`** — Android, iOS and desktop demo applications, ~20 MB. Building any of
   them requires Bazel plus platform SDKs
4. **`mediapipe/java/`, `mediapipe/objc/`, `mediapipe/web/`, `mediapipe/tasks/{java,ios,web,c}/`**
   — the same tasks bound to other languages. Irrelevant to a Python submission
5. **`mediapipe/gpu/`** — GPU inference paths. The project targets CPU so that it runs on any
   laptop
6. **`mediapipe/modules/`, `mediapipe/graphs/`** — the legacy `.pbtxt` pipelines behind the old
   Solutions API. Explicitly excluded from the wheel by `setup.py`
7. **`mediapipe/tasks/{text,audio,genai}/`** — text classification, audio classification, on-device
   LLM inference. The project's language layer is Bedrock, per `D1`/`D2`
8. **`mediapipe/model_maker/{image_classifier,object_detector,text_classifier}/`** — retraining
   recipes for tasks the project does not use
9. **`docs/`** — the legacy documentation site. `docs/solutions/hands.md` is the exception and is
   cited throughout [`MPR_S4`](#4-the-hand-landmarker-pipeline)
10. **Build infrastructure** — `WORKSPACE` (33 KB), `MODULE.bazel`, `.bazelrc`, three
    `Dockerfile`s, `setup_opencv.sh`, `build_*_examples.sh`. Needed only for a source build

---





# 9. WHAT THE HAND LANDMARKER DOES NOT DO
1. **No temporal model.** Tracking predicts a *region*, not a *pose*. There is no smoothing, no
   filtering and no velocity estimate in the task output
2. **No sign, gesture or meaning.** 21 points and a label. `GestureRecognizer` adds single-frame
   static shapes and stops there
3. **No subject selection.** `num_hands` caps the count; it does not choose *whose* hands
4. **No occlusion recovery.** A hand hidden behind the body drops out and is re-detected on
   reappearance, with no identity carried across the gap
5. **No person identity.** Hands are ordered per frame. There is no guarantee that index 0 is the
   same hand as index 0 on the previous frame
6. **No metric position in the room.** World landmarks are metric *within the hand*. Nothing
   locates that hand relative to the camera
7. **No face or body.** Separate tasks, separate models, separate cost
8. **No calibrated confidence.** Presence and handedness scores are model outputs, not calibrated
   probabilities, and must not be reported as such
9. **No guarantee of one output per input** in `LIVE_STREAM` mode, by explicit documentation
10. **No two-hand disambiguation.** Two left hands can be returned; the deduplication calculator
    suppresses geometric duplicates, not classification errors

Items 4, 5 and 10 are the ones that will hurt. All three are application-layer problems, and all
three have worked solutions in `RDH` — see
[`DHR_S5`](../depthai-hand-tracker/DHR_depthai_report.md#5-the-tracking-logic-worth-porting).

---





# 10. RUNNING IT
**Do not build this repository.** The Tasks API is consumed from a wheel; the source tree is
reference material. A source build needs Bazel, a C++ toolchain, and a source build of OpenCV via
`setup_opencv.sh`, and delivers nothing the wheel does not.

The intended path is three steps:

1. `pip install` a **pinned** MediaPipe version —
   [`MPR_S2.3`](#23-python-packaging-and-the-legacy-solutions-api)
2. Download the `hand_landmarker.task` bundle into `models/`, git-ignored per `CLD_S6` rule 5
3. Write against `mediapipe.tasks.python.vision`, never `mediapipe.solutions`

> **Placeholder — measured performance on the team's own hardware.**
> **Missing:** frames per second for `num_hands=1` and `num_hands=2`, with one and two hands
> present, on the laptop that will run the demo; and the frame-rate drop predicted by
> [`MPR_S4.4.2`](#442-the-num_hands--2-pathology).
> **Update trigger:** the first working capture loop.
> **Owner:** team. Record the results in `EVL`.

---





# 11. RELEVANCE TO SIMPLYNEXT
## 11.1. Lessons to Carry Across
| #  | Lesson                                                                                   |
| :- | :--------------------------------------------------------------------------------------- |
| M1 | **Detect rarely, track constantly.** The cheap loop answers; the expensive model rescues |
| M2 | **Confidence is a gate.** `AllowIf` emits nothing rather than something weak             |
| M3 | **Remove rotation before regressing.** Normalise the input, not the model                |
| M4 | **Predict the next region from this answer**, and accept that fast motion breaks it      |
| M5 | **Scale every threshold by object size**, never by pixels                                |
| M6 | **An empty result is a value.** Handle absence explicitly on every path                  |
| M7 | **Read the wiring, not the option name** — `min_tracking_confidence` is an IoU           |
| M8 | **Pin the dependency.** A 5,617-commit repository will move under the project            |

M2 and M6 are the two that connect directly to
[`CLD_S5.2`](../../CLAUDE.md#52-honesty-about-the-product): a system that never guesses needs a
perception layer that reports absence rather than inventing a plausible hand.




## 11.2. What the Project Must Build on Top
1. **Subject selection** · *Because:* `num_hands` caps count, not identity
   *Where:* Pipeline stage ① in [`ARC_S6.1`](../../plan/ARC_architecture.md#61-pipeline)
2. **Hand identity across frames** · *Because:* Per-frame ordering only
   *Where:* Stage ③, with handedness averaging ported from `RDH`
3. **Palm-detector rate limiting** · *Because:* [`MPR_S4.4.2`](#442-the-num_hands--2-pathology)
   *Where:* Stage ②, a tolerance counter around the two-hand case
4. **Body-relative normalisation** · *Because:* Partly solved by Holistic, not fully
   *Where:* Stage ③; scale by shoulder width, add velocity and acceleration
5. **Temporal segmentation** · *Because:* MediaPipe has no notion of an utterance
   *Where:* Stage ④, ported from
   [`APR_S5.3`](../apple/APR_apple_report.md#53-handgestureprocessorswift--the-state-machine)
6. **The classifier** · *Because:* No sign model exists here
   *Where:* Stage ⑤




## 11.3. Traps
1. **`mp.solutions.hands`** — not packaged at this commit. Every tutorial uses it
2. **`IMAGE` mode on a video** — silently disables tracking
3. **`num_hands = 2`** — palm detector on every frame while one hand is shown
4. **`min_tracking_confidence`** — an IoU threshold wearing a confidence's name
5. **Handedness index order** — `0 = Right`, `1 = Left` (`hand_landmarks_detector_graph.cc:129–142`)
6. **Normalised `z`** — scaled by 0.4 × crop width; not a depth in the room
7. **The y-flip** — MediaPipe's origin is top-left; Apple's is bottom-left
8. **Empty lists** — the normal output when no hand clears the gate
9. **Leaked handles** — use the context manager
10. **`LIVE_STREAM` drops frames** — by design; the segmenter must tolerate gaps

---





# 12. SOURCES
1. **`[S1]`**
   *Source:* `ref_repo/google-mediapipe/mediapipe/LICENSE` — Apache License 2.0, and
   https://github.com/google-ai-edge/mediapipe
   *Reliability:* The repository itself
2. **`[S2]`**
   *Source:* `ref_repo/google-mediapipe/mediapipe/docs/solutions/hands.md` — MediaPipe Hands
   solution page, including the palm-detection and hand-landmark model descriptions and the 95.7% /
   86.22% average-precision figures
   *Reliability:* ⚠ Official, but carries a deprecation banner forwarding to
   https://developers.google.com/mediapipe/solutions/vision/hand_landmarker. Re-verify the numbers
   against the current model card before quoting
3. **`[S3]`**
   *Source:* `ref_repo/google-mediapipe/mediapipe/README.md`, *Legacy solutions* section — support
   ended 1 March 2023; code continues *"on an as-is basis"*
   *Reliability:* Official
4. **`[S4]`**
   *Source:* [`DHR`](../depthai-hand-tracker/DHR_depthai_report.md), reporting
   `ref_repo/depthai-hand-tracker/depthai_hand_tracker/README.md`
   *Reliability:* Third-party practitioner observation, not a benchmark
5. **`[S5]`**
   *Source:* The clone itself: `ref_repo/google-mediapipe/mediapipe/` at `251c0cb96` (2026-08-28).
   All `file:line` citations in [`MPR_S4`](#4-the-hand-landmarker-pipeline) and
   [`MPR_S5`](#5-the-python-api-in-detail) resolve against this commit
   *Reliability:* Primary

---





# 13. CHANGE LOG
1. **2026-08-30** · *Author:* Claude (Opus 5)
   *Change:* Created from a read of the Hand Landmarker Python API, its C++ task graphs, the
   palm-detector and landmark-detector subgraphs, the association and deduplication calculators,
   the Holistic, Pose and Gesture Recognizer tasks, Model Maker's gesture recipe, `setup.py` and
   the legacy solution documentation. Recorded the `min_tracking_confidence` misnomer, the
   `num_hands = 2` detector pathology, and the exclusion of the legacy Solutions API from the
   1.0-line wheel.
