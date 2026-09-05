**EXECUTION PLAN**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field                      | Value                                           |
| :------------------------- | :---------------------------------------------- |
| **Code**                   | `PLN`                                           |
| **Status**                 | Draft                                           |
| **Last reviewed**          | 2026-09-05                                      |
| **Source of truth for**    | **Execution sequence, ownership, exit criteria** |
| **Parent**                 | [`ARC`](ARC_architecture.md)                    |
| **Scored against**         | [`JCR`](JCR_judging_criteria.md)                |
| **Problems catalogued in** | [`RSK`](RSK_risk_register.md)                   |
| **Children**               | `TDO` · `EVL` · `DEC`                           |

**For the team.** This document turns [`ARC`](ARC_architecture.md) into work. Every stage of the
pipeline in [`ARC_S6.1`](ARC_architecture.md#61-pipeline), every rule in
[`ARC_S6.5`](ARC_architecture.md#65-perception-engineering-rules) and every decision in
[`ARC_S9`](ARC_architecture.md#9-decisions) appears below as a numbered task with a size, a
dependency, an exit criterion and the reading that supports it. It does **not** re-argue the
architecture: where this document and `ARC` disagree on *what* to build, `ARC` wins; where they
disagree on *when*, this document wins.

Status is **Draft** because eighteen of the twenty-four decisions in
[`ARC_S9`](ARC_architecture.md#9-decisions) are still **Proposed** and four of the seven questions
in [`ARC_S9.1`](ARC_architecture.md#91-open-questions-for-the-team) are unanswered. The plan is
written against the decisions as they stand; [`PLN_S2.2`](#22-what-is-not-decided-and-what-it-blocks)
names every task an answer would move. Ratifying a decision unchanged moves nothing.

**For the assistant.** Task identifiers `T<wp>.<n>` are permanent and are never reused. Sizes are
the assistant's estimates, unmeasured, and carry `⚠` in
[`PLN_S1.2`](#12-work-item-identifiers-and-sizes) rather than on every line. No calendar date
appears in this document: the competition window is unconfirmed —
[`JCR_S9`](JCR_judging_criteria.md#9-sources). Decision status is changed only in `ARC`, on
explicit team instruction, never here.

</details>

---





# 1. HOW TO USE THIS DOCUMENT
## 1.1. What This Plan Is
A **build order**. Nine work packages, fifty tasks, one critical path, and a stated order in which
work is cut when the schedule runs short — [`PLN_S13.4`](#134-descoping-order).

Three things it deliberately is not:

1. **Not a design document.** The design is [`ARC`](ARC_architecture.md). Tasks below cite it by
   address rather than restating it
2. **Not a risk register.** The problems are [`RSK`](RSK_risk_register.md). Tasks name the risk IDs
   they answer, and [`PLN_S14`](#14-risk-controls-carried-into-the-plan) shows the coverage
3. **Not a task board.** `TDO` is the live board and is written from this document once the gates in
   [`PLN_S2`](#2-gates-and-prerequisites) clear




## 1.2. Work Item Identifiers and Sizes
Every task has a permanent ID of the form `T<work package>.<n>`. IDs are never reused.

| Size   | Meaning                                    |
| :----- | :----------------------------------------- |
| **S**  | Under two hours for one person             |
| **M**  | Half a day                                 |
| **L**  | A full day                                 |
| **XL** | More than one day, or more than one person |

> **Warning — ⚠ sizes are estimates, not measurements.** They are the assistant's judgement from
> the reference reports, not timings from this codebase, which does not yet exist. They exist to
> order the work and to make [`PLN_S13.4`](#134-descoping-order) arguable, not to promise a
> delivery time.




## 1.3. Reading a Task Entry
Each task carries the same five fields, in the same order.

1. **Header line** · *Contents:* Pipeline stage · size · dependencies · the `ARC` decision it
   implements or settles
2. **Statement** · *Contents:* One sentence naming what exists at the end that did not exist at the
   start
3. **Steps** · *Contents:* The numbered work, in order
4. **Done when** · *Contents:* The observable condition. A task is not done because it was worked
   on
5. **Read** · *Contents:* Addresses to open **before** starting, not after

---





# 2. GATES AND PREREQUISITES
## 2.1. What Is Decided
Six of the twenty-four decisions in [`ARC_S9`](ARC_architecture.md#9-decisions) carry a settled
status, and the plan below treats them as fixed.

1. **Decision 1 — Agreed** · *Consequence for the plan:* `T1.2` builds a hysteresis-held
   largest-person tracker. **No segmentation model is built at all**
2. **Decision 2 — Agreed** · *Consequence for the plan:* The landmark budget is hands (42) +
   handedness + upper-body pose (~11) + a curated brow and mouth subset. The full 468-point face
   mesh never reaches the classifier — `T4.1`
3. **Decision 3 — Agreed** · *Consequence for the plan:* Representation is body-normalised 2D plus
   per-hand world landmarks. No metric 3D, no depth hardware — `T1.5`
4. **Decision 4 — Agreed** · *Consequence for the plan:* The scenario is a normal, informal
   conversation between two individuals. `T3.1` must still bound it to a gloss list — see the
   warning below
5. **Decision 17 — Rejected** · *Consequence for the plan:* The 27–37 point budget from
   [`ARC_S3.2`](ARC_architecture.md#32-the-landmark-budget) is **not** the starting budget.
   Decision 2's budget is what `T4.1` builds
6. **Decision 18 — Agreed** · *Consequence for the plan:* The reverse direction is `RSS`, with the
   project's own lexicon — WP6, `PLN_S10`

> **Warning — decision 4 names a scenario, not a vocabulary.** *"A normal, informal conversation
> between two individuals"* is a **setting**; it does not bound what can be said in it, and an
> unbounded conversation is the shape `D3_p7` calls **"The Boiling Ocean"** and `RSK` rates `DEL-2`
> `S3`/`L3`. The closed vocabulary that decision 4 also mandates therefore has to be written down
> as an explicit gloss list before any data is recorded — that is `T3.1`, and it is on the critical
> path. The scenario decides the *register* of the vocabulary (greetings, introductions, small
> talk, repair phrases); it does not replace the list.

> **Note — decision 17's evidence has not gone away.** Two published systems set budgets of 27 and
> 63 points ([`ARC_S3.2`](ARC_architecture.md#32-the-landmark-budget)), and the team has chosen
> the wider one. `T4.1` therefore keeps the feature assembly parameterised by an index list, so a
> narrower budget can be measured later at no rewrite cost. **Whether to run that comparison is the
> team's call, not the assistant's** — [`CLD_S5.3`](../CLAUDE.md#53-scope).




## 2.2. What Is Not Decided, and What It Blocks
> **Placeholder — four unanswered questions.**
> **Missing:** answers to questions 2, 3, 4 and 5 of
> [`ARC_S9.1`](ARC_architecture.md#91-open-questions-for-the-team).
> **Update trigger:** a team decision on each; record it in
> [`ARC_S11`](ARC_architecture.md#11-change-log) and update
> [`PLN_S17`](#17-change-log) in the same change.
> **Owner:** team.

1. **Question 2 — SgSL or ASL?** · *Blocks:* `T3.1` `T3.2` `T3.3` `T6.3`
   *Why:* There is **no public SgSL data at all**, so SgSL means recording every sign the system
   will ever recognise, and recording 26 fingerspelling handshapes that `RSS` does not ship —
   [`ARC_S7.7.4`](ARC_architecture.md#774-what-the-data-registry-settles),
   [`SSS_S4`](../doc/SSS_spoken_to_signed_synthesis.md#4-the-coverage-ladder). ASL removes both
   tasks and removes the differentiator with them
2. **Question 3 — who is the named person?** · *Blocks:* `T8.5` `T8.6`, and the problem statement
   *Why:* [`JCR_S4.4`](JCR_judging_criteria.md#44-five-pressure-test-questions) question 1. `DEL-3`
   rates *"the Everyone Problem"* `S2`/`L3`. It blocks no code
3. **Question 4 — where does the data come from?** · *Blocks:* `T3.2` `T3.3` `T3.4`
   *Why:* Determines the whole of WP3, which is the critical path. Constrained by question 2 and by
   the fact that the field's public corpora are predominantly non-commercially licensed
4. **Question 5 — is geometric segmentation sound?** · *Blocks:* nothing
   *Why:* `T2.1` builds the interface that lets both answers coexist, and `T2.4` measures them.
   This is decision 20 working as designed: the question is answered by the plan rather than
   before it

Questions 1, 6 and 7 need no answer before work starts. Question 1 is settled far enough by
decision 4 to begin `T3.1`; question 6 (a learned segmenter) and question 7 (retrieval instead of
classification) are roadmap items for slide 9, not build items —
[`ARC_S5.6.4`](ARC_architecture.md#564-r4--retrieval-instead-of-classification).




## 2.3. The Lane That Proceeds Regardless
Nothing in [`PLN_S2.2`](#22-what-is-not-decided-and-what-it-blocks) blocks the following, which is
**thirty-one of the fifty tasks** and includes the entire perception stack. Work starts here on day
one whatever the answers turn out to be.

1. **All of WP0** · *Reason:* Repository shape, pins, config, telemetry and the frozen interfaces
   are vocabulary-independent
2. **All of WP1** · *Reason:* Landmarks, tracking fixes and normalisation are identical for SgSL
   and ASL
3. **All of WP2** · *Reason:* Segmentation is geometric and language-independent
4. **`T4.5`, the P2 baseline** · *Reason:* No training data is required — decision 9,
   [`ARC_S7.4`](ARC_architecture.md#74-p2--rationale-for-building-it-regardless)
5. **All of WP5 except the lexicon tool** · *Reason:* The graph, the critic, the loop bound and the
   repair planner are structure, not content
6. **`T6.1`, `T6.5`, and `T7.1`–`T7.4`** · *Reason:* The `RSS` install, the renderer, the screen and
   the fallback recording depend on a running pipeline, not on a chosen language

> **Decision implication.** The dataset is the long pole
> ([`RDM_S9`](../README.md#9-project-status) item 9), and the answers that unblock it are cheap to
> give. **Answering questions 2 and 4 is worth more team-hours than any single engineering task in
> this plan.**




## 2.4. Standing Constraints on Every Task
These bind all fifty tasks and are not repeated in each entry. Source:
[`CLD_S4`](../CLAUDE.md#4-hard-constraints-from-the-competition) and
[`TRN_S7`](../doc/TRN_training_synthesis.md#7-cross-cutting-rules).

1.  **Python, with `requirements.txt` or Docker** · *Source:* `D3_p42`
2.  **Folder structure `src/` `docs/` `data/` `tests/`** · *Source:* `D3_p23`
3.  **Secrets in `.env`; never commit a key or the `D6` 2FA secret** · *Source:* `D3_p42`,
    [`CLD_S6`](../CLAUDE.md#6-git)
4.  **Module names match the architecture slide** · *Source:* `D3_p42`, and `DEL-10`. The map is
    [`PLN_S3.3`](#33-module-map--the-slide-to-the-directory)
5.  **Every agent loop bounded by a counter held in state** · *Source:* `D3_p22`, and `AGT-6`
6.  **Model IDs read from a constant, never built** · *Source:* `D3`, and `SYS-12`
7.  **Heavy payloads in graph state, never in a prompt** · *Source:* `D2`, and `AGT-8`
8.  **Token usage logged on every model call** · *Source:* `D1`, `D3_p32`, and `SYS-8`
9.  **Nothing in `src/` imports from `ref_repo/`** · *Source:*
    [`RIX_S5.2`](../ref_index.md#52-what-version-control-tracks). The clones are git-ignored; a
    judge would get an `ImportError`
10. **No OpenPose, SLRT or SAM-SLR code, model or derivative enters `src/`** · *Source:* decisions
    16, 21, 22. They are cited, never used
11. **Never commit recorded video of a person without documented consent** · *Source:*
    [`RSK_S8.3`](RSK_risk_register.md#83-privacy-and-data-protection) `HUM-15`
12. **Capability is never overstated** · *Source:*
    [`CLD_S5.2`](../CLAUDE.md#52-honesty-about-the-product). A closed-vocabulary demonstration is
    described as one, in code comments and commit messages as well as on slides

---





# 3. THE WORK BREAKDOWN
## 3.1. Nine Work Packages
| WP  | Name                  | Pipeline stages | Tasks | Blocked by a gate |
| :-- | :-------------------- | :-------------- | ----: | :---------------- |
| WP0 | Foundations           | ---             |     6 | No                |
| WP1 | Perception            | ① ② ③           |     6 | No                |
| WP2 | Segmentation          | ④               |     4 | No                |
| WP3 | Data                  | ---             |     5 | **Yes — Q2, Q4**  |
| WP4 | Recognition           | ⑤               |     5 | Partly            |
| WP5 | The agent             | ⑥–⑩             |     8 | Partly            |
| WP6 | The reverse direction | ⑪–⑭             |     5 | Partly — Q2       |
| WP7 | Interface and demo    | ---             |     4 | No                |
| WP8 | Evaluation, submission| ---             |     7 | Partly — Q3       |

Stage numbers are [`ARC_S6.1`](ARC_architecture.md#61-pipeline)'s and are used unchanged in module
docstrings, on the architecture slide and in commit messages.




## 3.2. Dependency Order
```text
WP0 Foundations ────────────────────────────────────────────────────────────┐
  │  the frozen interfaces (T0.5) gate everything downstream                │
  ▼                                                                         │
WP1 Perception ──► WP2 Segmentation ──► WP4 Recognition ──► WP5 Agent ──► WP7 UI
  │                                        ▲                                │
  │                                        │                                │
  └──────────────► WP3 Data ───────────────┘                                │
                     ▲                                                      │
                     │ gated on ARC_S9.1 questions 2 and 4                  │
                                                                            │
WP6 Reverse direction ── independent of WP2/WP3/WP4; needs only WP0 + a lexicon
                                                                            │
WP8 Evaluation and submission ◄─────────────────────────────────────────────┘
     runs continuously from the first commit, not at the end
```

Two properties of this graph decide the schedule:

1. **WP3 is the only package with an external dependency** — people, time and consent. It is
   started first and finished last, and everything downstream of it is stubbed until it lands
2. **WP6 is off the critical path entirely.** It is a dependency (`RSS`), not a build, and it can
   be done by a second person in parallel with WP4 —
   [`ARC_S5.7`](ARC_architecture.md#57-the-reverse-direction)




## 3.3. Module Map — the Slide to the Directory
`D3_p42` states that judges check *"if presentation methodology is reflective at code level"*, and
`DEL-10` rates a mismatch `S2`/`L2`. The mapping below is therefore a **deliverable**, not a
convenience: the architecture slide is drawn from this table, and every module opens with a
docstring naming its stage.

```text
src/
├── main.py                    entry point; wires the stages, nothing else
├── config.py                  MODEL_ID, thresholds, pinned asset paths      [rule 6]
├── contracts.py               the typed payloads that cross every boundary  [T0.5]
├── telemetry.py               token counters + perception counters          [rules 8, 11]
│
├── capture/
│   ├── camera.py              bounded queue, drop-oldest, size 1        ①  [APS L7]
│   └── subject_tracker.py     largest / most central, hysteresis-held   ①  [decision 1]
├── perception/
│   ├── landmarker.py          the one interface                         ②  [decision 14]
│   ├── landmarker_holistic.py arm A — HolisticLandmarker                ②
│   ├── landmarker_split.py    arm B — Hand + Pose Landmarker            ②
│   ├── tracking_state.py      rate-limiter · handedness · identity      ②③ [rules 4–7]
│   └── normalise.py           body-normalised signing space             ③  [decision 3]
├── segment/
│   ├── base.py                the one interface                         ④  [decision 20]
│   ├── geometric.py           arm A — hysteresis + buffer-and-replay    ④
│   └── window.py              arm B — sliding window, blank class       ④
├── recognise/
│   ├── features.py            the curated subset, index-parameterised   ⑤  [decision 2]
│   ├── classifier.py          the small temporal model                  ⑤  [decision 5]
│   ├── calibrate.py           confidence calibration                    ⑤  [AGT-16]
│   └── vlm_baseline.py        P2 — frame-sampled, no training           ⑤′ [decision 9]
├── agent/
│   ├── state.py               typed graph state with reducers           ⑥–⑩
│   ├── graph.py               LangGraph wiring, loop bound in state     ⑥–⑩ [rule 5]
│   ├── assembler.py           lattice → candidate sentence              ⑥
│   ├── critic.py              reflection; can veto                      ⑦
│   ├── repair.py              the refusal path and its four actions     ⑨  [decision 8]
│   ├── adapter.py             per-signer episodic memory                ⑩
│   └── tools/
│       ├── lexicon.py         sgsl_lexicon_lookup()
│       ├── memory.py          conversation_memory()
│       └── context.py         context_hint()
├── reverse/
│   ├── glosser.py             the assembler agent, prompted             ⑪
│   ├── lookup.py              RSS coverage ladder                       ⑫  [decision 19]
│   ├── stitch.py              trim · cap · seam-match · filter          ⑬
│   └── render.py              pose skeleton, never an avatar            ⑭  [decision 23]
├── evaluate/
│   ├── metrics.py             the twelve metrics of ARC_S8.4
│   └── run_eval.py            one command, one report
└── ui/
    └── app.py                 one screen; the gloss trace is visible

data/     recordings and splits — consent-gated, size-capped   [HUM-15, DEL-11]
docs/     generated developer documentation
tests/    automated tests
```

> **Note — `main.py` currently sits at the repository root and is empty.** `T0.1` moves the entry
> point to `src/main.py`. The root file is removed rather than left as a decoy, because a judge
> following the `README` must reach the real entry point on the first attempt — `DEL-8`.




## 3.4. The Frozen Interfaces
`D5`'s one transferable engineering idea is a **stable layer boundary**: fix the contract early and
both sides can then move independently —
[`TRN_S5.3`](../doc/TRN_training_synthesis.md#53-three-transferable-ideas-from-the-physical-track).
`DEL-14` rates *"integration left to the last day"* `S3`/`L3`, and these four contracts are the
answer to it. All four live in `src/contracts.py` and are written in `T0.5`, **before** any of the
code that produces or consumes them.

1. **`Frame`** · *Produced by:* ① · *Consumed by:* ②
   *Contents:* Image buffer, capture timestamp, subject identifier, subject bounding box
2. **`LandmarkFrame`** · *Produced by:* ② · *Consumed by:* ③
   *Contents:* Per-group landmark arrays, per-point confidence, handedness label and its running
   average, a presence flag per group. **Absence is representable** — rule 8 of
   [`ARC_S6.5`](ARC_architecture.md#65-perception-engineering-rules)
3. **`FeatureWindow`** · *Produced by:* ③④ · *Consumed by:* ⑤
   *Contents:* Normalised coordinates, velocity, acceleration, the frame index range, and the
   segmenter arm that emitted it
4. **`GlossLattice`** · *Produced by:* ⑤ · *Consumed by:* ⑥
   *Contents:* Per-slot top-k glosses, calibrated confidences, timestamps, and the **provenance
   rung** of decision 19. Compact JSON. **Landmarks never appear in it** — `AGT-8`, and `D2`'s
   heavy-payload rule

> **Warning — `GlossLattice` is the boundary the AWS budget rests on.** It is what crosses from the
> local process to Bedrock. If a landmark array ever reaches it, cost per utterance rises by orders
> of magnitude and `SYS-8` becomes live —
> [`ARC_S8.2`](ARC_architecture.md#82-why-p1-fits-within-the-cap). A test asserts the serialised
> size stays under a fixed ceiling.

---





# 4. WP0 — FOUNDATIONS
Six tasks, all `S` or `M`, all unblocked. This package exists to make the remaining eight
packages cheap, and it is finished before anything else starts.




## 4.1. T0.1 — Repository Skeleton
*Stage:* --- · *Size:* S · *Depends on:* --- · *Answers:* `DEL-8`, `DEL-10`

The directory tree of [`PLN_S3.3`](#33-module-map--the-slide-to-the-directory) exists, with every
module present as a stub carrying its stage number in the docstring.

1. Create `src/`, `docs/`, `data/`, `tests/` per `D3_p23` and
   [`RDM_S6.5`](../README.md#65-required-project-structure).
2. Create every module named in [`PLN_S3.3`](#33-module-map--the-slide-to-the-directory) as a stub
   with a one-line docstring: the stage number, the decision it implements, and the `ARC` address.
3. Delete the empty root `main.py`; the entry point is `src/main.py`.
4. Extend `.gitignore`: `data/**` media, `*.task`, `*.tflite`, model checkpoints, `.env`. Verify
   each new rule with `git check-ignore -v <path>` rather than assuming it works — the ignore rules
   in this repository have already failed silently once, [`CLD_S6`](../CLAUDE.md#6-git) rule 7.
5. Commit `.env.example` with every key name and no value.

**Done when:** `tree src` matches [`PLN_S3.3`](#33-module-map--the-slide-to-the-directory) exactly,
and `git status` is clean after touching a file under `data/`.

*Read:* [`JCR_S3.3`](JCR_judging_criteria.md#33-development-best-practices) ·
[`RIX_S5.2`](../ref_index.md#52-what-version-control-tracks)




## 4.2. T0.2 — Dependencies, Pinned
*Stage:* --- · *Size:* S · *Depends on:* `T0.1` · *Implements:* decision 13 · *Answers:* `SYS-12`

A `requirements.txt` in which every version is exact, and a recorded date on which each was checked
against the live index.

The current install commands, declared packages, and deferred package candidates are maintained in
[`DEP`](DEP_dependencies.md). Its reproducibility-gap section records what remains before this task
is complete.

1. Pin `mediapipe` to an exact version. **Rule 2 of
   [`ARC_S6.5`](ARC_architecture.md#65-perception-engineering-rules) is not optional**: the
   upstream repository has already removed a public API, and almost every tutorial online uses the
   removed one.
2. Install `pose-format` **base only**. ⚠ Never the `mediapipe` extra: it pulls
   `mediapipe<0.10.30` and the legacy `mp.solutions` API, colliding with decision 13 —
   [`SPS_S4`](../doc/SPS_sign_pose_synthesis.md).
3. Add `spoken-to-signed-translation` for WP6, `boto3` and `langgraph` for WP5.
4. Record, in a comment beside each pin, the date the version was checked.
5. Download the `.task` model assets to a git-ignored path named in `config.py`; the `README`
   states how to fetch them.

**Done when:** a clean virtual environment built from `requirements.txt` imports
`mediapipe.tasks.python.vision` and `pose_format`, and `pip show mediapipe` reports the pinned
version.

*Read:* [`MPS_S6`](../doc/MPS_mediapipe_synthesis.md#6-the-four-traps-that-will-cost-a-day) ·
[`SPS_S4`](../doc/SPS_sign_pose_synthesis.md) ·
[`ARC_S7.7.2`](ARC_architecture.md#772-the-six-in-one-paragraph-each)




## 4.3. T0.3 — Configuration and Secrets
*Stage:* --- · *Size:* S · *Depends on:* `T0.1` · *Answers:* `SYS-9`, `SYS-10`, `SYS-12`

One `config.py` holding every constant that a reviewer would otherwise have to hunt for.

1. `MODEL_ID` as a **literal constant**, never assembled from parts — `D3`'s stack slide, and
   `SYS-12`.
2. `REGION`, defaulting to the workshop region `ap-southeast-1`; model access is granted per model
   **and** per region — [`RDM_S7.1`](../README.md#71-registration-and-lease).
3. Every threshold in one block: detection confidence, tracking confidence, the signing-space
   gate, the hysteresis counts, the refusal threshold, the loop cap.
4. A startup preflight that calls the model once and fails loudly with an actionable message if
   access or the region is wrong. `D1`: *"valid credentials do not guarantee a working call"*.
5. Secrets read from `.env` only.

**Done when:** every magic number in the codebase resolves to `config.py`, and running with a
missing `.env` produces a sentence a business user could act on, not a stack trace —
`D3_p23` error-handling rule.

*Read:* [`TRN_S4.6`](../doc/TRN_training_synthesis.md#46-the-taught-stack) ·
[`RSK_S6`](RSK_risk_register.md#6-system-and-platform)




## 4.4. T0.4 — Instrumentation, From the First Commit
*Stage:* ①–⑩ · *Size:* M · *Depends on:* `T0.1` · *Implements:* decision 12 · *Answers:* `SYS-8`

`telemetry.py`, wired before there is anything to measure, so that no stage is ever added without
its counter.

1. **Token accounting.** Log `usage.inputTokens` and `usage.outputTokens` on every model call, sum
   per utterance, and expose the running total — `D1`, `D3_p32` metric 4.
2. **A spend guard.** A configured ceiling below the `D6` cap that halts model calls and says so.
   `SYS-8` is a kill switch, not an invoice: at US$20 access is revoked, at US$30 the account is
   terminated — [`TRN_S6.3`](../doc/TRN_training_synthesis.md#63-the-budget).
3. **Perception counters**, in the shape of `RDH`'s exit statistics: frames with no hand, frames on
   which the palm detector ran, inferences split by detection versus tracking, failed inferences —
   rule 11 of [`ARC_S6.5`](ARC_architecture.md#65-perception-engineering-rules).
4. **Loop counters:** assembler↔critic iterations against the cap — `D3_p32` metric 5.
5. One JSON run record per session, written to a git-ignored path, consumed by `T8.2`.

**Done when:** a run with no camera attached still produces a valid run record, and the detection
rate appears in it.

*Read:* [`DHS_S3.5`](../doc/DHS_depthai_synthesis.md#35-counting-everything) ·
[`ARC_S8.3`](ARC_architecture.md#83-cost-discipline-as-a-deliverable)




## 4.5. T0.5 — The Frozen Interfaces
*Stage:* all · *Size:* M · *Depends on:* `T0.1` · *Answers:* `DEL-14`, `AGT-8`

`contracts.py`, holding the four payloads of
[`PLN_S3.4`](#34-the-frozen-interfaces) as typed structures with validation.

1. Define `Frame`, `LandmarkFrame`, `FeatureWindow` and `GlossLattice` as Pydantic models or
   `TypedDict`s — `D3`'s typed-state rule.
2. Make **absence representable** in `LandmarkFrame`. An empty result list is MediaPipe's *normal*
   output when nothing clears the presence gate, and indexing it without a check is rule 8 of
   [`ARC_S6.5`](ARC_architecture.md#65-perception-engineering-rules).
3. Carry per-point confidence everywhere, so rules 15 and 17 have something to weight by.
4. Add the provenance rung of decision 19 to every gloss slot in `GlossLattice`, on `RSS`'s
   four-state ladder.
5. Write the serialised-size test that guards the Bedrock boundary —
   [`PLN_S3.4`](#34-the-frozen-interfaces).

**Done when:** all four models round-trip through JSON, the size test passes, and every WP1–WP5
stub imports its input and output type from this file.

*Read:* [`SSS_S4`](../doc/SSS_spoken_to_signed_synthesis.md#4-the-coverage-ladder) ·
[`TRN_S5.3`](../doc/TRN_training_synthesis.md#53-three-transferable-ideas-from-the-physical-track)




## 4.6. T0.6 — The Walking Skeleton
*Stage:* ①–⑩ · *Size:* M · *Depends on:* `T0.5` · *Answers:* `DEL-14`, `DEL-6`

An end-to-end run on day one, in which every stage is a stub and the pipeline nevertheless produces
a sentence on screen from a live camera.

1. Camera → a stub landmarker returning fixed points → a stub segmenter emitting a window every two
   seconds → a stub classifier returning one hard-coded gloss with a fixed confidence → a stub
   assembler returning a fixed sentence → the screen.
2. Every stub behind the real interface from `T0.5`, so replacing it is a one-line change.
3. Run it from `python -m src.main` and from a clean clone.

**Done when:** the loop runs for five minutes without the queue growing, and each stub can be
swapped for a real implementation without touching any other file.

> **Decision:** the walking skeleton is built on day one and is never allowed to break. `DEL-14`
> rates integration-at-the-end `S3`/`L3`, and the cheapest defence is that integration was never
> deferred in the first place.




## 4.7. WP0 Exit Criteria
- [ ] `tree src` matches the module map, and every stub names its stage.
- [ ] A clean virtual environment builds from `requirements.txt` with exact pins.
- [ ] `MODEL_ID` is a constant; a preflight verifies model access in the configured region.
- [ ] A run record with token and perception counters is written on every run.
- [ ] The four contracts exist, validate, and the payload-size test passes.
- [ ] The walking skeleton runs end to end from a clean clone.

---





# 5. WP1 — PERCEPTION (STAGES ① ② ③)
Six tasks. This package is fully unblocked, is the largest body of code the team writes, and every
one of the eighteen rules in
[`ARC_S6.5`](ARC_architecture.md#65-perception-engineering-rules) lands in it.




## 5.1. T1.1 — Capture Loop and Bounded Queue
*Stage:* ① · *Size:* S · *Depends on:* `T0.6` · *Answers:* `SYS-2`, `SYS-3`, `SYS-4`

A capture thread that drops frames rather than queueing them.

1. Bounded queue, size 1, drop-oldest — `APS` lesson L7.
2. Do **not** port Apple's `DispatchQueue.main.sync` back-pressure literally; the naive Python
   equivalent stalls — `SYS-3`,
   [`APR_S4.3`](../ref_repo/tracking/apple/APR_apple_report.md#43-threading-model).
3. Record the capture timestamp on the frame, not the processing timestamp; every latency number in
   `T8.2` derives from it.
4. Log dropped-frame count to `telemetry.py`.

**Done when:** with an artificial 200 ms delay injected into the consumer, output stays ~200 ms
behind indefinitely rather than falling further behind with time.

*Read:* [`APS_S5`](../doc/APS_apple_synthesis.md#5-the-twelve-lessons) ·
[`ARC_S6.4`](ARC_architecture.md#64-latency-budget)




## 5.2. T1.2 — Subject Tracker
*Stage:* ① · *Size:* S · *Depends on:* `T1.1` · *Implements:* decision 1
*Answers:* `CAP-16`–`CAP-19`, `CNV-3`

Selection of the signer as the largest and most central detection, held with hysteresis so the
subject does not flip mid-sentence.

1. Rank detections by size and centrality. Subject selection is a **by-product of detection**, not
   a segmentation problem —
   [`ARC_S2.1`](ARC_architecture.md#21-verdict-confirmed-at-lower-cost-than-assumed).
2. Hold the choice with a hysteresis counter; contradicting evidence zeroes it — `APS` lesson L3.
3. **Build no segmentation and no background blur.** Decision 1 is explicit, and a segmentation
   error can erase a hand.
4. Emit the subject identifier on `Frame` so `CNV-2` (mis-attribution) has something to attach to
   later, even though multi-person is out of scope.

**Done when:** with two people in frame, one metre apart in depth, the tracker holds the nearer for
sixty seconds without a single switch.

*Read:* [`RSK_S2.3`](RSK_risk_register.md#23-subject-selection-and-framing) ·
[`RSK_S5`](RSK_risk_register.md#5-multi-person-and-conversation)




## 5.3. T1.3 — Landmark Extractor, Both Arms
*Stage:* ② · *Size:* L · *Depends on:* `T0.5` · *Settles:* decision 14 · *Implements:* decision 13

Two implementations of one interface, timed against each other on the demo laptop.

1. Write `landmarker.py` as the interface; both arms implement it.
2. **Arm A** — `HolisticLandmarker`. Gives the body-relative frame for free and derives handedness
   from the pose skeleton, but is hard-limited to **one person** `[S21]`.
3. **Arm B** — `HandLandmarker` + `PoseLandmarker`, configured exactly as `RST` configures them:
   `RunningMode.VIDEO`, `.task` assets by path, `output_segmentation_masks=False`, both landmarkers
   created and closed in one `with` block. It is the only correct example in `ref_repo/`, it is
   Apache 2.0, and it may be **adapted with attribution** — rule 18.
4. Import from `mediapipe.tasks.python.vision` only. `mp.solutions.hands` is excluded from the
   1.0-line wheel — rule 1, decision 13.
5. Never `IMAGE` mode: it silently disables the tracking loop and runs the palm detector on every
   call — rule 3.
6. ⚠ `RST` defaults to `pose_landmarker_heavy.task`. Measure `lite` and `full` before inheriting
   `heavy` — rule 18.

**Done when:** both arms run behind the same interface, and frames per second plus landmark quality
for one hand and for two hands are recorded for each. **That measurement is the answer to decision
14** and closes the placeholder in
[`ARC_S7.2.3`](ARC_architecture.md#723-consequences-for-the-pipeline).

*Read:* [`STS_S3`](../doc/STS_sign_translator_synthesis.md#3-the-tasks-api-done-right) ·
[`MPS_S4`](../doc/MPS_mediapipe_synthesis.md#4-the-api-in-one-page) ·
[`MPR_S7.1`](../ref_repo/tracking/google-mediapipe/MPR_mediapipe_report.md#71-holistic-landmarker)




## 5.4. T1.4 — Tracking State
*Stage:* ②③ · *Size:* M · *Depends on:* `T1.3` · *Implements:* decision 15
*Answers:* `CAP-9`, `LNG-4`

The four fixes MediaPipe does not supply and the application needs, re-implemented from `RDH`'s
readable Python with attribution.

1. **Detector rate-limiter.** With `num_hands = 2` and one hand visible, the palm detector runs on
   **every frame**. Signers drop to one hand constantly, so this is the common case — rule 4,
   [`DHS_S3.1`](../doc/DHS_depthai_synthesis.md#31-a-tolerance-counter-on-the-detector).
2. **Hand identity across frames.** MediaPipe orders hands per frame and guarantees nothing between
   frames — rule 6. Rule 5 depends on this, so the two are built together.
3. **Handedness averaging over a tracked lifetime.** Per-frame handedness flips, and because
   dominant and non-dominant hands carry different grammatical roles a flip is a **grammatical**
   error — rule 5, [`DHS_S3.2`](../doc/DHS_depthai_synthesis.md#32-handedness-averaging).
4. **Duplicate handling, but not `RDH`'s.** When two hands classify with the same handedness, keep
   both and mark handedness uncertain. **Do not drop one:** a two-handed sign seen with one hand is
   unrecognisable, which is worse than a mislabel — rule 7.
5. Attribute the re-implementation in the module docstring. `RDH` is MIT; the code is still not
   imported — constraint 9 of [`PLN_S2.4`](#24-standing-constraints-on-every-task).

**Done when:** the detection-rate counter from `T0.4` shows the palm detector running on a small
fraction of single-hand frames, and handedness does not flip across a sixty-second recording.

*Read:* [`DHS_S3`](../doc/DHS_depthai_synthesis.md#3-the-five-things-to-port) ·
[`DHS_S4`](../doc/DHS_depthai_synthesis.md#4-one-thing-not-to-copy)




## 5.5. T1.5 — The Normaliser
*Stage:* ③ · *Size:* L · *Depends on:* `T1.4` · *Implements:* decision 3
*Answers:* `MOD-11`, `CAP-8`

Body-normalised signing-space coordinates plus derived motion features, with the four
`ARC_S6.5` corrections that make them trustworthy.

1. **Confidence as a gate, not a weight.** Drop the point rather than guess it — `APS` lesson L2.
   MediaPipe emits coordinates whether or not it is confident, and `MOD-11` is the failure that
   follows.
2. **Correct the wrists first.** Holistic emits each wrist twice; when the hand model fails its
   wrist has zero confidence while the pose model's is valid, and the hand wrist is the **origin of
   the handshape descriptor** — rule 15,
   [`SPS_S3.2`](../doc/SPS_sign_pose_synthesis.md).
3. **Normalise.** `RSP`'s `Pose.normalize()` already implements decision 3's origin-and-scale step:
   shoulder midpoint to the origin, mean inter-shoulder distance to 1. ⚠ It is a **batch**
   operation computed over the whole sequence, so the live path must normalise per buffered
   utterance window or hold a running shoulder estimate. **That is a decision to make in this task,
   not an inheritance** —
   [`SPS_S3.1`](../doc/SPS_sign_pose_synthesis.md#31-normalize--already-written).
4. **Canonicalise hand rotation** with `normalize_hands_3d()`, so handshape is independent of hand
   orientation — [`ARC_S4.3`](ARC_architecture.md#43-recommended-representation).
5. **Interpolate missing hand keypoints; never pass zeros** — rule 16. ⚠ Reported by a survey; the
   underlying paper was not read.
6. **Smooth the hands and body; never the face.** A uniform filter dampens mouthing and fast brow
   movement, which is the entire reason the face is in the budget at all. Where the hands are
   filtered, `RSS` uses a zero-phase 4th-order Butterworth low-pass at **6 Hz** — ⚠ one system's
   parameter, not a measured property of sign language — rule 13.
7. **Do not treat normalised `z` as depth.** It is scaled by 0.4 × the *crop* width and is a
   within-hand ordering only — rule 9.
8. Add velocity and acceleration as **explicit derived features** rather than hoping a short window
   teaches them — [`ARC_S4.3`](ARC_architecture.md#43-recommended-representation) step 4.

> **Warning — the y-flip.** MediaPipe's normalised origin is the **top-left**; Apple's Vision origin
> is the **bottom-left**. Copying `y = 1 - y` out of `APR` into this file flips the image. Standing
> policy, [`CLD_S5.4`](../CLAUDE.md#54-working-with-the-reference-repositories) fact 2, repeated
> here because this is the file where it would happen.

**Done when:** the same sign performed at one metre and at two metres, by a tall and a short signer,
produces feature vectors whose distance is small relative to the distance between two different
signs.

*Read:* [`SPS_S3`](../doc/SPS_sign_pose_synthesis.md#3-the-five-things-to-take) ·
[`SSS_S5`](../doc/SSS_spoken_to_signed_synthesis.md#5-what-it-teaches-the-forward-direction)




## 5.6. T1.6 — Visualiser and Perception Health
*Stage:* ①–③ · *Size:* S · *Depends on:* `T1.5` · *Implements:* metric 9

A skeleton overlay and a live counter panel, wired immediately because they are the cheapest
debugging available.

1. `RSP`'s `PoseVisualizer` — `draw_on_video()` over the original footage —
   [`SPS_S3.5`](../doc/SPS_sign_pose_synthesis.md).
2. A live panel showing the counters from `T0.4`, above all **detection rate**, which is the one
   number that exposes rule 4's pathology.
3. Colour the overlay by confidence: honest hesitation shown, not hidden — `APS` lesson L5.

**Done when:** a teammate can see, without reading a log, which landmark group failed and when.




## 5.7. WP1 Exit Criteria
- [ ] Frames are dropped, never queued; the pipeline does not fall progressively behind.
- [ ] The subject is held through a sixty-second two-person scene.
- [ ] Decision 14 is **answered by a recorded measurement**, not an argument.
- [ ] The palm detector does not run on every single-hand frame.
- [ ] Handedness is stable across a recording.
- [ ] Normalised features are invariant to distance and signer size; the face is unsmoothed.
- [ ] The overlay and the counter panel run in the demo application.

---





# 6. WP2 — SEGMENTATION (STAGE ④)
Four tasks. Decision 20 requires both approaches behind one interface, and
[`ARC_S9.1`](ARC_architecture.md#91-open-questions-for-the-team) question 5 records published
evidence **against** the geometric approach. This package exists to settle that by measurement.




## 6.1. T2.1 — The Segmenter Interface
*Stage:* ④ · *Size:* S · *Depends on:* `T0.5` · *Implements:* decision 20

`segment/base.py`: one interface, two arms, one selection flag in `config.py`.

1. Input `LandmarkFrame`, output `FeatureWindow` plus an utterance-boundary event.
2. Both arms emit the same type, so `T2.4` compares them without touching downstream code.

**Done when:** the walking skeleton runs with either arm selected by a config flag alone.




## 6.2. T2.2 — Arm A: Geometry, Hysteresis, Buffer-and-Replay
*Stage:* ④ · *Size:* M · *Depends on:* `T2.1` · *Implements:* decision 6
*Answers:* `LNG-6`, `LNG-7`, `CNV-10`

The Apple state machine, ported to Python, with `RSS`'s scale-invariant signing gate.

1. **Gate by torso-normalised wrist height with hysteresis** — rule 14, which **supersedes** rule
   10's crude wrist-above-elbow test. `RSS` normalises wrist height by the signer's own
   hip-to-shoulder distance (0 at the hip, 1 at the shoulder), with a threshold of **0.15**, a
   **0.2 s** minimum duration, and a **median** over the sequence for torso length so one bad frame
   cannot move the threshold. About twenty lines, and scale-invariant, which the elbow test is not.
2. **Hysteresis before any state change**; contradicting evidence zeroes the counter — `APS` L3.
3. **Buffer while uncertain, commit retroactively.** Apple's debounce replays the buffered frames
   the moment the state commits, so the delay costs **latency, never data** — `APS` L4, and the
   single most important lesson in that repository.
4. **Staleness is a state.** Two seconds without hands is an event, not an absence — `APS` L8.
5. No model, no training data, deterministic — decision 6.

**Done when:** the first 100 ms of a sign is present in the emitted window, verified by replaying a
recording frame by frame.

*Read:* [`APS_S5`](../doc/APS_apple_synthesis.md#5-the-twelve-lessons) ·
[`SSS_S5`](../doc/SSS_spoken_to_signed_synthesis.md#5-what-it-teaches-the-forward-direction)




## 6.3. T2.3 — Arm B: Sliding Window with a Blank Class
*Stage:* ④ · *Size:* M · *Depends on:* `T2.1`, `T4.2` · *Implements:* decision 20, route R2

No segmentation at all: classify every window and recover the gloss sequence by beam search, with a
blank class absorbing the gaps.

1. Published parameters, re-implemented from the description: **16-frame window** (~640 ms at
   25 fps), **stride 1**, **beam width 10** — `RSL`'s `Online` framework, EMNLP 2024.
2. **Re-implemented, never copied.** `RSL` has **no licence file**, so no permission to copy exists
   — decision 21.
3. Costs one forward pass **per frame**, affordable only because the classifier is small.
4. ⚠ Its published training recipe needs a dictionary of isolated clips bootstrapped by cutting
   continuous video with an already-trained model — **a step this project cannot perform.** Arm B
   is therefore trained on the same clips as arm A, which is a weaker version of the published
   method and must be described as one.

**Done when:** arm B produces a gloss sequence from a continuous recording, behind the same
interface as arm A.

*Read:* [`ARC_S5.6.2`](ARC_architecture.md#562-r2--sliding-window-classifier-with-a-blank-class) ·
[`SLS_S6`](../doc/SLS_slrt_synthesis.md#6-the-architecture-worth-copying)




## 6.4. T2.4 — The Comparison That Settles It
*Stage:* ④ · *Size:* S · *Depends on:* `T2.2`, `T2.3`, `T3.4` · *Settles:* decision 20, question 5

One measurement, on the held-out split, reported whichever way it comes out.

1. Boundary agreement against hand-marked boundaries on the evaluation set.
2. End-to-end utterance accuracy with each arm, everything else held constant — `D5`'s
   *change-one-variable* discipline, [`TRN_S5.3`](../doc/TRN_training_synthesis.md).
3. Record the result in `EVL` and cite it on the evaluation slide.

> **Note — this is the highest-value slide content in the whole plan.** A stated comparison in
> which the team's first choice lost is exactly the evidence
> [`JCR_S2.3`](JCR_judging_criteria.md#23-c3--effectiveness-of-the-solution-20) rewards, and almost
> no hackathon team produces one. ⚠ A 2024 study of the Swedish Sign Language corpus reports *"no
> clear correspondence between utterance boundaries and articulatory features"* extracted with
> MediaPipe — read from a survey, one corpus, one language, and about *utterance* rather than
> *sign* boundaries, so it does not transfer straightforwardly.

**Done when:** the answer is written down, including the case where arm A loses.




## 6.5. WP2 Exit Criteria
- [ ] Both arms run behind one interface, selected by config.
- [ ] Buffer-and-replay demonstrably loses no frames at a boundary.
- [ ] The signing gate is scale-invariant, not an elbow test.
- [ ] The comparison is recorded in `EVL`, whichever arm wins.

---





# 7. WP3 — DATA
Five tasks, and the **critical path**. `MOD-1` and `MOD-2` are both `S3`/`L3`: there is no public
SgSL corpus, and anything recorded in four days is a handful of signers in one room. This package
cannot start until questions 2 and 4 of
[`ARC_S9.1`](ARC_architecture.md#91-open-questions-for-the-team) are answered.




## 7.1. T3.1 — The Vocabulary
*Stage:* --- · *Size:* M · *Depends on:* question 2 · *Implements:* decision 4 · *Answers:* `DEL-2`,
`MOD-8`

An explicit, written gloss list, sized from the field's own accuracy curve.

1. Write the list. Decision 4 gives the register — informal conversation between two individuals —
   and the list gives the bound. **The setting is not the bound**;
   [`PLN_S2.1`](#21-what-is-decided) explains why.
2. Size it in the **low hundreds at most**. One CVPR 2023 system, one method, four vocabulary sizes:
   top-1 accuracy falls from **92.64%** at 100 signs to **61.26%** at 2,000, monotonically and
   steeply — [`ARC_S5.2`](ARC_architecture.md#52-state-of-the-art). Closing the vocabulary is where
   the field's accuracy lives.
3. State the ceiling honestly in the same document: this project's smaller model on its own data
   will sit **below** 92.6%, and the deck says so — `HUM-5`.
4. Include the **repair phrases** the system itself needs: *say that again*, *spell it*, *yes*,
   *no*. Stage ⑨ is useless if the signer cannot answer it.
5. Write down the grammar alongside: word order, dropped function words, ambiguous words. This is
   linguistic work, not engineering, and it is the natural artefact of `T8.3` —
   [`STS_S5`](../doc/STS_sign_translator_synthesis.md#5-the-data-collection-protocol).

**Done when:** the list exists as a file under `data/`, every entry has a unique gloss token, and
the count is stated on the evaluation slide.

*Read:* [`SLS_S3`](../doc/SLS_slrt_synthesis.md#3-the-number-that-decides-the-vocabulary) ·
[`LTS_S6`](../doc/LTS_signlang_literature_synthesis.md#6-the-gloss-question)




## 7.2. T3.2 — Recording Protocol and Consent
*Stage:* --- · *Size:* M · *Depends on:* `T3.1`, question 4
*Answers:* `HUM-15`, `MOD-7`, `HUM-13`, `MOD-3`

A written protocol and a signed consent form, both completed **before** the camera is switched on.

1. **Consent first.** Sign-language video is identifying **by definition** — the face is part of the
   linguistic signal and cannot be removed, so standard anonymisation deletes the data
   (`HUM-10`). Recording teammates is easy; documenting consent is easy to skip, and `CLD_S6` rule
   3 forbids committing such video without it.
2. State retention and deletion, against PDPA-shaped obligations — `HUM-13`.
3. **Record more people, fewer repetitions each.** *"Diverse performers to capture all accents"* is
   the signer-generalisation problem written as a recording instruction —
   [`STS_S5`](../doc/STS_sign_translator_synthesis.md#5-the-data-collection-protocol),
   [`LTS_S3.1`](../doc/LTS_signlang_literature_synthesis.md#31-split-by-signer-not-at-random).
4. **Capture variation for the same concept.** Two signers may sign one concept differently and both
   be correct; one canonical clip per gloss produces a classifier that rejects the second signer.
5. Vary lighting, distance, clothing and background **during collection**, not only during testing —
   `MOD-15`, and `D3_p35`'s robustness metric.
6. ⚠ The published protocol assumes multiple synchronised cameras. **One camera, several people,
   several repetitions and a signer-held-out split is the achievable subset**, and the deck says so.

> **Warning — record fluent signing, not only citation forms.** `RSS`'s source notes that
> citation-form dictionary signs run *"~12-15x longer than the same sign in fluent signing (mostly
> preparation, holds and retraction)"*, and caps stitched signs at **0.8 s**. ⚠ That figure is an
> uncited source comment, not a measurement — but the direction is the risk: a classifier trained
> on isolated clips and tested on fluent signing does not see the distribution it is tested on.
> **Record both a dictionary pass and a connected-speech pass** —
> [`SSS_S6`](../doc/SSS_spoken_to_signed_synthesis.md#6-the-number-that-changes-data-collection).

**Done when:** a signed consent record exists for every person who will appear in `data/`, and the
protocol is a file another person could execute unaided.




## 7.3. T3.3 — Capture Sessions
*Stage:* --- · *Size:* XL · *Depends on:* `T3.2`, `T1.6` · *Answers:* `MOD-2`, `MOD-6`

The recordings themselves, captured **through the project's own pipeline** so that training and
inference share one preprocessing path.

1. Record landmarks, not only video: capture with `T1.3`'s landmarker so no train/inference skew is
   introduced. Store as `.pose`, the format both directions share.
2. Keep the raw video only where consent covers it, and keep it out of git — `DEL-11`'s 5 GB limit
   applies to the submission, and `HUM-15` to the footage.
3. Log per-clip metadata: signer ID, session, lighting, distance, dominant hand.
4. ⚠ **A hearing team's guess at a sign is not a label.** Sign annotation requires fluency, and a
   hearing team labelling from video makes errors that correlate with the hardest cases —
   `MOD-4`, and `D5`'s *"a review queue is not ground truth"*.

**Done when:** every gloss in `T3.1` has clips from at least three signers, and at least one whole
signer has been recorded and **not** used in training.




## 7.4. T3.4 — Splits, by Signer
*Stage:* --- · *Size:* S · *Depends on:* `T3.3` · *Implements:* decision 24 · *Answers:* `MOD-3`

Train, validation and test partitioned by **person**, never at random.

1. Hold out whole signers. A random split of self-recorded data measures **signer-dependent**
   recognition, and will make the demo worse than the slide —
   [`ARC_S8.4`](ARC_architecture.md#84-proposed-metric-set) metric 10.
2. Report seen-signer and held-out-signer accuracy **separately**, always both.
3. Freeze the split in a committed manifest, so no later run quietly re-splits.

**Done when:** the manifest exists, and `run_eval.py` refuses to run without it.

*Read:* [`LTS_S3.1`](../doc/LTS_signlang_literature_synthesis.md#31-split-by-signer-not-at-random)




## 7.5. T3.5 — Augmentation
*Stage:* --- · *Size:* S · *Depends on:* `T3.4` · *Answers:* `MOD-2`, `MOD-18`

`RSP`'s augmentation applied to the training split only.

1. `augment2d(rotation_std, shear_std, scale_std)` for affine perturbation.
2. **`frame_dropout_*` is the more valuable of the two here**, because it simulates the failure the
   pipeline actually has: MediaPipe returning nothing on some frames because the presence gate
   rejected them. A classifier trained with frame dropout has seen gaps before —
   [`SPS_S3.4`](../doc/SPS_sign_pose_synthesis.md).
3. `interpolate_fps()` if clips come from more than one camera.
4. Augment **after** the split, never before — augmented copies of a test clip in the training set
   is `MOD-3` by another route.

**Done when:** training runs with augmentation on and off are both recorded, so its effect is a
measurement rather than an assumption.




## 7.6. WP3 Exit Criteria
- [ ] The gloss list is written, bounded, and its size is on a slide.
- [ ] Consent is documented for every recorded person, before recording.
- [ ] Both a dictionary pass and a connected-speech pass exist.
- [ ] At least three signers per gloss, with at least one signer entirely held out.
- [ ] The split manifest is committed and enforced.

---





# 8. WP4 — RECOGNITION (STAGE ⑤)
Five tasks. This is the **only trained component in the project**, and it is not an LLM —
decision 5, [`ARC_S5.4`](ARC_architecture.md#54-corrections-to-scr--issues).




## 8.1. T4.1 — Feature Assembly
*Stage:* ⑤ · *Size:* M · *Depends on:* `T1.5` · *Implements:* decision 2

The curated subset of [`ARC_S3.2`](ARC_architecture.md#32-the-landmark-budget), assembled from an
**index list held in config** rather than hard-coded.

1. Hands: 21 per hand, both hands — 42 points.
2. Handedness: one label per hand, from `T1.4`'s running average.
3. Upper-body pose: shoulders, elbows, wrists, hips — approximately 11 of 33.
4. Face: a curated brow subset (syntactic and prosodic markers) and a curated mouth subset (lexical
   and morphological markers, including mouthing).
5. **The remaining ~400 face points are excluded as a model input.** Passing 543 × 3 floats per
   frame into a classifier trained on a small dataset is a reliable way to overfit — decision 2.
6. Parameterise by index list, so a narrower budget is a config change and not a rewrite —
   [`PLN_S2.1`](#21-what-is-decided).

> **Placeholder — the exact face indices.**
> **Missing:** the specific MediaPipe face-mesh indices for the brow and mouth subsets. `ARC`
> specifies *"a small subset"* for each and does not enumerate them; the published budgets that do
> enumerate belong to decision 17, which the team **rejected**.
> **Update trigger:** the first training run, which needs a concrete list.
> **Owner:** team, with the assistant. Record the chosen indices in `EVL` and in `config.py`.

**Done when:** the feature dimension is printed at startup, and changing the index list changes it
without touching any other file.




## 8.2. T4.2 — The Classifier
*Stage:* ⑤ · *Size:* L · *Depends on:* `T4.1`, `T3.4` · *Implements:* decision 5
*Answers:* `MOD-17`

A small temporal model over the feature sequence, closed vocabulary, top-k output, trainable in
hours on a laptop.

1. Small by design. The dimensionality argument is the whole reason for the pose representation: a
   pose vector is under 150 numbers against over 786,000 pixel-level features in a 512×512 frame,
   which is why pose models train fast on small data —
   [`ARC_S4.1`](ARC_architecture.md#41-verdict-right-instinct-over-specified).
2. Emit **top-k with per-class scores**, never a bare argmax. Top-5 stays high while top-1 collapses
   — the right sign is usually *in the candidate set*, which is what stages ⑤ and ⑨ are built on.
3. Handle variable sign duration; a fixed window truncates long signs and pads short ones with their
   neighbours — `MOD-17`.
4. ⚠ MediaPipe Model Maker ships a frozen `gesture_embedder` that may serve as a landmark feature
   stage; **its input format is unverified** —
   [`MPR_S7.4`](../ref_repo/tracking/google-mediapipe/MPR_mediapipe_report.md#74-model-maker).
   Timebox any attempt to use it and fall back to training from features directly.
5. Train from the frozen split only, and log every run.

**Done when:** held-out-signer top-1 and top-5 are recorded, and the model loads and runs inside the
pipeline at the latency budget of
[`ARC_S6.4`](ARC_architecture.md#64-latency-budget) — ≤ 50 ms per window.




## 8.3. T4.3 — Confidence Calibration
*Stage:* ⑤ · *Size:* M · *Depends on:* `T4.2` · *Answers:* `AGT-16`, `MOD-16`, `AGT-17`

A confidence number that means something, because every honesty mechanism in the design rests on
it.

1. **A softmax output is not a probability.** `MOD-16` and `AGT-16` are both `S3`/`L3` and they
   compound: without a calibrated notion of *unsure* there is nothing to threshold on and no basis
   to refuse.
2. Calibrate on the validation split — temperature scaling is the cheap standard — and plot a
   reliability curve.
3. Choose the refusal threshold **from the curve**, not by taste. `AGT-17`: too high and the system
   constantly asks for repeats; too low and it fabricates. There is no safe default.
4. Record both error directions at the chosen threshold; they become metric 4, *refusal precision*.

**Done when:** the reliability curve exists, the threshold is in `config.py` with the curve cited
beside it, and the number appears in `EVL`.

*Read:* [`RSK_S7.4`](RSK_risk_register.md#74-confidence-and-honesty)




## 8.4. T4.4 — The Lattice, with Provenance
*Stage:* ⑤ · *Size:* S · *Depends on:* `T4.3` · *Implements:* decision 19

`GlossLattice` populated for real, every slot carrying **how the gloss was obtained**.

1. The four rungs, forward-facing: *classifier, high confidence* / *top-k, signer-confirmed* /
   *fingerspelled* / *unresolved* — the forward analogue of `RSS`'s coverage ladder.
2. Compact JSON only. Landmarks never cross this boundary — `AGT-8`.
3. This makes refusal precision measurable **per token** rather than per utterance —
   [`ARC_S8.4`](ARC_architecture.md#84-proposed-metric-set) metric 11.

**Done when:** a printed lattice from a real utterance shows a rung on every slot, and the size test
from `T0.5` still passes.

*Read:* [`SSS_S4`](../doc/SSS_spoken_to_signed_synthesis.md#4-the-coverage-ladder)




## 8.5. T4.5 — P2, the Zero-Training Baseline
*Stage:* ⑤′ · *Size:* M · *Depends on:* `T2.2`, `T5.8` · *Implements:* decision 9
*Answers:* `DEL-15`

Sample k keyframes from an utterance window, send them plus a landmark summary to a multimodal
model, and ask for the sign. Built in an afternoon, kept for three reasons.

1. It is a **live fallback** if the classifier is not ready on demo day — `DEL-15`.
2. It is a **measured baseline**: *the zero-training approach scored X, the trained pipeline scored
   Y* is precisely the evidence
   [`JCR_S5`](JCR_judging_criteria.md#5-evaluation-and-metrics) asks for, and almost no team
   produces it.
3. It costs almost nothing to keep.

⚠ Claude models on Bedrock accept **images, not video**, so P2 is necessarily frame-sampling and
will struggle with fast movement. That is a limitation to **measure**, not to assert —
[`ARC_S7.4`](ARC_architecture.md#74-p2--rationale-for-building-it-regardless). Its token cost is
higher than P1's, so it stays utterance-triggered and is watched by the `T0.4` spend guard.

**Done when:** P2 runs from the same `FeatureWindow` as P1 and its accuracy sits beside P1's in the
same table.




## 8.6. WP4 Exit Criteria
- [ ] The feature budget is decision 2's, parameterised by index list.
- [ ] The classifier emits calibrated top-k, within the 50 ms budget.
- [ ] A reliability curve exists and the refusal threshold derives from it.
- [ ] Every gloss slot carries a provenance rung.
- [ ] P2 runs and its number sits beside P1's.

---





# 9. WP5 — THE AGENT (STAGES ⑥–⑩)
Eight tasks. Stages ①–⑤ are **not agentic** and the submission should say so — the agency is here,
and `D3_p10`'s test (*"what would a fixed workflow miss?"*) is answered at ⑥, ⑦, ⑨ and ⑩ —
[`ARC_S6.2`](ARC_architecture.md#62-where-agentic-ai-earns-its-place).




## 9.1. T5.1 — Typed Graph State
*Stage:* ⑥–⑩ · *Size:* S · *Depends on:* `T0.5` · *Answers:* `AGT-8`, `AGT-6`

`agent/state.py`: a typed state with reducers, holding everything heavy so no prompt has to.

1. Pydantic or `TypedDict`, with reducers where nodes write concurrently — `D3`'s stack slide.
2. Hold the lattice, the conversation history, the per-signer memory and **the loop counter** in
   state.
3. Heavy payloads live here; prompts carry metadata or references — `D2`, and `AGT-8`.

**Done when:** no prompt in the codebase interpolates anything larger than a lattice.




## 9.2. T5.2 — The Graph
*Stage:* ⑥–⑩ · *Size:* M · *Depends on:* `T5.1` · *Answers:* `AGT-6`, `AGT-7`

LangGraph wiring for ⑥ → ⑦ → (⑧ | ⑨) → ⑩, with the loop bound enforced in code.

1. **The iteration cap ignores the model's judgement.** `D3_p22`: *"A refine loop that exits when
   the critic is satisfied will sometimes never be satisfied, and we discover it from the bill."*
2. Short, single-purpose nodes that do one job and exit — the standing answer to context rot.
3. `InMemorySaver` plus a `thread_id` carries the conversation —
   [`TRN_S4.6`](../doc/TRN_training_synthesis.md#46-the-taught-stack).
4. `allowed_tools` is an allow-list and a **security boundary**; the agent cannot call anything off
   it.

**Done when:** a forced-disagreement test drives the assembler↔critic loop to the cap and the graph
exits cleanly, with the count in the run record.




## 9.3. T5.3 — The Assembler
*Stage:* ⑥ · *Size:* M · *Depends on:* `T5.2`, `T4.4`
*Answers:* `AGT-1`, `AGT-2`, `AGT-3`, `MOD-5`

The node that turns a confidence-scored lattice into a candidate sentence, and is explicitly
forbidden from inventing content.

1. **A gloss is not a word.** Treating a gloss sequence as a sentence produces confident nonsense —
   `MOD-5`. The prompt says so, in those terms.
2. Forbid completion of an unfinished utterance — `AGT-2` — and forbid filling gaps from what people
   usually say — `AGT-3`. Both are `S3`.
3. Output a structured object, never free text; schema validation pass rate is `D3_p32` metric 1
   and `AGT-10` is the failure it catches.
4. The prompt is a file, versioned, not a string literal buried in code.

**Done when:** given a lattice with a deliberately missing slot, the assembler marks the gap rather
than bridging it.




## 9.4. T5.4 — The Tools
*Stage:* ⑥ · *Size:* M · *Depends on:* `T5.2`, `T3.1` · *Answers:* `AGT-9`, `AGT-13`, `AGT-14`

`sgsl_lexicon_lookup()`, `conversation_memory()` and `context_hint()`, written as prompt text.

1. **Descriptions are the interface.** A tool docstring is the highest-leverage prompt text in the
   system, and a vague one produces an unused tool or a badly called one — `D3_p22`, `AGT-9`.
2. Return **small typed results**, never page dumps — `D3_p22`, and `AGT-8`.
3. **Retrieved lexicon content is data, never instruction.** Anything injected into a prompt from a
   store is a possible instruction channel — `AGT-13`.
4. Word-sense keys. A lexicon indexed by written word cannot distinguish
   `"spring(water-spring)"` from `"spring(metal-coil)"`; keys are `word + sense`, and the agent
   disambiguates because it holds the conversation context —
   [`STS_S4`](../doc/STS_sign_translator_synthesis.md#4-the-word-sense-gap).

**Done when:** tool-call success rate is measurable (`D3_p32` metric 2) and each description has
been read aloud by someone who did not write it.




## 9.5. T5.5 — The Critic
*Stage:* ⑦ · *Size:* M · *Depends on:* `T5.3` · *Answers:* `AGT-4`, `AGT-5`

A separate agent, with a separate prompt, that can veto the assembler's sentence.

1. One question: *is this supported by the glosses, or was it invented?* — `D3`'s reflection
   pattern, case study 2,
   [`TRN_S4.4`](../doc/TRN_training_synthesis.md#44-the-four-case-studies).
2. ⚠ **Two calls to the same model share the same priors and the same blind spots**, so a
   reflection loop can produce confidence without adding information — `AGT-5`. Constrain the critic
   to checking each output token against a lattice slot, which is a mechanical check rather than a
   second opinion.
3. Separate agents with separate prompts — `D3_p22`'s single-purpose rule.

**Done when:** a hand-written sentence containing a word with no supporting gloss is rejected.




## 9.6. T5.6 — The Repair Path
*Stage:* ⑨ · *Size:* M · *Depends on:* `T5.5`, `T4.3` · *Implements:* decision 8
*Answers:* `AGT-1`, `AGT-18`, `CNV-8`

**The single most important task in this plan.** Below the threshold, the system does not emit a
sentence; it plans a repair action.

1. Four actions, chosen between rather than fixed: ask for a repeat · request fingerspelling ·
   offer top-k for the signer to pick · escalate to a human interpreter.
2. **This is where the agency is.** A fixed pipeline emits its best guess every time; this system
   decides *between* actions based on the shape of its own uncertainty —
   [`ARC_S6.2`](ARC_architecture.md#62-where-agentic-ai-earns-its-place).
3. **Communicate uncertainty to the hearing listener too**, not only to the signer. `AGT-18` is
   `S3`: a listener who hears a fluent sentence cannot tell it was a guess, and `HUM-8` adds that
   they will trust the caption over the person.
4. The repair must be answerable in-language: the vocabulary from `T3.1` includes the phrases the
   signer needs to reply.

> **Decision — this path is never cut.** [`PLN_S13.4`](#134-descoping-order) removes work in a
> stated order; stage ⑨ is not in it. Decision 8 is a **design invariant**, not a tuning choice —
> [`CLD_S5.2`](../CLAUDE.md#52-honesty-about-the-product).

**Done when:** a deliberately low-confidence utterance produces a repair action and **no sentence**,
and the demo shows this happening.




## 9.7. T5.7 — The Adapter
*Stage:* ⑩ · *Size:* M · *Depends on:* `T5.2` · *Answers:* `AGT-15`, `HUM-14`

Per-signer episodic memory: corrections, preferred variants, personal signs.

1. Within a conversation first; across sessions only if time allows —
   [`PLN_S13.4`](#134-descoping-order) item 1.
2. **Learn only from confirmed corrections.** Personalisation that learns from a mis-recognition the
   user did not correct degrades over time, invisibly, for that user alone — `AGT-15`.
3. State retention and offer deletion — `HUM-14`.
4. This is the *adapts* leg of `D3`'s planning/acting/adapting test, and the literature names the
   shift *"from signer-independent to signer-adaptive systems"* as a needed paradigm shift.

**Done when:** a correction made once is honoured for the rest of the conversation, and the run
record shows it.




## 9.8. T5.8 — Bedrock Access and the Cost Guard
*Stage:* ⑥–⑩ · *Size:* S · *Depends on:* `T0.3`, `T0.4`
*Answers:* `SYS-8`, `SYS-9`, `SYS-11`, `SYS-13`

The connection to Bedrock, and the machinery that stops it ending the project.

1. **The lease is applied for before any of this**, because approval takes **up to two working
   days** and the approval email *"is highly likely to land in your spam box"* —
   [`TRN_S6.2`](../doc/TRN_training_synthesis.md#6-d6--aws-access-and-budget). This is the longest
   lead time in the plan.
2. Claude Haiku 4.5 as the default; escalate only if measurably wrong — `D1`'s own guidance.
3. **The agent is invoked once per utterance, never per frame** — decision 7. This is what keeps
   both latency and cost tractable, cutting calls by roughly three orders of magnitude.
4. Prompt caching on the stable system prompt; `D1` notes cache reads billed *"at up to 90% less"*.
5. **One named person owns the lease and watches the spend** — `SYS-11`, one shared account.
6. Tear down anything created: `D2` warns that `destroy` leaves S3 buckets, ECR repositories and
   CloudWatch log groups behind, spending silently — `SYS-13`.
7. `aws sso login` each morning; sessions expire after 8–12 hours — `SYS-10`.

> **Warning.** ⚠ The `$1 in / $5 out per million tokens` figure for
> `global.anthropic.claude-haiku-4-5-20251001-v1:0` is what the hackathon's own deck states.
> Bedrock is partner-operated and priced separately from Anthropic's first-party API; the
> authoritative figures are on the AWS Bedrock pricing page. **Verify before quoting on a slide** —
> [`ARC_S8.2`](ARC_architecture.md#82-why-p1-fits-within-the-cap).

**Done when:** the preflight passes in the configured region, a full utterance round trip is logged
with its token cost, and the spend guard has been tested by lowering the ceiling.




## 9.9. WP5 Exit Criteria
- [ ] The loop cap is enforced in code and its count appears in the run record.
- [ ] No prompt carries a payload larger than a lattice.
- [ ] The critic can and does veto.
- [ ] A low-confidence utterance produces a repair action and no sentence.
- [ ] Uncertainty is communicated to both parties, not only the signer.
- [ ] Token cost per utterance is logged, and the spend guard has been exercised.

---





# 10. WP6 — THE REVERSE DIRECTION (STAGES ⑪–⑭)
Five tasks. **This half is a dependency, not a build** — decision 18, and
[`ARC_S5.7`](ARC_architecture.md#57-the-reverse-direction). It answers `CNV-6`, the third-ranked
risk in [`RSK_S10`](RSK_risk_register.md#10-top-ten-risks), which is a structural criticism of the
product concept rather than of its implementation: without a return channel, this system has the
same shape as the gloves it rejects.




## 10.1. T6.1 — Install and Smoke Test
*Stage:* ⑪–⑭ · *Size:* S · *Depends on:* `T0.2`

`spoken-to-signed-translation` installed and producing a `.pose` file from a sentence.

1. MIT, five dependencies, CPU-only, published at AT4SSL 2023 and deployed behind `sign.mt`.
2. Run its own pipeline end to end on a shipped lexicon before touching the project's.

**Done when:** a sentence in, a `.pose` file out, on the demo laptop, with no GPU.




## 10.2. T6.2 — The Lexicon
*Stage:* ⑫ · *Size:* M · *Depends on:* `T6.1`, `T3.3` · *Answers:* `AGT-14`

The project's own lexicon, built from the same recordings as the forward direction.

1. One `.pose` clip per gloss, keyed by `word + sense` — `T5.4` item 4.
2. `RSP`'s `.pose` format is shared with the forward direction, which is why the two halves compose
   rather than merely coexist.
3. **It cannot fabricate a sign.** Every output is a retrieved clip or a spelled letter; there is no
   generative step. This is decision 8's invariant enforced by **architecture** rather than by
   threshold.

**Done when:** every gloss in `T3.1` resolves through the lexicon, and the coverage report shows
which rung each landed on.




## 10.3. T6.3 — Fingerspelling
*Stage:* ⑫ · *Size:* M · *Depends on:* question 2 · *Answers:* `MOD-8`

The fingerspelling fallback, which is the **default** path in `RSS`, not an error path.

1. If ASL: the alphabet ships. If SgSL: **it does not.** `RSS` ships alphabets for twenty sign
   languages and `sls` is not among them, nor is any Southeast Asian sign language.
2. Recording 26 handshapes is **the cheapest data-collection task in the entire plan** and an
   achievable deliverable in its own right —
   [`SSS_S4`](../doc/SSS_spoken_to_signed_synthesis.md#4-the-coverage-ladder).
3. It is also what gives the closed vocabulary an honest edge: a word outside the list is spelled
   rather than guessed.

**Done when:** a word absent from the lexicon is spelled, and the coverage report marks it
`FINGERSPELLING_BACKUP`.




## 10.4. T6.4 — The Glosser
*Stage:* ⑪ · *Size:* S · *Depends on:* `T6.2`, `T5.3`

The assembler agent, prompted with the closed vocabulary and asked for the word sense.

1. Reuse the agent rather than adding a second one; `RSS` supports an LLM glosser behind a flag —
   [`SSS_S3.2`](../doc/SSS_spoken_to_signed_synthesis.md#32-the-llm-glosser).
2. Ask for `word + sense`, closing the ambiguity gap `RSS` leaves open — the project's answer is
   cheap and already in the architecture, because the agent holds the conversation context.
3. ASR in front of it is off-the-shelf and is not a project deliverable.

**Done when:** a spoken sentence produces a gloss sequence whose senses are explicit.




## 10.5. T6.5 — Stitch and Render
*Stage:* ⑬⑭ · *Size:* S · *Depends on:* `T6.2` · *Implements:* decision 23
*Answers:* `CNV-7`, `HUM-16`

Trim, cap, seam-match, filter and hide idle hands; then render a **skeleton**.

1. Cap sign duration; citation-form clips are far longer than fluent signing and a naive stitch runs
   far too long — the 0.8 s default, ⚠ from a source comment.
2. **Filter the hands, never the face** — the same rule 13 that governs the forward direction.
3. Weight seam distance by the **product** of the two confidences and exclude the face from any
   whole-body distance: it is most of the points and it barely moves — rule 17.
4. **Render a pose skeleton, never a photorealistic avatar.** `RSS`'s video renderer needs a
   pix2pix model the project does not need, and *"an avatar that looks almost-human is a worse
   product than a skeleton that obviously is not"* — decision 23.
5. Place the output where the signer can see it. A translation the speaker cannot check is a
   translation they cannot correct — `CNV-7`; and the system's own feedback must be **visual**,
   because audio output is useless to the deaf user — `HUM-16`.

**Done when:** a hearing person's reply is rendered as a skeleton the signer can read, on the same
screen as the forward output.




## 10.6. WP6 Exit Criteria
- [ ] `RSS` runs on CPU and emits `.pose`.
- [ ] The lexicon covers the vocabulary, keyed by word and sense.
- [ ] Fingerspelling works and is marked as such in the coverage report.
- [ ] Output is a skeleton, positioned where the signer can see it.
- [ ] Nothing in this package is trained.

---





# 11. WP7 — INTERFACE AND DEMO
Four tasks. `DEL-6` (fragile live demo) is `S3`/`L3` and `DEL-15` (no fallback) is `S3`/`L2`; both
are answered here rather than on the morning of the deadline.




## 11.1. T7.1 — One Screen
*Stage:* --- · *Size:* M · *Depends on:* `T5.6`, `T1.6` · *Answers:* `DEL-6`, `HUM-16`

A zero-chrome demonstration: one screen, one capability, nothing to break on stage — `APS` L11.

1. Camera preview with the skeleton overlay, the current output, and the repair prompt when one is
   active.
2. Both directions on one screen, so the conversation is visible as a conversation.
3. The system's own feedback is visual throughout — `HUM-16`.
4. **Show the machine hesitating.** Honesty as a UI feature, not an error state — `APS` L5.

**Done when:** a person who has never seen the system can follow a two-turn conversation on it
without narration.




## 11.2. T7.2 — The Gloss Trace
*Stage:* --- · *Size:* S · *Depends on:* `T7.1`, `T4.4` · *Answers:* `AGT-19`, `AGT-18`

The provenance ladder, on screen, colour-coded.

1. Per-token provenance, visible: *classifier, high confidence* / *top-k, signer-confirmed* /
   *fingerspelled* / *unresolved*.
2. **The trace is what makes the system auditable rather than oracular** —
   [`ARC_S7.3`](ARC_architecture.md#73-p1--the-recommendation-in-detail) item 8.
3. ⚠ `AGT-19`: a confidence number nobody reads is not a safeguard. The trace must change what the
   user *does*, which is why it sits next to the repair action rather than in a corner.

**Done when:** every displayed sentence can be traced token by token to the evidence behind it.




## 11.3. T7.3 — The Fallback Recording
*Stage:* --- · *Size:* S · *Depends on:* `T7.1` · *Answers:* `DEL-15`, `DEL-6`, `SYS-7`

A recorded run of the working pipeline, refreshed whenever the pipeline improves.

1. Record it the first day anything works end to end, not the last.
2. Re-record after each significant improvement; the newest good recording is always available.
3. It also covers `SYS-7`: the agent stage needs connectivity, and venue Wi-Fi is a genuine
   demo-day risk.

**Done when:** a recording exists that could be shown if every live component failed, and its date
is newer than the last significant change.




## 11.4. T7.4 — The Robustness Pass
*Stage:* --- · *Size:* M · *Depends on:* `T7.1`
*Answers:* `DEL-7`, `MOD-15`, `CAP-1`, `CAP-3`, `CAP-5`

Re-test under changed lighting, distance, clothing, background and **signer** — `D3_p35` metric 5.

1. **A judge asking to try it is the fastest way to discover the demo works only for one team
   member** — `DEL-7`, `S3`/`L2`. Test it on someone who did not build it, before that happens.
2. Include the failure conditions `RSK_S2` catalogues: low light, backlight, out-of-frame signing
   above the head, motion blur.
3. Record the results as numbers, not impressions; they are metric 8.

**Done when:** the system has been run by at least one person outside the team, in at least two
lighting conditions, and the results are written down.




## 11.5. WP7 Exit Criteria
- [ ] One screen, both directions, no chrome.
- [ ] Every sentence is traceable token by token, on screen.
- [ ] A current fallback recording exists.
- [ ] The system has been driven by someone who did not build it.

---





# 12. WP8 — EVALUATION AND SUBMISSION
Seven tasks. This package **runs from the first commit**, not at the end: `D3_p42` requires testing
and evaluation to appear **in the slides**, and `DEL-9` rates the omission `S2`/`L2` as *"an
explicit, easily-avoided point loss"*.




## 12.1. T8.1 — Write `EVL`
*Stage:* --- · *Size:* M · *Depends on:* `T0.4` · *Answers:* `DEL-9`, `MOD-12`

The evaluation protocol, as its own registered document — `plan/EVL_eval_protocol.md`,
[`RIX_S2.2`](../ref_index.md#22-planned-documents).

1. The twelve metrics of [`ARC_S8.4`](ARC_architecture.md#84-proposed-metric-set), each with its
   measurement procedure.
2. The test set, the split rule, and the conditions under which each number was produced.
3. **Justify the methodology.** `D3_p24` asks for it explicitly, and *"are Agentic AI results always
   Yes/No?"* is the question the justification answers.
4. ⚠ **Do not quote literature accuracies as expected performance.** Reported ranges are on
   curated, isolated-sign, studio-recorded benchmarks and continuous real-world signing is much
   harder — `MOD-12`.
5. If BLEU is reported at all, compute it with **SacreBLEU**, publish the metric signature, and
   compare against nothing computed by an unknown procedure — metric 12.

**Done when:** `EVL` is registered in [`RIX_S2`](../ref_index.md#2-document-registry) and every
metric in it has a procedure a second person could follow.




## 12.2. T8.2 — The Metric Harness
*Stage:* --- · *Size:* M · *Depends on:* `T8.1`, `T3.4` · *Answers:* `MOD-15`, `AGT-11`

`src/evaluate/run_eval.py`: one command, one report, reproducible.

1. Reads the frozen split manifest and refuses to run without it.
2. Emits every metric in `EVL`, including **held-out-signer accuracy reported separately** —
   decision 24.
3. Emits the perception counters and the token cost per run alongside the accuracy numbers, so cost
   discipline is a **deliverable** and not a claim —
   [`ARC_S8.3`](ARC_architecture.md#83-cost-discipline-as-a-deliverable).
4. ⚠ Agent output is non-deterministic — *"the same input may therefore yield a different answer on
   a second attempt"* (`AGT-11`) — so report over repeated runs, not a single one.
5. Save the report as an **evidence package**: the run record, the numbers, and a replayable path —
   `D5`'s discipline,
   [`TRN_S5.3`](../doc/TRN_training_synthesis.md#53-three-transferable-ideas-from-the-physical-track).

**Done when:** `python -m src.evaluate.run_eval` produces the table that goes on the evaluation
slide.




## 12.3. T8.3 — The Deaf Reviewer Session
*Stage:* --- · *Size:* M · *Depends on:* `T7.1` · *Implements:* decision 11 · *Answers:* `HUM-1`,
`HUM-2`, `HUM-3`

At least one Deaf or hard-of-hearing person sees the prototype before submission.

1. `HUM-1` is `S3`/`L3` and is **a rare case where the ethical risk and the scoring risk are
   literally the same risk**: the literature reports that *"research in this domain is performed
   mostly by computer scientists in isolation"*, and `D3_p7` calls the same thing **"The
   Comfortable Guess"**.
2. It answers [`JCR_S4.4`](JCR_judging_criteria.md#44-five-pressure-test-questions) question 3 —
   *"would that person recognise themselves?"*
3. Book it **early**. It is the only task in this plan whose lead time is another person's calendar,
   and it cannot be compressed on the last day.
4. Record what was said, including what was criticised, and act on at least one item.

**Done when:** the session has happened, the notes exist, and one concrete change traceable to it
has been made.




## 12.4. T8.4 — The Clean-Clone Run
*Stage:* --- · *Size:* S · *Depends on:* `T7.1` · *Answers:* `DEL-8`

The prototype runs from a fresh clone following only the `README`.

1. `D3_p42`: judges check *"whether solution can run as demonstrated in video"*.
2. A `README` covering (a) how to run it and (b) the purpose of each script or file.
3. `requirements.txt` present, `.env.example` committed, no key in history.
4. Run it on a **second machine**, by a second person, from scratch. `DEL-8` is `S3`.

**Done when:** a teammate who did not write the code has run it from a clean clone without asking a
question.




## 12.5. T8.5 — The Deck
*Stage:* --- · *Size:* L · *Depends on:* `T8.2`, question 3 · *Answers:* `DEL-9`, `DEL-10`, `DEL-1`,
`DEL-5`

Ten slides, written to `DEC` — `plan/DEC_deck_outline.md` — on `D3_p43`'s structure.

1. **Slide 2** carries the POV problem statement, in the `[User] needs [a way to…] because
   [insight]` format, with the named person from question 3, a figure, a source and a date.
2. **Slide 5**, technical architecture, uses the module map of
   [`PLN_S3.3`](#33-module-map--the-slide-to-the-directory) verbatim — that is what makes `DEL-10`
   untriggerable.
3. **Slide 6**, innovation: name the incumbents explicitly and what each leaves undone — SignGemma,
   live captioning, gloves, human interpreters —
   [`ARC_S5.5`](ARC_architecture.md#55-positioning-against-existing-solutions). `DEL-1` is the risk
   of not doing this.
4. Say where the agency is, and where it is not: stages ①–⑤ are a fixed pipeline and the submission
   should say so. `DEL-5` fires when the agentic justification is thin.
5. **Evaluation is on a slide.** `D3_p42` requires it; `DEL-9` is the cost of forgetting.
6. **Slide 9**, roadmap: depth as an optional accuracy upgrade rather than a dependency, priced at
   the 0.99-point difference `RSA` measured; and wait-k streaming as the named answer to
   sub-utterance latency —
   [`ARC_S5.6.5`](ARC_architecture.md#565-routes-explicitly-rejected).
7. **Describe the closed vocabulary as a closed vocabulary**, everywhere — `HUM-5`,
   [`CLD_S5.2`](../CLAUDE.md#52-honesty-about-the-product).

**Done when:** ten slides or fewer, each mapped to a criterion, and the mechanism explanation has
been rehearsed — `JCR_S2.5`'s note that a judge's follow-up question means the score already
dropped to 1.

*Read:* [`JCR_S6`](JCR_judging_criteria.md#6-the-10-slide-deck)




## 12.6. T8.6 — The Video
*Stage:* --- · *Size:* M · *Depends on:* `T7.3`, `T8.5` · *Answers:* `HUM-17`, `DEL-11`

Five minutes, on `D3_p47`'s breakdown, **captioned**.

1. **Caption it.** `D3_p48` asks for *"clear voiceover or captions for accessibility"*, and for this
   project specifically an uncaptioned demo video is a self-inflicted wound in front of exactly the
   judges most likely to notice — `HUM-17`.
2. **Show the AI deciding, not the UI.** Narrate the reasoning: show the repair path firing —
   `D3_p48`, and it is the clearest demonstration of `D3_p10`'s *"what would a fixed workflow
   miss?"*
3. Show at least one **failure case and how the system handles it** —
   [`JCR_S8.3`](JCR_judging_criteria.md#83-c3--effectiveness-target-2).
4. Five minutes is a hard limit — `DEL-11`.

**Done when:** the video is under five minutes, captioned, and shows a refusal.

*Read:* [`JCR_S7`](JCR_judging_criteria.md#7-the-5-minute-demo-video)




## 12.7. T8.7 — The Self-Scoring Run
*Stage:* --- · *Size:* S · *Depends on:* `T8.4`, `T8.5`, `T8.6` · *Answers:* `DEL-11`

[`JCR_S8`](JCR_judging_criteria.md#8-self-scoring-checklist), run in full, before submission.

1. Every unchecked box is a point given away.
2. **One submission only.** 10 slides · 5 minutes · 5 GB — `D3_p37`, `D3_p42`, and `DEL-11` means
   there is no second attempt.
3. Check the repository size against 5 GB with the recordings included, and confirm no consent-bound
   video is in the submission that should not be.

**Done when:** every box in `JCR_S8.1`–`JCR_S8.5` is checked, or the reason it is not is written
down.




## 12.8. WP8 Exit Criteria
- [ ] `EVL` is registered and every metric has a procedure.
- [ ] One command produces the evaluation table.
- [ ] A Deaf or hard-of-hearing reviewer has seen the prototype and something changed.
- [ ] A second person has run it from a clean clone on a second machine.
- [ ] The deck is ten slides, evaluation included, incumbents named.
- [ ] The video is captioned, under five minutes, and shows a refusal.
- [ ] The self-scoring checklist has been run.

---





# 13. SCHEDULE
## 13.1. Phases
> **Placeholder — the calendar.**
> **Missing:** the competition's start date, submission deadline and any interim checkpoints. The
> hackathon site could not be read programmatically —
> [`JCR_S9`](JCR_judging_criteria.md#9-sources).
> **Update trigger:** a team member opens the site and reports the dates; the phases below are then
> given absolute dates in [`PLN_S17`](#17-change-log).
> **Owner:** team.

Phases are stated relative to the build window, which `RSK` and `ARC` both treat as **four days**.

1. **Phase 0 — Unblock** · *Before the window opens*
   *Contents:* AWS lease applied for (**up to two working days' approval**) · questions 2, 3, 4
   answered · consent form drafted · the Deaf reviewer session booked · `T0.1`–`T0.3` if machines
   are available
2. **Phase 1 — Skeleton and perception** · *Day 1*
   *Contents:* WP0 complete including the walking skeleton · `T1.1`–`T1.4` · `T3.1` and `T3.2`
   written in parallel
3. **Phase 2 — Features, segmentation, first recordings** · *Day 1–2*
   *Contents:* `T1.5` `T1.6` · `T2.1` `T2.2` · `T3.3` starts · `T6.1` in the parallel lane
4. **Phase 3 — Recognition** · *Day 2–3*
   *Contents:* `T3.4` `T3.5` · `T4.1`–`T4.4` · `T2.3` once a classifier exists · `T6.2`–`T6.5` in
   the parallel lane
5. **Phase 4 — Agent and integration** · *Day 3*
   *Contents:* `T5.1`–`T5.8` · `T4.5` · `T7.1` `T7.2` · the first fallback recording
6. **Phase 5 — Measure, harden, present** · *Day 4*
   *Contents:* `T2.4` · `T7.3` `T7.4` · `T8.2`–`T8.7`. **No new capability is added in this phase**

> **Note — `T8.1` and `T8.3` do not appear in phase 5.** `EVL` is written in phase 1 because it
> decides what the harness records, and the reviewer session is booked in phase 0 because it depends
> on another person's calendar. Both are the classic end-of-project casualties, and both are the
> ones `JCR` scores directly.




## 13.2. The Critical Path
```text
Q2 + Q4 answered ──► T3.1 vocabulary ──► T3.2 protocol ──► T3.3 recording ──► T3.4 splits
                                                                                   │
                                                                                   ▼
   T0.5 contracts ──► T1.3 landmarker ──► T1.5 normaliser ──► T4.1 ──► T4.2 classifier
                                                                                   │
                                                                                   ▼
                                                     T4.3 calibration ──► T5.6 repair path
                                                                                   │
                                                                                   ▼
                                                              T7.1 screen ──► T8.6 video
```

Three observations that should change how the week is spent:

1. **The path runs through people, not code.** Its first three links are a decision, a consent form
   and a recording session. None of them is accelerated by writing software
2. **`T4.3` is a hidden dependency of the whole honesty story.** Without a calibrated confidence
   there is nothing to threshold on, so `T5.6` — the differentiator — has no input. `AGT-16` is
   `S3`/`L3` for this reason
3. **The AWS lease has the longest single lead time in the plan** and it sits outside the build
   entirely. It is applied for in phase 0 or the agent stage has nowhere to run




## 13.3. Lanes and Ownership
`DEL-13` observes that sign-language linguistics, computer vision, agent engineering and
presentation are four different skills and *"no team of three to five has all four in depth"*. The
four lanes below are the acknowledgement of that, not a wish.

| Lane        | Work packages | Owns                                    |
| :---------- | :------------ | :-------------------------------------- |
| Perception  | WP1, WP2      | Stages ①–④, and the decision-14 answer  |
| Model, data | WP3, WP4      | The vocabulary, the recordings, stage ⑤ |
| Agent       | WP5, WP6      | Stages ⑥–⑭, and the AWS lease           |
| Evidence    | WP7, WP8      | `EVL`, `DEC`, the video, the checklist  |

WP0 is shared and is finished before the lanes diverge.

> **Placeholder — names.**
> **Missing:** which team member owns each lane, and who owns the AWS lease.
> **Update trigger:** the team assigns them.
> **Owner:** team.

> **Warning — the evidence lane is not the leftover lane.** Two of the five judging criteria (C2 and
> C5) are won at the desk rather than in the code, and all five are equally weighted:
> *"an excellent model nobody can explain scores exactly the same as a mediocre model that is
> explained well"* — [`JCR_S1.1`](JCR_judging_criteria.md#11-five-criteria-20-each-scored-02).




## 13.4. Descoping Order
When the schedule runs short, work is cut **in this order**, from the top. Deciding the order now
prevents the decision being made at 2 a.m. by whoever is most tired.

1. **Cross-session persistence in `T5.7`** · *Cost of cutting:* Low
   In-conversation adaptation still demonstrates the *adapts* leg
2. **`T2.3`, the sliding-window arm** · *Cost of cutting:* The decision-20 comparison is not run.
   **Say so** rather than implying it was — `T2.4` reports what was measured, including nothing
3. **The second arm of `T1.3`** · *Cost of cutting:* Decision 14 is settled by argument instead of
   measurement, which is weaker but survivable if recorded as such
4. **`normalize_hands_3d()` in `T1.5`** · *Cost of cutting:* Handshape stays orientation-dependent.
   Measurable accuracy cost, no structural damage
5. **`T3.5`, augmentation** · *Cost of cutting:* Accuracy on a small dataset. Cheap to restore
6. **`T6.5`'s renderer** · *Cost of cutting:* The reverse direction degrades to a printed gloss
   sequence plus fingerspelling. **Two-way communication survives**, which is the point
7. **WP6 entirely** · *Cost of cutting:* High and structural. `CNV-6` returns: the system becomes
   one-way, which is the criticism levelled at the gloves this project rejects. **Last resort**

**Never cut, at any point:**

1. **`T5.6`, the repair path.** Decision 8 is a design invariant —
   [`CLD_S5.2`](../CLAUDE.md#52-honesty-about-the-product)
2. **`T0.4`'s token logging and spend guard.** `SYS-8` is a kill switch, not a bill
3. **`T7.2`, the gloss trace.** It is the differentiator made visible
4. **`T7.3`, the fallback recording.** It is the difference between a bad score and a zero on C4
   and C5 — `DEL-15`
5. **`T3.2`'s consent, and `T8.3`'s reviewer session.** Neither is an engineering trade




## 13.5. Daily Discipline
Five habits, each answering a specific `S3` risk.

1. **The walking skeleton runs, end to end, every day** · *Answers:* `DEL-14`
2. **The fallback recording is refreshed whenever the pipeline improves** · *Answers:* `DEL-15`
3. **The AWS spend is read once a day by its named owner** · *Answers:* `SYS-8`, `SYS-11`
4. **Nothing is merged that the walking skeleton cannot run** · *Answers:* `DEL-6`
5. **`aws sso login` at the start of each day** · *Answers:* `SYS-10`

---





# 14. RISK CONTROLS CARRIED INTO THE PLAN
Every risk in [`RSK_S10`](RSK_risk_register.md#10-top-ten-risks) mapped to the task that answers
it. Where a risk has no task, that is stated rather than hidden.

1.  **`AGT-1` — hallucinated meaning** · *Answered by:* `T5.5` `T5.6` `T7.2` · *Residual:* Reduced,
    not removed. The refusal threshold is calibrated on a small validation set
2.  **`LNG-1` — non-manual grammar ignored** · *Answered by:* `T4.1` (brow and mouth in the budget),
    `T1.5` step 6 (the face is never smoothed) · *Residual:* ⚠ A curated subset is not the full
    non-manual channel, and this project will not close that gap
3.  **`CNV-6` — one-way communication** · *Answered by:* WP6 in full · *Residual:* Returns entirely
    if WP6 is cut — [`PLN_S13.4`](#134-descoping-order) item 7
4.  **`HUM-1` — built without Deaf involvement** · *Answered by:* `T8.3`
    *Residual:* One session is a minimum, not a partnership, and the deck says so
5.  **`LNG-6` / `LNG-7` — coarticulation and absent boundaries** · *Answered by:* `T2.2` `T2.3`
    `T2.4` · *Residual:* **Unsolved in the field.** The plan measures both approaches rather than
    claiming either works
6.  **`MOD-1` / `MOD-2` — no data at scale** · *Answered by:* `T3.1`–`T3.4` · *Residual:* Large.
    A handful of signers in one room is what four days buys, and metric 10 reports it
7.  **`CAP-2` / `CAP-4` — motion blur and self-occlusion** · *Answered by:* `T1.5` step 5
    (interpolation, not zeros), `T7.4` (measured, not assumed) · *Residual:* Physical limits of a
    webcam. No software fix
8.  **`AGT-16` — no calibrated notion of unsure** · *Answered by:* `T4.3` · *Residual:* The
    calibration set is small, so the threshold is better than a guess but not a guarantee
9.  **`DEL-2` / `DEL-12` — boiling the ocean, scope creep** · *Answered by:* `T3.1`,
    [`PLN_S13.4`](#134-descoping-order) · *Residual:* Decision 4's scenario is a setting, not a
    bound; `T3.1` is what supplies the bound
10. **`DEL-6` / `DEL-15` — fragile demo, no fallback** · *Answered by:* `T7.3` `T7.4` `T0.6` ·
    *Residual:* Low, if `T7.3` is actually refreshed

---





# 15. WHAT THIS PLAN DOES NOT COVER
Stated so that the omissions are visible rather than discovered.

1. **Multi-person signing.** `CNV-1`, `CNV-2` and `CNV-4` are catalogued and out of scope. Arm A of
   `T1.3` is hard-limited to one person, and `T1.2` emits a subject identifier so the capability is
   addable later
2. **Devices other than a laptop.** [`SCR`](scribbles.md) promises phones, tablets and glasses;
   `SYS-5` observes each is a separate integration. The MVP is one laptop with a webcam
3. **Turn-taking as a model.** `CNV-5` and `CNV-9` are real and the plan handles turns only as far
   as the one screen in `T7.1` shows them
4. **A liability or accountability model.** `HUM-7` is unanswered by every system in this space,
   this one included, and pretending otherwise on a slide would be worse than the gap
5. **Deployment beyond a local process.** AgentCore Runtime is in the taught stack; the plan runs
   locally against Bedrock, which is what the budget and the demo require
6. **Anything requiring depth hardware.** Decision 10, and the 0.99-point price `RSA` measured for
   the whole six-modality RGB-D ensemble

---





# 16. SOURCES
This document makes no external factual claim of its own. Every figure it repeats is carried across
from a document in this repository, by address, and resolves to that document's own sources section.

1. **`[S1]`**
   *Source:* `doc/[D3]_Hackathon_Training_Session_3.pdf` — deliverables, folder structure, loop
   bounds, metrics, deck and video rules. Extracted in full into
   [`JCR`](JCR_judging_criteria.md)
   *Reliability:* Official (organiser)
2. **`[S2]`**
   *Source:* `doc/[D6]_Hackathon_AWS_Access_Guide.pdf` — lease process, approval time, and the
   US$20 / US$30 budget cap. Summarised in
   [`TRN_S6`](../doc/TRN_training_synthesis.md#6-d6--aws-access-and-budget)
   *Reliability:* Official (organiser)
3. **`[S3]`**
   *Source:* `doc/[D1]` and `doc/[D2]` — model pricing as stated by the organiser, prompt caching,
   the taught stack. ⚠ Bedrock is partner-operated and priced separately; verify pricing against
   the AWS Bedrock pricing page before quoting
   *Reliability:* Official (organiser); pricing unverified against the operator
4. **`[S4]`**
   *Source:* [`ARC_S10`](ARC_architecture.md#10-sources) — the thirty sources behind every
   accuracy figure, budget and licence statement repeated in this plan, including which are
   preprints and which were transcribed rather than read
   *Reliability:* Mixed and individually marked in `ARC`. ⚠ Nothing quoted here is more reliable
   than its entry there

---





# 17. CHANGE LOG
1. **2026-09-05** · *Author:* Claude (Opus 5)
   *Change:* Created. Converted [`ARC`](ARC_architecture.md) into nine work packages and fifty
   tasks with sizes, dependencies and exit criteria; mapped every pipeline stage of
   [`ARC_S6.1`](ARC_architecture.md#61-pipeline) and every rule of
   [`ARC_S6.5`](ARC_architecture.md#65-perception-engineering-rules) onto a module in
   [`PLN_S3.3`](#33-module-map--the-slide-to-the-directory). Recorded the four frozen interfaces,
   the critical path, the four lanes, the descoping order and the never-cut list. Mapped
   [`RSK_S10`](RSK_risk_register.md#10-top-ten-risks) onto the tasks that answer it, with residual
   risk stated. Registered the gate in
   [`PLN_S2.2`](#22-what-is-not-decided-and-what-it-blocks): questions 2 and 4 block WP3 alone, and
   thirty-one of the fifty tasks proceed regardless. Recorded that decision 17 is **Rejected**, so
   the landmark budget is decision 2's; and that decision 4 names a scenario, not a vocabulary
   bound, which `T3.1` must supply. Placeholders left for the calendar, the lane owners and the
   face-mesh indices.
2. **2026-09-06** · *Author:* Codex (GPT-5)
   *Change:* Linked `T0.2` to [`DEP`](DEP_dependencies.md), the maintained dependency inventory and
   virtual-environment guide, while preserving the exact-lock requirement as unfinished work.
