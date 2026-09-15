# Upstream notes: `used-market-notifier`

이 스킬은 `tmp/used-market-notifier-upstream` 및 public repo `twbeatles/used-market-notifier`를 분석해, 다음 개념을 OpenClaw용으로 재구성했다.

## 유지 및 확장한 핵심 개념

- **지원 마켓 범위**: 당근마켓 / 번개장터 / 중고나라
- **가격 정규화**: `10만`, `2만5천`, `무료나눔` 같은 한국형 가격 파싱
- **8대 이모지 자동 태깅 (`auto_tagger.py`)**: `✨ A급`, `📦 풀박스`, `🔥 급처`, `💬 네고가능`, `📮 택포`, `🤝 직거래`, `✅ 정품`, `🎁 구성품포함`
- **판매자 문의 메시지 생성 (`message_templates.py`)**: 에이전트 환경에 맞춘 기본/네고/직거래/상태확인/플랫폼별 문의글 원클릭 템플릿
- **시세 통계 및 급매 감지**: 최저/최고가 외 전체 평균가(Avg), 중위가(Median) 통계 산출 및 시세 대비 25% 이상 저렴한 `🔥 시세이하` 매물 감지
- **가격 하락 상세화**: 단순 이전가가 아닌 인하폭(▼)과 할인율(%) 명시 (`100만원 → 85만원 (▼150,000원, -15.0%)`)
- **검색 후 필터링**: 가격 범위, 지역, 제외 키워드, 차단 판매자(`exclude_sellers`)
- **Playwright 수집 & Stealth**: 한국어 로케일, User-Agent, webdriver 우회 스크립트 적용
- **채팅/알림 친화 출력**: GUI 대신 text + JSON stdout

## 의도적으로 제거/축소한 것

- PyQt GUI 전체
- Telegram/Discord/Slack 직접 전송 (상위 OpenClaw 런타임이 채널 전송 담당)
- DB 기반 대시보드/백업/즐겨찾기 UI
- 복잡한 dual-engine orchestration

## 이 스킬에서의 재해석

- OpenClaw가 상위 레이어에서 메시징/cron을 담당하므로, 이 스킬은 **검색·브리핑·watch state 계산·메시지 템플릿 지원**에 집중한다.
- persistent state는 `data/watch-rules.json` 하나로 단순화했다.
- upstream scrapers의 title/link/article-id 파싱 감각을 가져오되, CLI용으로 최소한의 구조만 남겼다.

## upstream에서 특히 참고한 파일

- `README.md`
- `auto_tagger.py` (자동 태깅 규칙 및 이모지)
- `message_templates.py` (판매자 문의 템플릿 및 변수 치환)
- `monitor_engine.py`
- `models.py`
- `price_utils.py`
- `storage/stats.py` (시세 및 평균/중위 통계)
- `storage/filters.py` (판매자 차단)
- `scrapers/stealth.py`
- `scrapers/playwright_danggeun.py`
- `scrapers/playwright_bunjang.py`
- `scrapers/playwright_joonggonara.py`
