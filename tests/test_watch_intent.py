from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from watch_intent import parse_watch_request


def test_parse_watch_request_for_new_only():
    data = parse_watch_request('"아이폰 신규" 아이폰 15 프로 120만원 이하 당근 번장 신규만 감시 추가')
    assert data["name"] == "아이폰 신규"
    assert data["notify_on_new"] is True
    assert data["notify_on_price_drop"] is False
    assert data["max_price"] == 1200000
    assert "danggeun" in data["intent"]["markets"]
    assert "bunjang" in data["intent"]["markets"]


def test_parse_watch_request_for_price_drop_and_limit():
    data = parse_watch_request("맥북 에어 m2 가격하락만 감시 5개 잠실")
    assert data["notify_on_new"] is False
    assert data["notify_on_price_drop"] is True
    assert data["limit"] == 5
    assert data["intent"]["location"] and "잠실" in data["intent"]["location"]
