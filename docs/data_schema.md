# SQLite schema

실제 DDL은 `src/processors/store.py`의 SQL에 있습니다. 모든 시각은 timezone 포함 ISO8601, report_date는 Asia/Seoul입니다.

| Table | 키 | 역할 |
|---|---|---|
| run | run_id | report_date/source/status/collected_at/scope/raw_path: 성공·누락 실행 및 출처 감사 |
| keyword | source, canonical, category | first_seen_at/last_seen_at: 시스템이 실제 발견한 시각 |
| snapshot | run_id, source, canonical, period | category/scope/payload JSON: 원천 단위와 메타데이터를 포함한 불변 관측 |
| report | input_hash, model, prompt_version | generated_at/payload: 동일 입력 재호출 방지·LLM provenance/usage |

run_id는 소스·실제 시각·원천 payload 해시로 결정됩니다. 같은 XML 재생은 snapshot 중복 삽입하지 않습니다. keyword.first_seen은 최초 수집 시각이지 네이버 과거 지수의 period나 검색어 최초 등장일이 아닙니다. DB는 과거 응답값을 새 요청의 ratio로 덮어쓰지 않습니다.

snapshot 공통: source/category/keyword/canonical_keyword/collected_at/source_url/series_scope/coverage. period는 NAVER 지수 날짜, Google은 보고 날짜입니다. Google의 source_position은 XML 위치, source_rank는 null. exact_count 필드는 없습니다. Google volume_precision=bucket_lower_bound, traffic 문자열과 파싱 하한을 함께 보존합니다.

NAVER: interest_score, metric_unit(search_relative_index/shopping_click_relative_index), normalization_batch, watchlist_version, rank(내부 설정 그룹 순위). 가격/판매량/거래수 등 상품 필드는 없습니다.

JSON으로 소스 특이 필드를 유지하여 파서 수정 전 원천과 추적할 수 있습니다. PostgreSQL로 확장 시 source_fact/signal/collection_scope 별도 테이블로 옮길 수 있지만 이번에는 SQLite와 원천 파일로 단순하게 운영합니다. DB 자체의 검증 결과 10개 keyword, 10개 snapshot이 있고 실제 패션 지수는0개입니다.
