**OPENPOSE — SYNTHESIS FOR SIMPLYNEXT**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field             | Value                                                |
| :---------------- | :--------------------------------------------------- |
| **Code**          | `OPS`                                                |
| **Status**        | Live                                                 |
| **Last reviewed** | 2026-08-30                                           |
| **Scope**         | Short orientation to `ROP` and why it was not chosen |
| **Subject**       | `ROP` — `openpose/openpose/` at `5c5d965`            |
| **Full report**   | [`OPR`](../ref_repo/tracking/openpose/OPR_openpose_report.md) |

**For the team.** A five-minute orientation, and the record of a rejection. The complete analysis
is in [`OPR`](../ref_repo/tracking/openpose/OPR_openpose_report.md), which lives beside the clone in
`ref_repo/tracking/openpose/`. The sibling syntheses are [`APS`](APS_apple_synthesis.md),
[`MPS`](MPS_mediapipe_synthesis.md) and [`DHS`](DHS_depthai_synthesis.md); the four are compared
head-to-head in
[`ARC_S7.2`](../plan/ARC_architecture.md#72-the-four-reference-repositories-compared).

**For the assistant.** OpenPose is **not** an option under consideration. Its licence forbids the
use and its CPU performance forbids the demonstration. State both plainly wherever the question
arises. No OpenPose code, model or derivative enters `src/`. Where this file and
[`OPR`](../ref_repo/tracking/openpose/OPR_openpose_report.md) disagree, `OPR` wins.

</details>

---





# 1. WHAT THIS IS
CMU's **OpenPose**: by its own description, *"the first real-time multi-person system to jointly
detect human body, hand, facial, and foot keypoints (in total 135 keypoints) on single images"*.
A C++ library on Caffe, published in **IEEE TPAMI 2019**, with its hand detector published at
**CVPR 2017**.

It is the intellectual ancestor of everything else in `ref_repo/`, and the most citable work
among them. The clone is `v1.7.0-73-g5c5d965`; **v1.7.0 is dated 2020-11-17**, and every commit
since 2022 is a documentation or link fix. ⚠ Feature-frozen.

**Output per person:** 25 body/foot keypoints, 2 × 21 hand keypoints, 70 face keypoints.

---





# 2. WHY IT WAS NOT CHOSEN
Two reasons. Either one on its own would settle it.




## 2.1. The Licence
The first three lines of `LICENSE`:

```text
OPENPOSE: MULTIPERSON KEYPOINT DETECTION
SOFTWARE LICENSE AGREEMENT
ACADEMIC OR NON-PROFIT ORGANIZATION NONCOMMERCIAL RESEARCH USE ONLY
```

Three clauses matter, and each is independently disqualifying:

1. Use is granted for *"your own noncommercial internal research purposes"* only. A hackathon
   submission that could become a product is not that
2. *"You agree that all and any such derivatives and modifications **will be owned by Licensor**"*
   — building the pipeline on OpenPose would mean **CMU owns the pipeline**
3. *"You may not distribute, copy or use the Software except as explicitly permitted herein"* — and
   the submission is distributed to the organiser

Compare `RMP` (Apache 2.0) and `RDH` (MIT), which impose none of this. CMU offers a commercial
licence through a FlintBox page; that is not a four-day conversation.

> **Note — reading it is fine.** Studying the method, citing the papers and describing the
> architecture are unaffected. What is excluded is shipping code derived from it.




## 2.2. The Performance
From the repository's own speed documentation:

> *"The CPU version runs at about 0.3 FPS on the COCO model, and at about 0.1 FPS (i.e., about 15
> sec / frame) on the default BODY_25 model."*

**Fifteen seconds per frame, body only, before hands are enabled.** Interactive use requires a
CUDA GPU with cuDNN, and the FAQ warns that *"hands and face increases the GPU memory
requeriments, and 4 GB GPUs might run a bit short"* — sic.

