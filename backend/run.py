"""Run the local SignBridge backend.

Usage:
    python3 backend/run.py
"""

from __future__ import annotations

import argparse
import asyncio
import threading
from pathlib import Path

from signbridge_backend.http_api import create_server
from signbridge_backend.analyzer import SignAnalyzer
from signbridge_backend.service import SignBridgeBackend
from signbridge_backend.store import SequenceStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the SignBridge analysis API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--tracking-port", type=int, default=8001)
    parser.add_argument("--perception-port", type=int, default=8002)
    parser.add_argument(
        "--segmenter-arm",
        choices=("geometry_hysteresis", "sliding_window_blank"),
        default="geometry_hysteresis",
        help="Stage-④ arm used before classifier feature extraction",
    )
    parser.add_argument(
        "--store",
        default=str(Path(__file__).parent / "data" / "sign_sequences.jsonl"),
        help="JSONL path used for local sequence storage",
    )
    args = parser.parse_args()

    service = SignBridgeBackend(
        analyzer=SignAnalyzer(segmenter_arm=args.segmenter_arm),
        store=SequenceStore(args.store),
    )
    try:
        service.warm_up_emotion_models()
        print("HSEmotion face model ready")
    except Exception as error:
        # Keep the sign-processing and landmark-stream endpoints available
        # when the optional facial model is not installed.
        print(f"Emotion model warm-up deferred: {error}")
    server = create_server(args.host, args.port, service)
    from signbridge_backend.ws_api import make_servers

    websocket_loop = asyncio.new_event_loop()
    websocket_ready = threading.Event()
    websocket_servers = {}

    def run_websockets() -> None:
        asyncio.set_event_loop(websocket_loop)
        try:
            starter = make_servers(service, args.host, args.tracking_port, args.perception_port)
            websocket_servers["servers"] = websocket_loop.run_until_complete(starter())
            websocket_ready.set()
            websocket_loop.run_forever()
        finally:
            for websocket_server in websocket_servers.get("servers", ()):
                websocket_server.close()
            if websocket_servers.get("servers"):
                websocket_loop.run_until_complete(
                    asyncio.gather(*(
                        websocket_server.wait_closed()
                        for websocket_server in websocket_servers["servers"]
                    ))
                )
            websocket_loop.close()

    websocket_thread = threading.Thread(target=run_websockets, daemon=True)
    websocket_thread.start()
    websocket_ready.wait(timeout=5)
    print(f"SignBridge backend listening at http://{args.host}:{args.port}")
    print("POST /v1/sign-sequences/analyze")
    print(f"WebSocket ws://{args.host}:{args.tracking_port}/v1/tracking-stream (landmarks only)")
    print(f"WebSocket ws://{args.host}:{args.perception_port}/v1/perception-stream (local camera worker)")
    print("POST /v1/facial-analysis (optional CV4ED affect ONNX model)")
    print(f"Stage-④ segmenter arm: {args.segmenter_arm}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping SignBridge backend")
    finally:
        server.server_close()
        websocket_loop.call_soon_threadsafe(websocket_loop.stop)
        websocket_thread.join(timeout=3)


if __name__ == "__main__":
    main()
