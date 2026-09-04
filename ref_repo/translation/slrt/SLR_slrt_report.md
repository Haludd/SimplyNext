**SLRT — FULL REPOSITORY REPORT**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field                   | Value                                                 |
| :---------------------- | :---------------------------------------------------- |
| **Code**                | `SLR`                                                 |
| **Status**              | Live                                                  |
| **Last reviewed**       | 2026-09-04                                            |
| **Source of truth for** | Analysis of the SLRT reference clone                  |
| **Parent**              | [`RIX_S2.1`](../../../ref_index.md#21-live-documents) |
| **Short version**       | [`SLS`](../../../doc/SLS_slrt_synthesis.md)           |
| **Subject**             | `RSL` — `translation/slrt/SLRT/` at `38a4f7b`         |

**For the team.** `FangyunWei/SLRT` is the reference implementation of six published papers on sign
language recognition and translation, spanning **NeurIPS 2022, CVPR 2022, CVPR 2023 ×2, ICCV 2023
and EMNLP 2024**. It is the most decorated body of work in `ref_repo/` and the single best source
of *published numbers* for the sign-to-spoken direction. Three sections carry the weight:
[`SLR_S5`](#5-the-numbers-that-decide-the-architecture) is the performance evidence,
[`SLR_S6`](#6-the-online-framework--the-architecture-worth-copying) is the one architecture in this
repository that is shaped like the project's own pipeline, and [`SLR_S2.2`](#22-licence) is the
reason none of its code can be shipped.

**For the assistant.** `RSL` is **evidence and architecture, not a dependency**. It has **no
licence file** ([`SLR_S2.2`](#22-licence)), pins `torch==1.9.0+cu102`, and every training recipe
assumes eight GPUs. Do not describe it as something the project runs, trains or reproduces. Its
figures are peer-reviewed and may be quoted; its code may not be copied. Nothing inside
`ref_repo/translation/slrt/SLRT/` may be edited; it is an unmodified clone, excluded from version
control.

</details>

---





# 1. EXECUTIVE SUMMARY
## 1.1. What This Repository Is
`ref_repo/translation/slrt/SLRT/` is **FangyunWei/SLRT**, described by its own README as containing
*"the official implementations of the following papers on sign language processing"* `[S1]`. It is
not one system but **five sub-projects in one tree**, each the artefact of a separate publication:

| Directory          | Venue      | Task                                        |
| :----------------- | :--------- | :------------------------------------------ |
| `TwoStreamNetwork` | NeurIPS 22 | Recognition and translation, RGB + keypoint |
| `NLA-SLR`          | CVPR 23    | Isolated recognition, language-assisted     |
| `CiCo`             | CVPR 23    | Sign language retrieval                     |
| `Online`           | EMNLP 24   | **Online** continuous recognition           |
| `Spoken2Sign`      | ECCV 24    | Spoken → signed, with a 3D avatar           |

Two further papers — *A Simple Multi-Modality Transfer Learning Baseline for SLT* (CVPR 2022) and
*Improving Continuous Sign Language Recognition with Cross-Lingual Signs* (ICCV 2023) — are
implemented inside `TwoStreamNetwork` rather than in directories of their own `[S1]`.

The publication record is the strongest in `ref_repo/`: **six peer-reviewed venues, all top-tier**,
against `ROP`'s two. Where the project needs a defensible number about sign language translation,
this is where it comes from — see [`CLD_S5.1`](../../../CLAUDE.md#51-evidence).




## 1.2. Why It Matters to SimplyNext
It matters as **the measured state of the art**, as **one directly transferable architecture**, and
as **a warning about what a research codebase costs**.

1. **As the honest ceiling** · *Use:* [`SLR_S5`](#5-the-numbers-that-decide-the-architecture)
   supplies gloss-supervised translation figures (~29 BLEU-4) and isolated-recognition figures that
   fall from **92.6% to 61.3%** as the vocabulary grows from 100 to 2,000 signs. That curve is the
   evidence for the closed-vocabulary decision in
   [`ARC_S9`](../../../plan/ARC_architecture.md#9-decisions), decision 4
2. **As an architecture** · *Use:* The `Online` sub-project decomposes continuous recognition into
   *dictionary → isolated classifier → sliding window*, which is the pipeline
   [`ARC_S5.3`](../../../plan/ARC_architecture.md#53-recommended-approach) proposes, validated at
   EMNLP 2024 — [`SLR_S6`](#6-the-online-framework--the-architecture-worth-copying)
3. **As a landmark budget** · *Use:* Every configuration in the repository selects **63 or 79 of
   133 available keypoints** and never the full face. This is primary-source confirmation of
   [`ARC_S3.2`](../../../plan/ARC_architecture.md#32-the-landmark-budget) —
   [`SLR_S4`](#4-the-keypoint-budget-as-a-sota-system-actually-sets-it)
4. **As a cost warning** · *Use:* `torch==1.9.0+cu102`, eight-GPU training commands, and datasets
   behind signed agreements. [`SLR_S8`](#8-running-it) states plainly what reproduction would cost,
   which is why the answer is that the project does not attempt it

Against the four MVP steps in [`SCR`](../../../plan/scribbles.md):

1. **1. Isolate the subject** — not addressed. Every dataset is a single signer, pre-cropped
2. **2. Track many points** — solved upstream by HRNet on COCO-WholeBody, then **reduced** to a
   curated subset. The reduction, not the tracking, is the lesson
3. **3. Points → skeleton** — the keypoint stream is exactly a pose representation, and
   [`SLR_S5.3`](#53-what-the-keypoint-stream-contributes) measures what it contributes
4. **4. Skeleton → conversational text** — **this is the repository's subject**, and the only place
   in `ref_repo/` where it is attempted at all




## 1.3. Summary
The recurring method is *two streams and a language model*. An S3D video encoder and an S3D
keypoint encoder run in parallel with bidirectional lateral connections between them; a CTC head
reads glosses off the shared encoding; an mBART decoder turns glosses into spoken-language text.
Pretraining is progressive — general action recognition first, then sign, then the target corpus —
because every sign language dataset is too small to train from scratch. The `Online` sub-project
breaks the offline assumption by segmenting continuous video into isolated sign clips with an
already-trained model, training an isolated classifier on those clips, and then sliding a
**16-frame window at stride 1** over live input `[S2]`. Translation follows with a **wait-2**
policy: emit text after two glosses rather than after the sentence `[S3]`.

---





# 2. PROVENANCE, LICENCE AND REQUIREMENTS
## 2.1. Provenance
1. **Publisher**
   Fangyun Wei (Microsoft Research Asia) and collaborators at HKUST. Remote:
   `https://github.com/FangyunWei/SLRT.git`
2. **Clone state**
   `38a4f7b`, 2025-02-21, *"Update SingleStream-SLT.md"* — a documentation edit
3. **Maintenance status**
   ⚠ **Effectively archived as a research artefact.** The most recent functional addition is the
   `Online` sub-project (EMNLP 2024); commits since are documentation. This is normal for a paper
   repository and is not a defect, but it means no dependency updates will arrive
4. **Scale**
   796 Python files, 58 YAML configurations, 72 MB on disk, five sub-projects
5. **Language**
   Python, PyTorch




## 2.2. Licence
> **Warning — there is no licence file.** `find . -iname 'LICENSE*'` returns two hits, both inside
> vendored third-party progress-bar utilities (`CiCo/I3D_trainer/utils/progress/LICENSE` and
> `CiCo/I3D_feature_extractor/utils/progress/LICENSE`). **The repository root carries none.**

The consequence is not ambiguity in the project's favour. Under the copyright law of every
jurisdiction that matters, code published without a licence is **"all rights reserved"**: the
authors retain copyright and grant no permission to copy, modify or redistribute. A GitHub
repository with no licence is readable and forkable within GitHub's own terms of service, and
nothing more.

Set against `RMP` (Apache 2.0), `RSP` (MIT) and `RSS` (MIT), this places `RSL` in the same
practical category as `ROP` — **cite it, do not ship it** — but for a different reason. `ROP` has a
licence that forbids the use ([`OPR_S2.2`](../../tracking/openpose/OPR_openpose_report.md#22-licence));
`RSL` has no licence that permits it.

> **Note — the absence of a licence does not restrict reading, measuring or citing.** The papers
> are published at peer-reviewed venues and their figures are public record. What is excluded is
> *copying source code into `src/`*. Every idea recorded in this report is described so that it can
> be re-implemented from the description, which is the only lawful route.




## 2.3. Requirements
`Online/requirements.txt` and `NLA-SLR/requirements.txt` are identical in the parts that matter
`[S4]`:

1. **PyTorch** — `torch==1.9.0+cu102` and `torchvision==0.10.0`. ⚠ PyTorch 1.9 and CUDA 10.2 are
   a **2021** toolchain. Neither is installable against a current CUDA driver without work
2. **Video decoding** — `Lintel==1.0`, a C-extension decoder that must be compiled
3. **Cloud** — `azureml==0.2.7`, `azureml_core==1.44.0`, `wandb==0.12.17`; `Online` adds `gensim`
   and `ctcdecode`, the last of which is another compiled extension
4. **The maintainers' own recommendation is Docker** — `docker pull rzuo/pose:sing_ISLR`. The
   README's `pip install` path is offered second, which is a fair signal about how well it works
5. **Spoken2Sign additionally needs** `smplx`, `pyrender`, `trimesh`, **Blender**, and the SMPL-X
   body model, which is distributed under its own research-only registration

**Hardware.** Twenty-two of the thirty-three documented commands specify
`--nproc_per_node 8` — eight GPUs. Inference commands use `--nproc_per_node 1`, but on a GPU.




## 2.4. Data, and Why It Is Not Available
Every number in [`SLR_S5`](#5-the-numbers-that-decide-the-architecture) is measured on a dataset
the project cannot simply download:

1. **Phoenix-2014 / Phoenix-2014T** — German Sign Language weather forecasts, RWTH Aachen.
   Licensed **CC BY-NC-SA 3.0** `[S5]`
2. **CSL-Daily** — Chinese Sign Language. *"whose downloading needs an agreement submission"*, in
   the repository's own words `[S6]`
3. **WLASL** — 2,000 ASL signs, 100 signers. C-UDA 1.0 `[S5]`
4. **MSASL** — 1,000 ASL signs, Microsoft. Requires accepting Microsoft's terms `[S5]`
5. **Keypoints and checkpoints** — hosted on a personal HKUST OneDrive, not a permanent archive.
   ⚠ Link rot is a real risk for a 2022–2024 research artefact

> **Warning — the licence problem is upstream of the code problem.** Even if `RSL` carried a
> permissive licence, the benchmarks it is measured on are predominantly non-commercial. This is a
> field-wide pattern, catalogued in
> [`LTR_S6`](../signlang-literature/LTR_signlang_literature_report.md#6-datasets), and it is one of
> the strongest arguments for the project recording its own small vocabulary.

---





# 3. REPOSITORY MAP
```text
ref_repo/translation/slrt/
├── SLR_slrt_report.md                    — this document (tracked in git)
└── SLRT/                                 — the clone (git-ignored)
    ├── TwoStreamNetwork/     41 py, 23 yaml   NeurIPS 22 + CVPR 22. The backbone
    ├── NLA-SLR/              24 py, 15 yaml   CVPR 23. Isolated recognition ← read this
    ├── Online/              542 py, 16 yaml   EMNLP 24. Online CSLR + SLT ← and this
    ├── CiCo/                101 py            CVPR 23. Retrieval
    ├── Spoken2Sign/          88 py,  4 yaml   ECCV 24. The reverse direction
    └── README.md                             Paper index and citations
```

**Worth reading, in order:**

1. `Online/README.md` and `Online/CSLR/README.md` — the online framework in three paragraphs
2. `Online/CSLR/dataset/Dataset.py:9-17` — the keypoint budget, in fourteen lines
3. `Online/CSLR/configs/slide_phoenix-2014t.yaml` — every sliding-window parameter in one file
4. `Online/SLT/README.md` — the wait-k policy for streaming translation
5. `TwoStreamNetwork/README.md` — the results tables, which are the reason to open the repository
6. `Spoken2Sign/README.md` — the reverse direction, to compare against `RSS`

**Not worth reading:** `CiCo/` (retrieval is a different task), every `modelling/` directory (they
are S3D and mBART implementations that cannot be shipped anyway), and all 542 files under
`Online/` that are not named above.

---





# 4. THE KEYPOINT BUDGET, AS A SOTA SYSTEM ACTUALLY SETS IT
This is the most directly transferable finding in the repository, and it is fourteen lines long.

`Online/CSLR/dataset/Dataset.py:9-17` `[S7]`:

```python
Hrnet_Part2index = {
    'pose': list(range(11)),
    'hand': list(range(91, 133)),
    'mouth': list(range(71,91)),
    'face_others': list(range(23, 71))
}
for k_ in ['mouth','face_others', 'hand']:
    Hrnet_Part2index[k_+'_half'] = Hrnet_Part2index[k_][::2]
    Hrnet_Part2index[k_+'_1_3'] = Hrnet_Part2index[k_][::3]
```

The upstream pose estimator is HRNet trained on **COCO-WholeBody, which emits 133 keypoints**. The
named groups partition it:

| Group         | Indices | Count | Content                        |
| :------------ | :------ | ----: | :----------------------------- |
| `pose`        | 0–10    |    11 | Head and upper body only       |
| `face_others` | 23–70   |    48 | Brows, eyes, nose, jaw contour |
| `mouth`       | 71–90   |    20 | Lips                           |
| `hand`        | 91–132  |    42 | 21 per hand, both hands        |

The `_half` and `_1_3` suffixes are decimation by 2 and by 3, generated mechanically.




## 4.1. What Every Configuration Actually Selects
Across the **39 configuration files** in the repository that set `use_keypoints`, exactly **two**
combinations appear:

| Combination                      | Files | Total keypoints |
| :------------------------------- | ----: | --------------: |
| `pose` + `mouth_half` + `hand`   |    19 |          **63** |
| the same, plus `face_others_1_3` |    20 |          **79** |

Read carefully, because four separate decisions are visible in those two rows:

1. **The full face is never used.** The maximum face budget is `mouth_half` (10) plus
   `face_others_1_3` (16) = **26 face points out of 68 available**. Twenty of the thirty-nine
   configurations use ten
2. **The mouth is always present, and always at half resolution.** It is the one face group that
   never disappears — consistent with the linguistic claim in
   [`ARC_S3.2`](../../../plan/ARC_architecture.md#32-the-landmark-budget) that the mouth carries
   lexical and morphological information
3. **Both hands are always kept whole.** `hand` is never decimated, though the machinery to do so
   exists. The hands are the one channel the authors would not compress
4. **`pose` is 11 points, not 17.** COCO's first eleven indices are head and upper body; hips,
   knees and ankles are simply not in the range. The legs were never a question

> **Decision consequence.** [`ARC_S3.2`](../../../plan/ARC_architecture.md#32-the-landmark-budget)
> proposes hands + handedness + upper-body pose + a curated face subset and explicitly rejects the
> full 468-point face mesh. This repository reaches the same conclusion independently, from six
> publications, and puts a number on it: **63 to 79 keypoints**. `RSA` reaches it a third time with
> a smaller number still — [`SAR_S4`](../sam-slr/SAR_sam_slr_report.md#4-the-27-keypoint-budget).

---





# 5. THE NUMBERS THAT DECIDE THE ARCHITECTURE
Every figure below is copied from a results table in the repository's own documentation. They are
self-reported by the authors, but each corresponds to a peer-reviewed publication, which is a
materially stronger provenance than the preprints currently cited in
[`ARC_S5.2`](../../../plan/ARC_architecture.md#52-state-of-the-art).




## 5.1. Translation Quality, With Gloss Supervision
From `TwoStreamNetwork/README.md` `[S8]`. `R` is ROUGE; `B1`–`B4` are BLEU-1 to BLEU-4.

**TwoStream-SLT** — the best configuration in the repository:

| Dataset       |     R |    B1 |    B2 |    B3 |        B4 |
| :------------ | ----: | ----: | ----: | ----: | --------: |
| Phoenix-2014T | 53.48 | 54.90 | 42.43 | 34.46 | **28.95** |
| CSL-Daily     | 55.72 | 55.44 | 42.59 | 32.87 | **25.79** |

**SingleStream-SLT** — the CVPR 2022 baseline, without the keypoint stream:

| Dataset       |     R |    B1 |    B2 |    B3 |        B4 |
| :------------ | ----: | ----: | ----: | ----: | --------: |
| Phoenix-2014T | 53.08 | 54.48 | 41.93 | 33.97 | **28.57** |
| CSL-Daily     | 53.35 | 53.53 | 40.68 | 31.04 | **24.09** |

> **Warning — 28.95 BLEU-4 is not a general translation result, and quoting it as one would be
> dishonest.** Three qualifications, all of which must travel with the number:
> **(a)** Phoenix-2014T is **German Sign Language weather forecasts** — a vocabulary of 1,231
> glosses over one topic, from nine signers.
> **(b)** The result uses **gloss supervision**: human sign-by-sign annotation of the training set.
> Gloss-free systems on the same benchmark score far lower.
> **(c)** The sign-language-processing literature specifically recommends *"Focus on datasets
> beyond RWTH-PHOENIX-Weather-2014T. Openly discuss the limited size and linguistic domain of this
> dataset"* `[S9]` — see
> [`LTR_S5.2`](../signlang-literature/LTR_signlang_literature_report.md#52-the-gloss-question).

**What this changes for the project.**
[`ARC_S5.2`](../../../plan/ARC_architecture.md#52-state-of-the-art) currently reports gloss-free
translation at BLEU-4 ≈ 10.75 and 13.7–22.1, and concludes that open-vocabulary translation is
unsolved. That conclusion stands. What this repository adds is the *other* end of the range: with
gloss supervision, on a closed domain, the same field reaches ~29. **The gap between 10 and 29 is
almost entirely the cost of annotation and the narrowness of the domain** — which is precisely the
trade the project makes when it closes the vocabulary.




## 5.2. Recognition Accuracy Against Vocabulary Size
From `NLA-SLR/README.md` `[S10]`. `P-I` is per-instance, `P-C` per-class.

| Dataset    | P-I Top1  | P-I Top5 | P-C Top1 | P-C Top5 |
| :--------- | --------: | -------: | -------: | -------: |
| WLASL-100  | **92.64** |    96.90 |    93.08 |    97.17 |
| WLASL-300  | **86.98** |    97.60 |    87.33 |    97.81 |
| WLASL-1000 | **75.64** |    94.62 |    75.72 |    94.65 |
| WLASL-2000 | **61.26** |    91.77 |    58.31 |    90.91 |
| MSASL-100  | **91.02** |    97.89 |    91.24 |    98.19 |
| MSASL-200  | **89.48** |    96.69 |    89.86 |    96.93 |
| MSASL-500  | **82.90** |    93.46 |    83.06 |    93.54 |
| MSASL-1000 | **73.80** |    89.65 |    70.95 |    89.07 |

> **This is the single most decision-relevant table in `ref_repo/`.** One system, one method, one
> paper, evaluated at four vocabulary sizes on each of two datasets. Top-1 accuracy falls from
> **92.6% at 100 signs to 61.3% at 2,000** on WLASL, and from **91.0% to 73.8%** on MSASL. The
> curve is monotonic and steep.

Three consequences follow directly:

1. **Closing the vocabulary is not a hackathon compromise; it is where the field's accuracy lives.**
   [`ARC_S9`](../../../plan/ARC_architecture.md#9-decisions) decision 4 is now supported by a
   CVPR 2023 measurement rather than by schedule pressure alone
2. **A demonstration vocabulary in the low hundreds is the honest target.** At 100 signs a SOTA
   system is at 92.6%; the project's smaller model on its own recorded data will be below that, and
   the deck should say so
3. **Top-5 stays high while top-1 collapses** — 91.77% at WLASL-2000 against 61.26% top-1. The
   correct answer is usually *in the candidate set* even when it is not first. This is the direct
   argument for the top-k hypothesis lattice at stage ⑤ and for the *"offer top-k for the signer to
   pick"* repair action at stage ⑨ of
   [`ARC_S6.1`](../../../plan/ARC_architecture.md#61-pipeline). The repository supplies the number
   that makes that design pay




## 5.3. What the Keypoint Stream Contributes
Comparing [`SLR_S5.1`](#51-translation-quality-with-gloss-supervision)'s two tables isolates the
keypoint stream, because SingleStream and TwoStream differ in little else:

| Dataset       | SingleStream B4 | TwoStream B4 |  Gain |
| :------------ | --------------: | -----------: | ----: |
| Phoenix-2014T |           28.57 |        28.95 | +0.38 |
| CSL-Daily     |           24.09 |        25.79 | +1.70 |

⚠ This is a comparison across two papers a year apart, not a controlled ablation, and the two
systems differ in more than the second stream. Treat the gains as indicative.

**Twostream-SLR**, the recognition-only configuration, reports word error rates of **18.8 (Phoenix-2014)**,
**19.3 (Phoenix-2014T)** and **25.3 (CSL-Daily)** `[S8]`. A WER near 19 on a 1,231-gloss closed
weather vocabulary is a useful calibration point for how hard continuous recognition remains even
under ideal conditions.

---





# 6. THE `Online` FRAMEWORK — THE ARCHITECTURE WORTH COPYING
`Online` is the only sub-project whose *shape* matches the project's own pipeline, and it is the
most recent (EMNLP 2024).




## 6.1. The Problem It Names
From `Online/README.md` `[S2]`:

> *"During inference, typical CTC-based models generally require the entire sign video as input to
> make predictions, a process known as offline recognition, which suffers from high latency and
> substantial memory usage. In this work, we take the first step towards online CSLR."*

That sentence describes the defect in every other system in this repository, and it is
disqualifying for a conversational product. A system that must see the whole utterance before
producing anything cannot participate in a conversation.




## 6.2. The Three Phases
The README states the method in one sentence `[S2]`: *"Our approach consists of three phases: 1)
developing a sign dictionary; 2) training an isolated sign language recognition model on the
dictionary; and 3) employing a sliding window approach on the input sign sequence, feeding each
sign clip to the optimized model for online recognition."*

1. **Build a dictionary of isolated signs** · *How:* `gen_segment.py` runs an already-trained
   continuous model (TwoStream-SLR) over continuous video to cut it into isolated clips. The
   boundaries are **pseudo-labels**, and the repository says so — *"the segmented signs are pseudo
   ground-truths and their boundaries may not be accurate"* — so `sign_augment.py` perturbs them
   `[S11]`
2. **Train an isolated classifier on that dictionary** · *How:* Ordinary isolated recognition, the
   `NLA-SLR` task, on the clips from phase 1
3. **Slide a window at inference** · *How:* `prediction_slide.py` with
   `configs/slide_phoenix-2014t.yaml`

> **Note — phase 1 is the interesting one, and the project cannot do it.** Bootstrapping isolated
> clips out of continuous video requires a continuous model that already works. The project has no
> such model and no continuously-annotated corpus. What transfers is phases 2 and 3, which is
> exactly the half the project was already planning.




## 6.3. The Sliding-Window Parameters
From `Online/CSLR/configs/slide_phoenix-2014t.yaml` `[S12]`:

| Parameter       | Value                        | Meaning                            |
| :-------------- | :--------------------------- | :--------------------------------- |
| `win_size`      | `16`                         | 16 frames per classified clip      |
| `stride`        | `1`                          | Classify on **every** frame        |
| `split_size`    | `36`                         | Windows batched per forward pass   |
| `input_streams` | `keypoint`, `rgb`            | Both streams at inference          |
| `use_keypoints` | `pose`, `mouth_half`, `hand` | 63 keypoints — see `SLR_S4`        |
| `beam_size`     | `10`                         | Beam width over the gloss sequence |

At a typical 25 fps, a 16-frame window is **640 ms** — a plausible duration for one sign. Stride 1
means a decision every frame, with heavy overlap, and a vocabulary-plus-blank output per position.

> **Note — this is a segmentation-free design, and it is a genuine alternative to
> [`ARC_S6.1`](../../../plan/ARC_architecture.md#61-pipeline) stage ④.** The project's stage ④
> finds sign boundaries geometrically and then classifies each segment. This system never finds a
> boundary: it classifies every window and lets a beam search over the resulting per-frame
> distribution recover the sequence, with a **blank** class absorbing the gaps. Stride 1 with a
> 16-frame window costs one forward pass per frame, which is affordable only because the classifier
> is small. That is a trade the project should measure rather than assume — recorded as a new open
> question in [`ARC_S9.1`](../../../plan/ARC_architecture.md#91-open-questions-for-the-team).




## 6.4. Wait-k Translation — Streaming the Text Too
`Online/SLT` adds *"online sign language translation with a **wait-k** gloss2text network"* `[S3]`.
All four provided configurations set `wait_k: 2` `[S13]`.

A wait-k policy is standard in simultaneous machine translation: the decoder begins emitting target
tokens after **k** source tokens have arrived, then produces one target token per source token,
instead of waiting for the complete source sentence. At `k = 2`, spoken-language text begins two
glosses into the utterance.

> **Note — this is directly relevant to
> [`ARC_S6.4`](../../../plan/ARC_architecture.md#64-latency-budget).** The current budget invokes
> the agent **once per utterance** and accepts a 0.5–2 s round trip at the utterance boundary. A
> wait-k formulation would instead begin producing text mid-utterance. The project should **not**
> adopt it for the MVP: it multiplies model calls, which attacks the `D6` budget cap
> ([`ARC_S8`](../../../plan/ARC_architecture.md#8-cost-model-against-the-aws-cap)), and partial
> output that is later revised is exactly the *fluent, confident, wrong* failure
> [`CLD_S5.2`](../../../CLAUDE.md#52-honesty-about-the-product) forbids. It belongs on the roadmap
> slide as the named path to sub-utterance latency.

---





# 7. `Spoken2Sign` — THE REVERSE DIRECTION, AND WHY `RSS` WINS
`Spoken2Sign` (ECCV 2024) is the second implementation of spoken → signed in `ref_repo/`, and
comparing it against `RSS` settles which one the project builds on.




## 7.1. The Method
From `Spoken2Sign/README.md` `[S14]`, a three-step baseline: *"1) creating a gloss-video dictionary
using existing Sign2Spoken benchmarks; 2) estimating a 3D sign for each sign video in the
dictionary; 3) training a Spoken2Sign model, which is composed of a Text2Gloss translator, a sign
connector, and a rendering module"*, displayed *"through a sign avatar"*.

The **architectural skeleton is identical to `RSS`**: translate text to glosses, look each gloss up
in a dictionary, stitch the retrieved pieces together, render. The differences are in what is
stored and how it is displayed.

| Aspect             | `Spoken2Sign` (this repo)            | `RSS` spoken-to-signed          |
| :----------------- | :----------------------------------- | :------------------------------ |
| Dictionary entries | SMPL-X 3D body meshes                | `.pose` keypoint sequences      |
| Stitching          | Learned **sign connector**           | Butterworth filter + trimming   |
| Rendering          | Blender + SMPL-X add-on              | Pose skeleton, optional pix2pix |
| Licence            | **None** — [`SLR_S2.2`](#22-licence) | MIT                             |
| Install            | Docker, GPU, SMPL-X models           | `pip install spoken-to-signed`  |
| Runs on a laptop   | No                                   | **Yes**                         |

> **Decision:** the reverse direction is built on `RSS`, not on this. `Spoken2Sign` contributes one
> idea — the **learned sign connector**, a model trained to generate the transition between two
> dictionary signs rather than filtering the seam — which is the principled version of what
> [`SSR_S5.3`](../spoken-to-signed/SSR_spoken_to_signed_report.md#53-smoothing-the-seams) does with
> a low-pass filter. Roadmap, not MVP.




## 7.2. The Evaluation Trick Worth Keeping
`Spoken2Sign` evaluates production by **back-translation** `[S14]`: project the generated SMPL-X
motion down to 2D keypoints (`smplx2kps.py`), then train a keypoint-only sign-to-text model on the
synthetic keypoints and measure how well it recovers the original sentence.

This solves a real problem — there is no accepted automatic metric for whether a produced sign
sequence is *correct*, as
[`LTR_S5.4`](../signlang-literature/LTR_signlang_literature_report.md#54-evaluation-metrics)
records. It is also cheap in principle for this project, which will already have a
sign-to-text classifier: **feed the reverse direction's output back through the forward direction
and see whether the glosses come back.** Recorded for `EVL`.

---





# 8. RUNNING IT
The honest answer is that the project does not run this repository, and should not try.

1. **The dependency stack is four years old** — `torch==1.9.0+cu102`. Installing it against a
   current driver is a day's work with an uncertain outcome, and the maintainers' own first
   recommendation is a Docker image
2. **Training needs eight GPUs** — twenty-two of the documented commands say so
3. **The data needs agreements** — CSL-Daily requires *"an agreement submission"* `[S6]`; the rest
   are non-commercial
4. **The checkpoints are on personal cloud storage** — OneDrive links from 2022–2024
5. **There is no licence** — [`SLR_S2.2`](#22-licence). Even a successful reproduction could not
   ship

> **Placeholder — whether any `Online` checkpoint is still downloadable.**
> **Missing:** a check that the OneDrive links in `Online/CSLR/README.md` still resolve, and under
> what terms. This report did not attempt any network access.
> **Update trigger:** a decision to attempt a baseline comparison against a published model.
> **Owner:** team.

**What the project does instead:** reads [`SLR_S4`](#4-the-keypoint-budget-as-a-sota-system-actually-sets-it)
and [`SLR_S6`](#6-the-online-framework--the-architecture-worth-copying), re-implements the two ideas
it needs from the description, and cites the papers for the numbers.

---





# 9. WHAT THE REPOSITORY DOES NOT DO
1. **It does not isolate a signer.** Every dataset is pre-cropped to one signer against a
   controlled background. [`ARC_S2`](../../../plan/ARC_architecture.md#2-step-1--isolating-the-subject)
   gets no help here
2. **It does not detect whether anyone is signing.** Input is assumed to be signing throughout
3. **It does not run on CPU.** Nothing in the repository is designed to
4. **It does not handle conversation.** No turn-taking, no second speaker, no repair
5. **It does not express uncertainty as a product behaviour.** A beam search emits its best
   hypothesis. There is no refusal path — the invariant in
   [`ARC_S9`](../../../plan/ARC_architecture.md#9-decisions) decision 8 has no counterpart here
6. **It does not cover any Southeast Asian sign language.** German, Chinese, American and Turkish
   only
7. **It does not extract its own keypoints in the recognition path.** HRNet output is pre-computed
   offline into `.pkl` files; there is no live capture loop anywhere in the repository

---





# 10. RELEVANCE TO SIMPLYNEXT
## 10.1. Lessons to Carry Across
| #  | Lesson                                                                                     |
| :- | :----------------------------------------------------------------------------------------- |
| L1 | **Accuracy is a function of vocabulary size**, and the curve is steep — 92.6% → 61.3%      |
| L2 | **Top-5 survives where top-1 collapses.** Design for a candidate set, not an answer        |
| L3 | **No published system uses the full face.** 10–26 face points, mouth always included       |
| L4 | **Never decimate the hands.** Every configuration keeps all 42 hand points                 |
| L5 | **Online recognition is a sliding window over an isolated classifier**, not a new model    |
| L6 | **A blank class replaces boundary detection** where a window slides at stride 1            |
| L7 | **Streaming translation is a wait-k policy** — a known, named technique, not an invention  |
| L8 | **Progressive pretraining is how the field beats data scarcity**: general → sign → corpus  |
| L9 | **Check for a licence file before reading the benchmark table.** This one has none         |

L9 is the second time this check has changed a decision — [`OPR_S2.2`](../../tracking/openpose/OPR_openpose_report.md#22-licence)
was the first. It is now a standing step, recorded in
[`CLD_S5.4`](../../../CLAUDE.md#54-working-with-the-reference-repositories).




## 10.2. What the Project Takes
1. **The vocabulary-size curve** · *Take:* 92.64% at 100 signs → 61.26% at 2,000 ·
   *Where:* [`ARC_S5.2`](../../../plan/ARC_architecture.md#52-state-of-the-art) and the evaluation
   slide
2. **The gloss-supervised ceiling** · *Take:* 28.95 BLEU-4 on Phoenix-2014T, with all three
   qualifications attached · *Where:* `ARC` sources; the positioning slide
3. **The keypoint budget** · *Take:* 63–79 of 133; mouth always, full face never ·
   *Where:* [`ARC_S3.2`](../../../plan/ARC_architecture.md#32-the-landmark-budget)
4. **The top-k design argument** · *Take:* Top-5 ≫ top-1 justifies the hypothesis lattice and the
   *"offer top-k"* repair · *Where:* [`ARC_S6.1`](../../../plan/ARC_architecture.md#61-pipeline)
   stages ⑤ and ⑨
5. **The sliding-window alternative to segmentation** · *Take:* 16-frame window, stride 1, blank
   class · *Where:* A measured alternative to stage ④, recorded as an open question
6. **Back-translation as a production metric** · *Take:* Evaluate the reverse direction by running
   its output through the forward direction · *Where:* `EVL`
7. **The wait-k name** · *Take:* The roadmap answer for sub-utterance latency · *Where:* Slide 9




## 10.3. What the Project Does Not Take
1. **Any code.** [`SLR_S2.2`](#22-licence) — there is no licence granting permission
2. **Any checkpoint.** Same reason, plus dependence on personal cloud storage
3. **The training recipe.** Eight GPUs and a 2021 CUDA toolchain
4. **The benchmark datasets.** Predominantly non-commercial; none is Singaporean
5. **`Spoken2Sign`'s implementation.** `RSS` does the same job under MIT, on a CPU —
   [`SLR_S7.1`](#71-the-method)
6. **The offline assumption.** Everything but `Online` requires the complete utterance first

---





# 11. SOURCES
1. **`[S1]`**
   *Source:* `ref_repo/translation/slrt/SLRT/README.md` at `38a4f7b` — the six-paper index, venues
   and BibTeX entries
   *Reliability:* Official project documentation. The underlying papers are peer-reviewed and were
   **not** read in full for this review; only the repository's own documentation was read
2. **`[S2]`**
   *Source:* `ref_repo/translation/slrt/SLRT/Online/README.md` — the three-phase online framework
   and the offline-latency critique
   *Reliability:* Official, corresponding to Zuo, Wei and Mak, EMNLP 2024
3. **`[S3]`**
   *Source:* `ref_repo/translation/slrt/SLRT/Online/SLT/README.md` — the wait-k gloss2text network
   *Reliability:* Official
4. **`[S4]`**
   *Source:* `ref_repo/translation/slrt/SLRT/Online/requirements.txt` and
   `NLA-SLR/requirements.txt`, `Spoken2Sign/requirements.txt`
   *Reliability:* Primary — read from the clone
5. **`[S5]`**
   *Source:* Dataset licences as catalogued in
   [`LTR_S6`](../signlang-literature/LTR_signlang_literature_report.md#6-datasets), from
   `ref_repo/translation/signlang-literature/sign-language-processing.github.io/src/datasets/`
   *Reliability:* Secondary — a maintained community registry, not the licence texts themselves.
   ⚠ Verify against the dataset's own terms before relying on any of them
6. **`[S6]`**
   *Source:* `ref_repo/translation/slrt/SLRT/TwoStreamNetwork/README.md` — *"except CSL-Daily,
   whose downloading needs an agreement submission"*
   *Reliability:* Official
7. **`[S7]`**
   *Source:* `ref_repo/translation/slrt/SLRT/Online/CSLR/dataset/Dataset.py:9-17`, and the
   equivalent `Openpose_Part2index` / HRNet block at `TwoStreamNetwork/dataset/Dataset.py:8-23`
   *Reliability:* Primary — read from the clone at `38a4f7b`
8. **`[S8]`**
   *Source:* `ref_repo/translation/slrt/SLRT/TwoStreamNetwork/README.md` — the SingleStream-SLT,
   Twostream-SLR and Twostream-SLT results tables
   *Reliability:* Official, self-reported by the authors, corresponding to NeurIPS 2022 and CVPR
   2022 publications. Not independently reproduced here
9. **`[S9]`**
   *Source:* [`LTR_S5.2`](../signlang-literature/LTR_signlang_literature_report.md#52-the-gloss-question),
   reporting Müller et al. 2023's recommendations on gloss-based research
   *Reliability:* Secondary — a survey's summary of a peer-reviewed position paper
10. **`[S10]`**
    *Source:* `ref_repo/translation/slrt/SLRT/NLA-SLR/README.md` — the WLASL and MSASL
    performance table
    *Reliability:* Official, self-reported, corresponding to Zuo, Wei and Mak, CVPR 2023
11. **`[S11]`**
    *Source:* `ref_repo/translation/slrt/SLRT/Online/CSLR/README.md` — `gen_segment.py`,
    `sign_augment.py`, and the pseudo-ground-truth caveat
    *Reliability:* Official
12. **`[S12]`**
    *Source:* `ref_repo/translation/slrt/SLRT/Online/CSLR/configs/slide_phoenix-2014t.yaml:4-42`
    *Reliability:* Primary — read from the clone
13. **`[S13]`**
    *Source:* `ref_repo/translation/slrt/SLRT/Online/SLT/configs/g2t_wait2.yaml:75`, and the
    identical setting in the other three `Online/SLT/configs/*.yaml`
    *Reliability:* Primary — read from the clone
14. **`[S14]`**
    *Source:* `ref_repo/translation/slrt/SLRT/Spoken2Sign/README.md` — the three-step baseline, the
    SMPL-X and Blender requirements, and the back-translation evaluation
    *Reliability:* Official, corresponding to Zuo et al., ECCV 2024
15. **`[S15]`**
    *Source:* The clone itself at `38a4f7b` (2025-02-21). All `file:line` citations resolve against
    this commit. File and configuration counts were obtained by enumeration of the working tree
    *Reliability:* Primary

---





# 12. CHANGE LOG
1. **2026-09-04** · *Author:* Claude (Opus 5)
   *Change:* Created from a read of the root and five sub-project READMEs, the requirements files,
   the keypoint-selection code, all 39 configurations that set `use_keypoints`, the sliding-window
   and wait-k configurations, and a search for a licence file. Recorded the absence of any licence
   as the disqualifying fact; the WLASL/MSASL vocabulary-size curve as the strongest available
   evidence for the closed-vocabulary decision; the 63/79-keypoint budget as independent
   confirmation of [`ARC_S3.2`](../../../plan/ARC_architecture.md#32-the-landmark-budget); and the
   `Online` sliding-window design as a measurable alternative to geometric segmentation.
