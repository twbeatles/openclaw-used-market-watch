# used-market-watch

당근마켓, 번개장터, 중고나라를 대상으로 **중고 매물 검색 / 브리핑 / 지속 감시 / 신규 매물 / 가격하락 체크**를 수행하는 OpenClaw 스킬입니다.

이 스킬은 upstream GUI 앱 `used-market-notifier`의 핵심 개념을 OpenClaw에 맞게 재구성한 것입니다. 즉:
- 자연어로 찾고
- 결과를 브리핑하고
- 규칙을 저장해 반복 감시하고
- cron/메시징에 연결해 새 매물만 받아보는
흐름에 맞춰 설계했습니다.

## 지원 마켓
- 당근마켓
- 번개장터
- 중고나라

## 핵심 기능
- 한국어 자연어 질의 파싱
- 원샷 검색 / 브리핑
- persistent watch rule
- 신규 매물 감지
- 가격하락 감지
- `watch-plan`: 자연어 감시 요청 해석 미리보기
- `watch-upsert`: 자연어 요청으로 watch rule 저장/업데이트
- `watch-events`: 최근 이벤트 피드 조회
- `watch-enable` / `watch-disable` / `watch-remove`
- `watch-check --alerts-only`: cron/chat 알림용 출력
- chat-friendly text / JSON 출력

## 자연어 예시
- `잠실에서 아이폰 15 프로 120만원 이하 당근 번장만 찾아줘`
- `맥북 에어 m2 중고나라 포함해서 검색해줘`
- `아이폰 15 프로 신규 매물만 감시해줘`
- `맥북 에어 가격 내려가면 알려주는 규칙으로 저장해줘`
- `플스5 매물 1시간마다 체크할 감시 계획 보여줘`

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
python scripts/used_market_watch.py watch-plan "아이폰 15 프로 신규 매물만 감시해줘" --json
python scripts/used_market_watch.py watch-upsert "아이폰 15 프로 신규 매물만 감시해줘"
python scripts/used_market_watch.py watch-check --alerts-only --json
```

## 운영 팁
- 먼저 `search`로 결과 감을 본 뒤 `watch-upsert`로 감시 규칙을 저장하는 흐름이 안정적입니다.
- `watch-plan`은 실제 저장 전 미리보기용입니다.
- `watch-check --alerts-only`는 텔레그램/디스코드/cron에 바로 연결하기 좋습니다.

## 테스트
```bash
python -m pytest tests -q
```

## 한계
- 실검색은 Playwright와 각 마켓 DOM 구조에 의존합니다.
- 로그인/봇 차단이 강한 경우 결과가 줄 수 있습니다.
- 중고나라는 메타데이터가 제한적일 수 있습니다.
- 현재는 Playwright 단일 경로입니다.
