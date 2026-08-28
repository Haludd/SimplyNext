**SCRIBBLES — RAW IDEATION**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field                          | Value                    |
| :----------------------------- | :----------------------- |
| **Code**                       | `SCR`                    |
| **Status**                     | Live                     |
| **Last reviewed**              | 2026-08-28               |
| **Source of truth for**        | **Product intent**       |
| **Where every document lives** | [`RIX`](../ref_index.md) |

**For the team.** This document is the team's raw ideation, used for ideation with AI. Its body is
kept as written. Analysis and decisions live in the documents named below.

**For the assistant.** Do not rewrite the body. Section numbering and cross-references may be
maintained; the wording may not be changed — [`CLD_S3.4`](../CLAUDE.md#34-do-not-edit).

**Where each section is worked out.**

1. **SOLUTION & PRODUCT → Current MVP**
   [`ARC`](ARC_architecture.md) — each of the four steps confirmed or challenged against published
   sources, with alternatives ranked by cost and hardware
2. **EVALUATION** (areas of difficulty)
   [`RSK`](RSK_risk_register.md) — expanded into 136 catalogued issues. Problems only; solutions are
   in [`ARC`](ARC_architecture.md)
3. **ISSUES**
   [`ARC_S5.4`](ARC_architecture.md#54-corrections-to-scr--issues) — "training an LLM" is
   **rejected** as a premise, and "memory loss during training" is a category error
4. **RESEARCH AREAS → 1. Read apple repo**
   [`APL`](../doc/APL_apple_ref_report.md) (full) ·
   [`SYN`](../ref_repo/apple/SYN_apple_synthesis.md) (short version)
5. **CONTEXT → competition information**
   [`JCR`](JCR_judging_criteria.md) — judging criteria and deliverables ·
   [`TRN`](../doc/TRN_training_synthesis.md) — all six training decks

</details>

---





# 1. CONTEXT
We are building a working prototype, preferably production grade, for a Hackathon called SimplifyNext Agentic AI Hackathon. Refer to SimplifyNext or NUS' official websites for further information regarding the competition (timeline, past winners' solutions, ...)

---





# 2. PROBLEM
There still exists a communication or language barrier between hearing-loss people and those who do not suffer from this condition. They often rely on sign language (not everybody can converse in sign language) or technological solutions to type out what they want to say (disrupts normal conversational flow).

---





# 3. SOLUTION & PRODUCT
We want to develop a software which seamlessly translates sign-language to conversational text or audio in real-time. This idea took inspiration from auto-captioning function in video streaming platforms such as youtube as well as Google Translate and other similar products.

The software runs on phones, tablets, computers, augmented-reality / smart glasses, essentially any devices that has visual capturing / video features. Without using gloves to translate sign language (which requires the "speaker" to wear the glove device), we want the software to rely entirely on visual data and to produce sensible conversational output in either audio or text form.

Current MVP (concept):
1. Recognise the focus and isolate the person(s) from environment noises (other people within the camera's peripheral, ...).
2. Track multiple points (as many as possible to acquire coherent conversation) on the hands and face (if necessary).
3. Translate the points' motion into a 3D skeleton.
4. Use the skeleton's movements / behaviours to translate them into coherent conversational text / audio

---





# 4. EVALUATION
These are some areas of difficulty:
1. Covered / invisible hand movement - use AI to fill in context
2. Multiple people performing sign language - auto-captioning different input streams
3. Environment noises (glare, distracting movement, ...) - Google Meet & Zoom blur background
4. Depth perception
5. Motion blur

---





# 5. ISSUES
1. Training LLM (methodology)
2. AI memory loss (during training) or hallucination

---





# 6. RESEARCH AREAS
1. Read apple repo 
2. Model training
3. Research solutions on areas of difficulty

---





# 7. CHANGE LOG
The body of this document is not edited. This log records formatting and cross-reference changes
only.

1. **2026-08-28** · *Author:* Claude (Opus 5)
   *Change:* Reformatted to the revised conventions in
   [`RIX_S4`](../ref_index.md#4-markdown-formatting-rules): bold title, collapsible `# METADATA`,
   numbered `#`-level sections. Body wording unchanged.
2. **2026-08-28** · *Author:* Claude (Opus 5)
   *Change:* Applied the revised [`RIX_S4.4`](../#44-vertical-spacing) heading spacing and the
   [`RIX_S4.5`](../#45-tables-and-numbered-lists) table-versus-numbered-list rule: tables whose rows exceeded 100
   characters became numbered lists.
