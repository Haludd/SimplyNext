"""Small JSONL persistence layer for local development and demos."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .models import SignSequencePayload


class SequenceStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(
        self,
        payload: SignSequencePayload,
        result: dict[str, Any],
    ) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "received_at": datetime.now(timezone.utc).isoformat(),
            "payload": payload.to_dict(),
            "result": result,
        }
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, separators=(",", ":")) + "\n")

    def count(self) -> int:
        if not self.path.exists():
            return 0
        with self.path.open("r", encoding="utf-8") as stream:
            return sum(1 for line in stream if line.strip())
