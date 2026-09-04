**OPENPOSE — FULL REPOSITORY REPORT**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field                   | Value                                              |
| :---------------------- | :------------------------------------------------- |
| **Code**                | `OPR`                                              |
| **Status**              | Live                                               |
| **Last reviewed**       | 2026-08-30                                         |
| **Source of truth for** | Analysis of the OpenPose reference clone           |
| **Parent**              | [`RIX_S2.1`](../../ref_index.md#21-live-documents) |
| **Short version**       | [`OPS`](../../doc/OPS_openpose_synthesis.md)       |
| **Subject**             | `ROP` — `openpose/openpose/` at `5c5d965`          |

**For the team.** CMU's OpenPose: the first real-time multi-person whole-body keypoint system, and
the intellectual ancestor of everything else in `ref_repo/`. It is **not** a candidate for the
implementation, for two independent and individually sufficient reasons — a non-commercial licence
and a CPU frame rate of roughly **0.1 FPS**. [`OPR_S2.2`](#22-licence) and
[`OPR_S6`](#6-performance) are the two sections that decide it. The rest of the report records
what is worth learning from it anyway, chiefly the part-affinity-field idea in
[`OPR_S4`](#4-how-it-works) and the multiview-bootstrapping method in
[`OPR_S5.2`](#52-how-the-hand-model-was-trained).

**For the assistant.** Do not describe OpenPose as an option under consideration. The licence
question is settled and must be stated plainly wherever it comes up —
[`CLD_S5.2`](../../CLAUDE.md#52-honesty-about-the-product). Nothing inside
`ref_repo/openpose/openpose/` may be edited; it is an unmodified clone, excluded from version
control.

</details>

---





# 1. EXECUTIVE SUMMARY
## 1.1. What This Repository Is
`ref_repo/openpose/openpose/` is **CMU-Perceptual-Computing-Lab/openpose**, described by its own
README as *"the first real-time multi-person system to jointly detect human body, hand, facial,
and foot keypoints (in total 135 keypoints) on single images"* `[S1]`. It is a C++ library built on
Caffe, authored at Carnegie Mellon University's Perceptual Computing Lab.

The published record is strong: the core method is *OpenPose: Realtime Multi-Person 2D Pose
Estimation using Part Affinity Fields*, **IEEE TPAMI 2019**, with the hand detector from *Hand
Keypoint Detection in Single Images using Multiview Bootstrapping*, **CVPR 2017** `[S1]`. These are
peer-reviewed venues, which makes OpenPose the most citable thing in `ref_repo/` by a wide margin
— see [`CLD_S5.1`](../../CLAUDE.md#51-evidence).

**Output per person:** 25 body/foot keypoints (`BODY_25`), 2 × 21 hand keypoints, 70 face
keypoints.




## 1.2. Why It Matters to SimplyNext
It matters as **evidence and as a rejected alternative**, not as a dependency.

1. **As the honest comparison** · *Use:* `D3_p7` requires looking at *"what the existing tools
   still leave undone"*, and
   [`JCR_S2.2`](../../plan/JCR_judging_criteria.md#22-c2--original--innovative-idea-20) scores
   originality against existing solutions. OpenPose is the strongest existing whole-body
   keypoint system, and the submission is better for having read it rather than ignored it
2. **As citable evidence** · *Use:* TPAMI 2019 and CVPR 2017 are peer-reviewed. Where the project
   needs a defensible claim about multi-person pose estimation or hand-keypoint annotation, this
   is the citation
3. **As a source of ideas** · *Use:* Part affinity fields ([`OPR_S4.2`](#42-part-affinity-fields))
   and multiview bootstrapping ([`OPR_S5.2`](#52-how-the-hand-model-was-trained)) are both
   genuinely instructive, and the second is directly relevant to the project's data problem
4. **As a demonstration of the constraint** · *Use:* OpenPose is what "accurate whole-body
   keypoints without regard for the hardware budget" looks like. `RMP` is what the same problem
   looks like when a phone must run it

Against the four MVP steps in [`SCR`](../../plan/scribbles.md):

1. **1. Isolate the subject** — solved *better than any other repository here*: genuine
   multi-person, with runtime **invariant to the number of people** for the body model
2. **2. Track many points** — 135 keypoints per person, including face and both hands. On paper,
   the most complete answer available
3. **3. Points → skeleton** — 2D only from one camera. True 3D requires the multi-camera
   triangulation module and a calibrated rig
4. **4. Skeleton → conversational text** — not attempted




## 1.3. Summary
A single convolutional network processes the whole image once and predicts two things per body
part: a confidence map saying where the part is, and a **part affinity field** — a 2D vector field
saying which direction the *limb* runs. Greedy bipartite matching over those fields assembles
individual people, which is why the body stage costs the same whether one person or ten are in
frame. Hands and face are a second stage: a hand region is derived from the wrist and elbow
keypoints of an already-detected body, and a separate 368×368 network runs on each hand. That
second stage is emphatically *not* runtime-invariant — it runs once per hand, and the README says
so `[S1]`.

---





# 2. PROVENANCE, LICENCE AND REQUIREMENTS
## 2.1. Provenance
1. **Publisher**
   Carnegie Mellon University, Perceptual Computing Lab. Remote:
   `https://github.com/CMU-Perceptual-Computing-Lab/openpose.git`
2. **Clone state**
   `5c5d965`, 2024-08-02, *"Models working again"* — a fix to the model download links
3. **Version**
   `git describe` reports `v1.7.0-73-g5c5d965`. **v1.7.0 is dated 2020-11-17**
4. **History**
   716 commits. Tags `v1.4.0` through `v1.7.0`
5. **Maintenance status**
   ⚠ **Feature-frozen.** Every commit since 2022 in the visible history is a documentation typo
   fix, a link fix, or a community-project listing. The last functional release was **almost six
   years before this review**
6. **Language**
   C++ (193 headers, 119 source files), CMake, with a pybind11 Python wrapper




## 2.2. Licence
This is the decisive fact about the repository, and it is the first thing to check about any
academic vision project.

`LICENSE`, first three lines:

```text
OPENPOSE: MULTIPERSON KEYPOINT DETECTION
SOFTWARE LICENSE AGREEMENT
ACADEMIC OR NON-PROFIT ORGANIZATION NONCOMMERCIAL RESEARCH USE ONLY
```

The terms that matter:

1. **Grant** — a *"personal, non-exclusive, non-transferable license to use the Software for
   noncommercial research purposes, without the right to sublicense"*
2. **Permitted uses** — *"your own noncommercial internal research purposes"*
3. **Derivatives** — *"You may create derivatives of or make modifications to the Software,
   however, You agree that all and any such derivatives and modifications **will be owned by
   Licensor** and become a part of the Software licensed to You under this Agreement."*
4. **Distribution** — *"You may not distribute, copy or use the Software except as explicitly
   permitted herein"*, and no *"sell, rent, lease, sublicense, lend, time-share or transfer"*
5. **Trademark** — the names *"OpenPose"* and *"Carnegie Mellon"* may not be used without written
   permission
6. **Commercial route** — the README points at a CMU FlintBox page for commercial licensing `[S1]`

> **Warning — three separate blockers, any one of which is sufficient.**
> **(a)** A hackathon submission that could plausibly become a product is not
> *"noncommercial internal research"*.
> **(b)** Clause 3 assigns ownership of derivatives to CMU. Building the project's pipeline on
> OpenPose would mean CMU owns the pipeline.
> **(c)** The submission is distributed to the organiser and judged; clause 4 restricts
> distribution.
> Compare `RMP` (Apache 2.0) and `RDH` (MIT), which impose none of this. **This alone settles the
> choice**, before performance is considered at all.

> **Note — the licence does not forbid reading it.** Studying the method, citing the papers and
> describing the architecture in a document are unaffected. What is excluded is *shipping code
> derived from it*.




## 2.3. Requirements
From `doc/installation/1_prerequisites.md` `[S2]`:

1. **Nvidia GPU path** — CUDA plus cuDNN, with specific tested pairings: *"OpenPose has been
   tested extensively with CUDA 11.7.1 (cuDNN 8.5.0) for Ubuntu 20"*. Older releases pair with CUDA
   10.1 / 8.0
2. **AMD GPU path** — OpenCL and ROCm; for Ubuntu 20/18 *"Not tested and not officially supported.
   Try at your own risk"*
3. **CPU-only path** — supported, and [`OPR_S6`](#6-performance) explains why it does not help
4. **Build** — CMake, a 44 KB `CMakeLists.txt`, and Caffe as the default inference backend
5. **Memory** — *"hands and face increases the GPU memory requeriments, and 4 GB GPUs might run a
   bit short in some cases"* `[S3]` — sic
6. **Models** — **not in the repository.** `models/` holds `.prototxt` definitions plus
   `getModels.sh` / `getModels.bat`; the weights are downloaded. The whole directory is 940 KB

Set against `RMP`, whose requirement is `pip install`, this is a different order of commitment. It
is also a different order of *risk*: a source build of a Caffe-based project against a modern CUDA
toolchain, inside a four-day window, on the day of a demo.

---





# 3. REPOSITORY MAP
```text
ref_repo/openpose/
├── OPR_openpose_report.md                       — this document (tracked in git)
└── openpose/                                    — the clone (git-ignored)
    ├── include/openpose/            193 headers   The public C++ API
    ├── src/openpose/                119 sources   The implementation
    ├── examples/                                 Demo binary + tutorial_api_{cpp,python}
    ├── python/                                   pybind11 wrapper
    ├── models/                       940 KB      .prototxt + download scripts. NO WEIGHTS
    ├── doc/                                      Unusually thorough documentation
    ├── 3rdparty/                                 Caffe and friends
    ├── cmake/, CMakeLists.txt        44 KB       The build
    ├── .doc_autogeneration.doxygen  122 KB       Doxygen configuration
    └── LICENSE                       9.8 KB      ← read this first
```

**Worth reading:** `doc/02_output.md` (the keypoint formats and the JSON schema),
`doc/06_maximizing_openpose_speed.md` (the honest performance numbers),
`doc/advanced/standalone_face_or_hand_keypoint_detector.md` (how hands are located),
`include/openpose/flags.hpp` (every runtime option in one file), and `LICENSE`.

**Not worth reading:** everything else, unless the goal is to build it.

---





# 4. HOW IT WORKS
## 4.1. Bottom-Up, Not Top-Down
Most pose estimators of the period were **top-down**: detect each person, then estimate that
person's pose. Cost grows linearly with the number of people. OpenPose is **bottom-up**: find all
the body parts in the image at once, then work out which parts belong to which person.

The consequence is stated in the README `[S1]` and shown in its runtime chart: *"The OpenPose
runtime is constant, while the runtime of Alpha-Pose and Mask R-CNN grow linearly with the number
of people."*

> **Note — the invariance applies to the body model only.** The README is explicit that hand
> estimation and face estimation have *"Runtime depends on number of detected people"*. For a
> sign-language application, where hands are the entire signal, the headline property does not
> apply to the part that matters.




## 4.2. Part Affinity Fields
The contribution named in the TPAMI title. Alongside a confidence map for each body part, the
network predicts a **2D vector field for each limb** — at every pixel lying on, say, a forearm, a
unit vector pointing from elbow towards wrist.

Association then becomes a measurable question rather than a heuristic one: to decide whether a
particular elbow and a particular wrist belong to the same person, integrate the affinity field
along the line between them. A high integral means the limb is really there. Greedy bipartite
matching over those scores assembles the skeletons.

> **Decision support — this is a solved problem the project does not need to solve.** Signing space
> is defined relative to *one* signer's body, and `RMP`'s `HolisticLandmarker` already binds hands
> to a body for a single person. Part affinity fields matter only if the project ever needs to
> attribute hands to the correct person among several — which is
> [`RSK_S5`](../../plan/RSK_risk_register.md#5-multi-person-and-conversation), and which
> [`ARC_S2.2`](../../plan/ARC_architecture.md#22-recommended-build) deliberately defers.

---





# 5. THE HAND KEYPOINT DETECTOR
## 5.1. How Hands Are Found
OpenPose does not have a palm detector. By default the hand region is derived **from the body
skeleton** — the wrist and elbow keypoints of an already-detected person define a square around the
hand. `include/openpose/flags.hpp:143–158` documents the alternatives via `--hand_detector`, which
is *"Analogous to `--face_detector`"*:

1. **`0` (default)** — use the OpenPose body detector; *"most accurate one and fastest one if body
   is enabled"*
2. **`1`** — the OpenCV face detector; *"not implemented for hands"*
3. **`2`** — rectangles *"provided by the user"*
4. **`3`** — *"also apply hand tracking (only for hand)"*, with the honest caveat: *"Hand tracking
   might improve hand keypoint detection for webcam (if the frame rate is high enough, i.e., >7 FPS
   per GPU) and video. This is not person ID tracking, it simply looks for hands in positions at
   which hands were located in previous frames, but it does not guarantee the same person ID among
   frames"*

> **Decision support — a structural difference from MediaPipe, and it cuts both ways.** MediaPipe
> finds a hand directly, so a hand can be tracked with no body in frame. OpenPose requires the body
> first, so **a hand cannot be found unless the arm is found**. For a seated signer at a desk with
> a torso in frame that is fine, and it makes handedness trivially reliable — the same advantage
> `RDH`'s Body Pre Focusing and MediaPipe's Holistic both reach by a different route
> ([`DHR_S6`](../depthai-hand-tracker/DHR_depthai_report.md#6-body-pre-focusing)). For a
> close-up of hands only, it fails entirely.

Mode `3`'s caveat is worth keeping for its own sake: it describes exactly what MediaPipe's tracking
also is — region reuse, **not identity** — and it names the frame-rate floor below which the trick
stops working.




## 5.2. How the Hand Model Was Trained
*Hand Keypoint Detection in Single Images using Multiview Bootstrapping* (Simon, Joo, Matthews,
Sheikh, CVPR 2017) `[S1]`. The method, in outline: take a weak hand detector, run it on many
simultaneous views of the same hand from a calibrated multi-camera dome, keep the keypoints that
are geometrically consistent across views, triangulate them, re-project them into every view — and
use *those* as new training labels. Iterate. The detector improves each round without a human
labelling another image.

The README notes the face detector *"was trained using the same procedure"*.

> **Decision support — this is the most transferable idea in the repository, and it is about
> data.** [`ARC_S9.1`](../../plan/ARC_architecture.md#91-open-questions-for-the-team) open question
> 4 asks how the project gets training data. Multiview bootstrapping is the published answer to
> *"how do you label hand keypoints at scale without labelling hand keypoints at scale"*, and its
> principle — **use geometric consistency across views as a free supervisor** — survives without
> CMU's dome. A cheap version: record the same sign from two phone cameras at an angle, keep only
> the frames where both views agree, discard the rest.
> ⚠ **This is an extrapolation from the method, not something the paper proposes.** The paper was
> not read in full for this review; only the README's description of it and the repository's use of
> it were. Treat it as a research direction to evaluate, not a validated technique, and read the
> paper before planning against it.




## 5.3. Hand Configuration and Output
From `include/openpose/flags.hpp:154–162`:

- `--hand` — off by default. *"It will also slow down the performance, increase the required GPU
  memory and its speed depends on the number of people"*
- `--hand_net_resolution` — default `368x368`, *"Multiples of 16 and squared"*. Compare MediaPipe's
  192×192 palm detector
- `--hand_scale_number` / `--hand_scale_range` — defaults `1` and `0.4`, with the note that
  *"Our best results were found with `hand_scale_number` = 6 and `hand_scale_range` = 0.4"*
- `--hand_render_threshold` — default `0.2`

> **Warning — the accuracy configuration is six times the cost.** The authors' own best results use
> six scales, meaning the hand network runs six times per hand per frame. At default settings the
> published quality is not what is being measured. This is the kind of detail that separates a
> quoted benchmark number from an observed one, and it is exactly what
> [`JCR_S4.4`](../../plan/JCR_judging_criteria.md#44-five-pressure-test-questions) asks for.

**Output format** (`doc/02_output.md`): JSON per frame, with `pose_keypoints_2d`,
`face_keypoints_2d`, `hand_left_keypoints_2d` and `hand_right_keypoints_2d`, each a flat array of
`x, y, confidence` triples. The C++ API exposes `std::array<Array<float>, 2> handKeypoints`, index
0 for the left hand and 1 for the right.

> **Note — a confidence per keypoint, in the file format itself.** The JSON carries a score
> alongside every coordinate, and `--hand_render_threshold` is applied at render time rather than
> at detection time. It is a defensible design — keep the data, decide later — and it is the
> opposite of the gate-and-drop rule that
> [`ARC_S9`](../../plan/ARC_architecture.md#9-decisions) decision 8 adopts. Both are coherent; the
> project chooses gating because a downstream LLM must never receive a low-confidence value it can
> render fluent.




## 5.4. A Note on Cropping
`doc/advanced/standalone_face_or_hand_keypoint_detector.md` gives training-time guidance that is
useful regardless of framework:

> *"If you are using your own hand or face images, you should leave about 10-20% margin between
> the end of the hand/face and the sides (left, top, right, bottom) of the image. We trained with
> that configuration, so it should be the ideal one for maximizing detection."*

And: *"We did not use any solid-color-based padding, we simply cropped from the whole image. Thus,
if you can, use the image rather than adding a color-based padding."*

Both points transfer directly to any dataset the project records — margin matters, and synthetic
padding is worse than real background.

---





# 6. PERFORMANCE
`doc/06_maximizing_openpose_speed.md` is unusually candid, and the numbers are decisive `[S4]`:

> *"The CPU version runs at about 0.3 FPS on the COCO model, and at about 0.1 FPS (i.e., about 15
> sec / frame) on the default BODY_25 model."*

**Roughly fifteen seconds per frame, body only, before hands are enabled.** The same document
records a further oddity worth quoting because it shows how tightly the system is tuned to GPUs:
*"Contradictory fact: BODY_25 model is about 5x slower than COCO on CPU-only version, but it is
about 40% faster on GPU version."*

The optimisation advice is all GPU-shaped: enable OpenGL rendering, use cuDNN 5.1 or 7.2 because
*"cuDNN 6 is ~10% slower"*, reduce `--net_resolution` to 320×176 at a cost in accuracy, enable AVX.

> **Warning — this is the second, independent disqualification.** The product promise in
> [`SCR`](../../plan/scribbles.md) is *any device with a camera*, and
> [`JCR_S2.1`](../../plan/JCR_judging_criteria.md#21-c1--benefits-delivered-by-the-solution-20)
> pays for *"scalable or easily adopted"*. A system needing a CUDA GPU to reach interactive frame
> rates fails that clause as surely as a depth camera does — see
> [`ARC_S7.4`](../../plan/ARC_architecture.md#75-p4p5--depth-and-glasses-as-roadmap-items). Even if
> the licence permitted use, this would.

For calibration: `RMP` reaches video rate on a CPU with no GPU at all, using two small models and
a tracking loop. The gap is not incremental.

---





# 7. WHAT THE REPOSITORY DOES NOT DO
1. **No sign, gesture or meaning.** Keypoints only
2. **No temporal model.** `--hand_detector 3` reuses previous positions; the README states it *"is
   not person ID tracking"*
3. **No monocular 3D.** The 3D module needs multiple calibrated cameras and Flir/Point Grey
   hardware
4. **No usable CPU real-time path.** [`OPR_S6`](#6-performance)
5. **No hand detection without a body**, in the default configuration
6. **No pip installation.** A source build, or the Windows portable binary
7. **No model weights in the repository.** Downloaded by script; the 2024 commit exists because
   those links had broken
8. **No ongoing development.** Last functional release 2020-11-17
9. **⚠ No permissive licence.** [`OPR_S2.2`](#22-licence)
10. **No handedness inference.** Left and right come from the body skeleton, which is more reliable
    — but it means hands cannot be labelled without one

---





# 8. RUNNING IT
**Not attempted, and not recommended.** A source build requires CMake, CUDA, cuDNN and Caffe, and
would consume a meaningful fraction of the four-day window with no prospect of the result being
usable — the licence forbids shipping it and the CPU frame rate forbids demonstrating it.

If a team member wants to see the output for comparison, the cheapest route is the **Windows
portable demo** the README links, run on a machine with an Nvidia GPU, with `--hand` enabled and
`--write_json` capturing keypoints:

```text
bin\OpenPoseDemo.exe --video examples\media\video.avi --hand --write_json output_json_folder/
```

> **Placeholder — a side-by-side landmark comparison.**
> **Missing:** whether OpenPose's 21 hand keypoints and MediaPipe's 21 hand landmarks agree on
> the same recorded clip, and where they diverge. This would be genuine evidence for
> [`JCR_S5`](../../plan/JCR_judging_criteria.md#5-evaluation-and-metrics) and costs one afternoon
> on a GPU machine.
> **Update trigger:** access to a machine with an Nvidia GPU, and a decision that the comparison is
> worth the time.
> **Owner:** team. **Note:** this is a measurement, not a dependency — the licence permits internal
> research use, and no OpenPose code would enter `src/`.

---





# 9. RELEVANCE TO SIMPLYNEXT
## 9.1. Lessons to Carry Across
| #  | Lesson                                                                                    |
| :- | :---------------------------------------------------------------------------------------- |
| O1 | **Check the licence before the benchmark.** It settled this in three lines                |
| O2 | **A headline property may not cover the part you need** — runtime invariance is body-only |
| O3 | **Published accuracy often assumes a non-default configuration** — six scales, not one    |
| O4 | **Anchoring hands to a body makes handedness reliable**, at the cost of needing a body    |
| O5 | **Geometric consistency across views is a free labeller** — multiview bootstrapping       |
| O6 | **Leave 10–20% margin around a hand crop**, and prefer real background to padding         |
| O7 | **State performance honestly, including the embarrassing number.** *0.1 FPS on CPU*       |

O7 is a documentation lesson rather than a technical one, and it is the one to imitate. A project
that publishes its own worst number is trusted on its best.




## 9.2. What the Project Takes
1. **The citations** · *Take:* TPAMI 2019, CVPR 2017 · *Where:* `ARC` and `EVL` sources; the
   positioning slide
2. **The comparison** · *Take:* Why a bottom-up multi-person GPU system was not chosen ·
   *Where:* [`ARC_S7.2`](../../plan/ARC_architecture.md#72-the-four-reference-repositories-compared)
3. **The cropping guidance** · *Take:* 10–20% margin, real background · *Where:* Data recording
   protocol in `EVL`
4. **The bootstrapping principle** · *Take:* ⚠ As a research direction to evaluate, not a plan ·
   *Where:* [`ARC_S9.1`](../../plan/ARC_architecture.md#91-open-questions-for-the-team), question 4
5. **The honesty of the speed document** · *Take:* Report the worst number · *Where:* The
   evaluation section of the deck




## 9.3. What the Project Does Not Take
1. **Any code.** [`OPR_S2.2`](#22-licence), clause 3 — derivatives are owned by CMU
2. **Any model.** Same clause, plus weights that are not in the repository
3. **The architecture.** Bottom-up multi-person solves a problem the project defers
4. **The hardware assumption.** A CUDA GPU is not *"any device with a camera"*

---





# 10. SOURCES
1. **`[S1]`**
   *Source:* `ref_repo/openpose/openpose/README.md` at `5c5d965` — the feature list, the runtime
   claim, the citation block (TPAMI 2019; Simon et al., CVPR 2017; Cao et al., CVPR 2017; Wei et
   al., CVPR 2016) and the commercial-licensing pointer
   *Reliability:* Official project documentation; the underlying papers are peer-reviewed and were
   **not** read in full for this review
2. **`[S2]`**
   *Source:* `ref_repo/openpose/openpose/doc/installation/1_prerequisites.md`
   *Reliability:* Official
3. **`[S3]`**
   *Source:* `ref_repo/openpose/openpose/doc/05_faq.md` — the 4 GB GPU memory note
   *Reliability:* Official
4. **`[S4]`**
   *Source:* `ref_repo/openpose/openpose/doc/06_maximizing_openpose_speed.md` — the 0.3 FPS COCO
   and 0.1 FPS `BODY_25` CPU figures, and the cuDNN and `net_resolution` advice
   *Reliability:* Official, self-reported. Not independently reproduced here
5. **`[S5]`**
   *Source:* `ref_repo/openpose/openpose/LICENSE` — the non-commercial software licence agreement
   *Reliability:* Primary. ⚠ Read as an engineer, not a lawyer. If any commercial path is
   contemplated the text must be read by someone qualified
6. **`[S6]`**
   *Source:* The clone itself at `5c5d965` (2024-08-02), `git describe` → `v1.7.0-73-g5c5d965`.
   All `file:line` citations resolve against this commit
   *Reliability:* Primary

---





# 11. CHANGE LOG
1. **2026-08-30** · *Author:* Claude (Opus 5)
   *Change:* Created from a read of the README, the licence, the installation prerequisites, the
   output and speed documentation, the standalone hand-detector guidance and
   `include/openpose/flags.hpp`. Recorded the non-commercial licence and the ~0.1 FPS CPU figure as
   two independent disqualifications, and the multiview-bootstrapping principle as the one idea
   worth carrying forward.
