# SignBridge backend

This is the first working backend for the Flutter tracking contract. It uses
only Python's standard library, so it can run before the trained ASL and facial
models are ready.

## Run it

From the repository root:

```bash
python3 backend/run.py
```

The API listens on `http://127.0.0.1:8000`:

```text
GET  /health
POST /v1/sign-sequences/analyze
```

Start Flutter against it in another terminal:

```bash
cd appTesting
flutter run -d chrome \
  --dart-define=SIGNBRIDGE_API_URL=http://127.0.0.1:8000
```

The server validates the sequence, keeps a JSONL copy under
`backend/data/sign_sequences.jsonl`, and returns a deliberately conservative
handshape candidate. It does not claim to translate ASL yet. The analyzer is a
replaceable library class: a trained temporal model can implement the same
`SignAnalyzer.analyze()` contract later.

The stored payload includes the 21-point hand coordinates, world coordinates
when the browser provides them, hand geometry, motion, and facial expression
features. Raw video is not uploaded or stored.

Run the backend tests with:

```bash
python3 -m unittest discover -s backend/tests -v
```
