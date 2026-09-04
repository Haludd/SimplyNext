**DEPTHAI HAND TRACKER — FULL REPOSITORY REPORT**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field                   | Value                                                             |
| :---------------------- | :---------------------------------------------------------------- |
| **Code**                | `DHR`                                                             |
| **Status**              | Live                                                              |
| **Last reviewed**       | 2026-08-30                                                        |
| **Source of truth for** | Analysis of the DepthAI hand-tracker reference clone              |
| **Parent**              | [`RIX_S2.1`](../../ref_index.md#21-live-documents)                |
| **Short version**       | [`DHS`](../../doc/DHS_depthai_synthesis.md)                       |
| **Subject**             | `RDH` — `depthai-hand-tracker/depthai_hand_tracker/` at `9773123` |

**For the team.** This repository runs the same MediaPipe hand models as `RMP`, but on Luxonis
OAK hardware and with the whole pipeline re-implemented in **Python and NumPy**. The hardware is
not being bought. The Python is the point: it is the only place in the four reference repositories
where MediaPipe's tracking logic exists in a language the project can read, test and modify.
[`DHR_S5`](#5-the-tracking-logic-worth-porting) is the section that matters.

**For the assistant.** Distinguish carefully between the parts that need an OAK device
(`HandTracker*.py`, the `.blob` models, the `template_manager_script_*.py` device scripts) and the
parts that do not (`mediapipe_utils.py`, `FPS.py`, `HandTrackerRenderer.py`). Never describe this
repository as something the project depends on — it is not, and
[`ARC_S7.2`](../../plan/ARC_architecture.md#72-the-four-reference-repositories-compared) rejects
the hardware. Nothing inside `ref_repo/depthai-hand-tracker/depthai_hand_tracker/` may be edited.

</details>

---





# 1. EXECUTIVE SUMMARY
## 1.1. What This Repository Is
`ref_repo/depthai-hand-tracker/depthai_hand_tracker/` is **geaxgx/depthai_hand_tracker**, an
independent developer's project that runs *"Google Mediapipe Hand Tracking models on Luxonis
DepthAI hardware (OAK-D, OAK-D lite, OAK-1, …)"* `[S1]`. It is MIT-licensed, about 34 commits
long, and last changed on **2023-01-14** — a one-line NumPy compatibility fix.

It is not a library. It is a **worked implementation**: roughly 4,000 lines of Python that take
MediaPipe's two `.tflite` models, convert them to Intel MyriadX `.blob` format, run them on a
vision-processing unit, and rebuild in NumPy every piece of post-processing that MediaPipe
normally performs inside C++ calculators.

That last clause is why the repository is in `ref_repo/`.




## 1.2. Why It Matters to SimplyNext
The project will not buy an OAK camera —
[`ARC_S7.1`](../../plan/ARC_architecture.md#71-comparison-table) rates depth hardware `P4` and
rejects it because it breaks the *"scalable or easily adopted"* clause in
[`JCR_S2.1`](../../plan/JCR_judging_criteria.md#21-c1--benefits-delivered-by-the-solution-20).

The value is entirely in the source, and it is of three kinds:

1. **MediaPipe's algorithms, in readable Python** · *File:* `mediapipe_utils.py`, 1,000+ lines
   *Why it matters:* SSD anchor generation, box decoding, NMS, rotated-rect derivation, ROI
   expansion and the landmarks→ROI computation, all in NumPy, all with the original C++ `.pbtxt`
   quoted in comments. `MPR` describes these; this file *is* them
2. **The tracking-state logic MediaPipe does not give the application** · *File:* `HandTracker.py`
   *Why it matters:* Handedness averaging, the single-hand tolerance counter, duplicate-hand
   suppression and the detect-versus-track decision — the exact gaps listed in
   [`MPR_S11.2`](../google-mediapipe/MPR_mediapipe_report.md#112-what-the-project-must-build-on-top)
3. **A worked answer to the distance problem** · *File:* `HandTrackerBpf.py`, `mediapipe_utils.py`
   *Why it matters:* Body Pre Focusing — use a body-pose model to crop the region containing the
   hands before the palm detector runs, because *"the palm detector model from Google Mediapipe
   was trained to detect hands that are less than 2 meters away"* `[S1]`

Against the four MVP steps in [`SCR`](../../plan/scribbles.md):

1. **1. Isolate the subject** — solved twice over: Solo/Duo modes, and Body Pre Focusing with a
   `higher` / `left` / `right` / `group` selection policy
2. **2. Track many points** — the same 21 landmarks as `RMP`; no face, and body only as a
   cropping aid
3. **3. Points → skeleton** — world landmarks supported, plus true metric `xyz` of the wrist from
   the stereo depth sensor. **The `xyz` path is the part that needs the hardware**
4. **4. Skeleton → conversational text** — not attempted. `recognize_gesture()` is eight
   hard-coded static handshapes




## 1.3. Summary
A palm detector runs only when the tracker has no hand to follow. Its output is decoded from raw
tensors in NumPy, non-max-suppressed, turned into a rotated rectangle, expanded by 2.9× — the
author's own deviation from Google's 2.6 — and warped upright with an affine transform. A landmark
model runs on that crop. If the landmark score clears a threshold the hand survives; its landmarks
generate the next frame's region of interest directly. Handedness is averaged over the tracked
lifetime rather than trusted per frame. Two hands whose rectangles are within five pixels of each
other are collapsed to one. Two hands with the same handedness are collapsed to one. When only one
hand has been seen for ten consecutive frames, the palm detector is called again in case a second
appeared. Everything is counted and printed on exit.

---





# 2. PROVENANCE, LICENCE AND REQUIREMENTS
## 2.1. Provenance
1. **Author**
   `geaxgx`. Remote: `https://github.com/geaxgx/depthai_hand_tracker.git`
2. **Clone state**
   `9773123`, 2023-01-14, *"Replacing np.int by np.int32 as np.int is no longer available starting
   from numpy 1.24"*
3. **History**
   34 commits. Substantive development ran from 2021 to late 2021; the README's *"What's new"*
   entries stop at 18 December 2021
4. **Status**
   ⚠ Effectively **unmaintained**. The last four years produced one compatibility patch. Treat it
   as a frozen worked example, in the same category as `RAP`
5. **Credits**
   The README credits Google MediaPipe for the models and Katsuya Hyodo (`PINTO0309`) for the
   model conversion toolchain `[S1]`




## 2.2. Licence
**MIT** (`LICENSE.txt`, "Copyright (c) [2021] [geax]"). Permissive, with attribution. Copying an
algorithm out of `mediapipe_utils.py` into the project's own source is permitted provided the
copyright notice is preserved.

> **Note — the underlying models are Google's, not the author's.** The MIT licence covers this
> repository's Python. The `.blob` files in `models/` are conversions of Google's MediaPipe
> `.tflite` models and carry Google's terms. ⚠ Those terms were not read during this review.




## 2.3. Requirements
`requirements.txt` is two lines:

```text
opencv-python >= 4.5.1.48
depthai>=2.13
```

`depthai` is the Luxonis SDK, and `HandTracker.py:1–20` imports it unconditionally
(`import depthai as dai`). **Every `HandTracker*.py` file needs a physical OAK device.**

The exception is the file that matters most. `mediapipe_utils.py:1–8` imports only:

```python
import cv2
import numpy as np
from collections import namedtuple
from math import ceil, sqrt, exp, pi, floor, sin, cos, atan2, gcd
```

**No `depthai` import.** The algorithm library is hardware-independent and runs on any machine
with OpenCV and NumPy. `FPS.py` is likewise plain OpenCV.

> **Decision support.** This is what makes the repository useful despite the hardware. The
> algorithms can be read, executed and unit-tested on the team's laptops today, with no camera and
> no purchase — see [`DHR_S9`](#9-running-it).




## 2.4. Hardware, and Why It Is Rejected
The OAK family is a stereo-depth camera with an on-board Intel MyriadX VPU. Its genuine advantages
are visible in the code: neural inference runs on the device, the host receives *"~2kB/frame for 2
hands"* in Edge mode `[S1]`, and the `-xyz` flag returns the wrist's true metric position in the
camera's coordinate system.

That last capability is exactly the *"depth perception"* item [`SCR`](../../plan/scribbles.md)
lists, delivered properly. It is still rejected, for the reason
[`ARC_S7.4`](../../plan/ARC_architecture.md#75-p4p5--depth-and-glasses-as-roadmap-items) gives:
requiring a depth camera converts the product from *"any device with a camera"* into *"any device
with **this** camera"*, and that is a direct attack on the C1 scalability score, before considering
procurement inside a four-day window.

---





# 3. REPOSITORY MAP
## 3.1. File Inventory
```text
ref_repo/depthai-hand-tracker/
├── DHR_depthai_report.md                          — this document (tracked in git)
└── depthai_hand_tracker/                          — the clone (git-ignored)
    ├── mediapipe_utils.py             46 KB   ★ THE FILE. Pure NumPy, no depthai
    ├── HandTracker.py                 34 KB     Host mode, no body pre-focusing
    ├── HandTrackerEdge.py             26 KB     Edge mode
    ├── HandTrackerBpf.py              46 KB     Host mode + Body Pre Focusing
    ├── HandTrackerBpfEdge.py          29 KB     Edge mode + Body Pre Focusing
    ├── HandTrackerRenderer.py         11 KB     OpenCV drawing; replaceable
    ├── FPS.py                        1.3 KB     Rolling-window frame-rate meter
    ├── demo.py / demo_bpf.py         ~5 KB      CLI entry points
    ├── template_manager_script_*.py            Device-side scripts, Edge mode only
    ├── models/                        67 MB     .blob models + conversion scripts
    ├── custom_models/                          Palm-detection post-processing blob
    ├── examples/3d_visualization/              Open3d + smoothing filters
    ├── examples/remote_control/                Hand poses → device control
    └── README.md                      32 KB     Unusually good; a design document
```




## 3.2. What Is Worth Reading, and What Is Not
1. **`mediapipe_utils.py`** · *Verdict:* **Read all of it**
   *Reason:* The MediaPipe pipeline in Python. Hardware-free
2. **`HandTracker.py`, `next_frame()`** · *Verdict:* **Read `:487–643`**
   *Reason:* The tracking state machine — [`DHR_S5`](#5-the-tracking-logic-worth-porting)
3. **`HandTrackerBpf.py`, `BodyPreFocusing`** · *Verdict:* Read the class, skip the plumbing
   *Reason:* The distance strategy — [`DHR_S6`](#6-body-pre-focusing)
4. **`FPS.py`** · *Verdict:* Read; it is 40 lines
   *Reason:* A `deque`-based rolling frame-rate meter, copyable as-is
5. **`README.md`** · *Verdict:* **Read the first third**
   *Reason:* The best plain-English account of MediaPipe's tracking trade-offs in any of the four
   repositories, written by someone who measured them
6. **`HandTrackerEdge.py`, `HandTrackerBpfEdge.py`** · *Verdict:* Skip
   *Reason:* Splits the pipeline across the host/device boundary. Meaningless without an OAK
7. **`template_manager_script_*.py`** · *Verdict:* Skip
   *Reason:* ~100 KB of scripts executed on the VPU. Device-specific
8. **`models/`, `custom_models/`** · *Verdict:* Skip the binaries, skim the scripts
   *Reason:* `convert_models.sh` documents which MediaPipe model versions are in use
9. **`examples/`** · *Verdict:* Skim `3d_visualization`
   *Reason:* Demonstrates smoothing filters over landmark streams, which the project will need

---





# 4. `mediapipe_utils.py` — MEDIAPIPE IN NUMPY
The single most useful file in the repository. It re-implements, in NumPy, the calculators
`MPR_S4` describes in C++. Where the author ported a MediaPipe node he pasted the original
`.pbtxt` into a comment above his code, which makes the file a **side-by-side translation** of
Google's graph.




## 4.1. The Function Inventory
1. **`generate_anchors` / `generate_handtracker_anchors`** · *Lines:* `91–168`
   *Ports:* `SsdAnchorsCalculator`
   *Note:* Builds the 2016-anchor grid from `num_layers`, `min_scale`, `max_scale` and the stride
   list — the same constants cited in
   [`MPR_S4.2`](../google-mediapipe/MPR_mediapipe_report.md)
2. **`decode_bboxes`** · *Lines:* `169–284`
   *Ports:* `TensorsToDetectionsCalculator`
   *Note:* Sigmoid over raw scores, anchor-relative box decode, 7 keypoints per detection.
   `best_only` short-circuits when a single hand is wanted
3. **`non_max_suppression`** · *Lines:* `285–311`
   *Ports:* `NonMaxSuppressionCalculator`
   *Note:* Delegates to `cv2.dnn.NMSBoxes`, with a version guard for the OpenCV 4.5.4 output-format
   change — a small, honest piece of engineering
4. **`detections_to_rect`** · *Lines:* `319–350`
   *Ports:* `DetectionsToRectsCalculator`
   *Note:* Derives the palm's rotation from two of the seven detection keypoints
5. **`rect_transformation`** · *Lines:* `366–409`
   *Ports:* `RectTransformationCalculator`
   *Note:* **See [`DHR_S4.2`](#42-a-deliberate-deviation-from-google)**
6. **`hand_landmarks_to_rect`** · *Lines:* `410–446`
   *Ports:* `HandLandmarksToRectCalculator`
   *Note:* The next-frame ROI, from landmarks — [`DHR_S4.3`](#43-the-next-frame-roi-in-full)
7. **`warp_rect_img`** · *Lines:* `447–452`
   *Ports:* `ImageCroppingCalculator` + rotation
   *Note:* Three points and `cv2.getAffineTransform`. Four lines
8. **`HandRegion`** · *Lines:* `10–51`
   *Ports:* The task's result type
   *Note:* A documented per-hand record: detection score and box, rotated-rect geometry, landmark
   score, three landmark representations, handedness, `xyz`, gesture
9. **`HandednessAverage`** · *Lines:* `53–70`
   *Ports:* Nothing — **the author's own addition**
   *Note:* [`DHR_S5.3`](#53-handedness-averaging)
10. **`recognize_gesture`** · *Lines:* `512–574`
    *Ports:* Nothing — the author's own
    *Note:* [`DHR_S7`](#7-the-rule-based-gesture-recogniser)




## 4.2. A Deliberate Deviation From Google
`rect_transformation` carries this comment (`mediapipe_utils.py:366–388`), quoting Google's
`palm_detection_detection_to_roi.pbtxt` and then departing from it:

> *"IMHO 2.9 is better than 2.6. With 2.6, it may happen that finger tips stay outside of the
> bouding rotated rectangle"* — sic.

```python
scale_x = 2.9
scale_y = 2.9
shift_x = 0
shift_y = -0.5
```

Google's value is **2.6** (`hand_detector_graph.cc:137–138`). The author uses **2.9**.

> **Note — a documented, reasoned disagreement with the library authors, from someone running the
> pipeline daily.** It is not evidence that 2.6 is wrong; it is evidence that the constant is
> tunable and that the failure mode of too-small is *fingertips falling outside the crop*. Since
> fingertips are where sign language lives, this is worth knowing. The project does not control
> this constant when using the Tasks API — it is compiled into the graph — but it explains a class
> of failure the team may observe, and it belongs in the debugging notes rather than in the code.




## 4.3. The Next-Frame ROI, in Full
`hand_landmarks_to_rect` (`:410–446`) is the clearest available statement of how MediaPipe
predicts where a hand will be:

1. **Rotation** — from the wrist (landmark 0) to a weighted centre of the index, middle and ring
   MCP joints: `0.25 * (lm[5] + lm[13]) + 0.5 * lm[9]`. The hand's own axis, not the image's
2. **Bounding subset** — only twelve landmarks are used: `[0, 1, 2, 3, 5, 6, 9, 10, 13, 14, 17,
   18]`. **Fingertips are excluded**, so a pointing finger does not stretch the box
3. **Rotated extent** — landmarks are projected into the rotated frame, the extent measured there,
   and the centre projected back
4. **Expansion** — `2 * max(width, height)`, squared
5. **Shift** — `0.1 * height` along the rotated axis

Steps 4 and 5 are Google's `scale 2.0` and `shift_y −0.1` from
`hand_landmarks_detector_graph.cc:144–151`, arrived at independently and matching exactly. That
agreement is a useful cross-check on both readings.

---





# 5. THE TRACKING LOGIC WORTH PORTING
`HandTracker.next_frame()`, `HandTracker.py:487–643`. This is the application-layer state machine
that MediaPipe's Tasks API keeps inside its graph and does not expose. Every item below is a gap
named in
[`MPR_S11.2`](../google-mediapipe/MPR_mediapipe_report.md#112-what-the-project-must-build-on-top).




## 5.1. Detect Versus Track
```python
if self.use_previous_landmarks:
    self.hands = self.hands_from_landmarks     # no palm detection this frame
else:
    inference = self.q_pd_out.get()            # run the palm detector
    hands = self.pd_postprocess(inference)
```

`use_previous_landmarks` is set at the end of each frame (`:611–620`):

```python
self.use_previous_landmarks = True
if nb_hands == 0:
    self.use_previous_landmarks = False
elif not self.solo and nb_hands == 1:
    if self.single_hand_count >= self.single_hand_tolerance_thresh:
        self.use_previous_landmarks = False
        self.single_hand_count = 0
```

Three sentences, and they encode the whole policy: track while there are hands; fall back to
detection when there are none; and in two-hand mode, fall back periodically when only one hand has
been seen for a while.




## 5.2. The Single-Hand Tolerance Threshold
This is the answer to the pathology in
[`MPR_S4.4.2`](../google-mediapipe/MPR_mediapipe_report.md#442-the-num_hands--2-pathology), and
the README states the problem better than any Google document does `[S1]`:

> *"What happens if the user shows only one hand in Duo mode? Well in that case, we need to check
> in the following frames if a second hand will appear/reappear, and to do that we have to call the
> hand detection, which is a slow operation. If hand detection is run on every frame (until a
> second hand appear), the FPS drop is significant."*

The fix is one counter with a default of **10 frames** (`demo.py:38–39`,
`HandTracker.py:82`). The README's tuning advice is explicit: near `0` when two hands are expected
almost always; **10 to 30** when a second hand is occasional; and *"if the value is too high, the
delay between the appearance of the second hand and its actual detection may feel too long to be
comfortable"* `[S1]`.

> **Decision support.** Sign language sits in the difficult middle of that range: two hands are
> common, one hand is common, and the transition between them is *linguistically meaningful*. The
> counter is not free — it buys frame rate with detection latency on the second hand. The value
> must be measured against the chosen vocabulary rather than guessed. See
> [`ARC_S6.5`](../../plan/ARC_architecture.md#65-perception-engineering-rules).




## 5.3. Handedness Averaging
`HandednessAverage`, `mediapipe_utils.py:53–70`. The docstring is the argument:

> *"Handedness inferred by the landmark model is not perfect. For certain poses, it is not rare
> that the model thinks that a right hand is a left hand (or vice versa). Instead of using the last
> inferred handedness, we prefer to use the average of the inferred handedness on the last frames.
> This gives more robustness."*

The implementation is a running mean over the hand's tracked lifetime, reset whenever tracking
breaks or the hand count changes (`HandTracker.py:588–593`). It is roughly ten lines.

> **Decision support — this is not an optimisation, it is a correctness fix.**
> [`ARC_S3.2`](../../plan/ARC_architecture.md#32-the-landmark-budget) puts handedness in the
> landmark budget because *"dominant vs non-dominant hand carry different grammatical roles"*. A
> per-frame flip is therefore a **grammatical** error in the output, not a rendering glitch. The
> averaging is cheap, it is well understood, and there is no reason not to do it from the first
> commit. Note the design consequence: an averaged handedness needs a stable hand identity across
> frames, which MediaPipe does not provide — so this and item
> [`DHR_S5.5`](#55-same-handedness-suppression) must be built together.




## 5.4. Duplicate-Hand Suppression by Distance
`HandTracker.py:568–579`. Two tracked hands whose rotated-rectangle centres are closer than **five
pixels** are collapsed, keeping the higher landmark score:

> *"Check that 2 detected hands do not correspond to the same hand in the image. That may happen
> when one hand in the image cross another one."*

MediaPipe solves the same problem more carefully, with IoU plus landmark distances normalised by
hand size — [`MPR_S4.4.3`](../google-mediapipe/MPR_mediapipe_report.md#44-the-tracking-loop). The
five-pixel constant here is cruder and resolution-dependent. The point worth carrying is that
**crossing hands is a named failure mode that two independent implementations both had to handle**,
and signing crosses hands constantly.




## 5.5. Same-Handedness Suppression
`HandTracker.py:595–599`:

```python
if not self.solo and nb_hands == 2 and \
        (self.hands[0].handedness - 0.5) * (self.hands[1].handedness - 0.5) > 0:
    self.hands = [self.hands[0]]   # keep the higher score
```

Two hands classified with the same handedness cannot both be right, so one is dropped. The README
is candid about why this is needed: *"In case 2 hands with the same handedness are detected (e.g. 2
left hands, the model may be wrong :-)"* `[S1]`.

> **Warning — for sign language this rule is a trade, not a fix.** Dropping a hand is a *worse*
> failure than mislabelling one, because a two-handed sign observed with one hand is
> unrecognisable. The project should prefer to **keep both hands and mark the handedness as
> uncertain**, which is the behaviour
> [`ARC_S9`](../../plan/ARC_architecture.md#9-decisions) decision 8 requires anyway: report the
> uncertainty rather than resolve it silently.




## 5.6. Landmark-Score Filtering
`HandTracker.py:560`:

```python
self.hands = [h for h in self.hands if h.lm_score > self.lm_score_thresh]
```

Default `lm_score_thresh = 0.5` (`HandTracker.py:73`). Same gate, same threshold, same "drop
rather than weight" behaviour as MediaPipe's presence gate and Apple's confidence guard. Three
independent implementations, one rule.




## 5.7. Instrumentation
`HandTracker.exit()`, `:645–662`, prints on shutdown:

- global FPS and total frame count;
- frames with no hand, as a count and a percentage;
- frames on which palm detection ran, as a count and a percentage;
- frames with landmark inference, **split by whether the ROI came from detection or from the
  previous frame's landmarks**;
- average landmark inferences per frame;
- failed landmark inferences, as a count and a percentage;
- palm-detection and landmark round-trip times in milliseconds.

> **Decision support.** That list is very close to the perception half of the metric set in
> [`ARC_S8.4`](../../plan/ARC_architecture.md#84-proposed-metric-set), and it costs a handful of
> counters. In particular, *"frames on which palm detection ran, as a percentage"* is the single
> number that reveals the `num_hands = 2` pathology, and *"failed landmark inferences"* is the
> perception-layer analogue of refusal rate. Instrument from the first commit, exactly as
> `D3_p32` requires for the agent layer.

---





# 6. BODY PRE FOCUSING
`BodyPreFocusing`, `mediapipe_utils.py:634–900`, used by `HandTrackerBpf.py`.

The problem, stated in the README `[S1]`:

> *"The palm detector model from Google Mediapipe was trained to detect hands that are less than 2
> meters away from the camera. So if the person stands further away, his hands may not be detected.
> And the padding used to make the image square contributes even more to the problem."*

The solution: run a **body pose model** first — MoveNet Single Pose, chosen over BlazePose *"because
of its simpler architecture"* `[S1]` — take the wrist keypoints, crop a zone around them, and feed
only that crop to the palm detector.

Four policies select the zone, via `body_pre_focusing`: `left`, `right`, `higher` (the raised
hand) and `group` (a zone containing both). A separate `hands_up_only` flag considers only hands
whose wrist keypoint is above the elbow, *"meaning in practice that the hands are raised"*.

Two consequences are directly relevant:

1. **Handedness from the body, not from the hand.** When body pre-focusing is active, handedness
   comes from *which* wrist keypoint the zone was built around — *"which is much more reliable than
   the handedness inferred by the landmark model, especially when the body is far from the
   camera"* `[S1]`. This is the same mechanism `HolisticLandmarker` uses, and it is strictly better
   than classifying handedness from a hand crop
2. **The body model also stops running once a hand is tracked.** *"Once a hand has been
   successfully detected, the body pose network, like the palm detection network, stays inactive on
   the following frames, as long as the hand landmark regressor can keep track of the hand"*
   `[S1]`. The expensive stage is a rescue path, never a per-frame cost

> **Decision support — `hands_up_only` is a cheap segmentation prior.** The author adopted it to
> suppress false gesture recognition when the hand is at rest: *"when we want to recognize hand
> gestures, the arm is generally folded and the hand up"*. Sign language has the same structure —
> signing happens in a defined space in front of the torso, and hands at rest are not signing. A
> hands-in-signing-space test is already stage ④ of
> [`ARC_S6.1`](../../plan/ARC_architecture.md#61-pipeline); this repository is evidence that the
> heuristic works in practice, from someone who shipped it.

The README also notes the honest limitation: *"the further the distance, the more difficult the
tracking is, because fast moves appear fuzzier"*, with the recommendation that the arm stay still
during a pose. For a signer at conversational distance this is not binding, but it sets the
expectation for a demo across a room.

---





# 7. THE RULE-BASED GESTURE RECOGNISER
`recognize_gesture`, `mediapipe_utils.py:512–574`. Worth reading precisely because it is so small,
and because its limits are the project's argument for building something else.

**How it works.** Each finger is reduced to a state in `{open, closed, unknown}` by comparing the
`y` coordinates of its three joints in the *rotated, normalised* landmark frame:

```python
if lm[8][1] < lm[7][1] < lm[6][1]:   index_state = 1     # open
elif lm[6][1] < lm[8][1]:            index_state = 0     # closed
else:                                index_state = -1    # unknown
```

The thumb is handled separately, by summing three joint angles and comparing a distance ratio:
`angle0 + angle1 + angle2 > 460 and d(3,5) / d(2,3) > 1.2`. The five states are then matched
against a lookup of eight gestures: `FIVE`, `FIST`, `OK`, `PEACE`, `ONE`, `TWO`, `THREE`, `FOUR`.
Anything unmatched returns `None`.

Three things to take from it:

1. **An explicit `unknown` state per finger, and `None` for the gesture.** The function refuses
   rather than guessing — the same invariant as
   [`ARC_S9`](../../plan/ARC_architecture.md#9-decisions) decision 8, in twelve lines
2. **Cheap arithmetic beats a model where geometry answers the question** — Apple's lesson L12,
   [`APS_S5`](../../doc/APS_apple_synthesis.md#5-the-twelve-lessons), independently confirmed
3. **It is a ceiling, not a floor.** Eight static handshapes, no movement, no orientation, no
   location, no two-handed relationship, no non-manual marking. Sign language uses all of those

> **Warning — the parameters this approach cannot see.** Sign language is standardly analysed in
> terms of handshape, orientation, location, movement and non-manual markers. `recognize_gesture`
> reads **handshape only**, from a single frame. Describing a system of this kind as sign-language
> recognition would be exactly the capability overstatement
> [`CLD_S5.2`](../../CLAUDE.md#52-honesty-about-the-product) forbids. It is, however, a fair and
> nearly free **baseline** to measure the trained classifier against, in the same spirit as
> [`ARC_S7.5`](../../plan/ARC_architecture.md#74-p2--rationale-for-building-it-regardless).

---





# 8. WHAT THE REPOSITORY DOES NOT DO
1. **No face and no body landmarks in the output.** MoveNet is used only to crop; its keypoints
   are not part of the hand result
2. **No temporal model.** Tracking is region prediction, exactly as in `RMP`
3. **No sign recognition.** Eight static handshapes
4. **No stable hand identity.** Handedness averaging resets whenever the hand count changes
5. **No tests.** There is no test suite in the repository
6. **No packaging.** No `setup.py`, no module structure; the scripts are run from the directory
7. **Hard dependency on OAK hardware** for everything except `mediapipe_utils.py`, `FPS.py` and
   the renderer
8. **Models pinned to 2021 MediaPipe.** `full`, `lite`, `sparse` and a 2020 `0.8.0` variant.
   Google has since shipped newer weights, which this repository has not tracked
9. **⚠ Unmaintained.** One commit since 2021, and that a NumPy compatibility fix
10. **Duo mode caps at two hands.** Not a limitation for signing, but it is not a general
    multi-person tracker

---





# 9. RUNNING IT
## 9.1. The Demo — Not Possible
`demo.py` and `demo_bpf.py` construct `dai.Device()` on the first line of tracker setup. **Without
an OAK camera they cannot run.** No emulator is provided.




## 9.2. The Algorithms — Possible Today
`mediapipe_utils.py` imports only `cv2`, `numpy` and the standard library. Its functions can be
imported and exercised on any machine:

```python
import sys; sys.path.append("ref_repo/depthai-hand-tracker/depthai_hand_tracker")
import mediapipe_utils as mpu

anchors = mpu.generate_handtracker_anchors(192, 192)
print(anchors.shape)          # expect (2016, 4) — the anchor grid from MPR_S4.2
```

⚠ **Not executed during this review.** The expectation of `(2016, 4)` is derived from the anchor
constants read in both repositories, not from a run. Confirming it is a five-minute task and a
genuinely useful one: it validates the reading of `MPR_S4.2` against an independent
implementation.

> **Note — this stays out of `src/`.** Reading and running a reference file in place is fine.
> Importing from `ref_repo/` in project code is not: the directory is git-ignored, so a judge
> cloning the submission would get an `ImportError`. Anything the project keeps is re-implemented
> in `src/`, with attribution, under the MIT notice.

---





# 10. RELEVANCE TO SIMPLYNEXT
## 10.1. Lessons to Carry Across
| #  | Lesson                                                                               |
| :- | :----------------------------------------------------------------------------------- |
| D1 | **Rate-limit the expensive detector with a tolerance counter**, not with hope        |
| D2 | **Average handedness over a hand's tracked lifetime.** One frame is not evidence     |
| D3 | **Crossing hands is a named failure mode.** Detect duplicates explicitly             |
| D4 | **Prefer "uncertain" to dropping a hand** — the opposite of this repository's choice |
| D5 | **A body model can rescue a hand detector** that was trained for close range         |
| D6 | **Hands at rest are not signing.** `hands_up_only` is a free segmentation prior      |
| D7 | **Count everything and print it on exit.** Perception needs metrics too              |
| D8 | **Geometry beats a model** where geometry answers the question                       |
| D9 | **Constants are tunable, and the author disagreed with Google's** — record why       |




## 10.2. Port Table
1. **`HandednessAverage`** · *Port:* Direct — ~10 lines of Python
   *Where:* Pipeline stage ③, [`ARC_S6.1`](../../plan/ARC_architecture.md#61-pipeline)
2. **`single_hand_tolerance_thresh`** · *Port:* Direct, as a counter around the Tasks API call
   *Where:* Stage ②. Note the Tasks API hides the detector, so the counter must switch `num_hands`
   or accept the cost
3. **Duplicate-hand suppression** · *Port:* Adapt — use IoU normalised by hand size, per `RMP`,
   not five pixels
   *Where:* Stage ③
4. **`hands_up_only`** · *Port:* Adapt — wrist-above-elbow becomes hands-in-signing-space
   *Where:* Stage ④, the segmenter
5. **`FPS.py`** · *Port:* Direct — a `deque` of timestamps
   *Where:* Instrumentation
6. **`HandTracker.exit()` statistics** · *Port:* Direct in spirit
   *Where:* `EVL`, the evaluation protocol
7. **`recognize_gesture`** · *Port:* As a **baseline only**, clearly labelled
   *Where:* [`ARC_S7.5`](../../plan/ARC_architecture.md#74-p2--rationale-for-building-it-regardless)
8. **`mediapipe_utils.py` algorithms** · *Port:* **Do not port**
   *Where:* Nowhere. The Tasks API performs these inside the graph. Read them to understand what
   the graph is doing; re-implementing them would be building MediaPipe badly




## 10.3. What Not to Take
1. **The hardware.** [`ARC_S7.1`](../../plan/ARC_architecture.md#71-comparison-table), `P4`
2. **Edge mode and the device scripts.** No transferable content
3. **The `.blob` models.** Wrong format, wrong hardware, and 2021 weights
4. **Same-handedness dropping.** Replace with an uncertainty flag —
   [`DHR_S5.5`](#55-same-handedness-suppression)
5. **The five-pixel duplicate threshold.** Resolution-dependent
6. **Any dependency on `ref_repo/`.** The directory is git-ignored —
   [`DHR_S9.2`](#92-the-algorithms--possible-today)

---





# 11. SOURCES
1. **`[S1]`**
   *Source:* `ref_repo/depthai-hand-tracker/depthai_hand_tracker/README.md` at `9773123` — the
   author's design notes on Solo/Duo modes, Host/Edge modes, Body Pre Focusing, frame-rate
   behaviour and model provenance
   *Reliability:* ⚠ A single practitioner's observations, not a benchmark. Directionally
   trustworthy because it is written by the person who implemented and measured the pipeline;
   no figures in it are independently reproduced
2. **`[S2]`**
   *Source:* `ref_repo/depthai-hand-tracker/depthai_hand_tracker/LICENSE.txt` — MIT,
   "Copyright (c) [2021] [geax]"
   *Reliability:* Primary
3. **`[S3]`**
   *Source:* The clone itself at `9773123` (2023-01-14). All `file:line` citations resolve
   against this commit
   *Reliability:* Primary
4. **`[S4]`**
   *Source:* [`MPR`](../google-mediapipe/MPR_mediapipe_report.md) — the corresponding constants
   and graph wiring in Google's own implementation
   *Reliability:* Cross-check against primary source

---





# 12. CHANGE LOG
1. **2026-08-30** · *Author:* Claude (Opus 5)
   *Change:* Created from a read of `mediapipe_utils.py`, `HandTracker.next_frame()`, the
   `BodyPreFocusing` class, `recognize_gesture`, `FPS.py`, the demo entry points and the README.
   Recorded the single-hand tolerance counter as the fix for the `num_hands = 2` pathology in
   [`MPR_S4.4.2`](../google-mediapipe/MPR_mediapipe_report.md), the handedness-averaging
   correctness fix, and the author's documented 2.9-versus-2.6 deviation from Google's ROI scale.
