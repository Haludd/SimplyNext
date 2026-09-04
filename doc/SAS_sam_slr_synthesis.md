**SAM-SLR — SYNTHESIS FOR SIMPLYNEXT**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field             | Value                                                           |
| :---------------- | :-------------------------------------------------------------- |
| **Code**          | `SAS`                                                           |
| **Status**        | Live                                                            |
| **Last reviewed** | 2026-09-04                                                      |
| **Scope**         | Short orientation to `RSA` and the two measurements it supplies |
| **Subject**       | `RSA` — `translation/sam-slr/CVPR21Chal-SLR/` at `de6c53a`      |
| **Full report**   | [`SAR`](../ref_repo/translation/sam-slr/SAR_sam_slr_report.md)  |

**For the team.** The **1st-place winner of the CVPR 2021 ChaLearn isolated sign language
recognition challenge**, in both the RGB and RGB-D tracks. Two of its tables change project
decisions: [`SAS_S3`](#3-the-table-that-settles-the-depth-camera) prices a depth camera at **one
percentage point**, and [`SAS_S4`](#4-twenty-seven-points) gives the smallest validated landmark
budget in `ref_repo/` — 27 points, portable to MediaPipe without translation. The complete analysis
is in [`SAR`](../ref_repo/translation/sam-slr/SAR_sam_slr_report.md), beside the clone in
`ref_repo/translation/sam-slr/`.

**For the assistant.** The licence is **contradictory and must never be described as permissive** —
[`SAS_S2`](#2-the-licence-contradiction). Treat `RSA` as non-commercial: cite it, re-implement from
the description, ship none of it. Where this file and
[`SAR`](../ref_repo/translation/sam-slr/SAR_sam_slr_report.md) disagree, `SAR` wins.

</details>

---





# 1. WHAT THIS IS
`jackyjsy/CVPR21Chal-SLR` is **Skeleton Aware Multi-modal Sign Language Recognition (SAM-SLR)**,
from the Smile Lab at Northeastern University, published at the **CVPR 2021 ChaLearn workshop**.
⚠ An extended SAM-SLR-v2 exists as a preprint; its additional claims are unrefereed.

The task is **isolated** recognition: one video, one sign, one label. Not continuous, not
translation.

The method is **six models in parallel, fused late** — skeleton graph, skeleton features, RGB
frames, RGB optical flow, depth HHA, depth flow — each emitting a probability vector over 226
classes. The fusion weights, `alpha = [1, 0.9, 0.4, 0.4]`, say which the authors trusted: **the
skeleton carries the highest weight of all.**

The clone is `de6c53a`, 2022-05-10. ⚠ **Abandoned** — the last commit is a data-split bug fix more
than four years before this review.

---





# 2. THE LICENCE CONTRADICTION
> **Warning — three statements exist and they do not agree.**

1. **`LICENSE`** — *"Creative Commons Legal Code / CC0 1.0 Universal"*: an unconditional
   public-domain dedication
2. **`readme.md`** — *"Licensed under the Creative Commons Zero v1.0 Universal license **with the
   following exceptions: The code is released for academic research use only. Commercial use is
   prohibited.**"*
3. **`SL-GCN/LICENSE`** — **CC BY-NC 4.0**, over the one directory the project would want

Statements 1 and 2 are incompatible: CC0 waives the rights a non-commercial exception would need to
rely on. What statement 2 shows is the authors' **intent** — non-commercial, attribution required —
and statement 3 puts that intent into a real licence over the skeleton model.

> **Treat `RSA` as non-commercial.** A hackathon team is not the right body to decide which
> statement controls, and a submission that could become a product is not *"academic research use
> only"* — the same reasoning that settled `ROP` in
> [`OPS_S2.1`](OPS_openpose_synthesis.md#21-the-licence). Cite it, re-implement, ship nothing.

> **Note — a fact is not copyrightable.** That 27 keypoints at named indices work well is a
> finding, and the project may act on it. What may not be copied is the code.

**The operational lesson: read every `LICENSE` in the tree, not just the root one.** A check that
stopped at the root here would have returned "public domain".

---





# 3. THE TABLE THAT SETTLES THE DEPTH CAMERA
AUTSL validation set, from the paper's Table 7. K = keypoints, F = skeleton features, R = RGB,
O = optical flow, H = depth HHA, D = depth flow:

| Ensemble  | K   | F   | R   | O   | H   | D   | Top-1     | Top-5     |
| :-------- | :-  | :-  | :-  | :-  | :-  | :-  | --------: | --------: |
| Skeleton  | ✓   | ✓   | --- | --- | --- | --- | **96.11** |     99.43 |
| RGB+Flow  | --- | --- | ✓   | ✓   | --- | --- |     95.77 |     99.52 |
| RGB All   | ✓   | ✓   | ✓   | ✓   | --- | --- |     96.96 |     99.68 |
| Depth     | --- | --- | --- | --- | ✓   | ✓   |     95.76 |     99.41 |
| RGB+D     | --- | --- | ✓   | ✓   | ✓   | ✓   |     96.27 |     99.66 |
| RGBD All  | ✓   | ✓   | ✓   | ✓   | ✓   | ✓   | **97.10** | **99.73** |

> **Skeleton alone: 96.11%. Every modality including a depth camera: 97.10%.** The difference is
> **0.99 points**, bought with two extra deep video models, two optical-flow computations and an
> RGB-D sensor. Adding depth to `RGB All` moves 96.96 → 97.10 — **0.14 points**.

Four readings:

1. **Depth is not worth a hardware dependency.** This is the quantitative form of
   [`ARC_S7.5`](../plan/ARC_architecture.md#75-p4p5--depth-and-glasses-as-roadmap-items), and far
   stronger than the argument-from-scalability alone
2. **The skeleton is the best single modality**, ahead of RGB+Flow and ahead of both depth
   modalities together
3. **The authors agreed** — the GCN gets the highest fusion weight
4. **Top-5 exceeds 99.4% in every row**, skeleton-only included. Design for a candidate set

**And pose beats pixels on the harder benchmark.** On WLASL-2000 — 2,000 classes of web video —
keypoints alone score **51.50%** top-1 against RGB frames' **47.51%**, with the six-modality
ensemble at 58.73%. Optical flow is the weakest modality at 40.46% and the second most expensive.

> **The same system scores 98.42% on AUTSL and 58.73% on WLASL-2000.** Two variables moved together
> — vocabulary 226 → 2,000, and studio → web video — so it isolates neither. What it establishes is
> the size of the combined effect: nearly **forty points**. Any accuracy figure quoted without its
> vocabulary size and recording conditions is uninterpretable.

---





# 4. TWENTY-SEVEN POINTS
Every configuration in the repository uses the `'27'` selection over COCO-WholeBody's 133 keypoints:

| Group      | Count | Content                         |
| :--------- | ----: | :------------------------------ |
| Body       |     7 | Nose, shoulders, elbows, wrists |
| Right hand |    10 | See below                       |
| Left hand  |    10 | The same ten, mirrored          |

**The face contributes nothing.** The nose is kept as a head anchor; eyes, ears and the 68 face-mesh
points are never touched by this stream.

**The ten hand points translate directly to MediaPipe.** COCO-WholeBody and MediaPipe share the
21-point hand topology and index order, so the local indices name the same landmarks in both:

| Index | MediaPipe landmark  |   | Index | MediaPipe landmark  |
| ----: | :------------------ | - | ----: | :------------------ |
|     0 | `WRIST`             |   |    12 | `MIDDLE_FINGER_TIP` |
|     4 | `THUMB_TIP`         |   |    13 | `RING_FINGER_MCP`   |
|     5 | `INDEX_FINGER_MCP`  |   |    16 | `RING_FINGER_TIP`   |
|     8 | `INDEX_FINGER_TIP`  |   |    17 | `PINKY_MCP`         |
|     9 | `MIDDLE_FINGER_MCP` |   |    20 | `PINKY_TIP`         |

The pattern is **the wrist, every fingertip, and the base knuckle of every finger except the
thumb** — a handshape described by where the fingertips sit relative to the knuckles that anchor
them.

> **This is a directly usable constant.** No coordinate translation, no re-derivation, and no code
> from this repository: a list of ten integers a CVPR-winning system validated. It is the low end
> of the landmark budget in [`ARC_S3.2`](../plan/ARC_architecture.md#32-the-landmark-budget), with
> [`SLS_S5`](SLS_slrt_synthesis.md#5-the-keypoint-budget)'s 63–79 as the high end.

**The bone graph joins the wrists.** Of 26 edges over the 27 nodes, two — body wrist to hand wrist,
on each side — are the whole point. Without them the graph is three disconnected components and the
network cannot relate a handshape to its position in signing space. It is the graph form of the
body-relative normalisation
[`ARC_S4.3`](../plan/ARC_architecture.md#43-recommended-representation) specifies.

---





# 5. TWO ENGINEERING DETAILS
**Bone and motion streams are free features.** The same architecture is trained four times over
four derived representations — `joint`, `bone`, `joint_motion`, `bone_motion` — then ensembled.
*Bone* is the vector between connected joints; *motion* is the temporal difference. Both are NumPy
operations on an array the project already has. The cheap version — concatenating bone vectors and
frame differences into one feature vector — is what
[`ARC_S4.3`](../plan/ARC_architecture.md#43-recommended-representation) step 4 should specify.

> **Warning — one augmentation not to copy.** The training config sets `random_mirror: True` at
> `p=0.5`: half of all samples are horizontally mirrored. **Mirroring swaps the dominant hand.**
> Where dominant and non-dominant hands carry different grammatical roles — the premise of
> [`ARC_S3.2`](../plan/ARC_architecture.md#32-the-landmark-budget) item 2 and of the
> handedness-averaging rule in
> [`ARC_S6.5`](../plan/ARC_architecture.md#65-perception-engineering-rules) rule 5 — a mirrored
> sample is a sample of a *different* articulation. Defensible for a 226-class isolated benchmark;
> not defensible for a system whose downstream layer reasons about which hand did what. The
> temporal augmentations in the same file (`random_choose`, `random_shift`) are safe.

---





# 6. THE NINE LESSONS
| #  | Lesson                                                                                     |
| :- | :----------------------------------------------------------------------------------------- |
| A1 | **A depth camera bought 0.99 points.** The strongest anti-hardware argument available      |
| A2 | **Keypoints beat RGB frames on in-the-wild data** — 51.50 vs 47.51 on WLASL-2000           |
| A3 | **Ten points per hand is enough**: wrist, five fingertips, four knuckles                   |
| A4 | **Connect the hand wrist to the body wrist**, or the graph has three components            |
| A5 | **Bone and motion streams are free features**, derived with NumPy                          |
| A6 | **Optical flow is the worst return on compute** of the six modalities                      |
| A7 | **Top-5 exceeds 99% on a closed 226-class vocabulary.** Design for a candidate set         |
| A8 | **Read every `LICENSE` in the tree, not just the root one** — they disagreed here          |
| A9 | **Mirroring is not a safe augmentation** where handedness is grammatical                   |

---





# 7. WHAT IT DOES NOT DO
1. **No continuous recognition.** One video, one label. Segmentation is assumed away
2. **No translation.** A class index is not a sentence
3. **No keypoint extraction.** The pose step lives in a separate repository not in this clone
4. **No real-time operation**, and no claim to it — six models plus optical flow per clip
5. **No multi-person handling.** `num_person: 1`
6. **No calibrated confidence.** A weighted score sum and an argmax, with hand-tuned weights
7. **No use of the face.** Defensible for 226 isolated signs; a known gap for non-manual grammar

---





# 8. RUNNING IT
Not attempted, and not recommended: PyTorch 1.7 on Python 3.7, four GPUs for one stream of one
modality at 250 epochs, nine trained models to reproduce the submission, weights on Google Drive
whose four-year-old links are ⚠ unverified — and a licence that forbids the only outcome that
would matter.

The checked-in `ensemble/*.pkl` prediction files make the final fusion step reproducible without a
GPU, which reproduces a number this synthesis has already transcribed.

**What the project does instead:** takes the ten hand indices from [`SAS_S4`](#4-twenty-seven-points)
and the ablation table from [`SAS_S3`](#3-the-table-that-settles-the-depth-camera) into `ARC` and
the deck, and writes its own classifier.

---





# 9. WHERE TO GO NEXT
| Question                     | Document                                                       |
| :--------------------------- | :------------------------------------------------------------- |
| Full breakdown               | [`SAR`](../ref_repo/translation/sam-slr/SAR_sam_slr_report.md) |
| The larger keypoint budget   | [`SLS_S5`](SLS_slrt_synthesis.md)                              |
| The pose library             | [`SPS`](SPS_sign_pose_synthesis.md)                            |
| Why depth is a roadmap item  | [`ARC_S7.5`](../plan/ARC_architecture.md)                      |
| How the submission is scored | [`JCR`](../plan/JCR_judging_criteria.md)                       |
| Where documents live         | [`RIX`](../ref_index.md)                                       |

---





# 10. CHANGE LOG
1. **2026-09-04** · *Author:* Claude (Opus 5)
   *Change:* Created alongside [`SAR`](../ref_repo/translation/sam-slr/SAR_sam_slr_report.md), from
   a read of the README, both licence files, the keypoint-selection and graph code, the training
   configuration, the ensemble weights and the three results tables in `img/`.
