**SIGN LANGUAGE PROCESSING LITERATURE — SYNTHESIS FOR SIMPLYNEXT**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field             | Value                                                                                  |
| :---------------- | :------------------------------------------------------------------------------------- |
| **Code**          | `LTS`                                                                                  |
| **Status**        | Live                                                                                   |
| **Last reviewed** | 2026-09-04                                                                             |
| **Scope**         | Short orientation to `RLT` and the facts it settles                                    |
| **Subject**       | `RLT` — `signlang-literature/…github.io/` at `af5fb4a`                                 |
| **Full report**   | [`LTR`](../ref_repo/translation/signlang-literature/LTR_signlang_literature_report.md) |

**For the team.** Not software — a **maintained survey of the sign language processing field**,
plus a machine-readable registry of **49 datasets**. It is the evidence base the rest of
`ref_repo/translation/` should be read against, and it settles half of
[`ARC_S9.1`](../plan/ARC_architecture.md#91-open-questions-for-the-team) question 2 on its own:
**no Singapore Sign Language dataset exists**. The complete analysis is in
[`LTR`](../ref_repo/translation/signlang-literature/LTR_signlang_literature_report.md), beside the
clone in `ref_repo/translation/signlang-literature/`.

**For the assistant.** `RLT` is ⚠ **a survey, not a primary source**. Everything taken from it is
one step removed — a maintained summary of papers not read for this review — and must be marked so
under [`CLD_S5.1`](../CLAUDE.md#51-evidence). Cite the underlying paper where a number matters.
Where this file and
[`LTR`](../ref_repo/translation/signlang-literature/LTR_signlang_literature_report.md) disagree,
`LTR` wins.

</details>

---





# 1. WHAT THIS IS
The source of `sign-language-processing.github.io` — *"to contain and organize the sign language
processing literature, datasets, and tasks"*.

| Artefact             | File                  | Size        |
| :------------------- | :-------------------- | :---------- |
| The survey           | `src/index.md`        | 1,346 lines |
| The bibliography     | `src/references.bib`  | 4,892 lines |
| The dataset registry | `src/datasets/*.json` | 49 files    |

Citable as Moryossef and Goldberg, *Sign Language Processing*, 2021. **CC BY 4.0**, © Nagish Inc.
Maintained continuously — the clone is `af5fb4a`, **2026-08-11**. Its author also writes `RSP`
([`SPS`](SPS_sign_pose_synthesis.md)) and co-authors `RSS`
([`SSS`](SSS_spoken_to_signed_synthesis.md)).

The survey opens with the reason the field exists: *"around 200 to 300 different signed languages …
and up to 70 million deaf people"* are excluded by technology that assumes spoken-language input.

---





# 2. THE LINGUISTICS THE PRODUCT MUST RESPECT
## 2.1. Simultaneity
> *"Though an ASL sign takes about twice as long to produce than an English word, the rates of
> transmission of information between the two languages are similar."*

The mechanism is **simultaneity** — *"multiple visual cues to convey different information
simultaneously"*. The survey's example: signing *cup* on one hand while pointing at the actual cup
with the other, meaning *that cup*. *"Facial expressions can modify adjectives, adverbs, and verbs;
a head shake can negate a phrase or sentence; eye direction can help indicate referents."*

> **This is the structural argument against a linear gloss sequence**, and the reason
> [`ARC_S3.2`](../plan/ARC_architecture.md#32-the-landmark-budget) keeps face landmarks at all. A
> pipeline emitting one gloss per time step has, by construction, one channel.

The information-rate observation is also the honest answer to *"why not just wait for the whole
sentence?"* — signs are slow, so latency compounds.




## 2.2. Three Things a Fixed Vocabulary Cannot Hold
1. **Spatial referencing** — a signer assigns a region of signing space to a referent and points
   back to it. A **directional verb** *"can move from its subject's location and end at its
   object's location"* — not one sign but a family parameterised by two positions
2. **Role shift** — to quote someone, signers *"physically shift in space … and take on some
   characteristics of the people they represent"*
3. **Classifiers** — productive, depicting signs used to show how a referent moves. Generated, not
   looked up

> **Warning — the submission must not imply it handles these.** Role shift is the most dangerous:
> a system that misses it will attribute a **quoted** utterance to the signer as their own
> statement. This belongs in [`RSK_S3.3`](../plan/RSK_risk_register.md#33-lexicon-and-reference)
> and on the limitations slide.




## 2.3. Why Pose, Stated Better Than `ARC` Currently States It
Of the five representations the survey ranks, two matter:

- **Video** — *"As facial features are essential in sign, anonymizing raw videos remains an open
  problem, limiting the possibility of making these videos publicly available."*
- **Skeletal poses** — *"lower complexity and provide a **semi-anonymized** representation … while
  observing relatively low information loss"*, but *"remain a continuous, multidimensional
  representation that is not adapted to most NLP models."*

> Video anonymisation is unsolved **precisely because the face is linguistically necessary** — a
> sharper form of the privacy argument in
> [`ARC_S4.1`](../plan/ARC_architecture.md#41-verdict-right-instinct-over-specified), and one for
> [`RSK_S8.3`](../plan/RSK_risk_register.md#83-privacy-and-data-protection). The survey also names
> the cost honestly: a pose sequence is still continuous and *"not adapted to most NLP models"* —
> the gap the project's classifier exists to bridge.

---





# 3. TWO FINDINGS THAT CHANGE THE PLAN
## 3.1. Split by Signer, Not at Random
Pal et al., 2023 *"conducted a detailed analysis of the impact of signer overlap between the
training and test sets … they noticed a relative decrease in performance for signers not present
during training [and] suggested new dataset partitions that eliminate overlap."*

> **Warning — a random train/test split of self-recorded data will report an inflated number.** If
> the project records its vocabulary with a few people and splits the clips randomly, the same
> signers appear on both sides and the measured accuracy describes *signer-dependent* recognition.
> The demo will then be worse than the slide. **Split by signer, and say so.** `RSA`'s AUTSL
> figures are trustworthy precisely because the challenge enforced this
> ([`SAS_S3`](SAS_sam_slr_synthesis.md#3-the-table-that-settles-the-depth-camera)).




## 3.2. Evidence Against the Geometric Segmenter
Börstell, 2024 *"evaluated three approaches to segmenting the Swedish Sign Language (STS) Corpus
into utterance units—prosodic, syntactic, and translation-based—and found low alignment between
them as well as **no clear correspondence between utterance boundaries and articulatory features of
the hands and head extracted with MediaPipe**."*

> **Warning — this argues against
> [`ARC_S5.3`](../plan/ARC_architecture.md#53-recommended-approach)'s segmenter, and it is recorded
> rather than buried.** Stage ④ is *"geometry + hysteresis, no model"*, assuming pauses and hand
> position mark utterance boundaries. This study found no clear correspondence — and that three
> *human* definitions of an utterance boundary disagree with each other.
>
> ⚠ Read from a survey summary; one corpus, one sign language; and it concerns **utterance**
> boundaries, not the **sign** boundaries a closed-vocabulary classifier needs. Those are different
> granularities and the finding does not straightforwardly transfer.
>
> **What follows is not that the design is wrong, but that its assumption is contested and must be
> measured.** Two mitigations already exist in `ref_repo/`: `RSL`'s sliding window avoids boundary
> detection entirely ([`SLS_S6`](SLS_slrt_synthesis.md#6-the-architecture-worth-copying)), and
> Moryossef et al. 2023 says which features to add if boundaries are attempted —
> [`LTS_S4`](#4-the-tasks-under-their-proper-names).

---





# 4. THE TASKS, UNDER THEIR PROPER NAMES
Using the field's own vocabulary on the architecture slide is free credibility.

1. **Sign language detection** — *"the binary classification task of determining whether signing
   activity is present"*, analogous to **voice activity detection**. Moryossef et al., 2020 did it
   in real time *"on top of estimated human poses rather than directly on the video signal … the
   **optical flow norm of every joint** … and a shallow yet effective contextualized model."*
   > A cheap, published, pose-based upgrade to the geometric gate at stage ④. Its inputs already
   > exist — per-joint flow norm is the frame-to-frame landmark displacement magnitude, which the
   > project computes anyway for velocity features. It is the thing `RSS`'s source comment wishes
   > it had ([`SSS_S5`](SSS_spoken_to_signed_synthesis.md#5-what-it-teaches-the-forward-direction)).

2. **Sign language segmentation** — *"due to the simultaneity of sign language, the notion of a
   sign language 'word' is ill-defined."* Moryossef et al., 2023: **BIO** labelling *"makes a
   significant difference"* over IO, and *"including **optical flow and 3D hand normalization**
   helps with out-of-domain generalization."*
   > Three adoptable specifics — a *beginning* tag, optical flow, and 3D hand normalisation, which
   > `RSP` already implements as `normalize_hands_3d()`
   > ([`SPS_S3.3`](SPS_sign_pose_synthesis.md#33-normalize_hands_3d--rotation-canonical-handshape)).

3. **Pose-to-gloss (recognition)** — three items:
   - **OpenHands** (2022) — pose datasets and pretrained ISLR checkpoints across six languages,
     with *"high crosslingual transfer from Indian-SL to a few other sign languages."* If SgSL is
     chosen, pretraining on another sign language is a named route out of the data problem
   - **Roh et al., 2024** — preprocessing **MediaPipe** keypoints for isolated recognition with
     **palm-anchor normalisation** and **bilinear interpolation of undetected hand keypoints**. The
     project's exact stage-③ problem, for its exact tracker
   - **Kezar et al., 2023** — predicting **phonological** properties (handshape) as auxiliary
     targets: more supervision from the same data

4. **Gloss-to-text** — Yin and Read, 2020 *"show that using the sign language recognition
   (video-to-gloss) system output outperforms using the gold annotated glosses."*
   > **The text model does better on the recogniser's noisy output than on clean human glosses**,
   > because it learns the noise distribution it will face. Consequence for
   > [`ARC_S6.1`](../plan/ARC_architecture.md#61-pipeline) stage ⑥: **develop and prompt the
   > assembler against real classifier output — top-k lists, realistic confidences, realistic
   > errors — never against hand-written clean glosses.**

5. **Video-to-text (gloss-free)** — **SignLLM** (2024) projects learned sign tokens into an LLM's
   embedding space; *"The LLM itself can be taken 'off the shelf' and **does not need to be
   trained**."* The closest published system to the project's own stance, validating
   [`ARC_S5.4`](../plan/ARC_architecture.md#54-corrections-to-scr--issues) from the research side.
   **SSVP-SLT** (2024) uses **facial blurring** during pretraining — *"while pretraining with
   blurring hurts performance, some can be recovered when finetuning with unblurred data"* — a named
   privacy technique with an honest statement of its cost

---





# 5. THE DATA SITUATION
**49 datasets, 23 languages.** The ones the rest of `ref_repo/translation/` is measured on:

| Dataset                | Language | Items  | Signers | Licence         |
| :--------------------- | :------- | -----: | ------: | :-------------- |
| RWTH-PHOENIX-Weather T | German   |  1,231 |   **9** | CC BY-NC-SA 3.0 |
| AUTSL                  | Turkish  |    226 |      43 | Codalab         |
| WLASL                  | American |  2,000 |     100 | C-UDA 1.0       |
| MS-ASL                 | American |  1,000 |     222 | Public          |
| How2Sign               | American | 16,000 |  **11** | CC BY-NC 4.0    |
| BOBSL                  | British  |  2,281 |      37 | non-commercial  |

> **Note the signer counts.** Every translation number in
> [`SLS_S4`](SLS_slrt_synthesis.md#4-the-translation-ceiling) rests on **nine people**. Read with
> [`LTS_S3.1`](#31-split-by-signer-not-at-random), generalisation to an unseen signer is the
> field's structural weak point — and the project, recording a handful of people, sits at the same
> weak point.

> **Warning — there is no Singapore Sign Language dataset in the registry.** The 23 languages are
> American, Argentinian, Australian, Bangla, British, Chinese, Finnish, Flemish, German, Indian,
> Irish, Kazakh-Russian, Korean, Netherlands, Polish, Slovene, Spanish, Swedish, Swiss-German,
> Swiss-Italian/Flemish and Turkish, plus multilingual and synthetic collections. A full-text
> search of the clone for *Singapore*, *SgSL* or `sls` returns one hit — a conference venue in the
> bibliography. `RSS`'s twenty fingerspelling alphabets confirm it independently
> ([`SSS_S4`](SSS_spoken_to_signed_synthesis.md#4-the-coverage-ladder)).

> **This settles half of
> [`ARC_S9.1`](../plan/ARC_architecture.md#91-open-questions-for-the-team) question 2.** The choice
> is not *"SgSL or ASL, both of which have data"*. It is: **ASL has 2,000-sign public corpora with
> 100+ signers; SgSL has nothing public at all.** A SgSL system means recording every sign it will
> ever recognise — entirely feasible for a closed vocabulary of the size
> [`SLS_S3`](SLS_slrt_synthesis.md#3-the-number-that-decides-the-vocabulary) recommends, and the
> strongest possible differentiator, because the gap is real and verifiable.

> **Warning — the field's benchmark data is predominantly non-commercial.** Most registry entries
> record `CC BY-NC*`, *"Research purpose on request"*, *"Authorized Academics"* or *"Custom"*.
> Permissive terms are the exception: LSA-T is MIT; ChicagoFSWild and MS-ASL are *"Public"*; WLASL
> is C-UDA 1.0. **RWTH-PHOENIX-Weather-2014T — the benchmark the whole translation literature
> reports on — is CC BY-NC-SA 3.0.**
>
> This makes recording the project's own vocabulary not only pragmatic but **licence-clean**: data
> the team records, with documented consent, carries terms the team sets. ⚠ The registry's licence
> field is a community summary, not a licence text; verify before relying on any entry.

---





# 6. THE GLOSS QUESTION
The survey is direct: linear glosses *"fail to capture all the information expressed simultaneously
through different cues, such as body posture, eye gaze, or spatial relations"*, and *"a standardized
gloss annotation protocol has yet to be established."*

Müller et al.'s 2023 recommendations, reproduced by the survey:

1. *"Demonstrate awareness of limitations of gloss approaches and explicitly discuss them."*
2. *"Focus on datasets beyond RWTH-PHOENIX-Weather-2014T. Openly discuss the limited size and
   linguistic domain of this dataset."*
3. *"If BLEU is used, compute it with **SacreBLEU**, report metric signatures and disable internal
   tokenization for gloss outputs. Do not compare to scores produced with a different or unknown
   evaluation procedure."*
4. Process glosses corpus-specifically, informed by transcription conventions.
5. Optimise gloss baselines with low-resource MT methods.

> **Recommendation 1 is a scoring opportunity** — the project's architecture is gloss-mediated, and
> stating its limits is both what this literature asks for and what
> [`JCR_S4.4`](../plan/JCR_judging_criteria.md#44-five-pressure-test-questions) rewards.
> **Recommendation 2 qualifies every number in [`SLS_S4`](SLS_slrt_synthesis.md#4-the-translation-ceiling).**
> **Recommendation 3 is a direct instruction for `EVL`.**

**Metrics, by output type.** Text: BLEU, chrF, COMET. Pose: naive MSE and Average Position Error
*"do not account for variations in sequence length"*, since *"the same sign will not always take
exactly the same amount of time to produce, even by the same signer"* — **DTW-MJE** aligns first,
**nDTW-MJE** adds normalisation and handles missing keypoints. Multi-channel: **SignBLEU** (2024)
scores n-grams within and across channels — one per hand, others for non-manual signals — and its
authors report better correlation with human judgement than BLEU, TER, chrF or METEOR.

> The missing-keypoint problem nDTW-MJE addresses is the same one `RSS` solves with
> confidence-product weighting — two independent recognitions that a pose distance must handle
> absence explicitly. And **SignBLEU is the metric shaped like the simultaneity problem**; the
> project will not have multi-channel annotations, but naming it shows the limitation was
> understood rather than overlooked.

---





# 7. THE ELEVEN LESSONS
| #   | Lesson                                                                                   |
| :-- | :--------------------------------------------------------------------------------------- |
| T1  | **No SgSL dataset exists.** The choice is *public ASL data* against *record it yourself* |
| T2  | **The field's benchmarks are mostly non-commercial**, including PHOENIX-2014T            |
| T3  | **Split by signer, not at random**, or the reported number is signer-dependent           |
| T4  | **Simultaneity makes a linear gloss sequence structurally lossy** — say so               |
| T5  | **Directional verbs, classifiers and role shift are not in any fixed vocabulary**        |
| T6  | **Sign language detection is a solved, cheap, pose-based task** — per-joint flow norm    |
| T7  | **BIO beats IO** for segmentation; optical flow and 3D hand normalisation help           |
| T8  | ⚠ **Utterance boundaries may not correspond to MediaPipe articulatory features**         |
| T9  | **Train the text stage on noisy recogniser output**, not on gold glosses                 |
| T10 | **Pose is semi-anonymised; video is not**, because the face is linguistically necessary  |
| T11 | **If BLEU is used, use SacreBLEU with a published signature**, and compare nothing else  |

T8 is the uncomfortable one, and the reason it is in the table rather than a footnote. A finding
that argues against the project's own design is exactly what
[`CLD_S5.1`](../CLAUDE.md#51-evidence) exists to preserve.

---





# 8. WHAT IT DOES NOT DO
1. **It is not software.** Nothing here can be imported or trained
2. **It contains no data**, only descriptors of data hosted elsewhere
3. **It reports no numbers of its own.** Accuracies live in the papers it cites
4. **It is not exhaustive**, and does not claim to be
5. **It has visible gaps** — `TODO` markers and commented-out sections remain
6. **It covers no Southeast Asian sign language**
7. **It cannot substitute for reading a paper.** Every claim taken from it is one step removed

---





# 9. RUNNING IT
There is nothing to run — the rendered survey is public at `sign-language-processing.github.io`,
and building it needs Pandoc.

Two things in the clone are worth consuming directly: `src/datasets/*.json`, the machine-readable
registry; and `src/references.bib`, 4,892 lines and the fastest route to a correctly formatted
citation for anything in this field — which matters because
[`JCR_S4.4`](../plan/JCR_judging_criteria.md#44-five-pressure-test-questions) demands *"a figure, a
source, and a date"*.

---





# 10. WHERE TO GO NEXT
1. **Full breakdown** —
   [`LTR`](../ref_repo/translation/signlang-literature/LTR_signlang_literature_report.md)
2. **The field's numbers** — [`SLS`](SLS_slrt_synthesis.md)
3. **The pose library** — [`SPS`](SPS_sign_pose_synthesis.md)
4. **The reverse direction** — [`SSS`](SSS_spoken_to_signed_synthesis.md)
5. **The data and language question** — [`ARC_S9.1`](../plan/ARC_architecture.md)
6. **Where every document lives** — [`RIX`](../ref_index.md)

---





# 11. CHANGE LOG
1. **2026-09-04** · *Author:* Claude (Opus 5)
   *Change:* Created alongside
   [`LTR`](../ref_repo/translation/signlang-literature/LTR_signlang_literature_report.md), from a
   read of the introduction, linguistics, representations, detection, segmentation, pose-to-gloss,
   gloss-to-text, video-to-text and evaluation sections of `src/index.md`, plus a programmatic
   enumeration of the 49-dataset registry.
