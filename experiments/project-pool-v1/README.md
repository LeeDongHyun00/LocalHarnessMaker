# 다양한 프로젝트 풀 v1

작성 기준: 2026-10-14, Asia/Seoul. 상태: 요구사항 설계·검토 완료, 구현·블라인드 평가 미실행.

현재 파일럿의 두 원본을 참조하고, `gpt-6.1-sol` 실제 호출로 추가 원본 10개를 생성했습니다. 4분야 × 신규 개발·기능 확장·오류 수정으로 총 12개를 구성합니다.

## 프로젝트 목록

| 분야 | 신규 개발 | 기존 기능 확장 | 오류 수정 |
| --- | --- | --- | --- |
| 프론트엔드 | [식재료 소비 일정판](../pilot-v1/projects/frontend-001/intent-card.json) | [상품 검색·필터](projects/frontend-002/README.md) | [폼 상태·키보드 조작](projects/frontend-003/README.md) |
| 백엔드 | [장비 예약 API](../pilot-v1/projects/backend-001/intent-card.json) | [문서 API 권한](projects/backend-002/README.md) | [이벤트 중복·누락](projects/backend-003/README.md) |
| 풀스택 | [고객 요청 관리](projects/fullstack-001/README.md) | [팀 업무 검토 역할](projects/fullstack-002/README.md) | [화면·서버 상태 일치](projects/fullstack-003/README.md) |
| CLI·데이터 | [CSV 정리](projects/cli-data-001/README.md) | [NDJSON 형식 지원](projects/cli-data-002/README.md) | [인코딩·부분 실패](projects/cli-data-003/README.md) |

기존 두 원본과 A~E 파일은 변경하지 않습니다. [catalog.json](catalog.json)에 참조 경로와 SHA-256을 기록합니다. 신규 개발의 시작 공간과 기존 과제 8개의 시작 코드도 아직 준비하지 않았습니다. 특히 기존 과제의 `starting_state`는 앞으로 구현·검증할 블루프린트입니다.

## 구성과 의미

- 필수 요구사항 74개, Given/When/Then 판정 시나리오 127개.
- 각 프로젝트에 일부 결정이 빠진 요청과 명확한 요청을 연결해 24개 명확성 프로필을 준비했습니다.
- 기술 제안 설계 조건은 후보 제안 4개, 기존 스택 유지 4개, 추천 보류 4개입니다.
- 변경·수정 과제는 `change`와 기존 동작의 비회귀 기준인 `preserve`를 구분합니다.

명확성 프로필의 질문 행동과 기술 정책은 **실험 설계 가설**입니다. 실제로 질문이 도움이 됐거나 기술 유지·추천 보류가 더 좋았다는 실증적 정답은 아닙니다. 생략된 결정이 코드나 공통 맥락에서 확인되면 사용자에게 묻지 않아야 합니다. 실제 시작 코드를 준비한 뒤 이 구분을 다시 확인합니다.

현재 기술 정책은 신규 개발·기능 확장·오류 수정과 각각 연결되어 있어 독립 요인 설계가 아닙니다. 작업 유형만 보고 기술 정책을 고르는 학습 라벨로 사용하지 않습니다. 후속 설계에서는 기존 코드에서 기술 개선이 유용한 사례와 신규 개발에서도 추천 보류가 적합한 사례를 포함하고, 추천 효과는 같은 프로젝트 안에서 비교합니다.

24개 명확성 프로필은 질문 정책을 검증할 별도 조건입니다. 모든 프로필에 A~E를 자동으로 곱하지 않습니다. 추가 10개의 A~E 전체는 아직 생성하지 않았습니다. 현재 완성된 A~E는 기존 두 파일럿의 10개입니다.

## 파일 구조

- [catalog.json](catalog.json): 분야·작업·명확성·기술 조건과 원본 참조.
- `projects/<id>/intent-card.json`: 사용자 목적, 시작 상태 설계, 필수 요구사항·판정·질문 답변·수정 메시지.
- `projects/<id>/request-underspecified.md`, `request-clear.md`: 두 최초 요청 프로필.
- [authoring/instructions.md](authoring/instructions.md): 실제 교사에게 제공한 생성 지침.
- [authoring/project-cards.schema.json](authoring/project-cards.schema.json): 빈 판정 단계 등을 거절하는 출력 스키마.
- `authoring/<domain>.request.md`, `<domain>.teacher-output.json`: 실제 입력과 보정 전 출력.
- [authoring/review.json](authoring/review.json): 작업 에이전트의 일관성 검토와 보정 8개.
- [provenance.json](provenance.json): 실제 교사 호출 4회의 상태·요청 및 출력 해시·사용량.
- [hashes.json](hashes.json): 준비 자료 및 기존 원본 참조의 체크섬. 프로토콜 동결과 구분합니다.

## 검증

저장소 루트에서 실행합니다.

```bash
python -m pip install -r requirements-preparation.txt
python scripts/validate_project_pool.py --check-hashes
python scripts/validate_pilot.py --check-hashes
```

변경을 검토하고 체크섬을 갱신할 때만 `--write-hashes`를 사용합니다. 검증은 매트릭스, 스키마, ID 참조, 요청 프로필 연결, 생성 이력과 체크섬을 확인합니다. 실제 코드·질문 효과·기술 우수성을 판정하지 않습니다.

## 진행 순서

1. 기존 두 파일럿으로 격리, 평가기, 질문·수정과 익명 패키지 절차를 먼저 검증합니다.
2. 기능 확장·오류 수정 과제의 시작 저장소를 구현하고 결함 재현·정상 동작을 확인합니다. 시작 커밋과 의존성을 고정합니다.
3. 별도 새 작업 공간이 필요한 신규 과제를 준비합니다.
4. 프로필의 코드로 확인 가능한 정보와 실제 사용자 결정, 과제별 적절한 비교군을 재검토합니다.
5. 추가 A~E, 실행 한도와 평가 기준을 고정해 분야·작업별로 확대합니다.
6. 별도의 실제 사용자 요청·실제 저장소에서 재검증합니다. 합성 다양성이 한 교사의 편향을 제거한다고 가정하지 않습니다.

12개 모두 A~E·2반복으로 비교한다면 개발 실행은 120회입니다. 이는 향후 규모 계산이며 실행된 횟수가 아닙니다. 추천 보류가 적합한 과제의 E 처리와 명확성 통제 실험은 별도 설계를 확정해야 합니다.

검토·상태 보고서: [프로젝트 풀 준비 보고서](../../docs/experiments/project-pool-v1-preparation.md)
