**REFERENCE INDEX**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field                   | Value                                                      |
| :---------------------- | :--------------------------------------------------------- |
| **Code**                | `RIX`                                                      |
| **Status**              | Live                                                       |
| **Last reviewed**       | 2026-08-28                                                 |
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
8.  **`TRN`** — `doc/TRN_training_synthesis.md` · *Status:* Live
    *Contents:* Synthesis of all six hackathon training decks
    *SoT for:* Training content
9.  **`APL`** — `doc/APL_apple_ref_report.md` · *Status:* Live
    *Contents:* Technical report on the Apple reference repository
    *SoT for:* Apple repository analysis
10. **`SYN`** — `ref_repo/apple/SYN_apple_synthesis.md` · *Status:* Live
    *Contents:* Short in-place synthesis of the Apple repository; defers to `APL`




## 2.2. Planned Documents
Codes reserved; files not yet created.

1. **`PLN`** — `plan/PLN_master_plan.md`
   *Contents:* Master implementation plan; parent of all feature plans
   *Blocked on:* Architecture sign-off — [`ARC_S9`](plan/ARC_architecture.md#9-decisions)
2. **`TDO`** — `plan/TDO_todo.md`
   *Contents:* Live task board
   *Blocked on:* `PLN`
3. **`EVL`** — `plan/EVL_eval_protocol.md`
   *Contents:* Test data, metrics, measurement methodology — see
   [`JCR_S5`](plan/JCR_judging_criteria.md#5-evaluation-and-metrics)
   *Blocked on:* `PLN`
4. **`DEC`** — `plan/DEC_deck_outline.md`
   *Contents:* Ten-slide submission deck outline — see
   [`JCR_S6`](plan/JCR_judging_criteria.md#6-the-10-slide-deck)
   *Blocked on:* `PLN`




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
7. **`REF`**
   *File:* `ref_repo/apple/`
   *Contents:* Apple `HandPose` sample code (Swift, WWDC20)
   *Synthesised in:* [`APL`](doc/APL_apple_ref_report.md)




## 2.4. Retired Codes
| Code | File | Retired on | Reason |
| :--- | :--- | :--------- | :----- |
| :--- | :--- | :--------- | :----- |

---





# 3. ADDRESSING SCHEME
## 3.1. Address Format
```text
<CODE>_S<section>[.<sub>[.<sub>]]

APL_S4        → doc/APL_apple_ref_report.md, section 4
APL_S4.2      → ... section 4.2
RSK_S3.1      → plan/RSK_risk_register.md, section 3.1
D3_p39        → doc/[D3]_..., slide 39        (source PDFs use page addresses)
REF:CameraViewController.swift:212            (a line in the Apple reference repository)
```

Risk items carry their own stable IDs on top of the section address — see
[`RSK_S1.3`](plan/RSK_risk_register.md#13-identifiers-and-ratings).




## 3.2. Choosing a Code
- Three characters, uppercase, `A–Z` only. No digits, no reuse, no collision with `D1`–`D6`.
- The code compresses the document's real name: `ARChitecture` → `ARC` · `RiSK` → `RSK` ·
  `Judging CRiteria` → `JCR` · `APpLe` → `APL` · `TRaiNing` → `TRN` · `SYNthesis` → `SYN` ·
  `Reference IndeX` → `RIX`.




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
| Deeper          |     ---      |         ---          | Use a bold lead-in or a table instead |

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
├── ref_index.md                     RIX — registry, addressing, formatting
├── README.md                        RDM — human entry point
├── CLAUDE.md                        CLD — rules for AI agents
│
├── plan/                            what the team is building
│   ├── scribbles.md                 SCR — raw ideation (product intent)
│   ├── JCR_judging_criteria.md      JCR
│   ├── ARC_architecture.md          ARC
│   └── RSK_risk_register.md         RSK
│
├── doc/                             reference and supporting material
│   ├── [D1..D6]*.pdf                original training decks (read-only)
│   ├── TRN_training_synthesis.md    TRN
│   └── APL_apple_ref_report.md      APL
│
└── ref_repo/
    └── apple/                       Apple HandPose sample (Swift, WWDC20)
        └── SYN_apple_synthesis.md   SYN
```




## 5.1. Directory Rules
1. **`plan/`** · *Does not hold:* Third-party material
   *Holds:* Plans, to-dos, decisions, risks, criteria, evaluation protocol
2. **`doc/`** · *Does not hold:* Project plans
   *Holds:* Training decks, external references, and syntheses of them
3. **`ref_repo/`** · *Does not hold:* Project source code
   *Holds:* Unmodified third-party repositories, plus one synthesis file each
4. **`src/` *(future)*** · *Does not hold:* Documents
   *Holds:* Implementation — the folder shape judges expect is in
   [`TRN_S4.3`](doc/TRN_training_synthesis.md#43-development-best-practices)

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
   *Change:* Added [`RIX_S4.4`](#44-vertical-spacing) (vertical spacing before headings) and reworked
   [`RIX_S4.5`](#45-tables-and-numbered-lists) into the table-versus-numbered-list rule; renumbered the sections that
   follow. Converted every table whose rows exceeded 100 characters into a numbered list.
