from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import used_market_watch as umw


class DummyItem:
    def __init__(self, payload: dict):
        self.payload = payload

    def to_dict(self) -> dict:
        return dict(self.payload)


class Clock:
    def __init__(self, start: int = 1_700_000_000):
        self.value = start

    def __call__(self) -> int:
        current = self.value
        self.value += 1
        return current


def _args(name_or_id: str | None = None):
    return argparse.Namespace(name_or_id=name_or_id, alerts_only=False, json=True)


def test_watch_check_keeps_same_listing_scoped_per_rule_and_emits_price_drop_on_second_pass(monkeypatch, capsys):
    state = {
        "rules": [
            {
                "id": "rule-new",
                "name": "아이폰 신규",
                "query": "아이폰 15 프로",
                "limit": 12,
                "notify_on_new": True,
                "notify_on_price_drop": False,
                "enabled": True,
            },
            {
                "id": "rule-drop",
                "name": "아이폰 하락",
                "query": "아이폰 15 프로",
                "limit": 12,
                "notify_on_new": False,
                "notify_on_price_drop": True,
                "enabled": True,
            },
        ],
        "events": [],
        "last_seen": {},
    }
    saved_states: list[dict] = []
    clock = Clock()
    listings = [
        [{
            "market": "danggeun",
            "article_key": "danggeun:1",
            "title": "아이폰 15 프로",
            "price_text": "1,000,000원",
            "price_numeric": 1000000,
            "link": "https://example.com/1",
        }],
        [{
            "market": "danggeun",
            "article_key": "danggeun:1",
            "title": "아이폰 15 프로",
            "price_text": "1,000,000원",
            "price_numeric": 1000000,
            "link": "https://example.com/1",
        }],
        [{
            "market": "danggeun",
            "article_key": "danggeun:1",
            "title": "아이폰 15 프로",
            "price_text": "1,000,000원",
            "price_numeric": 1000000,
            "link": "https://example.com/1",
        }],
        [{
            "market": "danggeun",
            "article_key": "danggeun:1",
            "title": "아이폰 15 프로",
            "price_text": "900,000원",
            "price_numeric": 900000,
            "link": "https://example.com/1",
        }],
    ]

    monkeypatch.setattr(umw, "load_state", lambda: state)
    monkeypatch.setattr(umw, "load_config", lambda: {"first_run_skip_notifications": False, "notification_window": {"enabled": False, "start_hour": 8, "end_hour": 23}, "blocked_sellers": []})
    monkeypatch.setattr(umw, "save_state", lambda payload: saved_states.append(payload.copy()))
    monkeypatch.setattr(umw, "parse_search_intent", lambda query, limit: type("Intent", (), {"min_price": None, "max_price": None})())
    monkeypatch.setattr(umw, "search_markets", lambda intent: [DummyItem(row) for row in listings.pop(0)])
    monkeypatch.setattr(umw.time, "time", clock)

    assert umw.cmd_watch_check(_args()) == 0
    first = capsys.readouterr().out
    assert '"alert_count": 1' in first
    assert '"new_listing"' in first
    assert state["events"][0]["rule_id"] == "rule-new"

    assert umw.cmd_watch_check(_args()) == 0
    second = capsys.readouterr().out
    assert '"alert_count": 1' in second
    assert '"price_drop"' in second
    assert state["events"][-1]["rule_id"] == "rule-drop"

    assert umw._get_previous_seen(state["last_seen"], state["rules"][0], "danggeun:1")["price_numeric"] == 1000000
    assert umw._get_previous_seen(state["last_seen"], state["rules"][1], "danggeun:1")["price_numeric"] == 900000
    assert len(saved_states) == 2


