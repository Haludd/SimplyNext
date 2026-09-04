**SIGN-LANGUAGE-TRANSLATOR — SYNTHESIS FOR SIMPLYNEXT**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field             | Value                                                                          |
| :---------------- | :----------------------------------------------------------------------------- |
| **Code**          | `STS`                                                                          |
| **Status**        | Live                                                                           |
| **Last reviewed** | 2026-09-04                                                                     |
| **Scope**         | Short orientation to `RST` and its Tasks-API pattern                           |
| **Subject**       | `RST` — `sign-translator/…-translator/` at `cca5f3a`                           |
| **Full report**   | [`STR`](../ref_repo/translation/sign-translator/STR_sign_translator_report.md) |

**For the team.** An **Apache 2.0 Python framework for building a translator for a sign language
that has no data** — the position the project is in if it chooses Singapore Sign Language. Two
things in it are directly useful: [`STS_S3`](#3-the-tasks-api-done-right) is the only working
example in `ref_repo/` of MediaPipe's **Tasks API** driving `PoseLandmarker` and `HandLandmarker`
together in `VIDEO` mode, and [`STS_S5`](#5-the-data-collection-protocol) is a written protocol for
recording a corpus from nothing. The complete analysis is in
[`STR`](../ref_repo/translation/sign-translator/STR_sign_translator_report.md), beside the clone in
`ref_repo/translation/sign-translator/`.

**For the assistant.** State plainly that **the sign-to-text direction is not implemented** —
`models/sign_to_text/` holds one empty file and the README marks the loader *"COMING SOON!"*. The
package name promises both directions and delivers one. It is also ⚠ the **least maintained** of
the three permissively-licensed candidates. Where this file and
[`STR`](../ref_repo/translation/sign-translator/STR_sign_translator_report.md) disagree, `STR` wins.

</details>

---





# 1. WHAT THIS IS
`sign_language_translator` — *"Build custom Translators and Translate between text and sign language
videos with AI"* — on PyPI, with ReadTheDocs documentation, a `slt` CLI and HuggingFace Spaces
demonstrations.

Its stated purpose is the relevant part:

> *"A big hurdle is the lack of datasets (global & regional) and frameworks that deep learning
> engineers and software developers can use to build useful products for the target community …
> It aims to facilitate the creation of sign language translators **for any region**."*

The sign language actually implemented is **Pakistan Sign Language**, with Urdu, Hindi and English
as source text languages. Everything else is a base class waiting to be subclassed.

**Licence: Apache 2.0** — the most permissive in `ref_repo/translation/`, and the same as `RMP`.
Version `0.8.1` at `cca5f3a`, **2024-09-23**. ⚠ **Dormant** — no commit for roughly two years.

It is solo-authored, carries **no publication** and reports **no evaluation** — a different
provenance from every other repository in this track, cutting both ways: cleaner engineering,
unrefereed claims.

---





# 2. WHAT IS AND IS NOT THERE
The architecture is two subclassable base classes and one model:

1. **`TextLanguage`** — tokenise, normalise, tag, and *disambiguate* the spoken side
2. **`SignLanguage`** — map tagged tokens to sign clips under that sign language's grammar
3. **`ConcatenativeSynthesis`** — *"tokenize, map, download & concatenate"*, emitting video or
   landmarks

Around it sit n-gram and transformer language models used not for translation but to **generate
spoken sentences composed only of dictionary words**, so synthetic parallel data exists before real
data does. The project has a cheaper version available: an LLM, prompted with the closed vocabulary.

> **Warning — the sign-to-text direction is not implemented.** `models/sign_to_text/` contains
> exactly one file, `__init__.py`, and it is empty. The README's own example marks it:
>
> ```python
> # # Load sign-to-text model (pytorch) (COMING SOON!)
> # translation_model = slt.get_model(slt.ModelCodes.Gesture)
> ```
>
> The README describes that direction as four steps; **step 1 — MediaPipe embedding — exists, and
> steps 2–4 are a plan.** This is not dishonesty, it is marked; but it is the difference between
> what the package name promises and what it delivers, and it must be stated wherever `RST` is
> described.

**The operational lesson: check what a repository contains against what its name claims.** It is
the counterpart to `RSA`'s licence lesson
([`SAS_S2`](SAS_sam_slr_synthesis.md#2-the-licence-contradiction)).

---





# 3. THE TASKS API, DONE RIGHT
This is the reason to keep the clone.

```python
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

Six things are right, measured against
[`ARC_S6.5`](../plan/ARC_architecture.md#65-perception-engineering-rules) and
[`MPS`](MPS_mediapipe_synthesis.md):

1. **`mediapipe.tasks.vision`, not `mp.solutions`** — rule 1. The **only** repository in `ref_repo/`
   that gets this right; `RSP` is on the legacy API
   ([`SPS_S4`](SPS_sign_pose_synthesis.md#4-the-one-thing-not-to-take)), `RSL` and `RSA` use HRNet
2. **`RunningMode.VIDEO`, not `IMAGE`** — rule 3. The tracking loop is enabled
3. **`.task` model assets loaded by path**, downloaded and cached by the package's asset manager
4. **`PoseLandmarker` and `HandLandmarker` separately** — decision 14's option (b) — which preserves
   multi-person capability that `HolisticLandmarker` does not have
5. **`output_segmentation_masks=False`** — matching
   [`ARC_S2.1`](../plan/ARC_architecture.md#21-verdict-confirmed-at-lower-cost-than-assumed)'s
   verdict that segmentation is cost without signal
6. **Both landmarkers created in one `with` block** and closed together

Three cautions:

1. **⚠ `pose_landmarker_heavy.task` is the slowest of the three variants.** Right for offline
   embedding; possibly not for a 30 fps live loop. **Measure `lite`/`full`/`heavy` rather than
   inheriting `heavy`.**
2. **`num_hands = number_of_persons * 2` walks into the detector pathology.** With `num_hands=2` and
   one hand visible, the palm detector runs on **every frame** —
   [`MPS_S6`](MPS_mediapipe_synthesis.md#6-the-four-traps-that-will-cost-a-day) and rule 4. Signers
   drop to one hand constantly. This code has no tolerance counter; `RDH`'s is the fix
   ([`DHS_S3.1`](DHS_depthai_synthesis.md)).
3. **Hands are not associated with people.** With more than one person the landmarker returns up to
   `2n` hands and nothing says whose they are — the hand-identity gap in rule 6, still the project's
   own work.

The embedding shape is `(-1, 75, 5)` — **75 landmarks** (33 pose + 21 + 21), five values each, with
`landmark_type` selecting `"world"`, `"image"` or `"all"`.

> **This settles the mechanics of
> [`ARC_S9`](../plan/ARC_architecture.md#9-decisions) decision 14 option (b), leaving only the
> measurement.** It is Apache 2.0, so it may be read, adapted and attributed.

---





# 4. THE WORD-SENSE GAP
The README is explicit about the cost of the rule-based route:

> *"It is faster but the **word sense has to be disambiguated** in the input. See the deep learning
> approach to automatically handle ambiguous words & **words not in dictionary**."*

with the example `"spring" -> ["spring(water-spring)", "spring(metal-coil)"]`.

> **This is a gap in the project's reverse direction that neither `RSS` nor
> [`ARC`](../plan/ARC_architecture.md) currently names.** A lexicon is indexed by written word; a
> written word may have two meanings with two different signs; a lookup returns whichever the index
> holds. `RSS` handles the *missing* word by fingerspelling it
> ([`SSS_S4`](SSS_spoken_to_signed_synthesis.md#4-the-coverage-ladder)) but not the *ambiguous*
> one — its candidate generation normalises spelling, not sense.
>
> **The project's answer is cheap and already in the architecture: the agent disambiguates.** The
> LLM at stage ⑥ has the conversation context, and word-sense disambiguation given context is
> something it does well. Lexicon keys become `word + sense`, and the glosser is asked for the
> sense.

---





# 5. THE DATA-COLLECTION PROTOCOL
The README's *Datasets* section is a written protocol for building a corpus for a sign language that
has none — the most actionable content in the repository if SgSL is chosen.

**What the data should include:**

1. A **word-level dictionary** — videos of individual signs with their text tokens
2. **Replications** — *"multiple syncronized cameras and record random people performing the
   dictionary videos"* — sic
3. **Parallel sentences**, in four forms
4. **Grammatical rules**: word order (*"e.g. SUBJECT OBJECT VERB TIME"*), meaningless words
   (*"the, am, are"*), ambiguous words

**What to incorporate:** multiple camera angles; *"Diverse performers to capture all **accents** of
the signs"*; unique token labelling; *"Variations in signs for the same concept"*.

Four of these change what `EVL` should say:

1. **"Diverse performers to capture all accents" is the signer-generalisation problem as a recording
   instruction** — the same finding
   [`LTS_S3.1`](LTS_signlang_literature_synthesis.md#31-split-by-signer-not-at-random) reports as
   something to measure. **Record more people, fewer repetitions each**, and hold out whole signers
2. **Variations for the same concept are what a closed vocabulary hides.** Two signers may sign the
   same concept differently and both be correct. One canonical clip per gloss produces a classifier
   that rejects the second signer
3. **Writing the grammar down is a deliverable the project can produce.** Word order, dropped
   function words and ambiguous words is *linguistic* work, not engineering — and the natural
   artefact of consulting a deaf reviewer
   ([`ARC_S7.6`](../plan/ARC_architecture.md#76-p6--gloves-rejected-on-the-record))
4. **Separating the *dictionary* from the *replications*** is the same distinction `RSS` makes
   between citation form and fluent signing
   ([`SSS_S6`](SSS_spoken_to_signed_synthesis.md#6-the-number-that-changes-data-collection))

> **Note — the protocol assumes multiple synchronised cameras, which the project will not have.**
> One camera, several people, several repetitions, and a signer-held-out split is the achievable
> subset.

---





# 6. THE EIGHT LESSONS
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

---





# 7. WHAT IT DOES NOT DO
1. **It does not translate sign to text** — [`STS_S2`](#2-what-is-and-is-not-there)
2. **It implements one sign language**, Pakistan Sign Language
3. **It does not segment or detect signing**
4. **It has no published evaluation** — no paper, no benchmark, no accuracy claims
5. **It does not handle handedness, hand identity or tracking state**
6. **It does not use the `.pose` format**, so it does not interoperate with `RSP` or `RSS` without
   conversion
7. **It is not currently maintained** — no commit since 2024-09

---





# 8. RUNNING IT
It installs and runs today:

```bash
pip install "sign-language-translator[mediapipe]"   # torch 2.2, opencv, mediapipe 0.10.9
```

```python
import sign_language_translator as slt
model = slt.models.ConcatenativeSynthesis(
    text_language="english", sign_language="pk-sl", sign_format="video")
sign = model.translate("This is an apple.")
```

> **Warning — running the translator downloads Pakistan Sign Language assets.** That is a network
> dependency and a licence question about the sign *data*, separate from the Apache 2.0 code
> licence — the same distinction recorded for `RSS`.

**What the project actually does with it:** reads [`STS_S3`](#3-the-tasks-api-done-right) as the
Tasks-API template, adapts it with attribution, adds the tolerance counter and hand identity `RDH`
supplies, and takes [`STS_S5`](#5-the-data-collection-protocol) into `EVL`. It does **not** adopt
the package as a dependency — `RSP` and `RSS` cover the data structures and the reverse direction
better, are better maintained, and interoperate with each other.

---





# 9. WHERE TO GO NEXT
1. **Full breakdown** —
   [`STR`](../ref_repo/translation/sign-translator/STR_sign_translator_report.md)
2. **Why the legacy API is banned** — [`MPS_S6`](MPS_mediapipe_synthesis.md)
3. **The detector pathology it hits** — [`DHS_S3.1`](DHS_depthai_synthesis.md)
4. **The library to prefer** — [`SPS`](SPS_sign_pose_synthesis.md)
5. **The reverse direction, finished** — [`SSS`](SSS_spoken_to_signed_synthesis.md)
6. **The data question** — [`ARC_S9.1`](../plan/ARC_architecture.md)
7. **Where every document lives** — [`RIX`](../ref_index.md)

---





# 10. CHANGE LOG
1. **2026-09-04** · *Author:* Claude (Opus 5)
   *Change:* Created alongside
   [`STR`](../ref_repo/translation/sign-translator/STR_sign_translator_report.md), from a read of
   the README, the licence, `pyproject.toml`, the MediaPipe landmarks model, the module tree and
   the `sign_to_text` package.
