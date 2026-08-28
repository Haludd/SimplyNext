**JUDGING CRITERIA — SIMPLIFYNEXT AGENTIC AI HACKATHON 2026**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field                   | Value                                                    |
| :---------------------- | :------------------------------------------------------- |
| **Code**                | `JCR`                                                    |
| **Status**              | Live                                                     |
| **Last reviewed**       | 2026-08-28                                               |
| **Source of truth for** | How the submission is scored                             |
| **Source**              | `doc/[D3]_Hackathon_Training_Session_3.pdf`, slides 5–49 |

**Related.** [`ARC`](ARC_architecture.md) · [`RSK`](RSK_risk_register.md) ·
[`TRN_S4`](../doc/TRN_training_synthesis.md#4-d3--framing-classes-practices-case-studies)

**For the team.** Everything that determines the score, extracted from training deck `D3`. This is
the specification the project is built against. [`JCR_S8`](#8-self-scoring-checklist) is the pre-submission
checklist.

**For the assistant.** `D3` is a training deck, not the competition rulebook. Where an official
rules document or the submission portal states something different, it overrides this file; record
the change in [`JCR_S10`](#10-change-log). Quotations from `D3` are verbatim and keep their original
wording.

</details>

---





# 1. THE SCORE AT A GLANCE
## 1.1. Five Criteria, 20% Each, Scored 0–2
| #   | Criterion                                     | Weight | Max | `D3` slide |
| :-- | :-------------------------------------------- | :----- | :-- | :--------- |
| C1  | Benefits delivered by the solution            | 20%    | 2   | `D3_p39`   |
| C2  | Original / innovative idea                    | 20%    | 2   | `D3_p39`   |
| C3  | Effectiveness of the solution                 | 20%    | 2   | `D3_p40`   |
| C4  | Technical quality and superiority of solution | 20%    | 2   | `D3_p40`   |
| C5  | Presentation                                  | 20%    | 2   | `D3_p41`   |

**Total: 10 points across 5 equally-weighted criteria.**

> **Decision implication.** Equal weights mean that an excellent model nobody can explain scores
> exactly the same as a mediocre model that is explained well. Two of the five criteria (C2, C5)
> are won at the desk rather than in the code, and team time should be budgeted accordingly.




## 1.2. Where Each Criterion Is Judged
From the *Judging Criteria Alignment* slide (`D3_p38`). The evidence for each criterion has to
appear in a specific artefact — a claim made only in the deck and not visible in the demo or the
code will not carry.

1. **C1 Benefits**
   *`D3`'s instruction, verbatim:* *"Clearly link your features to measurable improvements"*
   *Judged from:* Presentation deck
2. **C2 Originality**
   *`D3`'s instruction, verbatim:* *"Point out what makes your approach different from existing
   solutions"*
   *Judged from:* Solution video / demo
3. **C3 Effectiveness**
   *`D3`'s instruction, verbatim:* *"Use evidence (data, tests, scenarios) to prove it works"*
   *Judged from:* Project files
4. **C4 Technical quality**
   *`D3`'s instruction, verbatim:* *"Show a functional prototype and explain how it is robust"*
   *Judged from:* Project files, demo
5. **C5 Presentation**
   *`D3`'s instruction, verbatim:* *"Structure your story well, rehearse delivery"*
   *Judged from:* Presentation

---





# 2. THE SCORING RUBRICS
Reproduced from `D3_p39–p41`. **The 1-point row of each rubric deserves the closest reading — it
is the row a submission lands on by accident.**




## 2.1. C1 — Benefits Delivered by the Solution (20%)
**Question asked:** *What positive impact does the solution bring to users, the organization, or
the community? Benefits may include increased revenue, productivity, quality, compliance, or
quality of life.*

| Score | Descriptor                                     |
| :---- | :--------------------------------------------- |
| **2** | Clear benefits; **scalable or easily adopted** |
| **1** | Clear benefits                                 |
| **0** | No or limited benefits                         |

> **Note:** the gap between 1 and 2 is a single phrase: *scalable or easily adopted*. Clear
> benefits alone cap the score at 1. The solution must be shown to spread — no special hardware,
> running on a device the user already owns, deployable beyond the demo scenario.




## 2.2. C2 — Original / Innovative Idea (20%)
**Question asked:** *How original and creative is this solution?*

| Score | Descriptor                                                |
| :---- | :-------------------------------------------------------- |
| **2** | Unique and innovative approach to the problem             |
| **1** | Based on existing ideas but addresses the problem         |
| **0** | **Not unique; existing solutions address it effectively** |

> **Warning — the sharpest risk in the rubric.** Sign-language translation is a crowded space with
> well-funded incumbents. A judge who knows of Google's SignGemma, of live-captioning products, or
> of the long history of sign-language gloves can legitimately award **0** here.
> `D3_p6` names this failure mode explicitly as **"The Solved Problem"**: *"A mature product
> already does this well, so the bar for our version sits impossibly high."* Its prescribed fix is
> *"Look for what the existing tools still leave undone."*
>
> Mitigation is an architecture and positioning problem, handled in
> [`ARC_S5`](ARC_architecture.md#5-step-4--skeleton-to-conversational-text), not a slide-writing problem.




## 2.3. C3 — Effectiveness of the Solution (20%)
**Question asked:** *How effective is the solution in addressing the problem or opportunity?*

| Score | Descriptor                                              |
| :---- | :------------------------------------------------------ |
| **2** | Fully addresses and **resolves** the problem            |
| **1** | Partially addresses the problem, but not fully resolved |
| **0** | Minimal effectiveness in solving the problem            |

> **Note:** "fully resolves" is a very high bar for open-ended sign-language translation, and
> over-claiming it is worse than scoping down. The controllable lever is the **width of the problem
> statement**: a narrow, well-chosen scope that is genuinely resolved scores 2; a broad scope only
> partially addressed scores 1. `D3_p6` calls the broad version **"The Boiling Ocean"** and
> prescribes *"Cut one slice we can finish and demonstrate."*




## 2.4. C4 — Technical Quality and Superiority of Solution (20%)
**Question asked:** *Is the prototype functional and technically sound?*

1. **2**
   Technically advanced, fully functional prototype with **minimal work needed for production**
2. **1**
   Functional prototype with **minor work** needed for production
3. **0**
   Partially functional or does not meet core requirements




## 2.5. C5 — Presentation (20%)
**Question asked:** *How effective is the team in articulating the problem statement and
explaining how the solution tackles the problem and delivers the benefits?*

| Score | Descriptor                                                             |
| :---- | :--------------------------------------------------------------------- |
| **2** | Clearly explained the problem and demonstrated the solution's benefits |
| **1** | Partially explained, with **some prompting or clarification needed**   |
| **0** | Unable to clearly explain the problem or demonstrate benefits          |

> **Note:** "some prompting or clarification needed" means a judge had to ask a follow-up. A Q&A
> question beginning *"So what actually happens when…"* indicates the score has already dropped to
> 1. Rehearse the mechanism explanation, not only the pitch.

---





# 3. DELIVERABLES
From `D3_p37` and `D3_p42`.




## 3.1. Required Submissions
1. **Project files / workflow**
   **Max 5 GB. One submission only**
2. **Presentation deck**
   **Max 10 slides**
3. Digital solution video **or** video recording of simulation
   **Max 5 minutes**

`D3_p37` states that the deliverables should, in the deck's own words:

> - **Answer the question** — clearly explain the problem and your innovative solution.
> - **Showcase your knowledge of Agentic AI** — technical soundness and functionality.
> - **Create business impact** — demonstrate that the solution addresses the problem statement.




## 3.2. Project Files
Verbatim requirements from `D3_p42`:

> Build a **simple proof-of-concept** to demonstrate your Agentic AI component.

1. **Documentation**
   Keep it concise. A good `README` will suffice, covering (a) instructions to run the code, (b) an
   overview of the code and the purpose of each script or file
2. **Environment setup**
   Virtual environments — provide `requirements.txt`. Docker setup is also acceptable. Path
   variables. Secrets and keys in `.env` files
3. **Language / stack**
   **Python is strongly recommended**
4. **Execution**
   No extensive test data required. Judges check: (1) whether the solution can run as demonstrated
   in the video; (2) whether the presentation methodology is reflected at code level — in-line
   documentation where relevant would be helpful; (3) **testing and evaluation must be covered in
   the slides**

> **Decision:** point (2) — *"if presentation methodology is reflective at code level"* — means the
> architecture diagram on the slide must map onto real module names in the repository. The modules
> are named after the diagram, not the other way round.




## 3.3. Development Best Practices
From `D3_p23`:

1. **Code readability**
   Clean, commented code. Clear variable names, consistent formatting. **Organise code to showcase
   application of Agentic AI techniques**
2. **Folder structure**
   A logical hierarchy. *"A good structure might include `src/`, `docs/`, `data/`, and `tests/`"*
3. **Documentation**
   Concise and clean. A good `README.md` is sufficient
4. **Error handling**
   Baseline: error handling for functional resilience. **Going further: make it actionable for
   business users**

---





# 4. PROBLEM STATEMENT
`D3_p10` is explicit that the problem statement and the solution overview answer **different
questions and are both graded**. It is the highest-leverage page in `D3`.




## 4.1. The Hackathon Theme
From `D3_p5`, *Design for a World in Transformation*:

> Change is everywhere — in how we live, learn, and relate to one another. Transformation takes
> time, effort, and the right support at the right moment. […] We envision a solution that
> **plans, acts, and adapts over time**. Your team will choose the problem and decide who it
> serves. You will design a solution that **thinks ahead, takes action, and leaves people
> genuinely better off**.




## 4.2. Required Format
`D3_p6` — the **POV format**:

```text
[User] needs [a way to ...] because [insight].
```

Worked example given: *"A caregiver needs a reliable way to track daily medication because missed
doses lead to avoidable hospital visits."*




## 4.3. Problem Statement Failure Modes
`D3_p7`. Check the statement against **all six** before writing any code.

1. **The Solution in Disguise**
   *Symptom:* The statement describes the thing the team already decided to build
   *Fix `D3` prescribes:* Name the person and the moment they are stuck
2. **The Everyone Problem**
   *Symptom:* The user is all of humanity, so no design decision follows
   *Fix `D3` prescribes:* Choose one person who can be pictured and described
3. **The Missing Because**
   *Symptom:* A need asserted with nothing behind it
   *Fix `D3` prescribes:* Find the evidence, then write the insight it supports
4. **The Boiling Ocean**
   *Symptom:* True, enormous, beyond what any team can move in four days
   *Fix `D3` prescribes:* Cut one slice we can finish and demonstrate
5. **The Solved Problem**
   *Symptom:* A mature product already does this well
   *Fix `D3` prescribes:* Look for what the existing tools still leave undone
6. **The Comfortable Guess**
   *Symptom:* Written from the team's imagination, no contact with anyone who lives the problem
   *Fix `D3` prescribes:* Talk to two real users this week and rewrite after

> **The fastest available check** (`D3_p7`): read the statement aloud to someone outside the team.
> **If they ask what is being built, the statement is still doing its job.**




## 4.4. Five Pressure-Test Questions
`D3_p9`. Any *no* returns the team to Empathise before code is written.

1. **Can one person be named?**
   A role at a moment, specific enough to picture them walking into the room. *"Users"* and
   *"people"* will not pass
2. **Can the evidence be cited?**
   A figure, a source, and a date. *"It feels true"* is an assumption to be tested
3. **Would that person recognise themselves?**
   The team has spoken with at least one of them
4. **Does it survive a different solution?**
   The statement still holds if another team builds something completely unlike this one
5. *(implied)* Would this problem exist without agentic AI?
   **Yes** = a problem statement. **No** = a product pitch; start again

> **`D3_p9` calls question 4 the sharpest one:** *"A statement that only makes sense once we
> describe our own build has quietly become a product pitch."*




## 4.5. Problem Statement vs Solution Overview
`D3_p10`:

| The problem statement                       | The solution overview                        |
| :------------------------------------------ | :------------------------------------------- |
| Names a role at a specific moment           | Names the planning, acting and adapting      |
| Carries evidence with a source              | Explains what a fixed workflow would miss    |
| Stays true whatever anyone builds           | Shows the reasoning a judge can follow       |
| Reads as plainly as a sentence spoken aloud | Connects each capability to the person above |

**The separating test:** *Would this problem still exist if agentic AI had never been invented?*

---





# 5. EVALUATION AND METRICS
`D3_p24` requires testing to be covered, and `D3_p42` requires it to appear **in the slides**.




## 5.1. Requirements from `D3_p24`
> **Accuracy testing** — Understand the difference in nuance compared to traditional ML accuracy
> measurements (e.g. Precision/Recall, F-1). *"Are Agentic AI results always Yes/No?"*
>
> **Evaluation metrics** — Identify relevant data points to be captured, in translation to the
> Problem Statement & Solution Objective. **Justify your testing methodology.**




## 5.2. Suggested Digital-Agent Metrics
From `D3_p32`. These are examples rather than a mandated set; using their vocabulary is free marks
under C4.

| #   | Metric                      | The question it answers                     |
| :-- | :-------------------------- | :------------------------------------------ |
| 1   | Schema validation pass rate | *Is the output usable by another system?*   |
| 2   | Tool-call success rate      | *Does the agent reach for the right hands?* |
| 3   | Task completion rate        | *Did it carry the job to the end?*          |
| 4   | Token cost per run          | *What does one answer actually cost?*       |
| 5   | Loop discipline             | *Is it converging or circling?*             |
| 6   | Answer fidelity             | *Is it right, as well as plausible?*        |




## 5.3. Physical-AI Metrics (For Reference)
`D3_p35`, where any part of the solution is framed as perception-in-the-world: task success rate,
**intervention rate** (*"the honest measure of autonomy"*), safety record, cycle time,
**robustness** (*"re-test under changed lighting, terrain, clutter and starting position"*).

> **Note:** *robustness* and *intervention rate* both transfer directly to this product and are
> more honest than accuracy alone. See [`ARC_S8`](ARC_architecture.md#8-cost-model-against-the-aws-cap).

---





# 6. THE 10-SLIDE DECK
## 6.1. Suggested Structure
`D3_p43`:

1.  **Title & team**
    Names, roles, and a one-line mission statement
2.  **Problem statement / why it matters**
    The real-world issue, **backed by data**, and why solving it matters for the public good
3.  **Solution overview**
    What the agentic AI does and why it is different
4.  **Methodology**
    Functional overview of the solution
5.  **Technical architecture**
    High-level system design, components, tech stack
6.  **Innovation & uniqueness**
    How the approach stands out
7.  **Benefits delivered**
    Quantified improvements or advantages
8.  **Demo preview**
    Screenshots or flow of the live or recorded demo
9.  **Roadmap & future potential**
    Where the solution can go next
10. **Conclusion & call to action**
    Recap and inspire adoption




## 6.2. Content Rules
`D3_p44`:

- One core message per slide. Do not overcrowd.
- Use visuals where relevant — diagrams, icons, infographics.
- Consistent branding: colours, fonts, style.
- **Tie each slide to a judging criterion** (impact, originality, effectiveness, technical quality, presentation).
- Avoid generic claims; use data or real examples.
  - Instead of *"Improves efficiency"*, say *"Reduces processing time by 30%"*.




## 6.3. Worked Examples
`D3_p45` — problem & impact slide:

1. **✅ Clear statement.** *"1 in 4 adults experience mental health issues annually, but only 40%
   receive treatment."*
   **❌** *"Mental health is a big problem everywhere."* — too vague
2. **✅ Credible data.** *"WHO reports depression costs the global economy $1 trillion yearly."*
   **❌** *"This issue affects everyone in the world."* — too broad, no focus
3. **✅ User story.** *"Meet Jane, a university student who struggles to access timely support."*
   **❌** *"Our solution will change the world."* — buzzwords, no evidence
4. **✅ Connected to public good.** *"Lack of early intervention leads to worsening conditions and
   higher healthcare costs."*

`D3_p46` — solution & technical flow slide:

1. **✅ Plain language.** *"Our AI agent detects early signs of stress from daily mood check-ins."*
   **❌** *"We built a GPT-4 + RLHF + custom neural net…"* — jargon-heavy, no context
2. **✅ Show the flow:** **inputs → AI reasoning → actions → feedback**
   **❌** Only listing features: *"Chatbot + API + dashboard"* — no user benefit
3. **✅ Name the agentic features.** *"Plans personalized activities, adapts based on user
   responses."*
   **❌** No diagram or flow
4. **✅ Keep the tech stack relevant and short.**
   **❌** Forgetting to link how features actually improve outcomes

---





# 7. THE 5-MINUTE DEMO VIDEO
## 7.1. Suggested Breakdown
`D3_p47`:

| Time      | Section                                                            |
| :-------- | :----------------------------------------------------------------- |
| 0:00–0:30 | **Opening hook** — start with a relatable story or bold fact       |
| 0:30–1:00 | **Problem explanation** — show the problem in action               |
| 1:00–1:30 | **Solution overview** — state how the solution addresses the issue |
| 1:30–3:30 | **Live or recorded demo** — walk through features, show it working |
| 3:30–4:15 | **Impact & benefits** — show before/after or metrics               |
| 4:15–5:00 | **Closing & call to action** — end with a vision, invite adoption  |




## 7.2. Delivery Rules
`D3_p48`:

- **Show, don't just tell** — demonstrate the AI making a decision or taking action.
- Highlight the agentic features: **where does it plan, act, adapt?**
- Use clear voiceover **or captions for accessibility**.
- Avoid jargon, or explain terms briefly.
- Pace the delivery — five minutes is short.
- *"If showing an AI chatbot, don't just show the interface — narrate the reasoning process behind its responses."*

> **Note:** the captions-for-accessibility line carries extra weight here. A sign-language
> accessibility product whose own demo video is uncaptioned is a self-inflicted wound in front of
> exactly the judges most likely to notice. Caption the video, and have a Deaf or hard-of-hearing
> reviewer watch it before submission.




## 7.3. Final Presentation Tips
`D3_p49`:

- Focus on a **strong problem statement within reach**.
- Make the value obvious to judges **in the first minute**.
- Keep a logical flow: **problem → solution → impact**.
- Practise with the team to ensure smooth delivery within time limits.
- End with a powerful call to action.

---





# 8. SELF-SCORING CHECKLIST
Run before submission. Every unchecked box is a point given away.




## 8.1. C1 — Benefits (Target: 2)
- [ ] The benefit is stated as a **number with a source**, not an adjective.
- [ ] The specific person who is better off, and the moment they are better off, can be named.
- [ ] **Scalability or ease of adoption** is shown — no special hardware, runs on a device the user already owns, works beyond the demo scenario.
- [ ] The benefit survives the question *"compared to what they do today?"*




## 8.2. C2 — Originality (Target: 2)
- [ ] The existing solutions are named **explicitly**, with what each leaves undone stated precisely.
- [ ] The differentiator is a **capability**, not a claim of being better.
- [ ] *"Why has a large company not already shipped this?"* has an answer that does not hand-wave.
- [ ] The agentic component is the reason for the differentiator, not a bolt-on.




## 8.3. C3 — Effectiveness (Target: 2)
- [ ] The problem statement is **narrow enough to be genuinely resolved**.
- [ ] Evidence exists: data, tests, or scenarios — not a single happy-path demonstration.
- [ ] At least one **failure case, and how the system handles it**, is shown.
- [ ] The evaluation is in the slides (`D3_p42` requires this).




## 8.4. C4 — Technical Quality (Target: 2)
- [ ] The prototype **runs from a clean clone** following only the `README`.
- [ ] `requirements.txt` (or Docker) present; secrets in `.env`; no keys committed.
- [ ] Folder structure is `src/` `docs/` `data/` `tests/` or similarly legible.
- [ ] Module names **match the architecture diagram on the slide**.
- [ ] Error handling exists and is **actionable for a business user**, not just a stack trace.
- [ ] Loops are bounded by a counter held in state (`D3_p22`).
- [ ] Token usage is logged per run (`D3_p32`, metric 4).




## 8.5. C5 — Presentation (Target: 2)
- [ ] Deck is **10 slides or fewer**; video is **5 minutes or under**.
- [ ] Each slide maps to a criterion (`D3_p44`).
- [ ] The value is obvious in the first minute.
- [ ] The demo shows the AI **deciding**, not just the UI.
- [ ] The video is **captioned**.
- [ ] The mechanism explanation is rehearsed, not only the pitch, so that no judge has to prompt.
- [ ] Someone outside the team has heard the problem statement read aloud and did **not** ask what is being built.

---





# 9. SOURCES
1. **`[S1]`**
   *Source:* `doc/[D3]_Hackathon_Training_Session_3.pdf` — slides 5–10, 22–24, 32, 35, 37–49.
   Primary and authoritative for this document
   *Reliability:* Official (organiser)
2. **`[S2]`**
   *Source:* NUS Centre for Future-ready Graduates event listing, *SimplifyNext Agentic AI Hackathon
   2026* — https://nus.edu.sg/cfg/events/details/a5782200ddb15305672ee3426b4f4753
   *Reliability:* Official (partner institution)
3. **`[S3]`**
   *Source:* Hackathon site — https://hackathon.simplifynext.com/ ⚠ page renders client-side and
   could not be read programmatically
   *Reliability:* Official; unverified

> **Placeholder — official rules confirmation.**
> **Missing:** dates, prizes and any criteria updates published on `[S3]`, which could not be read
> programmatically.
> **Update trigger:** a team member opens the page and reports what it states; where it differs
> from `D3`, the page overrides this document.
> **Owner:** team.

---





# 10. CHANGE LOG
1. **2026-08-28** · *Author:* Claude (Opus 5)
   *Change:* Created. Extracted criteria, weights, rubrics, deliverables, deck and video structure
   from `D3` slides 5–49. Added self-scoring checklist.
2. **2026-08-28** · *Author:* Claude (Opus 5)
   *Change:* Reformatted to the revised conventions in
   [`RIX_S4`](../ref_index.md#4-markdown-formatting-rules): bold title, collapsible `# METADATA`,
   `#`-level numbered sections, HTML anchors removed, padded tables, third-person voice,
   placeholders for unfinished content.
3. **2026-08-28** · *Author:* Claude (Opus 5)
   *Change:* Applied the revised [`RIX_S4.4`](../#44-vertical-spacing) heading spacing and the
   [`RIX_S4.5`](../#45-tables-and-numbered-lists) table-versus-numbered-list rule: tables whose rows exceeded 100
   characters became numbered lists.
