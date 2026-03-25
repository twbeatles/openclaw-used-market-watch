from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any

from market_client import search_markets
from models import MARKET_LABELS
from output_utils import render_search_text, render_watch_preview
from query_parser import parse_search_intent
from watch_store import load_state, make_rule, save_state


def _summarize(items: list[dict[str, Any]]) -> dict[str, Any]:
    by_market: dict[str, dict[str, Any]] = {}
    for item in items:
        row = by_market.setdefault(item["market"], {"count": 0, "prices": []})
        row["count"] += 1
        if item.get("price_numeric"):
            row["prices"].append(item["price_numeric"])
    out: dict[str, Any] = {"total": len(items), "by_market": {}}
    for market, row in by_market.items():
        prices = row.pop("prices")
        out["by_market"][market] = {
            **row,
            "min_price": min(prices) if prices else None,
            "max_price": max(prices) if prices else None,
        }
    return out


def run_search(query: str, *, limit: int, as_json: bool) -> int:
    intent = parse_search_intent(query, limit=limit)
    items = [item.to_dict() for item in search_markets(intent)]
    payload = {"kind": "used-market-search", "intent": intent.to_dict(), "summary": _summarize(items), "items": items}
    print(json.dumps(payload, ensure_ascii=False, indent=2) if as_json else render_search_text(payload))
    return 0


def cmd_parse(args: argparse.Namespace) -> int:
    intent = parse_search_intent(args.query, limit=args.limit)
    print(json.dumps(intent.to_dict(), ensure_ascii=False, indent=2))
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    return run_search(args.query, limit=args.limit, as_json=args.json)


def cmd_watch_add(args: argparse.Namespace) -> int:
    state = load_state()
    rule = make_rule(
        name=args.name,
        query=args.query,
        limit=args.limit,
        min_price=args.min_price,
        max_price=args.max_price,
        notify_on_new=args.notify_on_new,
        notify_on_price_drop=args.notify_on_price_drop,
    )
    state["rules"].append(rule)
    save_state(state)
    print(json.dumps({"saved": True, "rule": rule}, ensure_ascii=False, indent=2) if args.json else f"등록 완료: {rule['name']} -> {rule['query']}")
    return 0


def cmd_watch_list(args: argparse.Namespace) -> int:
    state = load_state()
    if args.json:
        print(json.dumps(state, ensure_ascii=False, indent=2))
        return 0
    if not state["rules"]:
        print("등록된 watch rule이 없습니다.")
        return 0
    for rule in state["rules"]:
        lines = [f"- {rule['name']} ({rule['id']}): {rule['query']}"]
        if rule.get("min_price"):
            lines.append(f"  · 최소가: {rule['min_price']:,}원")
        if rule.get("max_price"):
            lines.append(f"  · 최대가: {rule['max_price']:,}원")
        lines.append(f"  · 신규={rule.get('notify_on_new')} / 가격하락={rule.get('notify_on_price_drop')}")
        print("\n".join(lines))
    return 0


def _make_alert(rule: dict[str, Any], item: dict[str, Any], event_type: str, previous: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "event_type": event_type,
        "rule_id": rule["id"],
        "rule_name": rule["name"],
        "market": item["market"],
        "market_label": MARKET_LABELS.get(item["market"], item["market"]),
        "article_key": item["article_key"],
        "title": item["title"],
        "price_text": item.get("price_text"),
        "price_numeric": item.get("price_numeric"),
        "previous_price_text": previous.get("price_text") if previous else None,
        "previous_price_numeric": previous.get("price_numeric") if previous else None,
        "link": item.get("link"),
        "location": item.get("location"),
        "seller": item.get("seller"),
        "detected_at": int(time.time()),
    }


def cmd_watch_check(args: argparse.Namespace) -> int:
    state = load_state()
    rules = state.get("rules") or []
    if args.name_or_id:
        rules = [r for r in rules if r["id"] == args.name_or_id or r["name"] == args.name_or_id]
    alerts: list[dict[str, Any]] = []
    last_seen = state.setdefault("last_seen", {})
    new_events = []
    checked_at = int(time.time())
    for rule in rules:
        intent = parse_search_intent(rule["query"], limit=int(rule.get("limit") or 12))
        if rule.get("min_price"):
            intent.min_price = rule["min_price"]
        if rule.get("max_price"):
            intent.max_price = rule["max_price"]
        items = [item.to_dict() for item in search_markets(intent)]
        matched = []
        for item in items:
            prev = last_seen.get(item["article_key"])
            is_new = prev is None
            is_price_drop = bool(prev and prev.get("price_numeric") and item.get("price_numeric") and item["price_numeric"] < prev["price_numeric"])
            event_type = None
            if is_new and rule.get("notify_on_new"):
                event_type = "new_listing"
            if is_price_drop and rule.get("notify_on_price_drop"):
                event_type = "price_drop"
            if event_type:
                alert = _make_alert(rule, item, event_type, prev)
                matched.append(alert)
                dedupe_key = f"{rule['id']}::{event_type}::{item['article_key']}::{item.get('price_numeric')}"
                known = {row.get('dedupe_key') for row in state.get('events', [])[-500:]}
                if dedupe_key not in known:
                    new_events.append({"dedupe_key": dedupe_key, **alert})
            last_seen[item["article_key"]] = {
                "rule_id": rule["id"],
                "price_text": item.get("price_text"),
                "price_numeric": item.get("price_numeric"),
                "title": item.get("title"),
                "link": item.get("link"),
                "last_seen_at": checked_at,
            }
        alerts.append({
            "rule": rule,
            "matched_count": len(matched),
            "matched": matched,
            "snapshot": {"count": len(items), "items": items[:5], "summary": _summarize(items)},
        })
    state["last_checked_at"] = checked_at
    state["events"] = (state.get("events") or []) + new_events
    state["events"] = state["events"][-1000:]
    save_state(state)
    payload = {
        "kind": "used-market-watch-check",
        "checked_at": checked_at,
        "alert_count": sum(row["matched_count"] for row in alerts),
        "alerts": alerts,
        "summary": {"rule_count": len(alerts), "rules_with_matches": sum(1 for row in alerts if row["matched_count"] > 0)},
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else render_watch_preview(payload))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="한국 중고거래 검색/브리핑/watch 스킬")
    sub = p.add_subparsers(dest="cmd", required=True)

    x = sub.add_parser("parse")
    x.add_argument("query")
    x.add_argument("--limit", type=int, default=12)
    x.set_defaults(func=cmd_parse)

    x = sub.add_parser("search")
    x.add_argument("query")
    x.add_argument("--limit", type=int, default=12)
    x.add_argument("--json", action="store_true")
    x.set_defaults(func=cmd_search)

    x = sub.add_parser("watch-add")
    x.add_argument("name")
    x.add_argument("query")
    x.add_argument("--limit", type=int, default=12)
    x.add_argument("--min-price", type=int)
    x.add_argument("--max-price", type=int)
    x.add_argument("--notify-on-new", action="store_true")
    x.add_argument("--notify-on-price-drop", action="store_true")
    x.add_argument("--json", action="store_true")
    x.set_defaults(func=cmd_watch_add)

    x = sub.add_parser("watch-list")
    x.add_argument("--json", action="store_true")
    x.set_defaults(func=cmd_watch_list)

    x = sub.add_parser("watch-check")
    x.add_argument("name_or_id", nargs="?")
    x.add_argument("--json", action="store_true")
    x.set_defaults(func=cmd_watch_check)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
