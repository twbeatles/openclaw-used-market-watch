from __future__ import annotations

import json
import time
import uuid
from typing import Any

from _paths import WATCH_CONFIG_FILE, WATCH_STATE_FILE

SCHEMA_VERSION = 3

DEFAULT_CONFIG = {
    "first_run_skip_notifications": True,
    "notification_window": {
        "enabled": False,
        "start_hour": 8,
        "end_hour": 23,
    },
    "blocked_sellers": [],
}


def _normalize_rule(rule: dict[str, Any]) -> dict[str, Any]:
    rule.setdefault("delivery_mode", "alert")
    rule.setdefault("action", "watch")
    rule.setdefault("schedule", {"kind": "manual", "label": "수동 또는 상위 스케줄러 연결 필요", "cron": None})
    rule.setdefault("plan_hints", {})
    rule.setdefault("baseline_established_at", None)
    rule.setdefault("last_snapshot", None)
    return rule


def _normalize_config(config: dict[str, Any] | None) -> dict[str, Any]:
    payload = dict(DEFAULT_CONFIG)
    if isinstance(config, dict):
        payload.update({k: v for k, v in config.items() if k in DEFAULT_CONFIG})
        window = dict(DEFAULT_CONFIG["notification_window"])
        if isinstance(config.get("notification_window"), dict):
            window.update(config["notification_window"])
        payload["notification_window"] = window
    payload["blocked_sellers"] = [str(x).strip() for x in (payload.get("blocked_sellers") or []) if str(x).strip()]
    return payload


def load_state() -> dict[str, Any]:
    if WATCH_STATE_FILE.exists():
        data = json.loads(WATCH_STATE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("schema_version", SCHEMA_VERSION)
            data.setdefault("rules", [])
            data.setdefault("events", [])
            data.setdefault("last_seen", {})
            data.setdefault("last_checked_at", None)
            data.setdefault("config", load_config())
            data["rules"] = [_normalize_rule(rule) for rule in (data.get("rules") or [])]
            return data
    return {"schema_version": SCHEMA_VERSION, "rules": [], "events": [], "last_seen": {}, "last_checked_at": None, "config": load_config()}


def load_config() -> dict[str, Any]:
    if WATCH_CONFIG_FILE.exists():
        data = json.loads(WATCH_CONFIG_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return _normalize_config(data)
    return _normalize_config(None)


def save_config(config: dict[str, Any]) -> None:
    WATCH_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    WATCH_CONFIG_FILE.write_text(json.dumps(_normalize_config(config), ensure_ascii=False, indent=2), encoding="utf-8")


def save_state(data: dict[str, Any]) -> None:
    WATCH_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    WATCH_STATE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def make_rule(*, name: str, query: str, limit: int, min_price: int | None, max_price: int | None, notify_on_new: bool, notify_on_price_drop: bool, enabled: bool = True, delivery_mode: str = "alert", action: str = "watch", schedule: dict[str, Any] | None = None, plan_hints: dict[str, Any] | None = None) -> dict[str, Any]:
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
        "enabled": bool(enabled),
        "delivery_mode": delivery_mode,
        "action": action,
        "schedule": schedule or {"kind": "manual", "label": "수동 또는 상위 스케줄러 연결 필요", "cron": None},
        "plan_hints": plan_hints or {},
        "baseline_established_at": None,
        "last_snapshot": None,
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
                "delivery_mode": rule_data.get("delivery_mode") or existing.get("delivery_mode") or "alert",
                "action": rule_data.get("action") or existing.get("action") or "watch",
                "schedule": rule_data.get("schedule") or existing.get("schedule") or {"kind": "manual", "label": "수동 또는 상위 스케줄러 연결 필요", "cron": None},
                "plan_hints": rule_data.get("plan_hints") or existing.get("plan_hints") or {},
                "baseline_established_at": existing.get("baseline_established_at"),
                "last_snapshot": existing.get("last_snapshot"),
                "updated_at": now,
            }
        )
        return _normalize_rule(existing), False
    rule = make_rule(
        name=rule_data["name"],
        query=rule_data["query"],
        limit=int(rule_data.get("limit") or 12),
        min_price=rule_data.get("min_price"),
        max_price=rule_data.get("max_price"),
        notify_on_new=bool(rule_data.get("notify_on_new")),
        notify_on_price_drop=bool(rule_data.get("notify_on_price_drop")),
        enabled=bool(rule_data.get("enabled", True)),
        delivery_mode=rule_data.get("delivery_mode") or "alert",
        action=rule_data.get("action") or "watch",
        schedule=rule_data.get("schedule"),
        plan_hints=rule_data.get("plan_hints"),
    )
    state.setdefault("rules", []).append(rule)
    return _normalize_rule(rule), True


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
