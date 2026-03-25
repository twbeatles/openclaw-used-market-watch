# used-market-watch

OpenClaw skill for monitoring Korean used marketplaces.

Supported marketplaces:
- 당근마켓
- 번개장터
- 중고나라

## Features
- natural-language Korean query parsing
- one-shot search / briefing
- persistent watch rules
- new listing / price-drop checks
- chat-friendly text and JSON output
- marketplace narrowing and Korean price parsing

## Quick start
```bash
python scripts/used_market_watch.py parse "잠실에서 아이폰 15 프로 120만원 이하 당근 번장만 -깨짐"
python scripts/used_market_watch.py search "잠실에서 아이폰 15 프로 120만원 이하 당근 번장만 -깨짐"
python scripts/used_market_watch.py watch-add "아이폰 감시" "아이폰 15 프로 120만원 이하 당근 번장" --notify-on-new --notify-on-price-drop
python scripts/used_market_watch.py watch-check --json
```

## Install
```bash
clawhub install used-market-watch
```
