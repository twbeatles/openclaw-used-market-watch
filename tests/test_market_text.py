from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import market_client
from market_client import (
    _clean_title,
    _pid_from_href,
    _price_from_title,
)


def test_clean_title_strips_naver_noise():
    assert _clean_title("아이폰 17 프로 새 창 열림") == "아이폰 17 프로"
    assert _clean_title("아이폰17프로맥스 SSS급 실버 팝니다 새 창 열림") == "아이폰17프로맥스 SSS급 실버 팝니다"
    assert _clean_title("A  새창열림  B") == "A B"
    assert _clean_title("깨끗한 아이폰") == "깨끗한 아이폰"


def test_price_from_title_requires_price_unit():
    assert _price_from_title("아이폰17프로") == 0
    assert _price_from_title("아이폰 17프로 256GB") == 0
    assert _price_from_title("추천합니다") == 0
    assert _price_from_title(None) == 0
    assert _price_from_title("아이폰 17프로 120만원") == 1200000
    assert _price_from_title("아이폰 17 프로 1,200,000원") == 1200000


def test_pid_from_href():
    assert _pid_from_href("/products/425751521?imp_id=abc") == "425751521"
    assert _pid_from_href("https://m.bunjang.co.kr/products/12345") == "12345"
    assert _pid_from_href("/foo/bar") == ""
    assert _pid_from_href(None) == ""


def test_safe_collect_isolates_market_failure(monkeypatch):
    async def boom(page, intent):
        raise RuntimeError("bot blocked")

    monkeypatch.setattr(market_client, "_search_danggeun", boom)
    assert asyncio.run(market_client._safe_collect(None, "danggeun", None)) == []


def test_safe_collect_unknown_market():
    assert asyncio.run(market_client._safe_collect(None, "unknown", None)) == []
