---
name: used-market-watch
description: Search, brief, and monitor Korean used-market listings across 당근마켓, 번개장터, and 중고나라. Use when the user wants 중고 매물 찾아줘, 당근/번장/중고나라 동시 검색, 아이폰/맥북 같은 물건의 신규 매물 감시, 가격하락 체크, 자연어 기반 한국 중고거래 브리핑, or cron-friendly stdout/JSON monitoring output.
---

# Used Market Watch

한국 중고거래 매물을 **자연어 검색 / 채팅형 브리핑 / persistent watch rule / 신규·가격하락 체크** 형태로 다루는 OpenClaw 스킬이다.

핵심 원칙:
- **chat-first**: 사람이 읽는 한국어 브리핑을 먼저 만든다.
- **json-ready**: cron/상위 레이어 연결용 JSON도 바로 뽑는다.
- **watch-state 단순화**: GUI/DB 대신 `data/watch-rules.json` 하나로 상태를 유지한다.
- **upstream 계승**: `used-market-notifier`의 마켓 범위, 가격 파싱, Playwright 검색 감각, 신규/가격하락 개념을 OpenClaw용 CLI로 재구성했다.

## Source dependency / analysis

분석 기준 upstream:
- `tmp/used-market-notifier-upstream`
- public repo: `twbeatles/used-market-notifier`

핵심 참고 내용은 `references/upstream-notes.md`에 정리돼 있다.

## Scripts

### 1) 자연어 파싱 확인
```bash
python skills/used-market-watch/scripts/used_market_watch.py parse "잠실에서 아이폰 15 프로 120만원 이하 당근 번장만 -깨짐"
```

### 2) 원샷 검색 / 브리핑
```bash
python skills/used-market-watch/scripts/used_market_watch.py search "잠실에서 아이폰 15 프로 120만원 이하 당근 번장만 -깨짐"
python skills/used-market-watch/scripts/used_market_watch.py search "맥북 에어 m2 중고나라 포함" --json
```

출력 특징:
- 마켓별 개수 요약
- 대표 매물 리스트
- 링크 포함
- text / JSON 선택 가능

### 3) watch rule 추가
```bash
python skills/used-market-watch/scripts/used_market_watch.py watch-add "아이폰 감시" "아이폰 15 프로 120만원 이하 당근 번장" --notify-on-new --notify-on-price-drop
```

### 4) watch rule 목록
```bash
python skills/used-market-watch/scripts/used_market_watch.py watch-list
python skills/used-market-watch/scripts/used_market_watch.py watch-list --json
```

### 5) watch 점검
```bash
python skills/used-market-watch/scripts/used_market_watch.py watch-check
python skills/used-market-watch/scripts/used_market_watch.py watch-check --json
python skills/used-market-watch/scripts/used_market_watch.py watch-check "아이폰 감시"
```

점검 결과:
- 신규 매물(`new_listing`)
- 가격하락(`price_drop`)
- 각 rule별 snapshot 요약
- cron/메시징 레이어에서 바로 쓸 수 있는 stdout JSON

## Runtime notes

필수 준비:
```bash
pip install playwright
python -m playwright install chromium
```

테스트:
```bash
python -m pytest skills/used-market-watch/tests -q
```

## Stored files

- `data/watch-rules.json`: watch rule + last_seen + dedupe event state
- `references/upstream-notes.md`: upstream 분석 메모
- `dist/used-market-watch.skill`: 배포용 패키지 아티팩트

## Recommended workflow

1. 사용자가 한 줄로 원하는 물건/가격/마켓을 말하면 `search`로 먼저 브리핑한다.
2. 반복 추적이 필요하면 `watch-add`로 규칙을 저장한다.
3. heartbeat/cron에서는 `watch-check --json` 또는 기본 text 출력으로 신규/가격하락만 집계한다.
4. 상위 레이어(OpenClaw)가 텔레그램/디스코드 전달을 담당한다.

## Current limitations

- 각 마켓 DOM 구조 변경에 민감하다.
- 로그인 필요/봇 차단이 강한 상황에서는 결과가 줄 수 있다.
- 중고나라는 네이버 검색 결과 기반이라 가격 정보가 제한적일 수 있다.
- 현재는 Playwright 단일 경로이며 Selenium fallback은 넣지 않았다.
