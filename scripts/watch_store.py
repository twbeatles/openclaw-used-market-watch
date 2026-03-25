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


def find_rule(state: dict[str, Any], name_or_id: str) -> dict[str, Any] | None:
    for rule in state.get("rules") or []:
        if rule.get("id") == name_or_id or rule.get("name") == name_or_id:
            return rule
    return None


def upsert_rule(state: dict[str, Any], rule_data: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    now = int(time.time())
    existing = find_rule(state, rule_data["name"])
    if existing:
        existing.update(
            {
                "query": rule_data["query"],
                "limit": int(rule_data.get("limit") or existing.get("limit") or 12),
                "min_price": rule_data.get("min_price"),
                "max_price": rule_data.get("max_price"),
                "notify_on_new": bool(rule_data.get("notify_on_new")),
                "notify_on_price_drop": bool(rule_data.get("notify_on_price_drop")),
                "enabled": bool(rule_data.get("enabled", True)),
                "updated_at": now,
            }
        )
        return existing, False
    rule = make_rule(
        name=rule_data["name"],
        query=rule_data["query"],
        limit=int(rule_data.get("limit") or 12),
        min_price=rule_data.get("min_price"),
        max_price=rule_data.get("max_price"),
        notify_on_new=bool(rule_data.get("notify_on_new")),
        notify_on_price_drop=bool(rule_data.get("notify_on_price_drop")),
    )
    rule["enabled"] = bool(rule_data.get("enabled", True))
    state.setdefault("rules", []).append(rule)
    return rule, True


def set_rule_enabled(state: dict[str, Any], name_or_id: str, enabled: bool) -> dict[str, Any] | None:
    rule = find_rule(state, name_or_id)
    if not rule:
        return None
    rule["enabled"] = bool(enabled)
    rule["updated_at"] = int(time.time())
    return rule


def remove_rule(state: dict[str, Any], name_or_id: str) -> dict[str, Any] | None:
    rules = state.get("rules") or []
    for idx, rule in enumerate(rules):
        if rule.get("id") == name_or_id or rule.get("name") == name_or_id:
            return rules.pop(idx)
    return None
