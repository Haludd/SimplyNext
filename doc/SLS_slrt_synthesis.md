**SLRT — SYNTHESIS FOR SIMPLYNEXT**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field             | Value                                                    |
| :---------------- | :------------------------------------------------------- |
| **Code**          | `SLS`                                                    |
| **Status**        | Live                                                     |
| **Last reviewed** | 2026-09-04                                               |
| **Scope**         | Short orientation to `RSL` and the numbers it supplies   |
| **Subject**       | `RSL` — `translation/slrt/SLRT/` at `38a4f7b`            |
| **Full report**   | [`SLR`](../ref_repo/translation/slrt/SLR_slrt_report.md) |

**For the team.** A five-minute orientation to the most decorated body of work in `ref_repo/`: six
peer-reviewed papers on sign language recognition and translation in one tree. It supplies the
project's **numbers**, one **architecture**, and one **prohibition**. The complete analysis is in
[`SLR`](../ref_repo/translation/slrt/SLR_slrt_report.md), beside the clone in
`ref_repo/translation/slrt/`. The sibling translation syntheses are
[`SAS`](SAS_sam_slr_synthesis.md), [`SPS`](SPS_sign_pose_synthesis.md),
[`SSS`](SSS_spoken_to_signed_synthesis.md), [`LTS`](LTS_signlang_literature_synthesis.md) and
[`STS`](STS_sign_translator_synthesis.md).

**For the assistant.** `RSL` is **evidence, not a dependency**. It has **no licence file**, so no
permission to copy exists. Its figures are peer-reviewed and quotable **with their conditions
attached**; its code is not. Where this file and
[`SLR`](../ref_repo/translation/slrt/SLR_slrt_report.md) disagree, `SLR` wins.

</details>

---





# 1. WHAT THIS IS
`FangyunWei/SLRT` is *"the official implementations of the following papers on sign language
processing"* — **five sub-projects, six publications**:

| Directory          | Venue      | What it does                           |
| :----------------- | :--------- | :------------------------------------- |
| `TwoStreamNetwork` | NeurIPS 22 | RGB + keypoint recognition/translation |
| `NLA-SLR`          | CVPR 23    | Isolated recognition                   |
| `CiCo`             | CVPR 23    | Retrieval                              |
| `Online`           | EMNLP 24   | **Online** continuous recognition      |
| `Spoken2Sign`      | ECCV 24    | Spoken → signed, 3D avatar             |

CVPR 2022 and ICCV 2023 papers also live inside `TwoStreamNetwork`. The clone is `38a4f7b`,
2025-02-21 — a documentation edit; the last functional addition was `Online`.

---





# 2. WHY IT CANNOT BE USED
> **Warning — there is no licence file.** A search of the tree returns two hits, both inside
> vendored progress-bar utilities. The root has none, which means **all rights reserved**: the
> authors grant no permission to copy, modify or redistribute.

Two further blockers, either of which would be enough on its own:

1. **`torch==1.9.0+cu102`** — a 2021 CUDA toolchain. The maintainers' own first recommendation is
   a Docker image
2. **Eight GPUs** — 22 of the 33 documented commands specify `--nproc_per_node 8`

