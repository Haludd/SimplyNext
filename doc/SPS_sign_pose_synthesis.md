**POSE-FORMAT — SYNTHESIS FOR SIMPLYNEXT**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field             | Value                                                                 |
| :---------------- | :-------------------------------------------------------------------- |
| **Code**          | `SPS`                                                                 |
| **Status**        | Live                                                                  |
| **Last reviewed** | 2026-09-04                                                            |
| **Scope**         | Short orientation to `RSP`, the project's second candidate dependency |
| **Subject**       | `RSP` — `translation/sign-pose/pose/` at `7a36fcf`                    |
| **Full report**   | [`SPR`](../ref_repo/translation/sign-pose/SPR_sign_pose_report.md)    |

**For the team.** `pose-format` is the field's standard pose container: MIT, `pip install`, **three
runtime dependencies**, actively maintained, and it already implements the body-relative
normalisation [`ARC_S4.3`](../plan/ARC_architecture.md#43-recommended-representation) specifies. It
is the second candidate dependency after `RMP`. The complete analysis is in
[`SPR`](../ref_repo/translation/sign-pose/SPR_sign_pose_report.md), beside the clone in
`ref_repo/translation/sign-pose/`.

**For the assistant.** `RSP` is a **candidate dependency**, unlike `RSL`, `RSA` and `ROP`. Its data
structures may be shipped; its **pose-estimation path may not** — it is built on the legacy
`mp.solutions` API and pins `mediapipe<0.10.30`, colliding with
[`ARC_S6.5`](../plan/ARC_architecture.md#65-perception-engineering-rules) rule 1. State that
distinction whenever the library comes up. Where this file and
[`SPR`](../ref_repo/translation/sign-pose/SPR_sign_pose_report.md) disagree, `SPR` wins.

</details>

---





# 1. WHAT THIS IS
`sign-language-processing/pose` is *"a complete toolkit for working with poses"*, and three things
at once:

1. A **binary file format**, `.pose`, for pose sequences of any type, any number of people, any
   length
2. A **Python library** to read, normalise, augment, interpolate and visualise them, with NumPy,
   PyTorch and TensorFlow back-ends
3. **Importers** mapping MediaPipe Holistic, OpenPose (137 and 135), AlphaPose WholeBody and MMPose
   WholeBody into one representation

It is version `v0.14.1` at `7a36fcf`, **2026-07-23** — 383 commits, 20 contributors, 32 test files,
and the only **actively maintained** repository in `ref_repo/translation/`. Its author also writes
`RSS` ([`SSS`](SSS_spoken_to_signed_synthesis.md)) and `RLT`
([`LTS`](LTS_signlang_literature_synthesis.md)); the three are one stack.

**Licence: MIT.** Commercial use, modification and distribution granted, attribution required.

**Dependencies: `numpy`, `tqdm`, `simple-video-utils`.** No torch, no MediaPipe, no OpenCV in the
base install — every heavier capability is an extra. Against `RSL`'s `torch==1.9.0+cu102` and eight
GPUs, that is a different order of commitment, and it satisfies `D3_p42`'s `requirements.txt`
constraint without argument.

---





# 2. THE DATA MODEL
A `.pose` file is a **header** naming components (`POSE_LANDMARKS`, `FACE_LANDMARKS`,
`LEFT_HAND_LANDMARKS`, …), their points, the limbs connecting them and their colours; plus a
**body** holding a coordinate array of shape `(frames, people, points, dims)` and a parallel
confidence array of shape `(frames, people, points)`.

Three consequences:

1. **Points are named, not indexed.** `get_point_index("POSE_LANDMARKS", "LEFT_WRIST")` resolves a
   name. Code written against names survives a change of pose estimator — the boundary discipline
   [`APS_S5`](APS_apple_synthesis.md#5-the-twelve-lessons) recommends
2. **Confidence is a separate array**, not a fourth coordinate. A missing point is
   `confidence == 0`, and the visualiser draws only above zero. **Absence is a first-class state**
3. **The format is multi-person from the ground up.** ⚠ The library provides no logic for
   *choosing* a person, so [`ARC_S2`](../plan/ARC_architecture.md#2-step-1--isolating-the-subject)
   is unaffected

⚠ One known defect: the format's frame count is an `unsigned short`, capping a file at 65,535
frames — ~44 minutes at 25 fps. The specification annotates it `# THIS IS A PROBLEM`. Irrelevant at
utterance scale.

---





# 3. THE FIVE THINGS TO TAKE
## 3.1. `normalize()` — Already Written
```python
center = ((p2s + p1s) / 2).mean(axis=(0, 1))
self.body.data -= center
scale = scale_factor / distance_batch(p1s, p2s).mean()
self.body.data = self.body.data * scale
```

Called with no arguments it looks up the two shoulder points for the detected format, moves the
shoulder midpoint to the origin, and scales so mean inter-shoulder distance is 1 — automatically,
for MediaPipe Holistic, OpenPose, OpenPose-135, AlphaPose and COCO-WholeBody.

> **This is [`ARC_S4.3`](../plan/ARC_architecture.md#43-recommended-representation) step 2,
> verbatim.** It no longer needs writing.

Two details matter. The centre and scale are computed **over the whole sequence**, so the transform
is rigid and *relative motion between frames is preserved* — per-frame normalisation would destroy
exactly the motion signal the classifier needs. And ⚠ **it is a batch operation, not a streaming
one**: stage ③ runs live, so the project must normalise per buffered utterance window or maintain a
running shoulder estimate. Not hard; must be decided rather than inherited.




## 3.2. `correct_wrists()` — A Failure `ARC` Did Not Name
MediaPipe Holistic emits each wrist **twice**: once from the pose model, once from the hand model.
When the hand model fails, its wrist has zero confidence while the pose model's is still valid.
`correct_wrist()` substitutes the latter for the former, per frame, per hand.

> **This matters because the hand wrist is the origin of the handshape descriptor.** If it collapses
> to zero, every hand landmark expressed relative to it is wrong, and the error is silent. Ten
> lines, and it belongs in stage ③.




## 3.3. `normalize_hands_3d()` — Rotation-Canonical Handshape
Rotates each hand into a frame defined by a plane (`WRIST`, `PINKY_MCP`, `INDEX_FINGER_MCP`) and a
line, so handshape becomes independent of hand orientation. A genuine addition to
[`ARC_S4.3`](../plan/ARC_architecture.md#43-recommended-representation), which keeps per-hand world
landmarks but does not canonicalise their rotation.




## 3.4. `augment2d()` and `frame_dropout_*` — The Small-Dataset Answer
`augment2d(rotation_std, shear_std, scale_std)` perturbs every point affinely.
`frame_dropout_uniform`, `frame_dropout_normal` and `frame_dropout_given_percent` drop a random
proportion of frames.

> **Frame dropout is the more valuable of the two here**, because it simulates the failure the
> pipeline will actually have: MediaPipe returning nothing on some frames because the presence gate
> rejected them — [`MPS_S3`](MPS_mediapipe_synthesis.md#3-the-pipeline). A classifier trained with
> frame dropout has seen gaps before.

`interpolate_fps(fps, kind)` puts recordings from different cameras on one time base.




## 3.5. `PoseVisualizer` — Day-One Debugging
`save_video()`, `draw_on_video()` and `save_gif()` render a skeleton, optionally over the original
footage. The cheapest possible debugging tool for stages ②–③, and worth wiring up immediately.

---





# 4. THE ONE THING NOT TO TAKE
`utils/holistic.py`:

```python
import mediapipe as mp
mp_holistic = mp.solutions.holistic
```

`pyproject.toml`:

```toml
mediapipe = ["mediapipe<0.10.30"]
```

The library's video → pose path is built on **`mp.solutions.holistic`** — the legacy Solutions API
[`MPS_S6`](MPS_mediapipe_synthesis.md#6-the-four-traps-that-will-cost-a-day) identifies as excluded
from the 1.0-line wheel, and
[`ARC_S6.5`](../plan/ARC_architecture.md#65-perception-engineering-rules) rule 1 forbids. The
`<0.10.30` pin is the proof: the package caps MediaPipe *below* the version that removed the API it
needs. The README compounds it by advertising `model_complexity`, `smooth_landmarks` and
`refine_face_landmarks` — all legacy constructor arguments with no Tasks-API counterpart.

> **Warning — installing `pose-format[mediapipe]` caps the project's MediaPipe version and forces
> the forbidden API.** `video_to_pose`, `videos_to_poses` and `process_holistic()` are all on that
> path.

> **Decision — take the data structures, not the estimator.** The base install contains everything
> in [`SPS_S3`](#3-the-five-things-to-take). The project runs MediaPipe Tasks itself — `RST`
> demonstrates the correct setup, [`STS_S3`](STS_sign_translator_synthesis.md#3-the-tasks-api-done-right)
> — and constructs a `Pose` from the resulting arrays. **Never install the `mediapipe` extra.**

---





# 5. ONE BUDGET NOT TO MISREAD
`reduce_holistic()` cuts a 543-point Holistic pose to **178**: 8 upper-body points (shoulders,
elbows, wrists, hips — everything else in `POSE_LANDMARKS` dropped by name), the **128
`FACEMESH_CONTOURS`** points, and both hands whole.

> **Warning — 178 is a storage and rendering budget, not a model-input budget.** `RSS` calls it
> before *drawing* and stitching poses, where 128 face contour points make an avatar look right. A
> classifier is a different consumer: `RSL` feeds **10–26** face points to its model
> ([`SLS_S5`](SLS_slrt_synthesis.md#5-the-keypoint-budget)) and `RSA` feeds **none**
> ([`SAS_S4`](SAS_sam_slr_synthesis.md#4-twenty-seven-points)). Do not read 128 as a recommendation
> for [`ARC_S3.2`](../plan/ARC_architecture.md#32-the-landmark-budget).

The **body** reduction is directly endorsable, and `pose_hide_legs()` does the leg part alone.

---





# 6. THE EIGHT LESSONS
| #  | Lesson                                                                                     |
| :- | :----------------------------------------------------------------------------------------- |
| P1 | **Name points, do not index them.** Names survive a change of pose estimator               |
| P2 | **Confidence is a parallel array, not a coordinate.** Absence becomes representable        |
| P3 | **Normalise over the sequence, never per frame** — per-frame scaling destroys motion       |
| P4 | **The hand wrist and the body wrist are two different points**, and one of them fails      |
| P5 | **Canonicalise hand rotation** before treating handshape as a feature                      |
| P6 | **Frame dropout is the honest augmentation** for an intermittent detector                  |
| P7 | **A rendering budget is not a model budget.** 178 points to draw; 27–79 to classify        |
| P8 | **A library's defaults can contradict the project's rules.** Read the pin                  |

---





# 7. WHAT IT DOES NOT DO
1. **It does not recognise or classify anything.** There are no models
2. **It does not track** — no temporal association, no hand identity, no handedness averaging.
   [`ARC_S6.5`](../plan/ARC_architecture.md#65-perception-engineering-rules) rules 4–7 stay the
   project's own work
3. **It does not segment.** `RSS` builds a crude boundary detector *on top of* it
4. **It does not choose a signer**, despite a real people axis
5. **It does not stream.** The API assumes a complete sequence in memory
6. **It gives no classifier landmark budget** — [`SPS_S5`](#5-one-budget-not-to-misread)
7. **Its own estimator is on the forbidden API** — [`SPS_S4`](#4-the-one-thing-not-to-take)

---





# 8. RUNNING IT
It runs today, on a laptop, with no GPU:

```bash
pip install pose-format          # numpy, tqdm, simple-video-utils. Nothing else
```

```python
from pose_format import Pose
from pose_format.utils.generic import pose_normalization_info, correct_wrists

with open("example.pose", "rb") as f:
    pose = Pose.read(f.read())

pose = correct_wrists(pose)
pose.normalize(pose_normalization_info(pose.header))
data, conf = pose.body.data, pose.body.confidence
```

> **Warning — do not run `video_to_pose` or install `pose-format[mediapipe]`.**
> [`SPS_S4`](#4-the-one-thing-not-to-take). The estimation step is the project's own, on the Tasks
> API.

> **Placeholder — the cost of building a `Pose` from Tasks-API output.**
> **Missing:** whether a `PoseHeader` matching the Holistic component and point names can be built
> from Tasks-API output without reimplementing the library's header construction. `reduce_holistic`,
> `correct_wrists` and `pose_shoulders` all dispatch on `detect_known_pose_format`, so the names
> must match exactly or those functions return the input unchanged — **silently**.
> **Update trigger:** the first working capture loop.
> **Owner:** team.

---





# 9. WHERE TO GO NEXT
1. **Full breakdown** —
   [`SPR`](../ref_repo/translation/sign-pose/SPR_sign_pose_report.md)
2. **Correct MediaPipe Tasks setup** — [`STS`](STS_sign_translator_synthesis.md)
3. **Why the legacy API is banned** — [`MPS_S6`](MPS_mediapipe_synthesis.md)
4. **The reverse direction, built on it** — [`SSS`](SSS_spoken_to_signed_synthesis.md)
5. **The representation it serves** — [`ARC_S4.3`](../plan/ARC_architecture.md)
6. **Where every document lives** — [`RIX`](../ref_index.md)

---





# 10. CHANGE LOG
1. **2026-09-04** · *Author:* Claude (Opus 5)
   *Change:* Created alongside [`SPR`](../ref_repo/translation/sign-pose/SPR_sign_pose_report.md),
   from a read of the README, the binary format specification, `pyproject.toml`, and the
   normalisation, reduction, wrist-correction, augmentation and MediaPipe-integration source.
