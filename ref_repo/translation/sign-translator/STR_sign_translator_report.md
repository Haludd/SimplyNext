**SIGN-LANGUAGE-TRANSLATOR — FULL REPOSITORY REPORT**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field                   | Value                                                    |
| :---------------------- | :------------------------------------------------------- |
| **Code**                | `STR`                                                    |
| **Status**              | Live                                                     |
| **Last reviewed**       | 2026-09-04                                               |
| **Source of truth for** | Analysis of the sign-language-translator reference clone |
| **Parent**              | [`RIX_S2.1`](../../../ref_index.md#21-live-documents)    |
| **Short version**       | [`STS`](../../../doc/STS_sign_translator_synthesis.md)   |
| **Subject**             | `RST` — `sign-translator/…-translator/` at `cca5f3a`     |

**For the team.** `sign-language-translator` is an **Apache 2.0 Python framework for building a
translator for a sign language that has no data** — which is exactly the position the project is in
if it chooses Singapore Sign Language. Two things in it are directly useful.
[`STR_S5`](#5-the-mediapipe-tasks-reference-implementation) is the only working example in
`ref_repo/` of MediaPipe's **Tasks API** driving `PoseLandmarker` and `HandLandmarker` together in
`VIDEO` mode — the configuration
[`ARC_S9`](../../../plan/ARC_architecture.md#9-decisions) decision 14 calls option (b).
[`STR_S6`](#6-the-data-collection-protocol) is a written protocol for recording a sign language
corpus from nothing.

**For the assistant.** State plainly that **the sign-to-text direction is not implemented** —
`models/sign_to_text/` contains one empty file and the README marks the loader *"COMING SOON!"*
([`STR_S4.3`](#43-what-is-not-there)). The repository's name promises both directions and it
delivers one. It is also ⚠ **the least maintained of the three permissively-licensed candidates**,
with no commit since 2024-09. Nothing inside
`ref_repo/translation/sign-translator/sign-language-translator/` may be edited; it is an unmodified
clone, excluded from version control.

</details>

---





# 1. EXECUTIVE SUMMARY
## 1.1. What This Repository Is
`ref_repo/translation/sign-translator/sign-language-translator/` is the `sign_language_translator`
Python package — *"Build custom Translators and Translate between text and sign language videos
with AI"*, in its own words `[S1]`. It is on PyPI, has ReadTheDocs documentation, codecov
integration, and HuggingFace Spaces demonstrations.

Its stated purpose is unusual and directly relevant:

> *"A big hurdle is the lack of datasets (global & regional) and frameworks that deep learning
> engineers and software developers can use to build useful products for the target community. This
> project aims to empower sign language translation by providing robust components, tools, datasets
> and models for both sign language to text and text to sign language conversion. It aims to
> facilitate the creation of sign language translators **for any region**"* `[S1]`

The concrete sign language implemented is **Pakistan Sign Language** (`pk-sl`), with Urdu, Hindi
and English as source text languages. Everything else is a base class waiting to be subclassed.

It is a solo-authored project — Mudassar Iqbal — rather than an academic group's artefact, and it
carries no publication. That is a different provenance from every other repository in
`ref_repo/translation/`, and it cuts both ways: the engineering is cleaner and the claims are
unrefereed.




## 1.2. Why It Matters to SimplyNext
1. **It is the Tasks-API reference implementation** · *Use:* `MediaPipeLandmarksModel` instantiates
   `mediapipe.tasks.vision.PoseLandmarker` and `HandLandmarker` with `RunningMode.VIDEO` and
   `.task` model assets. That is
   [`ARC_S6.5`](../../../plan/ARC_architecture.md#65-perception-engineering-rules) rules 1 and 3 in
   working code, and the **only** such example in `ref_repo/` — every other repository here is on
   the legacy API or on HRNet — [`STR_S5`](#5-the-mediapipe-tasks-reference-implementation)
2. **It is built for the project's data situation** · *Use:* The whole design assumes no dataset
   exists and a rule-based system must bootstrap one. Its data-collection protocol is a written
   answer to [`ARC_S9.1`](../../../plan/ARC_architecture.md#91-open-questions-for-the-team)
   question 4 — [`STR_S6`](#6-the-data-collection-protocol)
3. **It names the word-sense problem explicitly** · *Use:* `spring` → `spring(water-spring)` /
   `spring(metal-coil)`. The reverse direction of the product hits this on the first ambiguous word
   and neither `RSS` nor `ARC` currently addresses it —
   [`STR_S4.2`](#42-the-stated-limitation)
4. **It is Apache 2.0** · *Use:* The most permissive licence in `ref_repo/translation/`, and one of
   only three the project could ship — [`STR_S2.2`](#22-licence)
5. **It is a cautionary example** · *Use:* A well-engineered package whose headline capability is
   absent. [`STR_S4.3`](#43-what-is-not-there) is a reminder to check what a repository *contains*
   against what it *claims*

Against the four MVP steps in [`SCR`](../../../plan/scribbles.md):

1. **1. Isolate the subject** — not addressed
2. **2. Track many points** — **yes**, and correctly:
   [`STR_S5`](#5-the-mediapipe-tasks-reference-implementation)
3. **3. Points → skeleton** — a `Landmarks` container with named connection sets, and pose
   transformations for augmentation. Lighter than `RSP`
4. **4. Skeleton → conversational text** — **not implemented** —
   [`STR_S4.3`](#43-what-is-not-there)




## 1.3. Summary
The architecture is a rule-based text-to-sign translator with pluggable language definitions.
`TextLanguage` subclasses handle tokenisation, normalisation, tagging and word-sense
disambiguation for a spoken language; `SignLanguage` subclasses map tagged tokens to sign clips
under a named sign language's grammar; `ConcatenativeSynthesis` joins the two and emits either
video or landmarks. Around that sit n-gram and transformer language models — used not for
translation but to *generate* sentences composed only of dictionary words, so that synthetic
parallel data can be produced before any real data exists. The sign-to-text direction is described
in the README as four steps, of which the first — MediaPipe embedding — is built and the rest are
not.

---





# 2. PROVENANCE, LICENCE AND REQUIREMENTS
## 2.1. Provenance
1. **Publisher**
   Mudassar Iqbal, under the `sign-language-translator` GitHub organisation. Remote:
   `https://github.com/sign-language-translator/sign-language-translator.git`
2. **Clone state**
   `cca5f3a`, **2024-09-23**, *"PR #50 - English Language Support"*
3. **Version**
   `0.8.1`, declared in `pyproject.toml` `[S2]`
4. **Maintenance status**
   ⚠ **Dormant.** No commit for roughly two years before this review. It is not abandoned in the
   way `RSA` is — the last change was a feature — but it is not the actively maintained package
   `RSP` is
5. **Scale**
   2.1 MB, one Poetry-managed package, `tests/` present, ReadTheDocs configured
6. **Distribution**
   `pip install sign-language-translator`; a `slt` CLI; HuggingFace Spaces demonstrations




## 2.2. Licence
`LICENSE`: **Apache License, Version 2.0**, confirmed by `pyproject.toml`'s `license = "Apache-2.0"`
`[S2]` `[S3]`.

Apache 2.0 permits commercial use, modification, distribution and patent use, requiring the licence
and notice to be preserved and changed files to be marked. It additionally grants an express patent
licence, which neither MIT nor CC BY does.

> **Note — this is the most permissive licence in `ref_repo/translation/`**, and the same licence
> as `RMP`. The three shippable repositories in this track are `RSP` (MIT), `RSS` (MIT) and `RST`
> (Apache 2.0). `RSL` (no licence), `RSA` (non-commercial) and `RLT` (a document) are not
> shippable code.




## 2.3. Requirements
`pyproject.toml` `[S2]`:

```toml
python = ">=3.8,<3.13"
torch = "==2.2.*"
numpy = "==1.26.*"
opencv-contrib-python = "^4.8.0.74"
matplotlib = "^3.7.4"
tqdm, click, requests
mediapipe = { version = "0.10.9", optional = true, python = ">=3.8,<=3.11" }
```

Two observations:

1. **`torch==2.2.*` is a 2024 stack, not a 2021 one.** Against `RSL`'s `torch==1.9.0+cu102`, this
   is installable today. But it is still a **pinned major-minor**, and PyTorch is a heavy
   dependency for a project whose classifier may not need it
2. **⚠ `mediapipe = "0.10.9"` is pinned exactly, and it is a 2024 release.** This does **not**
   have the same cause as `RSP`'s `mediapipe<0.10.30` cap
   ([`SPR_S6`](../sign-pose/SPR_sign_pose_report.md#6-the-mediapipe-collision)) — the code is on
   the Tasks API, which the 1.0 line keeps. It is an ordinary stale pin. The project pins its own
   MediaPipe version per
   [`ARC_S6.5`](../../../plan/ARC_architecture.md#65-perception-engineering-rules) rule 2 and does
   not inherit this one

MediaPipe is **optional**, behind the `mediapipe`, `full` or `all` extras.

---





# 3. REPOSITORY MAP
```text
ref_repo/translation/sign-translator/
├── STR_sign_translator_report.md              — this document (tracked in git)
└── sign-language-translator/                  — the clone (git-ignored)
    ├── sign_language_translator/
    │   ├── languages/
    │   │   ├── text/    english.py, urdu.py, hindi.py, text_language.py
    │   │   ├── sign/    pakistan_sign_language.py, sign_language.py, mapping_rules.py
    │   │   └── vocab.py
    │   ├── models/
    │   │   ├── text_to_sign/concatenative_synthesis.py   ← the core model
    │   │   ├── video_embedding/mediapipe_landmarks_model.py ← the Tasks API example
    │   │   ├── language_models/   n-gram, mixer, beam sampling, transformer
    │   │   ├── text_embedding/    vector lookup
    │   │   └── sign_to_text/      ← EMPTY. One file, no content
    │   ├── vision/
    │   │   ├── landmarks/  landmarks.py, connections.py, display.py
    │   │   ├── video/      video.py, video_iterators.py, transformations.py
    │   │   └── sign/       sign.py, transformations.py
    │   ├── config/assets.py     asset download manager
    │   └── cli.py               the `slt` command
    ├── tests/
    └── LICENSE                  Apache 2.0
```

**Worth reading:** `models/video_embedding/mediapipe_landmarks_model.py:60-140` (the Tasks API
configuration), `models/text_to_sign/concatenative_synthesis.py`, `languages/sign/sign_language.py`
and `languages/text/text_language.py` (the two base classes a new sign language subclasses), and
the *Datasets* section of `README.md`.

**Not worth reading:** `models/language_models/` (n-gram models for synthetic sentence generation —
a solved problem the project does not have), and the Urdu and Hindi language modules.

---





# 4. THE ARCHITECTURE
## 4.1. Two Base Classes and a Model
The extensibility story is stated in the README as a tip `[S1]`:

> *"To create a rule-based translation system for your regional language, you can inherit the
> TextLanguage and SignLanguage classes and pass them as arguments to the ConcatenativeSynthesis
> class."*

1. **`TextLanguage`** — for the spoken side: *"Normalize text input by substituting unknown
   characters/spellings with supported words"*, *"Disambiguate context-dependent words"*,
   *"Tokenize text (word & sentence level)"*, *"Classify tokens and mark them with Tags"* `[S1]`
2. **`SignLanguage`** — for the signed side: map tagged tokens to sign clips under that sign
   language's grammar, via `mapping_rules.py`
3. **`ConcatenativeSynthesis`** — *"tokenize, map, download & concatenate"* `[S1]`, emitting either
   `video` or `LANDMARKS`

> **Note — this is the same architecture as `RSS`, factored differently.**
> [`SSR_S3`](../spoken-to-signed/SSR_spoken_to_signed_report.md#3-the-three-stage-pipeline)
> separates glosser, lookup and concatenator as three pipeline stages chosen by flag; `RST`
> separates *the spoken language* from *the sign language* as two subclassable objects. `RSS`'s
> factoring is better for swapping *algorithms*; `RST`'s is better for adding a *new language*.
> The project needs the second only if it commits to SgSL, and even then `RSS`'s lexicon-plus-
> fingerspelling design covers most of it.

**The language models earn a mention.** `models/language_models/` holds n-gram models, a mixer, beam
sampling and a transformer, used *"to write sample texts of supported words"* `[S1]` — that is,
to generate spoken-language sentences composed **only of words the dictionary can sign**, so that
synthetic parallel data exists before any real data does. It is a neat solution to a real
bootstrap problem, and the project has a cheaper version of it available: an LLM, prompted with the
closed vocabulary, generating in-vocabulary sentences for testing.




## 4.2. The Stated Limitation
The README is explicit about the cost of the rule-based route `[S1]`:

> *"It is faster but the **word sense has to be disambiguated** in the input. See the deep learning
> approach to automatically handle ambiguous words & **words not in dictionary**."*

and gives the example `"spring" -> ["spring(water-spring)", "spring(metal-coil)"]`.

> **This is a gap in the project's reverse direction that neither `RSS` nor
> [`ARC`](../../../plan/ARC_architecture.md) currently names.** A lexicon is indexed by written
> word; a written word may have two meanings with two different signs; a lookup returns whichever
> the index holds. `RSS` handles the *missing* word (fingerspell it) but not the *ambiguous* one —
> its `gloss_candidates` normalises spelling, not sense
> ([`SSR_S6`](../spoken-to-signed/SSR_spoken_to_signed_report.md#6-the-coverage-ladder--the-most-transferable-idea-here)).
>
> The project's answer is cheap and already in the architecture: **the agent disambiguates.** The
> LLM at stage ⑥ has the conversation context, and word-sense disambiguation given context is
> something it does well. The lexicon entry becomes `word + sense`, and the glosser is asked for
> the sense. Recorded for [`ARC_S6.1`](../../../plan/ARC_architecture.md#61-pipeline).




## 4.3. What Is Not There
> **Warning — the sign-to-text direction is not implemented.** `models/sign_to_text/` contains
> exactly one file, `__init__.py`, and it is empty `[S5]`. The README's own Python example marks
> it `[S1]`:
>
> ```python
> # # Load sign-to-text model (pytorch) (COMING SOON!)
> # translation_model = slt.get_model(slt.ModelCodes.Gesture)
> # text = translation_model.translate(embedding)
> ```

The README describes the sign-to-text direction as four steps: extract features with MediaPipe;
transcribe and translate into multiple text languages; use synthetic concatenated data for the
gloss-writing task; *"Fine-tune a neural network, such as one from `slt.models.sign_to_text` or the
encoder of any multilingual seq2seq model, on your dataset"* `[S1]`. **Step 1 exists. Steps 2–4 are
a plan.**

This is not dishonesty — the README marks it — but it is the difference between what the package
name promises and what it delivers, and it must be stated wherever `RST` is described. The
practical effect: `RST` contributes to the project's **forward** direction only through
[`STR_S5`](#5-the-mediapipe-tasks-reference-implementation) and
[`STR_S6`](#6-the-data-collection-protocol), not as a model.

---





# 5. THE MEDIAPIPE TASKS REFERENCE IMPLEMENTATION
This is the most immediately useful code in the repository, and the reason to keep the clone.

`models/video_embedding/mediapipe_landmarks_model.py:60-140` `[S4]`:

```python
pose_model_name="pose_landmarker_heavy.task",
hand_model_name="hand_landmarker.task",
number_of_persons: int = 1,
...
self._pose_class = mediapipe.tasks.vision.PoseLandmarker
self._hand_class = mediapipe.tasks.vision.HandLandmarker

self._pose_options = mediapipe.tasks.vision.PoseLandmarkerOptions(
    base_options=mediapipe.tasks.BaseOptions(model_asset_path=path),
    running_mode=mediapipe.tasks.vision.RunningMode.VIDEO,
    output_segmentation_masks=False,
    num_poses=number_of_persons,
)
self._hand_options = mediapipe.tasks.vision.HandLandmarkerOptions(
    base_options=mediapipe.tasks.BaseOptions(model_asset_path=path),
    running_mode=mediapipe.tasks.vision.RunningMode.VIDEO,
    num_hands=number_of_persons * 2,
)
```

Six things are right here, measured against
[`ARC_S6.5`](../../../plan/ARC_architecture.md#65-perception-engineering-rules) and
[`MPS`](../../../doc/MPS_mediapipe_synthesis.md):

1. **`mediapipe.tasks.vision`, not `mp.solutions`** — rule 1. The only repository in `ref_repo/`
   that gets this right; `RSP` is on the legacy API
   ([`SPR_S6`](../sign-pose/SPR_sign_pose_report.md#6-the-mediapipe-collision)), and `RSL`, `RSA`
   use HRNet
2. **`RunningMode.VIDEO`, not `IMAGE`** — rule 3. The tracking loop is enabled
3. **`.task` model assets loaded by path** via `BaseOptions(model_asset_path=...)`, downloaded and
   cached by the package's own asset manager
4. **`PoseLandmarker` and `HandLandmarker` run separately**, which is
   [`ARC_S9`](../../../plan/ARC_architecture.md#9-decisions) decision 14's option (b) — and it
   preserves multi-person capability, which `HolisticLandmarker` does not
5. **`output_segmentation_masks=False`** — segmentation is off, matching
   [`ARC_S2.1`](../../../plan/ARC_architecture.md#21-verdict-confirmed-at-lower-cost-than-assumed)'s
   verdict that segmentation is cost without signal
6. **Both landmarkers are created inside one `with` block** and closed together, so the native
   resources are released deterministically

Three cautions:

1. **⚠ `pose_landmarker_heavy.task` is the slowest of the three pose variants.** For offline
   embedding of a dataset that is the right default; for a 30 fps live loop it may not be. The
   project measures `lite` / `full` / `heavy` rather than inheriting `heavy`
2. **`num_hands = number_of_persons * 2` walks straight into the detector pathology.** With
   `num_hands=2` and one hand visible, MediaPipe's palm detector runs on **every frame** —
   [`MPR_S4.4.2`](../../tracking/google-mediapipe/MPR_mediapipe_report.md#442-the-num_hands--2-pathology)
   and [`ARC_S6.5`](../../../plan/ARC_architecture.md#65-perception-engineering-rules) rule 4.
   Signers drop to one hand constantly. This code has no tolerance counter, and `RDH`'s is the fix
   ([`DHS_S3.1`](../../../doc/DHS_depthai_synthesis.md))
3. **Hands are not associated with people.** With `number_of_persons > 1` the hand landmarker
   returns up to `2n` hands and nothing says which belongs to whom — the hand-identity gap in
   [`ARC_S6.5`](../../../plan/ARC_architecture.md#65-perception-engineering-rules) rule 6, still
   the project's own work

The embedding shape is worth recording: the README reshapes to `(-1, 75, 5)` `[S1]` — **75
landmarks** (33 pose + 21 + 21) with **five values each**, and `landmark_type` selects `"world"`,
`"image"` or `"all"`.

> **Decision consequence.** This file is the concrete answer to *"what does correct Tasks-API
> setup look like?"*, and it is Apache 2.0, so it may be read, adapted and attributed. It settles
> the mechanics of decision 14 option (b), leaving only the measurement —
> [`ARC_S7.2`](../../../plan/ARC_architecture.md#72-the-four-reference-repositories-compared).

---





# 6. THE DATA-COLLECTION PROTOCOL
The README's *Datasets* section is a written protocol for building a corpus for a sign language
that has none `[S1]`. It is the most directly actionable content in the repository for a project
that may choose SgSL.

**What the data should include:**

1. **A word-level dictionary** — *"Videos of individual signs & corresponding Text tokens (words &
   phrases)"*
2. **Replications of the dictionary** — *"Set up multiple syncronized cameras and record random
   people performing the dictionary videos"* — sic
3. **Parallel sentences**, in four forms: text against sign video; text against text gloss; sign
   video against gloss; and sign sentences against translations in multiple text languages
4. **Grammatical rules of the sign language**, explicitly enumerated:
   1. *"Word order (e.g. SUBJECT OBJECT VERB TIME)"*
   2. *"Meaningless words (e.g. 'the', 'am', 'are')"*
   3. *"Ambiguous words (e.g. spring(coil) & spring(water-fountain))"*

**What to incorporate:**

1. *"Multiple camera angles"*
2. *"Diverse performers to capture all **accents** of the signs"*
3. *"Uniqueness in labeling of word tokens"*
4. *"Variations in signs for the same concept"*

Four of these change what `EVL` should say:

1. **Item 2 of the second list is the signer-generalisation problem as a recording instruction.**
   *"Diverse performers to capture all accents"* is the same finding
   [`LTR_S4.1`](../signlang-literature/LTR_signlang_literature_report.md#41-sign-language-detection)
   reports from Pal et al. 2023 — performance drops for signers not seen in training — stated as
   something to do rather than something to measure. **Record more people, fewer repetitions each**,
   and hold out whole signers for the test split
2. **Item 4 of the second list — variations for the same concept — is the thing a closed vocabulary
   hides.** Two signers may sign the same concept differently and both be correct. A single
   canonical clip per gloss will produce a classifier that rejects the second signer
3. **Item 4 of the first list is a deliverable the project can actually produce.** Writing down a
   sign language's word order, function-word drops and ambiguous words is *linguistic* work, not
   engineering, and it is what makes a rule-based glosser possible at all. It is also the natural
   artefact of consulting a deaf reviewer —
   [`ARC_S7.6`](../../../plan/ARC_architecture.md#76-p6--gloves-rejected-on-the-record)
4. **Item 2 of the first list — recording *replications* separately from the *dictionary*** — is
   the same distinction `RSS` makes between citation form and fluent signing
   ([`SSR_S5.4`](../spoken-to-signed/SSR_spoken_to_signed_report.md#54-duration-and-a-number-the-project-needs)).
   The dictionary is the reference; the replications are the training data

> **Note — the protocol assumes multiple synchronised cameras, and the project will not have
> them.** One camera, several people, several repetitions, and a signer-held-out split is the
> achievable subset. Recorded for `EVL`.

---





# 7. WHAT THE REPOSITORY DOES NOT DO
1. **It does not translate sign to text** — [`STR_S4.3`](#43-what-is-not-there)
2. **It implements one sign language**, Pakistan Sign Language. Everything else is a base class
3. **It does not segment or detect signing.** No boundaries, no activity detection
4. **It has no published evaluation.** No paper, no benchmark numbers, no accuracy claims
5. **It does not handle handedness, hand identity or tracking state** — the gaps in
   [`STR_S5`](#5-the-mediapipe-tasks-reference-implementation)
6. **It does not use the `.pose` format.** It has its own `Landmarks` container, so it does not
   interoperate with `RSP` or `RSS` without conversion
7. **It is not currently maintained** — no commit since 2024-09

---





# 8. RUNNING IT
It installs and runs today:

```bash
pip install sign-language-translator            # torch 2.2, opencv, numpy
pip install "sign-language-translator[mediapipe]"   # adds mediapipe 0.10.9
```

```python
import sign_language_translator as slt

model = slt.models.ConcatenativeSynthesis(
    text_language="english", sign_language="pk-sl", sign_format="video")
sign = model.translate("This is an apple.")
```

and a `slt` CLI exposes `assets`, `complete`, `embed` and translation commands `[S1]`.

> **Warning — running the translator downloads Pakistan Sign Language assets** through
> `config/assets.py`. That is a network dependency and a licence question about the sign data
> itself, separate from the Apache 2.0 code licence — the same distinction recorded for `RSS` in
> [`SSR_S2.2`](../spoken-to-signed/SSR_spoken_to_signed_report.md#22-licence).

**What the project actually does with it:** reads
[`STR_S5`](#5-the-mediapipe-tasks-reference-implementation) as the Tasks-API template, adapts it
with attribution under Apache 2.0, adds the tolerance counter and hand identity `RDH` supplies, and
takes [`STR_S6`](#6-the-data-collection-protocol) into `EVL`. It does **not** adopt the package as
a dependency — `RSP` and `RSS` cover the data structures and the reverse direction better, are
better maintained, and interoperate with each other.

---





# 9. RELEVANCE TO SIMPLYNEXT
## 9.1. Lessons to Carry Across
| #  | Lesson                                                                                      |
| :- | :-----------------------------------------------------------------------------------------  |
| G1 | **`tasks.vision` + `RunningMode.VIDEO` + a `.task` asset** is the correct MediaPipe setup   |
| G2 | **`PoseLandmarker` + `HandLandmarker` separately keeps multi-person open**                  |
| G3 | **`num_hands = 2` without a tolerance counter re-runs the palm detector every frame**       |
| G4 | **Record diverse performers, not many takes** — signer variation is the generalisation axis |
| G5 | **Write the grammar down**: word order, dropped function words, ambiguous words             |
| G6 | **Word sense must be resolved before a lexicon lookup**, or the wrong sign is emitted       |
| G7 | **A language model can generate in-vocabulary sentences** to bootstrap parallel data        |
| G8 | **Check what a repository contains against what its name claims**                           |

G8 is the operational lesson, and it is the counterpart to `RSA`'s licence lesson: a repository
called `sign-language-translator` implements one direction of translation.




## 9.2. What the Project Takes
1. **The Tasks-API configuration** · *Take:* `PoseLandmarkerOptions` / `HandLandmarkerOptions` in
   `VIDEO` mode, adapted with Apache 2.0 attribution ·
   *Where:* [`ARC_S6.1`](../../../plan/ARC_architecture.md#61-pipeline) stage ②;
   [`ARC_S9`](../../../plan/ARC_architecture.md#9-decisions) decision 14 option (b)
2. **The model-variant caution** · *Take:* Measure `lite`/`full`/`heavy`, do not inherit `heavy` ·
   *Where:* The decision-14 measurement
3. **The data-collection protocol** · *Take:* Dictionary + replications; diverse performers;
   variations per concept · *Where:* `EVL`
4. **The grammar artefact** · *Take:* Word order, dropped words, ambiguous words, written down ·
   *Where:* `EVL`, and the deaf-reviewer session in
   [`ARC_S7.6`](../../../plan/ARC_architecture.md#76-p6--gloves-rejected-on-the-record)
5. **The word-sense problem** · *Take:* Lexicon keys are `word + sense`; the agent disambiguates ·
   *Where:* [`ARC_S6.1`](../../../plan/ARC_architecture.md#61-pipeline), the reverse direction
6. **The synthetic-sentence idea** · *Take:* Generate in-vocabulary test sentences with the LLM ·
   *Where:* `EVL` test-set construction




## 9.3. What the Project Does Not Take
1. **The package as a dependency.** `RSP` and `RSS` are better maintained and interoperate
2. **`ConcatenativeSynthesis`.** `RSS` does the same job with `.pose` output and per-token coverage
3. **`torch==2.2.*` as a transitive pin.** The project chooses its own tensor stack
4. **`mediapipe = 0.10.9`.** The project pins its own current version — rule 2
5. **Its `Landmarks` container.** `.pose` is the interchange format —
   [`SPR_S4`](../sign-pose/SPR_sign_pose_report.md#4-the-data-model)
6. **Pakistan Sign Language assets**, or any claim of multi-language support the project has not
   verified

---





# 10. SOURCES
1. **`[S1]`**
   *Source:*
   `ref_repo/translation/sign-translator/sign-language-translator/README.md` at `cca5f3a` — the
   overview and solution statement, the major-components lists for both directions, the language-
   processing and datasets sections, the installation and Python usage examples including the
   `COMING SOON!` comment, and the `slt` CLI listing
   *Reliability:* Official project documentation. ⚠ **Unrefereed** — this repository carries no
   publication and reports no evaluation
2. **`[S2]`**
   *Source:* `.../sign-language-translator/pyproject.toml` — version `0.8.1`, `license =
   "Apache-2.0"`, the dependency block and the extras
   *Reliability:* Primary — read from the clone
3. **`[S3]`**
   *Source:* `.../sign-language-translator/LICENSE` — Apache License 2.0
   *Reliability:* Primary. ⚠ Read as an engineer, not a lawyer
4. **`[S4]`**
   *Source:*
   `.../sign_language_translator/models/video_embedding/mediapipe_landmarks_model.py:60-140` — the
   `PoseLandmarker` and `HandLandmarker` construction, running mode, and options
   *Reliability:* Primary — read from the clone
5. **`[S5]`**
   *Source:* `.../sign_language_translator/models/sign_to_text/` — enumerated from the working
   tree; one file, `__init__.py`, empty
   *Reliability:* Primary
6. **`[S6]`**
   *Source:* The clone itself at `cca5f3a` (2024-09-23). All `file:line` citations resolve against
   this commit
   *Reliability:* Primary

---





# 11. CHANGE LOG
1. **2026-09-04** · *Author:* Claude (Opus 5)
   *Change:* Created from a read of the README, the licence, `pyproject.toml`, the MediaPipe
   landmarks model, the module tree and the `sign_to_text` package. Recorded `RST` as the only
   working MediaPipe **Tasks API** example in `ref_repo/`, settling the mechanics of
   [`ARC_S9`](../../../plan/ARC_architecture.md#9-decisions) decision 14 option (b); recorded its
   data-collection protocol as a written answer to
   [`ARC_S9.1`](../../../plan/ARC_architecture.md#91-open-questions-for-the-team) question 4;
   recorded the word-sense-disambiguation gap that neither `RSS` nor `ARC` addresses; and recorded
   that the sign-to-text direction the package name promises is **not implemented**.
