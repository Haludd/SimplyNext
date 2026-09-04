**GOOGLE MEDIAPIPE — SYNTHESIS FOR SIMPLYNEXT**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field             | Value                                                         |
| :---------------- | :------------------------------------------------------------ |
| **Code**          | `MPS`                                                         |
| **Status**        | Live                                                          |
| **Last reviewed** | 2026-08-30                                                    |
| **Scope**         | Short orientation to `RMP` and what SimplyNext takes from it  |
| **Subject**       | `RMP` — `ref_repo/google-mediapipe/mediapipe/` at `251c0cb96` |
| **Full report**   | [`MPR`](../ref_repo/google-mediapipe/MPR_mediapipe_report.md) |

**For the team.** A five-minute orientation to the library the perception layer is built on. The
complete analysis — every threshold, every wiring citation, the trap list — is in
[`MPR`](../ref_repo/google-mediapipe/MPR_mediapipe_report.md), which lives beside the clone in
`ref_repo/google-mediapipe/`. The sibling syntheses are [`APS`](APS_apple_synthesis.md),
[`DHS`](DHS_depthai_synthesis.md) and [`OPS`](OPS_openpose_synthesis.md); the four are compared
head-to-head in
[`ARC_S7.2`](../plan/ARC_architecture.md#72-the-four-reference-repositories-compared).

**For the assistant.** MediaPipe is a **dependency**, not a reference to admire. Nothing inside
`ref_repo/google-mediapipe/mediapipe/` may be edited; it is an unmodified clone, excluded from
version control. Where this file and
[`MPR`](../ref_repo/google-mediapipe/MPR_mediapipe_report.md) disagree, `MPR` wins.

</details>

---





# 1. WHAT THIS IS
Google's **MediaPipe**: a C++ engine for on-device perception graphs, plus a **Tasks API** that
wraps ready-made models behind an options object and a `detect()` call. Apache 2.0. The clone is
`master` at `251c0cb96` (2026-08-28), 5,617 commits deep, declaring version **1.0.1** in
development.

The project consumes exactly one part of it: **`mediapipe.tasks.python.vision`**, and within that
principally the **Hand Landmarker**. Everything else — the framework, the Android and iOS
examples, the GPU paths, the Java, Objective-C and TypeScript bindings — is summarised and set
aside in [`MPR_S8`](../ref_repo/google-mediapipe/MPR_mediapipe_report.md).

> **Warning — this is a live dependency, not a frozen sample.** Unlike `RAP`, which has four
> commits and will never change, MediaPipe moves continuously and has already dropped an API the
> whole internet still teaches. **Pin the version in `requirements.txt` on day one.**

---





# 2. RELEVANCE
Mapped onto the four MVP steps in [`SCR`](../plan/scribbles.md):

1. **1. Isolate the subject**
   *MediaPipe:* `num_hands` caps how many hands; `num_poses` caps how many people; Holistic allows
   exactly one
   *Status:* Partially solved — choosing *whose* hands is still the application's job
2. **2. Track many points**
   *MediaPipe:* 21 per hand + handedness, 33 pose, 468 face, real-time on CPU
   *Status:* **Solved. This is the reason to depend on it**
3. **3. Points → skeleton**
   *MediaPipe:* Normalised image landmarks, metric hand world landmarks, and — via Holistic — hand
   world landmarks already translated into the body's coordinate system
   *Status:* Solved further than the plan assumed
4. **4. Skeleton → conversational text**
   *MediaPipe:* Not attempted. `GestureRecognizer` does single-frame static handshapes
   *Status:* **The project's entire contribution**

MediaPipe's own documentation names the ambition — hand perception *"can form the basis for sign
language understanding"* — and then stops at the basis.

---





# 3. THE PIPELINE
```text
   full frame
        │
        ▼
   PALM DETECTOR  192 × 192, SSD, 2016 anchors, 7 keypoints     ── runs RARELY
        │         NMS at IoU 0.3, score ≥ min_hand_detection_confidence
        ▼
   ROI = palm box × 2.6, shift_y −0.5, squared, rotated upright
        │
        ▼
   LANDMARK MODEL on the crop                                    ── runs EVERY frame
        │  four output tensors:
        │   ① 21 landmarks   ② presence   ③ handedness   ④ world landmarks (metres)
        ▼
   GATE: presence ≥ min_hand_presence_confidence
        │   below → EMIT NOTHING, drop the track, re-run the detector
        ▼
   next ROI = landmark box × 2.0, shift_y −0.1, squared
        │
        └──────────► back edge: skip the detector next frame
```

A palm is detected rather than a hand because a palm is near-rigid and roughly square, which lets
the model use square anchors only — *"reducing the number of anchors by a factor of 3–5"*. Reported
palm-detection average precision is **95.7%**, against an **86.22%** baseline. ⚠ Both figures come
from a documentation page carrying a deprecation banner; re-verify before putting either on a
slide —
[`MPR_S4.1`](../ref_repo/google-mediapipe/MPR_mediapipe_report.md#41-the-two-model-design).

---





# 4. THE API IN ONE PAGE
```python
options = vision.HandLandmarkerOptions(
    base_options=mp_python.BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=vision.RunningMode.LIVE_STREAM,   # IMAGE | VIDEO | LIVE_STREAM
    num_hands=2,
    min_hand_detection_confidence=0.5,   # → palm detector score threshold
    min_hand_presence_confidence=0.5,    # → the presence gate
    min_tracking_confidence=0.5,         # → an IoU threshold. NOT a confidence
    result_callback=on_result,           # required in LIVE_STREAM, banned otherwise
)
with vision.HandLandmarker.create_from_options(options) as landmarker:
    landmarker.detect_async(mp_image, timestamp_ms)
```

**The result** is three parallel lists, one entry per detected hand: `handedness`
(`"Left"`/`"Right"` with a score), `hand_landmarks` (21 normalised points, origin **top-left**),
`hand_world_landmarks` (21 points in metres, origin at the hand's centre). When nothing clears the
gate, all three are **empty** — that is the normal case, not an error.

**The three running modes** differ in more than ergonomics:

| Mode          | Method             | Tracking | Notes                                 |
| :------------ | :----------------- | :------- | :------------------------------------ |
| `IMAGE`       | `detect`           | **Off**  | Detector on every call; no timestamps |
| `VIDEO`       | `detect_for_video` | On       | Synchronous; timestamps must increase |
| `LIVE_STREAM` | `detect_async`     | On       | Async callback; **may drop frames**   |

---





# 5. THE EIGHT LESSONS
Full rationale in
[`MPR_S11.1`](../ref_repo/google-mediapipe/MPR_mediapipe_report.md#111-lessons-to-carry-across).

| #  | Lesson                                                                          |
| :- | :------------------------------------------------------------------------------ |
| M1 | **Detect rarely, track constantly** — the cheap loop answers, the model rescues |
| M2 | **Confidence is a gate.** Below threshold, emit nothing at all                  |
| M3 | **Remove rotation before regressing.** Normalise the input, not the model       |
| M4 | **Predict the next region from this answer** — and accept that speed breaks it  |
| M5 | **Scale thresholds by object size**, never by pixels                            |
| M6 | **An empty result is a value.** Handle absence on every path                    |
| M7 | **Read the wiring, not the option name**                                        |
| M8 | **Pin the dependency.** A 5,617-commit repository moves under the project       |

M2 is the same rule Apple reached independently in Swift
([`APS_S5`](APS_apple_synthesis.md#5-the-twelve-lessons), lesson L2) and the same rule
[`ARC_S9`](../plan/ARC_architecture.md#9-decisions) decision 8 makes a product invariant. Two
industrial teams converging on *refuse rather than guess* is worth one line on the architecture
slide.

---





# 6. THE FOUR TRAPS THAT WILL COST A DAY
1. **`mp.solutions.hands` is not in the 1.0-line wheel.** `setup.py` packages only
   `mediapipe.tasks.*`. Legacy-solutions support ended 1 March 2023. Almost every tutorial online
   uses the legacy API. Write against the Tasks API only
2. **`min_tracking_confidence` is an intersection-over-union threshold**, not a confidence.
   It is wired to `HandAssociationCalculator`'s rectangle-overlap test. Raising it makes the graph
   *more* willing to accept a new hand, not stricter —
   [`MPR_S4.5`](../ref_repo/google-mediapipe/MPR_mediapipe_report.md#45-the-misnamed-option)
3. **`num_hands = 2` with one hand visible runs the palm detector on every frame.** The tracking
   gate fires only when the tracked-hand count *equals* `num_hands`. Signers drop to one hand
   constantly, so the frame rate falls mid-utterance —
   [`MPR_S4.4.2`](../ref_repo/google-mediapipe/MPR_mediapipe_report.md).
   `DHS` carries the fix
4. **The y-flip.** MediaPipe's normalised origin is the **top-left**; Apple's Vision origin is the
   **bottom-left**. Copying Apple's `y = 1 - y` into a MediaPipe pipeline flips the image —
   [`CLD_S5.4`](../CLAUDE.md#54-working-with-the-reference-repositories)

Two more worth knowing: handedness index `0` is `Right` and `1` is `Left`, and the normalised `z`
is scaled by 0.4 × the *crop* width, so it is a within-hand depth ordering and not a distance from
the camera.

---





# 7. WHAT IT DOES NOT DO
No temporal model — tracking predicts a *region*, never a *pose*. No smoothing, no velocity. No
sign, gesture or meaning beyond single-frame static handshapes. No subject selection. No hand
identity across frames. No occlusion recovery. No metric position in the room. No calibrated
confidence. Two left hands can be returned at once.

Full list:
[`MPR_S9`](../ref_repo/google-mediapipe/MPR_mediapipe_report.md).

> **Note — Holistic Landmarker answers more of the plan than expected.** It emits 468 face + 33
> pose + 21 × 2 hand landmarks, and its hand world landmarks are *"translated so that wrist from
> hand matches wrist from pose in pose coordinates system"*. That is most of the body-relative
> normaliser [`ARC_S4.3`](../plan/ARC_architecture.md#43-recommended-representation) planned to
> write. The cost is a hard **one-person-only** limit —
> [`MPR_S7.1`](../ref_repo/google-mediapipe/MPR_mediapipe_report.md#71-holistic-landmarker).

---





# 8. RUNNING IT
**Do not build this repository.** A source build needs Bazel, a C++ toolchain and a source build
of OpenCV, and delivers nothing the wheel does not. The path is:

1. `pip install` a **pinned** MediaPipe version
2. Download `hand_landmarker.task` into `models/`, which `.gitignore` excludes
3. Import from `mediapipe.tasks.python.vision`, never `mediapipe.solutions`

No GPU, no CUDA, no compiler. That is the *"any device with a camera"* claim in
[`JCR_S2.1`](../plan/JCR_judging_criteria.md#21-c1--benefits-delivered-by-the-solution-20), and it
is the single biggest reason this library was chosen over `ROP`.

---





# 9. WHERE TO GO NEXT
| Question                     | Document                                                      |
| :--------------------------- | :------------------------------------------------------------ |
| Full breakdown of MediaPipe  | [`MPR`](../ref_repo/google-mediapipe/MPR_mediapipe_report.md) |
| Tracking fixes it needs      | [`DHS`](DHS_depthai_synthesis.md)                             |
| Segmentation state machine   | [`APS`](APS_apple_synthesis.md)                               |
| Why OpenPose was rejected    | [`OPS`](OPS_openpose_synthesis.md)                            |
| What is being built, and why | [`ARC`](../plan/ARC_architecture.md)                          |
| What can go wrong            | [`RSK`](../plan/RSK_risk_register.md)                         |
| Where every document lives   | [`RIX`](../ref_index.md)                                      |

---





# 10. CHANGE LOG
1. **2026-08-30** · *Author:* Claude (Opus 5)
   *Change:* Created alongside [`MPR`](../ref_repo/google-mediapipe/MPR_mediapipe_report.md), from
   a read of the Hand Landmarker Python API and its C++ task graphs.
