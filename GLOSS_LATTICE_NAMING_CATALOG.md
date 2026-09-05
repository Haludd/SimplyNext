# GlossLattice Naming Migration Catalog

This is a non-authoritative implementation and migration aid for teams integrating with the
SimplyNext frontend-classified path. [`CTR_contracts.md`](CTR_contracts.md) is the single source of
truth for the version 1.0 `GlossLattice` input. If any name, type, limit, or meaning here differs
from CTR, use CTR and correct this catalog.

The outbound names in section 5 are a deliberate backend convention aligned with CTR, but they are
not part of the CTR input contract.

## Metadata

| Field | Value |
| :-- | :-- |
| Branch | `front_back_contract` |
| Authoritative input contract | `CTR_contracts.md` |
| Executable input model | `src/simplynext/contracts/gloss_lattice.py` |
| Golden fixture | `tests/fixtures/gloss_lattice_v1.json` |
| Contract tests | `tests/test_gloss_lattice_contract.py` |
| Status | Secondary catalog; safe for migration reference only |

## 1. Naming conventions

| Category | Convention | Example |
| :-- | :-- | :-- |
| JSON property | lowercase `snake_case` | `lattice_seq`, `gloss_id` |
| Discriminator/enum value | lowercase `snake_case` | `gloss_lattice`, `top_k_signer_confirmed` |
| Python model or enum | `PascalCase` | `GlossLattice`, `GlossProvenance` |
| Python constant | uppercase `SNAKE_CASE` | `MAX_GLOSS_LATTICE_BYTES` |
| Environment variable | `SIMPLYNEXT_` + uppercase setting | `SIMPLYNEXT_MAX_LATTICES_PER_SESSION` |
| Millisecond value | `_ms` suffix | `started_at_ms`, `server_ms` |
| Identifier value | `_id` suffix | `session_id`, `gloss_id` |
| Ordered message counter | `_seq` suffix | `lattice_seq`, `control_seq` |
| Collection | plural noun | `slots`, `candidates`, `reason_codes` |

There are no JSON aliases or automatic case transforms. For wire models, the Python field name is
the JSON property name.

## 2. Shared CTR scalar rules

| Name | JSON type | Exact rule |
| :-- | :-- | :-- |
| `Identifier` | string | Length 1–128; `^[A-Za-z0-9][A-Za-z0-9_.:-]*$`; opaque and case-sensitive |
| `UUID` | string | Parsed as a UUID |
| `Confidence` | number | Finite; inclusive range 0.0–1.0 |
| safe integer | integer | Inclusive range 0–9,007,199,254,740,991 |

CTR models reject unknown properties, type coercion, non-finite numbers, and surrounding
identifier whitespace. They are immutable after validation. JSON arrays become Python tuples;
enums serialize as strings, UUIDs as UUID strings, and `None` as JSON `null`.

### Contract constants

| Python constant | Wire meaning | Value |
| :-- | :-- | --: |
| `GLOSS_LATTICE_SCHEMA_VERSION` | `schema_version` | `"1.0"` |
| `GLOSS_LATTICE_TIMEBASE` | `timebase` | `"session_monotonic_ms"` |
| `GLOSS_LATTICE_CONFIDENCE_KIND` | `producer.confidence_kind` | `"calibrated_probability"` |
| `MAX_GLOSS_LATTICE_BYTES` | raw UTF-8 ceiling | 32,768 |
| `MAX_GLOSS_LATTICE_SLOTS` | slots per lattice | 64 |
| `MAX_GLOSS_CANDIDATES_PER_SLOT` | candidates per slot | 5 |
| `MAX_SAFE_JSON_INTEGER` | sequence/timestamp ceiling | 9,007,199,254,740,991 |

## 3. Authoritative frontend-to-backend input

All properties in this section are required. In particular, literal-valued fields and the
nullable `resolved_gloss_id` must still be present.

### 3.1 `GlossLattice`

| JSON path | Type | Value or constraint | Meaning |
| :-- | :-- | :-- | :-- |
| `type` | string literal | `gloss_lattice` | WebSocket union discriminator |
| `schema_version` | string literal | `1.0` | Exact contract version |
| `session_id` | UUID string | equals authenticated route/session | Session correlation, not authorization |
| `lattice_seq` | integer | safe range; increases per session | Immutable message sequence |
| `utterance_id` | `Identifier` | stable across a repaired utterance | Logical utterance identity |
| `language` | enum | `sgsl`, `asl` | Producer vocabulary language |
| `timebase` | string literal | `session_monotonic_ms` | Clock declaration for every timestamp |
| `started_at_ms` | integer | safe range | Inclusive utterance start |
| `ended_at_ms` | integer | safe range; greater than start | Exclusive utterance end |
| `producer` | object | `GlossLatticeProducer` | Reproducibility lineage |
| `slots` | array | 1–64 `GlossSlot` objects | Ordered, non-overlapping sign positions |

