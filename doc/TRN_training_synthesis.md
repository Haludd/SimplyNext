**TRAINING SYNTHESIS — ALL SIX HACKATHON DECKS**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field                   | Value                 |
| :---------------------- | :-------------------- |
| **Code**                | `TRN`                 |
| **Status**              | Live                  |
| **Last reviewed**       | 2026-08-28            |
| **Source of truth for** | Training content      |
| **Sources**             | `doc/[D1]`–`doc/[D6]` |

**Extracted separately.** [`JCR`](../plan/JCR_judging_criteria.md) — judging criteria,
deliverables, deck and video structure.

**For the team.** Everything in `D1`–`D6` that affects the build, condensed into one place. The
original PDFs remain authoritative; this document points to the right slide.
[`TRN_S7`](#7-cross-cutting-rules) is the consolidated rule list.

**For the assistant.** Quotations are transcribed from the PDF text layer and are verbatim. `D4`
has no text layer, so [`TRN_S5.1`](#51-d4--physical-ai-foundations) is paraphrase from rendered slide images and carries
no quotations; keep it marked `⚠`.

</details>

---





# 1. ORIENTATION
## 1.1. What the Six Documents Are
1. **`D1`** · *Title:* Training Session 1 · *Track:* Digital · *Pages of substance:* ~30 slides
   *Relevant to:* Model calls, prompts, agent loops
2. **`D2`** · *Title:* Training Session 2 · *Track:* Digital · *Pages of substance:* ~25 slides
   *Relevant to:* The orchestration graph and deployment
3. **`D3`** · *Title:* Training Session 3 · *Track:* Both · *Pages of substance:* ~45 slides
   *Relevant to:* **The whole team, twice.** Problem framing, best practices, judging criteria
4. **`D4`** · *Title:* Session 1 Extra · *Track:* Physical · *Pages of substance:* 24 slides
   *Relevant to:* A pivot to robotics only. ⚠ Image-only PDF, no text layer
5. **`D5`** · *Title:* Session 2 Extra · *Track:* Physical · *Pages of substance:* ~12 slides
   *Relevant to:* A pivot to robotics only
6. **`D6`** · *Title:* AWS Access Guide · *Track:* Ops · *Pages of substance:* 24 slides
   *Relevant to:* Whoever holds the AWS lease




## 1.2. The Five Decisive Points
Ranked by effect on the submission:

1. **`D3` slides 5–10 decide the score more than the code does.** The problem statement is graded
   separately from the solution, and six named failure modes each cost points.
   → [`JCR_S4`](../plan/JCR_judging_criteria.md#4-problem-statement)
2. **Judging is five criteria at 20% each, scored 0/1/2.** Two of the five are won at the desk.
   → [`JCR_S2`](../plan/JCR_judging_criteria.md#2-the-scoring-rubrics)
3. **The AWS budget is a kill switch, not a bill.** US$20 revokes access; US$30 terminates the
   account. One lease per group. → [`TRN_S6`](#6-d6--aws-access-and-budget)
4. **Python is strongly recommended, and the judges will try to run the code.** → `D3_p42`
5. **`D3` names the agentic test:** *"would this be possible without agentic AI?"* Where a fixed
   workflow would do, the result is not an agent. → [`TRN_S4.1`](#41-agent-classes-and-project-placement)

---





# 2. `D1` — LLM FOUNDATIONS, AGENTS, PROMPTING, BEDROCK
## 2.1. The Three Paradigms
`D1` separates them by **tool access, orchestration and autonomy — not model capability**,
following Sapkota, Roumeliotis & Karkee, *AI Agents vs. Agentic AI*, arXiv:2505.10468 (2025).

1. **Autonomy** · *Generative AI (LLM):* Low, prompt-driven
   *AI Agent:* Medium, selects and invokes tools
   *Agentic AI:* High, manages the workflow
2. **Flow** · *Generative AI (LLM):* Input → Output
   *AI Agent:* Input → Tool → Output
   *Agentic AI:* Input → Agent → Agent → Output
3. **Decision** · *Generative AI (LLM):* Pattern selection
   *AI Agent:* Tool selection
   *Agentic AI:* Goal decomposition and assignment
4. **State** · *Generative AI (LLM):* None between calls
   *AI Agent:* Episodic, within one run
   *Agentic AI:* Persistent, shared across agents
5. **Failure mode** · *Generative AI (LLM):* Hallucination
   *AI Agent:* Tool misuse, shallow reasoning
   *Agentic AI:* Coordination failure, drift




## 2.2. How an LLM Behaves
Four properties `D1` insists on, each with a direct consequence here:

1. **Token-by-token**
   *`D1`'s statement:* *"No plan is formed in advance, and no stored answer is retrieved"*
   *Consequence:* It cannot "know" a sign it was not given evidence for
2. **Retains nothing**
   *`D1`'s statement:* *"Every call is independent. Continuity exists only because the application
   resends the conversation each time"*
   *Consequence:* All memory is the application's responsibility
3. **Samples**
   *`D1`'s statement:* *"The same input may therefore yield a different answer on a second attempt"*
   — and `temperature=0` *"is not fully deterministic"*
   *Consequence:* → [`RSK_S7.2`](../plan/RSK_risk_register.md#72-loop-and-context) `AGT-11`
4. **Finite shared context**
   *`D1`'s statement:* System prompt, history, retrieved documents and tool outputs share one window
   *Consequence:* → context rot, `D3_p22`




## 2.3. Anatomy of an Agent
Four parts around one model call — **only the model is supplied; the rest is application code**:

1. **Tools**
   Ordinary functions paired with a schema. *"The docstring is not a comment. It is the prompt"*
2. **Memory**
   Short-term = the messages list. Long-term = a store queried each turn and inserted into that list
3. **Planning**
   Reflection, self-critique, chain of thought, subgoal decomposition
4. **Action**
   *"The only step that changes the outside world, and the only step that can fail"*




## 2.4. Three Planning Strategies
Distinguished by *when the order of actions is settled*:

1. **Decomposition**
   *Order settled:* Before execution — one call returns the whole sequence
   *Suited to:* Tasks whose structure is known in advance
2. **Reactive**
   *Order settled:* One step at a time; the observation becomes the next state
   *Suited to:* Uncertain conditions, unknown step count
3. **Hierarchical**
   *Order settled:* Coarse phases fixed for the run; actions inside each phase chosen reactively
   *Suited to:* *"Most production systems, and what the frameworks implement"*

> **Note:** the assembly stage is naturally **hierarchical** — a fixed outer sequence (assemble →
> critique → decide) with reactive tool use inside. `D1` also stresses two bounds in the
> hierarchical pattern: an outer loop over phases and an inner step cap per phase.




## 2.5. Tool Composition
The model produces these shapes; the application runs only what it asks for.

| Shape                                                       | Latency              |
| :---------------------------------------------------------- | :------------------- |
| **Sequential** — each result feeds the next                 | The sum of the steps |
| **Parallel** — one reply asks for several independent calls | The slowest call     |
| **Conditional** — one result decides which tool comes next  | One branch executes  |

Error handling pattern `D1` teaches: a missing tool and a broken call are both **written into the
result string and appended**. Nothing raises. The model reads what went wrong and corrects on the
next step. *"The cap is the safety net."*




## 2.6. Prompt Engineering
1. **Zero shot**
   *When:* The task fits in a sentence and category names mean what they say. *"Correct far more
   often than people expect"*
   *Cost:* Cheapest
2. **Few shot**
   *When:* A borderline case keeps going the wrong way. *"Settles borderline cases that words
   cannot"*
   *Cost:* Input tokens on every call — and in an agent the system prompt is resent at every step
3. **Chain of thought**
   *When:* Complex reasoning
   *Cost:* *"Current models mostly do this already"*
4. **RAG**
   *When:* Answers must reflect current or private material
   *Cost:* *"Retrieve the wrong passages and the answer is confidently wrong. Every passage is
   billed as input"*

> **`D1`'s rule:** *"Reach for a technique only when the simple version has been shown to fail."*

Also flagged: *"One careless example is worse than none. The model follows the examples over the
written rule."*




## 2.7. AWS Bedrock
1. **What it is**
   One managed endpoint in front of many model vendors. No servers, no downloads, no fine-tuning.
   Pay per token
2. **Two APIs**
   `InvokeModel` takes each vendor's own JSON body; `Converse` takes one shape for all
3. **Two easy mistakes**
   `body` is a JSON **string**, not a dict. The response body is a **stream** and can only be read
   once
4. **Access**
   Granted **per model and per region**, off by default. *"Valid credentials do not guarantee a
   working call"*
5. **Workshop region**
   `ap-southeast-1`
6. **Default model**
   `global.anthropic.claude-haiku-4-5-20251001-v1:0` — *"Classification, extraction, anything
   high-volume. Your default tonight."* Stated at **$1 in / $5 out per million tokens**
7. **Escalation**
   Sonnet tier for *"ambiguous images, harder reasoning, when Haiku is measurably wrong"*. Opus tier
   *"rarely, and probably not during a hackathon"*
8. **`global.` prefix**
   Cross-region routing; the regional prefix costs about 10% more. *"Read it, never build it"*
9. **Prompt caching**
   Repeated system prompt billed *"at up to 90% less on cache reads"*; worth it above ~1k tokens

> **Note:** Bedrock is partner-operated and priced separately from Anthropic's first-party API.
> The figures above are what `D1` states for the model it prescribes; the authoritative rates live
> on the AWS Bedrock pricing page. Verify before putting a number on a slide.

**Choosing a model** — three axes, and `D1` insists on measuring rather than assuming:
capability, cost (*"output is the expensive half, and every step resends the whole history as
input"*), and latency (*"multiplied by the number of steps the loop takes"*).

**Cost visibility** — five places, three moments: the pricing page and AWS Budgets *before*;
`usage` on every response *while it runs*; Cost Explorer and CloudWatch *after* (*"two days of lag
is normal"*). *"Every response carries the token counts for that call. Logging them turns cost
into something measured per prompt rather than discovered at the end of the month."*

**Multimodal** — `D1`'s lab `05_multimodal.py` *"sends a photo and a question in the same
message"*. Images, not video. → [`ARC_S7.3`](../plan/ARC_architecture.md#74-p2--rationale-for-building-it-regardless)




## 2.8. Lab Environment
Repository: `https://github.com/thetsuwin66/agentic_ai_hackathon_2026`. Tooling is `git` + `uv`.
Session 1 labs run on a free Groq key (rate-limited, not billed); Bedrock is not used until
Session 2. `uv run 00_check_env.py` and `00_check_bedrock.py` verify the setup and *"report the
first one that failed"*.

---





# 3. `D2` — LANGGRAPH, DEEPAGENTS, AGENTCORE
## 3.1. LangGraph
An orchestration framework for **stateful** agents. Four parts:

1. **State**
   The single source of truth across the graph — a `TypedDict` or Pydantic model holding memory,
   history and intermediate results
2. **Node**
   A function that reads State, does one job, and returns **partial updates**
3. **Edge**
   Normal (unconditional), conditional (a routing function inspects State), and entry/exit
   (`START`/`END`)
4. **Runtime**
   After `builder.compile()`: read state → run node → apply diff → checkpoint → evaluate edge

Two traps `D2` calls out:

- **Nodes return partial updates, not complete State.** *"Returned keys must correspond exactly to
  the field names declared in the schema, as an unmatched key is discarded silently and the update
  is lost."*
- **Heavy payloads belong in State, not in prompts.** *"Heavy payloads such as uploaded files,
  full document parses, and intermediate datasets should be stored in the graph State. Prompts
  should carry only metadata or references, keeping token costs low and context focused."*

> **This second rule is load-bearing here.** Landmark tensors must never reach a prompt.
> → [`ARC_S6.3`](../plan/ARC_architecture.md#63-design-rules-inherited-from-the-training-decks), [`RSK_S7.2`](../plan/RSK_risk_register.md#72-loop-and-context) `AGT-8`

Three ways to run: `invoke` (returns the final State), `ainvoke` (awaited), `stream` (*"yields an
update as each node finishes, so the user can watch progress instead of waiting"*).




## 3.2. Choosing a Framework
`D2`'s comparison, with its own conclusion: *"There is no single 'best' framework."*

1. **LangGraph**
   *Mental model:* Flowchart (nodes and edges)
   *Best for:* Strict step-by-step rules where mistakes cannot be afforded
2. **CrewAI**
   *Mental model:* Roleplay team
   *Best for:* Quick prototypes with specialised personas
3. **OpenAI Agents SDK**
   *Mental model:* Relay race (explicit handoffs)
   *Best for:* Clean agent-to-agent transfers, on OpenAI models
4. **Claude Agent SDK**
   *Mental model:* Coding assistant (files and terminal)
   *Best for:* Autonomous coding, bash, filesystem tasks
5. **Google ADK**
   *Mental model:* Corporate tree
   *Best for:* Hierarchical workflows on Gemini and Vertex AI
6. **Microsoft Agent Framework**
   *Mental model:* Group chat
   *Best for:* Enterprise and .NET




## 3.3. Deep Agents and the Supervisor Pattern
*"Instead of one agent trying to do everything in a single loop, a Deep Agent acts as a Project
Manager that creates a plan and delegates tasks to focused Sub-Agents."*

1. **Dynamic planning — builds a to-do list**
   Specialised, narrow system prompts and specific tools
2. **Context protection** — *"prevents raw tool logs from cluttering main memory"*
   Clean handoffs — heavy lifting in isolated loops, returning short summaries
3. **Orchestration — assigns and tracks**
   MCP server integration

**Context isolation** is named as the point: *"Raw search results and trial-and-error tool logs
stay inside the sub-agent loop — keeping the Supervisor prompt clean."*

> ⚠ `D2` notes DeepAgents requires Claude; on Groq the harness uses `llama-3.3-70b` and fails with
> `tool_use_failed`.




## 3.4. Tools as an MCP Server
Three principles: **decoupled microservice** (tools run in their own process), **dynamic
discovery** (the agent calls `tools/list` on startup), **universal JSON-RPC** (any client can
invoke via `tools/call`).




## 3.5. Bedrock AgentCore
Managed pieces that *"work with any framework and any model, and none of them require the
others"*: **Runtime** (serverless hosting behind HTTPS), Memory, Identity, Gateway, Browser and
Code Interpreter, Observability.

The Runtime integration is one decorator:

```python
app = BedrockAgentCoreApp()

@app.entrypoint
def handler(payload):
    return agent(payload["prompt"])
```

The SDK supplies `POST /invocations` and `GET /ping`, builds the container image, pushes it to ECR
and runs it serverless. *"You do not write a Dockerfile."* One microVM per session.

**Lifecycle:** configure → launch → invoke → status → destroy.

> **Warning — teardown is not complete.** *"`destroy` removes the runtime and its deployment
> resources. Shared infrastructure — S3 buckets, ECR repositories, CloudWatch log groups — can
> survive, depending on the configuration."* → [`RSK_S6`](../plan/RSK_risk_register.md#6-system-and-platform) `SYS-13`

---





# 4. `D3` — FRAMING, CLASSES, PRACTICES, CASE STUDIES
Judging criteria, deliverables, deck and video structure are extracted in full into
[`JCR`](../plan/JCR_judging_criteria.md). This section covers the rest.




## 4.1. Agent Classes and Project Placement
**Digital classes:** Information (answer & advise) · **Extraction** (parse & transform) ·
Transaction (do & automate) · Decision-Support (guide & recommend) · Creative/Generative ·
Orchestration · **Personalized** (adapt & learn) · **Embedded** (live where people work).

**Physical classes:** Perception · Monitoring & Inspection · Navigation · Locomotion & Control ·
Embodied Task · Human-Robot Interaction · Fleet Coordination. The last two are marked **NOT
RECOMMENDED FOR THIS HACKATHON**.

> **The line that places this project.** `D3` states: *"Perception belongs here [on the physical side] when
> the reading feeds a decision that changes physical state. Analysing recorded media for a report
> sits with Extraction Agents on the digital side."*
>
> The perception stage here changes no physical state. **This is a digital-track project**,
> spanning Extraction, Personalized and Embedded. Stating so on the architecture slide demonstrates
> that the taxonomy was read. → [`ARC_S6.2`](../plan/ARC_architecture.md#62-where-agentic-ai-earns-its-place)

**The agentic test** (`D3_p10`): *"Would this problem still exist if agentic AI had never been
invented?"* Yes = a problem statement. No = a product pitch, start again. And separately:
*"justify agentic AI as well — would this be possible without agentic AI?"*




## 4.2. Decisions Made Before Coding
Four decisions `D3` says are made **before** writing code — *"what separates a shipped agent from
a demonstrated one"*:

1. **Context rot is real**
   *"Everything the model can see shares one window. Well before the limit, accuracy and consistency
   degrade while cost and latency rise on every turn of the loop."* Build short, single-purpose
   agents that do one job and exit
2. **Bound every loop**
   *"A refine loop that exits when the critic is satisfied will sometimes never be satisfied, and we
   discover it from the bill."* Keep a hard iteration cap in state that **ignores the model's
   judgement**
3. **Descriptions are the interface**
   *"A vague description produces an unused tool or a badly called one."* Treat tool descriptions as
   the highest-leverage prompt text in the system
4. **Keep payloads small**
   *"Tools that return page dumps fill the window with material the model has to re-read on every
   subsequent turn."* Return small typed results; hold large objects in state




## 4.3. Development Best Practices
1. **Code readability**
   Clean, commented, clear names, consistent formatting. **Organise code to showcase application of
   Agentic AI techniques**
2. **Folder structure**
   *"A good structure might include `src/`, `docs/`, `data/`, and `tests/`"*
3. **Documentation**
   Concise. A good `README.md` suffices
4. **Error handling**
   Baseline: functional resilience. **Going further: make it actionable for business users**
5. **Testing**
   Accuracy testing (*"Are Agentic AI results always Yes/No?"*) and evaluation metrics, with the
   methodology **justified**




## 4.4. The Four Case Studies
1. **Educational Support Hub — ~100 tickets/day**
   *Pattern:* **Multi-agent (A2A)**: a classification agent routes to department agents, each a
   subject-matter expert with its own knowledge and tools
   *Transferable element:* Separating a router from specialists
2. **Intelligent Exam Generation**
   *Pattern:* **Reflection (feedback loop)**: a generator agent proposes, a reviewer agent *"reviews
   against knowledge base, flags inaccuracies"*, then human review
   *Transferable element:* **Directly the assembler↔critic design.** The human-in-the-loop is drawn
   into the architecture, not bolted on
3. **Autonomous Facility Inspection**
   *Pattern:* Navigation + inspection + task agents over a baseline knowledge base
   *Transferable element:* *"A technician confirms or dismisses each flagged finding, and we feed
   that judgement back into the baseline"* — corrections as training signal
4. **Assistive Ageing-in-Place Companion**
   *Pattern:* Perception + navigation + task agents, resident memory
   *Transferable element:* *"The carer confirms or stands down every escalation, and we hold consent
   and privacy limits as a design constraint from day one"*

> **Note:** case studies 3 and 4 are the closest in shape to this product — continuous perception,
> an agent deciding what deserves a human's attention, and a human confirming every escalation.
> Both make **human-in-the-loop and privacy design constraints from day one**, not features. That
> is the framing to copy. → [`RSK_S8`](../plan/RSK_risk_register.md#8-human-ethical-and-legal)




## 4.5. Measuring Performance
**Digital agents** (`D3_p32`): schema validation pass rate · tool-call success rate · task
completion rate · token cost per run · loop discipline · answer fidelity.

**Physical AI** (`D3_p35`): task success rate · **intervention rate** (*"the honest measure of
autonomy"*) · safety record · cycle time · **robustness** (*"re-test under changed lighting,
terrain, clutter and starting position"*).

Full mapping onto this system: [`ARC_S8.4`](../plan/ARC_architecture.md#84-proposed-metric-set).




## 4.6. The Taught Stack
A request travels down; a response returns up. *"No framework is required"* at the interface layer.

| Layer          | Options `D3` names                                               |
| :------------- | :--------------------------------------------------------------- |
| Interface      | A project-supplied front end                                     |
| Deploy & serve | AgentCore Runtime · local first (`POST` to `localhost:8080`)     |
| Orchestrate    | `@app.entrypoint` handler                                        |
| Schema         | `create_react_agent` · LangGraph · deepagents · Claude Agent SDK |
| Access         | `boto3 InvokeModel` · Converse API · `ChatBedrockConverse`       |
| Model          | Claude Haiku 4.5 · Claude Sonnet 4.5                             |

**Cross-cutting** — typed state with reducers where nodes write concurrently; `InjectedState`
reaches large objects without a prompt; `InMemorySaver` plus `thread_id` carries a conversation;
token usage returns on every response; the `@app.entrypoint` handler is the seam a UI calls.

**Guardrails and limits** — verify model access in the deployment region; read model IDs from a
constant, **never build them**; `allowed_tools` is *"an allow-list and a security boundary"*; bound
every loop with a counter held in state.

---





# 5. `D4` AND `D5` — THE PHYSICAL AI TRACK
> **Relevance: low, but not zero.** These are the companion decks for the robotics track; this
> project is digital-track ([`TRN_S4.1`](#41-agent-classes-and-project-placement)). This section covers the framing ideas only.




## 5.1. `D4` — Physical AI Foundations
⚠ `D4` is a **24-page image-only PDF** with no text layer. The summary below is from reading the
rendered slide images, so quotations are not available and paraphrase is unavoidable.

**The four-step AI ladder** — the one genuinely useful frame in this deck:

```text
Perception AI  →  Generative AI  →  Agentic AI  →  Physical AI
understand        create new        take actions    interact with
the world         content           and achieve     the physical
                                    goals           world
```

> **Note:** this system is **Perception AI feeding Agentic AI**, with no physical step. That
> places the project on a slide in one line, using the organiser's own vocabulary.

Other content: traditional AI (images, text, conversation) versus physical AI (understanding
physical laws, controlling robots, manipulating objects, autonomously completing tasks); the
simulation-first argument (safe, massive, scalable, low-cost → simulation → synthetic data →
robot learning → real robot); real world versus simulation trade-offs (high cost, safety risks,
slow iteration, limited data, low reproducibility versus massive data, parallel training, safe,
repeatable, customisable); the ORCA toolchain (Engine → Sim → Replicator → Gym → Real Robot); and
sim-to-real transfer via domain randomisation, physics accuracy, sensor fidelity and validation.




## 5.2. `D5` — ORCA VLN Hackathon Manual
From Songying Technology (`orca3d.cn`). Reproduce visual-language navigation in OrcaLab:
instruction plus 8 ego RGB frames → NaVILA → one navigation action → velocity chunk drives the
robot → the scene returns the next observation. Baseline: Cheng et al., *NaVILA: Legged Robot
Vision-Language-Action Model for Navigation*, RSS 2025.




## 5.3. Three Transferable Ideas from the Physical Track
Applicable despite the track difference:

1. **A stable layer boundary** · *Where:* `D5`
   *Why it transfers:* ORCA fixes the `VelocityCommand` interface so the high-level VLN model and
   the low-level locomotion policy can be improved independently. The equivalent here is the
   landmark-feature contract between perception and the agent — fixed early, both halves can move
   independently
2. **Change one variable at a time** · *Where:* `D5`
   *Why it transfers:* Baseline reproduction, then language ablation, then camera ablation. This is
   a ready-made evaluation structure for
   [`JCR_S5`](../plan/JCR_judging_criteria.md#5-evaluation-and-metrics)
3. **An evidence package** · *Where:* `D5`
   *Why it transfers:* Ego-view images or video, `measurements.json` and logs, a replayable run
   path, reproduced with one command. *"Make the loop visible and reproducible first; then change
   one layer at a time"*

`D5` also warns: *"A review queue is not ground truth: label only after image–action alignment."*
The equivalent here is that a hearing team's guess at a sign is not a label.
→ [`RSK_S4.1`](../plan/RSK_risk_register.md#41-data) `MOD-4`

---





# 6. `D6` — AWS ACCESS AND BUDGET
## 6.1. Account Setup
1. **Who registers**
   **Group representative only** — one person per team signs in and manages the account
2. **Username format**
   `hackathon2026,<registered group leader email>` — **note the comma, and no spaces**
3. **Portal**
   `https://d-9667b91afb.awsapps.com/start`
4. **Verification**
   A code is emailed; enter it and sign in
5. **2FA**
   Mandatory. Register an authenticator app. *"Click on 'Show secret key'"* and share it with group
   members so each can log in independently
6. **Password**
   Shared with group members




## 6.2. Leasing the Sandbox
Applications tab → *Innovation Sandbox Ignite Hackathon Application* → *Request a new lease* →
lease template **Hackathon 2026** → accept terms → submit.

**Approval takes up to 2 working days.** The approval email *"is highly likely to land in your
spam box"*, and may be blocked entirely — so log in periodically to check status rather than
waiting for mail. If login shows an error immediately after approval, wait a few minutes and retry.




## 6.3. The Budget
> **Warning.** `D6` states: even though Max Budget might show **$30**, *"the actual budget is set
> to **$20**. At $20, access to your AWS account will be revoked. At $30, your AWS account would
> be terminated to eliminate run-away costs."*
>
> *"Barring certain exceptions, request for additional leases (past the first one) would not be
> granted. Every group is expected to lease one (and only one maximum) AWS account throughout the
> hackathon."*

This is a **kill switch**, not an invoice. An unbounded agent loop can end the project rather than
produce a surprise bill.

Direct consequences, argued in [`ARC_S8`](../plan/ARC_architecture.md#8-cost-model-against-the-aws-cap):

1. All perception runs **locally**. Nothing at 30 fps touches Bedrock.
2. The agent is invoked **per utterance**, not per frame.
3. Every loop carries a hard iteration cap held in state (`D3_p22`).
4. Token usage is logged from the first commit.
5. One person owns the lease and watches the spend.

---





# 7. CROSS-CUTTING RULES
Every hard rule the six decks state, in one list.

1.  **Python is strongly recommended** · *Source:* `D3_p42`
2.  **Provide `requirements.txt` or a Docker setup** · *Source:* `D3_p42`
3.  **Secrets and keys in `.env` files** · *Source:* `D3_p42`
4.  **Folder structure: `src/`, `docs/`, `data/`, `tests/`** · *Source:* `D3_p23`
5.  **A good `README` covering how to run the code and the purpose of each file** · *Source:*
    `D3_p42`
6.  Testing and evaluation must appear **in the slides** · *Source:* `D3_p42`
7.  **The presentation methodology must be reflected at code level** · *Source:* `D3_p42`
8.  **Bound every loop with a counter held in state** · *Source:* `D3_p22`
9.  **Read model IDs from a constant; never build them** · *Source:* `D3` stack slide
10. **`allowed_tools` is an allow-list and a security boundary** · *Source:* `D3` stack slide
11. **Heavy payloads in State; prompts carry metadata or references** · *Source:* `D2`
12. **Verify model access in the deployment region** · *Source:* `D1`, `D3`
13. **Log token usage on every call** · *Source:* `D1`, `D3_p32`
14. **Stay under US$20 of AWS spend** · *Source:* `D6`
15. 10 slides · 5 minutes · 5 GB · **one submission only** · *Source:* `D3_p37`, `D3_p42`

---





# 8. SOURCES
1.  **`[S1]`**
    `doc/[D1]_Hackathon_Training_Session_1.pdf`
2.  **`[S2]`**
    `doc/[D2]_Hackathon_Training_Session_2.pdf`
3.  **`[S3]`**
    `doc/[D3]_Hackathon_Training_Session_3.pdf`
4.  **`[S4]`**
    `doc/[D4]_Hackathon_Training_Session_1_Extra.pdf` — ⚠ image-only; read from rendered slide
    images
5.  **`[S5]`**
    `doc/[D5]_Hackathon_Training_Session_2_Extra.pdf`
6.  **`[S6]`**
    `doc/[D6]_Hackathon_AWS_Access_Guide.pdf`
7.  **`[S7]`**
    Sapkota, Roumeliotis & Karkee, *AI Agents vs. Agentic AI*, arXiv:2505.10468 (2025) — cited by
    `D1`
8.  **`[S8]`**
    Cheng et al., *NaVILA: Legged Robot Vision-Language-Action Model for Navigation*, RSS 2025 —
    cited by `D5`
9.  **`[S9]`**
    Lilian Weng, *LLM Powered Autonomous Agents* —
    https://lilianweng.github.io/posts/2023-06-23-agent/ — cited by `D1`
10. **`[S10]`**
    Prompt Engineering Guide — https://www.promptingguide.ai/techniques — cited by `D1`
11. **`[S11]`**
    Lab repository — https://github.com/thetsuwin66/agentic_ai_hackathon_2026 — cited by `D1`

> **Note:** all quotations are transcribed from the PDF text layer. `D4` has no text layer, so its
> section is paraphrase from slide images and carries no quotations. Where a slide's meaning
> matters to a decision, **open the original.**

---





# 9. CHANGE LOG
1. **2026-08-28** · *Author:* Claude (Opus 5)
   *Change:* Created. Synthesised all six decks. `D1`, `D2`, `D3`, `D5`, `D6` from extracted text;
   `D4` from rendered slide images (no text layer).
2. **2026-08-28** · *Author:* Claude (Opus 5)
   *Change:* Reformatted to the revised conventions in
   [`RIX_S4`](../ref_index.md#4-markdown-formatting-rules): bold title, collapsible `# METADATA`,
   `#`-level numbered sections, HTML anchors removed, padded tables, third-person voice,
   placeholders for unfinished content.
3. **2026-08-28** · *Author:* Claude (Opus 5)
   *Change:* Applied the revised [`RIX_S4.4`](../#44-vertical-spacing) heading spacing and the
   [`RIX_S4.5`](../#45-tables-and-numbered-lists) table-versus-numbered-list rule: tables whose rows exceeded 100
   characters became numbered lists.
