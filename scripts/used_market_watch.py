from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any

from market_client import search_markets
from models import MARKET_LABELS
from output_utils import (
    render_integration_plan,
    render_search_text,
    render_watch_events,
    render_watch_list,
    render_watch_plan,
    render_watch_preview,
)
from query_parser import parse_search_intent
from watch_intent import build_integration_bundle, parse_watch_request
from watch_store import (
    find_rule,
    load_config,
    load_state,
    make_rule,
    remove_rule,
    save_config,
    save_state,
    set_rule_enabled,
    upsert_rule,
)


def _blocked_seller_set(config: dict[str, Any]) -> set[str]:
    return {str(x).strip().lower() for x in (config.get("blocked_sellers") or []) if str(x).strip()}


def _is_blocked_seller(item: dict[str, Any], blocked_sellers: set[str]) -> bool:
    seller = str(item.get("seller") or "").strip().lower()
    return bool(seller and seller in blocked_sellers)


def _notification_window_reason(config: dict[str, Any], checked_at: int) -> str | None:
    window = (config or {}).get("notification_window") or {}
    if not window.get("enabled"):
        return None
    current_hour = time.localtime(checked_at).tm_hour
    start_hour = int(window.get("start_hour", 0))
    end_hour = int(window.get("end_hour", 24))
    if start_hour == end_hour:
        return None
    if start_hour < end_hour:
        allowed = start_hour <= current_hour < end_hour
    else:
        allowed = current_hour >= start_hour or current_hour < end_hour
    if allowed:
        return None
    return f"quiet-hours({start_hour:02d}-{end_hour:02d})"


def _tag_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for tag in row.get("tags") or []:
            counts[tag] = counts.get(tag, 0) + 1
    return counts


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


def _event_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        kind = row.get("event_type")
        if kind:
            counts[kind] = counts.get(kind, 0) + 1
    return counts


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


def cmd_watch_plan(args: argparse.Namespace) -> int:
    plan = parse_watch_request(args.request, default_limit=args.limit)
    payload = {"kind": "used-market-watch-plan", "rule": {k: v for k, v in plan.items() if k != "intent"}, "intent": plan["intent"]}
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else render_watch_plan(payload))
    return 0


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


def cmd_watch_upsert(args: argparse.Namespace) -> int:
    state = load_state()
    plan = parse_watch_request(args.request, default_limit=args.limit)
    rule, created = upsert_rule(state, plan)
    save_state(state)
    payload = {"saved": True, "created": created, "rule": rule, "intent": plan["intent"]}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        status = "등록" if created else "업데이트"
        print(render_watch_plan({"rule": rule, "intent": plan["intent"]}))
        print(f"\n{status} 완료")
    return 0


def cmd_integration_plan(args: argparse.Namespace) -> int:
    bundle = build_integration_bundle(args.request, default_limit=args.limit)
    if args.persist:
        state = load_state()
        rule, created = upsert_rule(state, bundle["parsed_plan"])
        save_state(state)
        bundle["persist"]["saved"] = True
        bundle["persist"]["created"] = created
        bundle["persist"]["rule"] = rule
    print(json.dumps(bundle, ensure_ascii=False, indent=2) if args.json else render_integration_plan(bundle))
    return 0


def cmd_watch_list(args: argparse.Namespace) -> int:
    state = load_state()
    if args.json:
        print(json.dumps(state, ensure_ascii=False, indent=2))
        return 0
    print(render_watch_list(state))
    return 0


def cmd_config_show(args: argparse.Namespace) -> int:
    config = load_config()
    print(json.dumps(config, ensure_ascii=False, indent=2) if args.json else json.dumps(config, ensure_ascii=False))
    return 0


def cmd_block_seller_add(args: argparse.Namespace) -> int:
    config = load_config()
    blocked = [x for x in (config.get("blocked_sellers") or []) if str(x).strip()]
    seller = str(args.seller).strip()
    if seller not in blocked:
        blocked.append(seller)
    config["blocked_sellers"] = blocked
    save_config(config)
    print(json.dumps({"updated": True, "blocked_sellers": blocked}, ensure_ascii=False, indent=2) if args.json else f"판매자 차단 추가: {seller}")
    return 0