### 3.2 `producer`

| JSON path | Type | Value or constraint | Meaning |
| :-- | :-- | :-- | :-- |
| `producer.classifier_id` | `Identifier` | required | Stable classifier family/artifact ID |
| `producer.classifier_version` | `Identifier` | required | Exact classifier version |
| `producer.confidence_kind` | string literal | `calibrated_probability` | Confidence semantics |
| `producer.calibration_version` | `Identifier` | required | Exact calibration version |
| `producer.vocabulary_version` | `Identifier` | required | Closed-vocabulary version |

### 3.3 `slots[]`

| JSON path | Type | Value or constraint | Meaning |
| :-- | :-- | :-- | :-- |
| `slots[].slot_index` | integer | 0–63; equals array position | Zero-based position |
| `slots[].slot_id` | `Identifier` | unique within lattice | Stable slot identity |
| `slots[].start_ms` | integer | safe range | Inclusive slot start |
| `slots[].end_ms` | integer | safe range; greater than start | Exclusive slot end |
| `slots[].candidates` | array | required; 0–5 candidates | Retained ranked hypotheses |
| `slots[].resolved_gloss_id` | `Identifier` or null | required | Resolution selected under provenance rules |
| `slots[].provenance` | enum | four values in section 6 | Origin of the resolution or its absence |

### 3.4 `slots[].candidates[]`

| JSON path | Type | Value or constraint | Meaning |
| :-- | :-- | :-- | :-- |
| `slots[].candidates[].gloss_id` | `Identifier` | unique in slot | Closed-vocabulary lexicon key |
| `slots[].candidates[].rank` | integer | 1–5; contiguous | One-based classifier rank |
| `slots[].candidates[].confidence` | number | finite 0.0–1.0 | Calibrated probability |

### 3.5 Cross-field rules

- All timestamps use the session monotonic timebase and all intervals are half-open.
- Every slot lies inside `[started_at_ms, ended_at_ms)`.
- Slot indices are exactly `0..N-1`; slot IDs are unique.
- The next slot starts at or after the previous slot ends. Gaps are valid; overlap is invalid.
- Candidate ranks are exactly `1..N`, candidate confidence is non-increasing, and candidate
  `gloss_id` values are unique using exact case-sensitive comparison.
- `classifier_high_confidence` resolves exactly to rank 1 and requires at least one candidate.
- `top_k_signer_confirmed` resolves exactly to one retained candidate.
- `fingerspelled` has a non-null resolution that need not be retained as a candidate.
- `unresolved` has a null resolution.
- Raw input larger than 32,768 UTF-8 bytes is rejected before JSON parsing.

## 4. Session and transport names

CTR is independent of the transport URL. These names are the implementation's negotiation layer.

### 4.1 `SessionCreateRequest`

| JSON path | Type/default | Meaning |
| :-- | :-- | :-- |
| `language` | `sgsl` or `asl`; required | Session language |
| `schema_version` | literal `1.0`; default | Session request version |
| `stream_kind` | `landmarks` or `gloss_lattice`; default `landmarks` | Selects the input boundary |
| `client` | object; required | Frontend application descriptor |
| `client.platform` | `android`, `ios`, or `test` | Client platform |
| `client.app_version` | string, length 1–64 | Client release |
| `client.device_model` | string or null | Device description |
| `detector` | object; required | Frontend detector descriptor |
| `detector.name` | string, length 1–128 | Detector name |
| `detector.version` | string, length 1–64 | Detector version |
| `detector.delegate` | `cpu`, `gpu`, `nnapi`, `core_ml`, `unknown` | Execution delegate |
| `producer` | CTR producer or null | Required when `stream_kind=gloss_lattice` |

The request `producer` and every later lattice `producer` must match exactly.

### 4.2 `SessionCreateResponse`

