**GLOSS LATTICE CONTRACT**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field                   | Value                                               |
| :---------------------- | :-------------------------------------------------- |
| **Code**                | `CTR`                                               |
| **Status**              | Frozen                                              |
| **Last reviewed**       | 2026-09-06                                          |
| **Source of truth for** | The version 1.0 `GlossLattice` wire contract        |
| **Parent**              | [`ARC`](ARC_architecture.md) · [`PLN`](PLN_plan.md) |
| **Related**             | [`BCT`](../doc/BCT_backend_comparison_test.md)      |

**For the team.** This document freezes the payload emitted by recognition stage ⑤ and consumed by
backend agent stage ⑥. Frontend and backend implementations may proceed independently when both
validate against this contract and the shared fixture.

**For the assistant.** Existing version 1.0 field names, types, enum values, limits, and semantics
must not be changed in place. Any incompatible change requires a new schema version, migration
notes, a new fixture, and coordinated frontend/backend tests.

</details>

---





# 1. AUTHORITY
## 1.1. Boundary
`GlossLattice` is the complete recognition payload that crosses from stage ⑤ to stage ⑥. It
carries ordered sign slots, each slot's retained top-k closed-vocabulary hypotheses, calibrated
confidence, session-relative timestamps, and the provenance rung required by
[`ARC_S5.7`](ARC_architecture.md#57-the-reverse-direction) decision 19. It implements the fourth
frozen interface in [`PLN_S3.4`](PLN_plan.md#34-the-frozen-interfaces) and unblocks typed graph
state in [`PLN_S9.1`](PLN_plan.md#91-t51--typed-graph-state).

The contract is independent of a WebSocket URL. One UTF-8 WebSocket text message contains one JSON
object conforming to this document. The authenticated route binds the message to a server session;
the payload does not replace authentication or session authorization.




## 1.2. Exclusions
The payload contains no camera frames, images, landmarks, feature windows, tensors, embeddings,
base64 data, prompts, conversation history, signer memory, or model drafts. This is the compact
boundary required by [`PLN_S8.4`](PLN_plan.md#84-t44--the-lattice-with-provenance) and the missing
boundary identified by [`BCT_S4.5`](../doc/BCT_backend_comparison_test.md#45-wp4--recognition).

Signer identity is resolved from trusted backend session/authentication context. It is not
accepted as a `GlossLattice` field. Conversation history, per-signer memory, loop counters, drafts,
critiques, routes, and final results are backend-owned graph state defined by
[`PLN_S9.1`](PLN_plan.md#91-t51--typed-graph-state).

---





# 2. WIRE OBJECT
## 2.1. Encoding and Limits
The sender emits compact JSON in a single UTF-8 WebSocket text message. The receiver rejects a raw
message larger than **32,768 bytes before JSON parsing**, then validates the decoded object. The
canonical Python serialization is `GlossLattice.model_dump_json()`.

Version 1.0 applies these fixed limits:

| Item                   | Limit   |
| :--------------------- | :------ |
| Slots per lattice      | 1–64    |
| Candidates per slot    | 0–5     |
| Identifier length      | 1–128   |
| Compact payload size   | 32 KiB  |
| Confidence             | 0.0–1.0 |
| Millisecond integers   | 0–2⁵³−1 |

An identifier begins with an ASCII letter or digit and thereafter contains only ASCII letters,
digits, `_`, `.`, `:`, or `-`. Identifiers are opaque and case-sensitive. A gloss identifier is a
closed-vocabulary lexicon key, not display text and not a natural-language instruction.




## 2.2. Envelope Fields
1. **`type`** · *Type:* string literal · *Required:* yes · *Value:* `gloss_lattice`
   *Meaning:* WebSocket union discriminator.
2. **`schema_version`** · *Type:* string literal · *Required:* yes · *Value:* `1.0`
   *Meaning:* Exact wire-schema version. No other value is accepted by the v1 model.
3. **`session_id`** · *Type:* UUID string · *Required:* yes
   *Meaning:* Session correlation value. It must equal the authenticated route/session value.
4. **`lattice_seq`** · *Type:* integer · *Required:* yes · *Range:* 0–2⁵³−1
   *Meaning:* Monotonically increasing lattice-message sequence within one session.
5. **`utterance_id`** · *Type:* identifier · *Required:* yes
   *Meaning:* Stable identity of the logical signed utterance.
6. **`language`** · *Type:* enum · *Required:* yes · *Values:* `sgsl`, `asl`
   *Meaning:* Sign-language vocabulary used by the producer.
7. **`timebase`** · *Type:* string literal · *Required:* yes
   *Value:* `session_monotonic_ms`
   *Meaning:* Every timestamp is elapsed monotonic milliseconds from the capture clock origin
   established for the session. Values are neither Unix time nor wall-clock time.
8. **`started_at_ms`** · *Type:* integer · *Required:* yes · *Range:* 0–2⁵³−1
   *Meaning:* Inclusive utterance start on the session timebase.
9. **`ended_at_ms`** · *Type:* integer · *Required:* yes · *Range:* 0–2⁵³−1
   *Meaning:* Exclusive utterance end on the session timebase; greater than `started_at_ms`.
10. **`producer`** · *Type:* `GlossLatticeProducer` · *Required:* yes
    *Meaning:* Reproducibility metadata for the recognizer, calibration, and vocabulary.
11. **`slots`** · *Type:* ordered array of `GlossSlot` · *Required:* yes
    *Meaning:* One to sixty-four chronological, non-overlapping sign positions.




## 2.3. Producer Fields
1. **`classifier_id`** · *Type:* identifier · *Required:* yes
   *Meaning:* Stable classifier family or artifact identity.
2. **`classifier_version`** · *Type:* identifier · *Required:* yes
   *Meaning:* Exact classifier artifact version.
3. **`confidence_kind`** · *Type:* string literal · *Required:* yes
   *Value:* `calibrated_probability`
   *Meaning:* Declares that candidate confidence is calibrated probability, never raw softmax,
   distance, margin, logit, or an uncalibrated model score.
4. **`calibration_version`** · *Type:* identifier · *Required:* yes
   *Meaning:* Exact calibration artifact or procedure version used for every confidence value.
5. **`vocabulary_version`** · *Type:* identifier · *Required:* yes
   *Meaning:* Exact closed-vocabulary version against which every `gloss_id` resolves.




## 2.4. Slot Fields
1. **`slot_index`** · *Type:* integer · *Required:* yes · *Range:* 0–63
   *Meaning:* Zero-based position. Values are contiguous and match array order.
2. **`slot_id`** · *Type:* identifier · *Required:* yes
   *Meaning:* Stable slot identity, unique within the utterance.
3. **`start_ms`** · *Type:* integer · *Required:* yes
   *Meaning:* Inclusive slot start on the envelope's timebase.
4. **`end_ms`** · *Type:* integer · *Required:* yes
   *Meaning:* Exclusive slot end; greater than `start_ms`.
5. **`candidates`** · *Type:* ordered array of `GlossCandidate` · *Required:* yes
   *Meaning:* Zero to five retained classifier hypotheses. Empty is valid for an unresolved or
   fingerspelled slot.
6. **`resolved_gloss_id`** · *Type:* identifier or `null` · *Required:* yes
   *Meaning:* Selected gloss after applying the provenance rules in [`CTR_S3.2`](#32-resolution).
7. **`provenance`** · *Type:* `GlossProvenance` · *Required:* yes
   *Meaning:* How `resolved_gloss_id` was obtained, or why it is absent.




## 2.5. Candidate Fields
1. **`gloss_id`** · *Type:* identifier · *Required:* yes
   *Meaning:* Opaque, case-sensitive key in `producer.vocabulary_version`.
2. **`rank`** · *Type:* integer · *Required:* yes · *Range:* 1–5
   *Meaning:* One-based hypothesis rank. Ranks are contiguous and match array order.
3. **`confidence`** · *Type:* finite number · *Required:* yes · *Range:* 0.0–1.0
   *Meaning:* Calibrated confidence produced by `producer.calibration_version`.

Candidate confidence values are non-increasing in array order. Candidate gloss identifiers are
unique within a slot. The values are not required to sum to one because retained top-k entries may
exclude probability mass. Every value is a calibrated probability produced by the declared
`calibration_version`; raw softmax, distance, margin, logit, or another uncalibrated score is a
contract violation. The contract does not set a high-confidence threshold; stage ⑤ applies the
threshold derived by [`PLN_S8.3`](PLN_plan.md#83-t43--confidence-calibration).

---





# 3. INVARIANTS
## 3.1. Time and Order
Every slot uses the envelope's `session_monotonic_ms` clock and represents the half-open interval
`[start_ms, end_ms)`. All slot intervals lie inside `[started_at_ms, ended_at_ms)`. Slot indices are
contiguous from zero, slot identifiers are unique, and adjacent slot intervals never overlap. Gaps
between slots are valid.




## 3.2. Resolution
The four wire values are fixed:

1. **`classifier_high_confidence`**
   `candidates` contains at least one entry and `resolved_gloss_id` equals the rank-1 candidate.
   The producer asserts that its separately calibrated acceptance policy cleared the slot.
2. **`top_k_signer_confirmed`**
   `resolved_gloss_id` equals one retained candidate. The signer-confirmation interaction, not the
   classifier score, authorizes that selection.
3. **`fingerspelled`**
   `resolved_gloss_id` contains the canonical lexicon/fingerspelling key. Retained classifier
   candidates may be empty or preserved for audit, and the resolved key need not be among them.
4. **`unresolved`**
   `resolved_gloss_id` is `null`. Low-confidence candidates may be retained so stage ⑨ can offer
   top-k repair without treating one as signed intent.

Every slot carries exactly one provenance value. A non-`unresolved` slot carries a non-null
`resolved_gloss_id`; an `unresolved` slot cannot carry one. These constraints prevent a low-score
hypothesis from silently becoming a signer's asserted words.




## 3.3. Strictness
Unknown fields are rejected at every object level. Models are immutable after validation. NaN,
positive infinity, and negative infinity are invalid confidence values. Numeric strings and JSON
booleans are not coerced into integer or confidence fields, and surrounding identifier whitespace
is rejected rather than trimmed. The same `(session_id, lattice_seq)` pair identifies one
immutable message; reuse with different content is a protocol error.

---





# 4. TRANSPORT
## 4.1. Session Binding
The backend validates `session_id` against the authenticated WebSocket path and token before
constructing graph state. A valid UUID in the payload does not grant access. The backend also
derives signer identity from trusted session context and does not infer it from an utterance or
slot identifier.




## 4.2. Sequencing
`lattice_seq` increases within a session; gaps are permitted. An exact retransmission of an already
accepted `(session_id, lattice_seq)` message is idempotent and must not start a second graph run. A
different payload that reuses the pair is rejected. `utterance_id` remains stable if a later
message represents an explicitly accepted revision; revision acceptance is backend policy rather
than a v1 payload field.




## 4.3. Receiver Order
The receiver applies checks in this order:

1. Authorize the WebSocket session and enforce the raw 32 KiB message limit.
2. Decode exactly one JSON object and validate `GlossLattice` with unknown fields forbidden.
3. Require the payload `session_id` to equal the authenticated session.
4. Apply sequence/idempotency checks.
5. Construct typed graph state with trusted signer context held separately.

---





# 5. EXAMPLE
## 5.1. Complete Version 1.0 Message
This example deliberately contains all four provenance rungs. The checked-in machine-readable copy
is [`tests/fixtures/gloss_lattice_v1.json`](../tests/fixtures/gloss_lattice_v1.json).

```json
{
  "type": "gloss_lattice",
  "schema_version": "1.0",
  "session_id": "12345678-1234-5678-1234-567812345678",
  "lattice_seq": 7,
  "utterance_id": "utterance-42",
  "language": "sgsl",
  "timebase": "session_monotonic_ms",
  "started_at_ms": 1000,
  "ended_at_ms": 3000,
  "producer": {
    "classifier_id": "temporal_classifier",
    "classifier_version": "1.3.0",
    "confidence_kind": "calibrated_probability",
    "calibration_version": "temperature_v2",
    "vocabulary_version": "sgsl_demo_v1"
  },
  "slots": [
    {
      "slot_index": 0,
      "slot_id": "slot-0",
      "start_ms": 1000,
      "end_ms": 1300,
      "candidates": [
        {"gloss_id": "WATER", "rank": 1, "confidence": 0.96},
        {"gloss_id": "WHAT", "rank": 2, "confidence": 0.02}
      ],
      "resolved_gloss_id": "WATER",
      "provenance": "classifier_high_confidence"
    },
    {
      "slot_index": 1,
      "slot_id": "slot-1",
      "start_ms": 1350,
      "end_ms": 1700,
      "candidates": [
        {"gloss_id": "PLEASE", "rank": 1, "confidence": 0.57},
        {"gloss_id": "THANK_YOU", "rank": 2, "confidence": 0.31}
      ],
      "resolved_gloss_id": "THANK_YOU",
      "provenance": "top_k_signer_confirmed"
    },
    {
      "slot_index": 2,
      "slot_id": "slot-2",
      "start_ms": 1800,
      "end_ms": 2200,
      "candidates": [],
      "resolved_gloss_id": "J-O-H-N",
      "provenance": "fingerspelled"
    },
    {
      "slot_index": 3,
      "slot_id": "slot-3",
      "start_ms": 2300,
      "end_ms": 2600,
      "candidates": [
        {"gloss_id": "TOMORROW", "rank": 1, "confidence": 0.42},
        {"gloss_id": "YESTERDAY", "rank": 2, "confidence": 0.38}
      ],
      "resolved_gloss_id": null,
      "provenance": "unresolved"
    }
  ]
}
```

Whitespace is included for review only. Production transport uses the compact serialization.

---





# 6. IMPLEMENTATION
## 6.1. Python Model
The executable contract lives in
[`src/simplynext/contracts/gloss_lattice.py`](../src/simplynext/contracts/gloss_lattice.py) and is
re-exported from `simplynext.contracts`. Backend code imports `GlossLattice` from that public
package. Frontend developers may derive their language model from the output of
`GlossLattice.model_json_schema()` but preserve the cross-field invariants in
[`CTR_S3`](#3-invariants), which JSON Schema alone does not express fully.




## 6.2. Compatibility
Version 1.0 is exact and rejects additions. A field rename, type change, enum change, semantic
change, relaxed identifier syntax, altered timebase, or changed limit requires a new schema
version. A new version is added beside v1 rather than changing v1 behavior. Both frontend and
backend must accept the new golden fixture before transport switches to it.




## 6.3. Acceptance Checks
The automated contract checks cover JSON round-trip, the shared fixture, all provenance states,
candidate rank and confidence order, slot chronology, unknown-field rejection, version rejection,
landmark exclusion, and the compact byte ceiling. They live in
[`tests/test_gloss_lattice_contract.py`](../tests/test_gloss_lattice_contract.py).

---





# 7. SOURCES
1. **[`ARC_S5.7`](ARC_architecture.md#57-the-reverse-direction)**
   *Use:* Four-state forward provenance ladder and signer-confirmed top-k repair.
2. **[`ARC_S6.1`](ARC_architecture.md#61-pipeline)**
   *Use:* Stage ⑤ top-k calibrated classifier output and stage ⑥ lattice consumer boundary.
3. **[`PLN_S3.4`](PLN_plan.md#34-the-frozen-interfaces)**
   *Use:* Required `GlossLattice` contents, compact JSON rule, and exclusion of landmarks.
4. **[`PLN_S8.4`](PLN_plan.md#84-t44--the-lattice-with-provenance)**
   *Use:* Per-slot provenance requirement and per-token uncertainty measurement.
5. **[`PLN_S9.1`](PLN_plan.md#91-t51--typed-graph-state)**
   *Use:* Graph-state consumer and separation of lattice from backend-owned memory and loop state.
6. **[`BCT_S4.5`](../doc/BCT_backend_comparison_test.md#45-wp4--recognition)**
   *Use:* Verified gap: the earlier backend dropped timestamps, provenance, and all but top-1.

---





# 8. CHANGE LOG
1. **2026-09-06** · *Author:* Codex (GPT-5)
   *Change:* Created and froze `GlossLattice` version 1.0. Defined its envelope, producer metadata,
   slots, candidates, provenance semantics, timestamp clock, sequencing, exclusions, 32 KiB limit,
   golden fixture, executable Pydantic model, and acceptance checks.
