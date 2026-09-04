**SPOKEN-TO-SIGNED — FULL REPOSITORY REPORT**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field                   | Value                                                   |
| :---------------------- | :------------------------------------------------------ |
| **Code**                | `SSR`                                                   |
| **Status**              | Live                                                    |
| **Last reviewed**       | 2026-09-04                                              |
| **Source of truth for** | Analysis of the spoken-to-signed reference clone        |
| **Parent**              | [`RIX_S2.1`](../../../ref_index.md#21-live-documents)   |
| **Short version**       | [`SSS`](../../../doc/SSS_spoken_to_signed_synthesis.md) |
| **Subject**             | `RSS` — `spoken-to-signed/…-translation/` at `259aacd`  |

**For the team.** `ZurichNLP/spoken-to-signed-translation` is the **reverse direction of the
product, already built**: MIT, `pip install spoken-to-signed`, CPU-only, published at AT4SSL 2023,
and deployed behind the live `sign.mt` service. It is the answer to the second half of *both-way
translation*. Two of its design decisions matter beyond their own direction:
[`SSR_S6`](#6-the-coverage-ladder--the-most-transferable-idea-here) is a four-level graceful
degradation with **per-token provenance**, which is the reverse-direction form of the refusal
invariant in [`ARC_S9`](../../../plan/ARC_architecture.md#9-decisions) decision 8; and
[`SSR_S5`](#5-the-gloss-to-pose-pipeline) contains several geometric findings that apply to the
**forward** direction.

**For the assistant.** `RSS` is a **candidate dependency**, like `RSP` on which it is built. It is
MIT and may be shipped. Its `text_to_gloss/gpt.py` calls OpenAI directly, which the project must
not do — `D1`/`D6` prescribe Bedrock. Port the prompt, not the client. Nothing inside
`ref_repo/translation/spoken-to-signed/spoken-to-signed-translation/` may be edited; it is an
unmodified clone, excluded from version control.

</details>

---





# 1. EXECUTIVE SUMMARY
## 1.1. What This Repository Is
`ref_repo/translation/spoken-to-signed/spoken-to-signed-translation/` is described by its own
README as *"a `text-to-gloss-to-pose-to-video` pipeline for spoken to signed language
translation"* `[S1]`.

Its provenance is unusually strong for a repository of this size:

1. **Published** — *An Open-Source Gloss-Based Baseline for Spoken to Signed Language Translation*,
   Moryossef, Müller, Göhring, Jiang, Goldberg and Ebling, presented at the **2nd International
   Workshop on Automatic Translation for Signed and Spoken Languages (AT4SSL), 2023** `[S1]`
2. **Deployed** — live demonstrations at `sign.mt` for Swiss German (`sgg`), Swiss French (`ssr`)
   and Swiss Italian (`slf`) sign languages `[S1]`
3. **Maintained** — the clone is at `259aacd`, **2026-07-23**
4. **Licensed MIT** — © 2026 ZurichNLP `[S2]`

It is the sibling of `RSP` ([`SPR`](../sign-pose/SPR_sign_pose_report.md)) and `RLT`
([`LTR`](../signlang-literature/LTR_signlang_literature_report.md)); it depends on the first and is
catalogued by the second.




## 1.2. Why It Matters to SimplyNext
[`SCR`](../../../plan/scribbles.md) promises a two-way conversation, and
[`ARC_S6.1`](../../../plan/ARC_architecture.md#61-pipeline) currently describes only the
sign → spoken half in detail. This repository is the other half, and it is finished.

1. **It is the reverse direction, shippable** · *Use:* MIT, `pip`, CPU. Text in, a `.pose` sequence
   out. The hearing person's reply becomes signing without the project training anything —
   [`SSR_S3`](#3-the-three-stage-pipeline)
2. **It never fabricates a sign** · *Use:* Every output sign is retrieved from a lexicon or spelled
   letter by letter. There is no generative step that could invent one. This is
   [`CLD_S5.2`](../../../CLAUDE.md#52-honesty-about-the-product) enforced by architecture rather
   than by threshold
3. **It records how each token was resolved** · *Use:* The `CoverageType` ladder and
   `--coverage-info` are the auditable trace
   [`ARC_S7.3`](../../../plan/ARC_architecture.md#73-p1--the-recommendation-in-detail) item 8 asks
   for, built for the opposite direction — [`SSR_S6`](#6-the-coverage-ladder--the-most-transferable-idea-here)
4. **Its geometry transfers backwards** · *Use:* The signing-boundary test, the hysteresis on short
   spans, the scale-invariant hand-height gate and the citation-form duration finding are all
   directly relevant to the **forward** direction's stages ③ and ④ —
   [`SSR_S5`](#5-the-gloss-to-pose-pipeline) and [`SSR_S7`](#7-findings-that-apply-to-the-forward-direction)
5. **It contains a working LLM glosser** · *Use:* A tested system prompt with a notation for
   mouthing and named entities — [`SSR_S4.2`](#42-the-llm-glosser)

Against the four MVP steps in [`SCR`](../../../plan/scribbles.md): none of them, directly. This
repository runs the pipeline backwards. Its relevance is to the product's second half and to the
engineering of the first.




## 1.3. Summary
Three stages. A **glosser** turns a spoken-language sentence into a sequence of glosses, by one of
six interchangeable strategies from a bare lemmatiser to an LLM. A **lookup** resolves each gloss
against a lexicon of recorded signs stored as `.pose` files, falling back through a related sign
language, then to fingerspelling, then to nothing — recording which of the four happened for every
token. A **concatenator** trims each retrieved sign to its active span, caps its duration, finds
the frame pair where consecutive signs are geometrically closest, splices there, low-pass filters
the seam without touching the face, and hides hands that are hanging at rest. An optional fourth
stage renders the pose as video.

---





# 2. PROVENANCE, LICENCE AND REQUIREMENTS
## 2.1. Provenance
1. **Publisher**
   ZurichNLP (University of Zurich), with Amit Moryossef. Remote:
   `https://github.com/sign-language-processing/spoken-to-signed-translation.git`
2. **Clone state**
   `259aacd`, **2026-07-23**, *"fix(download_lexicon): add retry logic for network interruptions
   (#70)"*
3. **Version**
   `0.0.2`, declared in `pyproject.toml` `[S3]`. ⚠ The version number understates the maturity;
   the PR numbers are in the seventies and the code is in production behind `sign.mt`
4. **Maintenance status**
   **Active.** Recent commits are ordinary maintenance on a working system
5. **Scale**
   Small — one package, six test files, and roughly a dozen modules that matter. The 298 MB on disk
   is almost entirely the fingerspelling lexicon assets




## 2.2. Licence
`LICENSE`: *"MIT License / Copyright (c) 2026 ZurichNLP"* `[S2]`.

Permissive without qualification: commercial use, modification, distribution and sublicensing are
all granted, subject only to carrying the copyright notice and licence text.

> **Note — this is the second of two repositories in `ref_repo/translation/` that the project may
> actually ship**, the other being `RSP` ([`SPR_S2.2`](../sign-pose/SPR_sign_pose_report.md#22-licence)),
> with `RST` a third under Apache 2.0. `RSL`, `RSA` and `RLT` are cite-only for licence reasons
> that differ in each case.

> **Warning — the lexicon is not the code.** The MIT grant covers this repository. The **sign data**
> it downloads is a separate question: the default lexicon is **SignSuisse**, from the Swiss Deaf
> Association (SGB-FSS) `[S1]`, under whatever terms that organisation sets. The project must check
> those terms before any lexicon is used or redistributed, and in practice will build its own
> lexicon from its own recordings. Recorded as a placeholder in [`SSR_S8`](#8-running-it).




## 2.3. Requirements
`pyproject.toml` `[S3]`:

```toml
requires-python = ">=3.9"
dependencies = [
    "pose-format>=0.4.1",
    "pose_anonymization",
    "numpy",
    "scipy",
    "simplemma>=1.0.0",
]
```

**Five runtime dependencies. No torch, no TensorFlow, no MediaPipe, no GPU.** The optional extras
name the cost of each upgrade path explicitly:

| Extra     | Pulls in                           | Buys                                  |
| :-------- | :--------------------------------- | :------------------------------------ |
| `spacy`   | `spacy`                            | The `spacylemma` and `rules` glossers |
| `nmt`     | `sentencepiece`, `sockeye==3.1.10` | The neural glosser                    |
| `lexicon` | `sign-language-datasets`           | Lexicon download                      |
| `gcs`     | `gcsfs`                            | Cloud-hosted lexicons                 |

> **Note — `pose-format>=0.4.1` is a floor, not a pin, and the MediaPipe extra is not requested.**
> This repository consumes `.pose` files that already exist; it never estimates a pose. It
> therefore does **not** inherit the `mediapipe<0.10.30` collision recorded in
> [`SPR_S6`](../sign-pose/SPR_sign_pose_report.md#6-the-mediapipe-collision) — an important detail,
> because it means adopting `RSS` does not drag the legacy API in.

The project would pin an exact `pose-format` version itself, per
[`ARC_S6.5`](../../../plan/ARC_architecture.md#65-perception-engineering-rules) rule 2.

---





# 3. THE THREE-STAGE PIPELINE
```text
ref_repo/translation/spoken-to-signed/
├── SSR_spoken_to_signed_report.md         — this document (tracked in git)
└── spoken-to-signed-translation/          — the clone (git-ignored)
    ├── spoken_to_signed/
    │   ├── text_to_gloss/          ① six interchangeable glossers
    │   │   ├── simple.py             lemmatiser (simplemma)
    │   │   ├── spacylemma.py         spaCy lemmatiser
    │   │   ├── rules.py              reorder + drop, per language pair
    │   │   ├── nmt.py                Sockeye neural MT
    │   │   ├── gpt.py                ← LLM glosser. OpenAI client
    │   │   └── few_shots.json        the LLM's examples
    │   ├── gloss_to_pose/          ② lexicon lookup + stitching
    │   │   ├── lookup/lookup.py      ← the coverage ladder
    │   │   ├── lookup/fingerspelling_lookup.py
    │   │   ├── concatenate.py        ← trimming, capping, hiding
    │   │   ├── smoothing.py          ← seam selection and filtering
    │   │   └── languages.py          the language-backup map
    │   ├── pose_to_video/          ③ optional rendering (external package)
    │   ├── assets/fingerspelling_lexicon/   20 sign languages
    │   └── bin.py                  the three CLI entry points
    └── LICENSE                     MIT
```

The three CLI entry points mirror the three stages `[S1]`:

```bash
text_to_gloss              --text ... --glosser simple|spacylemma|rules|nmt
text_to_gloss_to_pose      ... --lexicon <dir> --pose out.pose
text_to_gloss_to_pose_to_video  ... --video out.mp4
```

**Worth reading:** `gloss_to_pose/concatenate.py` (the whole file, 200 lines, and the most
instructive code in `ref_repo/translation/`), `gloss_to_pose/smoothing.py:78-110`
(`find_best_connection_point`), `gloss_to_pose/lookup/lookup.py:16-45` (the coverage ladder and
gloss candidates), and `text_to_gloss/gpt.py:13-40` (the system prompt).

**Not worth reading:** `text_to_gloss/nmt.py` (Sockeye 3.1.10 is a pinned research dependency),
and `rules.py`'s German morphology, which is language-specific.

---





# 4. STAGE ① — TEXT TO GLOSS
## 4.1. Six Strategies Behind One Interface
Every glosser exposes `text_to_gloss(text, language, signed_language, **kwargs) -> list[Gloss]`,
which makes them substitutable at the command line `[S1]`:

1. **`simple`** — lemmatisation with `simplemma`. The widest language coverage and the only glosser
   available for all five supported sign languages
2. **`spacylemma`** — spaCy lemmatisation. *"more accurate, but slower … covering fewer languages
   than `simple`"* `[S1]`
3. **`rules`** — *"Rule-based word reordering and dropping"* `[S1]`, per language pair. German and
   French only
4. **`nmt`** — a Sockeye neural translation model. `sgg`, `gsg` and `bfi` only
5. **`gpt`** — an LLM. Not listed in the README's support table, but present in the source
6. **`common`** — shared plumbing

> **Note — the interface is the lesson.** Five approaches of wildly different cost, from a
> dictionary lookup to a hosted LLM, sit behind one function signature and one `--glosser` flag.
> That is the same discipline
> [`ARC_S7.2`](../../../plan/ARC_architecture.md#72-the-four-reference-repositories-compared)
> decision 14 applies to the landmark task: *build both behind one interface and measure*. This
> repository is field evidence that the pattern holds up.

That a **bare lemmatiser** is the default and the most broadly supported option is itself
informative. For a language whose glosses are largely uninflected content words, dropping
morphology and looking up lemmas is a defensible first approximation — and it is deterministic,
free, and offline.




## 4.2. The LLM Glosser
`text_to_gloss/gpt.py` `[S4]` is a complete, working example of the task the project's own
assembler agent performs in reverse. Its call configuration is `model="gpt-4o-mini",
temperature=0, seed=42, max_tokens=500` (line 107), with a system prompt, a set of few-shot
message pairs loaded from `few_shots.json`, and a JSON-in/JSON-out contract.

The system prompt's four rules `[S4]`:

1. **Sentence structure** — gloss each sentence separately; *"Prefer SOV (Subject-Object-Verb) word
   order for glossing"*
2. **Glossing** — glosses uppercase, and the original word retained beside the gloss, separated by
   a slash: `HELLO/Hello`
3. **Mouthing** — `⌘` marks a mouthed gloss, with brackets: `⌘schön(SCHÖN/schöne)`
4. **Named entities** — `%` in place of a gloss means *spell it out*: `%(Inigo Montoya)`

Three of these are worth taking:

1. **Keeping the source word beside the gloss** (`GLOSS/word`) means the output carries its own
   provenance. Nothing downstream has to guess which input token produced which gloss, and a human
   reading the trace can check it. This is the same instinct as
   [`SSR_S6`](#6-the-coverage-ladder--the-most-transferable-idea-here)
2. **`%` for named entities is an anti-hallucination device at the notation level.** A proper noun
   has no gloss; the notation forces the model to say *"spell this"* rather than invent a sign.
   [`ARC_S6.1`](../../../plan/ARC_architecture.md#61-pipeline) stage ⑨ lists *"request
   fingerspelling"* as a repair action in the forward direction; here the same idea is a first-class
   output token
3. **`temperature=0, seed=42`** — determinism as a deliberate choice for a translation task

> **Warning — the client must change.** `get_openai_client()` reads `OPENAI_API_KEY` and calls
> `chat.completions.create`. The project's model access is **AWS Bedrock**, per `D1` and `D6`, and
> `CLD_S4` constraint 8 requires model IDs to be read from a constant. Port the **prompt and the
> notation**; write the client against Bedrock. The few-shot mechanism transfers unchanged.

---





# 5. THE GLOSS-TO-POSE PIPELINE
`gloss_to_pose/concatenate.py` is the most instructive single file in `ref_repo/translation/`,
because it is a working solution to *"stitch recorded fragments into something that looks
continuous"* — and several of its parts read the same geometry the forward direction must read.




## 5.1. Finding the Signing Span
`get_signing_boundary()` at `concatenate.py:29-49` `[S5]`:

```python
wrist_y = pose.body.data[:, 0, wrist_index, 1]
elbow_y = pose.body.data[:, 0, elbow_index, 1]
wrist_above_elbow = wrist_y < elbow_y
...
return SigningBoundary(
    start=max(first_non_zero_index, first_active_frame - 5),
    end=min(last_non_zero_index, last_active_frame + 5),
)
```

A frame is *signing* when the **wrist is above the elbow**, with a five-frame margin at each end
and a clamp to the frames where the wrist was detected at all. `active_signing_span()` takes the
union across both hands.

> **This is the third independent appearance of the same heuristic.** `RDH` uses `hands_up_only`
> as a segmentation prior ([`DHS_S3.4`](../../../doc/DHS_depthai_synthesis.md#34-hands-up-only-as-a-segmentation-prior));
> [`ARC_S6.5`](../../../plan/ARC_architecture.md#65-perception-engineering-rules) rule 10
> generalises it to *hands-in-signing-space*; and here a different team, in a different direction,
> in a different language, reaches for the same test. Three independent uses is as much
> corroboration as a heuristic of this kind gets.

The comment above it is equally worth recording — *"Ideally, this could use a sign language
detection model"* `[S5]`. The authors know the geometric test is a stand-in, and name the upgrade.
[`LTR_S4.1`](../signlang-literature/LTR_signlang_literature_report.md#41-sign-language-detection)
records what that model would be.




## 5.2. The Concatenation Order
`concatenate_poses()` at `concatenate.py:177-214` `[S5]` runs seven steps in a fixed order:

1. **`reduce_holistic`** each pose — 543 → 178 points
   ([`SPR_S5.2`](../sign-pose/SPR_sign_pose_report.md#52-reduction))
2. **`normalize`** each pose — shoulder-midpoint origin, inter-shoulder scale
3. **`process_sign`** each pose — trim to the active span; cap its duration; keep the first sign's
   onset and the last sign's offset at normal speed
4. **`smooth_concatenate_poses`** — seam selection and splicing
5. **`correct_wrists`** — *"should be after smoothing"*, says the source comment
6. **`normalize_pose_size`** — scale to a target render width
7. **`hide_lowered_hands`** — suppress hands hanging at rest

Steps 3 and 7 are the ones with transferable content, and step 5's ordering constraint is a
concrete engineering fact: smoothing runs over the arrays, so wrist substitution must follow it or
be smoothed away.




## 5.3. Smoothing the Seams
Two findings from `smoothing.py` `[S6]`.

**The seam is chosen, not assumed.** `find_best_connection_point()` at `smoothing.py:78-110`
searches a **0.3-second window** at the end of one sign and the start of the next for the frame
pair whose poses are closest, and splices there. The distance is **confidence-weighted**: each
keypoint contributes in proportion to the *product* of its confidence in the two frames, so
undetected points — whose coordinates are arbitrary — cannot decide the seam. The total is
normalised by the summed weight so that a pair is not rewarded for having fewer detected points.

> **Note — this distance function is directly reusable in the forward direction.** Any comparison
> of two poses with missing keypoints has the same problem, including template matching, dynamic
> time warping against reference signs, and nearest-neighbour classification. *Weight each keypoint
> by the product of its two confidences and normalise by the total weight* is the general form, and
> it is about six lines.

**The face is excluded from the seam distance**, with a stated reason: *"the face is ~130 of the
~180 keypoints and barely moves between signs, so it would dominate the distance and drown out the
hands"* `[S6]`. A distance over all points is a distance over the face.

**The face is also excluded from temporal smoothing**, for a different and more important reason.
`smooth_non_face()` at `smoothing.py:10-25` filters everything except the `FACE_LANDMARKS` block,
because *"smoothing it dampens mouthing and other fast facial expressions that carry meaning, and
it has no seam jitter to fix"* `[S6]`.

> **This is a rule for the forward direction, and it contradicts a natural instinct.** Any jitter
> in landmark output invites a smoothing filter. Applying one uniformly would attenuate exactly the
> fast mouth and brow movements that
> [`ARC_S3.2`](../../../plan/ARC_architecture.md#32-the-landmark-budget) items 4 and 5 include for
> their linguistic content. **Smooth the hands and body; leave the face alone.** Recorded as a new
> perception rule in [`ARC_S6.5`](../../../plan/ARC_architecture.md#65-perception-engineering-rules).

**The filter itself**, `pose_butterworth_filter()` at `smoothing.py:31-47`: a **zero-phase
4th-order Butterworth low-pass at 6.0 Hz**, applied with `scipy.signal.filtfilt`, falling back to a
3-point Savitzky–Golay pass for clips too short for `filtfilt`'s edge padding. The source cites
*"Sign Stitching", Walsh et al., BMVC 2024* for preferring it to the lighter filter `[S6]`.

> **A 6 Hz cutoff is a usable number.** It asserts that meaningful sign motion lives below ~6 Hz
> and that anything faster is noise — a defensible default for the project's own smoothing and a
> sanity check on its velocity features. ⚠ It is one system's chosen parameter, not a measured
> property of sign language; the BMVC 2024 paper it cites was not read for this report.




## 5.4. Duration, and a Number the Project Needs
`cap_pose_duration()` at `concatenate.py:81-97` carries this comment `[S5]`:

> *"Citation-form dictionary signs are ~12-15x longer than the same sign in fluent signing (mostly
> preparation, holds and retraction), which is the main reason a naive stitch runs far too long."*

The function resamples any sign longer than `max_sign_seconds` — **defaulting to 0.8 s** — down to
that duration while keeping the original fps, so the sign plays faster rather than at lower temporal
resolution. `process_sign()` exempts the first sign's onset and the last sign's offset, because
those are genuine rest-to-signing transitions rather than dictionary padding.

> **Warning — this is a data-collection warning for the forward direction, and it is severe.** If
> the project records its closed vocabulary as **isolated citation-form signs** — one sign per clip,
> performed deliberately for the camera — and then attempts to recognise **fluent signing** from
> the same model, the durations will differ by an order of magnitude and the preparation and
> retraction phases present in training will be absent at inference. A classifier trained on
> citation form will not see the same distribution it is tested on.
>
> This is the mechanism behind `RSL`'s dictionary-bootstrapping design, which cuts training clips
> **out of continuous video** rather than recording them in isolation
> ([`SLR_S6.2`](../slrt/SLR_slrt_report.md#62-the-three-phases)). Two independent repositories,
> pointing at the same problem from opposite directions.
>
> ⚠ The "12–15×" figure is a source-code comment, not a citation. It is directionally credible and
> corroborated by `RSL`'s design; it must not be quoted as a measurement. Recorded for `EVL` and
> for [`RSK_S4.1`](../../../plan/RSK_risk_register.md#41-data).




## 5.5. Hysteresis and a Scale-Invariant Height Gate
Two small functions with disproportionate value.

**`_drop_short_spans(flags, min_len)`** at `concatenate.py:138-149` `[S5]` takes a boolean array
over frames and clears any run of `True` shorter than `min_len`, by finding the run edges with a
single `np.flatnonzero` over a padded difference. It is roughly ten lines and it is exactly the
**minimum-duration hysteresis** that
[`ARC_S6.1`](../../../plan/ARC_architecture.md#61-pipeline) stage ④ requires to stop a segmenter
firing on a twitch.

**`hide_lowered_hands(pose, threshold=0.15, min_show_seconds=0.2)`** at `concatenate.py:151-175`
`[S5]` computes, per frame and per hand:

```python
torso = np.median(y[:, hip] - y[:, shoulder])
rel_height = (y[:, hip] - y[:, wrist]) / abs(torso)
shown = _drop_short_spans(rel_height >= threshold, min_show_frames)
```

Wrist height is expressed as a fraction of the signer's own **hip-to-shoulder distance** — 0 at the
hip, 1 at the shoulder — and a hand counts as raised above **0.15**, with runs shorter than
**0.2 s** discarded.

> **This is a strict improvement on the wrist-above-elbow test**, and on
> [`ARC_S6.5`](../../../plan/ARC_architecture.md#65-perception-engineering-rules) rule 10 as
> currently written. It is **scale-invariant** — normalised by the signer's own torso, so it is
> independent of distance from the camera and of body size — it uses a **median over the sequence**
> for the torso length rather than a per-frame estimate, so a bad frame cannot move the threshold,
> and it comes with **hysteresis attached**. The two functions together are the signing-space gate
> the project needs, in about twenty lines.

---





# 6. THE COVERAGE LADDER — THE MOST TRANSFERABLE IDEA HERE
`gloss_to_pose/lookup/lookup.py:16-37` `[S7]`:

```python
class CoverageType(str, Enum):
    LEXICON = "lexicon"
    LANGUAGE_BACKUP = "language_backup"
    FINGERSPELLING_BACKUP = "fingerspelling_backup"
    UNMATCHED = "unmatched"


class TokenCoverage(NamedTuple):
    word: str
    gloss: str
    coverage: CoverageType
```

Every token is resolved by descending a four-rung ladder, and **which rung it landed on is
recorded**:

1. **`LEXICON`** — the gloss was found in the target sign language's own lexicon
2. **`LANGUAGE_BACKUP`** — found in a related sign language. `languages.py` declares the map:
   `slf → ise` (Swiss Italian to Italian), `ssr → fsl` (Swiss French to French) `[S8]`
3. **`FINGERSPELLING_BACKUP`** — not found; spelled letter by letter from the fingerspelling
   lexicon. **This is the default behaviour**, and `--disable-fingerspelling` turns it off `[S1]`
4. **`UNMATCHED`** — nothing worked, and the token is dropped

The ladder is surfaced to the user. `--coverage-info` prints the per-token result colour-coded in
the terminal — *"green: lexicon, yellow: language backup, orange: fingerspelling, red: unmatched"*
— and `--coverage-stats <file.json>` writes the same as JSON `[S1]`.

Before the ladder is descended, `gloss_candidates()` at `lookup.py:45-55` generates progressively
normalised lookup forms *"most conservative first"* — the raw gloss, lowercased, stripped of
glosser artefacts (`REZEPT+` → `rezept`, `berg-ix` → `berg`), and finally alphabetic-only. Each
form is tried in order, so an exact match always beats a normalised one.

> **This is [`ARC_S9`](../../../plan/ARC_architecture.md#9-decisions) decision 8 in the other
> direction, and it is better engineered than the version `ARC` currently describes.** The
> forward-direction design says: below a confidence threshold, do not emit a sentence; plan a
> repair. This system says something stronger and more useful — **always emit, but always record
> the provenance of every token, and expose it.** Four named states, one per token, machine-readable
> and human-visible.
>
> Applied forward, the analogue is: every gloss in the assembler's input carries how it was
> obtained — *classifier, high confidence* / *classifier, top-k with the signer's confirmation* /
> *fingerspelled* / *unresolved* — and the output shows it. That is a richer trace than a single
> sentence-level confidence, it is exactly the *"show the gloss trace"* requirement in
> [`ARC_S7.3`](../../../plan/ARC_architecture.md#73-p1--the-recommendation-in-detail) item 8, and
> it turns *refusal precision*
> ([`ARC_S8.4`](../../../plan/ARC_architecture.md#84-proposed-metric-set) metric 4) into something
> measurable per token rather than per utterance.

**The system also cannot hallucinate.** Every emitted sign is a recorded `.pose` file or a spelled
letter. There is no model that could generate a plausible-but-wrong sign. The forward direction
cannot be made safe this cheaply — recognition is inherently probabilistic — but the *shape* of the
guarantee is the one to imitate.




## 6.1. The Fingerspelling Lexicon
`spoken_to_signed/assets/fingerspelling_lexicon/` holds alphabets for **twenty sign languages**,
by IANA subtag `[S9]`: `ase` (American), `asq`, `bzs`, `cse`, `csq`, `eso`, `gsg` (German), `gss`,
`ise` (Italian), `jos`, `lls`, `mfs`, `psr`, `sgg` (Swiss German), `ssp`, `svk`, `swl`, `tsm`
(Turkish), `ukl`, plus an index.

> **Warning — Singapore Sign Language (`sls`) is not among them.** Nor is any Southeast Asian sign
> language. This is the same gap
> [`LTR_S6.2`](../signlang-literature/LTR_signlang_literature_report.md#62-what-is-not-there)
> records in the dataset registry, and it bears directly on
> [`ARC_S9.1`](../../../plan/ARC_architecture.md#91-open-questions-for-the-team) question 2. A
> project choosing SgSL gets no fingerspelling alphabet for free and would have to record 26
> handshapes — which, at one clip per letter, is the cheapest data-collection task in the entire
> plan and a genuinely achievable deliverable.

---





# 7. FINDINGS THAT APPLY TO THE FORWARD DIRECTION
Collected here because they are the reason this repository matters beyond its own direction.

1. **Wrist-above-elbow as a signing gate** — a third independent use —
   [`SSR_S5.1`](#51-finding-the-signing-span)
2. **Torso-normalised hand height with hysteresis** — a strictly better version of the same gate —
   [`SSR_S5.5`](#55-hysteresis-and-a-scale-invariant-height-gate)
3. **Never temporally smooth the face** — it destroys mouthing —
   [`SSR_S5.3`](#53-smoothing-the-seams)
4. **6 Hz low-pass for hands and body**, zero-phase — ⚠ one system's parameter —
   [`SSR_S5.3`](#53-smoothing-the-seams)
5. **Confidence-product weighting for any pose-to-pose distance** —
   [`SSR_S5.3`](#53-smoothing-the-seams)
6. **Citation form is 12–15× longer than fluent signing** — a training-data warning —
   [`SSR_S5.4`](#54-duration-and-a-number-the-project-needs)
7. **Exclude the face from any whole-body distance** — 128 of 178 points would dominate it —
   [`SSR_S5.3`](#53-smoothing-the-seams)
8. **Per-token provenance beats a single confidence number** —
   [`SSR_S6`](#6-the-coverage-ladder--the-most-transferable-idea-here)
9. **Substitutable strategies behind one interface**, chosen by flag —
   [`SSR_S4.1`](#41-six-strategies-behind-one-interface)

---





# 8. RUNNING IT
This repository runs today, on a laptop, and the project should run it in week one.

```bash
pip install spoken-to-signed

text_to_gloss_to_pose \
  --text "Kleine Kinder essen Pizza in Zürich." \
  --glosser simple \
  --lexicon assets/dummy_lexicon \
  --spoken-language de --signed-language sgg \
  --pose quick_test.pose \
  --coverage-info
```

A **dummy lexicon is checked in** at `assets/dummy_lexicon/`, so the pipeline demonstrates
end-to-end with no download. A Colab notebook is linked from the README for the same purpose `[S1]`.

Video rendering is the one expensive step and it is **not** installed by default — it requires
`pose-to-video[pix2pix, simple_upscaler]` from a git URL `[S1]`. The project does not need it: a
rendered pose skeleton via `PoseVisualizer`
([`SPR_S5`](../sign-pose/SPR_sign_pose_report.md#5-the-functions-worth-the-dependency)) is an
adequate and honest output for the reverse direction, and an avatar that looks almost-human is a
worse product than a skeleton that obviously is not.

> **Placeholder — the lexicon the project will actually use.**
> **Missing:** the terms under which SignSuisse lexicon data may be used and redistributed, and
> whether the project builds its own lexicon instead by recording its closed vocabulary once and
> storing it as `.pose` files.
> **Update trigger:** the scenario and vocabulary decision —
> [`ARC_S9.1`](../../../plan/ARC_architecture.md#91-open-questions-for-the-team) question 1.
> **Owner:** team.

---





# 9. WHAT THE REPOSITORY DOES NOT DO
1. **It does not recognise sign language.** It runs the pipeline the other way; nothing here reads
   a signer
2. **It does not estimate pose.** It consumes `.pose` files that already exist
3. **It has no gloss for anything outside its lexicon.** Coverage is exactly the lexicon plus an
   alphabet — which is the source of its honesty, not a defect
4. **It supports no Southeast Asian sign language** — [`SSR_S6.1`](#61-the-fingerspelling-lexicon)
5. **It does not resolve word sense.** A spoken word with two meanings maps to whichever gloss the
   lexicon indexes first, and `RST` names this limitation explicitly for the same design —
   [`STR_S4.2`](../sign-translator/STR_sign_translator_report.md#42-the-stated-limitation)
6. **It does not generate novel signs.** By design — [`SSR_S6`](#6-the-coverage-ladder--the-most-transferable-idea-here)
7. **It does not model non-manual grammar** beyond the `⌘` mouthing annotation in the LLM glosser's
   notation, which the lookup stage does not consume

---





# 10. RELEVANCE TO SIMPLYNEXT
## 10.1. Lessons to Carry Across
| #  | Lesson                                                                                     |
| :- | :----------------------------------------------------------------------------------------- |
| Z1 | **Record how every token was resolved, and show it.** Four named states, not one score     |
| Z2 | **Retrieval cannot hallucinate.** Where the architecture can guarantee it, let it          |
| Z3 | **Fingerspelling is the universal fallback**, in both directions                           |
| Z4 | **Never smooth the face** — it is where the fast, meaningful motion is                     |
| Z5 | **Normalise a height gate by the signer's own torso**, and attach hysteresis               |
| Z6 | **Weight a pose distance by the product of confidences**, and normalise by the total       |
| Z7 | **Citation-form signs are ~12–15× too long.** Train on the distribution you will test on   |
| Z8 | **Put substitutable strategies behind one flag** and measure, rather than choosing early   |
| Z9 | **A checked-in dummy dataset makes a pipeline demonstrable on day one**                    |

Z9 is a delivery lesson. `assets/dummy_lexicon/` is a handful of files that let anyone run the
whole pipeline in one command, which is precisely what `D3_p42`'s *"the `README` must let a judge
run the code"* requires. The project should ship the equivalent.




## 10.2. What the Project Takes
1. **The package** · *Take:* `spoken-to-signed`, pinned · *Where:* `requirements.txt`; the reverse
   direction of [`ARC_S6.1`](../../../plan/ARC_architecture.md#61-pipeline)
2. **The coverage ladder** · *Take:* Per-token provenance, four named states, exposed ·
   *Where:* [`ARC_S6.1`](../../../plan/ARC_architecture.md#61-pipeline) stages ⑤/⑨ and
   [`ARC_S8.4`](../../../plan/ARC_architecture.md#84-proposed-metric-set) metric 4
3. **`hide_lowered_hands`'s height gate** · *Take:* Torso-normalised, threshold 0.15, 0.2 s
   hysteresis · *Where:*
   [`ARC_S6.5`](../../../plan/ARC_architecture.md#65-perception-engineering-rules) rule 10, rewritten
4. **`_drop_short_spans`** · *Take:* Minimum-duration hysteresis in ten lines ·
   *Where:* [`ARC_S6.1`](../../../plan/ARC_architecture.md#61-pipeline) stage ④
5. **The no-face-smoothing rule** · *Take:* Filter hands and body only ·
   *Where:* [`ARC_S6.5`](../../../plan/ARC_architecture.md#65-perception-engineering-rules), a new
   rule
6. **The confidence-weighted distance** · *Take:* Product weighting, normalised ·
   *Where:* Any template match or DTW against reference signs
7. **The LLM glosser's notation** · *Take:* `GLOSS/word`, `⌘` for mouthing, `%` for spell-out ·
   *Where:* The assembler's prompt, on Bedrock
8. **The citation-form warning** · *Take:* 12–15×, ⚠ as a code comment not a measurement ·
   *Where:* `EVL` data protocol; [`RSK_S4.1`](../../../plan/RSK_risk_register.md#41-data)




## 10.3. What the Project Does Not Take
1. **`text_to_gloss/gpt.py`'s OpenAI client.** Bedrock only — `D1`, `D6`,
   [`ARC_S8`](../../../plan/ARC_architecture.md#8-cost-model-against-the-aws-cap)
2. **The `nmt` extra.** `sockeye==3.1.10` for three language pairs the project does not use
3. **The SignSuisse lexicon**, without checking its terms — [`SSR_S2.2`](#22-licence)
4. **`pose_to_video` and pix2pix rendering.** A skeleton is the honest output
5. **The German and French rule sets.** Language-specific, and neither language is in scope

---





# 11. SOURCES
1. **`[S1]`**
   *Source:* `ref_repo/translation/spoken-to-signed/spoken-to-signed-translation/README.md` at
   `259aacd` — the pipeline description, the CLI usage, the glosser table, the supported-language
   table, the coverage flags, the fingerspelling default, the video-rendering note and the AT4SSL
   2023 citation
   *Reliability:* Official project documentation. The AT4SSL 2023 paper is peer-reviewed and was
   **not** read for this review
2. **`[S2]`**
   *Source:* `.../spoken-to-signed-translation/LICENSE` — MIT, © 2026 ZurichNLP
   *Reliability:* Primary. ⚠ Read as an engineer, not a lawyer
3. **`[S3]`**
   *Source:* `.../spoken-to-signed-translation/pyproject.toml` — version, dependencies, extras and
   console scripts
   *Reliability:* Primary — read from the clone
4. **`[S4]`**
   *Source:* `.../spoken_to_signed/text_to_gloss/gpt.py:13-40,107` — the system prompt and the model
   call configuration
   *Reliability:* Primary — read from the clone
5. **`[S5]`**
   *Source:* `.../spoken_to_signed/gloss_to_pose/concatenate.py:29-49,81-97,138-175,177-214` —
   the signing boundary, duration capping, short-span hysteresis, lowered-hand suppression and the
   concatenation order, including the source comments quoted
   *Reliability:* Primary — read from the clone. ⚠ The "12–15×" citation-form figure is an
   uncited source comment; it is corroborated in direction by
   [`SLR_S6.2`](../slrt/SLR_slrt_report.md#62-the-three-phases) but is not a measurement
6. **`[S6]`**
   *Source:* `.../spoken_to_signed/gloss_to_pose/smoothing.py:10-47,78-110` — `smooth_non_face`,
   the Savitzky–Golay and Butterworth filters, and `find_best_connection_point`
   *Reliability:* Primary — read from the clone. ⚠ The cited *"Sign Stitching", Walsh et al., BMVC
   2024* was not read for this review
7. **`[S7]`**
   *Source:* `.../spoken_to_signed/gloss_to_pose/lookup/lookup.py:16-55` — `CoverageType`,
   `TokenCoverage`, `PoseResult` and `gloss_candidates`
   *Reliability:* Primary — read from the clone
8. **`[S8]`**
   *Source:* `.../spoken_to_signed/gloss_to_pose/languages.py` — the `LANGUAGE_BACKUP` map
   *Reliability:* Primary — read from the clone
9. **`[S9]`**
   *Source:* `.../spoken_to_signed/assets/fingerspelling_lexicon/` — the twenty IANA-coded
   sub-directories, enumerated from the working tree
   *Reliability:* Primary
10. **`[S10]`**
    *Source:* The clone itself at `259aacd` (2026-07-23). All `file:line` citations resolve against
    this commit
    *Reliability:* Primary

---





# 12. CHANGE LOG
1. **2026-09-04** · *Author:* Claude (Opus 5)
   *Change:* Created from a read of the README, the licence, `pyproject.toml`, all six glossers,
   the full concatenation and smoothing modules, the lookup coverage ladder, the language-backup
   map and the fingerspelling lexicon inventory. Recorded `RSS` as the project's answer to the
   reverse direction and as its third permissively-licensed candidate dependency; identified the
   `CoverageType` ladder as a better-engineered form of
   [`ARC_S9`](../../../plan/ARC_architecture.md#9-decisions) decision 8; and extracted nine
   findings that apply to the **forward** direction, chief among them the no-face-smoothing rule,
   the torso-normalised height gate with hysteresis, and the citation-form duration warning.