| JSON property | Meaning |
| :-- | :-- |
| `session_id` | Generated session UUID |
| `stream_token` | Short-lived bearer credential |
| `token_type` | Literal `Bearer` |
| `stream_kind` | Selected input mode |
| `websocket_path` | Mode-selected path |
| `lattice_websocket_path` | Lattice path or null |
| `created_at`, `expires_at` | Timezone-aware server datetimes |
| `lattice_schema_version` | Literal `1.0` |
| `max_lattice_message_bytes` | Frozen v1 ceiling: exactly 32,768 |
| `max_lattice_slots` | 64 |
| `max_candidates_per_slot` | 5 |
| `layout`, `max_batch_frames`, `target_fps` | Legacy landmark compatibility values, not lattice fields |

### 4.3 Routes and control

| Name | Direction | Purpose |
| :-- | :-- | :-- |
| `POST /v1/sessions` | frontend → backend | Create session/token |
| `/v1/sessions/{session_id}/lattices` | bidirectional WebSocket | Lattice stream |
| `Authorization: Bearer <stream_token>` | frontend → backend | Authenticate stream |
| `DELETE /v1/sessions/{session_id}` | frontend → backend | End session |
| `type=control` | frontend → backend | Control discriminator |
| `control_seq` | frontend → backend | Increasing control counter |
| `action=ping|end` | frontend → backend | Allowed lattice controls |
| `client_ms` | frontend → backend | Optional client control timestamp |

## 5. Deliberately aligned backend-to-frontend names

These events are not defined by CTR, but their gloss vocabulary follows CTR so frontend code does
not need a second set of synonyms. Lattice ACK and terminal events intentionally omit `revision`.

### 5.1 Event envelopes

| Event `type` | Core properties |
| :-- | :-- |
| `activity` | `state`, `score`, `utterance_id`, `capture_ms` |
| `pong` | `control_seq`, `server_ms` |
| `error` | `code`, `message`, `retryable`, legacy `batch_seq` |
| `lattice_ack` | `lattice_seq`, `utterance_id`, `disposition`, `server_ms` |
| `lattice_result` | fields in section 5.3 |
| `lattice_repair_required` | fields in section 5.4 |

ACK `disposition` is `accepted` for new work and `cached` for an exact replay.

### 5.2 Evidence and choices

| Object | Exact JSON properties |
| :-- | :-- |
| `LatticeEvidenceTrace` | `slot_id`, `start_ms`, `end_ms`, `resolved_gloss_id`, `confidence`, `provenance`, `candidates` |
| `LatticeChoice` | `slot_id`, `rank`, `gloss_id`, `confidence` |

`LatticeEvidenceTrace.candidates` reuses the CTR `GlossCandidate` shape and therefore contains
`gloss_id`, `rank`, and `confidence`.

### 5.3 `lattice_result`

| JSON property | Meaning |
| :-- | :-- |
| `type` | Literal `lattice_result` |
| `lattice_seq` | Input correlation |
| `utterance_id` | Input correlation |
| `status` | Literal `confident` |
| `caption` | Supported user-visible text |
| `tts_text` | Text-to-speech text or null |
| `confidence` | Minimum/assembly evidence confidence |
| `gloss_id_trace` | Ordered gloss IDs used for assembly |
| `evidence_trace` | Per-slot evidence and provenance |
| `classifier_version` | Echo of `producer.classifier_version` |
| `agent_source` | Assembler identity such as `exact_template` or `bedrock_converse` |
| `latency_ms` | Non-negative stage timing map |

### 5.4 `lattice_repair_required`

| JSON property | Meaning |
| :-- | :-- |
| `type` | Literal `lattice_repair_required` |
| `lattice_seq`, `utterance_id` | Input correlation |
| `status` | Literal `uncertain` |
| `action` | Repair action from section 6 |
| `message` | Human-facing guidance |
| `confidence` | Confidence available at refusal |
| `target_slot_ids` | Slots to repair |
| `choices` | Slot-scoped `LatticeChoice` objects |
| `reason_codes` | Machine-readable refusal reasons |
| `evidence_trace` | Complete per-slot trace |
| `classifier_version` | Echo of `producer.classifier_version` |
| `agent_source` | Assembler identity or null |
| `latency_ms` | Non-negative stage timing map |

## 6. Literal and enum registry

| Domain | Values |
| :-- | :-- |
| Input `type` | `gloss_lattice` |
| `schema_version` | `1.0` |
| `timebase` | `session_monotonic_ms` |
| `confidence_kind` | `calibrated_probability` |
| `language` | `sgsl`, `asl` |
| `provenance` | `classifier_high_confidence`, `top_k_signer_confirmed`, `fingerspelled`, `unresolved` |
| Lattice control `action` | `ping`, `end` |
| `activity.state` | `idle`, `signing`, `processing` |
| ACK `disposition` | `accepted`, `cached` |
| Result `status` | `confident` |
| Repair `status` | `uncertain` |
| Repair `action` | `repeat`, `fingerspell`, `choose_candidate`, `reposition`, `reconnect`, `model_unavailable`, `escalate` |
| `error.code` | `invalid_message`, `unauthorized`, `session_not_found`, `session_expired`, `invalid_session_state`, `non_monotonic_sequence`, `batch_too_large`, `rate_limited`, `internal_error` |