def cmd_block_seller_remove(args: argparse.Namespace) -> int:
    config = load_config()
    seller = str(args.seller).strip().lower()
    blocked = [x for x in (config.get("blocked_sellers") or []) if str(x).strip().lower() != seller]
    config["blocked_sellers"] = blocked
    save_config(config)
    print(json.dumps({"updated": True, "blocked_sellers": blocked}, ensure_ascii=False, indent=2) if args.json else f"판매자 차단 해제: {args.seller}")
    return 0


def cmd_quiet_hours_set(args: argparse.Namespace) -> int:
    config = load_config()
    config["notification_window"] = {
        "enabled": not args.disable,
        "start_hour": int(args.start_hour),
        "end_hour": int(args.end_hour),
    }
    save_config(config)
    print(json.dumps(config["notification_window"], ensure_ascii=False, indent=2) if args.json else f"quiet hours 설정: {args.start_hour:02d}-{args.end_hour:02d} / {'비활성' if args.disable else '활성'}")
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
        "sale_status": item.get("sale_status"),
        "tags": item.get("tags") or [],
        "detected_at": int(time.time()),
    }


def _last_seen_key(rule: dict[str, Any], article_key: str) -> str:
    return f"{rule['id']}::{article_key}"


def _legacy_last_seen_row(last_seen: dict[str, Any], article_key: str) -> dict[str, Any] | None:
    row = last_seen.get(article_key)
    if isinstance(row, dict) and "_by_rule" in row:
        by_rule = row.get("_by_rule") or {}
        latest = row.get("_latest_rule_id")
        if latest and isinstance(by_rule.get(latest), dict):
            return by_rule[latest]
        for value in by_rule.values():
            if isinstance(value, dict):
                return value
        return None
    return row if isinstance(row, dict) and "price_numeric" in row else None


def _get_previous_seen(last_seen: dict[str, Any], rule: dict[str, Any], article_key: str) -> dict[str, Any] | None:
    scoped_key = _last_seen_key(rule, article_key)
    scoped = last_seen.get(scoped_key)
    if isinstance(scoped, dict):
        return scoped
    row = last_seen.get(article_key)
    if isinstance(row, dict) and "_by_rule" in row:
        scoped = (row.get("_by_rule") or {}).get(rule["id"])
        return scoped if isinstance(scoped, dict) else None
    return _legacy_last_seen_row(last_seen, article_key)


def _store_last_seen(last_seen: dict[str, Any], rule: dict[str, Any], item: dict[str, Any], checked_at: int) -> None:
    payload = {
        "rule_id": rule["id"],
        "price_text": item.get("price_text"),
        "price_numeric": item.get("price_numeric"),
        "title": item.get("title"),
        "link": item.get("link"),
        "location": item.get("location"),
        "seller": item.get("seller"),
        "sale_status": item.get("sale_status"),
        "tags": item.get("tags") or [],
        "last_seen_at": checked_at,
    }
    last_seen[_last_seen_key(rule, item["article_key"])] = payload
    row = last_seen.get(item["article_key"])
    by_rule = dict(row.get("_by_rule") or {}) if isinstance(row, dict) and "_by_rule" in row else {}
    by_rule[rule["id"]] = payload
    last_seen[item["article_key"]] = {
        "_latest_rule_id": rule["id"],
        "_by_rule": by_rule,
    }


def _dedupe_watch_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for item in items:
        article_key = item.get("article_key")
        dedupe_key = article_key or json.dumps(item, ensure_ascii=False, sort_keys=True)
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)
        deduped.append(item)
    return deduped


def _compact_last_seen(last_seen: dict[str, Any]) -> None:
    for key in [key for key in list(last_seen.keys()) if "::" in key]:
        article_key = key.split("::", 1)[1]
        if article_key in last_seen:
            del last_seen[key]


