from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from used_market_watch import _make_alert, _summarize


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
