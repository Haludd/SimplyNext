# GlossLattice WebSocket v1

This is the frontend-to-backend contract for the architecture in which the frontend performs
camera capture through classification and the backend begins at the Agent loop. The schema is
implemented by `src/simplynext/contracts/lattices.py`; examples below are illustrative JSON, while
the Pydantic models are authoritative.

## 1. Create a lattice session

```http
POST /v1/sessions
Content-Type: application/json
```

```json
{
  "language": "asl",
  "schema_version": "1.0",
  "stream_kind": "gloss_lattice",
  "client": {
    "platform": "android",
    "app_version": "1.0.0",
    "device_model": "demo-phone"
  },
  "detector": {
    "name": "mediapipe-holistic",
    "version": "0.10.22",
    "delegate": "gpu"
  },
  "classifier": {
    "name": "simplynext-temporal",
    "model_version": "asl-demo-v3",
    "calibration_version": "temperature-v2",
    "vocabulary_version": "demo-v1"
  }
}
```

The response contains `stream_token`, the mode-selected `websocket_path`, and the negotiated
limits. For this mode the path is `/v1/sessions/{session_id}/lattices`. Open it with:

```text
Authorization: Bearer <stream_token>
```

The token is returned once, stored only as a SHA-256 digest on the server, and expires with the
ephemeral session. Native Flutter clients can set this header. Standard browser WebSocket APIs
cannot; a web deployment needs a short-lived WebSocket ticket or an equivalent secure handshake
before using this endpoint. Do not put the bearer token in a URL query string.
When a browser sends an `Origin` header, it must match `SIMPLYNEXT_ALLOWED_ORIGINS`; native clients
that do not send `Origin` remain supported.

## 2. Send one final lattice per utterance

```json
{
  "type": "gloss_lattice",
  "schema_version": "1.0",
  "session_id": "3dd5e15d-991a-4c27-9a11-af4a1a3bb2e8",
  "lattice_seq": 7,
  "utterance_id": "utt-019",
  "revision": 0,
  "language": "asl",
  "subject_id": "track-4",
  "is_final": true,
  "capture_start_ms": 1788600000100,
  "capture_end_ms": 1788600001920,
  "produced_ms": 1788600001970,
  "producer": {
    "classifier": {
      "name": "simplynext-temporal",
      "model_version": "asl-demo-v3",
      "calibration_version": "temperature-v2",
      "vocabulary_version": "demo-v1"
    },
    "segmenter_version": "geometry-v2",
    "top_k": 5
  },
  "quality": {
    "observed_frames": 46,
    "dropped_frames": 1,
    "landmark_coverage": 0.94,
    "classifier_latency_ms": 31
  },
  "slots": [
    {
      "slot_id": "s0",
      "start_ms": 1788600000100,
      "end_ms": 1788600000780,
      "candidates": [
        {"rank": 1, "gloss": "HELLO", "confidence": 0.94},
        {"rank": 2, "gloss": "WELCOME", "confidence": 0.04}
      ],
      "resolved_gloss": "HELLO",
      "selected_rank": 1,
      "provenance": "classifier_high_confidence",
      "confirmed_at_ms": null,
      "reason_codes": []
    },
    {
      "slot_id": "s1",
      "start_ms": 1788600000900,
      "end_ms": 1788600001920,
      "candidates": [
        {"rank": 1, "gloss": "WATER", "confidence": 0.54},
        {"rank": 2, "gloss": "DRINK", "confidence": 0.49}
      ],
      "resolved_gloss": null,
      "selected_rank": null,
      "provenance": "unresolved",
      "confirmed_at_ms": null,
      "reason_codes": ["ambiguous_top_k"]
    }
  ]
}
```

The profile under `producer.classifier` must exactly match session negotiation. These version
identifiers provide lineage and prevent a mid-session profile switch; they are not cryptographic
proof that a client model was calibrated. Production deployments should distribute an approved
classifier bundle and validate its identifiers as deployment configuration.

## 3. Slot rules

Every slot has exactly one of these provenance values:

- `classifier_high_confidence`: selects rank 1; the backend rechecks confidence and margin.
- `top_k_signer_confirmed`: selects one transmitted rank and requires `confirmed_at_ms`.
- `fingerspelled`: has standalone `resolved_gloss`, no selected classifier rank, and requires
  `confirmed_at_ms`.
- `unresolved`: has no resolution and at least one `reason_code`; it can retain top-k choices.