The product promise in [`SCR`](../plan/scribbles.md) is *any device with a camera*, and
[`JCR_S2.1`](../plan/JCR_judging_criteria.md#21-c1--benefits-delivered-by-the-solution-20) pays
for *"scalable or easily adopted"*. Requiring a CUDA GPU fails that clause exactly as a depth
camera does. `RMP` reaches video rate on a CPU with no GPU at all.

---





# 3. WHAT IT IS STILL GOOD FOR
1. **The honest comparison.** `D3_p7` asks for *"what the existing tools still leave undone"*, and
   [`JCR_S2.2`](../plan/JCR_judging_criteria.md#22-c2--original--innovative-idea-20) scores
   originality against existing solutions. Having read the strongest existing whole-body keypoint
   system, and being able to say precisely why it was not used, is worth more than not mentioning it
2. **The citations.** TPAMI 2019 and CVPR 2017 are peer-reviewed, which
   [`CLD_S5.1`](../CLAUDE.md#51-evidence) prefers over everything else in `ref_repo/`
3. **Two genuinely instructive ideas.** Part affinity fields, and multiview bootstrapping

---





# 4. THE TWO IDEAS
## 4.1. Part Affinity Fields
Alongside a confidence map for each body part, the network predicts a **2D vector field for each
limb** — at every pixel on a forearm, a unit vector pointing from elbow to wrist. Deciding whether
a particular elbow and wrist belong to the same person then becomes an integral along the line
between them, rather than a heuristic. Greedy matching over those scores assembles the skeletons.

This is why the body stage's runtime is *"constant, while the runtime of Alpha-Pose and Mask R-CNN
grow linearly with the number of people"*.

> **Warning — the invariance covers the body only.** The README states that hand and face
> estimation have *"Runtime depends on number of detected people"*. For a sign-language
> application, the headline property does not apply to the part that matters.

The project does not need this. Signing space is defined relative to *one* signer's body, and
attributing hands among several people is
[`RSK_S5`](../plan/RSK_risk_register.md#5-multi-person-and-conversation), which
[`ARC_S2.2`](../plan/ARC_architecture.md#22-recommended-build) defers deliberately.




## 4.2. Multiview Bootstrapping
How the hand detector was trained (Simon et al., CVPR 2017), and the one idea here that touches a
live project problem.

Take a weak hand detector. Run it on many simultaneous views of the same hand from a calibrated
camera dome. Keep only the keypoints that are **geometrically consistent across views**,
triangulate them, re-project them into every view, and use those as new training labels. Iterate.
The detector improves each round with no additional human labelling.

> **Decision support.** [`ARC_S9.1`](../plan/ARC_architecture.md#91-open-questions-for-the-team)
> open question 4 asks how the project gets training data. The transferable principle is **use
> geometric consistency across views as a free supervisor** — in a cheap form, record each sign
> from two phone cameras at an angle and keep only the frames where the two views agree.
> ⚠ This is an extrapolation from the method, not something the paper proposes, and the paper was
> not read in full for this review. Treat it as a direction to evaluate.

---





# 5. TWO PRACTICAL DETAILS WORTH KEEPING
**Hands are found from the body.** OpenPose has no palm detector; by default the hand region comes
from the wrist and elbow keypoints of an already-detected person. That makes handedness trivially
reliable — the same advantage `RDH`'s Body Pre Focusing and MediaPipe's Holistic reach by different
routes — but it means **a hand cannot be found unless the arm is found**.

**Crop with margin.** The training guidance, which transfers to any dataset the project records:

> *"You should leave about 10-20% margin between the end of the hand/face and the sides … of the
> image. We trained with that configuration, so it should be the ideal one for maximizing
> detection."* — and *"if you can, use the image rather than adding a color-based padding."*

One more, on reading benchmarks: the default `--hand_scale_number` is `1`, but the authors note
*"Our best results were found with `hand_scale_number` = 6"*. Published quality assumes the hand
network runs **six times per hand per frame**. A quoted number and an observed number are not the
same thing —
[`JCR_S4.4`](../plan/JCR_judging_criteria.md#44-five-pressure-test-questions).

---





# 6. THE SEVEN LESSONS
Full rationale in
[`OPR_S9.1`](../ref_repo/tracking/openpose/OPR_openpose_report.md#91-lessons-to-carry-across).

| #  | Lesson                                                                        |
| :- | :---------------------------------------------------------------------------- |
| O1 | **Check the licence before the benchmark.** It settled this in three lines    |
| O2 | **A headline property may not cover the part you need**                       |
| O3 | **Published accuracy often assumes a non-default configuration**              |
| O4 | **Anchoring hands to a body makes handedness reliable** — at a cost           |
| O5 | **Geometric consistency across views is a free labeller**                     |
| O6 | **Leave 10–20% margin around a hand crop**; prefer real background to padding |
| O7 | **State performance honestly, including the embarrassing number**             |

O7 is the one to imitate. A project that publishes its own worst number is trusted on its best.

---





# 7. WHAT IT DOES NOT DO
No sign, gesture or meaning — keypoints only. No temporal model; the hand-tracking mode *"is not
person ID tracking"*. No monocular 3D — the 3D module needs multiple calibrated cameras. No usable
CPU real-time path. No hand detection without a body, by default. No pip install. No model weights
in the repository. No ongoing development since 2020. ⚠ No permissive licence.

Full list: [`OPR_S7`](../ref_repo/tracking/openpose/OPR_openpose_report.md).

---





# 8. RUNNING IT
**Not attempted, and not recommended.** A source build needs CMake, CUDA, cuDNN and Caffe, and
would consume a meaningful fraction of the four-day window for a result that cannot be shipped and
cannot be demonstrated at frame rate.

If a side-by-side landmark comparison against MediaPipe is judged worth an afternoon, the cheapest
route is the Windows portable demo on a machine with an Nvidia GPU, with `--hand` and
`--write_json`. That is a measurement, permitted as internal research; no OpenPose code would
enter `src/` —
[`OPR_S8`](../ref_repo/tracking/openpose/OPR_openpose_report.md).

---





# 9. WHERE TO GO NEXT
| Question                     | Document                                             |
| :--------------------------- | :--------------------------------------------------- |
| Full breakdown of OpenPose   | [`OPR`](../ref_repo/tracking/openpose/OPR_openpose_report.md) |
| The tracker actually chosen  | [`MPS`](MPS_mediapipe_synthesis.md)                  |
| How the four compare         | [`ARC_S7.2`](../plan/ARC_architecture.md)            |
| How the submission is scored | [`JCR`](../plan/JCR_judging_criteria.md)             |
| Where every document lives   | [`RIX`](../ref_index.md)                             |

---





# 10. CHANGE LOG
1. **2026-08-30** · *Author:* Claude (Opus 5)
   *Change:* Created alongside [`OPR`](../ref_repo/tracking/openpose/OPR_openpose_report.md), from a read of
   the README, the licence, the speed documentation and the runtime flags.
