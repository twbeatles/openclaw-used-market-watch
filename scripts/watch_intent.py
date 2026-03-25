from __future__ import annotations

import re
from typing import Any

from query_parser import parse_search_intent


def _derive_name(text: str, keyword: str) -> str:
    quoted = re.search(r'"([^"]{2,40})"', text)
    if quoted:
        return quoted.group(1).strip()
    clean_keyword = " ".join(str(keyword or "").split())[:32].strip()
    return f"{clean_keyword or '중고 매물'} 감시"


def _detect_notifications(text: str) -> tuple[bool, bool]:
    normalized = text.replace(" ", "")
    has_new = any(token in normalized for token in ("신규만", "새매물만", "신규", "새매물", "새로올라오면", "새로올라온"))
    has_drop = any(token in normalized for token in ("가격하락만", "가격내려가면", "가격떨어지면", "가격하락", "내려가면", "떨어지면"))
    if "신규만" in normalized or "새매물만" in normalized:
        return True, False
    if "가격하락만" in normalized:
        return False, True
    if has_new or has_drop:
        return has_new, has_drop
    return True, True


def _detect_limit(text: str, default_limit: int) -> int:
    m = re.search(r"(\d+)\s*(?:개|건)\s*(?:만|까지|정도)?", text)
    if m:
        return max(1, int(m.group(1)))
    return default_limit


def parse_watch_request(text: str, *, default_limit: int = 12) -> dict[str, Any]:
    intent = parse_search_intent(text, limit=_detect_limit(text, default_limit))
    notify_on_new, notify_on_price_drop = _detect_notifications(text)
    name = _derive_name(text, intent.keyword)
    return {
        "name": name,
        "query": intent.raw_query,
        "limit": intent.limit,
        "min_price": intent.min_price,
        "max_price": intent.max_price,
        "notify_on_new": notify_on_new,
        "notify_on_price_drop": notify_on_price_drop,
        "enabled": "비활성" not in text and "끄기" not in text,
        "intent": intent.to_dict(),
    }