## 7. Migration crosswalk

Old v1-shaped payloads are not accepted as aliases. Producers must send only the new CTR column.

| Previous implementation name | CTR/current name | Migration action |
| :-- | :-- | :-- |
| `capture_start_ms` | `started_at_ms` | Rename and use session monotonic time |
| `capture_end_ms` | `ended_at_ms` | Rename and use session monotonic time |
| absent | `timebase` | Add required literal `session_monotonic_ms` |
| `producer.classifier.name` | `producer.classifier_id` | Rename and flatten |
| `producer.classifier.model_version` | `producer.classifier_version` | Rename and flatten |
| `producer.classifier.calibration_version` | `producer.calibration_version` | Flatten |
| `producer.classifier.vocabulary_version` | `producer.vocabulary_version` | Flatten |
| absent | `producer.confidence_kind` | Add required literal `calibrated_probability` |
| array position only | `slots[].slot_index` | Add explicit contiguous index |
| `slots[].candidates[].gloss` | `slots[].candidates[].gloss_id` | Rename; enforce Identifier syntax |
| `slots[].resolved_gloss` | `slots[].resolved_gloss_id` | Rename; enforce Identifier syntax |
| `classifier_model_version` in lattice output | `classifier_version` | Rename |
| `gloss_trace` in lattice output | `gloss_id_trace` | Rename |
| `choices[].gloss` | `choices[].gloss_id` | Rename |

Remove these properties from CTR v1 input; do not send them as `null`:

- envelope: `revision`, `subject_id`, `is_final`, `produced_ms`, `quality`;
- producer: nested `classifier`, `segmenter_version`, `top_k`; and
- slot: `selected_rank`, `confirmed_at_ms`, `reason_codes`.

`GlossLatticeQuality`, `ReasonCode`, `ClassifierDescriptor`, and `GlossLatticeSlot` are no longer
public CTR model names. The corresponding current model names are `GlossLatticeProducer` and
`GlossSlot`.

## 8. Backend Agent names

These are backend implementation names, not frontend `GlossLattice` properties.

| Python object | Relevant fields or mapping |
| :-- | :-- |
| `GlossAlternativeEvidence` | `rank`, `gloss_id`, `confidence` |
| `GlossEvidence` | `evidence_id`, `gloss_id`, `confidence`, `provenance`, `slot_id`, `start_ms`, `end_ms`, `candidates` |
| `AssemblyRequest` | `utterance_id`, `language`, `evidence`, trusted `signer_id`, `lattice_seq`, `classifier_version`, `calibration_version`, `vocabulary_version`, `lattice` |
| `AssemblyResult` | `utterance_id`, `status`, `caption`, `tts_text`, internal `gloss_trace`, `confidence`, `source`, `repair_action`, `reason_codes`, internal `revision_count` |
| Bedrock assembler output | `caption`, `tts_text`, `used_evidence_ids`, `used_gloss_ids` |
| Bedrock critic output | `supported`, `reason` |

`signer_id` is trusted backend context and must never be copied from an input lattice. Internal
`revision_count` counts bounded Agent draft attempts; it is unrelated to frontend transport and is
never a lattice/output `revision` property. Authentication middleware may bind a verified
`request.state.signer_id` to the server-side session; without that integration the anonymous MVP
supplies `signer_id=None`. Never obtain it from a lattice field.

## 9. Relevant configuration names

