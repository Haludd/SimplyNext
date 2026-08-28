**RULES FOR AI AGENTS IN THIS REPOSITORY**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field                   | Value                                      |
| :---------------------- | :----------------------------------------- |
| **Code**                | `CLD`                                      |
| **Status**              | Live                                       |
| **Last reviewed**       | 2026-08-28                                 |
| **Source of truth for** | Agent behaviour in this repository         |
| **Related**             | [`RIX`](ref_index.md) · [`RDM`](README.md) |

**For the team.** This file constrains what an AI agent may do here. Amend it whenever a working
rule changes; agents follow it literally.

**For the assistant.** Read this file first, then [`ref_index.md`](ref_index.md), before any other
action in this repository.

</details>

---





# 1. THE STANDING RULE
## 1.1. Check the Reference Index First
At the start of every prompt, before any other action, read [`ref_index.md`](ref_index.md) (`RIX`).
It is the single source of truth for:

- which documents exist and where they live — [`RIX_S2`](ref_index.md#2-document-registry);
- the `<CODE>_S<section>` addressing scheme — [`RIX_S3`](ref_index.md#3-addressing-scheme);
- the markdown formatting rules every file must follow —
  [`RIX_S4`](ref_index.md#4-markdown-formatting-rules).

The file changes. Do not work from a remembered version of it.




## 1.2. Keep the Registry Current
Creating, moving, renaming, splitting or retiring a document requires updating
[`RIX_S2`](ref_index.md#2-document-registry) in the same change. An unregistered document does not
exist as far as the team is concerned.

---





# 2. WHAT THIS PROJECT IS
A working prototype for the **SimplifyNext Agentic AI Hackathon 2026**: software that translates
sign language into conversational text or audio in real time, from ordinary camera video, with no
gloves or wearables.

| Question                              | Document                                    |
| :------------------------------------ | :------------------------------------------ |
| What is being built, and why          | [`SCR`](plan/scribbles.md) — product intent |
| How the submission is scored          | [`JCR`](plan/JCR_judging_criteria.md)       |
| The technical direction, with sources | [`ARC`](plan/ARC_architecture.md)           |
| What can go wrong                     | [`RSK`](plan/RSK_risk_register.md)          |
| What the training decks require       | [`TRN`](doc/TRN_training_synthesis.md)      |
| The Apple reference repository        | [`APL`](doc/APL_apple_ref_report.md)        |

---





# 3. DOCUMENT RULES
## 3.1. Writing Documents
1.  Follow [`RIX_S4`](ref_index.md#4-markdown-formatting-rules) exactly: bold title, collapsible `# METADATA` block,
    heading ladder, vertical spacing, `---` between `#` sections, padded tables
2.  The title is bold text, never a heading. `#` is reserved for numbered sections: `# 1. ALL CAPS`,
    `## 1.1. Caps Initials Only`, `### 1.1.1. First character only`
3.  Every document opens with a collapsible `# METADATA` section immediately after the title,
    carrying the document's code, status, last-reviewed date, and instructions for human and AI
    readers — [`RIX_S4.2`](ref_index.md#42-metadata-block)
4.  Do not add HTML anchors above headings. Addresses resolve from the document code and the printed
    section number — [`RIX_S3.4`](ref_index.md#34-resolving-an-address)
5.  **Choose between a table and a numbered list by width.** Content that fits on one line stays a
    table; content that would spill past 100 characters becomes a numbered list —
    [`RIX_S4.5`](ref_index.md#45-tables-and-numbered-lists)
6.  In the tables that remain, pad every column to the width of its longest cell and fill empty
    cells with a centred `---`
7.  **Leave blank lines before every heading:** five before `#`, four before `##`, three before
    `###`. Never leave a blank line after a heading — [`RIX_S4.4`](ref_index.md#44-vertical-spacing)
8.  Register the document's three-letter code in [`RIX_S2`](ref_index.md#2-document-registry) before or with
    creation
9.  Filenames are `<CODE>_<snake_case_name>.md`, except `README.md`, `CLAUDE.md`, `ref_index.md`,
    `plan/scribbles.md`
10. Every external factual claim carries a source tag resolving to a `# N. SOURCES` section with a
    full URL
11. Mark unverified or preprint-based claims with `⚠` and state why. Never state an unverified thing
    plainly
12. Every document in `plan/` carries a `# N. CHANGE LOG`. Add a line when it changes
13. Dates are absolute (`2026-08-28`)
14. Cross-reference by address — `` [`ARC_S7.1`](plan/ARC_architecture.md#71-comparison-table) `` — never by
    prose description




## 3.2. Tone and Placeholders
1. Write in the third person. No first- or second-person pronouns: "the team", "the assistant",
   "this document". Verbatim quotations keep their original wording
2. Headings and emphasis points state the idea in the fewest words that carry it. No conversational
   framing, rhetorical questions, or invented reader scenarios
3. Where content is unavailable or undecided, insert a `> **Placeholder:**` callout naming what is
   missing, the update trigger, and the owner — [`RIX_S4.7`](ref_index.md#47-placeholders). Do not
   approximate the content instead




## 3.3. Where Things Go
1. **`plan/`** · *Never:* Third-party material
   *Contents:* Plans, decisions, risks, criteria, to-dos, evaluation protocol
2. **`doc/`** · *Never:* Project plans
   *Contents:* Training decks, external references, syntheses of them
3. **`ref_repo/`** · *Never:* Project source code
   *Contents:* Unmodified third-party repositories, plus one synthesis file each
4. **`src/` *(future)*** · *Never:* Documents
   *Contents:* Implementation




## 3.4. Do Not Edit
- The six PDFs in `doc/` — they are primary sources.
- Anything inside `ref_repo/apple/` **except** `SYN_apple_synthesis.md`.
- The body of `plan/scribbles.md` — it is the team's raw ideation. Cross-references and formatting
  may be maintained; the wording may not be rewritten.

---





# 4. HARD CONSTRAINTS FROM THE COMPETITION
These are not preferences. They come from the organiser's own decks — see
[`TRN_S7`](doc/TRN_training_synthesis.md#7-cross-cutting-rules).

1.  **Python is strongly recommended** for the implementation · *Source:* `D3_p42`
2.  **Ship `requirements.txt` or a Docker setup** · *Source:* `D3_p42`
3.  Secrets in `.env`. **Never commit a key** · *Source:* `D3_p42`
4.  **Folder structure: `src/`, `docs/`, `data/`, `tests/`** · *Source:* `D3_p23`
5.  **The `README` must let a judge run the code** · *Source:* `D3_p42`
6.  **The architecture on the slide must match module names in the repository** · *Source:* `D3_p42`
7.  **Bound every agent loop** with a counter held in state · *Source:* `D3_p22`
8.  **Read model IDs from a constant; never build them** · *Source:* `D3`
9.  **Heavy payloads live in graph State, never in a prompt** · *Source:* `D2`
10. **Log token usage on every model call** · *Source:* `D1`, `D3_p32`
11. **AWS spend stays under US$20.** At $20 access is revoked; at $30 the account is terminated ·
    *Source:* `D6`
12. 10 slides · 5 minutes · 5 GB · **one submission only** · *Source:* `D3_p37`, `D3_p42`

---





# 5. CONDUCT ON THIS PROJECT
## 5.1. Evidence
The competition grades evidence —
[`JCR_S4.4`](plan/JCR_judging_criteria.md#44-five-pressure-test-questions) demands *"a figure, a
source, and a date"*. The same standard applies to everything written here.

- Prefer official and peer-reviewed sources. Cite the URL.
- Where only a preprint or a secondary reproduction is available, say so with `⚠`.
- Never invent a statistic, a benchmark number, or a citation.
- Where something cannot be verified, record that it could not, and state what would verify it.




## 5.2. Honesty About the Product
This is an assistive tool for Deaf and hard-of-hearing people. The dominant failure mode is a
**fluent, confident, wrong** output attributed to a real person —
[`RSK_S7.1`](plan/RSK_risk_register.md#71-fabrication).

Two consequences for anything written or built here:

1. **The system never guesses.** Low confidence produces a refusal and a repair action, not a
   sentence. This is a design invariant, not a tuning choice —
   [`ARC_S9`](plan/ARC_architecture.md#9-decisions), decision D8.
2. **Capability is never overstated** in documentation, slides, code comments or commit messages.
   A closed-vocabulary demonstration is described as a closed-vocabulary demonstration.




## 5.3. Scope
`D3_p7` names *"The Boiling Ocean"* as a graded failure, and
[`RSK_S9`](plan/RSK_risk_register.md#9-delivery-and-competition) rates scope creep (`DEL-12`)
`S3`/`L3`. Do the task asked. Where adjacent work is worth doing, name it and leave the decision to
the team.




## 5.4. Working with the Reference Repository
`ref_repo/apple/` is Apple's WWDC20 `HandPose` sample — **iOS, not Apple Vision Pro**. Do not
repeat that error in any document or slide. See
[`APL_S1.1`](doc/APL_apple_ref_report.md#11-what-this-repository-is).

When porting ideas from it: Vision's normalised coordinate space has its origin at the
**bottom-left**; MediaPipe's at the **top-left**. Copying Apple's `y = 1 - y` line into a MediaPipe
pipeline flips the image. See
[`APL_S10.2`](doc/APL_apple_ref_report.md#102-swift--python-port-table).

---





# 6. GIT
1. Commit or push only when asked
2. Never commit `.env`, credentials, AWS keys, or the 2FA secret from `D6`
3. Never commit recorded video of a person without documented consent —
   [`RSK_S8.3`](plan/RSK_risk_register.md#83-privacy-and-data-protection)
4. Keep the `ref_index.md` update in the same commit as the document change it describes
5. Do not add training data or model weights without checking the 5 GB submission limit

---





# 7. CHANGE LOG
1. **2026-08-28** · *Author:* Claude (Opus 5)
   *Change:* Created. Standing rule to check `ref_index.md`; document, scope, evidence and honesty
   rules; competition hard constraints; git rules.
2. **2026-08-28** · *Author:* Claude (Opus 5)
   *Change:* Added the mandatory `# METADATA` block rule, the revised heading ladder, the
   no-HTML-anchor rule, table padding, and [`CLD_S3.2`](#32-tone-and-placeholders) on tone and
   placeholders.
3. **2026-08-28** · *Author:* Claude (Opus 5)
   *Change:* Added the table-versus-numbered-list rule and the heading-spacing rule to
   [`CLD_S3.1`](#31-writing-documents); converted the over-width rule tables in this file into numbered
   lists.
