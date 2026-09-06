**SIMPLYNEXT BACKEND**

SimplyNext is an uncertainty-aware translation backend for a client-side sign-recognition
pipeline. The client sends compact, versioned `GlossLattice` JSON. The backend returns exactly one
terminal outcome per accepted lattice: grounded caption/TTS text or a repair instruction. It does
not ingest raw camera frames, landmarks, or feature tensors.

# 1. CURRENT STATUS

The local backend vertical slice is implemented and tested:

- strict GlossLattice v1 contracts;
- ephemeral bearer-authenticated sessions;
- bounded WebSocket transport with acknowledgement, replay, rate limits, and controls;
- confidence and producer-profile policy gates;
- a bounded LangGraph assembler → critic → confident/repair flow;
- deterministic no-spend mode and optional guarded Amazon Bedrock Converse mode;
- payload-free structured logs and in-process metrics;
- unit, integration, and end-to-end protocol tests.

The repository is not yet a hosted production service. Live Bedrock verification, container
packaging, Railway controls, and real client integration remain. Follow
`plan/BPP_backend_production_plan.md` in that order.

# 2. WHY `src/simplynext/` IS INTENTIONAL

This project uses Python's standard `src` layout. `src/` prevents accidental imports from the
checkout; `simplynext/` is the stable package namespace. Flattening its children into `src/` would
create generic top-level packages such as `agent`, `api`, and `contracts`, weaken packaging
isolation, and require callers to abandon `simplynext.*` imports.

# 3. REQUIREMENTS

- Python 3.11–3.13; Python 3.12 is the tested deployment target.
- A virtual environment with `pip`.
- Optional: AWS credentials and Bedrock model access for live model mode.

# 4. INSTALLATION

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
cp .env.example .env
```

The committed `requirements.txt` delegates to `pyproject.toml`; `pylock.toml` is the resolved
dependency lock. Do not commit `.env` or AWS credentials.

# 5. LOCAL OPERATION

Deterministic mode requires an exact caption-template file for readiness:

```bash
export SIMPLYNEXT_CAPTION_TEMPLATES_PATH=data/caption_templates.example.json
python main.py
```

The defaults expose the service on `http://127.0.0.1:8000`. Useful routes are:

| Method | Path | Purpose |
| :----- | :--- | :------ |
| `GET` | `/healthz` | Process liveness |
| `GET` | `/readyz` | Transport and assembler readiness |
| `GET` | `/metrics` | In-process counters and latency observations |
| `GET` | `/docs` | OpenAPI UI for HTTP endpoints |
| `POST` | `/v1/sessions` | Negotiate a lattice stream and bearer capability |
| `DELETE` | `/v1/sessions/{session_id}` | End an authenticated session |
| WebSocket | `/v1/sessions/{session_id}/lattices` | Submit lattices and receive events |

Bedrock is disabled by default. The live enablement procedure and required manual AWS values are
in `plan/BPP_backend_production_plan.md`.

# 6. DATA FLOW

```text
client classifier
  -> POST /v1/sessions
  -> authenticated WSS connection
  -> GlossLattice JSON
  -> schema/policy/session checks
  -> bounded assembler and independent critic
  -> lattice_result OR lattice_repair_required JSON
  -> client caption UI / local TTS / repair UI
```

The server sends text and evidence as JSON over the WebSocket. `tts_text` is text intended for the
client's speech synthesizer; the server does not send an audio file or audio stream. The
`evidence_trace` is an ordered audit copy of the lattice slots, resolved glosses, confidence,
provenance, and retained candidates that supported the decision.

# 7. QUALITY GATES

```bash
python -m pytest
python -m ruff check .
python -m mypy src
python -m pip check
```

The current verified baseline is 139 passing tests, Ruff clean, strict mypy clean, and a valid
installed dependency set. Re-run the gates after every change; the number of tests may increase.

# 8. REPOSITORY MAP

```text
SimplyNext/
├── src/simplynext/             installable Python package
│   ├── agent/                  graph, Bedrock nodes, prompts, and read-only tools
│   ├── api/                    HTTP/WebSocket handlers and middleware
│   ├── contracts/              strict public wire models
│   ├── observability/          structured logging and in-process metrics
│   ├── sessions/               bounded process-local session/replay state
│   ├── config.py               environment-backed settings
│   ├── lattice_runtime.py      policy and graph-to-event adapter
│   ├── main.py                 FastAPI factory and runtime command
│   └── runtime.py              service container
├── tests/                      contract, unit, integration, and transport tests
├── data/                       deterministic caption-template example
├── plan/                       maintained backend documents
├── pyproject.toml              dependencies, packaging, and tool configuration
├── pylock.toml                 resolved dependency lock
├── requirements.txt            editable install entry point
└── main.py                     checkout-compatible application entry point
```

# 9. DESIGN CONSTRAINTS

- Unknown fields and invalid contract values are rejected.
- Low confidence, ambiguity, model failure, and invalid output fail closed to repair.
- Prompts and model outputs are never trusted as contracts until parsed and grounded.
- Session tokens are opaque capabilities and must remain in memory on the client.
- Session/checkpoint state is process-local, so production starts with one worker and one replica.
- Horizontal scaling requires shared session, replay, rate-limit, and checkpoint storage first.

# 10. DOCUMENTATION

- `plan/ARC_architecture.md` — implemented architecture.
- `plan/CTR_contracts.md` — wire contract.
- `plan/DEP_dependencies.md` — dependency policy.
- `plan/PLN_plan.md` — implementation status.
- `plan/BPP_backend_production_plan.md` — remaining production work.
