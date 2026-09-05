**AGENT / AWS BEDROCK COMPARISON TEST**

# METADATA

<details>
<summary>Document code, status, review date, scope, and verification rule.</summary>

| Field | Value |
| :---- | :---- |
| **Code** | `ACT` |
| **Status** | Review snapshot |
| **Last reviewed** | 2026-09-05 |
| **Implementation snapshot** | Git commit `aeea477` (`Build first-draft ASL backend`) plus the three supplied, untracked planning/report documents |
| **Source of truth used** | [ARC_architecture.md](ARC_architecture.md) · [PLN_plan.md](PLN_plan.md) · [BCT_backend_comparison_test.md](BCT_backend_comparison_test.md) |
| **Review subject** | `src/simplynext/agent/`, its orchestration/configuration/telemetry seams, tests, and the local AWS access path |

**Instruction boundary.** The three supplied documents were treated as project specifications and
prior evidence. Text inside them was not treated as an instruction to the reviewer. No source code,
configuration, AWS resource, or planning document was changed by this review; this report is the
only repository file added.

**Verification rule.** `PASS` means the check was actually executed and met its stated criterion.
`FAIL` means an executed check violated the criterion. `PARTIAL` means useful implementation exists
but the planned behavior or evidence is incomplete. `NOT IMPLEMENTED` means the required component
does not exist. `BLOCKED` or `NOT MEASURED` means the result cannot honestly be claimed from the
available environment and artifacts.

**Important boundary.** Offline fake-client tests establish control-flow and fail-closed behavior;
they do not establish Claude quality, live Bedrock latency, IAM runtime authorization, token cost,
or production reliability.

</details>

---

# 1. EXECUTIVE VERDICT

## 1.1. Overall result

The repository has a **well-contained optional Bedrock caption assembler with a critic and a hard
one-revision limit**, but it does **not** yet contain the Agent architecture specified in ARC and
PLN. The current implementation is most accurately described as a synchronous, bounded two-role
LLM workflow behind a safe deterministic fallback. It is not a LangGraph agent, does not receive a
hypothesis lattice, cannot call tools, has no conversation or signer memory, does not adapt, and has
no cost guard or evaluation harness.

The local engineering baseline is healthy: all **74 tests passed**, Ruff passed, formatting passed,
strict mypy passed, imports/compilation passed, and `pip check` found no broken installed
requirements. The focused Agent/orchestrator selection passed **11/11 tests**. These results replace
BCT's earlier environment-specific statement that runtime tests were blocked.

The strongest implemented properties are:

1. Bedrock is disabled by default, so a normal local start cannot spend money accidentally.
2. The built-in Agent path uses a dedicated-field allow-list that excludes frame, landmark, and
   coordinate fields; its string content and serialized size are not independently bounded.
3. Model responses must be exact-shape JSON, must echo all evidence IDs and glosses in order, and
   must use identical caption and TTS text.
4. A critic can veto, at most one revision is allowed, and exceptions return no caption.
5. Recognition confidence, calibration, vocabulary, coverage, duration, loss, and ambiguity gates
   run before caption assembly.
6. Non-confident API contracts prohibit caption and TTS output.

