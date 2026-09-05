**BACKEND COMPARISON TEST**

# METADATA

<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field                   | Value |
| :---------------------- | :---- |
| <strong>Code</strong>                | BCT |
| <strong>Status</strong>              | Live |
| <strong>Last reviewed</strong>       | 2026-09-05 |
| <strong>Source of truth for</strong> | Backend implementation versus ARC and PLN at this review snapshot |
| <strong>Related</strong>             | [ARC](../plan/ARC_architecture.md) · [PLN](../plan/PLN_plan.md) · [RDM](../README.md) |

<strong>For the team.</strong> This report answers whether the merged backend implements the
architecture and execution plan. It distinguishes implemented behavior from scaffolding, planned
work, and claims that are not yet supported by evidence. ARC remains the source of truth for
technical direction; PLN remains the source of truth for execution order.

<strong>Review snapshot.</strong> The backend is the implementation under src/, with its tests and
packaging files, corresponding to backend commit aeea477 (Build first-draft ASL backend). The current
working tree also contains the docs-side planning changes. Findings below are based on the files
present in this workspace, not on a deployed service, camera run, AWS account, or collected dataset.

<strong>Verification rule.</strong> A check is marked PASS only when it was actually executed. A
source-level feature without a runtime or measurement artifact is marked PARTIAL or NOT IMPLEMENTED.

</details>

---

# 1. EXECUTIVE VERDICT

## 1.1. Overall result

The merged backend is a credible <strong>landmark-stream service and safety-oriented baseline</strong>,
but it is not yet the end-to-end system specified by ARC and PLN.

