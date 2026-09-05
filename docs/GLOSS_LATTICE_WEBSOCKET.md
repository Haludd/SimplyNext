# GlossLattice WebSocket v1

This guide explains how a frontend sends classifier output to the SimplyNext Agent backend. It is
an integration walkthrough, not a second contract definition. [`CTR_contracts.md`](../CTR_contracts.md)
is the single source of truth for the version 1.0 `GlossLattice` input. If this guide and CTR ever
disagree, CTR wins.

The frontend owns camera capture, subject tracking, MediaPipe, normalization, segmentation and
closed-vocabulary classification. The backend receives only compact symbolic evidence, validates
it, runs the bounded Agent/critic workflow and returns either a supported caption or an explicit
repair request.

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
  "producer": {
    "classifier_id": "simplynext_temporal",
    "classifier_version": "asl_demo_v3",
    "confidence_kind": "calibrated_probability",
    "calibration_version": "temperature_v2",
    "vocabulary_version": "demo_v1"
  }
}
```

`producer` is required for a `gloss_lattice` session and uses the same five fields as the CTR
lattice producer. The lattice sent later must repeat that exact producer profile. The identifiers
provide reproducibility and prevent an accidental mid-session model switch; they are not remote
attestation that an untrusted client really ran the named artifacts.

The response contains a `stream_token`, the mode-selected `websocket_path`, and the negotiated
limits. In lattice mode the path is `/v1/sessions/{session_id}/lattices`,
`max_lattice_message_bytes` is exactly 32,768 for v1, `max_lattice_slots` is 64, and
`max_candidates_per_slot` is 5.

Open the returned path with:

```text
Authorization: Bearer <stream_token>
```

The server stores only a SHA-256 digest of the token, and the token expires with its ephemeral
session. Native Flutter clients can set the header. Standard browser WebSocket APIs cannot set an
arbitrary `Authorization` header, so a browser deployment needs a short-lived WebSocket ticket or
an equivalent secure handshake. Never put the bearer token in a URL query string. If a browser
sends `Origin`, it must match `SIMPLYNEXT_ALLOWED_ORIGINS`; native clients may omit it.

## 2. Send one committed lattice

One WebSocket text frame contains one UTF-8 JSON object. This valid example uses two of the four
provenance states; the golden fixture in
[`tests/fixtures/gloss_lattice_v1.json`](../tests/fixtures/gloss_lattice_v1.json) contains all four.

```json
{
  "type": "gloss_lattice",
  "schema_version": "1.0",
  "session_id": "3dd5e15d-991a-4c27-9a11-af4a1a3bb2e8",
  "lattice_seq": 7,
  "utterance_id": "utt-019",
  "language": "asl",
  "timebase": "session_monotonic_ms",
  "started_at_ms": 1000,
  "ended_at_ms": 1920,
  "producer": {
    "classifier_id": "simplynext_temporal",
    "classifier_version": "asl_demo_v3",
    "confidence_kind": "calibrated_probability",
    "calibration_version": "temperature_v2",
    "vocabulary_version": "demo_v1"
  },
  "slots": [
    {
      "slot_index": 0,
      "slot_id": "s0",
      "start_ms": 1000,
      "end_ms": 1380,
      "candidates": [
        {"gloss_id": "HELLO", "rank": 1, "confidence": 0.94},
        {"gloss_id": "WELCOME", "rank": 2, "confidence": 0.04}
      ],
      "resolved_gloss_id": "HELLO",
      "provenance": "classifier_high_confidence"
    },
    {
      "slot_index": 1,
      "slot_id": "s1",
      "start_ms": 1450,
      "end_ms": 1920,
      "candidates": [
        {"gloss_id": "WATER", "rank": 1, "confidence": 0.54},
        {"gloss_id": "DRINK", "rank": 2, "confidence": 0.49}
      ],
      "resolved_gloss_id": null,
      "provenance": "unresolved"
    }
  ]
}
```

Every CTR envelope property is required, including `type`, `schema_version`, `timebase`, and a
nullable `resolved_gloss_id`. Do not omit a required property merely because its only valid value
is a literal or `null`.

### Time semantics

`started_at_ms`, `ended_at_ms`, `start_ms`, and `end_ms` are elapsed monotonic milliseconds from
the capture-clock origin established for the session. They are not Unix timestamps and must not be
created with `Date.now()`. Intervals are half-open: the start is included and the end is excluded.
Every slot must lie inside the utterance interval.

### Slot and candidate semantics

- `slots` contains 1–64 entries. `slot_index` starts at zero, is contiguous, and equals array order.
- Slot IDs are unique. Slots are chronological and may have gaps, but they must not overlap.
- `candidates` is required and contains 0–5 entries.
- Candidate ranks start at one, are contiguous, and equal array order.
- Candidate confidence is a finite calibrated probability from 0.0 through 1.0. Values are
  non-increasing and need not sum to one.
- Candidate `gloss_id` values are unique within a slot. They are opaque, case-sensitive lexicon
  keys—not display text or natural-language instructions.
- Identifiers are 1–128 ASCII characters, begin with a letter or digit, and thereafter use only
  letters, digits, `_`, `.`, `:`, or `-`.

Every slot has exactly one provenance value:

- `classifier_high_confidence`: at least one candidate is present and `resolved_gloss_id` equals
  the rank-1 candidate.
- `top_k_signer_confirmed`: `resolved_gloss_id` exactly equals one retained candidate.
- `fingerspelled`: `resolved_gloss_id` is present but need not occur in `candidates`.
- `unresolved`: `resolved_gloss_id` is `null`; low-confidence choices may remain in `candidates`.

The receiver rejects unknown properties at every level, numeric strings or booleans used as
numbers, non-finite confidence, invalid identifier whitespace, overlapping slots, and unsupported
schema versions. It also rejects media, landmarks, coordinates, feature arrays, embeddings,
prompts, signer identity, memory, and Agent-loop state because none is a CTR field.

Legacy fields such as `revision`, `subject_id`, `is_final`, `capture_start_ms`, `capture_end_ms`,
`produced_ms`, `quality`, `selected_rank`, `confirmed_at_ms`, and slot `reason_codes` are not aliases;
their presence makes a v1 lattice invalid.

## 3. Response sequence

After connection, the server sends `activity` with `state: "idle"`. A new valid lattice then
produces:

```text
lattice_ack(disposition=accepted)
activity(state=processing)
lattice_result | lattice_repair_required
activity(state=idle)
```

The response event contract is backend-owned rather than part of CTR. Its gloss-related names are
deliberately aligned with CTR: `gloss_id`, `resolved_gloss_id`, `gloss_id_trace`, and
`classifier_version`. Lattice output events do not contain a `revision` field.

A successful result has this shape:

```json
{
  "type": "lattice_result",
  "lattice_seq": 7,
  "utterance_id": "utt-019",
  "status": "confident",
  "caption": "Hello",
  "tts_text": "Hello",
  "confidence": 0.94,
  "gloss_id_trace": ["HELLO"],
  "evidence_trace": [
    {
      "slot_id": "s0",
      "start_ms": 1000,
      "end_ms": 1380,
      "resolved_gloss_id": "HELLO",
      "confidence": 0.94,
      "provenance": "classifier_high_confidence",
      "candidates": [
        {"gloss_id": "HELLO", "rank": 1, "confidence": 0.94},
        {"gloss_id": "WELCOME", "rank": 2, "confidence": 0.04}
      ]
    }
  ],
  "classifier_version": "asl_demo_v3",
  "agent_source": "exact_template",
  "latency_ms": {"assemble": 1, "total": 2}
}
```

`lattice_repair_required` never contains caption or TTS text. It includes an `action`, a safe
human-facing `message`, machine-readable `reason_codes`, `target_slot_ids`, and, for
`choose_candidate`, slot-scoped `choices`. Each choice uses `slot_id`, `rank`, `gloss_id`, and
`confidence`. Both terminal event kinds include the complete `evidence_trace` and
`classifier_version`.

## 4. Sequencing, retries, and later repairs

For a new message, `lattice_seq` must be strictly greater than every previously accepted sequence
in the session; gaps are valid. The immutable idempotency identity is
`(session_id, lattice_seq)`.

An exact semantic retransmission of an accepted pair returns
`lattice_ack(disposition=cached)` and the cached terminal event. It does not start the Agent again
or consume another new-lattice quota. Reusing the pair with different validated content is a
protocol error.

`utterance_id` is the stable identity of the logical utterance. CTR v1 intentionally has no
`revision` property. A frontend repair therefore uses the same `utterance_id` and a new, greater
`lattice_seq`; whether that later representation is accepted is backend policy. Do not add a local
revision counter to the v1 JSON.

## 5. Controls and failure behavior

The lattice socket accepts `control` messages with only `ping` or `end`. It does not accept
`commit`, because every lattice message is already a committed utterance.

- Three consecutive invalid schema/control/profile messages close the socket with `1008`.
- A raw text message over 32,768 UTF-8 bytes is rejected before JSON parsing and closes with `1009`.
- Authentication/session close codes are `4401` (invalid token or mismatch), `4404` (missing
  session), `4408` (expired), and `4409` (wrong mode or competing stream).
- A socket idle timeout closes with `1001`.
- Rate and Agent-capacity limits fail without silently producing a caption.

Unresolved evidence, duration/confidence failures, Agent exceptions, and critic rejection fail
closed as repair events. Once a new lattice is acknowledged, the backend finalizes a terminal
event in its replay cache even if delivery is interrupted. Reconnect with the same session/token
and retransmit the exact lattice to recover that result.

## 6. Trust and deployment scope

The payload `session_id` must equal the authenticated WebSocket route and token session. A valid
UUID in JSON does not grant access. CTR requires signer identity to come from trusted backend
session/auth context and never from the lattice payload. Server authentication middleware may set
the verified `request.state.signer_id` while creating a session; the backend stores it separately
and passes it to the Agent. Without that middleware this MVP creates an anonymous bearer session
and deliberately passes `signer_id=None`. Enable per-signer memory only when that verified binding
exists; do not fill the gap by adding a client-controlled signer field to `GlossLattice`.

The frontend must establish one monotonic capture-clock origin when it creates the session and use
that origin for every CTR timestamp. The server validates interval order and bounds, but an
anonymous remote server cannot independently attest which client clock produced those values.

Classifier metadata is reproducibility lineage, not proof. Before accepting untrusted session
creation, use a server-owned allow-list of approved classifier, calibration, and vocabulary
versions.

The session store, replay cache, rate counters and Agent semaphore are process-local. This MVP runs
with one application worker. Horizontal deployment requires a shared atomic store/queue such as
DynamoDB or Redis; sticky routing alone does not provide global idempotency or spend limits.

Bedrock uses bounded connect/read timeouts and SDK retries. Its internal assembler/critic revision
loop is separate from the CTR wire contract and never adds a `revision` property to a lattice. The
MVP has no process-level kill mechanism for a locally hung assembler thread; production isolation
should run Agent work in a cancellable worker with a hard execution deadline.