And the data is encumbered: CSL-Daily *"needs an agreement submission"*, Phoenix-2014T is
CC BY-NC-SA 3.0 — [`LTS_S5`](LTS_signlang_literature_synthesis.md#5-the-data-situation).

**The rule is the same as [`OPS`](OPS_openpose_synthesis.md)'s: cite it, re-implement ideas from
the description, ship nothing.**

---





# 3. THE NUMBER THAT DECIDES THE VOCABULARY
From `NLA-SLR`, one system evaluated at four vocabulary sizes on each of two datasets — per-instance
top-1 accuracy:

| Vocabulary  | WLASL     | MSASL     |
| :---------- | --------: | --------: |
| 100 signs   | **92.64** | **91.02** |
| 200 signs   | ---       |     89.48 |
| 300 signs   |     86.98 | ---       |
| 500 signs   | ---       |     82.90 |
| 1,000 signs |     75.64 |     73.80 |
| 2,000 signs | **61.26** | ---       |

> **Accuracy falls from 92.6% to 61.3% as the vocabulary grows from 100 to 2,000 signs.** The curve
> is monotonic and steep, and it is measured by one method in one CVPR 2023 paper.

Three consequences:

1. **Closing the vocabulary is where the field's accuracy lives**, not a hackathon compromise.
   [`ARC_S9`](../plan/ARC_architecture.md#9-decisions) decision 4 now rests on a measurement
2. **A demonstration vocabulary in the low hundreds is the honest target.** The project's own
   classifier on its own data will sit below 92.6%, and the deck should say so
3. **Top-5 stays high while top-1 collapses** — 91.77% at WLASL-2000 against 61.26% top-1. The
   right sign is usually *in the candidate set*. This is the argument for the top-k hypothesis
   lattice at stage ⑤ and the *"offer top-k for the signer to pick"* repair at stage ⑨ of
   [`ARC_S6.1`](../plan/ARC_architecture.md#61-pipeline)

---





# 4. THE TRANSLATION CEILING
`TwoStreamNetwork`'s best configuration, on the benchmark the whole field reports:

| Dataset       | ROUGE |    BLEU-4 |
| :------------ | ----: | --------: |
| Phoenix-2014T | 53.48 | **28.95** |
| CSL-Daily     | 55.72 | **25.79** |

Recognition-only, word error rate: **18.8** on Phoenix-2014, **19.3** on Phoenix-2014T, **25.3** on
CSL-Daily.

> **Warning — 28.95 BLEU-4 is not general translation, and three conditions must travel with it.**
> **(a)** Phoenix-2014T is **German Sign Language weather forecasts** — 1,231 glosses, one topic,
> nine signers.
> **(b)** It uses **gloss supervision** — human sign-by-sign annotation of the training set.
> **(c)** The field's own guidance is to *"Focus on datasets beyond RWTH-PHOENIX-Weather-2014T"* and
> to discuss its limited domain openly — [`LTS_S4`](LTS_signlang_literature_synthesis.md#4-the-gloss-question).

**What this changes.** [`ARC_S5.2`](../plan/ARC_architecture.md#52-state-of-the-art) reports
gloss-free translation at BLEU-4 ≈ 10.75 and 13.7–22.1 and concludes open-vocabulary translation is
unsolved. That stands. This adds the other end: with glosses, on a closed domain, the field reaches
~29. **The gap between 10 and 29 is the price of annotation and narrowness** — which is exactly the
trade the project makes by closing its vocabulary.

---





# 5. THE KEYPOINT BUDGET
Fourteen lines in `Online/CSLR/dataset/Dataset.py` define the groups over HRNet's 133
COCO-WholeBody keypoints: `pose` = 11, `face_others` = 48, `mouth` = 20, `hand` = 42, with
mechanical decimation by 2 (`_half`) and 3 (`_1_3`).

Across the **39 configurations** that set `use_keypoints`, exactly **two** combinations appear:

| Combination                    | Files | Keypoints |
| :----------------------------- | ----: | --------: |
| `pose` + `mouth_half` + `hand` |    19 |    **63** |
| the same + `face_others_1_3`   |    20 |    **79** |

Four decisions are visible in those two rows:

1. **The full face is never used.** The maximum is 26 face points out of 68 available
2. **The mouth is always present, at half resolution** — the one face group that never disappears
3. **Both hands are always kept whole**, though the decimation machinery exists
4. **`pose` is 11 points**, head and upper body. Legs were never a question

> This is independent confirmation of
> [`ARC_S3.2`](../plan/ARC_architecture.md#32-the-landmark-budget), with a number attached.
> [`SAS_S4`](SAS_sam_slr_synthesis.md#4-twenty-seven-points) reaches it a third time, lower still.

---





# 6. THE ARCHITECTURE WORTH COPYING
`Online` (EMNLP 2024) is the only sub-project shaped like the project's own pipeline, and it names
the defect in all the others:

> *"typical CTC-based models generally require the entire sign video as input … which suffers from
> high latency and substantial memory usage."*

**Three phases:** build a dictionary of isolated signs by cutting continuous video with an
already-trained model; train an isolated classifier on those clips; slide a window at inference.

The sliding window, from `slide_phoenix-2014t.yaml`:

| Parameter   | Value | Meaning                                 |
| :---------- | :---- | :-------------------------------------- |
| `win_size`  | `16`  | ~640 ms at 25 fps — one sign's duration |
| `stride`    | `1`   | A decision on **every** frame           |
| `beam_size` | `10`  | Beam search over the gloss sequence     |

> **This is a segmentation-free alternative to
> [`ARC_S6.1`](../plan/ARC_architecture.md#61-pipeline) stage ④.** The project's design finds sign
> boundaries geometrically, then classifies. This system never finds a boundary: it classifies
> every window and lets a beam search over per-frame distributions — with a **blank** class
> absorbing the gaps — recover the sequence. It costs one forward pass per frame. That is a trade
> to **measure**, not assume, and it matters more given the segmentation counter-evidence in
> [`LTS_S3`](LTS_signlang_literature_synthesis.md#3-two-findings-that-change-the-plan).

**Phase 1 is the part the project cannot do**: bootstrapping isolated clips out of continuous video
needs a continuous model that already works. Phases 2 and 3 are the half already planned.

**Wait-k translation.** `Online/SLT` adds a *wait-k* gloss-to-text network, with all four
configurations at `wait_k: 2` — text begins two glosses into the utterance. **Not for the MVP**: it
multiplies model calls against the `D6` cap, and partial output later revised is the
*fluent, confident, wrong* failure [`CLD_S5.2`](../CLAUDE.md#52-honesty-about-the-product) forbids.
It is the named roadmap answer to sub-utterance latency.

---





# 7. `Spoken2Sign`, AND WHY `RSS` WINS
`Spoken2Sign` (ECCV 2024) and `RSS` share one architecture — text → gloss → dictionary lookup →
stitch → render — and differ in everything practical:

| Aspect     | `Spoken2Sign`          | `RSS` ([`SSS`](SSS_spoken_to_signed_synthesis.md)) |
| :--------- | :--------------------- | :------------------------------------------------- |
| Dictionary | SMPL-X 3D meshes       | `.pose` keypoint sequences                         |
| Stitching  | Learned sign connector | Butterworth filter + trimming                      |
| Rendering  | Blender + SMPL-X       | Pose skeleton                                      |
| Licence    | **None**               | MIT                                                |
| Laptop     | No                     | **Yes**                                            |

> **Decision:** the reverse direction is built on `RSS`. `Spoken2Sign` contributes one roadmap
> idea — a **learned connector** that generates the transition between two dictionary signs rather
> than filtering the seam — and one evaluation trick: **back-translation**, running produced signs
> back through a recogniser to see whether the glosses return. That second one is cheap for this
> project, which will already have the forward model. Recorded for `EVL`.

---





# 8. THE NINE LESSONS
| #  | Lesson                                                                                     |
| :- | :----------------------------------------------------------------------------------------- |
| L1 | **Accuracy is a function of vocabulary size**, and the curve is steep — 92.6% → 61.3%      |
| L2 | **Top-5 survives where top-1 collapses.** Design for a candidate set, not an answer        |
| L3 | **No published system uses the full face.** 10–26 face points; the mouth always            |
| L4 | **Never decimate the hands.** Every configuration keeps all 42                             |
| L5 | **Online recognition is a sliding window over an isolated classifier**, not a new model    |
| L6 | **A blank class replaces boundary detection** at stride 1                                  |
| L7 | **Streaming translation is a wait-k policy** — a named technique, not an invention         |
| L8 | **Progressive pretraining beats data scarcity**: general → sign → corpus                   |
| L9 | **Check for a licence file before reading the benchmark table.** This one has none         |

L9 is the second time this check has changed a verdict —
[`OPS_S2.1`](OPS_openpose_synthesis.md#21-the-licence) was the first, and
[`SAS_S2`](SAS_sam_slr_synthesis.md#2-the-licence-contradiction) is the third.

---





# 9. WHAT IT DOES NOT DO
1. **It does not isolate a signer.** Every dataset is pre-cropped to one signer
2. **It does not detect whether anyone is signing.** Input is assumed to be signing throughout
3. **It does not run on CPU**, and nothing in it is designed to
4. **It does not handle conversation** — no turn-taking, no second speaker, no repair
5. **It does not express uncertainty as a behaviour.** Beam search emits its best hypothesis;
   there is no refusal path, so [`ARC_S9`](../plan/ARC_architecture.md#9-decisions) decision 8 has
   no counterpart here
6. **It covers no Southeast Asian sign language** — German, Chinese, American, Turkish only
7. **It never extracts its own keypoints.** HRNet output is pre-computed into `.pkl` files; there
   is no capture loop anywhere in the repository

---





# 10. RUNNING IT
**The project does not run this repository, and should not try.** A 2021 CUDA toolchain, eight-GPU
training recipes, datasets behind agreements, checkpoints on a personal OneDrive, and no licence
under which a successful reproduction could ship.

What the project does instead: reads [`SLS_S5`](#5-the-keypoint-budget) and
[`SLS_S6`](#6-the-architecture-worth-copying), re-implements the two ideas it needs from the
description, and cites the papers for the numbers.

---





# 11. WHERE TO GO NEXT
| Question                      | Document                                                 |
| :---------------------------- | :------------------------------------------------------- |
| Full breakdown of SLRT        | [`SLR`](../ref_repo/translation/slrt/SLR_slrt_report.md) |
| The smallest keypoint budget  | [`SAS`](SAS_sam_slr_synthesis.md)                        |
| The reverse direction, usable | [`SSS`](SSS_spoken_to_signed_synthesis.md)               |
| What the field knows          | [`LTS`](LTS_signlang_literature_synthesis.md)            |
| How this changes the plan     | [`ARC_S5`](../plan/ARC_architecture.md)                  |
| How the submission is scored  | [`JCR`](../plan/JCR_judging_criteria.md)                 |
| Where every document lives    | [`RIX`](../ref_index.md)                                 |

---





# 12. CHANGE LOG
1. **2026-09-04** · *Author:* Claude (Opus 5)
   *Change:* Created alongside [`SLR`](../ref_repo/translation/slrt/SLR_slrt_report.md), from a
   read of the six sub-project READMEs, the requirements files, the keypoint-selection code, all 39
   `use_keypoints` configurations, and the sliding-window and wait-k settings.