def cmd_watch_check(args: argparse.Namespace) -> int:
    state = load_state()
    state["config"] = load_config()
    config = state.get("config") or {}
    rules = state.get("rules") or []
    if args.name_or_id:
        rules = [r for r in rules if r["id"] == args.name_or_id or r["name"] == args.name_or_id]
    alerts: list[dict[str, Any]] = []
    last_seen = state.setdefault("last_seen", {})
    new_events = []
    suppressed_count = 0
    checked_at = int(time.time())
    quiet_reason = _notification_window_reason(config, checked_at)
    blocked_sellers = _blocked_seller_set(config)
    for rule in rules:
        if not rule.get("enabled", True):
            alerts.append({"rule": rule, "matched_count": 0, "matched": [], "snapshot": {"count": 0, "items": [], "summary": {"total": 0, "by_market": {}}}, "skipped": True})
            continue
        intent = parse_search_intent(rule["query"], limit=int(rule.get("limit") or 12))
        if rule.get("min_price"):
            intent.min_price = rule["min_price"]
        if rule.get("max_price"):
            intent.max_price = rule["max_price"]
        items = _dedupe_watch_items([item.to_dict() for item in search_markets(intent)])
        items = [item for item in items if not _is_blocked_seller(item, blocked_sellers)]
        matched = []
        rule_suppressed_count = 0
        known = {row.get('dedupe_key') for row in state.get('events', [])[-500:]}
        is_baseline_run = bool(config.get("first_run_skip_notifications", True) and not rule.get("baseline_established_at"))
        for item in items:
            prev = _get_previous_seen(last_seen, rule, item["article_key"])
            is_new = prev is None
            is_price_drop = bool(prev and prev.get("price_numeric") and item.get("price_numeric") and item["price_numeric"] < prev["price_numeric"])
            event_type = None
            if is_new and rule.get("notify_on_new"):
                event_type = "new_listing"
            if is_price_drop and rule.get("notify_on_price_drop"):
                event_type = "price_drop"
            if event_type:
                alert = _make_alert(rule, item, event_type, prev)
                if is_baseline_run:
                    alert["suppressed_reason"] = "baseline"
                    rule_suppressed_count += 1
                elif quiet_reason:
                    alert["suppressed_reason"] = quiet_reason
                    rule_suppressed_count += 1
                else:
                    matched.append(alert)
                    dedupe_key = f"{rule['id']}::{event_type}::{item['article_key']}::{item.get('price_numeric')}"
                    if dedupe_key not in known:
                        known.add(dedupe_key)
                        new_events.append({"dedupe_key": dedupe_key, **alert})
            _store_last_seen(last_seen, rule, item, checked_at)
        if is_baseline_run:
            rule["baseline_established_at"] = checked_at
        rule["last_snapshot"] = {"checked_at": checked_at, "summary": _summarize(items), "tag_counts": _tag_counts(items), "sample_items": items[:5]}
        suppressed_count += rule_suppressed_count
        alerts.append({
            "rule": rule,
            "matched_count": len(matched),
            "matched": matched,
            "suppressed_count": rule_suppressed_count,
            "snapshot": {"count": len(items), "items": items[:5], "summary": _summarize(items), "tag_counts": _tag_counts(items)},
        })
    _compact_last_seen(last_seen)
    state["last_checked_at"] = checked_at
    state["events"] = (state.get("events") or []) + new_events
    state["events"] = state["events"][-1000:]
    save_state(state)
    visible_alerts = [row for row in alerts if row["matched_count"] > 0] if args.alerts_only else alerts
    payload = {
        "kind": "used-market-watch-check",
        "checked_at": checked_at,
        "alert_count": sum(row["matched_count"] for row in alerts),
        "alerts": visible_alerts,
        "summary": {
            "rule_count": len(alerts),
            "rules_with_matches": sum(1 for row in alerts if row["matched_count"] > 0),
            "event_counts": _event_counts(new_events),
            "suppressed_count": suppressed_count,
        },
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else render_watch_preview(payload))
    return 0


def cmd_watch_events(args: argparse.Namespace) -> int:
    state = load_state()
    events = list(state.get("events") or [])
    if args.name_or_id:
        rule = find_rule(state, args.name_or_id)
        target_rule_id = rule.get("id") if rule else args.name_or_id
        events = [row for row in events if row.get("rule_id") == target_rule_id or row.get("rule_name") == args.name_or_id]
    events = events[-args.limit:]
    payload = {"kind": "used-market-watch-events", "count": len(events), "events": events}
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else render_watch_events(payload))
    return 0


