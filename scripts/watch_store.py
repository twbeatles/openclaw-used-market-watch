from __future__ import annotations

import json
import time
import uuid
from typing import Any

from _paths import WATCH_STATE_FILE

SCHEMA_VERSION = 1


def load_state() -> dict[str, Any]:
    if WATCH_STATE_FILE.exists():
        data = json.loads(WATCH_STATE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("schema_version", SCHEMA_VERSION)
            data.setdefault("rules", [])
            data.setdefault("events", [])
            data.setdefault("last_seen", {})
            data.setdefault("last_checked_at", None)
            return data
    return {"schema_version": SCHEMA_VERSION, "rules": [], "events": [], "last_seen": {}, "last_checked_at": None}


def save_state(data: dict[str, Any]) -> None:
    WATCH_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    WATCH_STATE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def make_rule(*, name: str, query: str, limit: int, min_price: int | None, max_price: int | None, notify_on_new: bool, notify_on_price_drop: bool) -> dict[str, Any]:
    now = int(time.time())
    return {
        "id": f"rule-{uuid.uuid4().hex[:10]}",
        "name": name,
        "query": query,
        "limit": limit,
        "min_price": min_price,
        "max_price": max_price,
        "notify_on_new": bool(notify_on_new),
        "notify_on_price_drop": bool(notify_on_price_drop),
        "enabled": True,
        "created_at": now,
        "updated_at": now,
    }
