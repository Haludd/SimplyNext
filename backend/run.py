"""Run the local SignBridge backend.

Usage:
    python3 backend/run.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

from signbridge_backend.http_api import create_server
from signbridge_backend.service import SignBridgeBackend
from signbridge_backend.store import SequenceStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the SignBridge analysis API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--store",
        default=str(Path(__file__).parent / "data" / "sign_sequences.jsonl"),
        help="JSONL path used for local sequence storage",
    )
    args = parser.parse_args()

    service = SignBridgeBackend(store=SequenceStore(args.store))
    server = create_server(args.host, args.port, service)
    print(f"SignBridge backend listening at http://{args.host}:{args.port}")
    print("POST /v1/sign-sequences/analyze")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping SignBridge backend")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
