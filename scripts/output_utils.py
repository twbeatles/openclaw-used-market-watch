from __future__ import annotations

from typing import Any

from models import MARKET_LABELS
from price_utils import format_price_kr


def render_search_text(payload: dict[str, Any]) -> str:
    intent = payload.get("intent") or {}
    items = payload.get("items") or []
    lines = [f"중고 매물 브리핑: {intent.get('keyword') or intent.get('raw_query')}"]
    filters = []
    if intent.get("markets"):
        filters.append("마켓=" + ", ".join(MARKET_LABELS.get(m, m) for m in intent["markets"]))
    if intent.get("location"):
        filters.append(f"지역={intent['location']}")
    if intent.get("min_price"):
        filters.append(f"최소={format_price_kr(intent['min_price'])}")
    if intent.get("max_price"):
        filters.append(f"최대={format_price_kr(intent['max_price'])}")
    if intent.get("exclude_terms"):
        filters.append("제외=" + ", ".join(intent["exclude_terms"]))
    if filters:
        lines.append("- " + " / ".join(filters))
    summary = payload.get("summary") or {}
    lines.append(f"- 총 {summary.get('total', 0)}건, 표시 {len(items)}건")
    for market, row in (summary.get("by_market") or {}).items():
        lines.append(f"- {MARKET_LABELS.get(market, market)}: {row.get('count', 0)}건, 최저 {format_price_kr(row.get('min_price'))}, 최고 {format_price_kr(row.get('max_price'))}")
    if not items:
        lines.append("- 조건에 맞는 매물이 없습니다.")
        return "\n".join(lines)
    for idx, item in enumerate(items, start=1):
        label = MARKET_LABELS.get(item.get("market"), item.get("market"))
        price = item.get("price_text") or format_price_kr(item.get("price_numeric"))
        extra = []
        if item.get("location"):
            extra.append(item["location"])
        if item.get("seller"):
            extra.append(f"판매자 {item['seller']}")
        suffix = f" ({' / '.join(extra)})" if extra else ""
        lines.append(f"{idx}. [{label}] {item.get('title')} - {price}{suffix}")
        if item.get("link"):
            lines.append(f"   - {item['link']}")
    return "\n".join(lines)


def render_watch_preview(payload: dict[str, Any]) -> str:
    lines = [f"중고 매물 watch 점검: {payload.get('alert_count', 0)}건 알림"]
    for row in payload.get("alerts") or []:
        rule = row.get("rule") or {}
        lines.append(f"- {rule.get('name')}: {row.get('matched_count', 0)}건")
        for match in (row.get("matched") or [])[:5]:
            badges = [match.get("event_type")]
            if match.get("previous_price_text"):
                badges.append(f"이전 {match['previous_price_text']}")
            lines.append(f"  · [{MARKET_LABELS.get(match.get('market'), match.get('market'))}] {match.get('title')} / {match.get('price_text')} ({', '.join([b for b in badges if b])})")
            if match.get("link"):
                lines.append(f"    - {match['link']}")
    return "\n".join(lines)
