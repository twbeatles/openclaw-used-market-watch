from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from output_utils import render_integration_plan, render_watch_plan
from used_market_watch import _event_counts, _get_previous_seen, _last_seen_key, _make_alert, _store_last_seen, _summarize, _tag_counts


def test_summarize_by_market():
    items = [
        {"market": "danggeun", "price_numeric": 10000},
        {"market": "danggeun", "price_numeric": 5000},
        {"market": "bunjang", "price_numeric": 30000},
    ]
    data = _summarize(items)
    assert data["total"] == 3
    assert data["by_market"]["danggeun"]["count"] == 2
    assert data["by_market"]["danggeun"]["min_price"] == 5000


def test_make_alert_has_previous_fields():
    rule = {"id": "r1", "name": "테스트"}
    item = {
        "market": "danggeun",
        "article_key": "danggeun:1",
        "title": "아이폰",
        "price_text": "100,000원",
        "price_numeric": 100000,
        "link": "https://example.com",
    }
    prev = {"price_text": "120,000원", "price_numeric": 120000}
    alert = _make_alert(rule, item, "price_drop", prev)
    assert alert["event_type"] == "price_drop"
    assert alert["previous_price_numeric"] == 120000


def test_event_counts_groups_by_type():
    counts = _event_counts([
        {"event_type": "new_listing"},
        {"event_type": "price_drop"},
        {"event_type": "new_listing"},
    ])
    assert counts == {"new_listing": 2, "price_drop": 1}


def test_last_seen_is_scoped_per_rule():
    last_seen = {}
    first_rule = {"id": "rule-1", "name": "아이폰 신규"}
    second_rule = {"id": "rule-2", "name": "아이폰 하락"}
    item = {
        "article_key": "danggeun:123",
        "title": "아이폰 15 프로",
        "price_text": "1,000,000원",
        "price_numeric": 1000000,
        "link": "https://example.com/123",
    }

    _store_last_seen(last_seen, first_rule, item, checked_at=1234567890)

    assert _last_seen_key(first_rule, item["article_key"]) in last_seen
    assert _get_previous_seen(last_seen, first_rule, item["article_key"])
    assert _get_previous_seen(last_seen, second_rule, item["article_key"]) is None


def test_last_seen_falls_back_to_legacy_unscoped_key():
    rule = {"id": "rule-1", "name": "아이폰 감시"}
    article_key = "danggeun:123"
    legacy = {article_key: {"price_numeric": 900000, "price_text": "900,000원"}}

    prev = _get_previous_seen(legacy, rule, article_key)

    assert prev == legacy[article_key]


def test_render_watch_plan_includes_schedule_and_cron_hint():
    text = render_watch_plan(
        {
            "rule": {
                "name": "플스5 감시",
                "query": "플스5 매일 아침 8시에 브리핑해줘",
                "notify_on_new": True,
                "notify_on_price_drop": True,
                "enabled": True,
                "limit": 12,
                "delivery_mode": "briefing",
                "schedule": {"kind": "daily", "hour": 8, "minute": 0, "label": "매일 08:00", "cron": "0 8 * * *"},
                "plan_hints": {"recommended_command": 'python skills/used-market-watch/scripts/used_market_watch.py watch-check "플스5 감시" --json', "cron_example": '0 8 * * * python skills/used-market-watch/scripts/used_market_watch.py watch-check "플스5 감시" --json'},
            },
            "intent": {"markets": ["danggeun", "bunjang"]},
        }
    )
    assert "실행 주기: 매일 08:00" in text
    assert "cron 예시:" in text
    assert "권장 실행:" in text
    assert "동작: 브리핑" in text


def test_tag_counts_groups_all_tags():
    assert _tag_counts([
        {"tags": ["급처", "택포"]},
        {"tags": ["급처"]},
    ]) == {"급처": 2, "택포": 1}


def test_render_integration_plan_includes_save_and_cron_details():
    text = render_integration_plan(
        {
            "request": "아이폰 15 프로 신규 매물만 1시간마다 감시해줘",
            "parsed_plan": {
                "name": "아이폰 15 프로 감시",
                "query": "아이폰 15 프로 신규 매물만 1시간마다 감시해줘",
                "notify_on_new": True,
                "notify_on_price_drop": False,
                "delivery_mode": "alert",
                "schedule": {"kind": "interval", "every_hours": 1, "label": "1시간마다", "cron": "0 */1 * * *"},
            },
            "persist": {"command": 'python skills/used-market-watch/scripts/used_market_watch.py watch-upsert "아이폰 15 프로 신규 매물만 1시간마다 감시해줘"'},
            "execution": {
                "recommended_command": 'python skills/used-market-watch/scripts/used_market_watch.py watch-check "아이폰 15 프로 감시" --alerts-only --json',
                "cron_payload": {"expr": "0 */1 * * *"},
                "system_event": {"type": "used-market-watch-check", "rule_name": "아이폰 15 프로 감시", "delivery_mode": "alert"},
            },
            "operator_summary": "운영 요약",
            "user_confirmation": "확인 문구",
        }
    )
    assert "자동화 연동 계획" in text
    assert "저장 명령:" in text
    assert "cron 제안: 0 */1 * * *" in text
    assert "systemEvent 힌트:" in text
