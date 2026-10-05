# 한국 Trend Insight PoC

2026-10-05 실제 수집 결과를 포함합니다. **NOW는 공식 RSS HTTP 수집부터 SQLite·편집 결과 파일까지 실행했습니다. FASHION의 실데이터 수집과 외부 LLM API 자동 호출은 인증키가 없어 실행하지 못했습니다.** 전체 자동화 성공이라고 표시하지 않습니다.

오늘 한국 Google 피드에서 실제 관측한 키워드는 kbo, 김태규, 실종자, 전국노래자랑, 리센느, 유해진, 카를로스 알카라스, 대전문화방송, 띠별 운세, 폭격기입니다. 원천 XML과 수집 시각·URL을 보존했습니다. 첫 수집이므로 전일/지속 상승/새 트렌드 지표는 null입니다. 빈 칸을 AI로 채우지 않았습니다.

## 검증 범위

| 경로 | 실행 결과 | 판단 |
|---|---|---|
| Google 한국 Trending Now 공식 RSS | HTTP 200, 실제 10개 항목, XML 20,180 bytes | 일일 관측 후보. 여러 날 안정성 미검증 |
| NAVER API HUB Search Trend | 최신 공식 요청 코드·파서 작성, 실호출 0회 | API 키 발급 후 우선 검증 |
| NAVER Shopping Insight | 공식 요청/파서 모듈 작성, 카테고리 미설정·미호출 | Phase 1 자동 실행에 포함하지 않음 |
| Deterministic 계산 | 실제 RSS에는 지원되지 않는 값 null; 알고리즘은 테스트 통과 | 상대지수 이력이 확보돼야 증가율 검증 가능 |
| LLM 편집 | 이 Work 세션의 LLM으로 입력 JSON을 읽고 구조화 초안 작성·가져오기 | 실제 편집 결과이며 외부 API 자동 호출 검증과 다름 |
| 외부 OpenAI API | Responses/Structured Outputs 어댑터, 캐시·사용량 기록 구현 | 인증키 부재로 실호출 미검증 |
| 채널 출력 | Daily Brief/Instagram/Blog/Website/Newsletter 파일 생성 | 독립 초안, 자동 게시 없음 |

**중요한 기획 수정:** 네이버 Search Trend는 지정한 키워드의 상대 검색 관심을 추적합니다. 패션 전체 인기 키워드를 자동 발견하는 API가 아닙니다. Shopping Insight의 클릭 지수도 검색량이나 판매량이 아닙니다. NOW 피드 역시 전체 인기 검색어 순위표가 아닙니다.

## 실행

Python 3.11 이상, 표준 라이브러리만 사용합니다. 외부 패키지·Playwright·비공식 scraping 라이브러리·클라우드 인프라를 요구하지 않습니다.

프로젝트 디렉터리에서:

```bash
python -m pip install -r requirements.txt
# 첨부한 실제 수집 XML 재생: 네트워크와 외부 LLM 비용 없음
python src/run.py --offline --llm-file src/llm/work_session_editorial.json
python -m unittest discover -s tests -v
# 새 RSS 1회 HTTP 수집 + DB 저장 + 계산 + 편집 전 기초 보고서
python src/run.py
```

`--offline`은 원래 수집 시각/날짜를 유지합니다. 과거 데이터를 오늘 데이터로 재표시하지 않습니다. 제공된 Work 편집 파일은 해당 입력 해시에서만 가져올 수 있습니다. 다른 날/다른 데이터에는 재사용할 수 없습니다.

