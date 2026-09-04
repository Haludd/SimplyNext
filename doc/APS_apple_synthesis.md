**APPLE HANDPOSE — SYNTHESIS FOR SIMPLYNEXT**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field             | Value                                                        |
| :---------------- | :----------------------------------------------------------- |
| **Code**          | `APS`                                                        |
| **Status**        | Live                                                         |
| **Last reviewed** | 2026-08-30                                                   |
| **Scope**         | Short orientation to `RAP` and what SimplyNext takes from it |
| **Subject**       | `RAP` — `ref_repo/apple/handpose/` at `ec30ff6`              |
| **Full report**   | [`APR`](../ref_repo/apple/APR_apple_report.md)               |

**For the team.** A five-minute orientation. The complete technical analysis, including line
references and the Swift → Python port table, is in
[`APR`](../ref_repo/apple/APR_apple_report.md), which lives beside the clone in `ref_repo/apple/`.
The sibling syntheses are [`MPS`](MPS_mediapipe_synthesis.md),
[`DHS`](DHS_depthai_synthesis.md) and [`OPS`](OPS_openpose_synthesis.md); the four are compared
head-to-head in
[`ARC_S7.2`](../plan/ARC_architecture.md#72-the-four-reference-repositories-compared).

**For the assistant.** Nothing in `ref_repo/apple/handpose/` belongs to the project; it is an
unmodified third-party clone, excluded from version control, and must not be edited. Where this
file and [`APR`](../ref_repo/apple/APR_apple_report.md) disagree, `APR` wins.

</details>

---





# 1. WHAT THIS IS
Apple's official sample **"Detecting Hand Poses with Vision"** (`HandPose`), companion code to
WWDC20 session 10653. About 454 lines of Swift in five files. It turns the front camera into a
finger-painting surface: pinching thumb and index together draws, pulling them apart stops.

> **Correction.** This is **not** an Apple Vision Pro project. It targets **iOS 14 on iPhone and
> iPad**, using Apple's **Vision** framework — a computer-vision library that predates the Vision
> Pro headset by six years. The hand-pose API is also available on visionOS 1.0+, so this changes
> nothing technically, but calling it a Vision Pro project in a submission would be a factual
> error. Details: [`APR_S1.1`](../ref_repo/apple/APR_apple_report.md#11-what-this-repository-is).

---





# 2. RELEVANCE
Apple's app is **steps 1–3 of the MVP** in [`SCR`](../plan/scribbles.md), built to production
quality and stopping deliberately before step 4.

1. **1. Isolate the subject**
   *Apple's app:* `maximumHandCount = 1`; Vision orders hands by size, largest wins
   *Status:* Solved, crudely
2. **2. Track many points**
   *Apple's app:* 21 hand joints available; **the app uses 2**
   *Status:* Capability present, under-used
3. **3. Points → skeleton**
   *Apple's app:* 2D normalised, confidence-gated, three coordinate spaces
   *Status:* Solved in 2D
4. **4. Skeleton → conversational text**
   *Apple's app:* Not attempted — a 5-state machine over one distance
   *Status:* **The project's entire contribution**

The value is not the drawing feature. It is the **plumbing**: getting from a camera buffer to
landmark data that is stable, trustworthy and never fabricated, in about 80 lines. That plumbing is
where naive sign-language prototypes fail.

---





# 3. THE PIPELINE
```text
camera ──► serial queue (drops late frames)
             │
             ├─ VNDetectHumanHandPoseRequest      one hand, stateless, per frame
             ├─ GATE: point exists?
             ├─ GATE: confidence > 0.3?           low confidence → emit NOTHING
             └─ Vision space → AVFoundation space (y := 1 − y)
                       │
                       ▼  main.sync   ← deliberate back-pressure
             AVFoundation → UIKit layer points
                       │
             HandGestureProcessor                 evidence counters, 3-frame trigger
               unsure  → buffer the frames        (orange dots)
               pinched → REPLAY the buffer, draw  (green dots)
               apart   → discard buffer, close    (red dots)
               2 s with no hand → reset
                       │
             UIBezierPath → CAShapeLayer, implicit animation off
```

---





# 4. FILE MAP
1. **`handpose/HandPose/CameraViewController.swift`** · *Lines:* 243
   *Contents:* **Start here.** Capture setup, Vision call, confidence gates, coordinate conversions,
   the evidence buffer
2. **`handpose/HandPose/HandGestureProcessor.swift`** · *Lines:* 79
   *Contents:* **The most instructive file.** A hysteresis state machine importing *only*
   `CoreGraphics`
3. **`handpose/HandPose/CameraView.swift`** · *Lines:* 58
   *Contents:* `layerClass` override; disabling implicit Core Animation
4. **`handpose/HandPose/AppDelegate.swift`** · *Lines:* 59
   *Contents:* The typed `AppError` vocabulary
5. **`handpose/HandPose/SceneDelegate.swift`** · *Lines:* 15
   *Contents:* Boilerplate

---





# 5. THE TWELVE LESSONS
Full rationale and application in
[`APR_S10.1`](../ref_repo/apple/APR_apple_report.md#101-lessons-to-carry-across).

| #   | Lesson                                                                                  |
| :-- | :-------------------------------------------------------------------------------------- |
| L1  | Keep the ML layer **stateless**; own every temporal concept in plain, testable code     |
| L2  | Confidence is a **gate**, not a weight — drop the point rather than guess it            |
| L3  | **Hysteresis** before any state change; contradicting evidence zeroes the counter       |
| L4  | **Buffer while uncertain, commit retroactively** — debouncing costs latency, never data |
| L5  | **Show the machine hesitating** (orange = unsure). Honesty as a UI feature              |
| L6  | Smooth the *output*, not the *decision*                                                 |
| L7  | **Drop frames** under load; never queue them                                            |
| L8  | **Staleness is a state** — 2 s without hands is an event, not an absence                |
| L9  | Convert coordinates **once**, at layer boundaries                                       |
| L10 | **Fail loudly and stop.** Never degrade silently                                        |
| L11 | **Zero-chrome demo** — one screen, one capability, nothing to break on stage            |
| L12 | Use **cheap arithmetic** where geometry answers the question                            |

L4 is the one to internalise. A 3-frame debounce normally costs the first 100 ms of every gesture;
Apple's buffer replays those frames the moment the state commits, so the delay costs latency but no
data. That is the template for the sign-boundary detector.

---





# 6. WHAT IT DOES NOT DO
One hand. Two of twenty-one joints. No chirality (the API postdates the sample). No face, no body,
no depth. No temporal model beyond a 3-frame counter. A two-symbol output vocabulary. No
multi-person handling, no text output, no tests, no metrics. Swift and UIKit only.

Full list: [`APR_S8`](../ref_repo/apple/APR_apple_report.md#8-what-the-repository-does-not-do).

> **Note:** Apple's *platform* has since answered two more MVP steps —
> `VNDetectHumanBodyPose3DRequest` (iOS 17, 3D body points relative to the camera) and
> `VNGeneratePersonInstanceMaskRequest` (iOS 17, per-person masks). Neither is in this 2020 sample.
> See [`APR_S7.2`](../ref_repo/apple/APR_apple_report.md#72-the-vision-hand-pose-api-in-detail).

---





# 7. PORTING TO THE PROJECT STACK
The implementation is Python (`D3_p42`). Full table:
[`APR_S10.2`](../ref_repo/apple/APR_apple_report.md#102-swift--python-port-table).

1. **`VNDetectHumanHandPoseRequest` (21 joints)**
   MediaPipe Hand Landmarker (21 landmarks + handedness)
2. **`VNDetectHumanBodyPoseRequest` + face**
   MediaPipe Holistic Landmarker (543 landmarks)
3. **`chirality`**
   MediaPipe `handedness`
4. **`alwaysDiscardsLateVideoFrames`**
   `queue.Queue(maxsize=1)`, drop-oldest
5. **`HandGestureProcessor`**
   The utterance segmenter — **must import neither camera, model, nor LLM**

> **Warning — the y-flip trap.** Vision's normalised space has its origin at the **bottom-left**;
> MediaPipe's at the **top-left**. The line `y = 1 - thumbTipPoint.location.y`
> (`CameraViewController.swift:233`) exists to reconcile Vision with AVFoundation. **Copying it
> into a MediaPipe pipeline flips the image upside down.** This is the most likely bug to come out
> of reading this repository.

---





# 8. RUNNING IT
Optional. Requires a Mac with Xcode 12+ and a **physical** iPhone or iPad on iOS 14+; the Simulator
has no camera. Open the project, set the Development Team under *Signing & Capabilities*, and build
to the device.

The fingertip dots show the state machine directly: **orange** while undecided, **green** while
committed to drawing, **red** while committed to not drawing. Waving a hand out of frame for two
seconds triggers the reset. The orange window is lesson L4 made visible.

---





# 9. WHERE TO GO NEXT
| Question                                    | Document                                       |
| :------------------------------------------ | :--------------------------------------------- |
| Full technical breakdown of this repository | [`APR`](../ref_repo/apple/APR_apple_report.md) |
| The tracker chosen, and why                 | [`MPS`](MPS_mediapipe_synthesis.md)            |
| What is being built, and why                | [`ARC`](../plan/ARC_architecture.md)           |
| What can go wrong                           | [`RSK`](../plan/RSK_risk_register.md)          |
| How the submission is scored                | [`JCR`](../plan/JCR_judging_criteria.md)       |
| Where every document lives                  | [`RIX`](../ref_index.md)                       |

---





# 10. CHANGE LOG
1. **2026-08-28** · *Author:* Claude (Opus 5)
   *Change:* Created as `SYN` in `ref_repo/apple/`.
2. **2026-08-30** · *Author:* Claude (Opus 5)
   *Change:* Recoded `SYN` → `APS` and moved to `doc/`, joining the three new repository syntheses
   — [`RIX_S2.1`](../ref_index.md#21-live-documents). Paths updated for the clone's relocation to
   `ref_repo/apple/handpose/`. No analysis changed.
