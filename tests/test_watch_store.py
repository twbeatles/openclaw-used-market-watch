from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from watch_store import remove_rule, set_rule_enabled, upsert_rule


def test_upsert_rule_creates_then_updates_existing_name():
    state = {"rules": []}
    created, is_created = upsert_rule(
        state,
        {
            "name": "아이폰 감시",
            "query": "아이폰 15 프로",
            "limit": 12,
            "min_price": None,
            "max_price": 1200000,
            "notify_on_new": True,
            "notify_on_price_drop": False,
            "enabled": True,
        },
    )
    assert is_created is True
    updated, is_created = upsert_rule(
        state,
        {
            "name": "아이폰 감시",
            "query": "아이폰 15 프로 max",
            "limit": 5,
            "min_price": None,
            "max_price": 1100000,
            "notify_on_new": True,
            "notify_on_price_drop": True,
            "enabled": False,
        },
    )
    assert is_created is False
    assert created["id"] == updated["id"]
    assert updated["query"] == "아이폰 15 프로 max"
    assert updated["limit"] == 5
    assert updated["enabled"] is False


def test_enable_disable_and_remove_rule():
    state = {
        "rules": [
            {
                "id": "rule-1",
                "name": "맥북 감시",
                "query": "맥북",
                "limit": 12,
                "notify_on_new": True,
                "notify_on_price_drop": True,
                "enabled": True,
            }
        ]
    }
    rule = set_rule_enabled(state, "맥북 감시", False)
    assert rule and rule["enabled"] is False
    removed = remove_rule(state, "rule-1")
    assert removed and removed["name"] == "맥북 감시"
    assert state["rules"] == []