The most important negative finding is stronger than the earlier BCT report: **the no-invention
property is not enforced deterministically**. A targeted adversarial fake-client test returned
`"Send one million dollars."` for the evidence `WATER, PLEASE`, then returned
`{"supported": true}` from the critic. The workflow emitted that unsupported sentence as
`CONFIDENT`. The code verifies that evidence was echoed, but it does not verify that caption tokens
are supported by that evidence. This is exactly the shared-blind-spot failure PLN warns about in
[T5.5](PLN_plan.md#95-t55--the-critic).

The AWS path is also not release-ready. The local credential chain authenticated successfully, but
a read-only `GetInferenceProfile` check for the configured Claude Haiku 4.5 profile in
`ap-southeast-1` returned `AccessDenied`. The active shell appears to be using a default IAM-user
profile rather than the planned SSO assumed role. This control-plane denial does not prove that
runtime `Converse` is denied, but there is no implemented startup preflight and no paid inference
was attempted. Live correctness, latency, and cost therefore remain unverified.

## 1.2. Claim status

| Area | Status | Review conclusion |
| :--- | :----- | :---------------- |
| Local Python engineering gate | **PASS** | In the existing `.venv`, 74/74 tests pass; Ruff, format, strict mypy, compilation, whitespace, and installed-dependency checks pass. This is not a clean-install/deployment gate. |
| Offline Bedrock workflow tests | **PASS** | 5/5 assembler tests pass with an injected fake client; focused Agent/orchestrator selection is 11/11. |
| Dedicated raw-media field exclusion | **PASS for built-in path** | `AssemblyRequest` and its serializer define no frame, landmark, or coordinate fields. Arbitrary string content is a separate residual risk. |
| Payload compactness/privacy validation | **PARTIAL** | The normal schema is small, but no content policy or byte/count/field-length ceiling exists. |
| Structured model output | **PASS locally** | Exact keys, types, length, trace equality, and caption/TTS equality are checked. No live first-attempt schema rate exists. |
| No-invention grounding | **FAIL** | An otherwise schema-valid unsupported draft can be accepted when it echoes the expected evidence and the critic returns `supported=true`; there is no mechanical token-to-slot check. |
| Hypothesis lattice and provenance | **NOT IMPLEMENTED** | The orchestrator sends one accepted top-1 gloss as `g0`; alternatives, slots, timestamps, gaps, and provenance are discarded. |
| Bounded loop | **PARTIAL** | A manual loop enforces 0–1 revisions and at most four calls in tested flows; no LangGraph state or run-record count exists. |
| LangGraph state machine | **NOT IMPLEMENTED** | No `state.py`, `graph.py`, reducers, checkpointer, `thread_id`, or LangGraph dependency exists. |
| Tools and allow-list | **NOT IMPLEMENTED** | The three T5.4 tools and `allowed_tools` boundary do not exist; the broader ARC TTS/escalation integrations are also absent. |
| Critic | **PARTIAL** | Separate prompt and veto route work, but the critic is another call to the same model and its Boolean verdict is trusted. |
| Repair policy / refusal | **PARTIAL, safety invariant PASS** | Low-confidence results emit no sentence and useful fixed actions exist; there is no Agent planner, listener-facing proof, or reliable service-outage action. |
| Per-signer adapter and memory | **NOT IMPLEMENTED** | No Agent correction contract, confirmed-learning rule, conversation memory, Agent-memory retention/deletion policy, or signer isolation exists. Transport-session TTL/deletion is separate. |
| Bedrock control-plane profile check | **FAIL — AccessDenied** | Credentials work, but the checked identity lacks `GetInferenceProfile` permission for the configured profile/region. |
| Bedrock runtime `Converse` authorization | **UNKNOWN** | Control-plane permission does not decide runtime permission; no paid call was made. |
| Application Bedrock readiness | **FAIL** | `ready` always returns true without checking credentials, region, model access, or a real inference. |
| Token/cost/spend control | **NOT IMPLEMENTED beyond per-call log fields** | No aggregation, pricing, cache accounting, ceiling, kill switch, quota, or session run record exists. |
| Live Agent performance | **NOT MEASURED** | No live invocation was made; the ARC 0.5–2 s target cannot be evaluated. |
| Agent quality evaluation | **NOT IMPLEMENTED** | No frozen lattice set, reviewed sentence truth, repeated-run harness, EVL document, or evidence package exists. |

## 1.3. WP5 completion statement

Using the full `Done when` condition for each task, **0 of 8 WP5 tasks are complete**. Five have
useful partial implementation and three are absent; T5.1's small counter concept is represented
internally, but not its required graph-state contract.

Of the six WP5 exit criteria in [PLN](PLN_plan.md#99-wp5-exit-criteria):

- **2 are behaviorally verified:** critic veto under a rejecting fixture; low-confidence repair
  with no sentence.
- **2 are partial:** a loop cap exists but its count is not in a run record; prompts are field-
  minimized but there is no lattice contract or size ceiling.
- **2 are not demonstrated:** uncertainty presented to both parties; per-utterance cost plus an
  exercised spend guard.

## 1.4. Safe release description

The current code can accurately be described as:

> An optional, fake-client-tested Bedrock Converse caption workflow that accepts one confidence-
> gated gloss, validates structured output and evidence echoes, obtains a separate critic verdict,
> allows at most one revision, logs per-call token fields, and fails closed to a repair event. A
> deterministic exact-template assembler remains the default.

It must not yet be described as:

- a LangGraph Agent;
- a lattice-to-sentence Agent;
- a tool-using or context-aware Agent;
- a conversational-memory or signer-adaptive Agent;
- mechanically grounded against hallucination;
- protected by an AWS spend guard;
- live-tested on Bedrock;
- meeting the 0.5–2 s latency target;
- measured for fidelity, schema rate, refusal precision, or cost.

---

# 2. REVIEW METHOD AND VERIFICATION

## 2.1. Controlling requirements

The review traced the implementation primarily against:

1. [PLN T5.1–T5.8](PLN_plan.md#9-wp5--the-agent-stages-) and the WP5 exit criteria.
2. [PLN frozen interfaces](PLN_plan.md#34-the-frozen-interfaces), instrumentation, configuration,
   recognition-lattice prerequisites, and [evaluation harness](PLN_plan.md#122-t82--the-metric-harness).
3. [ARC recommended Agent architecture](ARC_architecture.md#6-the-recommended-architecture), Agent
   justification, design rules, latency budget, cost controls, and proposed metrics.
4. [BCT's prior WP5 findings](BCT_backend_comparison_test.md#46-wp5--agent), rechecked rather than
   assumed current.

The supplied root-level ARC is longer and newer than `plan/ARC_architecture.md`; this review used
the supplied root-level document named by the request.

## 2.2. Implementation reviewed

The complete Python Agent package contains only:

- [agent/assembler.py](src/simplynext/agent/assembler.py) — evidence/result dataclasses, exact
  templates, and the generic repair result;
- [agent/bedrock.py](src/simplynext/agent/bedrock.py) — Bedrock Converse assembler, critic,
  revision loop, response checking, and client construction;
- [agent/__init__.py](src/simplynext/agent/__init__.py) — exports.

Adjacent paths reviewed were:

- [orchestrator.py](src/simplynext/orchestrator.py) for confidence-to-Agent data flow and events;
- [recognition/policy.py](src/simplynext/recognition/policy.py) for repair selection;
- [config.py](src/simplynext/config.py) and [.env.example](.env.example) for model/region/limits;
- [metrics.py](src/simplynext/observability/metrics.py) and logging for evidence;
- HTTP, WebSocket, session, and output contracts for invocation and failure behavior;
- all tests, with detailed attention to `test_assembler.py`, `test_orchestrator.py`, and
  `test_policy.py`.

## 2.3. Checks executed

| Check | Result | What it establishes |
| :---- | :----- | :------------------ |
| `.venv/bin/python -m pytest -q` | **PASS — 74 passed, 2 warnings, 1.09 s** | Current repository tests execute successfully in the populated local environment. |
| Focused assembler + orchestrator tests | **PASS — 11/11, 0.31 s** | Current fake-client Agent flow and orchestration safety cases pass. |
| `.venv/bin/python -m pytest --collect-only -q` | **PASS — 74 collected** | Current test inventory; BCT's count of 70 is stale. |
| `.venv/bin/python -m ruff check src tests main.py` | **PASS** | Configured lint rules pass. |
| `.venv/bin/python -m ruff format --check src tests main.py` | **PASS — 42 files already formatted** | Formatting gate passes. |
| `.venv/bin/python -m mypy src` | **PASS — 31 source files** | Strict configured type check passes. |
| Python compile/import checks | **PASS** | Source/tests compile and boto3, FastAPI, Pydantic, NumPy, and package imports resolve. |
| `.venv/bin/python -m pip check` | **PASS** | No broken requirements in this installed environment. |
| `git diff --check` | **PASS** | No tracked whitespace errors. |
| Standard-library `trace` over committed Agent tests | **assembler.py 86%; bedrock.py 85% approximate line coverage** | Useful line-execution signal only; not branch coverage and not whole-system coverage. |
| boto3/botocore `Stubber` Converse contract smoke | **PASS — 2 requests accepted** | The real generated Bedrock Runtime client accepts the request shape offline; it does not establish IAM or live service behavior. |
| LangGraph module/dependency check | **FAIL / absent** | `langgraph` is neither declared nor installed. |
| AWS credential resolution and STS identity check | **PASS** | A working credential source exists without exposing credentials in this report. |
| AWS `GetInferenceProfile` for configured profile and region | **FAIL — AccessDenied** | Current identity lacks this Bedrock control-plane permission. It does not decide runtime `Converse` permission. |
| Paid Bedrock `Converse` smoke test | **NOT EXECUTED** | Avoided an unguarded paid call after the access/preflight gate failed. |
| Adversarial fake-client probes | **Mixed; material failures found** | Deterministic grounding, payload ceiling, outage action, and log-status weaknesses described in section 5. |
| 10,000-iteration local microbenchmarks | **PASS as local code measurement only** | Python control overhead; excludes the network and model and cannot be compared to live targets. |

The two pytest warnings are dependency-drift signals: Starlette reports that its `httpx` TestClient
path is deprecated in favor of `httpx2`, and an AnyIO alias used by Starlette is deprecated. They do
not fail the current suite, but the broad dependency ranges in
[pyproject.toml](pyproject.toml#L11-L27) allow future clean installs to change behavior.

## 2.4. Review environment and limitations

- Python 3.12.3 on Linux/WSL2, x86-64, 20 logical CPUs.
- Relevant installed versions include boto3/botocore 1.43.89, FastAPI 0.141.1, Starlette 1.6.0,
  HTTPX 0.28.1, Pydantic 2.13.5, pytest 8.4.2, Ruff 0.16.6, and mypy 1.20.2.
- This was not a clean-clone install; it used the repository's existing `.venv`.
- No recognition dataset, calibrated production bundle, frozen GlossLattice fixture set, reviewed
  caption ground truth, or Agent evaluation package exists.
- `coverage.py`/pytest-cov is not installed. A standard-library `trace` run provided approximate
  line coverage of 86% for `assembler.py` and 85% for `bedrock.py` under the committed Agent tests;
  no branch or whole-repository coverage percentage was measured.
- No paid model invocation was made. No live output quality, model schema rate, throttling behavior,
  network latency, token usage, or monetary cost is claimed.
- Control-plane `AccessDenied` may be an identity/profile issue. The active credentials appear to
  be a default IAM-user profile rather than the SSO assumed-role flow expected by PLN.

---

# 3. CURRENT ARCHITECTURE VERSUS THE PLAN

## 3.1. Data-flow comparison

The central mismatch is visible in the data path:

```text
PLANNED
per-slot top-k lattice + confidence + time + provenance
    -> typed LangGraph state / thread
    -> assembler + allow-listed tools
    -> evidence-mechanical critic
    -> confident output OR uncertainty-shaped repair
    -> confirmed-correction adapter / run record

CURRENT
one accepted top-1 gloss ("g0")
    -> synchronous assembler Converse call
    -> schema/echo checks
    -> synchronous critic Converse call
    -> optional single revision and second critic
    -> caption OR generic repair
```

Both frame and replay seams construct exactly one evidence item from
`decision.accepted` ([orchestrator.py](src/simplynext/orchestrator.py#L215) and
[orchestrator.py](src/simplynext/orchestrator.py#L355)). The Agent therefore never sees the top-k
candidate set that the recognizer produced. It also never receives per-slot timestamps, a missing
slot, classifier/template provenance, signer confirmation, or prior conversation.

This is not a small payload-shape omission. With one gloss for the whole recognized window, the
current LLM has little legitimate assembly work to do and cannot implement the planned hypothesis-
lattice-to-sentence reasoning.

## 3.2. What is working

### Default and boundary safety

- `SIMPLYNEXT_BEDROCK_ENABLED` defaults to false in
  [config.py](src/simplynext/config.py#L61) and [.env.example](.env.example#L24).
- The default non-Bedrock path emits only explicitly configured exact templates and refuses unknown
  sequences ([assembler.py](src/simplynext/agent/assembler.py#L113)).
- `AssemblyRequest` has no dedicated frame or landmark properties; the built-in prompt builder uses
  an explicit field allow-list ([bedrock.py](src/simplynext/agent/bedrock.py#L294)). This does not
  prevent arbitrary or oversized string content inside allowed fields.
- The configured model ID is a literal Claude Haiku 4.5 inference-profile ID, and region is explicit
  ([config.py](src/simplynext/config.py#L18)).
- boto3 uses the standard AWS credential provider chain; credentials are not application settings.

### Model-output containment

- Assembler output must be a JSON object with exactly four keys.
- Caption/TTS types, caption length, caption/TTS equality, evidence IDs, gloss strings, and order are
  checked ([bedrock.py](src/simplynext/agent/bedrock.py#L320)).
- Critic output must be exact-shape JSON with a Boolean `supported` value
  ([bedrock.py](src/simplynext/agent/bedrock.py#L365)).
- Response envelopes with missing or multiple text blocks are rejected.
- Invalid output is revised at most once; failures return a repair with `caption=None`.

### Loop and refusal behavior

- Configuration restricts revisions to zero or one
  ([bedrock.py](src/simplynext/agent/bedrock.py#L53)).
- The revision count is held in a local state object and checked before revision.
- Tested call counts are bounded at two, three, or four depending on outcome.
- Recognition policy blocks unready, uncalibrated, low-coverage, short/long, lossy, low-confidence,
  ambiguous, rejected-class, and out-of-vocabulary evidence before Agent invocation
  ([policy.py](src/simplynext/recognition/policy.py#L108)).
- API result contracts prevent captions/TTS on non-confident output
  ([utterances.py](src/simplynext/contracts/utterances.py#L75)).

### Testability

- The Converse client is a small injectable protocol, allowing deterministic offline tests.
- Existing tests prove exact-template refusal, happy-path structured assembly, one-revision limit,
  critic veto, model-output failure refusal, pre-Agent confidence rejection, and assembler exception
  fail-closed behavior.

## 3.3. What is not working or not present

1. **No actual graph.** The while loop is useful bounded orchestration, but there is no LangGraph,
   node graph, reducer, checkpointer, `thread_id`, or resumable state.
2. **No lattice.** Only top-1 is passed. The Agent cannot reason over ambiguous slots or preserve a
   gap.
3. **No mechanical grounding.** Evidence echoes can coexist with an unrelated caption. The same
   model family produces the draft and judges it.
4. **No tools.** PLN T5.4's lexicon, memory, and context tools are absent, along with the security
   allow-list. ARC's broader TTS and interpreter-escalation integrations are also absent.
5. **No conversation.** Every request is stateless; prior turns cannot disambiguate meaning.
6. **No adaptation.** There is no confirmed correction or per-signer memory path.
7. **No trustworthy readiness.** `BedrockCaptionAssembler.ready` always returns true
   ([bedrock.py](src/simplynext/agent/bedrock.py#L110)); `/readyz` trusts that property
   ([routes.py](src/simplynext/api/routes.py#L53)).
8. **No deadline/reliability policy.** The boto3 client is created without explicit connect/read
   timeouts or retry mode ([bedrock.py](src/simplynext/agent/bedrock.py#L283)).
9. **No spend safety.** Token fields are logged per call, but there is no accumulation, price,
   ceiling, cache accounting, or call kill switch.
10. **No Agent evidence package.** Calls cannot be reconstructed by utterance/session from the
    current logs, and no run record is persisted.
11. **No live validation.** AWS control-plane permission failed and runtime inference was not run.
12. **No measured quality.** There is no repeated-run or ground-truth Agent evaluation.

---

# 4. WP5 EXECUTION-PLAN TRACEABILITY

## 4.1. T5.1 — Typed graph state

**Status: NOT IMPLEMENTED.**

`_AssemblyState` contains only `revision_count` and `model_call_count`
([bedrock.py](src/simplynext/agent/bedrock.py#L83)). It is per-call mutable bookkeeping, not the
planned public graph state. Missing items are:

- `agent/state.py`;
- `GlossLattice` in state;
- conversation history;
- per-signer memory;
- loop/reducer annotations for graph writes;
- JSON round-trip and state migration tests;
- persisted or checkpointed thread state.

The narrow local counter is a good implementation fragment, but it does not satisfy T5.1's state
contract.

## 4.2. T5.2 — The graph

**Status: PARTIAL.**

The manual `while True` workflow implements assemble -> validate -> critic -> optional revise and
enforces a revision limit independently of model opinion
([bedrock.py](src/simplynext/agent/bedrock.py#L116)). A forced-disagreement fixture exits cleanly
after four calls and returns repair.

Missing items are:

- LangGraph dependency and graph wiring;
- short named nodes for stages 6–10;
- `InMemorySaver` or another checkpointer;
- `thread_id` conversation continuity;
- `allowed_tools` allow-list;
- adapter route after confident/repair outcomes;
- loop count in a session run record;
- graph-level tests for resumption, isolation, and concurrent state writes.

The current maximum is **one revision**, selected by implementation. PLN requires a numeric hard
cap but does not specify its value, so the report cannot claim that one is the ratified product cap.

## 4.3. T5.3 — The assembler

**Status: PARTIAL with a critical failed acceptance property.**

Implemented:

- compact typed `AssemblyRequest` and `GlossEvidence` dataclasses;
- ordered gloss evidence and confidence;
- exact structured-response validation;
- caption length limit;
- evidence ID/gloss equality checks;
- deterministic exact-template fallback;
- prompt wording that forbids invention.

Missing or failing:

- complete per-slot top-k lattice input;
- timestamps, slot identity, gaps, confidence alternatives, and provenance;
- a representable explicit missing slot;
- deterministic sentence-to-evidence alignment;
- a separate versioned prompt file and prompt version in results;
- the plan's explicit prompt rules that a gloss is not a word and that unfinished utterances/gaps
  must not be completed from plausibility;
- a measured first-attempt schema-validation rate;
- a live missing-slot test.

An empty gloss is rejected, while omitting an intermediate evidence ID is accepted without any slot
or gap metadata. Therefore the required “mark the gap rather than bridge it” test is structurally
impossible with the current contract.

## 4.4. T5.4 — The tools

**Status: NOT IMPLEMENTED.**

There is no `agent/tools/` package and no implementation of T5.4's required:

- `sgsl_lexicon_lookup()`;
- `conversation_memory()`;
- `context_hint()`;
- word-plus-sense lexicon keys;
- small typed tool results;
- tool-call success telemetry;
- retrieved-data prompt-injection handling;
- `allowed_tools` security boundary.

Separately, ARC's broader Agent architecture calls for TTS and escalation actions. The current
system returns a `tts_text` string and an escalation enum/message, but implements neither a TTS
service/tool nor a human-interpreter handoff.

The SgSL lexicon tool is legitimately blocked by the unresolved ASL-versus-SgSL decision, but PLN
states that the graph, critic, loop, repair planner, and non-language-specific tools can proceed
without it. The repository currently defaults recognition to ASL while the planned tool name remains
SgSL-specific.

## 4.5. T5.5 — The critic

**Status: PARTIAL with a failed mechanical-grounding check.**

The critic has a separate single-purpose system prompt and can veto. Existing tests prove that when
the fake critic returns false twice, no caption is emitted.

However, the acceptance decision is:

```text
if critique.supported:
    accept the draft
```

There is no independent token-to-lattice validator. `_parse_and_check_draft` proves only output
shape and evidence echoes, and `_parse_critique` proves only the type of a model-supplied Boolean.
The adversarial false-positive test therefore succeeds in emitting unsupported content. This is the
precise failure T5.5 says a second opinion from the same model may not catch.

## 4.6. T5.6 — The repair path

**Status: PARTIAL; core no-sentence invariant PASS.**

The deterministic recognition policy already chooses among repeat, fingerspell, top-k choice,
reposition, reconnect, and model-unavailable actions according to fixed uncertainty conditions. Low-
confidence and ambiguous tests pass, and non-confident results contain no caption or TTS.

What remains missing:

- an Agent repair-planning node;
- the exact planned four-action decision table;
- a real human-interpreter escalation integration;
- evidence that both signer and hearing listener see/hear uncertainty;
- repair phrases proven answerable inside the chosen sign vocabulary;
- evaluation of whether each selected repair is appropriate;
- escalation after repeated unresolved attempts.

There is also a concrete wrong-action defect: Bedrock exceptions return reason
`language_service_unavailable` but use the generic repair default `repeat`
([bedrock.py](src/simplynext/agent/bedrock.py#L183) and
[assembler.py](src/simplynext/agent/assembler.py#L163)). Repeating a sign cannot repair an AWS
outage. The runtime should use a service fallback or explicit escalation, not blame the input.

## 4.7. T5.7 — The adapter

**Status: NOT IMPLEMENTED.**

Missing items are:

- correction/confirmation input contract;
- per-signer episodic state;
- preferred variants and personal signs;
- confirmed-only learning rule;
- within-conversation adaptation;
- optional cross-session persistence;
- retention and deletion behavior;
- signer/thread isolation tests;
- correction entry in a run record.

The ephemeral session store is transport state, not conversation or personalization memory.

## 4.8. T5.8 — Bedrock access and cost guard

**Status: PARTIAL implementation; checked access gate FAIL.**

Implemented:

- boto3 Bedrock Runtime client construction;
- literal default Claude Haiku 4.5 profile ID;
- configured `ap-southeast-1` region;
- standard credential chain;
- Bedrock disabled by default;
- invocation only after an utterance passes recognition policy;
- `maxTokens=300`, `temperature=0`, caption-character limit, and one-revision cap;
- logging of input/output/total token fields for every attempted model call.

Missing or failing:

- startup inference preflight and actionable readiness failure;
- verified model access in the configured profile/region;
- SSO lease/profile workflow;
- prompt caching;
- upper bounds on the programmatic `max_tokens` and evidence/count inputs (the application builder
  happens to use safer defaults, but the reusable configuration accepts arbitrarily large values);
- per-utterance and per-session token aggregation;
- verified current Bedrock price and monetary cost calculation;
- configured spend ceiling below the hard account cap;
- an exercised kill switch;
- per-session/user invocation quota and rate limiting;
- explicit timeouts/retry mode/circuit breaker;
- JSON run records and teardown/spend-owner evidence.

The control-plane `AccessDenied` is a current environment result, not proof that the configured
profile ID is invalid. Runtime permission must be tested only after the intended SSO role is active
and the preflight/cost guard exists.

## 4.9. Required prerequisites outside WP5

| Prerequisite | Status | Agent consequence |
| :----------- | :----- | :---------------- |
| T0.2 reproducible pinned dependencies | **NOT IMPLEMENTED** | Version ranges permit test/runtime drift; `langgraph` is missing. |
| T0.3 centralized config and preflight | **PARTIAL** | Model/region/revision settings exist; deadlines, spend, all thresholds, and real access check do not. |
| T0.4 instrumentation/run record | **PARTIAL** | Generic counters and per-call token log text exist; required correlated session evidence does not. |
| T0.5 `GlossLattice` frozen interface | **NOT IMPLEMENTED** | The Agent cannot receive slots, top-k alternatives, gaps, time, or provenance. |
| T4.3 calibrated recognition evidence | **NOT DEMONSTRATED** | Code requires calibration metadata, but no fitted/validated production evidence exists. |
| T4.4 lattice with provenance | **NOT IMPLEMENTED** | Top-k recognition output is collapsed to top-1 before the Agent. |
| T8.1/T8.2 evaluation protocol and command | **NOT IMPLEMENTED** | No reproducible Agent quality/performance table can be generated. |

---

# 5. BEHAVIORAL AND ADVERSARIAL EVALUATION

## 5.1. Existing automated Agent coverage

`tests/test_assembler.py` contains five tests. They cover:

1. exact-template allow-list behavior;
2. happy-path Bedrock structured output and usage log count;
3. one-revision maximum;
4. critic rejection after the only revision;
5. malformed model output returning repair rather than text.

Six orchestrator tests add calibrated acceptance, uncalibrated refusal, normalization failure,
recognizer failure, assembler failure, and transport-loss behavior. Eleven policy tests exercise
repair selection. This is a useful safety baseline.

There are no tests for graph state, tools, memory, prompt injection, prompt versions, lattice gaps,
payload byte ceilings, application deadlines, retries/throttling, cost ceilings, cache use, run
records, AWS IAM/model access, live schemas, repeated nondeterminism, or Agent answer fidelity.

## 5.2. Targeted probe results

| Probe | Executed result | Verdict |
| :---- | :-------------- | :------ |
| Valid draft + supporting critic | Confident after 2 fake model calls, 0 revisions. | **PASS** for control flow. |
| Invalid draft, then valid revision + supporting critic | Confident after 3 calls, 1 revision. | **PASS** for bounded schema repair. |
| Valid draft, critic rejects, revision, critic rejects again | Repair after 4 calls, 1 revision, no caption. | **PASS** for hard local bound. |
| Invalid JSON twice | Repair after 2 calls, 1 revision, no caption. | **PASS** for fail-closed parsing. |
| Client raises `TimeoutError` | Repair, no caption, reason `language_service_unavailable`. | **PASS** for no text; **FAIL** because action is `repeat`. |
| Unsupported caption + critic false-positive | `WATER, PLEASE` produced `"Send one million dollars."` with confident status. | **FAIL — critical grounding hole.** |
| Missing middle slot | Empty gloss is rejected; skipped evidence IDs are accepted with no slot/gap semantics. | **FAIL — required gap behavior unrepresentable.** |
| Oversized Agent request | One 1,000,000-character gloss serialized to **1,000,110 bytes** and was accepted by the contract. | **FAIL — no compact-boundary ceiling.** |
| Prompt privacy | Existing fake-client serialization contains no `landmark` or `coordinates`; request type exposes neither. | **PASS** for field boundary. |
| Malformed nonempty Bedrock envelope | Usage log says `status=ok`, then assembly returns service unavailable. | **FAIL** for operational log accuracy. |
| Caller timeout/cancellation | A 20 ms `wait_for` timed out, but the worker continued, made the critic call, and later incremented `utterances_confident`. | **FAIL** for cancellation and cost containment. |
| Untrusted protocol implementation | A custom assembler returned an invented caption, mismatched TTS, unsupported trace, and a repair flag; orchestration still emitted the confident text. | **FAIL** for defense-in-depth at the `CaptionAssembler` boundary. |
| Invalid confidence from custom assembler | Outbound Pydantic validation raised after the assembler exception boundary. | **FAIL** for contained failure at the protocol seam. |
| Duplicate JSON object keys | Python's default JSON parser silently kept the last duplicate value. | **PARTIAL** — strict field set does not detect duplicate-key ambiguity. |
| Bedrock profile control-plane lookup | `AccessDenied`. | **FAIL** for that permission; runtime remains unknown. |

## 5.3. Interpretation of the grounding failure

The false-positive critic probe does not claim that Claude will always approve the specific bad
sentence. It demonstrates something more fundamental: **there is no code-level safety barrier if
the critic is wrong**. Both `used_evidence_ids` and `used_glosses` can be copied correctly beside an
unrelated caption, and a Boolean critic response completes acceptance.

To meet the plan, the structured result needs a deterministic evidence mapping, for example caption
spans/tokens each carrying supporting lattice slot IDs and an allowed transformation type. The
validator must reject unsupported semantic content independently of the critic. The exact-template
assembler is currently the only path with a true content allow-list.

## 5.4. Conditional cost-abuse path

The classified-hypothesis replay endpoint is disabled by default, which is good. If enabled, it is
not restricted to non-production environments ([main.py](src/simplynext/main.py#L77)). The replay
path trusts client-supplied `features["calibrated"]` and constructs the vocabulary from those same
client hypotheses ([orchestrator.py](src/simplynext/orchestrator.py#L291)). Session creation itself
does not authenticate a user. With Bedrock enabled and replay accidentally exposed, a caller can
obtain a session token, label arbitrary hypotheses calibrated, and cause paid Agent calls. Body-size
limits reduce individual request size but do not provide a call rate or spend ceiling.

This is not an active default exploit; it is a deployment/configuration hazard that must be closed
before any network exposure.

## 5.5. Defense-in-depth and cancellation findings

`AssemblyResult` is a plain dataclass with no cross-field validation
([assembler.py](src/simplynext/agent/assembler.py#L85)). The two built-in assemblers construct it
carefully, but the public `CaptionAssembler` protocol permits an implementation to return confident
text with a repair flag, mismatched TTS, or unrelated trace. The orchestrator discards the repair
flag/reasons on the confident branch and builds the outward result. An invalid confidence can raise
an uncaught validation error because outward event construction occurs after the assembler's
exception handler. The protocol result should enforce the same no-guessing invariants as the public
Pydantic response, and orchestration should validate any implementation before branching.

Cancellation is also not propagated into the worker used by `asyncio.to_thread`. In a controlled
probe, the caller timed out after 20 ms while a fake model call was running; the background worker
continued through the critic, completed two calls, and incremented the success counter. A client
disconnect or request deadline can therefore fail to stop paid work. The fix needs cooperative
cancellation/deadline checks before every call and budget reservation that remains correct even when
the caller disappears.

The revision request feeds the raw previous model output and critic reason back into the next model
prompt ([bedrock.py](src/simplynext/agent/bedrock.py#L192)). That is currently contained by the lack
of tools, but it should be explicitly delimited and treated as untrusted data before tools are added.

---

# 6. PERFORMANCE, COST, AND RELIABILITY

## 6.1. Planned performance target

ARC assigns stages 6–7 an **Agent round-trip target of 0.5–2 seconds**, with perceived end-to-end lag
of about 1–2 seconds, and requires invocation once per utterance rather than per frame
([ARC latency budget](ARC_architecture.md#64-latency-budget)). The code satisfies the once-per-
accepted-utterance placement, but no live measurement exists for the time target.

## 6.2. Measured local control overhead

The following microbenchmark ran on Python 3.12.3 under WSL2. It used a two-gloss request, 100 warmup
iterations, and 10,000 timed iterations per path.

| Path | Calls represented | Mean | p50 | p95 | p99 | Max |
| :--- | :---------------- | ---: | --: | --: | --: | --: |
| Exact-template assembler | No network/model | 0.0048 ms | 0.0040 ms | 0.0073 ms | 0.0125 ms | 0.1117 ms |
| Bedrock workflow with immediate fake client | 2 fake calls | 0.0597 ms | 0.0440 ms | 0.0931 ms | 0.1811 ms | 12.6771 ms |

The evidence-only JSON for that two-gloss request was 167 bytes. These figures show that Python
validation/control overhead is negligible compared with a network model call. They do **not**
measure Bedrock and must not be used on a performance slide as Agent latency.

A separate latency-injection probe reinforced that the workflow is serial and call-dominated:
100 happy paths with 5 ms delay in each of two fake calls measured p50 10.839 ms and p95 11.252 ms;
50 four-call revision paths measured p50 21.680 ms and p95 22.413 ms. These are controlled timing
checks, not estimates of real model speed.

## 6.3. Live performance verdict

| Metric | Current value | Target | Verdict |
| :----- | :------------ | :----- | :------ |
| Initial assembly latency p50/p95 | Not measured | Not separately specified | **UNKNOWN** |
| Critic latency p50/p95 | Not measured | Not separately specified | **UNKNOWN** |
| Total stages 6–7 latency | Not measured | 0.5–2 s | **NOT EVALUABLE** |
| Revision-path latency | Not measured | Must remain within usable interaction budget | **UNKNOWN** |
| End-to-end perceived lag | Not measured | About 1–2 s | **NOT EVALUABLE** |
| First-attempt schema rate | Not measured live | Target absent from plan | **UNKNOWN** |
| Throttle/retry success | Not measured | Target absent | **UNKNOWN** |
| Calls per successful utterance | 2 in local workflow | Once per utterance does not mean one model call | **KNOWN structurally** |
| Worst tested logical calls | 4 | Hard cap required; numeric target unspecified | **BOUNDED locally** |

## 6.4. Deadline and throughput risk

Runtime introspection of the boto3 client created by the application showed SDK defaults of:

- connect timeout: 60 seconds;
- read timeout: 60 seconds;
- retry mode: `legacy`;
- HTTP connection pool: 10.

No application-level utterance deadline, per-call deadline, concurrency semaphore, circuit breaker,
or backpressure exists. The normal path makes two serial calls. A critic disagreement makes four.
SDK retry behavior can multiply delay, so this design cannot currently guarantee a 0.5–2 s total
round trip or even a bounded user-facing wait at the application level.

The synchronous Converse workflow runs inside the orchestrator's worker-thread call. The WebSocket
awaits that utterance result. Under concurrent sessions, paid calls can therefore occupy the
process's default thread pool without a project-owned concurrency or spend bound.

Canceling the awaiting coroutine does not cancel the worker or the underlying SDK request. The
executed timeout probe showed the workflow proceeding to its second paid-call position after the
caller had already timed out. Application timeouts alone are therefore insufficient unless each
node also checks a shared deadline/cancellation state.

## 6.5. Cost verdict

The code logs `inputTokens`, `outputTokens`, and `totalTokens` when the SDK returns them
([bedrock.py](src/simplynext/agent/bedrock.py#L265)). This is a useful first fragment, but it is not
the planned cost control.

Missing cost evidence and controls are:

- prompt/cache-read/cache-write token categories;
- totals per utterance and session;
- model and price version used for calculation;
- monetary cost per run;
- current authoritative Bedrock price verification;
- per-session/global spend accumulator;
- configured guard ceiling below the account threshold;
- atomic reservation before a call, so concurrent calls cannot overshoot;
- idempotency/deduplication so replaying the same utterance does not automatically incur another
  two to four calls;
- explicit stopped-by-budget outcome;
- lowered-ceiling test;
- daily/lease owner record.

The planning document's price and `$1–3` project estimate remain planning assumptions, not measured
performance. This report intentionally does not repeat them as current AWS pricing.

---

# 7. METRIC-BY-METRIC EVALUATION

## 7.1. ARC/PLN Agent metrics

| Metric | Required procedure | Evidence available now | Status |
| :----- | :----------------- | :--------------------- | :----- |
| Answer fidelity | Compare captions with reviewed ground truth; separate Agent-only frozen lattices from end-to-end input. | No corpus, reviewed truth, or live output. | **NOT MEASURED** |
| Task completion | Fraction resolved without repair. | Counters exist in process, but no representative evaluation set/run record. | **NOT MEASURED** |
| Intervention rate | Count repeats/escalations over total attempts. | Repair counter is aggregate only; action distribution is not recorded. | **NOT MEASURED** |
| Refusal precision | Review whether every refusal was justified. | Policy fixtures exist; no labeled refusal set. | **NOT MEASURED** |
| First-attempt schema pass | First response parses and validates / all first responses. | Parser tests exist; no metric or live sample. | **NOT MEASURED** |
| Loop discipline | Distribution of revisions/calls versus cap. | Local probes show 0–1 revisions and 2–4 calls; result is not logged per utterance. | **PARTIAL local evidence** |
| Tool-call success | Successful typed tool calls / attempted tool calls, by tool. | No tools. | **NOT IMPLEMENTED** |
| Token cost per run | Sum usage by utterance, apply verified model pricing. | Per-call log fields only; no correlation or price. | **NOT MEASURED** |
| Robustness | Repeat frozen and end-to-end cases across stated conditions. | No Agent harness or repeated runs. | **NOT MEASURED** |
| Per-token provenance | Distribution across classifier/top-k-confirmed/fingerspelled/unresolved rungs. | Outbound trace is only gloss strings; provenance is discarded. | **NOT IMPLEMENTED** |
| Nondeterminism | Repeat identical frozen inputs and report distributions. | All Agent tests are deterministic fakes; temperature zero does not replace measurement. | **NOT MEASURED** |
| Metric hygiene | Reproducible command, conditions, versions, artifacts; SacreBLEU signature if used. | No `evaluate/` package or EVL artifact. | **NOT IMPLEMENTED** |

## 7.2. Minimum valid Agent evaluation design

A future evaluation must isolate Agent behavior from recognition behavior with two layers:

1. **Frozen-lattice Agent evaluation.** Hand-reviewed lattices covering confident single slots,
   multi-slot utterances, ambiguity, explicit gaps, conflicting context, unsupported completions,
   each repair shape, tool errors, and confirmed corrections. Repeat each live case enough times to
   report a distribution; PLN does not yet specify the repeat count.
2. **End-to-end evaluation.** Real held-out-signer utterances through recognition, lattice, Agent,
   and UI, retaining upstream error attribution rather than blaming every error on the Agent.

For every live run, record at minimum:

- fixture/utterance ID and reviewed expected outcome;
- model ID, region, prompt version, inference settings, and timestamp;
- thread and signer pseudonymous IDs;
- exact compact lattice hash/size, not camera or landmark payloads;
- node/tool route, critic verdicts, revision count, and repair action;
- per-call and total latency (p50/p95/p99 across runs);
- input/output/cache tokens and verified monetary cost;
- schema errors, retries, throttles, timeouts, guard blocks, and AWS request IDs;
- final caption with per-span evidence mapping, or explicit repair with no caption.

The repository should provide one command that regenerates the table and retains a replayable,
privacy-safe evidence package, as required by PLN T8.2.

## 7.3. Specification gaps that must be decided before acceptance

The plan correctly requires several controls but does not assign their numeric/product values:

- revision/iteration cap (the code currently chooses one revision);
- maximum serialized lattice bytes, slot count, alternatives per slot, and string lengths;
- Agent call timeout, total utterance deadline, retry policy, and concurrency cap;
- project spend-guard ceiling below the AWS account limit;
- repeated-run count for nondeterministic evaluation;
- pass thresholds for fidelity, schema rate, task completion, refusal precision, and tool success;
- repair-action decision table and repeated-failure escalation rule;
- prompt-cache hit-rate target;
- measured criterion for escalating from Haiku to a larger model;
- ASL versus SgSL and therefore the actual lexicon tool;
- what function words/paraphrases are allowed by mechanical evidence grounding.

These should be recorded as product decisions, not silently selected inside implementation.

There is also a document-control inconsistency: ARC's metadata summary says all 24 decisions are
proposed, while many individual rows in [ARC section 9](ARC_architecture.md#9-decisions) are marked
agreed; PLN's metadata summary similarly describes a proposed-decision count that no longer matches
the individual rows. This report used the latest status written on each decision row and treated
unanswered language/data questions as unresolved. The summaries should be reconciled before they
are used as a release gate.

---

# 8. SAFETY, SECURITY, AND OPERABILITY

## 8.1. Strong alignments

1. **Fail closed.** Parsing, response-envelope, critic, and client exceptions produce no model text.
2. **Pre-Agent confidence gate.** Uncalibrated or weak recognition cannot reach caption assembly.
3. **Dedicated raw-media fields excluded.** Built-in prompt serialization has no frame, landmark,
   or coordinate fields; allowed strings still require content/size controls.
4. **Exact-template safe mode.** The default deterministic path is genuinely allow-listed.
5. **Bedrock opt-in.** Local default is non-spending.
6. **Credential hygiene.** AWS secrets are not stored as settings or logged.
7. **Hard local revision bound.** The model cannot choose to continue indefinitely.
8. **Strict model-output shape.** Unexpected fields and malformed types are rejected.
9. **Payload-free application logging intent.** Prompts and evidence values are not logged.
10. **Typed outward refusal.** API consumers can distinguish a repair from a caption.

## 8.2. Prioritized risks

| Severity | Risk | Evidence / consequence |
| :------- | :--- | :--------------------- |
| **P0** | Unsupported content can be accepted | Caption content is not mechanically tied to evidence; adversarial false-positive critic emitted a confident invented sentence. |
| **P0** | Required lattice is absent | Top-k, gaps, time, and provenance disappear before the Agent, preventing the planned task itself. |
| **P0 before live use** | No spend kill switch | Two to four calls per accepted utterance, unauthenticated session creation, no rate/quota/cost ceiling. |
| **P0 operational** | Readiness can be false-positive | `ready=True` without access check; current Bedrock control-plane lookup is denied. |
| **P1** | No application deadline | 60 s SDK connect/read defaults, serial calls, legacy retries, no total cap; live UX target cannot be guaranteed. |
| **P1** | Caller cancellation does not stop paid work | Timed-out probe continued into the critic call and recorded success in the background. |
| **P1** | Service outage tells signer to repeat | Misattributes infrastructure failure to signing and cannot repair the fault. |
| **P1** | Conditional replay/cost injection | If replay is enabled, caller-declared calibration and self-declared vocabulary can reach paid assembly. |
| **P1** | Prompt/data size is unbounded internally | A 1,000,110-byte evidence payload was accepted; no count/length/serialized byte guard. |
| **P1 when tools arrive** | No tool security boundary | `allowed_tools`, typed result ceilings, and retrieved-data-as-data rules are absent. |
| **P2** | Logs cannot reconstruct runs | No session/utterance/model/prompt/request ID correlation, latency, cache, revision, or price data. |
| **P2** | Log `status=ok` is inaccurate | Any non-`None` response logs ok even if its envelope cannot be parsed. |
| **P2** | Dependency drift | Broad ranges already emit TestClient deprecations; clean-clone reproducibility is not proven. |
| **P2** | Output trace loses audit facts | Outbound event drops evidence source, revision count, Agent model, and per-token provenance. |
| **P2** | Protocol result lacks invariants | A custom assembler can bypass built-in assumptions or trigger validation outside the caught exception boundary. |
| **P2** | Exception details may leak | Normal usage logs omit prompts, but SDK/client exception messages and stack traces are emitted verbatim. |

## 8.3. Required security tests once tools/memory exist

- deny a non-allow-listed tool even when the model requests it;
- reject invalid, oversized, and cross-tenant tool arguments/results;
- treat lexicon and memory content containing instruction-like text as quoted data;
- isolate history and corrections across `thread_id`, session, and signer;
- learn only after an explicit confirmed-correction event;
- delete requested signer memory and verify it cannot be retrieved;
- reserve spend atomically before parallel calls and stop at the lowered ceiling;
- prove that timeout, cancellation, disconnect, and duplicate/idempotent requests cannot continue
  or multiply paid work;
- rate-limit session creation and Agent invocations;
- disable the replay endpoint automatically in production;
- redact prompts, evidence, credentials, and signer identifiers from logs and exceptions.

---

# 9. PRIORITIZED GAP CLOSURE

## 9.1. P0 — Freeze the real Agent contract

1. Define `GlossLattice` with ordered slots, per-slot top-k alternatives, calibrated confidence,
   timestamps, explicit gap state, and the four-state provenance ladder.
2. Set hard limits for bytes, slots, alternatives, and field lengths; add JSON round-trip and
   serialized-size tests.
3. Pass the complete lattice from recognition instead of one accepted `g0` gloss.
4. Preserve provenance through the outward result as structured per-token/per-span trace data.

Until this is complete, adding more prompt logic builds on the wrong boundary.

## 9.2. P0 — Establish deterministic grounding

1. Move assembler, critic, and revision prompts into versioned files.
2. Define allowed linguistic transformations from glosses to caption text.
3. Require every output span to cite supporting lattice slots and its transformation type.
4. Reject gaps bridged without confirmed evidence and reject unsupported spans in code.
5. Keep the critic as a veto signal, not the sole proof of support.
6. Add the hand-written unsupported-sentence and missing-slot acceptance tests required by PLN.

Retain the exact-template path as the safest fallback until the grounded schema passes adversarial
and live repeated-run evaluation.

## 9.3. P0 — Put cost and availability controls before live inference

1. Activate the intended SSO lease/profile and correct least-privilege Bedrock permissions.
2. Implement a startup/runtime preflight that makes `/readyz` false with an actionable reason when
   credentials, region, model access, or quota are wrong.
3. Add explicit connect/read/total deadlines, bounded retries, a circuit breaker, and concurrency
   limit.
4. Add per-session/global call quotas and an atomic token/cost budget reservation.
5. Configure and test a spend ceiling below the account cutoff; emit a typed budget-exhausted repair.
6. Only then run a minimal paid smoke test and record its latency, schema, token, and cost evidence.

## 9.4. P1 — Build the planned graph and Agent capabilities

1. Add pinned LangGraph and a typed state containing lattice, history, memory, counters, and
   `allowed_tools`.
2. Wire separate assembler, critic, repair, and adapter nodes with a checkpointer and `thread_id`.
3. Implement small typed context/memory results, then the language-specific lexicon after the
   ASL/SgSL decision.
4. Add an explicit repair planner and human-interpreter/fallback action.
5. Add a confirmed-correction contract and in-conversation signer adapter with deletion/isolation.

## 9.5. P1 — Make telemetry evaluable

1. Create a per-session JSON run record keyed by privacy-safe session and utterance identifiers.
2. Record model/prompt versions, node route, revisions, critic vetoes, tool calls, action, latency,
   tokens, cache use, AWS request ID, cost, and guard state.
3. Correct usage status so a malformed response is logged as failed.
4. Expose aggregated distributions rather than only count/mean/min/max; p50/p95/p99 matter for live
   captioning.
5. Add the one-command EVL/evaluation package with frozen-lattice and end-to-end tracks.

## 9.6. P2 — Close deployment and reproducibility hazards

1. Pin/lock the dependency set and run a clean-clone install/test gate.
2. Resolve current Starlette/HTTP client deprecation warnings.
3. Prevent replay activation in production and add authentication/rate limiting before exposure.
4. Add AWS failure fixtures for throttling, timeout, invalid envelope, access denied, and partial
   usage metadata.
5. Re-run live repeated evaluation only when costs are guarded and evidence is persisted.

---

# 10. FINAL ACCEPTANCE CHECKLIST

## 10.1. Safe claims now

- [x] Bedrock assembly is optional and disabled by default.
- [x] A deterministic exact-caption-template fallback exists.
- [x] Built-in Agent requests expose no dedicated frame, landmark, or coordinate fields.
- [x] Bedrock response JSON receives strict local shape/type/trace checks.
- [x] Assembler, critic, and revision roles use distinct system prompts.
- [x] Revision is hard-capped at zero or one in current configuration.
- [x] Critic rejection and malformed output fail closed with no caption.
- [x] Recognition uncertainty gates run before Agent invocation.
- [x] Non-confident outward contracts prohibit caption and TTS text.
- [x] Per-call token fields are written to logs when available.
- [x] The full current test/lint/type/format/install-health baseline passes.

## 10.2. Claims blocked until implementation and evidence exist

- [ ] Full confidence-scored `GlossLattice` reaches the Agent.
- [ ] Explicit gaps remain gaps and cannot be completed from plausibility.
- [ ] Every caption span is deterministically grounded in lattice evidence.
- [ ] Typed LangGraph state, graph, checkpointer, thread continuity, and allowed tools exist.
- [ ] Lexicon, context, memory, TTS, and escalation tools are implemented and secured.
- [ ] Repair is selected correctly, communicated to both parties, and evaluated.
- [ ] Confirmed corrections adapt the remainder of a conversation without cross-signer leakage.
- [ ] Startup readiness proves actual runtime model access in the configured profile/region.
- [ ] Explicit deadlines, bounded retries, concurrency control, and circuit breaking exist.
- [ ] Caller cancellation/disconnect prevents later model calls and cannot corrupt success metrics.
- [ ] Token/cost aggregation, prompt caching, spend ceiling, and an exercised kill switch exist.
- [ ] One JSON run record reconstructs every Agent route without storing sensitive payloads.
- [ ] Live repeated runs measure fidelity, schema rate, refusal precision, latency, tokens, and cost.
- [ ] Stages 6–7 meet the 0.5–2 s target at p50/p95 under stated network conditions.
- [ ] A clean-clone environment reproduces the passing gate from pinned dependencies.

## 10.3. Final conclusion

The Agent side is a **good safety-conscious scaffold and deterministic fallback**, not the planned
Agent system. Its local tests are healthy, its output parser is stricter than a typical prototype,
and its refusal boundary is valuable. However, the two defining claims of the architecture—reasoning
over a provenance-carrying hypothesis lattice and refusing unsupported meaning—are not yet secured.
One is absent; the other failed an adversarial control-flow test.

The next implementation should not be a larger model or more prompt prose. It should establish the
real lattice contract, deterministic evidence grounding, trustworthy AWS readiness, an application
deadline, and an atomic spend guard. Once those gates exist, the team can add LangGraph tools and
memory, then perform the live repeated evaluation needed to make honest quality, latency, and cost
claims.