Candidate ranks start at 1, remain contiguous, have unique glosses, and are ordered by
non-increasing confidence. Slot times must lie inside the utterance capture interval. Slots are
ordered by `start_ms`; overlap is allowed so sliding-window classifiers are representable.

The v1 bounds are 32 slots, five candidates per slot, eight reason codes per slot and 64 KiB of
UTF-8 JSON per message. Sequence and millisecond integers stay within JavaScript's safe-integer
range. Unknown fields are rejected. Because there are no frame, landmark, image, coordinate or
tensor fields, such data fails schema validation rather than reaching the Agent.

## 4. Response sequence

A new valid lattice produces:

```text
activity(idle)
lattice_ack(disposition=accepted)
activity(processing)
lattice_result | lattice_repair_required
activity(idle)
```

`lattice_result` includes caption/TTS plus `evidence_trace`, containing every slot's selected gloss,
timestamps, full candidate list and provenance. `lattice_repair_required` never contains caption or
TTS; it includes target slot IDs and slot-scoped choices when the action is `choose_candidate`.

An exact semantic retry—same sequence, utterance revision and validated content—returns
`lattice_ack(disposition=cached)`, the cached terminal event, then idle. It never calls the Agent a
second time. Reusing an ID or sequence with changed content is rejected.

If repair succeeds on the frontend, send a new, strictly greater `lattice_seq`, retain the same
`utterance_id`, increment `revision` by exactly one, and update the repaired slot's provenance. A
revision is accepted only when the preceding revision ended in `lattice_repair_required`; a
confident result is terminal.

## 5. Controls and failure behavior

The lattice socket accepts only `control` messages with `ping` or `end`. It does not accept
`commit`: a lattice is already one committed utterance. The third malformed schema message closes
with `1008`; a message beyond the negotiated byte ceiling closes with `1009`. Authentication and
session close codes are `4401` (token/mismatch), `4404` (missing), `4408` (expired), and `4409`
(wrong mode or another active stream).

Incomplete lattices, unresolved slots, confidence/quality failures, Agent exceptions and critic
rejection all fail closed as repair events. The service limits new lattices per minute and per
session, applies a process-wide lattice rate ceiling, and bounds simultaneous Agent executions.
Waiting for an Agent slot has a deadline; a busy service returns a retryable `rate_limited` error
without consuming `lattice_seq`. An idle socket is closed with `1001`. Exact cached retries do not
consume lattice rate or session-quota capacity.

Once a new lattice is acknowledged, its terminal result is finalized in the idempotency cache even
if delivery is interrupted. HTTP deletion and TTL cleanup cannot erase a session during that Agent
run. If the client disconnects, reconnect with the same session/token and resend the exact lattice
to retrieve the cached result. HTTP deletion returns `409` while a WebSocket or Agent run owns the
session.

## 6. Deployment scope and trust boundary

The session store, replay cache, rate counters and Agent semaphore are process-local. Run this MVP
with one application worker, as the included CLI does. Horizontal deployment needs a shared atomic
store/queue (for example DynamoDB or Redis), sticky routing alone is not sufficient for global
exactly-once and spend limits.

Bedrock transport uses explicit connect/read timeouts and bounded standard retries configured by
`SIMPLYNEXT_BEDROCK_CONNECT_TIMEOUT_SECONDS`, `SIMPLYNEXT_BEDROCK_READ_TIMEOUT_SECONDS` and
`SIMPLYNEXT_BEDROCK_TOTAL_MAX_ATTEMPTS`. One Agent workflow may make several bounded Converse calls
because it includes assembly, critique and at most one revision. `/readyz` checks configuration; it
does not spend money on a live AWS preflight.

Classifier metadata is version lineage, not remote attestation. The current service verifies that
the lattice repeats the profile negotiated by the same client; it does not yet load a server-owned
classifier/vocabulary allow-list. Only issue session tokens to the trusted SimplyNext frontend, and
add that allow-list before exposing session creation to untrusted callers. The process-wide lattice
rate is an abuse/backpressure control, not a cumulative Bedrock currency budget.

The optional Bedrock critic is a bounded model-based check, not a formal proof that every caption
concept is grounded. The deterministic caption-template assembler is the stricter demo path. Before
using generated Bedrock captions in a production assistive setting, add a server-owned gloss lexicon
or alignment verifier and run adversarial grounding/refusal evaluations.
