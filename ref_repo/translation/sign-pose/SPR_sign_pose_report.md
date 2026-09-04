**POSE-FORMAT — FULL REPOSITORY REPORT**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field                   | Value                                                 |
| :---------------------- | :---------------------------------------------------- |
| **Code**                | `SPR`                                                 |
| **Status**              | Live                                                  |
| **Last reviewed**       | 2026-09-04                                            |
| **Source of truth for** | Analysis of the `pose-format` reference clone         |
| **Parent**              | [`RIX_S2.1`](../../../ref_index.md#21-live-documents) |
| **Short version**       | [`SPS`](../../../doc/SPS_sign_pose_synthesis.md)      |
| **Subject**             | `RSP` — `translation/sign-pose/pose/` at `7a36fcf`    |

**For the team.** `sign-language-processing/pose` is the field's **standard pose container and
manipulation library**: MIT-licensed, `pip install pose-format`, three runtime dependencies, and
actively maintained. It is the second candidate dependency in `ref_repo/` after `RMP`, and it
already implements the body-relative normalisation that
[`ARC_S4.3`](../../../plan/ARC_architecture.md#43-recommended-representation) specifies. Two
sections decide how it is used: [`SPR_S5`](#5-the-functions-worth-the-dependency) is what it gives
the project for free, and [`SPR_S6`](#6-the-mediapipe-collision) is the one part of it the project
must **not** adopt.

**For the assistant.** `RSP` is a **candidate dependency**, unlike `RSL`, `RSA` and `ROP`. Its data
structures may be used; its **pose-estimation path may not**, because it is built on the legacy
`mp.solutions` API and pins `mediapipe<0.10.30` — a direct collision with
[`ARC_S6.5`](../../../plan/ARC_architecture.md#65-perception-engineering-rules) rule 1. State that
distinction whenever the library comes up. Nothing inside
`ref_repo/translation/sign-pose/pose/` may be edited; it is an unmodified clone, excluded from
version control.

</details>

---





# 1. EXECUTIVE SUMMARY
## 1.1. What This Repository Is
`ref_repo/translation/sign-pose/pose/` is **`pose-format`**, described by its own README as *"a
complete toolkit for working with poses"* for developers *"interested in Sign Language Processing
(SLP)"*, comprising *"a file format with Python and Javascript readers and writers"* `[S1]`.

It is three things at once:

1. A **binary file format** — `.pose` — for pose sequences of arbitrary type, arbitrary numbers of
   people and indefinite length, specified in `docs/specs/v0.1.md` `[S2]`
2. A **Python library** for reading, normalising, augmenting, interpolating and visualising those
   sequences, with NumPy, PyTorch and TensorFlow back-ends
3. A set of **importers** that map the output of MediaPipe Holistic, OpenPose (137- and
   135-keypoint), AlphaPose WholeBody and MMPose WholeBody into one common representation

It is authored by Amit Moryossef and maintained by the `sign-language-processing` organisation —
the same people behind `RSS` ([`SSR`](../spoken-to-signed/SSR_spoken_to_signed_report.md)) and
`RLT` ([`LTR`](../signlang-literature/LTR_signlang_literature_report.md)). Those three repositories
form one coherent stack, and that is part of the argument for adopting this one.




## 1.2. Why It Matters to SimplyNext
Unlike every other repository in `ref_repo/translation/`, this one is **usable as shipped**.

1. **It implements the project's normalisation** · *Use:*
   [`ARC_S4.3`](../../../plan/ARC_architecture.md#43-recommended-representation) step 2 specifies
   *"origin at mid-shoulder, scale by shoulder width"*. `Pose.normalize()` does exactly this, and
   selects the shoulder points automatically for six pose formats —
   [`SPR_S5.1`](#51-normalisation)
2. **It supplies the augmentation the small-dataset problem needs** · *Use:* `augment2d()` and
   three frame-dropout variants, on a representation the project already has —
   [`SPR_S5.3`](#53-augmentation)
3. **It fixes a MediaPipe failure the project did not know about** · *Use:* `correct_wrists()`
   substitutes the *body* wrist where the *hand* wrist has zero confidence —
   [`SPR_S5.4`](#54-wrist-correction)
4. **It is the interchange format the field uses** · *Use:* `RSS` consumes `.pose` files; so does
   the `sign.mt` production system. Adopting it keeps both directions of the project on one
   representation
5. **It carries one trap** · *Use:* Its own MediaPipe path is the legacy API —
   [`SPR_S6`](#6-the-mediapipe-collision)

Against the four MVP steps in [`SCR`](../../../plan/scribbles.md):

1. **1. Isolate the subject** — not addressed; the format supports multiple people, the library
   does not choose between them
2. **2. Track many points** — it does not track. It **stores and reduces** what a tracker produced
3. **3. Points → skeleton** — this is precisely its subject, and
   [`SPR_S5`](#5-the-functions-worth-the-dependency) is the list of what it already does
4. **4. Skeleton → conversational text** — not attempted. No models, no classifier, no translation




## 1.3. Summary
A `.pose` file is a header plus a body. The header names the components (`POSE_LANDMARKS`,
`FACE_LANDMARKS`, `LEFT_HAND_LANDMARKS`, …), the points inside each, the limbs connecting them and
their colours. The body is a dense array of shape `(frames, people, points, dimensions)` with a
parallel confidence array of shape `(frames, people, points)`. Everything else in the library is a
transformation of that pair: normalise, reduce, augment, interpolate, filter, draw. Because
confidence is a first-class parallel array rather than a fourth coordinate, *absence* is
representable — and several of the library's most useful functions exist purely to handle it.

---





# 2. PROVENANCE, LICENCE AND REQUIREMENTS
## 2.1. Provenance
1. **Publisher**
   Amit Moryossef, with Mathias Müller and Rebecka Fahrni credited as authors in `pyproject.toml`;
   published under the `sign-language-processing` organisation. Remote:
   `https://github.com/sign-language-processing/pose.git`
2. **Clone state**
   `7a36fcf`, **2026-07-23**, *"Fix `PoseHeaderCache` race under concurrent `Pose.read` (#239)"*
3. **Version**
   `v0.14.1`, declared in `src/python/pyproject.toml:4` `[S3]`
4. **Maintenance status**
   **Active and healthy** — the only repository in `ref_repo/translation/` of which this is true.
   383 commits, 20 contributors, and the three most recent commits are a concurrency bug fix, a
   documentation dependency bump and a new MMPose estimator, all dated 2026-07
5. **Test coverage**
   32 test files under `src/python`
6. **Breadth**
   Python is the complete implementation; `src/js` holds a JavaScript reader and a
   `<pose-viewer>` web component; `src/dart` is present but empty in this clone




## 2.2. Licence
`LICENSE.txt`, first lines: *"MIT License / Copyright (c) 2021 Amit Moryossef"* `[S4]`.

MIT permits commercial use, modification, distribution and sublicensing, requiring only that the
copyright notice and licence text travel with substantial portions of the software. There is no
non-commercial clause, no derivative-ownership clause and no field-of-use restriction.

> **Note — this is one of only three permissive licences in `ref_repo/`**, alongside `RMP`
> (Apache 2.0), `RDH` (MIT), `RSS` (MIT) and `RST` (Apache 2.0). It is the reason `RSP` can be a
> dependency where `RSL`, `RSA` and `ROP` cannot. Attribution is still required and belongs in the
> submission's `README`.




## 2.3. Requirements
`src/python/pyproject.toml:12-17` `[S3]`:

```toml
dependencies = [
    "numpy",
    "tqdm",
    "simple-video-utils",
]
requires-python = ">= 3.8"
```

**Three runtime dependencies, none of them heavy.** No PyTorch, no TensorFlow, no MediaPipe, no
OpenCV in the base install. Every heavier capability is an extra:

| Extra       | Pulls in                                     | Needed for                |
| :---------- | :------------------------------------------- | :------------------------ |
| `mediapipe` | `mediapipe<0.10.30`                          | Its own video → pose path |
| `mmpose`    | `mmcv`, `mmengine`, `mmdet`, `mmpose`        | The MMPose importer       |
| `dev`       | `pytest`, `torch`, `tensorflow`, `opencv`, … | Tests                     |

Set against `RSL`'s `torch==1.9.0+cu102` and eight GPUs, a three-dependency pure-Python-plus-NumPy
package is a different order of commitment entirely. It satisfies `D3_p42`'s
`requirements.txt` constraint without argument.

---





# 3. REPOSITORY MAP
```text
ref_repo/translation/sign-pose/
├── SPR_sign_pose_report.md                    — this document (tracked in git)
└── pose/                                      — the clone (git-ignored)
    ├── src/python/pose_format/
    │   ├── pose.py                   Pose: normalize, normalize_distribution, get_components
    │   ├── pose_body.py              The array pair: augment2d, interpolate, frame_dropout
    │   ├── pose_header.py            Components, points, limbs, normalization_info
    │   ├── pose_visualizer.py        draw(), draw_on_video(), save_video(), save_gif()
    │   ├── numpy/ torch/ tensorflow/ Three back-ends behind one interface
    │   ├── utils/
    │   │   ├── generic.py            ← reduce_holistic, correct_wrists, pose_shoulders
    │   │   ├── holistic.py           ← the MediaPipe path. Legacy API. See SPR_S6
    │   │   ├── openpose.py, openpose_135.py, alphapose*.py, mmposewholebody.py
    │   │   └── normalization_3d.py   Plane-and-line 3D normalisation
    │   ├── bin/                      video_to_pose, videos_to_poses, visualize_pose CLIs
    │   └── tests/                    32 test files
    ├── src/js/                       Reader + <pose-viewer> web component
    ├── docs/specs/v0.1.md            ← the binary format, in one page
    └── LICENSE.txt                   MIT
```

**Worth reading:** `docs/specs/v0.1.md` (the whole format), `pose.py:104-142` (`normalize`),
`utils/generic.py:151-230` (shoulder selection and normalisation info),
`utils/generic.py:369-435` (`correct_wrist` and `reduce_holistic`), `pose_body.py:380`
(`augment2d`), and `utils/holistic.py:18-33` (the collision).

**Not worth reading:** the TensorFlow back-end (the project has no TensorFlow), `src/js` and
`src/dart` (no browser deliverable is planned), and `utils/siren.py`.

---





# 4. THE DATA MODEL
## 4.1. Header and Body
From `docs/specs/v0.1.md` `[S2]`, the header carries a version, a width, height and depth, and then
per component: a name, a format string, and counts of points, limbs and colours, followed by point
names, limb index pairs and RGB triples. The body carries fps, frame count, people count, then the
coordinates, then the confidences.

Three consequences of that shape are worth stating:

1. **Points are named, not indexed.** `pose_header.get_point_index("POSE_LANDMARKS",
   "LEFT_WRIST")` resolves a name to a position. Code written against names survives a change of
   pose estimator, which is exactly the boundary discipline
   [`APR_S6.6`](../../tracking/apple/APR_apple_report.md) recommends
2. **Confidence is a separate array**, of shape `(frames, people, points)`, not a fourth coordinate.
   A missing point is `confidence == 0`, and the visualiser draws only where confidence exceeds
   zero. Absence is therefore a first-class state, not a sentinel value
3. **The format is multi-person from the ground up.** The people axis is real. ⚠ The library
   provides no logic for *choosing* a person, so
   [`ARC_S2`](../../../plan/ARC_architecture.md#2-step-1--isolating-the-subject) is unaffected

> **Warning — a known format defect.** `docs/specs/v0.1.md` annotates the body's frame count field
> with the comment `# THIS IS A PROBLEM`, because it is an `unsigned short` and therefore caps at
> 65,535 frames — roughly 44 minutes at 25 fps `[S2]`. Irrelevant at utterance scale; relevant if
> the project ever stores a long recording as a single `.pose` file.




## 4.2. Back-ends
`Pose.read(buffer, NumPyPoseBody | TorchPoseBody | TensorflowPoseBody)` selects the array library,
and `pose.torch()` / `pose.tensorflow()` convert in place `[S1]`. The project's classifier will
want tensors; the perception layer wants NumPy. One object serves both without a conversion layer
of the project's own.

---





# 5. THE FUNCTIONS WORTH THE DEPENDENCY
Each of the following is something
[`ARC`](../../../plan/ARC_architecture.md) currently specifies as work to be done, and which this
library has already done.




## 5.1. Normalisation
`Pose.normalize()` at `pose.py:104-142` `[S5]`, with `pose_normalization_info()` at
`utils/generic.py:205-208`:

```python
center = ((p2s + p1s) / 2).mean(axis=(0, 1))
self.body.data -= center
mean_distance = distance_batch(p1s, p2s).mean()
scale = scale_factor / mean_distance
self.body.data = self.body.data * scale
```

Called with no arguments, it looks up the two shoulder points for the detected pose format,
translates every point so the shoulder midpoint is the origin, and scales so the mean inter-shoulder
distance is 1.

> **This is [`ARC_S4.3`](../../../plan/ARC_architecture.md#43-recommended-representation) step 2,
> verbatim.** The document specifies *"origin at mid-shoulder, scale by shoulder width"*, making
> the representation invariant to distance from the camera, to the signer's size and to where they
> stand in frame. The library does it in five lines and selects the shoulder points automatically
> for MediaPipe Holistic, OpenPose, OpenPose-135, AlphaPose-133/136 and COCO-WholeBody
> (`utils/generic.py:151-173`).

Two details matter for correctness:

1. **The centre and the scale are computed over the whole sequence**, not per frame —
   `.mean(axis=(0,1))` and `distance_batch(...).mean()`. Within one utterance the normalisation is
   a single rigid transform, so *relative motion between frames is preserved*. Per-frame
   normalisation would destroy exactly the motion signal the classifier needs
2. **⚠ This is a batch operation over a complete sequence, not a streaming one.** The project's
   stage ③ runs live, one frame at a time. It must either normalise per buffered utterance window,
   or maintain a running shoulder estimate. Neither is difficult; both must be decided rather than
   inherited

`normalize_distribution(axis=...)` provides the second scheme, zero-mean unit-variance per keypoint
and per dimension — which is the scheme
[`LTR_S5.5`](../signlang-literature/LTR_signlang_literature_report.md#55-pose-to-text) records
`ko2019neural` experimenting with.




## 5.2. Reduction
`reduce_holistic()` at `utils/generic.py:395-435` `[S6]` cuts a 543-point MediaPipe Holistic pose
down to a curated subset:

1. **Face** — from 468 mesh points to the **128 `FACEMESH_CONTOURS` points**, hard-coded in the
   source with a comment explaining that they were extracted from MediaPipe once *"to avoid
   installing mediapipe"*
2. **Body** — every `POSE_LANDMARKS` point whose name contains `EAR`, `NOSE`, `MOUTH`, `EYE`,
   `THUMB`, `PINKY`, `INDEX`, `KNEE`, `ANKLE`, `HEEL` or `FOOT_INDEX` is dropped. Of MediaPipe's 33
   pose landmarks that leaves **8**: both shoulders, elbows, wrists and hips
3. **Hands** — both hands kept whole, 21 each
4. **`POSE_WORLD_LANDMARKS`** — dropped entirely

The result is **8 + 128 + 42 = 178 points**, from 543.

> **Warning — 178 is a storage and rendering budget, not a model-input budget.** `RSS` calls
> `reduce_holistic` before *drawing* poses and stitching them
> ([`SSR_S5.2`](../spoken-to-signed/SSR_spoken_to_signed_report.md#52-the-concatenation-order)),
> where 128 face contour points make an avatar look right. A classifier is a different problem:
> `RSL` feeds **10 to 26** face points to its model
> ([`SLR_S4.1`](../slrt/SLR_slrt_report.md#41-what-every-configuration-actually-selects)) and `RSA`
> feeds **none** ([`SAR_S4`](../sam-slr/SAR_sam_slr_report.md#4-the-27-keypoint-budget)). Do not
> read `reduce_holistic`'s 128 as a recommendation for
> [`ARC_S3.2`](../../../plan/ARC_architecture.md#32-the-landmark-budget); the two budgets serve
> different consumers and the project needs both.

The body reduction, by contrast, is directly endorsable: **8 upper-body points**, dropping legs and
the redundant hand stubs that MediaPipe's pose model emits alongside the real hand model.
`pose_hide_legs()` at `utils/generic.py:80` does the leg part alone.




## 5.3. Augmentation
Two families, both operating on the array pair and therefore free of any model:

1. **`PoseBody.augment2d(rotation_std=0.2, shear_std=0.2, scale_std=0.2)`** at `pose_body.py:380`
   `[S7]` — random affine perturbation of every point. The defaults are Gaussian standard
   deviations, not bounds
2. **`frame_dropout_uniform(dropout_min=0.2, dropout_max=1.0)`**, `frame_dropout_normal(mean=0.5,
   std=0.1)` and `frame_dropout_given_percent()` at `pose.py:182-220` and `pose_body.py:553-620` —
   drop a random proportion of frames, returning both the shortened pose and the retained indices

Frame dropout is the more interesting of the two for this project, because it simulates the failure
mode the pipeline will actually have: MediaPipe returning nothing on some frames because the
presence gate rejected them —
[`MPR_S4.3.1`](../../tracking/google-mediapipe/MPR_mediapipe_report.md#431-the-presence-gate-is-a-hard-gate).
A classifier trained with frame dropout has seen gaps before.

`interpolate_fps(fps, kind='linear'|'cubic')` normalises recordings made at different frame rates
onto one time base — necessary the moment training data comes from more than one camera.




## 5.4. Wrist Correction
`correct_wrist()` at `utils/generic.py:369-387` `[S6]`:

```python
new_wrist_data = ma.where(stacked_conf == 0, body_wrist, wrist)
new_wrist_conf = ma.where(wrist_conf == 0, body_wrist_conf, wrist_conf)
```

MediaPipe Holistic emits a wrist twice: once as `POSE_LANDMARKS.LEFT_WRIST` from the pose model,
once as `LEFT_HAND_LANDMARKS.WRIST` from the hand model. When the hand model fails, its wrist has
zero confidence while the pose model's is still valid. This function substitutes the latter for the
former, per frame, per hand.

> **This is a failure mode [`ARC`](../../../plan/ARC_architecture.md) does not currently name.** It
> matters because the hand wrist is the origin of the handshape descriptor: if it collapses to
> zero, every hand landmark expressed relative to it is wrong, and the error is silent. Ten lines,
> and it should be in stage ③. Recorded as a new perception rule in
> [`ARC_S6.5`](../../../plan/ARC_architecture.md#65-perception-engineering-rules).

`normalize_hands_3d()` at `utils/generic.py:252` provides the companion operation: rotate each hand
into a canonical frame defined by a plane (`WRIST`, `PINKY_MCP`, `INDEX_FINGER_MCP`) and a line, so
that handshape becomes independent of hand orientation. That is a genuine addition to
[`ARC_S4.3`](../../../plan/ARC_architecture.md#43-recommended-representation), which keeps per-hand
world landmarks but does not canonicalise their rotation.

---





# 6. THE MEDIAPIPE COLLISION
This is the one thing about `RSP` that must not be adopted, and it is easy to adopt by accident.

`src/python/pose_format/utils/holistic.py:18-33` `[S8]`:

```python
import mediapipe as mp
...
mp_holistic = mp.solutions.holistic
...
BODY_POINTS = mp_holistic.PoseLandmark._member_names_
HAND_POINTS = mp_holistic.HandLandmark._member_names_
```

`src/python/pyproject.toml:26,33` `[S3]` pins the consequence:

```toml
mediapipe = [
    "mediapipe<0.10.30",
]
```

The library's video → pose path is built on **`mp.solutions.holistic`** — the legacy Solutions API
that [`MPS_S6`](../../../doc/MPS_mediapipe_synthesis.md#6-the-four-traps-that-will-cost-a-day)
identifies as excluded from the 1.0-line wheel by MediaPipe's own `setup.py`, and that
[`ARC_S6.5`](../../../plan/ARC_architecture.md#65-perception-engineering-rules) rule 1 forbids. The
`<0.10.30` pin is the direct evidence: the package caps MediaPipe *below* the version that removed
the API it depends on.

The README compounds it by advertising `--additional-config="model_complexity=2,
smooth_landmarks=false, refine_face_landmarks=true"` `[S1]` — all three are `mp.solutions.holistic`
constructor arguments with no counterpart in the Tasks API.

> **Warning — installing `pose-format[mediapipe]` caps the project's MediaPipe version and forces
> the forbidden API.** `video_to_pose`, `videos_to_poses` and `process_holistic()` are all on that
> path.

> **Decision — take the data structures, not the estimator.** The base install
> (`pip install pose-format`, three dependencies, no MediaPipe) contains everything in
> [`SPR_S5`](#5-the-functions-worth-the-dependency). The project runs MediaPipe Tasks itself, as
> `RST` demonstrates in
> [`STR_S5`](../sign-translator/STR_sign_translator_report.md#5-the-mediapipe-tasks-reference-implementation),
> and constructs a `Pose` object from the resulting arrays. **Never install the `mediapipe`
> extra.** Recorded in [`ARC_S9`](../../../plan/ARC_architecture.md#9-decisions).

> **Placeholder — the cost of building a `Pose` from Tasks-API output.**
> **Missing:** whether a `PoseHeader` matching the Holistic component and point names can be
> constructed from `HolisticLandmarker` / `HandLandmarker` + `PoseLandmarker` output without
> reimplementing `utils/holistic.py`'s header construction. `reduce_holistic`, `correct_wrists` and
> `pose_shoulders` all dispatch on `detect_known_pose_format`, so the header names must match
> exactly or those functions return the input unchanged — silently.
> **Update trigger:** the first working capture loop.
> **Owner:** team.

---





# 7. WHAT THE REPOSITORY DOES NOT DO
1. **It does not recognise or classify anything.** There are no models
2. **It does not track.** No temporal association, no hand identity, no handedness averaging.
   Everything in [`ARC_S6.5`](../../../plan/ARC_architecture.md#65-perception-engineering-rules)
   rules 4–7 remains the project's own work
3. **It does not segment.** No sign or utterance boundaries. `RSS` builds a crude boundary detector
   *on top of* it — [`SSR_S5.1`](../spoken-to-signed/SSR_spoken_to_signed_report.md#51-finding-the-signing-span)
4. **It does not choose a signer**, despite a real people axis
5. **It does not stream.** The API assumes a complete sequence in memory; normalisation statistics
   are computed over the whole array
6. **It provides no landmark budget for a classifier.** `reduce_holistic` targets rendering —
   [`SPR_S5.2`](#52-reduction)
7. **Its own estimator is on the forbidden API** — [`SPR_S6`](#6-the-mediapipe-collision)

---





# 8. RUNNING IT
Unlike every other repository in `ref_repo/translation/`, this one runs today, on a laptop, with no
GPU:

```bash
pip install pose-format          # numpy, tqdm, simple-video-utils. Nothing else
```

```python
from pose_format import Pose
from pose_format.utils.generic import pose_normalization_info, correct_wrists, reduce_holistic

with open("example.pose", "rb") as f:
    pose = Pose.read(f.read())

pose = correct_wrists(pose)
pose.normalize(pose_normalization_info(pose.header))
data = pose.body.data              # (frames, people, points, dims), masked
conf = pose.body.confidence        # (frames, people, points)
```

`PoseVisualizer(pose).save_video(...)` and `.draw_on_video(...)` render a skeleton over the original
footage, which is the cheapest possible debugging tool for stages ②–③ and worth wiring up on day
one.

> **Warning — do not run `video_to_pose` or `pip install pose-format[mediapipe]`.**
> [`SPR_S6`](#6-the-mediapipe-collision). The estimation step is the project's own, on the Tasks
> API.

---





# 9. RELEVANCE TO SIMPLYNEXT
## 9.1. Lessons to Carry Across
| #  | Lesson                                                                                      |
| :- | :-----------------------------------------------------------------------------------------  |
| P1 | **Name points, do not index them.** Names survive a change of pose estimator                |
| P2 | **Confidence is a parallel array, not a coordinate.** Absence becomes a representable state |
| P3 | **Normalise over the sequence, never per frame** — per-frame scaling destroys motion        |
| P4 | **The hand wrist and the body wrist are two different points**, and one of them fails       |
| P5 | **Canonicalise hand rotation** before treating handshape as a feature                       |
| P6 | **Frame dropout is the honest augmentation** for an intermittent detector                   |
| P7 | **A rendering budget is not a model budget.** 178 points to draw; 27–79 to classify         |
| P8 | **A library's defaults can contradict the project's rules.** Read the pin                   |

P8 is the transferable one. `pose-format` is well maintained, permissively licensed and exactly
right for the project — and its headline feature is on an API the project has already banned.




## 9.2. What the Project Takes
1. **The library, base install** · *Take:* `pose-format` at a pinned version, no extras ·
   *Where:* `requirements.txt`; the data structure behind stages ②–⑤
2. **`normalize()` and `pose_normalization_info()`** · *Take:* Shoulder-midpoint origin,
   inter-shoulder scale · *Where:*
   [`ARC_S4.3`](../../../plan/ARC_architecture.md#43-recommended-representation) step 2, which no
   longer needs writing
3. **`correct_wrists()`** · *Take:* Substitute the body wrist when the hand wrist is absent ·
   *Where:* [`ARC_S6.5`](../../../plan/ARC_architecture.md#65-perception-engineering-rules), a new
   rule
4. **`normalize_hands_3d()`** · *Take:* Rotation-canonical handshape ·
   *Where:* [`ARC_S4.3`](../../../plan/ARC_architecture.md#43-recommended-representation) step 3
5. **`augment2d()` and `frame_dropout_*`** · *Take:* The small-dataset answer ·
   *Where:* The classifier training script; `EVL`
6. **`interpolate_fps()`** · *Take:* One time base across cameras · *Where:* Data protocol in `EVL`
7. **`PoseVisualizer`** · *Take:* Skeleton overlay on the source video · *Where:* Day-one debugging,
   and the demo video
8. **The `.pose` format** · *Take:* The on-disk representation for recorded vocabulary ·
   *Where:* `data/`, and the interchange with `RSS` for the reverse direction




## 9.3. What the Project Does Not Take
1. **`pose_format[mediapipe]`, `video_to_pose`, `videos_to_poses`, `process_holistic()`** — all on
   the legacy Solutions API — [`SPR_S6`](#6-the-mediapipe-collision)
2. **`reduce_holistic`'s 128 face points as a model input** — [`SPR_S5.2`](#52-reduction)
3. **The TensorFlow back-end.** The project has no TensorFlow
4. **`src/js` and `src/dart`.** No browser or Flutter deliverable is planned
5. **Whole-sequence normalisation semantics, unexamined.** The streaming case must be decided —
   [`SPR_S5.1`](#51-normalisation)

---





# 10. SOURCES
1. **`[S1]`**
   *Source:* `ref_repo/translation/sign-pose/pose/README.md` at `7a36fcf` — the toolkit
   description, the installation and CLI usage, the normalisation and augmentation examples, and
   the importer list
   *Reliability:* Official project documentation
2. **`[S2]`**
   *Source:* `ref_repo/translation/sign-pose/pose/docs/specs/v0.1.md` — the binary format,
   including the `# THIS IS A PROBLEM` annotation on the frame-count field
   *Reliability:* Primary — read from the clone
3. **`[S3]`**
   *Source:* `ref_repo/translation/sign-pose/pose/src/python/pyproject.toml:4,12-17,26,33` — the
   version, the three runtime dependencies and the `mediapipe<0.10.30` pin
   *Reliability:* Primary — read from the clone
4. **`[S4]`**
   *Source:* `ref_repo/translation/sign-pose/pose/LICENSE.txt` — MIT, © 2021 Amit Moryossef
   *Reliability:* Primary. ⚠ Read as an engineer, not a lawyer
5. **`[S5]`**
   *Source:* `ref_repo/translation/sign-pose/pose/src/python/pose_format/pose.py:104-142` and
   `src/python/pose_format/utils/generic.py:151-230`
   *Reliability:* Primary — read from the clone
6. **`[S6]`**
   *Source:* `ref_repo/translation/sign-pose/pose/src/python/pose_format/utils/generic.py:369-435`
   — `correct_wrist`, `correct_wrists`, `reduce_holistic`. The 128-point face contour count was
   obtained by enumerating the hard-coded list
   *Reliability:* Primary — read from the clone
7. **`[S7]`**
   *Source:* `ref_repo/translation/sign-pose/pose/src/python/pose_format/pose_body.py:380,553-620`
   and `pose.py:182-220`
   *Reliability:* Primary — read from the clone
8. **`[S8]`**
   *Source:* `ref_repo/translation/sign-pose/pose/src/python/pose_format/utils/holistic.py:18-33`
   *Reliability:* Primary — read from the clone
9. **`[S9]`**
   *Source:* The clone itself at `7a36fcf` (2026-07-23), version `v0.14.1`. Commit, contributor and
   test-file counts were obtained by enumeration of the working tree and `git log`
   *Reliability:* Primary

---





# 11. CHANGE LOG
1. **2026-09-04** · *Author:* Claude (Opus 5)
   *Change:* Created from a read of the README, the binary format specification, `pyproject.toml`,
   and the normalisation, reduction, wrist-correction, augmentation and MediaPipe-integration
   source. Recorded `RSP` as the project's second candidate dependency after `RMP`; identified
   `normalize()` as an existing implementation of
   [`ARC_S4.3`](../../../plan/ARC_architecture.md#43-recommended-representation) step 2;
   identified `correct_wrists()` as a fix for a MediaPipe failure `ARC` had not named; and recorded
   the `mediapipe<0.10.30` pin and `mp.solutions.holistic` dependency as a collision with
   [`ARC_S6.5`](../../../plan/ARC_architecture.md#65-perception-engineering-rules) rule 1 that
   confines the adoption to the base install.
