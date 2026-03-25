---
name: used-market-watch
description: Search, brief, and monitor Korean used-market listings across 당근마켓, 번개장터, and 중고나라. Use when the user wants 중고 매물 찾아줘, 당근/번장/중고나라 동시 검색, 아이폰/맥북 같은 물건의 신규 매물 감시, 가격하락 체크, 자연어 기반 한국 중고거래 브리핑, 자연어 watch rule 추가/수정, 최근 watch 이벤트 확인, 1시간마다/매일 아침 8시 같은 주기 표현이 포함된 감시 요청, or cron-friendly stdout/JSON monitoring output.
---

# Used Market Watch

한국 중고거래 매물을 **자연어 검색 / 채팅형 브리핑 / persistent watch rule / 신규·가격하락 체크 / 주기 해석 기반 운영 계획** 형태로 다루는 OpenClaw 스킬이다.

핵심 원칙:
- **chat-first**: 사람이 읽는 한국어 브리핑을 먼저 만든다.
- **json-ready**: cron/상위 레이어 연결용 JSON도 바로 뽑는다.
- **watch-state 단순화**: GUI/DB 대신 `data/watch-rules.json` 하나로 상태를 유지한다.
- **natural-language ops**: 검색과 감시 등록을 분리하지 않고 한 줄 한국어 요청에서 watch intent를 최대한 바로 해석한다.
- **plan-aware**: `1시간마다`, `30분마다`, `매일 아침 8시`, `브리핑해줘` 같은 운영 문장을 rule 메타와 실행 힌트로 변환한다.

## Commands

```bash
python scripts/used_market_watch.py parse "잠실에서 아이폰 15 프로 120만원 이하 당근 번장만 -깨짐"
python scripts/used_market_watch.py search "잠실에서 아이폰 15 프로 120만원 이하 당근 번장만 -깨짐"
python scripts/used_market_watch.py watch-plan "아이폰 15 프로 1시간마다 신규만 감시해줘"
python scripts/used_market_watch.py watch-upsert "맥북 에어 가격 내려가면 알려줘"
python scripts/used_market_watch.py watch-upsert "플스5 매일 아침 8시에 브리핑해줘"
python scripts/used_market_watch.py watch-list
python scripts/used_market_watch.py watch-check --alerts-only --json
python scripts/used_market_watch.py watch-events --limit 20
```

## Runtime notes

```bash
pip install playwright
python -m playwright install chromium
python -m pytest tests -q
```
