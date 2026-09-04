**SIGN LANGUAGE PROCESSING LITERATURE — FULL REPOSITORY REPORT**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field                   | Value                                                      |
| :---------------------- | :--------------------------------------------------------- |
| **Code**                | `LTR`                                                      |
| **Status**              | Live                                                       |
| **Last reviewed**       | 2026-09-04                                                 |
| **Source of truth for** | Analysis of the sign-language-processing literature clone  |
| **Parent**              | [`RIX_S2.1`](../../../ref_index.md#21-live-documents)      |
| **Short version**       | [`LTS`](../../../doc/LTS_signlang_literature_synthesis.md) |
| **Subject**             | `RLT` — `signlang-literature/…github.io/` at `af5fb4a`     |

**For the team.** This clone is **not software**. It is the source of
`sign-language-processing.github.io`, a maintained survey of the sign language processing field:
a 1,346-line literature review, a 4,892-line BibTeX file, and a machine-readable registry of
**49 datasets**. It is the evidence base the rest of `ref_repo/translation/` should be read
against, and it settles two open questions on its own —
[`LTR_S6.2`](#62-what-is-not-there) shows that **no Singapore Sign Language dataset exists** in the
field's own registry, and [`LTR_S6.3`](#63-the-licence-pattern) shows that the benchmark corpora
the whole literature reports on are predominantly non-commercial.

**For the assistant.** `RLT` is **a survey, not a primary source**. Every claim taken from it is
one step removed: it is a maintained summary of papers that were not read for this review, and
must be marked accordingly under [`CLD_S5.1`](../../../CLAUDE.md#51-evidence). Cite the underlying
paper where a claim matters; cite `LTR` where the survey's own synthesis is the point. Nothing
inside `ref_repo/translation/signlang-literature/` may be edited; it is an unmodified clone,
excluded from version control.

</details>

---





# 1. EXECUTIVE SUMMARY
## 1.1. What This Repository Is
`ref_repo/translation/signlang-literature/sign-language-processing.github.io/` is the source of a
published survey. Its README states the goal plainly: *"to contain and organize the sign language
processing literature, datasets, and tasks"* `[S1]`. The rendered site is at
`sign-language-processing.github.io`; the repository is the Pandoc pipeline that builds it.

Its shape:

| Artefact             | File                    | Size        | Content                             |
| :------------------- | :---------------------- | :---------- | :---------------------------------- |
| The survey           | `src/index.md`          | 1,346 lines | Linguistics, representations, tasks |
| The bibliography     | `src/references.bib`    | 4,892 lines | Every work cited                    |
| The dataset registry | `src/datasets/*.json`   | 49 files    | One JSON per dataset                |
| The build            | `Makefile` plus scripts | ---         | Pandoc → HTML and LaTeX             |

The citable form is: Moryossef and Goldberg, *Sign Language Processing*, 2021, `[S1]`. It is
maintained continuously rather than published once — the clone is at `af5fb4a`, **2026-08-11**.

Authorship links it to the rest of the stack: Amit Moryossef also authors `RSP`
([`SPR`](../sign-pose/SPR_sign_pose_report.md)) and co-authors `RSS`
([`SSR`](../spoken-to-signed/SSR_spoken_to_signed_report.md)). Reading the three together is
reading one group's survey, format and reference implementation.




## 1.2. Why It Matters to SimplyNext
It is the only thing in `ref_repo/` that answers *"what does the field already know?"* rather than
*"what does this program do?"*

1. **It closes two open questions with facts, not argument** · *Use:*
   [`ARC_S9.1`](../../../plan/ARC_architecture.md#91-open-questions-for-the-team) question 2 (SgSL
   or ASL) and question 4 (data) both turn on what data exists.
   [`LTR_S6`](#6-datasets) enumerates it: 49 datasets, 23 languages, **none Singaporean**
2. **It names the tasks the project is decomposing** · *Use:* The survey's taxonomy —
   *detection*, *segmentation*, *video-to-gloss*, *gloss-to-text*, *pose-to-text*, *text-to-gloss*
   — is the formal vocabulary for
   [`ARC_S5.1`](../../../plan/ARC_architecture.md#51-three-problems-inside-step-4)'s three
   problems. Using the field's names on the architecture slide is free credibility
3. **It supplies the linguistics the product must respect** · *Use:*
   [`LTR_S3`](#3-the-linguistics-that-constrain-the-product) records simultaneity, spatial
   referencing, role shift and classifiers — the features a linear gloss sequence structurally
   cannot carry, and which the submission must therefore not claim to handle
4. **It supplies methodology the evaluation must follow** · *Use:*
   [`LTR_S5.4`](#54-evaluation-metrics) and the signer-overlap finding in
   [`LTR_S4.1`](#41-sign-language-detection) are direct instructions for `EVL`
5. **It contains one finding that argues against the current design** · *Use:*
   [`LTR_S4.2`](#42-sign-language-segmentation) reports a 2024 study finding no clear
   correspondence between utterance boundaries and MediaPipe-extracted articulatory features. That
   is a counter-argument to
   [`ARC_S5.3`](../../../plan/ARC_architecture.md#53-recommended-approach)'s geometric segmenter,
   and it is recorded here because
   [`CLD_S5.1`](../../../CLAUDE.md#51-evidence) requires it to be

Against the four MVP steps in [`SCR`](../../../plan/scribbles.md): it addresses all four as
literature, and none as code.




## 1.3. Summary
The survey opens with why sign language processing exists — *"around 200 to 300 different signed
languages … and up to 70 million deaf people"* are excluded by technology that assumes spoken-language
input `[S2]` — then covers the linguistics a modeller must know, then the five candidate
representations (video, skeletal pose, radar, written notation, glosses), then a task-by-task
review organised as a matrix of source and target representations, then evaluation metrics, then
datasets and annotation tools. The recurring theme is that the field's dominant intermediate
representation, the **gloss**, is a lossy linearisation of a simultaneous language, and that the
field knows it.

---





# 2. PROVENANCE, LICENCE AND BUILD
## 2.1. Provenance
1. **Publisher**
   Amit Moryossef and Yoav Goldberg, with community contributions. Remote:
   `https://github.com/sign-language-processing/sign-language-processing.github.io.git`
2. **Clone state**
   `af5fb4a`, **2026-08-11**, *"Apply automatic changes"* — a scheduled build commit
3. **Maintenance status**
   **Active**, and updated by automation as well as by hand. Citations dated 2024 appear
   throughout `src/index.md`
4. **Scale**
   17 MB; 1,346 lines of survey, 4,892 lines of BibTeX, 49 dataset descriptors
5. **Nature**
   Prose and data. There is no library here to depend on




## 2.2. Licence
`LICENSE`: *"Attribution 4.0 International"* — **CC BY 4.0** — *"Copyright (c) 2026 Nagish Inc."*
`[S3]`.

CC BY permits sharing and adaptation, including commercially, on the single condition of
attribution. For a *document*, that is as permissive as it gets.

> **Note — the licence covers the survey text and the registry, not the works surveyed.** Quoting
> the survey requires attribution to Moryossef and Goldberg. Quoting a *paper* the survey
> describes requires citing that paper. The two are separate obligations, and this report keeps
> them separate: every claim below is tagged either as the survey's own statement or as the
> survey's report of someone else's.




## 2.3. Build
`make` runs Pandoc over `src/index.md` with `src/references.bib`, `src/header.html` and a template,
emitting HTML and LaTeX. `src/datasets.js` renders the JSON registry into the datasets table with
per-feature emoji. `src/split_sections.py`, `src/replace_gifs.py`, `src/find_bare_citations.py` and
`addons/` are build utilities. Pandoc must be installed `[S1]`.

The project has no reason to build it — the rendered site is public — but the **registry is
machine-readable and worth consuming directly**, which is what [`LTR_S6`](#6-datasets) does.

---





# 3. THE LINGUISTICS THAT CONSTRAIN THE PRODUCT
The survey's linguistics section is short and every part of it bears on a design decision. All
claims in this section are the survey's, citing works not read for this review `[S2]`.




## 3.1. Simultaneity
> *"Though an ASL sign takes about twice as long to produce than an English word, the rates of
> transmission of information between the two languages are similar."*

The mechanism is **simultaneity**: *"Signed languages use multiple visual cues to convey different
information simultaneously."* The survey's example is producing the sign for *cup* on one hand
while pointing at the actual cup with the other, to mean *that cup*. Facial expressions *"modify
adjectives, adverbs, and verbs; a head shake can negate a phrase or sentence; eye direction can
help indicate referents."*

> **This is the structural argument against a linear gloss sequence**, and it is the reason
> [`ARC_S3.2`](../../../plan/ARC_architecture.md#32-the-landmark-budget) keeps face landmarks at
> all. A pipeline that emits one gloss per time step has, by construction, one channel. The
> survey's *Multi-Channel Block output* discussion ([`LTR_S5.4`](#54-evaluation-metrics)) is the
> field's response to exactly this.

The information-rate observation is also the honest answer to *"why not just wait for the whole
sentence?"* — signs are slow, so an utterance takes real time, and latency compounds.




## 3.2. Spatial Referencing, Role Shift, Classifiers
Three phenomena, each of which a closed-vocabulary classifier **cannot represent**:

1. **Spatial referencing** — a signer assigns a region of signing space to a referent and points
   back to it later. *"Spatial referencing also impact[s] morphology when the directionality of a
   verb depends on the location of the reference to its subject and/or object"* — a directional
   verb *"can move from its subject's location and end at its object's location"*
2. **Role shift** — to quote another person, signers *"physically shift in space … and take on some
   characteristics of the people they represent"*, including gaze direction and posture
3. **Classifiers** — *"typically one-handed signs that do not have a particular location or
   movement assigned to them"*, used productively to depict how a referent moves and relates to
   others. The survey's example is a vehicle classifier swerving and crashing

> **Warning — none of these is in a fixed vocabulary, and the submission must not imply otherwise.**
> A directional verb is not one sign but a family parameterised by two positions. A classifier
> construction is generated, not looked up. A role shift changes who the subsequent signs are
> attributed to — the most dangerous failure available to this product, because a system that
> misses it will attribute a quoted utterance to the signer as their own statement. This belongs
> in [`RSK_S3.3`](../../../plan/RSK_risk_register.md#33-lexicon-and-reference) and on the
> limitations slide, per
> [`CLD_S5.2`](../../../CLAUDE.md#52-honesty-about-the-product).




## 3.3. Fingerspelling
*"Fingerspelling results from language contact between a signed language and a surrounding spoken
language written form … often used to indicate names or places or new concepts from the spoken
language but has often become integrated into the signed languages as another linguistic
strategy."*

Two consequences. It is the **universal escape hatch** for out-of-vocabulary items — which is why
`RSS` makes it the default fallback
([`SSR_S6`](../spoken-to-signed/SSR_spoken_to_signed_report.md#6-the-coverage-ladder--the-most-transferable-idea-here))
and why *"request fingerspelling"* is a repair action in
[`ARC_S6.1`](../../../plan/ARC_architecture.md#61-pipeline) stage ⑨. And it is **not just a
fallback**: fingerspelled forms lexicalise, so a fingerspelling recogniser is part of the language,
not a patch over it. The survey gives it its own task section with separate recognition and
production literature.




## 3.4. Representations, and Why Pose
The survey ranks five representations `[S2]`:

1. **Video** — *"the most straightforward … can amply incorporate the information"*, but
   high-dimensional, expensive, and: *"As facial features are essential in sign, anonymizing raw
   videos remains an open problem, limiting the possibility of making these videos publicly
   available."*
2. **Skeletal poses** — *"lower complexity and provide a semi-anonymized representation of the
   human body, while observing relatively low information loss"*, but *"remain a continuous,
   multidimensional representation that is not adapted to most NLP models"*
3. **Radar sensing** — kinematics without images, *"inherently protecting signer identity"*.
   ⚠ Surveyed from a 2024 paper; hardware the project is not buying
4. **Written notation** — SignWriting, HamNoSys and others. *"no writing system has been adopted
   widely by any sign language community"*
5. **Glosses** — [`LTR_S5.2`](#52-the-gloss-question)

> **Two things follow for [`ARC_S4`](../../../plan/ARC_architecture.md#4-step-3--the-3d-skeleton).**
> First, the survey independently states the privacy argument the document already makes: pose is
> *semi-anonymised*, and video anonymisation is an open problem **precisely because the face is
> linguistically necessary**. That is a sharper version of the claim than
> [`ARC_S4.1`](../../../plan/ARC_architecture.md#41-verdict-right-instinct-over-specified)
> currently carries, and it belongs in [`RSK_S8.3`](../../../plan/RSK_risk_register.md#83-privacy-and-data-protection).
> Second, the survey names the cost honestly: a pose sequence is still continuous and
> multidimensional, and *"not adapted to most NLP models"*. That is the gap the project's
> classifier exists to bridge.




## 3.5. A Terminology Note
The survey footnotes its own usage `[S2]`: *"When capitalized, 'Deaf' refers to a community of deaf
people who share a language and a culture, whereas the lowercase 'deaf' refers to the audiological
condition of not hearing. We follow the more recent convention of abandoning a distinction between
'Deaf' and 'deaf', using the latter term also to refer to (deaf) members of the sign language
community."*

> **Note — the project's documents currently use both forms.** The survey's convention is one
> defensible option and its reasoning is worth reading before the deck is written; it is not the
> only convention in use. This is a decision for the team, not for the assistant, and it should be
> made once and applied consistently — see
> [`ARC_S7.6`](../../../plan/ARC_architecture.md#76-p6--gloves-rejected-on-the-record), where the
> commitment to consult a deaf reviewer already exists.

---





# 4. THE TASKS THE PROJECT IS ACTUALLY BUILDING
The survey organises sign language processing as a matrix over representations — every
`<source>-to-<target>` pair gets a section. Four of them are the project's own pipeline stages
under their proper names.




## 4.1. Sign Language Detection
*"the binary classification task of determining whether signing activity is present in a given
video frame"*, with the spoken-language analogue named as **voice activity detection** `[S2]`.

The survey's account of the two main approaches is directly useful:

1. **Borg and Camilleri, 2019** — VGG-16 per frame plus a GRU over *"a window of 20 frames at
   5fps"*, with optical-flow history, aggregated motion history or frame difference as extra
   channels
2. **Moryossef et al., 2020** — *"improved upon their method by performing sign language detection
   in real time … designed a model that works on top of estimated human poses rather than directly
   on the video signal. They calculated the **optical flow norm of every joint** detected on the
   body and applied a shallow yet effective contextualized model to predict for every frame whether
   the person is signing or not."*

> **The second is a cheap, published, pose-based answer to a stage
> [`ARC`](../../../plan/ARC_architecture.md) currently leaves to geometry alone.** Its inputs are
> already available — per-joint optical flow norm is the magnitude of the frame-to-frame landmark
> displacement, which the project computes anyway for its velocity features
> ([`ARC_S4.3`](../../../plan/ARC_architecture.md#43-recommended-representation) step 4). Its
> model is *"shallow"*. It is the natural upgrade to the hands-in-signing-space gate at stage ④,
> and the thing `RSS`'s source comment wishes it had
> ([`SSR_S5.1`](../spoken-to-signed/SSR_spoken_to_signed_report.md#51-finding-the-signing-span)).

**And a methodological warning that changes `EVL`.** Pal et al., 2023 *"conducted a detailed
analysis of the impact of signer overlap between the training and test sets on two sign detection
benchmark datasets … By comparing the accuracy with and without overlap, they noticed a relative
decrease in performance for signers not present during training. As a result, they suggested new
dataset partitions that eliminate overlap between train and test sets"* `[S2]`.

> **Warning — a random train/test split of self-recorded data will report an inflated number.** If
> the project records its vocabulary with a small number of people and splits the clips randomly,
> the same signers appear on both sides and the measured accuracy describes *signer-dependent*
> recognition. The demo will then be worse than the slide. **Split by signer, and say so.**
> `RSA`'s AUTSL numbers are trustworthy precisely because the challenge enforced this
> ([`SAR_S2.4`](../sam-slr/SAR_sam_slr_report.md#24-the-dataset-which-explains-the-numbers)).
> Recorded for `EVL` and for [`RSK_S4.2`](../../../plan/RSK_risk_register.md#42-model-and-evaluation).




## 4.2. Sign Language Segmentation
*"detecting the frame boundaries for signs or phrases in videos to divide them into meaningful
units"*. The survey states the difficulty first `[S2]`:

> *"While the most canonical way of dividing a spoken language text is into a linear sequence of
> words, due to the simultaneity of sign language, the notion of a sign language 'word' is
> ill-defined, and sign language cannot be fully linearly modeled."*

And criticises the state of the art: current methods *"do not explicitly leverage reliable
linguistic predictors of sentence boundaries such as prosody in signed languages (i.e., pauses,
extended sign duration, facial expressions)"*.

Two results matter to the project's stage ④.

**Moryossef et al., 2023** *"presented a method motivated by linguistic cues observed in sign
language corpora, such as prosody (pauses, pace, etc) and handshape changes. They also find that
using **BIO**, an annotation scheme that notes the beginning, inside and outside, makes a
significant difference over previous ones that only note IO (inside or outside). They find that
including **optical flow and 3D hand normalization** helps with out-of-domain generalization and
other signed languages as well."* `[S2]`

> Three adoptable specifics: label segments **BIO rather than IO** — an explicit *beginning* tag,
> not merely *inside/outside*; feed **optical flow**; and apply **3D hand normalisation**, which
> `RSP` already implements as `normalize_hands_3d()`
> ([`SPR_S5.4`](../sign-pose/SPR_sign_pose_report.md#54-wrist-correction)). The last two are
> reported to help *out-of-domain* generalisation specifically, which is the project's whole
> problem.

**Börstell, 2024** — and this one cuts against the current design. The survey reports that this
study *"evaluated three approaches to segmenting the Swedish Sign Language (STS) Corpus into
utterance units—prosodic, syntactic, and translation-based—and found low alignment between them as
well as **no clear correspondence between utterance boundaries and articulatory features of the
hands and head extracted with MediaPipe**."* `[S2]`

> **Warning — this is evidence against
> [`ARC_S5.3`](../../../plan/ARC_architecture.md#53-recommended-approach)'s segmenter, and it is
> recorded rather than buried.** The project's stage ④ is *"geometry + hysteresis, no model"*, on
> the assumption that pauses and hand position mark utterance boundaries. This study, on one
> corpus and one sign language, found no clear correspondence between such features and
> utterance boundaries — and additionally found that three *human* definitions of an utterance
> boundary disagree with each other.
>
> ⚠ Read from a survey summary; the paper was not read. It is one corpus and one language, and
> it concerns **utterance** boundaries, not the **sign** boundaries a closed-vocabulary classifier
> needs — those are different granularities and the finding does not straightforwardly transfer.
>
> **What follows is not that the design is wrong, but that its assumption is now known to be
> contested and must be measured rather than asserted.** Two mitigations are already available in
> `ref_repo/`: `RSL`'s sliding window avoids boundary detection entirely
> ([`SLR_S6.3`](../slrt/SLR_slrt_report.md#63-the-sliding-window-parameters)), and this section's
> Moryossef 2023 result says which features to add if boundaries are attempted. Recorded as an
> open question in [`ARC_S9.1`](../../../plan/ARC_architecture.md#91-open-questions-for-the-team).




## 4.3. Recognition, and the Preprocessing Nobody Documents
From the survey's **Pose-to-Gloss** section `[S2]`, three items the project can act on:

1. **OpenHands** (Selvaraj et al., 2022) — *"an open-source library … standardized pose datasets
   for different existing sign language datasets and trained checkpoints of four pose-based
   isolated sign language recognition models across six languages (American, Argentinian, Chinese,
   Greek, Indian, and Turkish)"*, which *"demonstrat[es] improved fine-tuning performance
   especially in low-resource settings and **high crosslingual transfer from Indian-SL to a few
   other sign languages**."*
   > Pretrained pose-based ISLR checkpoints, and evidence that transfer across sign languages
   > works. If SgSL is chosen, pretraining on another sign language's pose data is a named,
   > published route out of the data problem. ⚠ Not in `ref_repo/`; not inspected
2. **Roh et al., 2024** — *"focus on preprocessing **MediaPipe** keypoints for isolated SLR by
   introducing **palm-anchor-based normalization** to emphasize hand shape and **bilinear
   interpolation to reconstruct undetected hand keypoints**, achieving the highest accuracy on
   WLASL-100 with a Transformer encoder among pose-based approaches at the time."*
   > This is the project's exact stage-③ problem, addressed for the project's exact tracker. Two
   > techniques: anchor the hand on the palm rather than the wrist, and **interpolate missing
   > keypoints** rather than passing zeros — the natural companion to
   > [`SPR_S5.4`](../sign-pose/SPR_sign_pose_report.md#54-wrist-correction)'s wrist substitution
3. **Kezar et al., 2023** — predicting **phonological** properties such as handshape as auxiliary
   targets, using ASL-LEX annotations
   > An auxiliary-loss idea for a small classifier: predicting *handshape* alongside *sign* gives
   > the model more supervision from the same data

And from **Gloss-to-Text**, one counter-intuitive result worth designing around: Yin and Read, 2020
*"show that using the sign language recognition (video-to-gloss) system output outperforms using
the gold annotated glosses"* when training the gloss-to-text model `[S2]`.

> **The downstream text model does better on the recogniser's noisy output than on clean human
> glosses**, because it learns the noise distribution it will actually face. The direct consequence
> for [`ARC_S6.1`](../../../plan/ARC_architecture.md#61-pipeline) stage ⑥: **develop and prompt the
> assembler against real classifier output — top-k lists with realistic confidences and realistic
> errors — never against a hand-written clean gloss sequence.** Few-shot examples built from clean
> glosses will mislead it.




## 4.4. Translation, and the Gloss-Free Route
The **Video-to-Text** section surveys the gloss-free literature `[S2]`. Two entries change how
[`ARC_S7`](../../../plan/ARC_architecture.md#7-alternatives-priority-ordered) should read.

**SignLLM** (Gong et al., 2024) converts sign video into *"discrete and hierarchical
representations compatible with LLMs"* through a vector-quantised *"character-level"* tokeniser and
a reconstruction module producing *"word-level"* tokens, which are *"projected into the LLM's
embedding space, which is then prompted for translation."* Critically: *"The LLM itself can be
taken 'off the shelf' and **does not need to be trained**."*

> This is the closest published system to the project's own stance — a small trained perception
> front-end feeding an untrained LLM — and it validates
> [`ARC_S5.4`](../../../plan/ARC_architecture.md#54-corrections-to-scr--issues)'s rejection of the
> *"train an LLM"* premise from the research side rather than the schedule side. ⚠ Reported by the
> survey; the paper was not read

**SSVP-SLT** (Rust et al., 2024) is a privacy-aware method that *"employs **facial blurring** during
pretraining"* and finds that *"while pretraining with blurring hurts performance, some can be
recovered when finetuning with unblurred data."*

> A named, published privacy technique with an honest statement of its cost. Directly relevant to
> [`RSK_S8.3`](../../../plan/RSK_risk_register.md#83-privacy-and-data-protection), and to any
> decision about retaining recorded video of consenting participants

---





# 5. WHAT THE SURVEY SAYS ABOUT METHOD
## 5.1. The Field's Own Warning About Its Numbers
Recorded here because it corroborates
[`ARC_S5.2`](../../../plan/ARC_architecture.md#52-state-of-the-art)'s existing warning from an
independent direction.




## 5.2. The Gloss Question
The survey is direct `[S2]`:

> *"Linear gloss annotations have been criticized for their imprecise representation of signed
> language. These annotations fail to capture all the information expressed simultaneously through
> different cues, such as body posture, eye gaze, or spatial relations, leading to a loss of
> information that can significantly affect downstream performance on SLP tasks."*

and *"a standardized gloss annotation protocol has yet to be established."*

It then reproduces Müller et al.'s 2023 recommendations for anyone using glosses:

1. *"Demonstrate awareness of limitations of gloss approaches and explicitly discuss them."*
2. *"Focus on datasets beyond RWTH-PHOENIX-Weather-2014T. Openly discuss the limited size and
   linguistic domain of this dataset."*
3. *"Use metrics that are well-established in MT. If BLEU is used, compute it with **SacreBLEU**,
   report metric signatures and **disable internal tokenization for gloss outputs**. Do not compare
   to scores produced with a different or unknown evaluation procedure."*
4. *"Given that glossing is corpus-specific, process glosses in a corpus-specific way, informed by
   transcription conventions."*
5. *"Optimize gloss translation baselines with methods shown to be effective for low-resource MT."*

> **Recommendation 1 is a scoring opportunity.** The project's architecture is gloss-mediated, and
> stating its limitations explicitly is both what this literature asks for and what
> [`JCR_S4.4`](../../../plan/JCR_judging_criteria.md#44-five-pressure-test-questions) rewards.
>
> **Recommendation 2 qualifies every number in
> [`SLR_S5.1`](../slrt/SLR_slrt_report.md#51-translation-quality-with-gloss-supervision).**
> Phoenix-2014T is weather forecasts. The 28.95 BLEU-4 figure must never travel without that.
>
> **Recommendation 3 is a direct instruction for `EVL`:** if BLEU is reported at all, use
> SacreBLEU, publish the signature, and never compare against a number computed elsewhere by an
> unknown procedure.




## 5.3. Pose-to-Text Normalisation
From the **Pose-to-Text** section, on Ko et al., 2019: *"They experimented with various
normalization schemes, mainly subtracting the mean and dividing by the standard deviation of every
individual keypoint either concerning the entire frame or the relevant 'object' (Body, Face, and
Hand)."* `[S2]`

> Per-object normalisation — separate statistics for body, face and each hand — is a third option
> alongside the two in [`ARC_S4.3`](../../../plan/ARC_architecture.md#43-recommended-representation),
> and `RSP` implements it directly: `normalize_distribution(axis=...)`
> ([`SPR_S5.1`](../sign-pose/SPR_sign_pose_report.md#51-normalisation)). It is a cheap ablation.




## 5.4. Evaluation Metrics
The survey's metrics section, by output type `[S2]`:

1. **Text output** — *"standard machine translation metrics such as BLEU, chrF, or COMET"*
2. **Gloss output** — scorable, *"though not without issues"*; see
   [`LTR_S5.2`](#52-the-gloss-question)
3. **Pose output** — *"an open line of research"*. Naive MSE and Average Position Error *"do not
   account for variations in sequence length"* since *"the same sign will not always take exactly
   the same amount of time to produce, even by the same signer"*. **DTW-MJE** aligns sequences by
   dynamic time warping first; **nDTW-MJE** adds normalisation and *"a distance function that
   accounts for … missing keypoints"*
4. **Multi-channel output** — **SignBLEU** (Kim et al., 2024) segments output into *"multiple
   linear channels, each containing discrete 'blocks'"* — *"one for each hand and others for
   various non-manual signals like eyebrow movements"* — and scores temporal n-grams within a
   channel and *"channel grams"* across channels. The authors report it *"consistently correlated
   better to human evaluation"* than BLEU, TER, chrF and METEOR, with the limitation that
   multi-channel annotated corpora are scarce. Source code is public, and like SacreBLEU it emits
   a version signature

> **Two things for `EVL`.** The missing-keypoint problem that nDTW-MJE addresses is the same
> problem `RSS` solves with confidence-product weighting
> ([`SSR_S5.3`](../spoken-to-signed/SSR_spoken_to_signed_report.md#53-smoothing-the-seams)) —
> two independent recognitions that a pose distance must handle absence explicitly. And
> **SignBLEU is the metric shaped like the simultaneity problem**; the project will not have
> multi-channel annotations, but naming it on the evaluation slide demonstrates that the
> limitation of a single-channel metric was understood rather than overlooked.




## 5.5. Annotation Tools
The survey lists **ELAN**, **iLex** and **SignStream** as the field's annotation tools `[S2]`. If
the project records its own vocabulary and needs time-aligned labels, ELAN is the standard choice
and produces `.eaf` files the field can read. ⚠ Not inspected for this report.

---





# 6. DATASETS
`src/datasets/*.json` is a machine-readable registry, one file per dataset, each carrying a
publication, a language, item and sample counts, a signer count and a licence `[S4]`.




## 6.1. The Registry
**49 datasets across 23 languages.** The ones the rest of `ref_repo/translation/` is measured on:

| Dataset                | Language | Items  | Samples          | Signers | Licence         |
| :--------------------- | :------- | -----: | :--------------- | ------: | :-------------- |
| RWTH-PHOENIX-Weather T | German   | 1,231  | 8,257 sentences  |       9 | CC BY-NC-SA 3.0 |
| AUTSL                  | Turkish  |    226 | 36,302 samples   |      43 | Codalab         |
| WLASL                  | American | 2,000  | ---              |     100 | C-UDA 1.0       |
| MS-ASL                 | American | 1,000  | 25,513 (~25 h)   |     222 | Public          |
| How2Sign               | American | 16,000 | 79 h (35k sents) |      11 | CC BY-NC 4.0    |
| BOBSL                  | British  | 2,281  | 1.2M sentences   |      37 | non-commercial  |
| Public DGS Corpus      | German   |    --- | 50 hours         |     330 | Custom          |
| NMFs-CSL               | Chinese  | 1,067  | 32,010 videos    |      10 | On request      |

> **Note the signer counts.** Phoenix-2014T has **nine** signers; How2Sign has **eleven**. Every
> translation number in [`SLR_S5.1`](../slrt/SLR_slrt_report.md#51-translation-quality-with-gloss-supervision)
> rests on nine people. Read together with the signer-overlap finding in
> [`LTR_S4.1`](#41-sign-language-detection), generalisation to an unseen signer is the field's
> structural weak point — and the project, recording a handful of people, sits at the same
> weak point.




## 6.2. What Is Not There
> **Warning — there is no Singapore Sign Language dataset in the registry.** The 23 languages
> represented are American, Argentinian, Australian, Bangla, British, Chinese, Finnish, Flemish,
> German, Indian, Irish, Kazakh-Russian, Korean, Netherlands, Polish, Slovene, Spanish, Swedish,
> Swiss-German, Swiss-Italian/Flemish, Turkish, plus two multilingual collections and one
> synthetic ASL corpus. A search of the whole clone for *Singapore*, *SgSL* or the IANA subtag
> `sls` returns one hit — a conference venue in the bibliography `[S4]`.

This is corroborated independently: `RSS`'s fingerspelling lexicon covers twenty sign languages and
`sls` is not among them
([`SSR_S6.1`](../spoken-to-signed/SSR_spoken_to_signed_report.md#61-the-fingerspelling-lexicon)).
**No Southeast Asian sign language appears in either.**

> **This settles half of
> [`ARC_S9.1`](../../../plan/ARC_architecture.md#91-open-questions-for-the-team) question 2.** The
> choice is not *"SgSL or ASL, both of which have data"*. It is: **ASL has 2,000-sign public
> corpora with 100+ signers; SgSL has nothing public at all.** A SgSL system means recording every
> sign it will ever recognise. That is entirely feasible for a closed vocabulary of the size
> [`SLR_S5.2`](../slrt/SLR_slrt_report.md#52-recognition-accuracy-against-vocabulary-size)
> recommends — and it is the strongest possible differentiator, because the gap is real and
> verifiable. The trade is now stated in numbers rather than impressions.




## 6.3. The Licence Pattern
> **Warning — the field's benchmark data is predominantly non-commercial.** Of the 49 registry
> entries, the licence field records `CC BY-NC*` variants, *"non-commercial authorized academics"*,
> *"Research purpose on request"*, *"Authorized Academics"*, *"Permission"*, *"Partially
> Restricted"* or *"Custom"* for the large majority. Permissive or computational-use terms are the
> exception: **LSA-T is MIT**; ChicagoFSWild, ChicagoFSWild+ and MS-ASL are recorded as *"Public"*;
> WLASL is **C-UDA 1.0**; and a handful are *"Attribution"*.

Three consequences:

1. **This is the same class of problem as the `ROP` and `RSA` licences**, one layer down. A
   submission that could become a product cannot be trained on `CC BY-NC` data, and
   **RWTH-PHOENIX-Weather-2014T — the benchmark the entire translation literature reports on — is
   CC BY-NC-SA 3.0.**
2. **Recording the project's own vocabulary is therefore not only pragmatic but licence-clean.**
   Data the team records, with documented consent
   ([`RSK_S8.3`](../../../plan/RSK_risk_register.md#83-privacy-and-data-protection)), carries terms
   the team sets. This strengthens the answer to
   [`ARC_S9.1`](../../../plan/ARC_architecture.md#91-open-questions-for-the-team) question 4.
3. **⚠ The registry's licence field is a community summary, not a licence text.** Verify against
   the dataset's own terms before relying on any entry.

---





# 7. WHAT THE REPOSITORY DOES NOT DO
1. **It is not software.** Nothing here can be imported, called or trained
2. **It contains no data**, only descriptors of data hosted elsewhere
3. **It reports no numbers of its own.** Accuracies and BLEU scores live in the papers it cites;
   the survey summarises methods, not results
4. **It is not exhaustive**, and does not claim to be. It is a maintained community survey
5. **It has visible gaps** — `src/index.md` carries `TODO` markers and commented-out sections,
   including several under *Evaluation Metrics* and the notation-conversion tasks
6. **It covers no Southeast Asian sign language** — [`LTR_S6.2`](#62-what-is-not-there)
7. **It cannot substitute for reading a paper.** Every claim in this report tagged to `[S2]` is
   the survey's characterisation of work not read here

---





# 8. RUNNING IT
There is nothing to run, and no reason to build it — the rendered survey is public at
`sign-language-processing.github.io`.

Two things in the clone are worth consuming directly:

```bash
# The dataset registry, machine-readable
cat src/datasets/*.json

# The bibliography, for any citation the project needs
grep -A6 '@inproceedings{moryossef' src/references.bib
```

`src/references.bib` is 4,892 lines and is the fastest route to a correctly formatted citation for
anything in this field — which matters because
[`JCR_S4.4`](../../../plan/JCR_judging_criteria.md#44-five-pressure-test-questions) demands *"a
figure, a source, and a date"*.

Building the site requires **Pandoc**, per the README `[S1]`.

---





# 9. RELEVANCE TO SIMPLYNEXT
## 9.1. Lessons to Carry Across
| #   | Lesson                                                                                     |
| :-  | :----------------------------------------------------------------------------------------- |
| T1  | **No SgSL dataset exists.** The choice is *public ASL data* against *record it yourself*   |
| T2  | **The field's benchmarks are mostly non-commercial**, including PHOENIX-2014T              |
| T3  | **Split by signer, not at random**, or the reported number is signer-dependent             |
| T4  | **Simultaneity means a linear gloss sequence is structurally lossy** — say so              |
| T5  | **Directional verbs, classifiers and role shift are not in any fixed vocabulary**          |
| T6  | **Sign language detection is a solved, cheap, pose-based task** — per-joint flow norm      |
| T7  | **BIO beats IO** for segmentation labels; optical flow and 3D hand normalisation help      |
| T8  | ⚠ **Utterance boundaries may not correspond to MediaPipe articulatory features**           |
| T9  | **Train the text stage on noisy recogniser output**, not on gold glosses                   |
| T10 | **Pose is semi-anonymised; video is not**, because the face is linguistically necessary    |
| T11 | **If BLEU is used, use SacreBLEU with a published signature**, and compare nothing else    |

T8 is the uncomfortable one, and the reason it is in the table rather than in a footnote. A finding
that argues against the project's own design is exactly what
[`CLD_S5.1`](../../../CLAUDE.md#51-evidence) exists to preserve.




## 9.2. What the Project Takes
1. **The dataset facts** · *Take:* 49 datasets, 23 languages, no SgSL; PHOENIX-2014T is 9 signers
   and CC BY-NC-SA · *Where:*
   [`ARC_S9.1`](../../../plan/ARC_architecture.md#91-open-questions-for-the-team) questions 2 and 4
2. **The signer-split rule** · *Take:* No signer overlap between train and test ·
   *Where:* `EVL`; [`RSK_S4.2`](../../../plan/RSK_risk_register.md#42-model-and-evaluation)
3. **The task taxonomy** · *Take:* detection, segmentation, video-to-gloss, gloss-to-text ·
   *Where:* The architecture slide, using the field's own names
4. **The linguistic limits** · *Take:* Simultaneity, spatial reference, role shift, classifiers ·
   *Where:* [`RSK_S3.3`](../../../plan/RSK_risk_register.md#33-lexicon-and-reference); the
   limitations slide
5. **Pose-based sign detection** · *Take:* Per-joint optical-flow norm + a shallow model ·
   *Where:* [`ARC_S6.1`](../../../plan/ARC_architecture.md#61-pipeline) stage ④, as the named
   upgrade from geometry
6. **The segmentation counter-evidence** · *Take:* ⚠ Börstell 2024 ·
   *Where:* [`ARC_S9.1`](../../../plan/ARC_architecture.md#91-open-questions-for-the-team), a new
   question
7. **The noisy-gloss training result** · *Take:* Prompt the assembler on real classifier output ·
   *Where:* [`ARC_S6.1`](../../../plan/ARC_architecture.md#61-pipeline) stage ⑥
8. **The metric guidance** · *Take:* SacreBLEU with signatures; nDTW-MJE; SignBLEU ·
   *Where:* `EVL`
9. **The privacy framing** · *Take:* Pose is semi-anonymised; video anonymisation is unsolved
   because the face is linguistically necessary · *Where:*
   [`RSK_S8.3`](../../../plan/RSK_risk_register.md#83-privacy-and-data-protection)
10. **The bibliography** · *Take:* `src/references.bib` · *Where:* Every source section that needs
    a formatted citation




## 9.3. What the Project Does Not Take
1. **Any code.** There is none to take
2. **Any number, without opening the underlying paper.** The survey reports methods, not results
3. **Any claim as primary.** Everything from `src/index.md` is one step removed and marked so
4. **The `Deaf`/`deaf` convention, silently.** [`LTR_S3.5`](#35-a-terminology-note) — a team
   decision
5. **The datasets themselves.** [`LTR_S6.3`](#63-the-licence-pattern)

---





# 10. SOURCES
1. **`[S1]`**
   *Source:* `ref_repo/translation/signlang-literature/sign-language-processing.github.io/README.md`
   at `af5fb4a` — the project goal, the Pandoc build instructions and the citation block
   *Reliability:* Official project documentation
2. **`[S2]`**
   *Source:*
   `ref_repo/translation/signlang-literature/sign-language-processing.github.io/src/index.md` at
   `af5fb4a` — the introduction, the linguistics overview, the representations section, the
   detection, segmentation, pose-to-gloss, gloss-to-text, video-to-text and pose-to-text task
   sections, the evaluation-metrics section and the annotation-tools list. All quotations in
   [`LTR_S3`](#3-the-linguistics-that-constrain-the-product) through [`LTR_S5`](#5-what-the-survey-says-about-method)
   are verbatim from this file
   *Reliability:* ⚠ **Secondary.** A maintained community survey, CC BY 4.0, citable as Moryossef
   and Goldberg 2021. It characterises works that were **not read** for this review. Every
   attributed finding must be verified against its own paper before it appears on a slide as a
   number
3. **`[S3]`**
   *Source:* `.../sign-language-processing.github.io/LICENSE` — CC BY 4.0, © 2026 Nagish Inc.
   *Reliability:* Primary. ⚠ Read as an engineer, not a lawyer
4. **`[S4]`**
   *Source:* `.../sign-language-processing.github.io/src/datasets/*.json` — 49 descriptors,
   enumerated programmatically for this report; and a full-text search of `src/` for *Singapore*,
   *SgSL* and `sls`
   *Reliability:* Primary for the registry's contents; ⚠ **secondary** for the licence and count
   fields inside it, which are a community summary rather than the datasets' own terms
5. **`[S5]`**
   *Source:* The clone itself at `af5fb4a` (2026-08-11). Line counts and file counts were obtained
   by enumeration of the working tree
   *Reliability:* Primary

---





# 11. CHANGE LOG
1. **2026-09-04** · *Author:* Claude (Opus 5)
   *Change:* Created from a read of the README, the licence, and the introduction, linguistics,
   representations, detection, segmentation, pose-to-gloss, gloss-to-text, video-to-text,
   pose-to-text and evaluation-metrics sections of `src/index.md`, plus a programmatic enumeration
   of the 49-dataset registry. Recorded the absence of any Singapore Sign Language dataset and the
   predominantly non-commercial licensing of the field's benchmarks as the two findings that
   change [`ARC_S9.1`](../../../plan/ARC_architecture.md#91-open-questions-for-the-team); recorded
   the signer-overlap warning as a rule for `EVL`; and recorded Börstell 2024 as evidence
   **against** the geometric segmenter in
   [`ARC_S5.3`](../../../plan/ARC_architecture.md#53-recommended-approach), with its limits stated.
