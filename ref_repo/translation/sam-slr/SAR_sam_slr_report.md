**SAM-SLR — FULL REPOSITORY REPORT**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field                   | Value                                                      |
| :---------------------- | :--------------------------------------------------------- |
| **Code**                | `SAR`                                                      |
| **Status**              | Live                                                       |
| **Last reviewed**       | 2026-09-04                                                 |
| **Source of truth for** | Analysis of the SAM-SLR reference clone                    |
| **Parent**              | [`RIX_S2.1`](../../../ref_index.md#21-live-documents)      |
| **Short version**       | [`SAS`](../../../doc/SAS_sam_slr_synthesis.md)             |
| **Subject**             | `RSA` — `translation/sam-slr/CVPR21Chal-SLR/` at `de6c53a` |

**For the team.** `jackyjsy/CVPR21Chal-SLR` is the **1st-place winner of the CVPR 2021 ChaLearn
Isolated Sign Language Recognition challenge**, in both the RGB and RGB-D tracks. Two things in it
change project decisions. [`SAR_S4`](#4-the-27-keypoint-budget) is the smallest landmark budget any
winning system has used — **27 points**, mapping one-to-one onto MediaPipe's own indices.
[`SAR_S5.2`](#52-what-each-modality-actually-contributes) measures skeleton-only against a
six-modality RGB-D ensemble and finds **one percentage point** between them. That single row is the
strongest evidence in `ref_repo/` for the pose-only, no-depth-camera architecture.

**For the assistant.** The licence is **contradictory and must never be described as permissive** —
[`SAR_S2.2`](#22-licence). The `LICENSE` file says CC0; the README attaches a non-commercial
restriction to it; and the sub-directory that matters carries CC BY-NC 4.0. Treat `RSA` as
**non-commercial**: cite it, re-implement from the description, ship none of it. Nothing inside
`ref_repo/translation/sam-slr/CVPR21Chal-SLR/` may be edited; it is an unmodified clone, excluded
from version control.

</details>

---





# 1. EXECUTIVE SUMMARY
## 1.1. What This Repository Is
`ref_repo/translation/sam-slr/CVPR21Chal-SLR/` is **Skeleton Aware Multi-modal Sign Language
Recognition (SAM-SLR)**, from the Smile Lab at Northeastern University. Its README states that it
*"ranked 1st in CVPR 2021 Challenge: Looking at People Large Scale Signer Independent Isolated Sign
Language Recognition"* `[S1]`, a claim the repository substantiates with the organisers' own
announcement image naming `smilelab2021` as the 1st-place team in both tracks `[S2]`.

The published record is a **CVPR 2021 Workshop paper** (ChaLearn LAP), with an extended version,
SAM-SLR-v2, released as a preprint `[S1]`. ⚠ The workshop paper is peer-reviewed; the v2 extension
is a preprint and its additional claims are not.

The task is **isolated** sign language recognition: one video, one sign, one label. It is not
continuous recognition and not translation.




## 1.2. Why It Matters to SimplyNext
It matters for two measurements and one architecture, and for nothing else.

1. **As the depth-camera argument, settled with a number** · *Use:*
   [`SAR_S5.2`](#52-what-each-modality-actually-contributes) shows skeleton-only at **96.11%** and
   a six-modality RGB-D ensemble at **97.10%** on the same validation set. Depth plus RGB plus
   optical flow buys **0.99 points**. That is the evidence behind
   [`ARC_S7.5`](../../../plan/ARC_architecture.md#75-p4p5--depth-and-glasses-as-roadmap-items)
2. **As the pose-versus-RGB argument** · *Use:* On WLASL-2000, the keypoint modality alone scores
   **51.50%** top-1 against RGB frames' **47.51%** `[S3]`. Pose beats pixels on the harder
   benchmark. [`ARC_S4.1`](../../../plan/ARC_architecture.md#41-verdict-right-instinct-over-specified)
   currently rests this claim on a preprint survey; this is a better citation
3. **As the smallest credible landmark budget** · *Use:* 27 keypoints — 7 body, 10 per hand — and
   **no face at all** in the skeleton stream. The hand selection maps directly onto MediaPipe's
   indices, so it is portable without translation — [`SAR_S4`](#4-the-27-keypoint-budget)
4. **As a licence lesson** · *Use:* A repository can carry a permissive licence *file* and a
   restrictive licence *statement*. [`SAR_S2.2`](#22-licence) is the third time in `ref_repo/` that
   reading the licence changed the verdict

Against the four MVP steps in [`SCR`](../../../plan/scribbles.md):

1. **1. Isolate the subject** — not addressed. AUTSL videos are pre-cropped, one signer, studio
   conditions
2. **2. Track many points** — the opposite: it demonstrates how **few** points suffice
3. **3. Points → skeleton** — the SL-GCN stream is exactly a skeleton model, with an explicit
   graph of bones — [`SAR_S6`](#6-sl-gcn--the-skeleton-model)
4. **4. Skeleton → conversational text** — not attempted. Isolated classification stops at a label




## 1.3. Summary
Six parallel models, one per modality — skeleton graph, skeleton features, RGB frames, RGB optical
flow, depth HHA, depth flow — each producing a probability vector over 226 classes, combined by a
**weighted late fusion** with hand-tuned weights. The skeleton branch is a Sign Language Graph
Convolution Network (SL-GCN): a decoupled spatial-temporal GCN over a 27-node graph whose edges are
the bones of the upper body and both hands, trained in four streams (joint, bone, joint-motion,
bone-motion) that are themselves ensembled. The fusion weights `[1, 0.9, 0.4, 0.4]` `[S4]` say
plainly which modality the authors trusted: **the skeleton gets the highest weight of all.**

---





# 2. PROVENANCE, LICENCE AND REQUIREMENTS
## 2.1. Provenance
1. **Publisher**
   Songyao Jiang, Bin Sun, Lichen Wang, Yue Bai, Kunpeng Li and Yun Fu — Smile Lab, Northeastern
   University, Boston. Remote: `https://github.com/jackyjsy/CVPR21Chal-SLR.git`
2. **Clone state**
   `de6c53a`, 2022-05-10, *"fixe train_val issue #23"* — sic
3. **Maintenance status**
   ⚠ **Abandoned.** The last commit is more than four years before this review, and it is a bug
   fix to a data split. This is a competition artefact, not a maintained library
4. **Scale**
   110 MB on disk, of which most is the checked-in `.pkl` prediction files used to reproduce the
   challenge submission without re-running the models
5. **Language**
   Python 3.7, PyTorch 1.7.1, per the README's own badges `[S1]`




## 2.2. Licence
> **Warning — the licence is self-contradictory, and the contradiction resolves against use.**

Three statements exist in the repository, and they do not agree:

1. **`LICENSE` (repository root)** — *"Creative Commons Legal Code / CC0 1.0 Universal"*. CC0 is a
   **public-domain dedication**: an unconditional waiver of all copyright, with no conditions
   whatsoever
2. **`readme.md`, the *License* section** — *"Licensed under the Creative Commons Zero v1.0
   Universal license **with the following exceptions: The code is released for academic research
   use only. Commercial use is prohibited.** Published versions (changed or unchanged) must include
   a reference to the origin of the code."* `[S1]`
3. **`SL-GCN/LICENSE`** — *"Attribution-NonCommercial 4.0 International"*, i.e. **CC BY-NC 4.0**
   `[S10]`

Statements 1 and 2 are incompatible as a matter of licence construction: CC0 cannot carry a
non-commercial exception, because CC0's entire operation is to waive the rights that such an
exception would rely on. What statement 2 demonstrates, however, is the authors' **stated
intent** — non-commercial, attribution required. Statement 3 puts that intent into a real licence,
and it does so over `SL-GCN/`, **the one directory the project would otherwise want**.

> **Warning — treat `RSA` as non-commercial.** Three reasons, any one sufficient.
> **(a)** The directory carrying the skeleton model is unambiguously CC BY-NC 4.0.
> **(b)** Where a file and a README disagree, a hackathon team is not the right body to decide
> which controls; the conservative reading is the only defensible one.
> **(c)** A submission that could plausibly become a product is not *"academic research use only"*
> — the same reasoning that settled `ROP` in
> [`OPR_S2.2`](../../tracking/openpose/OPR_openpose_report.md#22-licence).
> The practical rule is identical to `ROP` and `RSL`: **cite it, re-implement ideas from the
> description, ship nothing.**

> **Note — what is unencumbered.** A **fact** is not copyrightable. That 27 keypoints at specified
> indices work well is a finding, not code; the project may act on it. What may not be copied is
> `decouple_gcn_attn.py` and its siblings.




## 2.3. Requirements
From the README and the per-folder `requirements.txt` files `[S1]`:

1. **Python and framework** — *"Anaconda Python >= 3.6 and Pytorch 1.7 with OpenCV"*. ⚠ PyTorch
   1.7 is a 2020 release
2. **The maintainers ship an Nvidia Docker image** and offer it as the convenience path, which is
   the same signal `RSL` gives
3. **Training hardware** — `SL-GCN/config/sign/train/train_joint.yaml` sets `device: [0,1,2,3]` —
   **four GPUs** — with `num_epoch: 250` `[S5]`. And that is one stream of one modality; the full
   submission is four GCN streams plus five other models
4. **Pretrained models and processed data** — Google Drive links. ⚠ Not a permanent archive
5. **Data** — AUTSL, from ChaLearn, obtained through the CodaLab competition page




## 2.4. The Dataset, Which Explains the Numbers
AUTSL is Turkish Sign Language: **226 classes, 36,302 samples, 43 signers**, recorded RGB-D
`[S6]`. Two properties matter when reading [`SAR_S5`](#5-the-numbers):

1. **It is signer-independent by construction** — the challenge's whole point. Test signers do not
   appear in training. This is the property
   [`LTR_S4.1`](../signlang-literature/LTR_signlang_literature_report.md#41-sign-language-detection)
   records as routinely violated elsewhere, and it makes AUTSL numbers unusually trustworthy
2. **It is a studio corpus, not the wild.** Controlled background, consistent framing, one signer,
   prompted vocabulary. The **same system** scores 98.42% here and 58.73% on WLASL-2000, which is
   web video — [`SAR_S5.3`](#53-the-same-system-on-a-harder-benchmark)

---





# 3. REPOSITORY MAP
```text
ref_repo/translation/sam-slr/
├── SAR_sam_slr_report.md                 — this document (tracked in git)
└── CVPR21Chal-SLR/                       — the clone (git-ignored)
    ├── SL-GCN/                  Skeleton graph network ← the part worth reading
    │   ├── data_gen/sign_gendata.py      The 27-keypoint selection ← 6 lines that matter
    │   ├── graph/sign_27.py              The bone graph
    │   ├── model/decouple_gcn_attn.py    The network (CC BY-NC — do not copy)
    │   └── LICENSE                       CC BY-NC 4.0 ← read this
    ├── SSTCN/                   Separable spatial-temporal conv over skeleton features
    ├── Conv3D/                  RGB, optical flow, depth HHA, depth flow — four models
    ├── ensemble/                Late fusion + checked-in .pkl predictions
    ├── data-prepare/            Pointer to a separate repository
    ├── img/                     The results tables, as images ← the numbers live here
    ├── CVPR21W_SAM-SLR.pdf      The workshop presentation (slides, not the paper)
    ├── LICENSE                  CC0 1.0 ← and this, and note they disagree
    └── readme.md
```

**Worth reading:** `SL-GCN/data_gen/sign_gendata.py:10-15` (the keypoint budget),
`SL-GCN/graph/sign_27.py:5-13` (the bone graph), `SL-GCN/config/sign/train/train_joint.yaml` (every
training hyper-parameter in one file), `ensemble/ensemble_multimodal_rgb.py:20` (the fusion
weights), `img/AUTSL_val.jpg` and `img/WLASL2000.jpg` (the ablation tables), and both licence files.

**Not worth reading:** `Conv3D/` (twelve near-identical training scripts, one per modality × phase),
`CVPR21W_SAM-SLR.pdf` (⚠ it is the *presentation deck with speaker notes*, not the paper; the
results tables in it are rendered images and its extractable text is narration).

> **Note — the numbers are in `img/*.jpg`, not in text.** The performance tables reproduced in
> [`SAR_S5`](#5-the-numbers) were read from the images `AUTSL_val.jpg`, `AUTSL_test.jpg` and
> `WLASL2000.jpg`, which are the paper's Tables 7, 8 and the WLASL table respectively. They are
> primary in the sense of being the authors' own figures, and ⚠ transcribed by eye for this report.

---





# 4. THE 27-KEYPOINT BUDGET
`SL-GCN/data_gen/sign_gendata.py:10-15` `[S7]`:

```python
selected_joints = {
    '59': np.concatenate((np.arange(0,17), np.arange(91,133)), axis=0), #59
    '31': np.concatenate((np.arange(0,11), [91,95,96,99,100,103,104,107,108,111],
                                           [112,116,117,120,121,124,125,128,129,132]), axis=0), #31
    '27': np.concatenate(([0,5,6,7,8,9,10],
                          [91,95,96,99,100,103,104,107,108,111],
                          [112,116,117,120,121,124,125,128,129,132]), axis=0) #27
}
```

Every training and test configuration in the repository uses `'27'` — the training config sets
`num_point: 27` and `graph: graph.sign_27.Graph` `[S5]`. The 59- and 31-point variants are kept but
unused.




## 4.1. What the 27 Points Are
The source indices are **COCO-WholeBody**, where 0–16 are body, 91–111 the first hand and 112–132
the second.

1. **Body** · *Count:* 7 · *Content:* Nose, shoulders, elbows, wrists
   *Source indices:* `0, 5, 6, 7, 8, 9, 10`
2. **Right hand** · *Count:* 10 · *Content:* See below
   *Source indices:* `91, 95, 96, 99, 100, 103, 104, 107, 108, 111`
3. **Left hand** · *Count:* 10 · *Content:* The same ten, mirrored
   *Source indices:* `112, 116, 117, 120, 121, 124, 125, 128, 129, 132`

**The face contributes nothing.** Index 0 is the nose, kept as a head anchor; indices 1–4 (eyes and
ears) are excluded, and the 68 face-mesh points at 23–90 are never touched by this stream.




## 4.2. The Hand Selection, Translated to MediaPipe
Subtracting the hand's base index turns the ten absolute indices into local ones:

`91 → 0` · `95 → 4` · `96 → 5` · `99 → 8` · `100 → 9` · `103 → 12` · `104 → 13` · `107 → 16` ·
`108 → 17` · `111 → 20`

**COCO-WholeBody and MediaPipe use the same 21-point hand topology and the same index order**, so
those local indices name the same anatomical landmarks in both:

| Local index | MediaPipe landmark  | Role              |
| ----------: | :------------------ | :---------------- |
|           0 | `WRIST`             | The hand's origin |
|           4 | `THUMB_TIP`         | Fingertip         |
|           5 | `INDEX_FINGER_MCP`  | Knuckle           |
|           8 | `INDEX_FINGER_TIP`  | Fingertip         |
|           9 | `MIDDLE_FINGER_MCP` | Knuckle           |
|          12 | `MIDDLE_FINGER_TIP` | Fingertip         |
|          13 | `RING_FINGER_MCP`   | Knuckle           |
|          16 | `RING_FINGER_TIP`   | Fingertip         |
|          17 | `PINKY_MCP`         | Knuckle           |
|          20 | `PINKY_TIP`         | Fingertip         |

The pattern is exactly: **the wrist, every fingertip, and the base knuckle of every finger except
the thumb.** The intermediate joints — PIP, DIP, and the thumb's CMC and MCP — are dropped. A
handshape is described by where the fingertips are relative to the knuckles that anchor them, which
is a defensible compression of a 21-point hand into 10.

> **Decision consequence.** This is a **directly usable constant** for the project. It requires no
> coordinate translation, no re-derivation, and no code from this repository — it is a list of ten
> integers that a CVPR-winning system validated. Recorded in
> [`ARC_S3.2`](../../../plan/ARC_architecture.md#32-the-landmark-budget) as the low end of the
> landmark budget, against `RSL`'s 63–79 as the high end.




## 4.3. The Bone Graph
`SL-GCN/graph/sign_27.py:5-13` `[S8]` defines 26 directed edges over the 27 nodes: the shoulder →
elbow → wrist chains for both arms, a five-way star from each hand's wrist to its five knuckle-or-tip
points, the four finger chains within each hand, and two edges — `(10,12)` and `(11,22)` — that
**join each body wrist to the corresponding hand wrist**.

Those last two edges are the whole point. Without them the graph is three disconnected components
and the network cannot relate a handshape to its position in signing space. This is the graph
equivalent of the body-relative normalisation
[`ARC_S4.3`](../../../plan/ARC_architecture.md#43-recommended-representation) specifies, and of
`RSP`'s `correct_wrists()` —
[`SPR_S5.4`](../sign-pose/SPR_sign_pose_report.md#54-wrist-correction).

---





# 5. THE NUMBERS
## 5.1. The Challenge Result
`img/AUTSL_test.jpg`, the paper's Table 8 `[S9]` — AUTSL **test** set, top-1 accuracy:

| System              | Track | Top-1     |
| :------------------ | :---- | --------: |
| Challenge baseline  | RGB   |     49.23 |
| Challenge baseline  | RGB-D |     62.03 |
| SAM-SLR ensemble    | RGB   |     97.51 |
| SAM-SLR ensemble    | RGB-D |     97.68 |
| SAM-SLR, fine-tuned | RGB   | **98.42** |
| SAM-SLR, fine-tuned | RGB-D | **98.53** |

The *"w/ Val"* rows fold the validation set into training before the final test submission — a
legitimate competition practice, and the reason the headline number is 98.42 rather than 97.51.




## 5.2. What Each Modality Actually Contributes
`img/AUTSL_val.jpg`, the paper's Table 7 `[S9]` — AUTSL **validation** set. K = keypoints,
F = skeleton features, R = RGB, O = optical flow, H = depth HHA, D = depth flow:

| Ensemble  | K   | F   | R   | O   | H   | D   | Top-1     | Top-5     |
| :-------- | :-  | :-  | :-  | :-  | :-  | :-  | --------: | --------: |
| Skeleton  | ✓   | ✓   | --- | --- | --- | --- | **96.11** |     99.43 |
| RGB+Flow  | --- | --- | ✓   | ✓   | --- | --- |     95.77 |     99.52 |
| RGB All   | ✓   | ✓   | ✓   | ✓   | --- | --- |     96.96 |     99.68 |
| Depth     | --- | --- | --- | --- | ✓   | ✓   |     95.76 |     99.41 |
| RGB+D     | --- | --- | ✓   | ✓   | ✓   | ✓   |     96.27 |     99.66 |
| RGBD All  | ✓   | ✓   | ✓   | ✓   | ✓   | ✓   | **97.10** | **99.73** |

> **This is the most important table in this report.** Read the first and last rows together.
> **Skeleton alone: 96.11%. Every modality the authors had, including a depth camera: 97.10%.** The
> difference is **0.99 percentage points**, bought with two extra deep video models, two optical
> flow computations, and an RGB-D sensor.

Four readings, in descending order of consequence for the project:

1. **Depth is not worth a hardware dependency.** Adding both depth modalities to `RGB All` moves
   96.96 → 97.10, a gain of **0.14 points**. That is the quantitative form of
   [`ARC_S7.5`](../../../plan/ARC_architecture.md#75-p4p5--depth-and-glasses-as-roadmap-items)'s
   argument, and it is far stronger than the argument-from-scalability the document currently
   makes alone
2. **The skeleton stream is the best single modality**, ahead of RGB+Flow (96.11 vs 95.77) and
   ahead of both depth modalities together (95.76)
3. **The authors agreed.** The late-fusion weights in `ensemble/ensemble_multimodal_rgb.py:20` are
   `alpha = [1, 0.9, 0.4, 0.4]` for GCN, RGB, colour flow and the fourth stream `[S4]`. **The
   skeleton carries the highest weight.**
4. **Top-5 is above 99.4% in every row**, including skeleton-only. On a 226-class closed
   vocabulary the correct sign is essentially always in the top five — which is the same finding
   [`SLR_S5.2`](../slrt/SLR_slrt_report.md#52-recognition-accuracy-against-vocabulary-size) reports
   at larger vocabularies, and the same argument for a top-k lattice




## 5.3. The Same System on a Harder Benchmark
`img/WLASL2000.jpg` `[S3]` — WLASL-2000, 2,000 classes of web video:

| Modality     | P-I Top-1 | P-I Top-5 | P-C Top-1 | P-C Top-5 |
| :----------- | --------: | --------: | --------: | --------: |
| Keypoints    | **51.50** |     84.94 |     48.87 |     84.02 |
| Features     |     46.84 |     79.63 |     44.41 |     78.35 |
| RGB Frames   |     47.51 |     80.31 |     44.53 |     78.93 |
| RGB Flow     |     40.46 |     73.23 |     37.88 |     71.86 |
| Key + RGB    |     57.55 |     90.34 |     54.83 |     89.75 |
| Ensemble All | **58.73** |     91.46 |     55.93 |     90.94 |

> **The same architecture scores 98.42% on AUTSL and 58.73% on WLASL-2000.** Two variables changed
> together — the vocabulary grew from 226 to 2,000, and the recording moved from a studio to the
> web — so this comparison does **not** isolate either. What it does establish is the size of the
> combined effect: nearly **forty points**. Any demonstration figure quoted without naming its
> vocabulary size and recording conditions is uninterpretable.

Two further points from this table:

1. **Keypoints beat RGB frames** — 51.50 against 47.51 — on the harder, in-the-wild benchmark.
   Pose is not merely the cheap option; on this data it is the better one
2. **Optical flow is the weakest modality** at 40.46, and it is the second most expensive to
   compute. Where the project needs motion, explicit landmark velocity is the cheaper route —
   [`ARC_S4.3`](../../../plan/ARC_architecture.md#43-recommended-representation) step 4

---





# 6. SL-GCN — THE SKELETON MODEL
Described, not reproduced; the code is CC BY-NC 4.0.

The model is a **decoupled spatial-temporal graph convolutional network with attention and
drop-graph regularisation**, adapted from `DecoupleGCN-DropGraph`, which the README credits `[S1]`.
Its configuration is small enough to state completely `[S5]`:

| Parameter     | Value                    | Note                                       |
| :------------ | :----------------------- | :----------------------------------------- |
| `num_class`   | `226`                    | AUTSL vocabulary                           |
| `num_point`   | `27`                     | [`SAR_S4`](#4-the-27-keypoint-budget)      |
| `num_person`  | `1`                      | **Single signer, by construction**         |
| `groups`      | `16`                     | Decoupling groups in the graph convolution |
| `block_size`  | `41`                     | Drop-graph block size                      |
| `window_size` | `100`                    | 100 frames per sample                      |
| `batch_size`  | `64`                     | ---                                        |
| `num_epoch`   | `250`                    | With `warm_up_epoch: 20`                   |
| `base_lr`     | `0.1`, steps at 150, 200 | SGD with Nesterov momentum                 |

**Four streams, not one.** The same architecture is trained four times over four derived
representations — `joint`, `bone`, `joint_motion`, `bone_motion` — generated by
`data_gen/gen_bone_data.py` and `data_gen/gen_motion.py`, and the four are then ensembled. *Bone*
is the vector between connected joints; *motion* is the temporal difference. This is a standard
skeleton-action-recognition practice, and it is worth naming because it is **free feature
engineering**: differences and temporal deltas of an existing 27×3 array, computed with NumPy.

> **Note — this corroborates
> [`ARC_S4.3`](../../../plan/ARC_architecture.md#43-recommended-representation) step 4.** The
> document already proposes adding velocity and acceleration as explicit derived features rather
> than hoping the model infers them. SAM-SLR goes further and trains separate models on them. The
> cheap version — concatenating bone vectors and frame differences into one feature vector — is
> what the project should do.




## 6.1. One Augmentation Not to Copy
`train_joint.yaml` sets `random_mirror: True` with `random_mirror_p: 0.5` `[S5]` — half of all
training samples are horizontally mirrored.

> **Warning — mirroring swaps the dominant hand.** In sign languages where the dominant and
> non-dominant hands carry different grammatical roles — the premise of
> [`ARC_S3.2`](../../../plan/ARC_architecture.md#32-the-landmark-budget) item 2 and of the
> handedness-averaging rule in
> [`ARC_S6.5`](../../../plan/ARC_architecture.md#65-perception-engineering-rules) rule 5 — a
> mirrored sample is a sample of a *different* articulation. It is defensible for a 226-class
> isolated benchmark where left- and right-dominant signers must both be recognised, and it is
> **not** defensible for a system whose downstream layer reasons about which hand did what. Do not
> port this augmentation without deciding that question explicitly.

Other augmentations in the same file are safe and worth keeping: `random_choose` and `random_shift`
over the 100-frame window (temporal jitter) and `normalization: True`.

---





# 7. WHAT THE REPOSITORY DOES NOT DO
1. **It does not do continuous recognition.** One video in, one label out. Segmentation —
   [`ARC_S5.1`](../../../plan/ARC_architecture.md#51-three-problems-inside-step-4) problem 1 — is
   assumed away
2. **It does not translate.** A class index is not a sentence
3. **It does not extract keypoints.** `data-prepare/` points at a *separate* repository, and the
   wholebody pose step is described as *"Use TPose/data_process to extract wholebody pose
   features"* `[S1]` — a directory that is not in this clone
4. **It does not run in real time**, and makes no claim to. Six models plus optical flow per clip
5. **It does not handle more than one person.** `num_person: 1`
6. **It does not express calibrated confidence.** The ensemble sums weighted scores and takes an
   argmax; the weights are hand-tuned on validation data
7. **It does not use the face.** For a system whose task is 226 isolated Turkish signs this is
   defensible; for a system that must read non-manual grammar it is a known gap —
   [`ARC_S3.1`](../../../plan/ARC_architecture.md#31-verdict-confirmed-with-a-corrected-objective)

---





# 8. RUNNING IT
Not attempted, and not recommended.

1. **PyTorch 1.7 on Python 3.7** — a 2020 stack, with the same age problem as `RSL`
2. **Four GPUs for one stream of one modality**, 250 epochs
3. **Reproducing the submission requires nine trained models** plus the ensemble step
4. **The pretrained weights are on Google Drive**, and ⚠ their continued availability four years
   on is unverified
5. **The licence forbids the only outcome that would matter** — [`SAR_S2.2`](#22-licence)

The repository does ship `ensemble/*.pkl` — the per-modality prediction files — which means the
*final ensemble step alone* is reproducible without a GPU. That is a curiosity rather than a use:
it reproduces a number this report has already transcribed.

**What the project does instead:** takes the ten hand indices from
[`SAR_S4.2`](#42-the-hand-selection-translated-to-mediapipe), takes the ablation table from
[`SAR_S5.2`](#52-what-each-modality-actually-contributes) into `ARC` and the deck, and writes its
own classifier.

---





# 9. RELEVANCE TO SIMPLYNEXT
## 9.1. Lessons to Carry Across
| #  | Lesson                                                                                     |
| :- | :----------------------------------------------------------------------------------------- |
| A1 | **A depth camera bought 0.99 points.** The strongest anti-hardware argument available      |
| A2 | **Keypoints beat RGB frames on in-the-wild data** — 51.50 vs 47.51 on WLASL-2000           |
| A3 | **Ten points per hand is enough**: wrist, five fingertips, four knuckles                   |
| A4 | **Connect the hand wrist to the body wrist**, or the graph has three components            |
| A5 | **Bone and motion streams are free features**, derived from the same array with NumPy      |
| A6 | **Optical flow is the worst return on compute** of the six modalities                      |
| A7 | **Top-5 exceeds 99% on a closed 226-class vocabulary.** Design for a candidate set         |
| A8 | **Read every `LICENSE` in the tree, not just the root one** — they disagreed here          |
| A9 | **Mirroring is not a safe augmentation** where handedness is grammatical                   |

A8 is the operational lesson. The root file said CC0; the directory the project cared about said
CC BY-NC. A check that stops at the root gets the wrong answer.




## 9.2. What the Project Takes
1. **The modality ablation** · *Take:* Skeleton 96.11 vs RGBD-All 97.10 on AUTSL validation ·
   *Where:* [`ARC_S7.5`](../../../plan/ARC_architecture.md#75-p4p5--depth-and-glasses-as-roadmap-items),
   and the roadmap slide
2. **The pose-beats-RGB figure** · *Take:* 51.50 vs 47.51, WLASL-2000 ·
   *Where:* [`ARC_S4.1`](../../../plan/ARC_architecture.md#41-verdict-right-instinct-over-specified),
   replacing a preprint citation
3. **The ten hand indices** · *Take:* `0, 4, 5, 8, 9, 12, 13, 16, 17, 20`, MediaPipe-native ·
   *Where:* [`ARC_S3.2`](../../../plan/ARC_architecture.md#32-the-landmark-budget)
4. **The wrist-joining edges** · *Take:* Body wrist ↔ hand wrist must be connected ·
   *Where:* [`ARC_S4.3`](../../../plan/ARC_architecture.md#43-recommended-representation)
5. **Bone and motion derivations** · *Take:* Concatenate bone vectors and frame differences ·
   *Where:* [`ARC_S4.3`](../../../plan/ARC_architecture.md#43-recommended-representation) step 4
6. **The benchmark-conditions warning** · *Take:* 98.42 and 58.73 from one system ·
   *Where:* `EVL`, and the honesty section of the deck
7. **The mirroring caveat** · *Take:* Do not mirror where handedness is grammatical ·
   *Where:* `EVL` data protocol




## 9.3. What the Project Does Not Take
1. **Any code**, and specifically nothing from `SL-GCN/` — CC BY-NC 4.0
2. **The ensemble architecture.** Nine models is not a real-time laptop pipeline
3. **The depth modalities.** [`SAR_S5.2`](#52-what-each-modality-actually-contributes) prices them
4. **The mirroring augmentation.** [`SAR_S6.1`](#61-one-augmentation-not-to-copy)
5. **The `98.42%` headline as a comparison target.** It is 226 studio classes; the project's number
   will not be comparable and must not be presented as though it were

---





# 10. SOURCES
1. **`[S1]`**
   *Source:* `ref_repo/translation/sam-slr/CVPR21Chal-SLR/readme.md` at `de6c53a` — the challenge
   claim, the requirements, the licence statement, the citations and the reference list
   *Reliability:* Official project documentation. The CVPR 2021 Workshop paper is peer-reviewed and
   was **not** read in full; ⚠ the SAM-SLR-v2 extension is a preprint
2. **`[S2]`**
   *Source:* `ref_repo/translation/sam-slr/CVPR21Chal-SLR/img/challenge_result.jpg` — the
   organisers' announcement naming `smilelab2021` 1st place on both tracks
   *Reliability:* Primary, as a reproduction of the organisers' own post. ⚠ Read from an image
3. **`[S3]`**
   *Source:* `ref_repo/translation/sam-slr/CVPR21Chal-SLR/img/WLASL2000.jpg` — multi-modal
   performance on WLASL-2000
   *Reliability:* The authors' own figure. ⚠ Transcribed by eye from an image for this report
4. **`[S4]`**
   *Source:* `ref_repo/translation/sam-slr/CVPR21Chal-SLR/ensemble/ensemble_multimodal_rgb.py:20`
   — `alpha = [1,0.9,0.4,0.4]`
   *Reliability:* Primary — read from the clone
5. **`[S5]`**
   *Source:* `ref_repo/translation/sam-slr/CVPR21Chal-SLR/SL-GCN/config/sign/train/train_joint.yaml`
   — the full training configuration
   *Reliability:* Primary — read from the clone
6. **`[S6]`**
   *Source:* AUTSL's entry in the sign-language-processing dataset registry —
   [`LTR_S6`](../signlang-literature/LTR_signlang_literature_report.md#6-datasets); 226 items,
   36,302 samples, 43 signers, RGB-D
   *Reliability:* Secondary — a maintained community registry. Consistent with the ChaLearn
   challenge description
7. **`[S7]`**
   *Source:* `ref_repo/translation/sam-slr/CVPR21Chal-SLR/SL-GCN/data_gen/sign_gendata.py:10-15`
   *Reliability:* Primary — read from the clone
8. **`[S8]`**
   *Source:* `ref_repo/translation/sam-slr/CVPR21Chal-SLR/SL-GCN/graph/sign_27.py:5-13`
   *Reliability:* Primary — read from the clone
9. **`[S9]`**
   *Source:* `ref_repo/translation/sam-slr/CVPR21Chal-SLR/img/AUTSL_val.jpg` (Table 7) and
   `img/AUTSL_test.jpg` (Table 8)
   *Reliability:* The authors' own figures, corresponding to the CVPR 2021 Workshop paper.
   ⚠ Transcribed by eye from images for this report; not independently reproduced
10. **`[S10]`**
    *Source:* `ref_repo/translation/sam-slr/CVPR21Chal-SLR/LICENSE` (CC0 1.0) and
    `SL-GCN/LICENSE` (CC BY-NC 4.0)
    *Reliability:* Primary. ⚠ Read as an engineer, not a lawyer. The contradiction between them is
    recorded in [`SAR_S2.2`](#22-licence); a commercial path requires qualified review
11. **`[S11]`**
    *Source:* The clone itself at `de6c53a` (2022-05-10). All `file:line` citations resolve against
    this commit
    *Reliability:* Primary

---





# 11. CHANGE LOG
1. **2026-09-04** · *Author:* Claude (Opus 5)
   *Change:* Created from a read of the README, both licence files, the keypoint-selection and
   graph-definition code, the training configuration, the ensemble weights, and the three results
   tables in `img/`. Recorded the CC0-versus-CC-BY-NC contradiction and resolved it conservatively;
   transcribed the AUTSL validation ablation as the project's strongest evidence against a depth
   dependency; translated the ten-point hand selection into MediaPipe indices; and flagged
   `random_mirror` as an augmentation that is unsafe where handedness is grammatical.
