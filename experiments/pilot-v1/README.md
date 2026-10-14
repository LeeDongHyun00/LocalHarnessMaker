# 파일럿 v1 준비 자료

상태: 실행 전 준비. 이 폴더에는 요구사항과 최초 요청, 평가·질문·수정 정책이 있으며 개발 결과나 성능 개선 점수는 없습니다.

## 프로젝트

| 프로젝트 | 요구사항 원본 | 공통 시작 자료 | 판정 기준 |
| --- | --- | --- | --- |
| 가정 식재료 소비 일정판 | [frontend-001/intent-card.json](projects/frontend-001/intent-card.json) | [common-context.md](projects/frontend-001/common-context.md) | [평가 체크리스트](projects/frontend-001/evaluation-checklist.md) |
| 공유 작업실 장비 예약 API | [backend-001/intent-card.json](projects/backend-001/intent-card.json) | [common-context.md](projects/backend-001/common-context.md) | [평가 체크리스트](projects/backend-001/evaluation-checklist.md) |

두 프로젝트는 각각 필수 요구사항 7개와 판정 시나리오 15개를 가집니다. 주요 기능 요구사항은 `critical`로 표시합니다. 사용자 질문 답변은 원본의 `user_decisions`, 수정 메시지는 각 요구사항의 `correction_feedback`에 있습니다.

## 최초 요청

| 군 | 프론트엔드 | 백엔드 | 비교 의미 |
| --- | --- | --- | --- |
| A | [A.md](projects/frontend-001/prompts/A.md) | [A.md](projects/backend-001/prompts/A.md) | 자연스러운 최초 요청 |
| B | [B.md](projects/frontend-001/prompts/B.md) | [B.md](projects/backend-001/prompts/B.md) | A의 정보만 정리 |
| C | [C.md](projects/frontend-001/prompts/C.md) | [C.md](projects/backend-001/prompts/C.md) | 필수 정보가 있는 최소 명세 |
| D | [D.md](projects/frontend-001/prompts/D.md) | [D.md](projects/backend-001/prompts/D.md) | 같은 목표의 상세 설명 |
| E | [E.md](projects/frontend-001/prompts/E.md) | [E.md](projects/backend-001/prompts/E.md) | 정확히 C + 기술 후보 문단 |

모든 입력은 해당 프로젝트의 `common-context.md`와 배정한 군의 본문으로 구성합니다. `prompt-metadata.json`의 요구사항 ID 언급은 완전한 판정 기준 포함을 뜻하지 않습니다. 정보 보존과 목표 일치는 문장을 별도로 검토해야 합니다.

## 운영·평가 정책

- [policies.json](policies.json): 모의 사용자 답변, 수정 회차, 첫 제출·최종 제출, 블라인드 평가 규칙.
- [runtime.json](runtime.json): 관찰된 환경과 미확정 실행 조건, 프로토콜 고정 전 확인할 항목.
- [provenance.json](provenance.json): 실제 교사 호출의 성공·실패와 생성 이력. 학습 정답 채택 여부는 별도입니다.
- [intent-review.json](authoring/intent-review.json): 원본을 보존한 형식·일관성 보정 내역.
- [hashes.json](hashes.json): 준비 파일의 SHA-256 목록. 프로토콜 동결을 의미하지 않습니다.

최초 A~E 생성은 기술 후보의 효과를 확인한 것이 아닙니다. 검증 결과가 없으면 기술 제안은 실험용 가설로 남깁니다.

## 준비 자료 검증

저장소 루트에서 실행합니다.

```bash
python -m pip install -r requirements-preparation.txt
python scripts/validate_pilot.py --check-hashes
```

의도적으로 준비 파일을 변경한 뒤 목록을 갱신할 때는 다음 명령을 사용합니다.

```bash
python scripts/validate_pilot.py --write-hashes
```

이 검증은 스키마, 요구사항 참조, A/B의 선언된 정보 목록, C/D/E 목표 목록, E의 정확한 접합과 체크섬을 확인합니다. 실제 프로젝트 기능, 문장의 의미적 동등성, 모델 성능을 검증하지 않습니다.

## 교사 생성 재현

[01-intent-cards.md](authoring/01-intent-cards.md)와 [요구사항 스키마](authoring/intent-cards.schema.json)를 사용해 먼저 원본을 생성합니다. 결과를 검토하고 고정한 다음 [02-prompt-variants.md](authoring/02-prompt-variants.md)에 원본 JSON을 붙여 [프롬프트 스키마](authoring/prompt-variants.schema.json)로 생성합니다.

이번 실제 호출은 `codex exec --model gpt-6.1-sol --sandbox read-only --ephemeral --json --output-schema` 경로를 사용했습니다. 입력만 제공하고 생성 도구에 파일 읽기나 개발을 요청하지 않았습니다. 원시 CLI 이벤트와 인증 정보는 `.local/` 및 Codex 인증 저장소에만 남기며 Git에 넣지 않습니다.

## 실행 전에 확인할 것

1. 실제 개발 작업 공간에서 이 폴더, 다른 군과 평가 코드에 접근할 수 없도록 경로·환경을 분리합니다. 단순히 파일을 복사하지 않는 것만으로 접근 차단을 입증하지 않습니다.
2. 라이브러리 설치 및 시작 상태를 재현 가능하게 정의하고 모든 군에 같은 자원을 제공합니다.
3. 브라우저·HTTP 판정 절차를 실제 결과물에 적용할 수 있는 평가기로 구현하고 검증합니다.
4. 질문·답변과 수정 피드백이 이어지는 Codex 실행 경로를 확인합니다.
5. 반복 수, 실행·사용량·비용 한도, 평가 담당자와 블라인드 대응표의 별도 보관 위치를 확정합니다.
6. 그 뒤 프로토콜을 동결하고 개발 실행을 시작합니다.

다음 작업과 상태: [파일럿 준비 보고서](../../docs/experiments/pilot-v1-preparation.md)