| Python setting | Environment variable |
| :-- | :-- |
| `allowed_origins` | `SIMPLYNEXT_ALLOWED_ORIGINS` |
| `session_ttl_seconds` | `SIMPLYNEXT_SESSION_TTL_SECONDS` |
| `websocket_max_message_bytes` | `SIMPLYNEXT_WEBSOCKET_MAX_MESSAGE_BYTES` |
| `gloss_lattice_max_message_bytes` | `SIMPLYNEXT_GLOSS_LATTICE_MAX_MESSAGE_BYTES` |
| `max_lattices_per_session` | `SIMPLYNEXT_MAX_LATTICES_PER_SESSION` |
| `max_lattices_per_minute` | `SIMPLYNEXT_MAX_LATTICES_PER_MINUTE` |
| `max_lattices_per_minute_global` | `SIMPLYNEXT_MAX_LATTICES_PER_MINUTE_GLOBAL` |
| `max_concurrent_agent_runs` | `SIMPLYNEXT_MAX_CONCURRENT_AGENT_RUNS` |
| `agent_queue_timeout_seconds` | `SIMPLYNEXT_AGENT_QUEUE_TIMEOUT_SECONDS` |
| `lattice_websocket_idle_timeout_seconds` | `SIMPLYNEXT_LATTICE_WEBSOCKET_IDLE_TIMEOUT_SECONDS` |
| `caption_templates_path` | `SIMPLYNEXT_CAPTION_TEMPLATES_PATH` |
| `recognition_language` | `SIMPLYNEXT_RECOGNITION_LANGUAGE` |
| `min_recognition_confidence` | `SIMPLYNEXT_MIN_RECOGNITION_CONFIDENCE` |
| `min_recognition_margin` | `SIMPLYNEXT_MIN_RECOGNITION_MARGIN` |
| `bedrock_enabled` | `SIMPLYNEXT_BEDROCK_ENABLED` |
| `bedrock_model_id` | `SIMPLYNEXT_BEDROCK_MODEL_ID` |
| `aws_region` | `SIMPLYNEXT_AWS_REGION` |
| `agent_max_revisions` | `SIMPLYNEXT_AGENT_MAX_REVISIONS` |

The only valid v1 value for `gloss_lattice_max_message_bytes` is 32,768. A different transport
ceiling requires a new schema version instead of a deployment-specific v1 dialect.
AWS credentials use the standard AWS credential provider chain and are never schema fields.

## 10. Metrics names

| Kind | Exact names |
| :-- | :-- |
| Connections | `lattice_websocket_connections`, `lattice_websocket_disconnects`, `lattice_websocket_idle_timeouts`, `lattice_websocket_internal_errors` |
| Input validation | `invalid_lattice_messages`, `oversized_lattice_messages`, `gloss_lattices_accepted`, `gloss_lattice_bytes`, `gloss_lattice_slots` |
| Agent/replay | `lattice_agent_queue_rejections`, `lattice_agent_failures`, `lattice_cached_replays`, `lattice_utterances_confident`, `lattice_utterances_repair_required` |
| Dynamic counters | `lattice_provenance_<provenance>`, `lattice_repair_<action>` |
| Timings | `lattice_validation`, `lattice_agent_queue`, `lattice_time_to_ack`, `lattice_utterance_total` |

## 11. Idempotency and ownership vocabulary

- `session_id` identifies the authenticated session; it is not a credential.
- `lattice_seq` identifies one immutable session message. New values strictly increase; gaps are
  valid.
- `(session_id, lattice_seq)` is the replay/conflict key. Identical validated content returns the
  cached event; different content conflicts.
- `utterance_id` identifies the logical utterance and remains stable for a later backend-approved
  repair.
- CTR has no input or output `revision` property.
- `slot_id` identifies evidence within an utterance; `slot_index` records its array position.
- `signer_id` belongs only to trusted backend session/auth context.

## 12. Source map

| Concern | Source |
| :-- | :-- |
| Authoritative input prose | `CTR_contracts.md` |
| Executable input model and invariants | `src/simplynext/contracts/gloss_lattice.py` |
| Public exports | `src/simplynext/contracts/__init__.py` |
| Session/control contracts | `src/simplynext/contracts/sessions.py` |
| Output contracts | `src/simplynext/contracts/events.py` |
| Trusted signer-context handoff | `src/simplynext/api/routes.py`, `src/simplynext/sessions/store.py` |
| Authentication and WebSocket event order | `src/simplynext/api/lattice_websocket.py` |
| Sequence/idempotency state | `src/simplynext/sessions/store.py` |
| Agent mapping and policy | `src/simplynext/orchestrator.py` |
| Internal assembly names | `src/simplynext/agent/assembler.py` |
| Bedrock prompt boundary | `src/simplynext/agent/bedrock.py` |
| Golden fixture | `tests/fixtures/gloss_lattice_v1.json` |
| Executable acceptance checks | `tests/test_gloss_lattice_contract.py` |

Generate language-specific DTOs or JSON Schema from `GlossLattice.model_json_schema()`, but retain
the cross-field rules from CTR in frontend validation and shared tests because JSON Schema alone
does not express every provenance, ordering, and idempotency invariant.
