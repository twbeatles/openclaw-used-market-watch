# used-market-watch

당근마켓, 번개장터, 중고나라를 대상으로 **중고 매물 검색 / 채팅형 브리핑 / 저장형 감시 규칙 / 신규 매물 / 가격하락 체크**를 수행하는 OpenClaw 스킬입니다.

이 스킬은 `used-market-notifier`의 핵심 아이디어를 OpenClaw 운영 흐름에 맞게 다시 묶은 버전입니다.

- 자연어로 검색하고
- 결과를 바로 브리핑하고
- 감시 규칙을 저장하고
- `watch-check`를 cron/heartbeat/메시징에 연결해 반복 운영하는 데 초점을 맞췄습니다.

## 지원 마켓

- 당근마켓
- 번개장터
- 중고나라

## 어떤 요청을 잘 받나

### 신규 매물 감시형

```text
아이폰 15 프로 1시간마다 신규만 감시해줘
```

해석 포인트:
- 감시 대상: 아이폰 15 프로
- 주기: 1시간마다
- 알림 조건: 신규만
- 출력 성격: 알림(alert)

### 가격하락 알림형

```text
맥북 에어 가격 내려가면 알려줘
```

해석 포인트:
- 감시 대상: 맥북 에어
- 주기: 수동 또는 상위 스케줄러 연결
- 알림 조건: 가격하락만
- 출력 성격: 알림(alert)

### 정기 브리핑형

```text
플스5 매일 아침 8시에 브리핑해줘
```

해석 포인트:
- 감시 대상: 플스5
- 주기: 매일 08:00
- 알림 조건: 신규 + 가격하락 기본
- 출력 성격: 브리핑(briefing)
- cron 예시: `0 8 * * * ... watch-check "플스5 감시" --json`

## 설치

```bash
clawhub install used-market-watch
```

## 준비

```bash
pip install playwright
python -m playwright install chromium
```

## 빠른 시작

```bash
python scripts/used_market_watch.py parse "잠실에서 아이폰 15 프로 120만원 이하 당근 번장만 -깨짐"
python scripts/used_market_watch.py search "잠실에서 아이폰 15 프로 120만원 이하 당근 번장만 -깨짐"
python scripts/used_market_watch.py watch-plan "아이폰 15 프로 1시간마다 신규만 감시해줘"
python scripts/used_market_watch.py watch-upsert "아이폰 15 프로 1시간마다 신규만 감시해줘"
python scripts/used_market_watch.py watch-check --alerts-only --json
```

## 운영 패턴 추천

### 검색 후 감시 등록

1. `search`로 검색 품질과 키워드를 먼저 확인
2. 원하는 조건이 맞으면 `watch-upsert`로 저장
3. 이후는 scheduler가 `watch-check`만 주기적으로 실행

### 하루 1회 브리핑

```bash
python scripts/used_market_watch.py watch-plan "플스5 매일 아침 8시에 브리핑해줘"
python scripts/used_market_watch.py watch-upsert "플스5 매일 아침 8시에 브리핑해줘"
python scripts/used_market_watch.py watch-check "플스5 감시" --json
```

## cron 연결 힌트

`watch-plan`은 해석 결과와 함께 다음 정보를 제공합니다.

- 실행 주기
- 권장 실행 명령
- cron 예시

예:

```text
watch 규칙 해석: 플스5 감시
- 실행 주기: 매일 08:00
- 권장 실행: python skills/used-market-watch/scripts/used_market_watch.py watch-check "플스5 감시" --json
- cron 예시: 0 8 * * * python skills/used-market-watch/scripts/used_market_watch.py watch-check "플스5 감시" --json
```

## 테스트

```bash
python -m pytest tests -q
```

## 한계

- 실검색은 Playwright와 각 마켓 DOM 구조에 의존합니다.
- 로그인/봇 차단이 강한 경우 결과가 줄 수 있습니다.
- 중고나라는 메타데이터가 제한적일 수 있습니다.
- 현재는 Playwright 단일 경로입니다.
