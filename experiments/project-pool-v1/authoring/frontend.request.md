너는 LocalHarnessMaker의 교사 모델이다. 여러 프로젝트에서 최초 요청 구체화·질문의 효과를 시험할 요구사항 원본을 작성하라. 제공된 배치의 모든 project_id를 정확히 한 번씩 반환한다. 한국어로 JSON을 작성하고 도구 호출, 파일 읽기, 구현은 하지 않는다.

현재 작업은 실제 개발 및 성능 평가 전 합성 프로젝트 설계다. 기존 파일럿 2개는 재생성하지 않는다. 새 프로젝트도 기존 프로젝트의 이름만 바꾼 CRUD 반복이 되지 않도록 분야·작업 유형에 맞게 설계한다.

## 원본 요구사항

각 프로젝트에 필수 요구사항을 정확히 6개 작성한다. 신규 구현은 핵심 동작을, 기능 확장은 변경과 기존 동작 보존을, 오류 수정은 수정할 결함과 비회귀 동작을 포함한다. requirement id는 R1~R6이며 critical은 2~3개다. requirement_scope는 신규 구현에서는 deliver_new, 기존 작업에서는 change 또는 preserve다. 기능 확장·오류 수정의 기존 정상 동작을 보존하는 기준이 반드시 있어야 한다.

각 요구사항에 Given/When/Then 시나리오 1~2개를 작성한다. given은 시작 상태, when은 실행할 행동, then은 관찰할 기대 결과다. 모든 필드는 비어 있지 않아야 한다. when에 기대 결과를 합쳐 넣거나 '(Then)' 같은 표식을 쓰지 않는다. 정해진 입력·출력과 브라우저·HTTP·CLI·파일 결과로 판단할 수 있어야 한다. 특정 내부 구현을 선택하지 않았다는 이유로 실패시키지 않는다.

교사 원본은 아직 없는 가상 프로젝트의 설계다. 기능 확장과 오류 수정은 starting_state.status를 baseline_not_materialized로 두고 기존 동작, 재현할 결함, 공통 공개 계약 및 기술 스택을 구체적인 블루프린트로 작성한다. 실제 저장소 커밋이나 파일을 읽었다고 표현하지 않는다. 신규 구현은 new_workspace로 둔다. 기존 스택을 유지하는 사례는 블루프린트에서 스택을 지정하되 이는 앞으로 준비할 시작 상태다.

common_context는 모든 비교군에 동일하게 제공할 런타임·입출력·전송·fixture 계약이다. 실험에서 질문할 사용자 선택이나 기대 동작을 전부 노출하지 않는다. Linux, Node.js 24, Python 3.12와 로컬 브라우저를 사용할 수 있고 외부 계정·유료 서비스·비밀 키 없이 재현 가능해야 한다. API, CLI, 파일의 공통 이름·형식은 평가가 기술 선택에 좌우되지 않게 정의한다. 계정·권한 과제는 로컬 테스트용 식별자를 명시하고 실제 인증 서비스 구축을 추가하지 않는다.

user_decisions에는 중요한 사용자 결정 3~5개, 질문 예시, 원본에 일치하는 답변과 관련 요구사항 ID를 적는다. correction_feedback는 미충족일 때 보낼 사용자 관점의 수정 요청이다. 숨겨진 테스트 코드나 다른 군의 답을 제공하지 않는다. out_of_scope와 자유로운 구현 선택인 implementation_defaults를 구분한다.

## 명확한 요청과 질문이 필요한 요청

initial_requests.underspecified는 현실적인 최초 요청이다. 목적과 일부 동작을 포함하며 중요한 결정 2개 이상을 생략한다. omitted_decision_ids로 빠진 결정을 연결한다. expected_question_action은 clarify다.

initial_requests.clear는 동일한 원본의 필수 요구사항과 필요한 사용자 결정을 간결하게 제공한다. 새 기능을 추가하지 않는다. requirement_ids에는 R1~R6 모두를 기록하고 omitted_decision_ids는 빈 배열이다. expected_question_action은 pass_or_enrich다. 학생이 충분한 요청에까지 불필요하게 질문하지 않는지 확인하기 위한 조건이다.

이 판단 라벨은 실험 설계의 가설이며 실행으로 확인한 정답은 아니다. 기존 요구사항 원본의 구체적인 평가 입력을 최초 요청에 복사하지 않는다.

## 기술 제안 적합성

각 배치 항목의 technology_design_mode를 따르는 사례를 설계한다. candidate는 신규 프로젝트에서 비교할 기술 후보, maintain_existing은 기존 스택을 유지하며 기능을 바꾸는 사례, withhold는 기술 변경보다 재현·정확한 수정이 핵심인 사례다. technology_policy에 mode, 이유와 추후 필요한 검증 근거를 기록한다. 특정 기술이 실제로 더 좋았다고 주장하지 않는다. 기능 확장·오류 수정에서 새 스택·새 기능을 제안으로 강제하지 않는다.

## 범위

한 과제는 소규모 실험으로 완성 가능한 크기로 제한한다. 온라인 배포, 외부 OAuth, 실제 결제, 실시간 대규모 부하 등 별도 인프라를 요구하지 않는다. 완성 코드·블라인드 결과·실증적 추천 근거는 이번 출력에 포함하지 않는다. limitations에 합성 설계이며 실제 시작 저장소, 구현·기능 테스트·블라인드 평가가 아직 없다는 점을 명시한다.

이번 배치:

[
  {
    "project_id": "frontend-002",
    "domain": "frontend",
    "work_type": "feature_extension",
    "title": "기존 상품 목록의 검색·필터 확장",
    "source_kind": "new_teacher_card",
    "source_path": "experiments/project-pool-v1/projects/frontend-002/intent-card.json",
    "technology_design_mode": "maintain_existing",
    "input_status": "pending"
  },
  {
    "project_id": "frontend-003",
    "domain": "frontend",
    "work_type": "bug_fix",
    "title": "폼 상태와 키보드 조작 오류 수정",
    "source_kind": "new_teacher_card",
    "source_path": "experiments/project-pool-v1/projects/frontend-003/intent-card.json",
    "technology_design_mode": "withhold",
    "input_status": "pending"
  }
]
