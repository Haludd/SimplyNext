**REFERENCE INDEX**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field                   | Value                                                      |
| :---------------------- | :--------------------------------------------------------- |
| **Code**                | `RIX`                                                      |
| **Status**              | Live                                                       |
| **Last reviewed**       | 2026-09-04                                                 |
| **Source of truth for** | Document locations, addressing scheme, markdown formatting |
| **Related**             | [`CLD`](CLAUDE.md) · [`RDM`](README.md)                    |

**For the team.** This file answers three questions: which documents exist and where they live
([`RIX_S2`](#2-document-registry)), how to cite any section of any of them
([`RIX_S3`](#3-addressing-scheme)), and how every `.md` file in the repository must be formatted
([`RIX_S4`](#4-markdown-formatting-rules)). Read it before creating or renaming a document.

**For the assistant.** Read this file at the start of every prompt, before any other action. It
changes; do not work from a remembered version. Any document created, moved, renamed, split or
retired must be reflected in [`RIX_S2`](#2-document-registry) within the same change.

</details>

---





# 1. USING THIS FILE
## 1.1. Addressing in Brief
Every document carries a three-letter code. Every section carries a number. Joined with `_S`, the
two form a global address that resolves anywhere in the repository.

1. **Document code** · *Example:* `ARC`
   *Where it is declared:* The `METADATA` block of the document, and
   [`RIX_S2.1`](#21-live-documents)
2. **Section number** · *Example:* `3.2`
   *Where it is declared:* The heading itself — `## 3.2. Pose Extraction`
3. **Global address** · *Example:* `ARC_S3.2`
   *Where it is declared:* Formed by joining the two

An address written in a chat message, a slide, a code comment or another document is enough for a
reader to locate the exact paragraph: open the file the code names, then search for the number.




## 1.2. Rules of Engagement
1. Consult this file at the start of every work session and every AI prompt.
2. No document exists until a code for it is registered in [`RIX_S2`](#2-document-registry).
3. Registry updates ship in the same commit as the document change they describe.
4. Retired codes are never reused. Mark them `RETIRED` in [`RIX_S2.4`](#24-retired-codes).
5. Where two documents disagree, the one marked **SoT** in [`RIX_S2.1`](#21-live-documents) wins.

---





# 2. DOCUMENT REGISTRY
## 2.1. Live Documents
1.  **`RIX`** — `ref_index.md` · *Status:* Live
    *Contents:* Registry, addressing scheme, formatting rules
    *SoT for:* Document locations and naming
2.  **`CLD`** — `CLAUDE.md` · *Status:* Live
    *Contents:* Rules for AI agents working in this repository
    *SoT for:* Agent behaviour
3.  **`RDM`** — `README.md` · *Status:* Live
    *Contents:* Human entry point: orientation, setup, conventions
    *SoT for:* Onboarding
4.  **`SCR`** — `plan/scribbles.md` · *Status:* Live
    *Contents:* Raw ideation: context, problem, solution, MVP concept
    *SoT for:* **Product intent**
5.  **`JCR`** — `plan/JCR_judging_criteria.md` · *Status:* Live
    *Contents:* Judging criteria, deliverables, deck and video structure, extracted from `D3`
    *SoT for:* **Scoring**
6.  **`ARC`** — `plan/ARC_architecture.md` · *Status:* Live
    *Contents:* MVP architecture confirmed against sources; alternatives, priority-ordered
    *SoT for:* **Technical direction**
7.  **`RSK`** — `plan/RSK_risk_register.md` · *Status:* Live
    *Contents:* Catalogue of potential problems. Problems only, no mitigations
    *SoT for:* **Known problems**
8.  **`PLN`** — `plan/PLN_plan.md` · *Status:* Draft
    *Contents:* Execution plan: nine work packages, fifty tasks, schedule and descoping order
    *SoT for:* **Execution sequence**
9.  **`TRN`** — `doc/TRN_training_synthesis.md` · *Status:* Live
    *Contents:* Synthesis of all six hackathon training decks
    *SoT for:* Training content

**Reference-repository documents.** Two per repository, on the pattern in
[`RIX_S3.5`](#35-repository-document-codes): a **full report** beside the clone it describes, and a
**synthesis** in `doc/`. The reports live inside `ref_repo/` and are the only files there that
version control tracks — [`RIX_S5.2`](#52-what-version-control-tracks).

The repositories are grouped by the problem they address: **`ref_repo/tracking/`** for
perception — finding and following the body — and **`ref_repo/translation/`** for turning what was
tracked into language, and back. Items 10–17 are the tracking set; items 18–29 the translation set.

10. **`APR`** — `ref_repo/tracking/apple/APR_apple_report.md` · *Status:* Live
    *Contents:* Full technical report on the Apple `HandPose` clone
    *SoT for:* Apple repository analysis
11. **`APS`** — `doc/APS_apple_synthesis.md` · *Status:* Live
    *Contents:* Short synthesis of the Apple repository; defers to `APR`
12. **`MPR`** — `ref_repo/tracking/google-mediapipe/MPR_mediapipe_report.md` · *Status:* Live
    *Contents:* Full technical report on MediaPipe, focused on the Hand Landmarker task
    *SoT for:* MediaPipe repository analysis
13. **`MPS`** — `doc/MPS_mediapipe_synthesis.md` · *Status:* Live
    *Contents:* Short synthesis of MediaPipe; defers to `MPR`
14. **`DHR`** — `ref_repo/tracking/depthai-hand-tracker/DHR_depthai_report.md` · *Status:* Live
    *Contents:* Full technical report on the DepthAI hand tracker
    *SoT for:* DepthAI repository analysis
15. **`DHS`** — `doc/DHS_depthai_synthesis.md` · *Status:* Live
    *Contents:* Short synthesis of the DepthAI hand tracker; defers to `DHR`
16. **`OPR`** — `ref_repo/tracking/openpose/OPR_openpose_report.md` · *Status:* Live
    *Contents:* Full technical report on OpenPose, including the licence analysis
    *SoT for:* OpenPose repository analysis
17. **`OPS`** — `doc/OPS_openpose_synthesis.md` · *Status:* Live
    *Contents:* Short synthesis of OpenPose and the record of its rejection; defers to `OPR`
18. **`SLR`** — `ref_repo/translation/slrt/SLR_slrt_report.md` · *Status:* Live
    *Contents:* Full technical report on `FangyunWei/SLRT` — six papers on recognition and
    translation
    *SoT for:* SLRT repository analysis
19. **`SLS`** — `doc/SLS_slrt_synthesis.md` · *Status:* Live
    *Contents:* Short synthesis of SLRT and the numbers it supplies; defers to `SLR`
20. **`SAR`** — `ref_repo/translation/sam-slr/SAR_sam_slr_report.md` · *Status:* Live
    *Contents:* Full technical report on SAM-SLR, including the licence contradiction
    *SoT for:* SAM-SLR repository analysis
21. **`SAS`** — `doc/SAS_sam_slr_synthesis.md` · *Status:* Live
    *Contents:* Short synthesis of SAM-SLR and its two decisive tables; defers to `SAR`
22. **`SPR`** — `ref_repo/translation/sign-pose/SPR_sign_pose_report.md` · *Status:* Live
    *Contents:* Full technical report on `pose-format`, including the MediaPipe collision
    *SoT for:* `pose-format` repository analysis
23. **`SPS`** — `doc/SPS_sign_pose_synthesis.md` · *Status:* Live
    *Contents:* Short synthesis of `pose-format`; defers to `SPR`
24. **`SSR`** — `ref_repo/translation/spoken-to-signed/SSR_spoken_to_signed_report.md` ·
    *Status:* Live
    *Contents:* Full technical report on the spoken-to-signed pipeline
    *SoT for:* Spoken-to-signed repository analysis; **the reverse translation direction**
25. **`SSS`** — `doc/SSS_spoken_to_signed_synthesis.md` · *Status:* Live
    *Contents:* Short synthesis of the spoken-to-signed pipeline; defers to `SSR`
26. **`LTR`** — `ref_repo/translation/signlang-literature/LTR_signlang_literature_report.md` ·
    *Status:* Live
    *Contents:* Full report on the sign language processing survey and its 49-dataset registry
    *SoT for:* **The field's published state, and what data exists**
27. **`LTS`** — `doc/LTS_signlang_literature_synthesis.md` · *Status:* Live
    *Contents:* Short synthesis of the survey and the facts it settles; defers to `LTR`
28. **`STR`** — `ref_repo/translation/sign-translator/STR_sign_translator_report.md` ·
    *Status:* Live
    *Contents:* Full technical report on `sign-language-translator`, including the Tasks-API example
    *SoT for:* `sign-language-translator` repository analysis
29. **`STS`** — `doc/STS_sign_translator_synthesis.md` · *Status:* Live
    *Contents:* Short synthesis of `sign-language-translator`; defers to `STR`
30. **`BCT`** — `doc/BCT_backend_comparison_test.md` · *Status:* Live
    *Contents:* Comparison of the merged backend against `ARC` and `PLN`, with verification results
    *SoT for:* Backend-versus-plan comparison at the review snapshot




## 2.2. Planned Documents
Codes reserved; files not yet created.

1. **`TDO`** — `plan/TDO_todo.md`
   *Contents:* Live task board, written from
   [`PLN_S4`](plan/PLN_plan.md#4-wp0--foundations) onwards
   *Blocked on:* `PLN` reaching **Live** — architecture sign-off,
   [`ARC_S9`](plan/ARC_architecture.md#9-decisions)
2. **`EVL`** — `plan/EVL_eval_protocol.md`
   *Contents:* Test data, metrics, measurement methodology — see
   [`JCR_S5`](plan/JCR_judging_criteria.md#5-evaluation-and-metrics)
   *Blocked on:* Nothing. It is task `T8.1` —
   [`PLN_S12.1`](plan/PLN_plan.md#121-t81--write-evl)
3. **`DEC`** — `plan/DEC_deck_outline.md`
   *Contents:* Ten-slide submission deck outline — see
   [`JCR_S6`](plan/JCR_judging_criteria.md#6-the-10-slide-deck)
   *Blocked on:* The named person —
   [`ARC_S9.1`](plan/ARC_architecture.md#91-open-questions-for-the-team) question 3




## 2.3. Source Material
Read-only originals. Reference a slide as `<code>_p<slide>`, for example `D3_p39`.

1. **`D1`**
   *File:* `doc/[D1]_Hackathon_Training_Session_1.pdf`
   *Contents:* LLM foundations, agent anatomy, planning, memory, tools, prompt engineering, AWS
   Bedrock
   *Synthesised in:*
   [`TRN_S2`](doc/TRN_training_synthesis.md#2-d1--llm-foundations-agents-prompting-bedrock)
2. **`D2`**
   *File:* `doc/[D2]_Hackathon_Training_Session_2.pdf`
   *Contents:* LangGraph, DeepAgents, Claude Agent SDK, MCP, Bedrock AgentCore deployment
   *Synthesised in:* [`TRN_S3`](doc/TRN_training_synthesis.md#3-d2--langgraph-deepagents-agentcore)
3. **`D3`**
   *File:* `doc/[D3]_Hackathon_Training_Session_3.pdf`
   *Contents:* Problem framing, agent classes, best practices, case studies, **judging criteria**,
   submission rules
   *Synthesised in:* [`JCR`](plan/JCR_judging_criteria.md) ·
   [`TRN_S4`](doc/TRN_training_synthesis.md#4-d3--framing-classes-practices-case-studies)
4. **`D4`**
   *File:* `doc/[D4]_Hackathon_Training_Session_1_Extra.pdf`
   *Contents:* Physical-AI track: the perception→generative→agentic→physical ladder, sim-to-real,
   ORCA platform. ⚠ Image-only PDF, no text layer
   *Synthesised in:* [`TRN_S5`](doc/TRN_training_synthesis.md#5-d4-and-d5--the-physical-ai-track)
5. **`D5`**
   *File:* `doc/[D5]_Hackathon_Training_Session_2_Extra.pdf`
   *Contents:* Physical-AI track: ORCA VLN / NaVILA closed-loop navigation manual
   *Synthesised in:* [`TRN_S5`](doc/TRN_training_synthesis.md#5-d4-and-d5--the-physical-ai-track)
6. **`D6`**
   *File:* `doc/[D6]_Hackathon_AWS_Access_Guide.pdf`
   *Contents:* AWS registration, 2FA, sandbox lease, **budget caps**
   *Synthesised in:* [`TRN_S6`](doc/TRN_training_synthesis.md#6-d6--aws-access-and-budget)
7.  **`RAP`**
    *File:* `ref_repo/tracking/apple/handpose/` at `ec30ff6`
    *Contents:* Apple `HandPose` sample code (Swift, WWDC20)
    *Documented in:* [`APR`](ref_repo/tracking/apple/APR_apple_report.md) ·
    [`APS`](doc/APS_apple_synthesis.md)
8.  **`RMP`**
    *File:* `ref_repo/tracking/google-mediapipe/mediapipe/` at `251c0cb96`
    *Contents:* Google MediaPipe — the framework and the Tasks API. **A dependency, not just a
    reference**
    *Documented in:* [`MPR`](ref_repo/tracking/google-mediapipe/MPR_mediapipe_report.md) ·
    [`MPS`](doc/MPS_mediapipe_synthesis.md)
9.  **`RDH`**
    *File:* `ref_repo/tracking/depthai-hand-tracker/depthai_hand_tracker/` at `9773123`
    *Contents:* `geaxgx/depthai_hand_tracker` — MediaPipe's hand models on Luxonis OAK hardware,
    with the pipeline re-implemented in NumPy
    *Documented in:* [`DHR`](ref_repo/tracking/depthai-hand-tracker/DHR_depthai_report.md) ·
    [`DHS`](doc/DHS_depthai_synthesis.md)
10. **`ROP`**
    *File:* `ref_repo/tracking/openpose/openpose/` at `5c5d965`
    *Contents:* CMU OpenPose. ⚠ **Non-commercial licence** — read
    [`OPR_S2.2`](ref_repo/tracking/openpose/OPR_openpose_report.md#22-licence) before touching it
    *Documented in:* [`OPR`](ref_repo/tracking/openpose/OPR_openpose_report.md) ·
    [`OPS`](doc/OPS_openpose_synthesis.md)
11. **`RSL`**
    *File:* `ref_repo/translation/slrt/SLRT/` at `38a4f7b`
    *Contents:* `FangyunWei/SLRT` — six published papers on sign language recognition and
    translation. ⚠ **No licence file** — read
    [`SLR_S2.2`](ref_repo/translation/slrt/SLR_slrt_report.md#22-licence) before touching it
    *Documented in:* [`SLR`](ref_repo/translation/slrt/SLR_slrt_report.md) ·
    [`SLS`](doc/SLS_slrt_synthesis.md)
12. **`RSA`**
    *File:* `ref_repo/translation/sam-slr/CVPR21Chal-SLR/` at `de6c53a`
    *Contents:* SAM-SLR, winner of the CVPR 2021 isolated-recognition challenge. ⚠ **Contradictory
    licence, treated as non-commercial** —
    [`SAR_S2.2`](ref_repo/translation/sam-slr/SAR_sam_slr_report.md#22-licence)
    *Documented in:* [`SAR`](ref_repo/translation/sam-slr/SAR_sam_slr_report.md) ·
    [`SAS`](doc/SAS_sam_slr_synthesis.md)
13. **`RSP`**
    *File:* `ref_repo/translation/sign-pose/pose/` at `7a36fcf`
    *Contents:* `pose-format` — the field's pose container and manipulation library, MIT. **A
    candidate dependency, not just a reference**
    *Documented in:* [`SPR`](ref_repo/translation/sign-pose/SPR_sign_pose_report.md) ·
    [`SPS`](doc/SPS_sign_pose_synthesis.md)
14. **`RSS`**
    *File:* `ref_repo/translation/spoken-to-signed/spoken-to-signed-translation/` at `259aacd`
    *Contents:* ZurichNLP's `text-to-gloss-to-pose-to-video` pipeline, MIT. **A candidate
    dependency — the reverse translation direction**
    *Documented in:*
    [`SSR`](ref_repo/translation/spoken-to-signed/SSR_spoken_to_signed_report.md) ·
    [`SSS`](doc/SSS_spoken_to_signed_synthesis.md)
15. **`RLT`**
    *File:* `ref_repo/translation/signlang-literature/sign-language-processing.github.io/` at
    `af5fb4a`
    *Contents:* The sign language processing survey, bibliography and 49-dataset registry, CC BY
    4.0. ⚠ **A survey, not a primary source**
    *Documented in:*
    [`LTR`](ref_repo/translation/signlang-literature/LTR_signlang_literature_report.md) ·
    [`LTS`](doc/LTS_signlang_literature_synthesis.md)
16. **`RST`**
    *File:* `ref_repo/translation/sign-translator/sign-language-translator/` at `cca5f3a`
    *Contents:* `sign-language-translator` — an Apache 2.0 framework for building a translator for
    a sign language with no data. ⚠ The sign-to-text direction is **not implemented**
    *Documented in:*
    [`STR`](ref_repo/translation/sign-translator/STR_sign_translator_report.md) ·
    [`STS`](doc/STS_sign_translator_synthesis.md)

> **Note:** the clones themselves are **excluded from version control** —
> [`RIX_S5.2`](#52-what-version-control-tracks). A teammate obtains them by cloning from the
> upstream remote each report names in its provenance section.




## 2.4. Retired Codes
All retired on **2026-08-30**, in the change that registered the three new reference
repositories.

1. **`APL`** — `doc/APL_apple_ref_report.md`
   *Reason:* Recoded `APR` and moved to `ref_repo/tracking/apple/`, beside the clone it describes
2. **`SYN`** — `ref_repo/tracking/apple/SYN_apple_synthesis.md`
   *Reason:* Recoded `APS` and moved to `doc/`, alongside the other syntheses
3. **`REF`** — `ref_repo/tracking/apple/`
   *Reason:* One source code per repository is now required: `RAP`, `RMP`, `RDH`, `ROP`

---





# 3. ADDRESSING SCHEME
## 3.1. Address Format
```text
<CODE>_S<section>[.<sub>[.<sub>]]

APR_S4        → ref_repo/tracking/apple/APR_apple_report.md, section 4
APR_S4.2      → ... section 4.2
RSK_S3.1      → plan/RSK_risk_register.md, section 3.1
D3_p39        → doc/[D3]_..., slide 39        (source PDFs use page addresses)
RAP:HandPose/CameraViewController.swift:212   (a line in a reference repository, relative
RMP:mediapipe/tasks/python/vision/hand_landmarker.py:311        to that clone's own root)
RSP:src/python/pose_format/pose.py:104
```

Risk items carry their own stable IDs on top of the section address — see
[`RSK_S1.3`](plan/RSK_risk_register.md#13-identifiers-and-ratings).




## 3.2. Choosing a Code
- Three characters, uppercase, `A–Z` only. No digits, no reuse, no collision with `D1`–`D6`.
- The code compresses the document's real name: `ARChitecture` → `ARC` · `RiSK` → `RSK` ·
  `Judging CRiteria` → `JCR` · `TRaiNing` → `TRN` · `Reference IndeX` → `RIX`.
- Reference-repository documents follow the systematic pattern in
  [`RIX_S3.5`](#35-repository-document-codes) instead.




## 3.3. Filenames
```text
<CODE>_<snake_case_name>.md      e.g. ARC_architecture.md
```

Exceptions kept for tooling and convention: `README.md`, `CLAUDE.md`, `ref_index.md`,
`plan/scribbles.md`.




## 3.4. Resolving an Address
Headings carry no HTML anchor. The address is derived from the document code declared in the
`METADATA` block and the section number printed in the heading itself.

1. **Cite in speech, chat or a slide**
   Write the address: `ARC_S2.1`
2. **Find it in an editor**
   Open the file the code names, search for `2.1.`
3. **Link from another `.md`**
   Address as link text, GitHub slug as target: ``
   [`ARC_S2.1`](plan/ARC_architecture.md#21-verdict-confirmed-at-lower-cost-than-assumed) ``

The GitHub slug is the heading text lowercased, with punctuation removed and spaces replaced by
hyphens. Where the slug is unknown, link the file alone and keep the address as the link text; the
address still resolves by search.




## 3.5. Repository Document Codes
Every repository in `ref_repo/` carries three codes, built from a two-letter repository tag plus
one role letter. The pattern is fixed so that an eleventh repository needs no discussion.

**Tracking** — `ref_repo/tracking/`:

| Repository           | Tag  | Source | Report | Synthesis |
| :------------------- | :--- | :----- | :----- | :-------- |
| Apple `HandPose`     | `AP` | `RAP`  | `APR`  | `APS`     |
| Google MediaPipe     | `MP` | `RMP`  | `MPR`  | `MPS`     |
| DepthAI hand tracker | `DH` | `RDH`  | `DHR`  | `DHS`     |
| CMU OpenPose         | `OP` | `ROP`  | `OPR`  | `OPS`     |

**Translation** — `ref_repo/translation/`:

| Repository                 | Tag  | Source | Report | Synthesis |
| :------------------------- | :--- | :----- | :----- | :-------- |
| FangyunWei SLRT            | `SL` | `RSL`  | `SLR`  | `SLS`     |
| SAM-SLR                    | `SA` | `RSA`  | `SAR`  | `SAS`     |
| `pose-format`              | `SP` | `RSP`  | `SPR`  | `SPS`     |
| Spoken-to-signed           | `SS` | `RSS`  | `SSR`  | `SSS`     |
| SLP literature survey      | `LT` | `RLT`  | `LTR`  | `LTS`     |
| `sign-language-translator` | `ST` | `RST`  | `STR`  | `STS`     |

1. **`R` + tag** — the **source clone** itself, registered in
   [`RIX_S2.3`](#23-source-material). Not a document
2. **tag + `R`** — the **full report**, in `ref_repo/<track>/<slug>/`, beside the clone it
   describes
3. **tag + `S`** — the **synthesis**, in `doc/`, alongside the other syntheses

> **Note — `SLR` is a document code, not the field term.** *SLR* also abbreviates *sign language
> recognition* throughout the literature these documents discuss. Document codes are always written
> in backticks; the field term never is.

Reports hold the depth: file-by-file analysis, line citations, port tables. Syntheses hold the
five-minute orientation. Where a report and its synthesis disagree, **the report wins**, and each
synthesis says so in its own metadata block.

---





# 4. MARKDOWN FORMATTING RULES
These rules apply to every `.md` file in this repository. The target is a document a teammate can
skim in sixty seconds and search in ten, in raw source as well as rendered.




## 4.1. Document Skeleton
```markdown
**DOCUMENT TITLE**

# METADATA

<details>
<summary>Document code, status, review date, and usage instructions.</summary>

...

</details>

---

# 1. FIRST SECTION
```

The title is **bold text, not a heading**. `#` is reserved for numbered sections, so that the
heading ladder and the addressing scheme share one numbering.




## 4.2. Metadata Block
Every document opens with a collapsible `# METADATA` section immediately after the title. It
carries a field table and, where useful, notes addressed to the team and to the assistant.

1. **Code** · *Required:* yes
   *Contents:* The document's three-letter code
2. **Status** · *Required:* yes
   *Contents:* `Draft`, `Live` or `Frozen` — see [`RIX_S4.8`](#48-required-tail-sections)
3. **Last reviewed** · *Required:* yes
   *Contents:* Absolute date, `YYYY-MM-DD`
4. **Source of truth for** · *Required:* where applicable
   *Contents:* The subject on which this document overrides others
5. **Parent** / **Related** · *Required:* where applicable
   *Contents:* Addresses of the documents above and beside it
6. **For the team** · *Required:* where useful
   *Contents:* How a human should use the document, and what is unfinished
7. **For the assistant** · *Required:* where useful
   *Contents:* Standing instructions for AI agents editing the document




## 4.3. Heading Ladder
| Level           | Syntax       | Case                 | Example                               |
| :-------------- | :----------- | :------------------- | :------------------------------------ |
| Title           | `**bold**`   | ALL CAPS             | `**ARCHITECTURE**`                    |
| Metadata        | `# METADATA` | ALL CAPS, unnumbered | `# METADATA`                          |
| Section         | `# N.`       | ALL CAPS             | `# 3. RECOMMENDED ARCHITECTURE`       |
| Sub-section     | `## N.M.`    | Caps Initials Only   | `## 3.2. Pose Extraction`             |
| Sub-sub-section | `### N.M.K.` | First character only | `### 3.2.1. Landmark budget`          |
| Deeper          | ---          | ---                  | Use a bold lead-in or a table instead |

Headings are as short as the idea allows and name the content rather than describing it. Every
heading number ends with a period, so a search for `3.2.` reaches the heading and not the prose.




## 4.4. Vertical Spacing
Blank lines separate sections in raw source; their count signals depth before the reader parses the
heading.

1. **Before a heading**, leave `6 − level` blank lines: five before `#`, four before `##`, three
   before `###`, two before `####`.
2. **After a heading**, leave none. The heading is followed immediately by its content or by the
   next heading down.
3. Rule 2 **supersedes** rule 1. Where a heading follows another heading directly — a `#` section
   opening straight onto its first `##` — no blank line is inserted between them.
4. The `---` section rule closes the section it follows; the blank lines belong between that rule
   and the next heading.

```markdown
...last line of the previous section.

---
                                    ← five blank lines before a `#`
# 3. RECOMMENDED ARCHITECTURE
                                    ← none: a heading follows a heading
## 3.1. Pipeline
The pipeline has five stages.
```




## 4.5. Tables and Numbered Lists
Width decides the format, not preference. A padded table is only readable while its rows fit on one
line; past that the pipes stop aligning and the padding becomes noise.

1. **Use a table** when every row fits within 100 characters once the columns are padded. This is
   the preferred format for short, parallel, scannable content: codes, statuses, dates, ratings,
   one- or two-word labels.
2. **Use a numbered list** when any row would spill onto a second line.
3. In a table, pad every cell in a column to the width of the longest cell in that column, header
   and separator row included. The separator row matches that width: `| :------ | :------ |`.
4. Fill an empty table cell with `---`, centred within the column.
5. When converting a table to a list, make the identifying column the item's bold title, fold
   attributes of 20 characters or fewer onto that line as `· *Label:* value`, and give every
   remaining attribute its own `*Label:* value` line.
6. Never discard an identifying column that is cited elsewhere. A `#` column that only counts rows
   is replaced by the list numbering, but a column holding real identifiers — `P1`, `[S3]`, `CAP-4`
   — becomes part of the title.
7. Where the *headers* carry the meaning, as in a DO / DON'T pair, restate them inside each list
   item rather than dropping them.




## 4.6. Body Conventions
1.  **Section separator**
    A `---` rule between every `#` section. Nothing else
2.  **Voice**
    Third person throughout. No first- or second-person pronouns — see [`RIX_S4.9`](#49-tone)
3.  **Lists**
    Bullets for unordered sets. Numbers only where order or count matters
4.  **Emphasis**
    `**bold**` for the one word carrying the sentence. No underline, no capitals mid-sentence
5.  **Callouts**
    `> **Note:**`, `> **Warning:**`, `> **Decision:**`, `> **Open question:**`, `>
    **Placeholder:**`. Nothing else
6.  **Code and identifiers**
    Always in backticks — filenames, API names and document codes included
7.  **Claims**
    Every external factual claim carries a source tag `[S<n>]` resolving to the document's `SOURCES`
    section
8.  **Uncertainty**
    Prefixed with `⚠` and accompanied by the reason. An unverified claim is never stated plainly
9.  **Line length**
    Soft-wrapped near 100 characters in source, so diffs stay readable
10. **Dates**
    Absolute, `2026-08-28`. Never relative




## 4.7. Placeholders
Unwritten or unresolved content is marked rather than approximated, so that the gap is visible to
the team and actionable by the assistant.

```markdown
> **Placeholder — <topic>.**
> **Missing:** <what is absent>.
> **Update trigger:** <the event or decision that resolves it>.
> **Owner:** <team | assistant>.
```




## 4.8. Required Tail Sections
1. **`# N. SOURCES`**
   Any document making external factual claims. Numbered `[S1]`, `[S2]`, … with full URLs and a
   reliability note
2. **`# N. CHANGE LOG`**
   Any document expected to change — everything in `plan/`. One line per revision: date, author,
   change




## 4.9. Tone
1. **Perspective**
   Third person. "The team", "the assistant", "this document" — never "we", "our", "you"
2. **Register**
   Professional and declarative. Conversational asides and rhetorical questions are removed
3. **Length**
   Headings and emphasis points state the idea in the fewest words that still carry it
4. **Claims**
   Capability is described exactly. A closed-vocabulary demonstration is described as one
5. **Quotations**
   Verbatim source quotations keep their original pronouns and are marked as quotations

---





# 5. DIRECTORY MAP
```text
SimplyNext/
├── ref_index.md                          RIX — registry, addressing, formatting
├── README.md                             RDM — human entry point
├── CLAUDE.md                             CLD — rules for AI agents
├── .gitignore                            excludes every clone under ref_repo/
│
├── plan/                                 what the team is building
│   ├── scribbles.md                      SCR — raw ideation (product intent)
│   ├── JCR_judging_criteria.md           JCR
│   ├── ARC_architecture.md               ARC
│   ├── RSK_risk_register.md              RSK
│   └── PLN_plan.md                       PLN — execution plan
│
├── doc/                                  reference material and syntheses
│   ├── [D1..D6]*.pdf                     original training decks (read-only)
│   ├── TRN_training_synthesis.md         TRN
│   ├── APS_apple_synthesis.md            APS  ┐
│   ├── MPS_mediapipe_synthesis.md        MPS  │ tracking
│   ├── DHS_depthai_synthesis.md          DHS  │
│   ├── OPS_openpose_synthesis.md         OPS  ┘
│   ├── SLS_slrt_synthesis.md             SLS  ┐
│   ├── SAS_sam_slr_synthesis.md          SAS  │
│   ├── SPS_sign_pose_synthesis.md        SPS  │ translation
│   ├── SSS_spoken_to_signed_synthesis.md SSS  │
│   ├── LTS_signlang_literature_synthesis.md  LTS │
│   └── STS_sign_translator_synthesis.md  STS  ┘
│
└── ref_repo/                             tracked: the reports. ignored: the clones
    ├── tracking/                         perception — finding and following the body
    │   ├── apple/
    │   │   ├── APR_apple_report.md               APR  ← tracked
    │   │   └── handpose/                         RAP  ← ignored
    │   ├── google-mediapipe/
    │   │   ├── MPR_mediapipe_report.md           MPR  ← tracked
    │   │   └── mediapipe/                        RMP  ← ignored
    │   ├── depthai-hand-tracker/
    │   │   ├── DHR_depthai_report.md             DHR  ← tracked
    │   │   └── depthai_hand_tracker/             RDH  ← ignored
    │   └── openpose/
    │       ├── OPR_openpose_report.md            OPR  ← tracked
    │       └── openpose/                         ROP  ← ignored
    │
    └── translation/                      turning what was tracked into language, and back
        ├── slrt/
        │   ├── SLR_slrt_report.md                SLR  ← tracked
        │   └── SLRT/                             RSL  ← ignored
        ├── sam-slr/
        │   ├── SAR_sam_slr_report.md             SAR  ← tracked
        │   └── CVPR21Chal-SLR/                   RSA  ← ignored
        ├── sign-pose/
        │   ├── SPR_sign_pose_report.md           SPR  ← tracked
        │   └── pose/                             RSP  ← ignored
        ├── spoken-to-signed/
        │   ├── SSR_spoken_to_signed_report.md    SSR  ← tracked
        │   └── spoken-to-signed-translation/     RSS  ← ignored
        ├── signlang-literature/
        │   ├── LTR_signlang_literature_report.md LTR  ← tracked
        │   └── sign-language-processing.github.io/  RLT  ← ignored
        └── sign-translator/
            ├── STR_sign_translator_report.md     STR  ← tracked
            └── sign-language-translator/         RST  ← ignored
```

Each repository directory holds **exactly two entries**: the project's report, and the clone in a
sub-directory of its own. The nesting is not decoration — a clone carries its own `.git`, and git
refuses to track a file inside an embedded repository, so the report must sit one level above it.

The **track** directory above it — `tracking/` or `translation/` — groups repositories by the
problem they address. A report therefore sits at `ref_repo/<track>/<slug>/`, three levels below the
repository root, which is what the un-ignore rule in
[`RIX_S5.2`](#52-what-version-control-tracks) must match.




## 5.1. Directory Rules
1. **`plan/`** · *Does not hold:* Third-party material
   *Holds:* Plans, to-dos, decisions, risks, criteria, evaluation protocol
2. **`doc/`** · *Does not hold:* Project plans
   *Holds:* Training decks, and the syntheses — training and repository alike
3. **`ref_repo/`** · *Does not hold:* Project source code
   *Holds:* One unmodified third-party clone per sub-directory, plus that repository's full report
4. **`src/` *(future)*** · *Does not hold:* Documents
   *Holds:* Implementation — the folder shape judges expect is in
   [`TRN_S4.3`](doc/TRN_training_synthesis.md#43-development-best-practices)




## 5.2. What Version Control Tracks
`.gitignore` excludes everything under `ref_repo/` and then re-admits only the report documents:

```text
ref_repo/**
!ref_repo/
!ref_repo/*/
!ref_repo/*/*/
!ref_repo/*/*/[A-Z][A-Z][A-Z]_*.md
ref_repo/*/*/*/
```

The consequences, in order of how often they bite:

1. **A teammate cloning this repository gets the reports, not the clones.** Each report's
   provenance section names the upstream remote and the commit it was read at
2. **Nothing in `src/` may import from `ref_repo/`.** A judge running the submission would get an
   `ImportError`. Algorithms worth keeping are re-implemented, with attribution
3. **A report must be named `<CODE>_<name>.md` at the top of its repository directory**, or the
   un-ignore rule will not match it and it will be silently untracked
4. **A clone must live in its own sub-directory**, never directly in `ref_repo/<track>/<slug>/`
5. **The depth is fixed at `ref_repo/<track>/<slug>/`.** The un-ignore rules count directory
   levels, so a repository added at the wrong depth — directly under `ref_repo/`, or one level
   deeper — will have its report silently untracked and its clone silently committed. Adding a
   third track means adding a `ref_repo/<track>/` directory, not changing the pattern
6. **Model weights stay out.** `.gitignore` also excludes `*.tflite`, `*.task`, `*.blob`,
   `*.caffemodel` and similar, against the 5 GB submission limit — `CLD_S6` rule 5

---





# 6. CHANGE LOG
1. **2026-08-28** · *Author:* Claude (Opus 5)
   *Change:* Created. Registered `RIX`, `CLD`, `RDM`, `SCR`, `JCR`, `ARC`, `RSK`, `TRN`, `APL`,
   `SYN`, `D1`–`D6`, `REF`. Reserved `PLN`, `TDO`, `EVL`, `DEC`.
2. **2026-08-28** · *Author:* Claude (Opus 5)
   *Change:* Reformatted to the revised conventions: bold title, collapsible `# METADATA`, `#`-level
   numbered sections, HTML anchors removed, padded tables, third-person voice. Added
   [`RIX_S4.7`](#47-placeholders) and [`RIX_S4.9`](#49-tone).
3. **2026-08-28** · *Author:* Claude (Opus 5)
   *Change:* Added [`RIX_S4.4`](#44-vertical-spacing) (vertical spacing before headings) and
   reworked [`RIX_S4.5`](#45-tables-and-numbered-lists) into the table-versus-numbered-list rule;
   renumbered the sections that follow. Converted every table whose rows exceeded 100 characters
   into a numbered list.
4. **2026-08-30** · *Author:* Claude (Opus 5)
   *Change:* Registered the three new reference repositories. Retired `APL`, `SYN` and `REF`;
   introduced the systematic repository-code pattern in
   [`RIX_S3.5`](#35-repository-document-codes) and registered `RAP`/`APR`/`APS`,
   `RMP`/`MPR`/`MPS`, `RDH`/`DHR`/`DHS` and `ROP`/`OPR`/`OPS`. Full reports now live beside the
   clone they describe in `ref_repo/`; syntheses live in `doc/`. Added
   [`RIX_S5.2`](#52-what-version-control-tracks) for the `.gitignore` rules that exclude the clones
   while tracking the reports, and redrew the directory map.
5. **2026-09-04** · *Author:* Claude (Opus 5)
   *Change:* Regrouped `ref_repo/` into `tracking/` and `translation/`, repathing `APR`, `MPR`,
   `DHR` and `OPR` and every reference to them. Registered the six translation repositories and
   their twelve documents: `RSL`/`SLR`/`SLS`, `RSA`/`SAR`/`SAS`, `RSP`/`SPR`/`SPS`,
   `RSS`/`SSR`/`SSS`, `RLT`/`LTR`/`LTS` and `RST`/`STR`/`STS`. Split
   [`RIX_S3.5`](#35-repository-document-codes) into a table per track and noted the `SLR`
   code/field-term collision. Redrew the directory map.
   **Corrected [`RIX_S5.2`](#52-what-version-control-tracks):** the `ref_repo/**` block it
   described was **never present in `.gitignore`**, and the four tracking clones were committed as
   embedded-repository gitlinks. The block is now written, at the new three-level depth, and
   consequence 5 records that the depth is load-bearing.
6. **2026-09-05** · *Author:* Claude (Opus 5)
   *Change:* Registered [`PLN`](plan/PLN_plan.md) as item 8 of
   [`RIX_S2.1`](#21-live-documents), status **Draft**, and renumbered the twenty
   reference-repository documents that follow to 10–29. **The filename is `plan/PLN_plan.md`, not
   the `plan/PLN_master_plan.md` reserved in 2026-08-28**; the reservation is superseded, the code
   is unchanged. Removed `PLN` from [`RIX_S2.2`](#22-planned-documents) and restated what now
   blocks `TDO`, `EVL` and `DEC`: `EVL` is unblocked and is task `T8.1`, and `DEC` waits on the
   named person rather than on `PLN`. Added `PLN` to the directory map in
   [`RIX_S5`](#5-directory-map).
