**SPOKEN-TO-SIGNED — SYNTHESIS FOR SIMPLYNEXT**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field             | Value                                                                            |
| :---------------- | :------------------------------------------------------------------------------- |
| **Code**          | `SSS`                                                                            |
| **Status**        | Live                                                                             |
| **Last reviewed** | 2026-09-04                                                                       |
| **Scope**         | Short orientation to `RSS`, the reverse direction                                |
| **Subject**       | `RSS` — `spoken-to-signed/…-translation/` at `259aacd`                           |
| **Full report**   | [`SSR`](../ref_repo/translation/spoken-to-signed/SSR_spoken_to_signed_report.md) |

**For the team.** The **reverse direction of the product, already built**: MIT, `pip install
spoken-to-signed`, CPU-only, published at AT4SSL 2023, deployed behind `sign.mt`. It answers the
second half of *both-way translation*, and it contributes two things to the **forward** half —
a per-token provenance design ([`SSS_S4`](#4-the-coverage-ladder)) and six geometric findings
([`SSS_S5`](#5-what-it-teaches-the-forward-direction)). The complete analysis is in
[`SSR`](../ref_repo/translation/spoken-to-signed/SSR_spoken_to_signed_report.md), beside the clone
in `ref_repo/translation/spoken-to-signed/`.

**For the assistant.** `RSS` is a **candidate dependency**, MIT, and may be shipped. Its
`text_to_gloss/gpt.py` calls OpenAI directly, which the project must not do — `D1`/`D6` prescribe
Bedrock. Port the prompt, not the client. Where this file and
[`SSR`](../ref_repo/translation/spoken-to-signed/SSR_spoken_to_signed_report.md) disagree, `SSR`
wins.

</details>

---





# 1. WHAT THIS IS
`ZurichNLP/spoken-to-signed-translation` is *"a `text-to-gloss-to-pose-to-video` pipeline for spoken
to signed language translation"*.

Its provenance is strong for a repository this small: **published** at the 2nd International
Workshop on Automatic Translation for Signed and Spoken Languages, **2023**; **deployed** at
`sign.mt` for Swiss German, Swiss French and Swiss Italian sign languages; **maintained** — the
clone is `259aacd`, 2026-07-23; and **MIT-licensed**.

It is the sibling of `RSP` ([`SPS`](SPS_sign_pose_synthesis.md)), which it depends on, and of `RLT`
([`LTS`](LTS_signlang_literature_synthesis.md)), which catalogues it.

**Five runtime dependencies**: `pose-format`, `pose_anonymization`, `numpy`, `scipy`, `simplemma`.
No torch, no MediaPipe, no GPU — and because it *consumes* `.pose` files rather than estimating
them, it does **not** inherit `RSP`'s legacy-API collision
([`SPS_S4`](SPS_sign_pose_synthesis.md#4-the-one-thing-not-to-take)).

> **Warning — the code licence is not the data licence.** MIT covers this repository. The default
> lexicon is **SignSuisse**, from the Swiss Deaf Association, under whatever terms that organisation
> sets. Check before use; in practice the project builds its own lexicon from its own recordings.

---





# 2. RELEVANCE
[`SCR`](../plan/scribbles.md) promises a two-way conversation, and
[`ARC_S6.1`](../plan/ARC_architecture.md#61-pipeline) currently details only the sign → spoken half.
This is the other half, finished.

1. **It is shippable.** Text in, a `.pose` sequence out, on a laptop, without training anything
2. **It cannot fabricate a sign.** Every output is retrieved from a lexicon or spelled letter by
   letter. There is no generative step that could invent one — this is
   [`CLD_S5.2`](../CLAUDE.md#52-honesty-about-the-product) enforced by architecture rather than by
   threshold
3. **It records how every token was resolved**, and shows it — [`SSS_S4`](#4-the-coverage-ladder)
4. **Its geometry transfers backwards** — [`SSS_S5`](#5-what-it-teaches-the-forward-direction)
5. **It contains a working LLM glosser** with a tested notation — [`SSS_S3.2`](#32-the-llm-glosser)

---





# 3. THE PIPELINE
```text
text ──► ① GLOSSER ──► ② LOOKUP + STITCH ──► ③ RENDER (optional)
         simple            lexicon                 pix2pix
         spacylemma        language backup         upscaler
         rules             fingerspelling
         nmt               ↓
         gpt               concatenate.py + smoothing.py
```

Three CLI entry points mirror the three stages: `text_to_gloss`, `text_to_gloss_to_pose`,
`text_to_gloss_to_pose_to_video`.




## 3.1. Six Glossers Behind One Flag
Every glosser exposes the same signature, selected by `--glosser`:

| Glosser      | Method                       | Coverage                |
| :----------- | :--------------------------- | :---------------------- |
| `simple`     | `simplemma` lemmatiser       | All five sign languages |
| `spacylemma` | spaCy lemmatiser             | Fewer, more accurate    |
| `rules`      | Reordering and word dropping | German, French          |
| `nmt`        | Sockeye neural MT            | Three language pairs    |
| `gpt`        | An LLM                       | Any                     |

> **The interface is the lesson.** Five approaches of wildly different cost sit behind one function
> signature and one flag. That is the discipline
> [`ARC_S9`](../plan/ARC_architecture.md#9-decisions) decision 14 applies to the landmark task —
> *build both behind one interface and measure* — and this is field evidence that it holds up.

That a **bare lemmatiser** is the default and the most broadly supported option is itself
informative: for a language whose glosses are largely uninflected content words, dropping morphology
and looking up lemmas is a defensible, deterministic, free first approximation.




## 3.2. The LLM Glosser
`gpt.py` calls `gpt-4o-mini` at `temperature=0, seed=42, max_tokens=500` with a system prompt and
few-shot examples, on a JSON-in/JSON-out contract. Its notation is the transferable part:

1. **`GLOSS/word`** — the source word is kept beside the gloss, so the output carries its own
   provenance and a human reading the trace can check it
2. **`⌘schön(SCHÖN/schöne)`** — mouthing marked explicitly
3. **`%(Inigo Montoya)`** — a named entity is **spelled out**, not glossed

> **Rule 3 is an anti-hallucination device at the notation level.** A proper noun has no gloss, and
> the notation forces the model to say *"spell this"* rather than invent a sign.
> [`ARC_S6.1`](../plan/ARC_architecture.md#61-pipeline) stage ⑨ lists *"request fingerspelling"* as
> a repair action in the forward direction; here the same idea is a first-class output token.

> **Warning — the client must change.** `get_openai_client()` reads `OPENAI_API_KEY`. The project's
> model access is **AWS Bedrock**, per `D1` and `D6`, and `CLD_S4` constraint 8 requires model IDs
> read from a constant. Port the **prompt and the notation**; write the client against Bedrock.

---





# 4. THE COVERAGE LADDER
```python
class CoverageType(str, Enum):
    LEXICON = "lexicon"
    LANGUAGE_BACKUP = "language_backup"
    FINGERSPELLING_BACKUP = "fingerspelling_backup"
    UNMATCHED = "unmatched"
```

Every token descends a four-rung ladder, and **which rung it landed on is recorded**:

1. **`LEXICON`** — found in the target sign language's own lexicon
2. **`LANGUAGE_BACKUP`** — found in a related sign language (`slf → ise`, `ssr → fsl`)
3. **`FINGERSPELLING_BACKUP`** — spelled letter by letter. **This is the default**;
   `--disable-fingerspelling` turns it off
4. **`UNMATCHED`** — dropped

And it is **surfaced**: `--coverage-info` prints per-token results colour-coded — *"green: lexicon,
yellow: language backup, orange: fingerspelling, red: unmatched"* — and `--coverage-stats` writes
the same as JSON.

> **This is [`ARC_S9`](../plan/ARC_architecture.md#9-decisions) decision 8 in the other direction,
> better engineered than the version `ARC` currently describes.** The forward design says: below a
> confidence threshold, do not emit; plan a repair. This says something stronger — **always emit,
> but always record the provenance of every token, and expose it.**
>
> Applied forward: every gloss reaching the assembler carries how it was obtained — *classifier,
> high confidence* / *top-k, signer-confirmed* / *fingerspelled* / *unresolved* — and the output
> shows it. That is a richer trace than one sentence-level confidence, it is the *"show the gloss
> trace"* requirement in [`ARC_S7.3`](../plan/ARC_architecture.md#73-p1--the-recommendation-in-detail)
> item 8, and it makes *refusal precision*
> ([`ARC_S8.4`](../plan/ARC_architecture.md#84-proposed-metric-set) metric 4) measurable **per
> token** rather than per utterance.

**Fingerspelling alphabets ship for twenty sign languages**, by IANA subtag.

> **Warning — Singapore Sign Language (`sls`) is not among them**, nor is any Southeast Asian sign
> language. The same gap [`LTS_S5`](LTS_signlang_literature_synthesis.md#5-the-data-situation)
> records in the dataset registry. A project choosing SgSL would have to record 26 handshapes —
> which is the cheapest data-collection task in the whole plan, and an achievable deliverable.

---





# 5. WHAT IT TEACHES THE FORWARD DIRECTION
Six findings from `concatenate.py` and `smoothing.py`, all of which apply to stages ③ and ④ of
[`ARC_S6.1`](../plan/ARC_architecture.md#61-pipeline).

1. **Wrist-above-elbow marks signing — a third independent use.**
   `get_signing_boundary()` tests `wrist_y < elbow_y` with a ±5-frame margin. `RDH` uses the same
   test as `hands_up_only` ([`DHS_S3.4`](DHS_depthai_synthesis.md#34-hands-up-only-as-a-segmentation-prior));
   [`ARC_S6.5`](../plan/ARC_architecture.md#65-perception-engineering-rules) rule 10 generalises it.
   Three independent teams, three directions, one heuristic. The source comment is honest about it:
   *"Ideally, this could use a sign language detection model."*

2. **A better version of that gate.** `hide_lowered_hands()` normalises wrist height by the
   signer's own **hip-to-shoulder distance** — 0 at the hip, 1 at the shoulder — with a threshold of
   **0.15** and a **0.2 s** minimum. It is **scale-invariant**, uses a **median over the sequence**
   for torso length so one bad frame cannot move the threshold, and comes with hysteresis attached.
   Twenty lines, and strictly better than the raw elbow test.

3. **Hysteresis in ten lines.** `_drop_short_spans(flags, min_len)` clears any run of `True`
   shorter than `min_len` with a single `np.flatnonzero` over a padded difference. Exactly what
   stage ④ needs to stop a segmenter firing on a twitch.

4. **Never temporally smooth the face.** `smooth_non_face()` filters everything *except* the face
   block, because *"smoothing it dampens mouthing and other fast facial expressions that carry
   meaning."*
   > **This contradicts a natural instinct.** Landmark jitter invites a uniform smoothing filter.
   > Applying one would attenuate exactly the fast mouth and brow movements
   > [`ARC_S3.2`](../plan/ARC_architecture.md#32-the-landmark-budget) items 4 and 5 include for
   > their linguistic content. **Smooth the hands and body; leave the face alone.**

5. **A filter spec, and a frequency.** A zero-phase 4th-order **Butterworth low-pass at 6.0 Hz**,
   with a 3-point Savitzky–Golay fallback for short clips, citing *"Sign Stitching", Walsh et al.,
   BMVC 2024*. ⚠ One system's parameter, not a measured property of sign language — but a usable
   default and a sanity check on velocity features.

6. **Confidence-product weighting for any pose distance.** `find_best_connection_point()` weights
   each keypoint by the **product of its confidence in both frames** and normalises by the total, so
   undetected points cannot decide the answer — and excludes the face, because *"the face is ~130 of
   the ~180 keypoints and barely moves between signs, so it would dominate the distance."*
   Reusable for any template match, DTW or nearest-neighbour comparison in the forward direction.

---





# 6. THE NUMBER THAT CHANGES DATA COLLECTION
`cap_pose_duration()` carries this comment:

> *"Citation-form dictionary signs are ~12-15x longer than the same sign in fluent signing (mostly
> preparation, holds and retraction), which is the main reason a naive stitch runs far too long."*

The default cap is **0.8 seconds** per sign.

> **Warning — this is a severe training-data warning for the forward direction.** If the project
> records its closed vocabulary as **isolated citation-form clips** and then tries to recognise
> **fluent signing**, durations will differ by an order of magnitude and the preparation and
> retraction phases present in training will be absent at inference. The classifier will not see
> the distribution it is tested on.
>
> This is the mechanism behind `RSL`'s design, which cuts training clips **out of continuous video**
> rather than recording them in isolation
> ([`SLS_S6`](SLS_slrt_synthesis.md#6-the-architecture-worth-copying)). Two repositories pointing at
> the same problem from opposite directions.
>
> ⚠ The 12–15× figure is a source comment, not a citation. Directionally credible; not quotable as
> a measurement.

---





# 7. THE NINE LESSONS
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

Z9 is a delivery lesson. `assets/dummy_lexicon/` lets anyone run the whole pipeline in one command,
which is exactly what `D3_p42`'s *"the `README` must let a judge run the code"* requires. The
project should ship the equivalent.

---





# 8. WHAT IT DOES NOT DO
1. **It does not recognise sign language.** Nothing here reads a signer
2. **It does not estimate pose.** It consumes `.pose` files that already exist
3. **It has no gloss for anything outside its lexicon** — the source of its honesty, not a defect
4. **It supports no Southeast Asian sign language**
5. **It does not resolve word sense.** An ambiguous word maps to whichever gloss the index holds
   first — a gap `RST` names explicitly for the same design,
   [`STS_S4`](STS_sign_translator_synthesis.md#4-the-word-sense-gap)
6. **It does not generate novel signs.** By design
7. **It does not model non-manual grammar** beyond the `⌘` annotation, which the lookup stage does
   not consume

---





# 9. RUNNING IT
It runs today, and the project should run it in week one:

```bash
pip install spoken-to-signed

text_to_gloss_to_pose \
  --text "Kleine Kinder essen Pizza in Zürich." \
  --glosser simple --lexicon assets/dummy_lexicon \
  --spoken-language de --signed-language sgg \
  --pose quick_test.pose --coverage-info
```

A **dummy lexicon is checked in**, so this works with no download. Video rendering is the one
expensive step and is **not** installed by default — and the project does not need it: a rendered
pose skeleton is an adequate and honest output, and an avatar that looks almost-human is a worse
product than a skeleton that obviously is not.

---





# 10. WHERE TO GO NEXT
1. **Full breakdown** —
   [`SSR`](../ref_repo/translation/spoken-to-signed/SSR_spoken_to_signed_report.md)
2. **The library beneath it** — [`SPS`](SPS_sign_pose_synthesis.md)
3. **The rejected alternative** — [`SLS_S7`](SLS_slrt_synthesis.md)
4. **The word-sense gap** — [`STS`](STS_sign_translator_synthesis.md)
5. **Where it sits in the pipeline** — [`ARC_S6.1`](../plan/ARC_architecture.md)
6. **Where every document lives** — [`RIX`](../ref_index.md)

---





# 11. CHANGE LOG
1. **2026-09-04** · *Author:* Claude (Opus 5)
   *Change:* Created alongside
   [`SSR`](../ref_repo/translation/spoken-to-signed/SSR_spoken_to_signed_report.md), from a read of
   the README, the licence, `pyproject.toml`, all six glossers, the concatenation and smoothing
   modules, the lookup coverage ladder and the fingerspelling lexicon inventory.