What is implemented is the server seam: strict landmark/session contracts, authenticated bounded
WebSocket ingestion, ephemeral state, geometric utterance segmentation, body-relative 2D
normalization, a DTW template recognizer, confidence gates, deterministic caption templates, and an
optional bounded Bedrock caption/critic path. The code also fails closed when recognition or caption
assembly is unavailable. See
[contracts/landmarks.py](../src/simplynext/contracts/landmarks.py#L152),
[sessions/store.py](../src/simplynext/sessions/store.py#L125),
[pipeline/segmentation.py](../src/simplynext/pipeline/segmentation.py#L296),
[pipeline/normalization.py](../src/simplynext/pipeline/normalization.py#L507), and
[orchestrator.py](../src/simplynext/orchestrator.py#L130).

The largest gaps are the ones that make the planned product more than a backend seam:

1. There is no camera capture, MediaPipe Tasks landmarker, largest-person subject tracker, or
   MediaPipe tracking-state implementation.
2. There is no trained small temporal classifier, calibration workflow, GlossLattice, P2 VLM
   baseline, dataset, or held-out-signer evaluation.
3. The Bedrock path has a bounded assembler/critic, but no LangGraph state graph, tools, conversation
   memory, per-signer adapter, or spend guard.
4. The planned reverse spoken-to-signed direction, skeleton renderer, UI, evaluation package, and
   fallback recording are absent.
5. The implementation boundary disagrees with the plan: the plan describes camera and perception in
   the project pipeline, while the backend README explicitly says the Flutter client currently
   supplies demonstration landmarks and is expected to perform capture and MediaPipe extraction.

## 1.2. Claim status

| Area | Status | Review conclusion |
| :--- | :----- | :---------------- |
| Backend protocol and session safety | <strong>PASS</strong> | Strong implementation with tests present. |
| Fail-closed uncertainty behavior | <strong>PASS</strong> | No caption/TTS is emitted for non-confident results. |
| Body-relative 2D preprocessing | <strong>PARTIAL</strong> | Robust XY normalization, interpolation, masks, and derivatives exist. |
| ARC perception pipeline | <strong>NOT IMPLEMENTED</strong> | The backend consumes landmarks; it does not produce them. |
| ARC feature budget | <strong>PARTIAL</strong> | Fixed hand/pose/face layouts exist, but handedness and world-landmark separation do not. |
| PLN segmentation work | <strong>PARTIAL</strong> | Geometry/hysteresis/buffer replay exists; the comparison arm does not. |
| PLN recognition work | <strong>PARTIAL</strong> | DTW template baseline exists; training and calibration evidence do not. |
| ARC agentic layer | <strong>PARTIAL</strong> | Optional Bedrock assembler/critic exists; planned graph/tools/memory do not. |
| Two-way conversation | <strong>NOT IMPLEMENTED</strong> | No spoken-to-signed dependency or renderer exists. |
| Evaluation and submission evidence | <strong>NOT IMPLEMENTED</strong> | No EVL, evaluation command, dataset, or measured product result exists. |

## 1.3. Release-level conclusion

The backend can be described accurately as:

> A runnable, authenticated landmark-stream backend with deterministic geometric segmentation,
> body-relative feature preprocessing, a closed-vocabulary DTW template baseline, fail-closed
> confidence policy, and optional bounded Bedrock caption assembly.

It cannot yet be described as a working real-time camera-to-text translator, a MediaPipe backend, a
trained sign recognizer, a LangGraph tool-using agent, or a two-way sign conversation product.

---

# 2. REVIEW METHOD AND VERIFICATION

## 2.1. Sources compared

The comparison used the following as controlling documents:

1. [ARC](../plan/ARC_architecture.md), especially ARC_S3.2 (landmark budget), ARC_S4.3
   (representation), ARC_S5.3–ARC_S5.7 (recognition, assembly, alternatives and reverse
   direction), ARC_S6.1–ARC_S6.5 (pipeline, agent rules and perception rules), ARC_S8.3–ARC_S8.4
   (cost and metrics), and ARC_S9 (decisions).
2. [PLN](../plan/PLN_plan.md), especially PLN_S2.4 (standing constraints), PLN_S3.3–PLN_S3.4
   (module map and frozen interfaces), tasks T0.1–T0.6, T1.1–T1.6, T2.1–T2.4, T4.1–T4.5,
   T5.1–T5.8, and the WP6–WP8 exit criteria.
3. [RDM](../README.md), to reconcile the planning documents with the backend branch's stated
   runtime boundary and project status.

## 2.2. Checks run

| Check | Result | Evidence |
| :---- | :----- | :------- |
| Static AST parsing | <strong>PASS</strong> | Python parsed 42 files: main.py, src/**/*.py, and tests/**/*.py. |
| Git whitespace check | <strong>PASS</strong> | git diff --check returned no errors. |
| Test inventory | <strong>70 tests found</strong> | Ten test files contain 70 test functions by source inspection. |
| python3 -m pytest | <strong>BLOCKED</strong> | pytest is not installed in the current environment. |
| python3 -m ruff check ... | <strong>BLOCKED</strong> | ruff is not installed in the current environment. |
| python3 -m mypy src | <strong>BLOCKED</strong> | mypy is not installed in the current environment. |
| Runtime import/test execution | <strong>BLOCKED</strong> | pydantic, fastapi, boto3, and other runtime dependencies are not installed. |

The source-level findings are therefore implementation inspection results, not a claim that the
backend's automated test suite passes. A clean environment must install the project dependencies
before the test gate can be closed.

---

# 3. ARCHITECTURE COMPARISON

## 3.1. Pipeline boundary

ARC_S6.1 starts with camera capture, a bounded queue, subject tracking and MediaPipe landmark
extraction. The backend's actual boundary starts after those steps. LandmarkBatch requires canonical
coordinates and LandmarkFrame accepts already materialized pose, hand and face arrays; the contract
explicitly says landmarks must be canonicalized on the client
([landmarks.py](../src/simplynext/contracts/landmarks.py#L175-L207)). The README independently states
that the Flutter client performs camera capture and MediaPipe extraction and currently emits
demonstration landmarks ([README.md](../README.md#L240-L255)).

This is a material architecture decision, not merely a missing module. Either:

1. implement PLN's camera/perception packages in the backend and make the backend boundary match ARC;
   or
2. formally revise ARC_S6.1, PLN_S3.3 and PLN_S3.4 so Flutter is the landmark producer and the
   Python service is explicitly the canonical landmark consumer.

Until one is chosen, the repository has two incompatible descriptions of where stages ① and ② run.

## 3.2. Architecture decision matrix

| ARC requirement | Backend evidence | Result |
| :--------------- | :--------------- | :---- |
| Subject selection is tracking, with largest/central hysteresis (ARC_S2.2, decision 1) | subject_id is an optional client field; the WebSocket passes it to the segmenter, which resets on a subject change. No detector ranking or tracker exists. | <strong>PARTIAL</strong> — identity is carried, not selected. |
| Hands + handedness + upper-body pose + curated face (ARC_S3.2, decision 2) | Contract fixes 21 points per hand, 9 pose points and 16 face points. It has hand scores but no handedness/chirality field. | <strong>PARTIAL</strong> — fixed layouts exist; the required semantic hand labels do not. |
| Reject full 468-point face input | Contract accepts only 16 face points, not a 468-point mesh. | <strong>PASS at seam</strong> — the curated limit is enforced by the API. |
| Body-normalized 2D plus per-hand world landmarks (ARC_S4.3, decision 3) | Normalizer uses median shoulder midpoint/width and image-plane rotation; z is retained as non-metric metadata and omitted from temporal features. | <strong>PARTIAL</strong> — XY normalization is implemented; separate world hand landmarks are not. |
| Confidence gates, no zero guessing, short-gap interpolation (ARC_S6.5 rules 1, 8, 15, 16) | Points below threshold become unavailable; short internal gaps are interpolated with provenance masks. | <strong>PASS for implemented inputs</strong> — requires real landmark producer integration. |
| Explicit velocity and acceleration (ARC_S4.3) | Resampling differentiates masked XY features into velocity and acceleration. | <strong>PASS</strong> — no evidence yet that the resulting features are useful on real signs. |
| Never temporally smooth the face (ARC_S6.5 rule 13) | No smoothing implementation exists for hands, body or face. | <strong>PARTIAL</strong> — face is not smoothed, but the planned hand/body filter is also absent. |
| Geometry + hysteresis + buffer-and-replay (ARC_S5.3, decision 6) | UtteranceSegmenter implements idle/possible-start/active/possible-end state, pre-roll, inactivity, missing-hand timeout, max duration and replay. | <strong>PASS for Arm A</strong>. |
| Build and compare sliding-window Arm B (ARC_S5.6.2, decision 20) | No segmenter interface, sliding-window classifier, blank class or comparison harness. | <strong>NOT IMPLEMENTED</strong>. |
| Small trained temporal classifier, top-k and calibrated confidence (ARC_S5.3, decision 5) | DtwTemplateRecognizer performs nearest-template masked DTW and returns top-k; calibration is accepted only when an external bundle marks it validated. | <strong>PARTIAL</strong> — template baseline, not trained classifier/calibration workflow. |
| Compact gloss lattice with provenance (ARC_S5.7, decision 19) | RecognitionResult has ranked candidates; the orchestrator passes only the accepted top candidate as one GlossEvidence item to assembly. No GlossLattice, timestamps or provenance rung exists. | <strong>NOT IMPLEMENTED</strong>. |
| Agent once per utterance, not per frame (decision 7) | The WebSocket invokes process_frames only after a committed segment or explicit commit/end. | <strong>PASS</strong>. |
| Agentic assembly, critic, bounded graph loop and tools (ARC_S6.2–ARC_S6.3) | Optional Bedrock class has assembler/critic/revision roles, structured JSON checking and a maximum of one revision. Prompts are inline; no LangGraph, tools, memory, reducers or allow-list exists. | <strong>PARTIAL</strong> — bounded model workflow, not the planned graph agent. |
| Refusal below threshold (decision 8) | ConfidencePolicy gates readiness, calibration, vocabulary, coverage, duration, transport loss, confidence and margin; contracts reject caption/TTS on non-confident results. | <strong>PASS</strong> — strongest alignment. |
| Reverse spoken-to-signed direction (ARC_S5.7, decision 18) | No reverse/ package, spoken input, lexicon, .pose lookup, stitcher or renderer. | <strong>NOT IMPLEMENTED</strong>. |
| Pose skeleton, not avatar (decision 23) | No reverse renderer or UI exists to demonstrate this. | <strong>NOT IMPLEMENTED</strong>. |
| No OpenPose, SLRT or SAM-SLR code/model/derivative (decisions 16, 21, 22) | No imports or dependencies for these rejected repositories were found in src or pyproject.toml. | <strong>PASS by inspection</strong>. |
| Token accounting and cost per run (ARC_S8.3, decision 12) | Bedrock logs per-call input/output/total token fields. In-process metrics contain generic counters/timings only; no token accumulator, price calculation, run record or spend ceiling exists. | <strong>PARTIAL</strong>. |
| Held-out-signer evaluation (decision 24) | No dataset, split manifest, evaluator or measured accuracy exists. | <strong>NOT IMPLEMENTED</strong>. |

## 3.3. Feature-budget consequence

The implementation's default feature schema is materially wider than the plan's “under 150 numbers”
motivation. The normalizer builds position names for pose, both raw hands, face, and both handshape
groups ([normalization.py](../src/simplynext/pipeline/normalization.py#L560-L591)). That is:

- 9 pose points + 42 hand points + 16 face points + 42 handshape points = 109 point groups;
- x and y for each = 218 position scalars;
- position + velocity + acceleration = <strong>654 scalar features per frame</strong>.

This is not automatically wrong, because the current recognizer is a template baseline and masks are
preserved. It is a direct mismatch with PLN_T4.1's intended small curated model, however. Before
training, the team should make the feature budget explicit, decide whether handshape duplicates the
raw hand stream, and record the chosen dimension in the evaluation artifact.

---

# 4. EXECUTION-PLAN COMPARISON

## 4.1. WP0 — Foundations

| Task | Status | Evidence and interpretation |
| :--- | :----- | :--------------------------- |
| T0.1 repository skeleton | <strong>PARTIAL</strong> | Installable src/simplynext package, tests, data and docs placeholders exist. The tree does not match PLN_S3.3; the root main.py is retained as a compatibility shim rather than removed. |
| T0.2 exact dependencies | <strong>NOT IMPLEMENTED</strong> | requirements.txt is only -e .; pyproject.toml uses version ranges and lacks mediapipe, langgraph, pose-format and spoken-to-signed-translation. See [requirements.txt](../requirements.txt#L1-L2) and [pyproject.toml](../pyproject.toml#L11-L27). |
| T0.3 config and secrets | <strong>PARTIAL</strong> | Namespaced .env settings, AWS credential-chain guidance and a literal Bedrock model default exist. No startup Bedrock preflight exists; thresholds are split between settings and NormalizationConfig/SegmenterConfig. See [config.py](../src/simplynext/config.py#L18-L65). |
| T0.4 instrumentation | <strong>PARTIAL</strong> | Payload-free JSON logging and in-process metrics exist. Bedrock logs usage per call, but there is no per-session JSON run record, spend guard, token-cost metric or perception detector/tracker counters. |
| T0.5 frozen interfaces | <strong>PARTIAL</strong> | Strict Pydantic contracts exist for landmark batches, sessions, utterance replay and outbound events. The four planned Frame, LandmarkFrame, FeatureWindow and GlossLattice boundaries are not present as planned; only LandmarkFrame is a matching named type. |
| T0.6 walking skeleton | <strong>PARTIAL</strong> | The API/session path is testable with synthetic landmarks, but there is no live-camera five-minute skeleton and no python -m src.main entry point. |

## 4.2. WP1 — Perception

| Task | Status | Evidence and interpretation |
| :--- | :----- | :--------------------------- |
| T1.1 capture loop | <strong>NOT IMPLEMENTED</strong> | No capture/ package or bounded camera queue exists. The 240-frame server deque is a bounded transport/session buffer, not the planned size-one capture queue. |
| T1.2 subject tracker | <strong>NOT IMPLEMENTED</strong> | No largest/central detection ranking or hysteresis tracker exists. subject_id is client supplied. |
| T1.3 MediaPipe landmarker, both arms | <strong>NOT IMPLEMENTED</strong> | No mediapipe import, .task asset, VIDEO/LIVE_STREAM mode, Holistic arm, or Hand+Pose arm exists. |
| T1.4 tracking state | <strong>NOT IMPLEMENTED</strong> | No detector rate limiter, hand identity matching, handedness averaging or duplicate-hand handling exists. |
| T1.5 normalizer | <strong>PARTIAL / strongest WP1 item</strong> | Sequence-level median shoulder reference, rotation, confidence gating, short-gap interpolation, masks, handshape normalization and XY velocity/acceleration are implemented. Per-hand world landmarks and the planned smoothing/canonical 3D path are not. |
| T1.6 visualizer and health panel | <strong>NOT IMPLEMENTED</strong> | Metrics endpoint exists, but no skeleton overlay, confidence-colored visualizer or live perception panel exists. |

## 4.3. WP2 — Segmentation

T2.2 is substantially implemented in
[pipeline/segmentation.py](../src/simplynext/pipeline/segmentation.py#L296-L514): it has a bounded
pre-roll, hysteresis evidence counters, signing-space checks, motion energy, inactivity and
missing-hand termination, maximum duration, buffer limit, subject-change reset and manual commit.

The package still fails the plan as a decision experiment. There is no common segment/base.py
interface (T2.1), no sliding-window blank-class arm (T2.3), and no comparison report (T2.4).
Therefore the implementation demonstrates one proposed segmentation strategy but does not settle
ARC question 5 or decision 20.

## 4.4. WP3 — Data

WP3 is <strong>not implemented</strong>. The only data artifact is an example caption-template file
with three glosses
([caption_templates.example.json](../data/caption_templates.example.json#L1-L25)). There is no
explicit vocabulary/gloss registry, consent-controlled recording protocol, landmark capture
manifest, signer-based split, augmentation, calibration set, or recognition bundle. This agrees with
the README's project status: the dataset is not collected and no calibrated template bundle exists
([README.md](../README.md#L512-L539)).

The practical consequence is that the service is expected to return 503 readiness and repair
requests by default. That is honest behavior, but it means the product cannot yet produce a measured
caption from a real sign.

## 4.5. WP4 — Recognition

| Task | Status | Evidence and interpretation |
| :--- | :----- | :--------------------------- |
| T4.1 feature assembly | <strong>PARTIAL</strong> | Features are generated from a fixed contract layout, not an index list in config. The feature schema includes all 16 face points and duplicated handshape coordinates. |
| T4.2 small temporal classifier | <strong>NOT IMPLEMENTED</strong> | DtwTemplateRecognizer is a nearest-template baseline; no trainable temporal model, variable-duration training pipeline or model checkpoint format exists. |
| T4.3 calibration | <strong>PARTIAL</strong> | Distance-logistic calibration can be loaded and is required by policy when marked validated. No validation fitting, reliability curve, threshold selection procedure or refusal-precision result exists. |
| T4.4 lattice/provenance | <strong>NOT IMPLEMENTED</strong> | Candidates are top-k at the recognizer boundary, but the orchestrator sends only the accepted candidate as g0; no per-slot timestamps, provenance rungs or compact lattice contract exists. |
| T4.5 P2 VLM baseline | <strong>NOT IMPLEMENTED</strong> | No frame sampling, multimodal request or measured classifier-versus-VLM comparison exists. |

The current recognizer's safety posture is good: it rejects invalid schemas, marks unvalidated
calibration, returns a ranked closed-vocabulary result, and leaves acceptance to the policy
([dtw.py](../src/simplynext/recognition/dtw.py#L180-L292)). That is useful infrastructure for T4.2,
but it is not evidence that recognition accuracy meets the plan.

## 4.6. WP5 — Agent

The deterministic assembler is an exact-template lookup and refuses any gloss sequence that has no
configured caption
([assembler.py](../src/simplynext/agent/assembler.py#L113-L181)). The optional Bedrock assembler
adds strict JSON parsing, evidence-ID checks, a separate critic prompt and a hard one-revision
maximum ([bedrock.py](../src/simplynext/agent/bedrock.py#L103-L190)). These are valuable partial
implementations of T5.3, T5.5 and T5.6.

The following plan items remain open:

1. T5.1/T5.2: no typed graph state, reducers, LangGraph graph, persistent thread state or
   allowed_tools boundary.
2. T5.4: no lexicon, conversation-memory or context-hint tools; no word-sense keys.
3. T5.7: no per-signer episodic memory or confirmed-correction adapter.
4. T5.8: no AWS preflight, prompt caching, spend ceiling, token-cost calculation or run record.

There is also a data-flow reduction that matters: TranslationEngine constructs
AssemblyRequest(... evidence=(GlossEvidence.from_candidate("g0", decision.accepted),))
([orchestrator.py](../src/simplynext/orchestrator.py#L215-L223)). This gives the agent one accepted
gloss, not the planned hypothesis lattice. The Bedrock layer is therefore a bounded caption checker,
not yet a lattice-to-conversation agent.

## 4.7. WP6 — Reverse direction

WP6 is <strong>not implemented</strong>. pyproject.toml has no spoken-to-signed dependency, and the
source tree has no reverse/ package. Consequently there is no ASR seam, glosser, project's own
lexicon, word-sense lookup, coverage ladder, fingerspelling fallback, .pose stitcher, or
pose-skeleton renderer. ARC_S5.7 and decisions 18/19/23 therefore remain entirely unimplemented in
code.

## 4.8. WP7 and WP8 — Interface, evaluation and submission

The backend has API health/readiness endpoints, a metrics endpoint and WebSocket events, but no
planned one-screen demo UI, visual gloss trace, reverse-direction screen, fallback recording or
robustness evidence. There is no EVL document, evaluate/ package, split manifest, held-out-signer
metric, repeated-agent run, Deaf reviewer record, clean-clone evidence package, deck or captioned
video. These are not inferred failures; they are explicitly future work in PLN and are absent from
the workspace.

---

# 5. SAFETY, SECURITY AND OPERABILITY

## 5.1. Strong alignments

1. <strong>No raw video at the backend seam.</strong> The API accepts canonical landmark batches, not
   camera frames. This reduces payload and privacy exposure, provided the client boundary is
   documented and secured.
2. <strong>Ephemeral session handling.</strong> Sessions use TTLs, bounded frame buffers, hashed bearer
   tokens, exclusive stream ownership, monotonic batch/frame/control sequences, and explicit live-data
   clearing ([store.py](../src/simplynext/sessions/store.py#L125-L205) and
   [store.py](../src/simplynext/sessions/store.py#L224-L255)).
3. <strong>Transport limits.</strong> HTTP and WebSocket size checks, invalid-message limits and typed
   retryable errors are implemented ([websocket.py](../src/simplynext/api/websocket.py#L78-L103) and
   [middleware.py](../src/simplynext/api/middleware.py#L11-L61)).
4. <strong>Fail-closed output.</strong> The result contracts prohibit caption/TTS fields on non-confident
   responses, and the policy requires readiness and calibrated confidence before acceptance
   ([utterances.py](../src/simplynext/contracts/utterances.py#L62-L87) and
   [policy.py](../src/simplynext/recognition/policy.py#L108-L192)).
5. <strong>Prompt payload minimization.</strong> The Bedrock request whitelist sends utterance ID,
   language, glosses, IDs and confidence, not landmarks or coordinates. The assembly tests assert
   this property ([bedrock.py](../src/simplynext/agent/bedrock.py#L294-L317) and
   [test_assembler.py](../tests/test_assembler.py#L84-L107)).
6. <strong>Rejected repository isolation.</strong> No forbidden reference-repository imports or
   dependencies were found, satisfying PLN_S2.4 rule 10 by inspection.

## 5.2. Important operational gaps

1. BedrockCaptionAssembler.ready returns true without checking model access; the plan requires a
   preflight in the configured region. Readiness is deliberately local-configuration-only in the
   README, so an operator can see a ready caption path that still fails at the first paid call.
2. Per-call usage logging is not the same as cost discipline. The implementation logs token fields
   ([bedrock.py](../src/simplynext/agent/bedrock.py#L231-L280)), but does not persist or aggregate
   them, calculate cost, or stop calls at a configured ceiling.
3. Thresholds are not centralized as PLN_T0.3 requests. Runtime settings hold some thresholds, while
   normalization and segmentation hold additional defaults in separate dataclasses.
4. The default requirements.txt is not a reproducible pinned install. A clean clone cannot satisfy
   the plan's dependency gate from the current file without resolving unpinned ranges.
5. No runtime test result is currently available because the environment lacks dependencies. The 70
   test functions are evidence of intended coverage, not evidence of execution.

---

# 6. PRIORITIZED GAP CLOSURE

## 6.1. P0 — Resolve the boundary before adding models

Decide whether the Python backend is:

1. a full local camera-to-caption process, as drawn in ARC_S6.1 and PLN_S3.3; or
2. a landmark-only service whose Flutter client owns capture, MediaPipe and subject tracking.

Then update ARC, PLN, README, the frozen contracts and the demo claim in one change. If option 2 is
selected, require the client to provide the missing semantics explicitly: subject identity policy,
handedness, detector version, world-landmark availability, confidence meaning, and the exact feature
schema. This is the highest-leverage action because it prevents implementing the wrong half of the
system.

## 6.2. P1 — Close the runtime foundation gate

Complete T0.2–T0.6 in this order:

1. Install the project's dependencies in a clean environment and run the 70-test suite, Ruff and
   mypy; record the results.
2. Choose and pin the actual runtime dependencies. Add MediaPipe, LangGraph and the reverse
   dependency only if the boundary decision keeps those stages in scope.
3. Centralize thresholds and add the model-access preflight, token accumulator, spend guard and run
   record.
4. Define the four actual pipeline contracts, especially FeatureWindow and GlossLattice, before
   expanding recognition or agent behavior.

## 6.3. P2 — Make recognition evidence real

Complete T3.1–T4.4 before claiming translation:

1. Choose ASL or SgSL, write the closed vocabulary, document consent, and collect landmarks with
   signer IDs and signer-separated splits.
2. Decide the final feature budget. Reconcile the current 654-dimensional schema with the plan's
   small-model target and add handedness/world-hand features if the chosen architecture requires
   them.
3. Train the small temporal classifier, fit calibration on a validation split, create the
   reliability curve, and derive the refusal threshold from that curve.
4. Carry all top-k candidates, timestamps, confidence and provenance into a compact lattice; pass
   the lattice, not only top-1, to assembly.
5. Build P2 and record classifier-versus-P2 results in the same evaluation table.

## 6.4. P3 — Complete the differentiating product behavior

Implement the bounded graph/repair workflow, tool allow-list, confirmed-correction adapter and
visible per-token gloss trace. Then add the RSS-based reverse direction, the project's lexicon and
the skeleton renderer. Keep the current deterministic template assembler as a safe local fallback.

## 6.5. P4 — Turn the implementation into evidence

Create EVL, implement the one-command evaluator, measure held-out-signer accuracy, task completion,
intervention/refusal precision, robustness, latency, token cost and provenance coverage. Run the
clean-clone check and record a Deaf or hard-of-hearing reviewer session before changing the product
claim from “first-draft backend” to “working translator.”

---

# 7. FINAL ACCEPTANCE CHECKLIST

The following claims are safe now:

- strict versioned landmark/session/event contracts;
- authenticated, bounded, ephemeral WebSocket landmark ingestion;
- deterministic geometric segmentation with hysteresis and replay;
- body-relative 2D normalization with confidence masks, interpolation and derivatives;
- closed-vocabulary DTW template baseline with top-k output;
- fail-closed confidence, calibration and caption policies;
- exact caption templates and optional bounded Bedrock assembler/critic;
- no raw camera frames sent to Bedrock and no imports from rejected reference repositories.

The following claims must remain blocked until the corresponding PLN work is completed and
measured:

- camera capture and MediaPipe landmark extraction in the backend;
- stable largest-person and handedness tracking;
- trained recognition accuracy or calibrated refusal precision;
- ARC's full landmark budget, including world hand landmarks and provenance lattice;
- LangGraph tools, conversation memory, per-signer adaptation and spend guard;
- spoken-to-signed translation and skeleton rendering;
- two-way demo behavior, held-out-signer generalization and robustness;
- a passing clean-clone/runtime verification result in an environment with installed dependencies.

<strong>Conclusion:</strong> the backend merge is a solid safety-and-transport foundation and a useful
partial implementation of the local sign-to-caption path. It is not yet aligned enough with ARC/PLN
to serve as evidence that the planned end-to-end product has been built. The next change should
resolve the capture/perception boundary and close the dependency/test gate before adding more
user-facing claims.