def test_watch_check_dedupes_duplicate_listing_rows_within_same_run(monkeypatch, capsys):
    state = {
        "rules": [
            {
                "id": "rule-new",
                "name": "중복 테스트",
                "query": "플스5",
                "limit": 12,
                "notify_on_new": True,
                "notify_on_price_drop": False,
                "enabled": True,
            }
        ],
        "events": [],
        "last_seen": {},
    }
    clock = Clock()

    monkeypatch.setattr(umw, "load_state", lambda: state)
    monkeypatch.setattr(umw, "load_config", lambda: {"first_run_skip_notifications": False, "notification_window": {"enabled": False, "start_hour": 8, "end_hour": 23}, "blocked_sellers": []})
    monkeypatch.setattr(umw, "save_state", lambda payload: None)
    monkeypatch.setattr(umw, "parse_search_intent", lambda query, limit: type("Intent", (), {"min_price": None, "max_price": None})())
    monkeypatch.setattr(
        umw,
        "search_markets",
        lambda intent: [
            DummyItem({
                "market": "bunjang",
                "article_key": "bunjang:55",
                "title": "플스5 디지털",
                "price_text": "450,000원",
                "price_numeric": 450000,
                "link": "https://example.com/55",
            }),
            DummyItem({
                "market": "bunjang",
                "article_key": "bunjang:55",
                "title": "플스5 디지털",
                "price_text": "450,000원",
                "price_numeric": 450000,
                "link": "https://example.com/55",
            }),
        ],
    )
    monkeypatch.setattr(umw.time, "time", clock)

    assert umw.cmd_watch_check(_args()) == 0
    output = capsys.readouterr().out
    assert '"alert_count": 1' in output
    assert len(state["events"]) == 1
    assert len(state["last_seen"]) == 1


def test_watch_check_skips_first_run_notifications_as_baseline(monkeypatch, capsys):
    state = {
        "rules": [
            {
                "id": "rule-new",
                "name": "baseline 테스트",
                "query": "아이폰",
                "limit": 12,
                "notify_on_new": True,
                "notify_on_price_drop": False,
                "enabled": True,
            }
        ],
        "events": [],
        "last_seen": {},
    }
    clock = Clock()

    monkeypatch.setattr(umw, "load_state", lambda: state)
    monkeypatch.setattr(umw, "load_config", lambda: {"first_run_skip_notifications": True, "notification_window": {"enabled": False, "start_hour": 8, "end_hour": 23}, "blocked_sellers": []})
    monkeypatch.setattr(umw, "save_state", lambda payload: None)
    monkeypatch.setattr(umw, "parse_search_intent", lambda query, limit: type("Intent", (), {"min_price": None, "max_price": None})())
    monkeypatch.setattr(
        umw,
        "search_markets",
        lambda intent: [DummyItem({
            "market": "danggeun",
            "article_key": "danggeun:1",
            "title": "아이폰 15 프로",
            "price_text": "1,000,000원",
            "price_numeric": 1000000,
            "link": "https://example.com/1",
            "tags": ["급처"],
        })],
    )
    monkeypatch.setattr(umw.time, "time", clock)

    assert umw.cmd_watch_check(_args()) == 0
    output = capsys.readouterr().out
    assert '"alert_count": 0' in output
    assert '"suppressed_count": 1' in output
    assert state["rules"][0]["baseline_established_at"] is not None
    assert state["events"] == []


def test_watch_check_applies_blocked_seller_filter(monkeypatch, capsys):
    state = {
        "rules": [
            {
                "id": "rule-new",
                "name": "seller filter 테스트",
                "query": "플스5",
                "limit": 12,
                "notify_on_new": True,
                "notify_on_price_drop": False,
                "enabled": True,
                "baseline_established_at": 1700000000,
            }
        ],
        "events": [],
        "last_seen": {},
    }
    clock = Clock()

    monkeypatch.setattr(umw, "load_state", lambda: state)
    monkeypatch.setattr(umw, "load_config", lambda: {"first_run_skip_notifications": True, "notification_window": {"enabled": False, "start_hour": 8, "end_hour": 23}, "blocked_sellers": ["업자계정"]})
    monkeypatch.setattr(umw, "save_state", lambda payload: None)
    monkeypatch.setattr(umw, "parse_search_intent", lambda query, limit: type("Intent", (), {"min_price": None, "max_price": None})())
    monkeypatch.setattr(
        umw,
        "search_markets",
        lambda intent: [DummyItem({
            "market": "bunjang",
            "article_key": "bunjang:9",
            "title": "플스5 급처",
            "price_text": "450,000원",
            "price_numeric": 450000,
            "link": "https://example.com/9",
            "seller": "업자계정",
        })],
    )
    monkeypatch.setattr(umw.time, "time", clock)

    assert umw.cmd_watch_check(_args()) == 0
    output = capsys.readouterr().out
    assert '"alert_count": 0' in output
    assert state["events"] == []
