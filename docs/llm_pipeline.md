# LLM 편집 파이프라인

수집→정규화→DB→지표→압축 입력까지 AI 호출이 없습니다. `src/llm/editor.py`만 선택적 외부 API를 사용합니다. 입력은 원천 XML/기사 수천 건 대신 NOW 최대30개, 설정된 FASHION 최대5개 그룹의 지표·근거 목록입니다. 원천 뉴스 메타데이터를 모델 입력에서 제외합니다.

## 근거를 바꾸지 않는 출력

`llm_input.json`의 fact registry에는 불변 ID와 `Source Fact`/`Calculated Metric` 텍스트가 있습니다. LLM은 문장·기존 ID 참조·claim_type만 반환합니다. 코드가 최종 보고서에 참조된 원천 숫자를 그대로 넣습니다. 모델이 숫자를 복사해 변형하는 경로를 줄였습니다.

- `interpretation`: 주어진 관측 해석
- `hypothesis`: 확인되지 않은 가능성
- `idea`: 활용 아이디어

출력 schema는 section/channel 키를 고정합니다. 알 수 없는 근거 ID·없는 신호 section·숫자를 새로 쓰는 문장을 거절합니다. 원문 키워드 안의 숫자는 허용합니다. 한글로 쓴 수량 주장이나 잘못된 인과 해석까지 자동 검증할 수는 없습니다. JSON schema와 숫자 검사만으로 사실성을 보장하지 않으므로 편집 검토용 초안으로 표시합니다. 외부 원인/뉴스 배경/특정 인물 추정/투자 권유는 prompt로 금지합니다.

source label은 지시가 아닌 신뢰하지 않는 데이터라고 명시합니다. prompt injection을 완전히 막았다는 주장 없이 모델에 도구/검색 권한을 주지 않습니다. LLM 모델에 원천 사실 생성이나 결측 추정을 맡기지 않습니다.

## 오늘의 실제 편집 결과

이 Work 세션에서 `output/2026-10-05/metrics/llm_input.json`을 읽고 LLM 편집 JSON을 작성했습니다. `src/llm/work_session_editorial.json`을 입력 해시 확인 후 가져와 각 채널 파일을 렌더링했습니다. provenance는 `work_session_import`, model은 미공개를 뜻하는 `work-session-model-unreported`, API calls는0, 토큰/비용은 null입니다. 임의 모델명·토큰을 쓰지 않았습니다.

이는 실제 관측 자료에 대한 LLM 해석 예시이나 독립 실행 Python 서비스의 자동 LLM 호출 성공은 아닙니다. 입력 해시가 바뀌면 제공된 편집 파일을 거절합니다. 수집 결과가 바뀐 날에 어제 문장을 재사용하지 않습니다.

## 자동 API 경로

`--llm-api`는 OpenAI Responses API를 1회 호출하고 `text.format`의 JSON schema strict 형식을 사용합니다. 검증 통과한 응답만 SQLite report와 insight.json에 기록합니다. 동일 input_hash + model + prompt_version이면 캐시 재사용합니다. 네트워크 재시도/잘린 응답 추가호출/수정호출은 구현하지 않았습니다.

max_output_tokens=6000. 모델은 환경변수로 선택하며 기본 gpt-4.1-mini. usage의 실제 입력/출력 토큰을 기록하고 알려진 기본 모델 단가만 달러로 계산합니다. cached token 할인은 반영하지 않은 보수적 표준 비용 계산입니다. 실제 청구액과 다를 수 있습니다. 모델별 최신 가격은 운영 시작 때 재확인하세요.

- [Responses Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses)
- [기본 모델 사양·가격](https://developers.openai.com/api/docs/models/gpt-4.1-mini)

한 번의 요청에 Daily Brief와 각 채널의 독립 배열을 함께 요구하여 같은 숫자를 여러 번 전송하지 않습니다. 채널마다 별도의 문장이며 동일 분석문을 복사하는 템플릿이 아닙니다. Python renderer는 채널별 fact_refs를 사용해 숫자를 추가합니다.