def cmd_watch_enable(args: argparse.Namespace) -> int:
    state = load_state()
    rule = set_rule_enabled(state, args.name_or_id, True)
    if not rule:
        raise ValueError("해당 watch rule을 찾을 수 없습니다.")
    save_state(state)
    print(json.dumps({"updated": True, "rule": rule}, ensure_ascii=False, indent=2) if args.json else f"활성화 완료: {rule['name']}")
    return 0


def cmd_watch_disable(args: argparse.Namespace) -> int:
    state = load_state()
    rule = set_rule_enabled(state, args.name_or_id, False)
    if not rule:
        raise ValueError("해당 watch rule을 찾을 수 없습니다.")
    save_state(state)
    print(json.dumps({"updated": True, "rule": rule}, ensure_ascii=False, indent=2) if args.json else f"비활성화 완료: {rule['name']}")
    return 0


def cmd_watch_remove(args: argparse.Namespace) -> int:
    state = load_state()
    rule = remove_rule(state, args.name_or_id)
    if not rule:
        raise ValueError("해당 watch rule을 찾을 수 없습니다.")
    save_state(state)
    print(json.dumps({"removed": True, "rule": rule}, ensure_ascii=False, indent=2) if args.json else f"삭제 완료: {rule['name']}")
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

    x = sub.add_parser("watch-plan")
    x.add_argument("request")
    x.add_argument("--limit", type=int, default=12)
    x.add_argument("--json", action="store_true")
    x.set_defaults(func=cmd_watch_plan)

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

    x = sub.add_parser("watch-upsert")
    x.add_argument("request")
    x.add_argument("--limit", type=int, default=12)
    x.add_argument("--json", action="store_true")
    x.set_defaults(func=cmd_watch_upsert)

    x = sub.add_parser("integration-plan")
    x.add_argument("request")
    x.add_argument("--limit", type=int, default=12)
    x.add_argument("--persist", action="store_true")
    x.add_argument("--json", action="store_true")
    x.set_defaults(func=cmd_integration_plan)

    x = sub.add_parser("watch-list")
    x.add_argument("--json", action="store_true")
    x.set_defaults(func=cmd_watch_list)

    x = sub.add_parser("config-show")
    x.add_argument("--json", action="store_true")
    x.set_defaults(func=cmd_config_show)

    x = sub.add_parser("block-seller-add")
    x.add_argument("seller")
    x.add_argument("--json", action="store_true")
    x.set_defaults(func=cmd_block_seller_add)

    x = sub.add_parser("block-seller-remove")
    x.add_argument("seller")
    x.add_argument("--json", action="store_true")
    x.set_defaults(func=cmd_block_seller_remove)

    x = sub.add_parser("quiet-hours-set")
    x.add_argument("start_hour", type=int)
    x.add_argument("end_hour", type=int)
    x.add_argument("--disable", action="store_true")
    x.add_argument("--json", action="store_true")
    x.set_defaults(func=cmd_quiet_hours_set)

    x = sub.add_parser("watch-check")
    x.add_argument("name_or_id", nargs="?")
    x.add_argument("--alerts-only", action="store_true")
    x.add_argument("--json", action="store_true")
    x.set_defaults(func=cmd_watch_check)

    x = sub.add_parser("watch-events")
    x.add_argument("name_or_id", nargs="?")
    x.add_argument("--limit", type=int, default=10)
    x.add_argument("--json", action="store_true")
    x.set_defaults(func=cmd_watch_events)

    x = sub.add_parser("watch-enable")
    x.add_argument("name_or_id")
    x.add_argument("--json", action="store_true")
    x.set_defaults(func=cmd_watch_enable)

    x = sub.add_parser("watch-disable")
    x.add_argument("name_or_id")
    x.add_argument("--json", action="store_true")
    x.set_defaults(func=cmd_watch_disable)

    x = sub.add_parser("watch-remove")
    x.add_argument("name_or_id")
    x.add_argument("--json", action="store_true")
    x.set_defaults(func=cmd_watch_remove)
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
