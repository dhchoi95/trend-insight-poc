# Deterministic 지표

모든 계산은 `src/analytics/metrics.py`에서 Python으로 처리합니다. 결측/0분모/비교 불가 값은 null입니다. null은 0이나 감소가 아닙니다. NAVER 지수는 같은 응답 내 기간값만 비교하고 서로 다른 normalization_batch를 합치지 않습니다.

| 지표 | 정의 | 필요 자료 |
|---|---|---|
| rank_change | 오늘 내부 순위 − 어제 내부 순위, 음수면 상승 | 동일 watchlist·기간의 순위 |
| rank_rise | 어제 − 오늘, 양수면 상승 | 같은 조건 |
| daily_growth_pct | 100 × (오늘 − 어제) / 어제 | 비교 가능한 지수, 어제 >0 |
| seven_day_momentum_pct | 최근7일 평균 / 직전7일 평균 −1, ×100 | 연속14일 |
| thirty_day_momentum_pct | 최근30일 평균 / 직전30일 평균 −1, ×100 | 연속60일 |
| persistent_rise | 연속5일 지수 엄격 상승 | 연속5일, 동률이면 false |
| fast_rising | daily_growth_pct ≥50% | 비교 가능한 지수 |
| spike_candidate | 오늘 ≥직전7일 평균×3, baseline>0 | 연속8일 |
| one_day_spike | candidate이고 다음날 ≤baseline×1.5 | 미래 관측 필요, 오늘 즉시 확정 불가 |
| new_to_observed_feed | 전날 성공 관측 피드에 없고 오늘 있음 | 동일 KR RSS 범위의 전날 성공 수집 |
| Cross-Source Signal | 정규화/alias 일치 + 양쪽 daily_growth_pct>0 | NAVER 및 Google의 실제 comparable growth |

임계치50%/3배/5일은 운영 설정값이며 통계적 유의성이나 원인 확인을 의미하지 않습니다. 신규 진입은 **관측 피드 재진입/진입**이지 전세계 첫 발생·전체 TOP100 최초 진입이 아닙니다. 첫 실행/어제 수집 실패 시 신규 판정 null입니다.

Google RSS에는 공식 순위/연속 상대지수/전일 증가율이 없으므로 위 성장·순위·지속 지표가 null입니다. 구간 하한끼리 비율을 계산하지 않습니다. Google 원천 성장률이 향후 추가되더라도 source_growth_rate와 우리 전일 증가율을 구분해야 합니다. 현재 cross-source 탐지는 구현돼 있지만 실제 Google 증가율이 없어 결과는 빈 배열입니다.

네이버 rank는 같은 응답·같은 날짜의 설정된 그룹끼리 상대지수를 비교한 내부 순위입니다. 동률은 competition rank(1,1,3). 전체 패션 인기순위나 공식 데이터랩 순위가 아닙니다. 다른 배치의 지수를 한 순위표에 합치지 않습니다. 그룹별 여러 동의어가 있으면 단일 상품 키워드가 아닌 해당 그룹의 관심입니다.

스케일이 요청마다 바뀌는 문제를 피하기 위해 61일 응답 전체를 보존하고 그 안에서만 계산합니다. 달라진 응답의 최근값으로 과거 DB 값을 덮어쓰지 않습니다. 같은 scope도 서로 다른 batch의 ratio를 무조건 연결하지 않습니다. 향후 anchor 기반 확장도 이번 PoC에는 포함하지 않습니다.

현재 NOW 표본은 전일 이력이 없어 새 진입 null입니다. 이번 알고리즘 검증의 과거 숫자는 테스트 전용 synthetic fixture이며 실제 데이터 디렉터리에 기록하지 않습니다.
