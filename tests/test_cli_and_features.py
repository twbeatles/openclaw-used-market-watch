from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from unittest.mock import patch

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from output_utils import _format_price_change, render_search_text
from used_market_watch import _ensure_utf8_stdout, _summarize, main


def test_summarize_avg_median_bargain():
    items = [
        {"market": "danggeun", "price_numeric": 100000},
        {"market": "danggeun", "price_numeric": 110000},
        {"market": "bunjang", "price_numeric": 120000},
        {"market": "bunjang", "price_numeric": 60000},  # bargain <= 75% of avg
    ]
    summary = _summarize(items)
    assert summary["total"] == 4
    assert summary["min_price"] == 60000
    assert summary["max_price"] == 120000
    # avg = (100000 + 110000 + 120000 + 60000) / 4 = 97500
    assert summary["avg_price"] == 97500
    assert summary["median_price"] == 105000
    # Check if 60000 item got marked as bargain (threshold = 97500 * 0.75 = 73125)
    assert items[3].get("is_bargain") is True
    assert items[0].get("is_bargain") is not True


def test_format_price_change():
    # 1,000,000 -> 800,000 (-200,000, -20.0%)
    res = _format_price_change("1,000,000원", "800,000원")
    assert "이전 1,000,000원 → 800,000원" in res
    assert "▼200,000원" in res
    assert "-20.0%" in res


def test_cli_message_template():
    buf = io.StringIO()
    with patch("sys.stdout", buf):
        code = main([
            "message-template",
            "nego",
            "--title", "맥북 프로 14인치",
            "--price", "180만원",
            "--json",
        ])
    assert code == 0
    data = json.loads(buf.getvalue())
    assert data["kind"] == "used-market-seller-message"
    assert data["template_id"] == "nego"
    assert "맥북 프로 14인치" in data["message"]
    assert "180만원" in data["message"]


def test_ensure_utf8_stdout_allows_emoji():
    buf = io.BytesIO()
    wrapper = io.TextIOWrapper(buf, encoding="cp949", errors="strict")
    with patch.object(sys, "stdout", wrapper):
        _ensure_utf8_stdout()
        print(json.dumps({"tags": ["📦 풀박스"]}, ensure_ascii=False))
        wrapper.flush()
    assert "풀박스" in buf.getvalue().decode("utf-8")


def test_cli_message_template_list():
    buf = io.StringIO()
    with patch("sys.stdout", buf):
        code = main([
            "message-template",
            "--list",
            "--json",
        ])
    assert code == 0
    data = json.loads(buf.getvalue())
    assert data["kind"] == "used-market-message-templates"
    assert len(data["templates"]) >= 7
