# SignBridge backend

This is the local backend for the Flutter tracking contract. The sign-sequence
endpoint still uses only Python's standard library. The optional emotion
endpoint adapts the OpenCV + DeepFace example used by the frontend.

## Run it

From the repository root:

```bash
python3 backend/run.py
```

To enable DeepFace emotion analysis, install the model dependencies first:

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
.venv/bin/python backend/run.py
```

The API listens on `http://127.0.0.1:8000`:

```text
GET  /health
POST /v1/sign-sequences/analyze
POST /v1/emotions/analyze  (JPEG or PNG body)
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
features. Raw video is not stored. When DeepFace is enabled, the browser sends
one compressed camera snapshot about once per second to the configured API so
the Python service can analyse it; keep the API local unless the user has
explicitly consented to remote processing.

The emotion response looks like this:

```json
{
  "status": "ok",
  "dominant_emotion": "happy",
  "confidence": 0.86,
  "emotions": {"angry": 0.01, "happy": 0.86, "neutral": 0.08},
  "model": "DeepFace"
}
```

Run the backend tests with:

```bash
python3 -m unittest discover -s backend/tests -v
```
