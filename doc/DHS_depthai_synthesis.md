**DEPTHAI HAND TRACKER — SYNTHESIS FOR SIMPLYNEXT**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field             | Value                                                             |
| :---------------- | :---------------------------------------------------------------- |
| **Code**          | `DHS`                                                             |
| **Status**        | Live                                                              |
| **Last reviewed** | 2026-08-30                                                        |
| **Scope**         | Short orientation to `RDH` and what SimplyNext takes from it      |
| **Subject**       | `RDH` — `depthai-hand-tracker/depthai_hand_tracker/` at `9773123` |
| **Full report**   | [`DHR`](../ref_repo/tracking/depthai-hand-tracker/DHR_depthai_report.md)   |

**For the team.** A five-minute orientation. The complete analysis is in
[`DHR`](../ref_repo/tracking/depthai-hand-tracker/DHR_depthai_report.md), which lives beside the clone in
`ref_repo/tracking/depthai-hand-tracker/`. The sibling syntheses are [`APS`](APS_apple_synthesis.md),
[`MPS`](MPS_mediapipe_synthesis.md) and [`OPS`](OPS_openpose_synthesis.md); the four are compared
head-to-head in
[`ARC_S7.2`](../plan/ARC_architecture.md#72-the-four-reference-repositories-compared).

**For the assistant.** This repository is **not a dependency**. Its hardware is rejected. What
transfers is Python, and only from the three files that do not import `depthai`. Never describe
the project as using DepthAI or OAK hardware. Where this file and
[`DHR`](../ref_repo/tracking/depthai-hand-tracker/DHR_depthai_report.md) disagree, `DHR` wins.

</details>

---





# 1. WHAT THIS IS
`geaxgx/depthai_hand_tracker`: one developer's project to run **Google's MediaPipe hand models on
Luxonis OAK cameras**. MIT-licensed, 34 commits, last touched 2023-01-14 — and that a one-line
NumPy compatibility fix. ⚠ Effectively unmaintained.

To do this, the author had to re-implement in **NumPy** every piece of post-processing MediaPipe
normally performs inside compiled C++ calculators, and then build, in plain Python, the tracking
state machine MediaPipe keeps hidden inside its graph.

**That is the entire reason this repository is here.** The hardware is not being bought. The
Python is a translation of `RMP` into a language the team can read, test and change.

---





# 2. RELEVANCE
[`ARC_S7.1`](../plan/ARC_architecture.md#71-comparison-table) rates depth hardware `P4` and
rejects it: requiring an OAK camera turns *"any device with a camera"* into *"any device with
**this** camera"*, which attacks the C1 scalability score directly.

What is left is worth more than the hardware:

1. **MediaPipe's algorithms in readable Python** — `mediapipe_utils.py` (46 KB) ports the SSD
   anchors, box decoding, NMS, rotated-rect derivation and both ROI computations, with Google's
   original `.pbtxt` quoted in the comments beside each one
2. **The tracking state MediaPipe does not expose** — handedness averaging, a detector
   rate-limiter, duplicate-hand suppression. Exactly the gaps `MPS` lists as the project's to fill
3. **A worked answer to distance** — Body Pre Focusing, because *"the palm detector model from
   Google Mediapipe was trained to detect hands that are less than 2 meters away from the camera"*

And critically: **`mediapipe_utils.py` does not import `depthai`.** It imports `cv2`, `numpy` and
the standard library. It runs on the team's laptops today.

---





# 3. THE FIVE THINGS TO PORT
## 3.1. A Tolerance Counter on the Detector
`MPS` trap 3: with `num_hands = 2` and one hand visible, MediaPipe runs the palm detector on every
frame. The author hit this and named it plainly:

> *"If hand detection is run on every frame (until a second hand appear), the FPS drop is
> significant."*

His fix is one counter, `single_hand_tolerance_thresh`, default **10 frames**: after ten
consecutive one-hand frames, call the detector once in case a second hand appeared. His tuning
advice — near `0` when two hands are almost always expected, **10–30** when a second hand is
occasional, and not higher because *"the delay … may feel too long to be comfortable"*.

Sign language sits awkwardly in the middle of that range, and the transition between one hand and
two is *linguistically meaningful*. The value must be measured, not guessed.




## 3.2. Handedness Averaging
Ten lines, and a correctness fix rather than an optimisation. The docstring:

> *"Handedness inferred by the landmark model is not perfect. For certain poses, it is not rare
> that the model thinks that a right hand is a left hand (or vice versa). Instead of using the last
> inferred handedness, we prefer to use the average of the inferred handedness on the last frames."*

[`ARC_S3.2`](../plan/ARC_architecture.md#32-the-landmark-budget) puts handedness in the landmark
budget because dominant and non-dominant hands carry different grammatical roles. A per-frame flip
is therefore a **grammatical** error in the output. Averaging needs a stable hand identity across
frames, which MediaPipe does not provide, so the two must be built together.




## 3.3. Duplicate-Hand Detection
Two hands whose rectangle centres are within five pixels are collapsed, because *"that may happen
when one hand in the image cross another one"*. The five-pixel constant is crude and
resolution-dependent — MediaPipe's own deduplication normalises by hand size and is the better
model. The point to carry is that **crossing hands is a named failure mode that two independent
implementations both had to handle**, and signing crosses hands constantly.




## 3.4. Hands-Up-Only as a Segmentation Prior
Body Pre Focusing has an option to consider only hands whose wrist keypoint is above the elbow —
*"meaning in practice that the hands are raised"* — adopted to stop false gesture recognition when
a hand is at rest.

Sign language has the same structure: signing happens in a defined space in front of the torso,
and hands at rest are not signing. A hands-in-signing-space test is already stage ④ of
[`ARC_S6.1`](../plan/ARC_architecture.md#61-pipeline); this is field evidence that the heuristic
works.

A second, subtler point from the same feature: when the crop is built around a *body* wrist
keypoint, handedness comes from **which wrist it was**, *"much more reliable than the handedness
inferred by the landmark model"*. That is the same mechanism `HolisticLandmarker` uses, and it is
strictly better than classifying handedness from a hand crop.




## 3.5. Counting Everything
`HandTracker.exit()` prints, on shutdown: global frame rate; frames with no hand; frames on which
palm detection ran; frames with landmark inference **split by whether the region came from
detection or from the previous frame's landmarks**; failed landmark inferences; and per-stage
round-trip times.

That is most of the perception half of
[`ARC_S8.4`](../plan/ARC_architecture.md#84-proposed-metric-set), for the cost of a handful of
counters. *"Frames on which palm detection ran, as a percentage"* is the one number that exposes
the `num_hands = 2` pathology.

---





# 4. ONE THING NOT TO COPY
When two hands are classified with the same handedness, this repository **drops one of them**.

For sign language that is the wrong trade. A two-handed sign observed with one hand is
unrecognisable, which is a worse outcome than a mislabelled hand. The project keeps both hands and
marks the handedness **uncertain** — which is what
[`ARC_S9`](../plan/ARC_architecture.md#9-decisions) decision 8 requires anyway: report the
uncertainty rather than resolve it silently.

---





# 5. THE NINE LESSONS
Full rationale in
[`DHR_S10.1`](../ref_repo/tracking/depthai-hand-tracker/DHR_depthai_report.md#101-lessons-to-carry-across).

| #  | Lesson                                                                           |
| :- | :------------------------------------------------------------------------------- |
| D1 | **Rate-limit the expensive detector with a tolerance counter**, not with hope    |
| D2 | **Average handedness over a hand's tracked lifetime.** One frame is not evidence |
| D3 | **Crossing hands is a named failure mode.** Detect duplicates explicitly         |
| D4 | **Prefer "uncertain" to dropping a hand**                                        |
| D5 | **A body model can rescue a hand detector** trained for close range              |
| D6 | **Hands at rest are not signing.** A cheap, free segmentation prior              |
| D7 | **Count everything and print it on exit.** Perception needs metrics too          |
| D8 | **Geometry beats a model** where geometry answers the question                   |
| D9 | **Constants are tunable** — the author documented disagreeing with Google's      |

---





# 6. WHAT IT DOES NOT DO
No face and no body landmarks in the output — the body model is used only to crop. No temporal
model. No sign recognition: `recognize_gesture()` reads **handshape only**, from a single frame,
and matches eight hard-coded patterns (`FIVE`, `FIST`, `OK`, `PEACE`, `ONE`…`FOUR`). No stable
hand identity. No tests, no packaging. ⚠ Unmaintained since 2021.

Full list:
[`DHR_S8`](../ref_repo/tracking/depthai-hand-tracker/DHR_depthai_report.md).

> **Warning — `recognize_gesture` is a ceiling, not a floor.** Sign language is analysed in terms
> of handshape, orientation, location, movement and non-manual markers. That function reads one of
> the five. Describing anything like it as sign-language recognition would be the capability
> overstatement [`CLD_S5.2`](../CLAUDE.md#52-honesty-about-the-product) forbids. It is a fair and
> nearly free **baseline** to measure the trained classifier against, and nothing more.

The one habit worth stealing from it: every finger has an explicit `unknown` state, and an
unmatched pattern returns `None`. It refuses rather than guesses, in twelve lines.

---





# 7. RUNNING IT
**The demos cannot run** without an OAK camera; `dai.Device()` is constructed during tracker
setup, and no emulator exists.

**The algorithms can run today.** `mediapipe_utils.py` needs only OpenCV and NumPy:

```python
import sys; sys.path.append("ref_repo/tracking/depthai-hand-tracker/depthai_hand_tracker")
import mediapipe_utils as mpu
anchors = mpu.generate_handtracker_anchors(192, 192)   # expect (2016, 4)
```

⚠ Not executed during this review; the expected shape is derived from the anchor constants read in
both this repository and `RMP`. Confirming it takes five minutes and validates the reading of
[`MPS_S3`](MPS_mediapipe_synthesis.md#3-the-pipeline) against an independent implementation.

> **Note — nothing in `src/` may import from `ref_repo/`.** The directory is git-ignored, so a
> judge cloning the submission would get an `ImportError`. Anything the project keeps is
> re-implemented in `src/`, with attribution under the MIT notice.

---





# 8. WHERE TO GO NEXT
| Question                     | Document                                                        |
| :--------------------------- | :-------------------------------------------------------------- |
| Full breakdown of DepthAI    | [`DHR`](../ref_repo/tracking/depthai-hand-tracker/DHR_depthai_report.md) |
| Library these fixes apply to | [`MPS`](MPS_mediapipe_synthesis.md)                             |
| Segmentation state machine   | [`APS`](APS_apple_synthesis.md)                                 |
| Why the hardware is rejected | [`ARC_S7.1`](../plan/ARC_architecture.md)                       |
| What is being built, and why | [`ARC`](../plan/ARC_architecture.md)                            |
| Where every document lives   | [`RIX`](../ref_index.md)                                        |

---





# 9. CHANGE LOG
1. **2026-08-30** · *Author:* Claude (Opus 5)
   *Change:* Created alongside
   [`DHR`](../ref_repo/tracking/depthai-hand-tracker/DHR_depthai_report.md), from a read of
   `mediapipe_utils.py`, `HandTracker.next_frame()`, `BodyPreFocusing` and the README.
