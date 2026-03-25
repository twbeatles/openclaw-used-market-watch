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
- 마켓 범위 축소
  - 예: `당근만`, `번장만`, `중고나라 포함`
- 가격 조건 해석
  - 예: `120만원 이하`, `80만 원 이하`
- 원샷 검색 / 브리핑
- persistent watch rule
- 신규 매물 감지
- 가격하락 감지
- chat-friendly text / JSON 출력
- 한국형 가격 문자열 파싱

## 이 스킬이 잘 맞는 요청 예시

- `잠실에서 아이폰 15 프로 120만원 이하 당근 번장만 찾아줘`
- `맥북 에어 m2 중고나라 포함해서 검색해줘`
- `플스5 신규 매물 계속 감시해줘`
- `갤럭시 S24 가격 내려간 매물만 보고 싶어`
- `아이폰, 맥북, 카메라 매물 모니터링 파이프라인 만들고 싶어`

## 설치

### ClawHub로 설치

```bash
clawhub install used-market-watch
```

### 로컬 실행 전 준비

```bash
pip install playwright
python -m playwright install chromium
```

## 빠른 시작

### 1) 자연어 파싱 확인

```bash
python scripts/used_market_watch.py parse "잠실에서 아이폰 15 프로 120만원 이하 당근 번장만 -깨짐"
```

### 2) 원샷 검색 / 브리핑

```bash
python scripts/used_market_watch.py search "잠실에서 아이폰 15 프로 120만원 이하 당근 번장만 -깨짐"
```

### 3) JSON 출력

```bash
python scripts/used_market_watch.py search "맥북 에어 m2 중고나라 포함" --json
```

### 4) watch rule 추가

```bash
python scripts/used_market_watch.py watch-add \
  "아이폰 감시" \
  "아이폰 15 프로 120만원 이하 당근 번장" \
  --notify-on-new --notify-on-price-drop
```

### 5) watch 목록

```bash
python scripts/used_market_watch.py watch-list
python scripts/used_market_watch.py watch-list --json
```

### 6) watch 점검

```bash
python scripts/used_market_watch.py watch-check
python scripts/used_market_watch.py watch-check --json
python scripts/used_market_watch.py watch-check "아이폰 감시"
```

## 출력 특징

기본 출력은 사람이 읽기 쉬운 한국어 브리핑입니다.
필요하면 `--json`으로:
- 검색 결과
- watch snapshot
- 신규 매물 이벤트
- 가격하락 이벤트
를 구조화해서 받을 수 있습니다.

즉, 텔레그램/디스코드 알림, cron 점검, 상위 브리핑 워크플로우에 바로 붙이기 좋습니다.

## 자연어 입력 예시

잘 되는 형식 예시:
- `잠실에서 아이폰 15 프로 120만원 이하 당근 번장만 -깨짐`
- `맥북 에어 m2 중고나라 포함`
- `서초에서 플레이스테이션 5 40만원 이하 당근만`
- `후지 x100 시리즈 번장 포함 -고장 -파손`

주로 해석하는 요소:
- 물건 키워드
- 지역 힌트
- 최대 가격
- 마켓 제한
- 제외 키워드

## 저장 파일

- `data/watch-rules.json`: watch rule, last_seen, dedupe 이벤트 상태
- `references/upstream-notes.md`: upstream에서 어떤 개념을 가져왔는지 정리한 메모

## 테스트

```bash
python -m pytest tests -q
```

## 한계

- 실검색은 Playwright와 각 마켓 DOM 구조에 의존하므로, 사이트 변경 시 보정이 필요할 수 있습니다.
- 로그인이나 봇 차단이 강한 경우 결과 수가 줄 수 있습니다.
- 중고나라는 네이버 검색 기반 메타데이터가 섞일 수 있어 정보가 제한적일 수 있습니다.
- 현재는 Playwright 단일 경로이며 Selenium fallback까지는 옮기지 않았습니다.
- 이번 버전은 비네트워크 로직 위주로 테스트했으며, 실네트워크 smoke는 환경에 따라 별도 점검이 좋습니다.

## 왜 이 스킬이 유용한가

이 스킬은 단순 검색기가 아니라,
- **원하는 물건을 찾는 도구**이면서
- **새 매물을 놓치지 않는 감시기**이고
- **가격하락 이벤트만 뽑아보는 브리핑 도구**입니다.

즉 OpenClaw 안에서 “중고거래 모니터링 자동화”를 만들기 위한 기반 엔진으로 쓰기 좋습니다.
