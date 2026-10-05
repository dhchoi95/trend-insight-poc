# 데이터 소스 조사 — 2026-10-05

| 소스 | 의미 | 확보/준비한 필드 | 이번 상태 |
|---|---|---|---|
| Google 한국 Trending Now RSS | 공식 급상승 피드가 반환한 항목 | title, approx_traffic, pubDate, 관련 뉴스 메타데이터 | 실제 10개 확보 |
| NAVER HUB Search Trend | 지정 그룹의 기간별 상대 검색 관심 | results.title/keywords, data.period/ratio | 인증키 없어 실호출 미검증 |
| NAVER HUB Shopping keywords | 지정 카테고리·키워드의 상대 쇼핑 클릭 관심 | results, data.period/ratio | 카테고리·인증 미설정 |
| Google Trends API | 기간별 검색 관심 Alpha API | 승인 후 공식 사양에 맞춰 추가 | 미승인·미구현 |

## Google

- HTTP GET `https://trends.google.com/trending/rss?geo=KR`
- query: `geo=KR`. 인증·JS·Playwright 불필요. XML namespace `https://trends.google.com/trending/rss`.
- 파서 위치: `channel/item/title`, `ht:approx_traffic`, `pubDate`, `ht:news_item`.
- 실제 HTTP 200, 20,180 bytes, 수집시각 `2026-10-05T09:38:12.832777+00:00` (=한국 18:38:12).
- 수집된 `500+`, `1000+`, `2000+`, `5000+`는 구간 표시. lower_bound는 표시값의 구간 하한 파싱이며 실제 횟수 추정값이 아님. 비율 계산에 사용하지 않음.
- `source_position`은 XML 배열 위치. 공식 rank는 null. `pubDate`는 소스 게시 시각이며 `trend_started_at`에 복사하지 않음.
- 이번 RSS에는 상승률, active/ended, 관련 검색어 필드가 없음. 관련 뉴스 제목과 관련 검색어는 다름.
- 반환 항목 10개를 확보한 것이며 TOP10 전체 인기 순위/고정 최대10개라는 주장 아님. pagination/과거7일 export는 이 경로에서 확인하지 못함.
- Trending Now 웹 기능은 시간대/필터/CSV/RSS export가 있지만 웹 화면의 모든 필드가 RSS에 포함된다고 가정하지 않음. 약 10분 갱신 안내는 하루 1회 관측으로 모든 이벤트를 포착한다는 보장 아님.
- 이번엔 RSS를 원천 화면으로 보고 XML→파싱을 교차 검증. 별도 Google 웹 화면과의 독립 대조는 미실시.
- [Trending Now 공식 도움말](https://support.google.com/trends/answer/3076011?hl=en)
- [Alpha 상태·신청](https://developers.google.com/search/apis/trends)
- [공식 재사용·출처 표시 안내](https://support.google.com/trends/answer/4365538?hl=en): Google Terms 적용, Google 출처 표시 요구. 본 PoC는 비공식 endpoint/pytrends/우회 사용 안 함.

## NAVER API HUB 이관

[공식 공지](https://developers.naver.com/notice/article/32530): HUB 정식 출시 2026-06-25, 구 개발자센터 신규 신청 차단 2026-07-31, 기존 신청 API 지원 종료 예정 2027-06-30. 신규 시스템은 HUB용 인증 사용. 네이버 쇼핑 상품검색 API의 종료와 Shopping Insight의 이관은 서로 다른 사안이며 혼용하지 않음.

[Application 공식 가이드](https://guide.ncloud-docs.com/docs/apihub-application): Search Trend와 Shopping Insight 월 최대 각각 50,000건, 일/월 사용자 한도 설정 지원. 공식 플랫폼 전체 RPS는 개인 호출 허용량이 아니므로 저빈도 PoC에 사용하지 않음. 가입 시 콘솔 약관 동의 필요. 기존 키는 이 프로젝트에서 지원하지 않음.

### Search Trend

POST `https://naverapihub.apigw.ntruss.com/search-trend/v1/search`

헤더:
- `X-NCP-APIGW-API-KEY-ID`: HUB Client ID
- `X-NCP-APIGW-API-KEY`: HUB Client Secret
- `Content-Type: application/json`

Body: `startDate`, `endDate`, `timeUnit: date`, `keywordGroups`(최대5 그룹, 그룹당 최대20 검색어). 선택 필터 device/gender/ages는 현재 사용하지 않음. 코드의 키워드 그룹은 아우터·가디건을 살피기 위한 사람 지정 시드이며 인기 키워드 목록을 발급받는 기능이 아님.

응답 `data.period/ratio`의 ratio는 요청 내 상대값. 최대값을 기준으로 정규화되므로 요청 기간/그룹/필터가 달라진 두 응답의 절대 ratio를 직접 비교하지 않음. 이번 runner는 어제 종료하는 61일 요청 안에서만 전일/7일/30일 지표를 계산함. pagination 없음. 전체 분야 랭킹 API로 사용 불가.

[공식 API 문서](https://api.ncloud-docs.com/docs/naver-api-hub-search-trend)

### Shopping Insight

POST `https://naverapihub.apigw.ntruss.com/shopping/v1/category/keywords`

Body: 날짜/timeUnit, 실제 확인한 `category`, `keyword` 배열 최대5개, 항목 `{name,param:[키워드]}`. 현재 공식 HUB 문서상 param은 키워드 1개. 키워드 묶음인 Search Trend와 다름. 인증 헤더는 동일. `ratio`는 쇼핑 검색 클릭 추이 지수이며 판매·거래·정확한 검색량 아님. 공식 상품카테고리 ID는 네이버 쇼핑 URL의 cat_id 등에서 확인한 뒤 기록해야 함. 현재 null로 보존.

[공식 Shopping keywords 문서](https://api.ncloud-docs.com/docs/naver-api-hub-shopping-insight-keywords)

## PLACE·MONEY 확장

이번 Phase 1에 구현/관측하지 않음. 검증된 Search Trend 그룹 설정을 각각 지역/장소 및 금융 키워드로 확장할 수 있음. 지역검색 API의 업체 검색 결과를 장소 검색 관심도로 오해하지 않음. 금융 키워드 관심과 주가/투자 성과는 별개의 데이터임.

## 운영·약관 기록

인증키를 파일/에러 메시지에 저장하지 않음. 자동 재시도 없음; 403/429/인증오류는 우회 없이 실패로 처리. 공식 API/export 경로만 사용하므로 robots 허용 여부를 비공식 스크래핑 권한으로 해석하지 않음. 이번엔 전체 계약/콘솔별 약관을 법적으로 판정하지 않았으며 원천 데이터 재판매 권리 확인은 남아 있음. 뉴스 메타데이터는 감사용 원천 자료에만 보존하며 기사 본문 수집·전재를 안 함.
