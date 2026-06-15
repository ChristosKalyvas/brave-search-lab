"""A tiny, dependency-free TTL cache on disk.

Brave's free tier is rate-limited, so caching repeated queries keeps demos
snappy and friendly to your quota. Keys are hashed query signatures.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional


class TTLCache:
    def __init__(self, directory: str | Path = ".bravecache", ttl_seconds: int = 900):
        self.dir = Path(directory)
        self.ttl = ttl_seconds
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
        return self.dir / f"{digest}.json"

    def get(self, key: str) -> Optional[Any]:
        path = self._path(key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text("utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if time.time() - payload.get("stored_at", 0) > self.ttl:
            return None
        return payload.get("value")

    def set(self, key: str, value: Any) -> None:
        path = self._path(key)
        path.write_text(
            json.dumps({"stored_at": time.time(), "value": value}),
            encoding="utf-8",
        )

    def clear(self) -> int:
        removed = 0
        for f in self.dir.glob("*.json"):
            f.unlink(missing_ok=True)
            removed += 1
        return removed