네이버 신청·발급: [NCP API HUB Application](https://guide.ncloud-docs.com/docs/apihub-application). 가입 및 약관 동의는 사용자 계정에서 진행합니다. HUB용 키와 구 개발자센터용 키는 다릅니다. 키는 채팅에 보내지 말고 실행 환경에 설정하세요. `.env.example`은 참고용이며 자동으로 로딩하지 않습니다.

```bash
export NAVER_HUB_CLIENT_ID='본인의_HUB_Client_ID'
export NAVER_HUB_CLIENT_SECRET='본인의_HUB_Client_Secret'
python src/run.py
# 외부 API 편집까지 실행할 때만 추가 설정
export OPENAI_API_KEY='본인의_OpenAI_API_key'
export OPENAI_MODEL='gpt-4.1-mini'
python src/run.py --llm-api
```

Search Trend는 `config/watchlist.json`의 패션 키워드 그룹 5개를 대상으로 어제까지 61일을 요청합니다. 오늘의 불완전한 검색 지수를 전일 완성값과 비교하지 않습니다. FASHION 보고 기간은 어제, NOW는 오늘 수집 피드이므로 출력에 각각 날짜를 구분합니다. 현재 watchlist는 아우터/가디건 시드이며 패션 전 카테고리를 대표하지 않습니다.

쇼핑 모듈은 runner에 연결하지 않았습니다. `shopping_category`에 실제 확인된 네이버 카테고리 코드를 넣고 별도 실호출 검증 후 연결해야 합니다. 카테고리 코드나 순위를 임의 생성하지 않았습니다.

## 구조와 산출물

- `src/collectors`: 공식 Google RSS, NAVER HUB 요청/파싱
- `src/processors`: SQLite 수집 실행·키워드·스냅샷 저장
- `src/analytics`: deterministic 지표, alias 기반 교차 신호
- `src/llm`: 근거 참조 스키마, 숫자/없는 신호 방지 검증, 선택적 API, Work 편집 표본
- `src/outputs`: 변경 불가능한 근거값과 해석을 분리하여 출력
- `config/watchlist.json`: 사람이 지정한 관측 대상과 alias. 실제 관측 데이터가 아님
- `data/raw`: 실제 RSS/XML·HTTP 수집 메타데이터
- `data/processed/normalized.json`: 정규화한 실제 관측
- `data/trends.sqlite3`: 실제 PoC DB
- `output/2026-10-05/raw`: 해당 보고 날짜의 원천 자료·네이버 준비 요청
- `output/2026-10-05/metrics`: 계산 결과 및 압축 LLM 입력
- `output/2026-10-05/insight.json`: 모델/경로/사용량/해시/구조화 편집
- `output/2026-10-05/{daily_brief,instagram,blog,newsletter,website}.md`
- `output/2026-10-05/website.json`: UI 없는 데이터 중심 웹 콘텐츠 자료
- `docs`: 출처/지표/LLM/제약/DB/정기 운영 설계

## API 제한·위험

2026-10-05 공식 확인 기준, 네이버 HUB는 Search Trend와 Shopping Insight 각각 월 최대 50,000건을 안내합니다. 계정의 설정 한도는 더 작을 수 있습니다. 구 개발자센터의 일 1,000회 제한을 HUB 제한으로 혼용하지 않습니다. 신규 신청은 2026-07-31부터 HUB에서만 가능하며, 기존 개발자센터 키 지원 종료 예정은 2027-06-30입니다. 한시 무료 정책과 향후 유료화 계획을 확인했으므로 영구 무료라고 가정하지 않습니다.

Google Trends API는 Alpha 신청 방식입니다. 승인 계정이 없어 사용하지 않았습니다. 공식 RSS export를 사용하며 호출 제한 숫자는 문서에서 확인하지 못했습니다. 이 PoC는 각 소스를 한 번만 요청하고 자동 재시도·우회는 없습니다. Google 데이터 출처 표시와 Terms of Service를 준수해야 합니다. 재배포·장기 보존·B2B 판매 허용 여부는 별도 약관 검토 대상이며 판매 권리가 확인된 것으로 표시하지 않습니다.

## LLM 사용 경계와 비용

수집/정규화/DB/순위/증감/alias 판단에는 LLM이 없습니다. 계산이 끝난 데이터와 근거만 편집 모델에 전달합니다. 뉴스 본문을 가져오거나 LLM에게 사실 배경 검색을 맡기지 않습니다. 모델은 Daily Brief와 각 채널을 한 번의 구조화 응답 안에서 서로 다른 문장으로 작성합니다.

이번 외부 OpenAI API 호출은 0회입니다. Work 세션의 토큰/비용/세부 모델명은 확인할 수 없어 null/미보고로 기록했습니다. **시스템이 LLM을 무료로 자동 실행했다는 뜻은 아닙니다.** 반복 자동 운영은 사용자 API 키가 필요합니다.

비용 시나리오: GPT-4.1 mini 공식 표준 단가 입력 $0.40/백만, 출력 $1.60/백만 토큰을 적용하면, 입력 6,000 + 출력 3,000 토큰의 하루 1회 호출은 $0.0072/일, 30일 $0.216입니다. 이는 가정이며 실제 사용량 예측이나 이번 청구액이 아닙니다. 사용량은 API 응답의 usage로 기록합니다. 다른 모델 단가는 자동 추정하지 않습니다. 입력은 원천 뉴스 없이 최대 30개 NOW·5개 FASHION 그룹, 출력 상한은 6,000 토큰이며 초과/거절/미완료 시 자동 재호출하지 않습니다. 무료 RSS·현재 HUB 정책 외에 서버/전기/세금은 별도입니다.

## 정기 실행 설계

로컬 PC/저가 서버의 스케줄러 → 수집 → 검증 → SQLite → 날짜별 지표 → 선택적 LLM → 파일 출력. 설계만 제공했고 스케줄러를 등록하지 않았습니다. 성공한 NOW부터 고정 한국 시간에 관측하고, 네이버는 키 설정 후 실검증한 다음 추가합니다. 처음에는 사람이 초안을 검토하고 자동 게시는 도입하지 않습니다. 자세한 실패 처리·운영 전 요구사항은 `docs/limitations.md`를 참고하세요.

## 최종 판단

1. NOW 일일 관측은 실제 확보 가능성이 확인됐지만 장기 안정성은 미검증입니다.
2. FASHION은 공식 API 경로가 적합하나 이번에는 실데이터를 얻지 못했습니다. 키워드 발견 서비스보다 지정 키워드 모니터링으로 시작해야 합니다.
3. 정량 지표는 구현·테스트됐지만 실제 상대지수 검증이 남았습니다. RSS 구간값만으로 정확한 성장률을 만들 수 없습니다.
4. 근거값을 코드가 출력하고 LLM이 해석만 쓰는 콘텐츠 파이프라인은 실행했습니다. 숫자 검증만으로 의미의 정확성까지 보장되지 않아 편집 검토가 필요합니다.
5. 다음 검증은 HUB 키로 Search Trend 5개 그룹을 실제 수집하고, NOW를 최소 7일 같은 시각에 관측하는 것입니다. 장기 모니터링과 수익화는 그 결과로 판단합니다.
