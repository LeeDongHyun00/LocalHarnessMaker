# harness-v1 평가기 검증 기록

기존 파일럿 2개의 HTTP·브라우저 평가 코드, 제출 서비스 컨테이너 격리와 익명 패키징을 구현한 단계 0 기록입니다. 사용법은 [harness/README.md](../../harness/README.md), 범위와 다음 작업은 [검증 보고서](../../docs/experiments/harness-v1-validation.md)에 있습니다.

[validation.json](validation.json)은 직접 작성한 참조 앱의 30개 인수 시나리오, 의도적 결함 16종, 컨테이너·브라우저 통신 제한과 단위 검사의 실행 증거를 담습니다. GPT 6.1 SOL의 프로젝트 개발 결과나 프롬프트 개선 효과를 담은 자료는 아닙니다. 학습 정답으로 채택하지 않습니다.

`experiments/pilot-v1/`와 `project-pool-v1/`의 입력·정책·초기 runtime과 체크섬은 변경하지 않습니다. 초기 runtime의 `false` 값은 당시 준비 상태를 보존합니다. 최신 구현 확인 범위는 이 별도 기록을 사용하고, 실제 개발 조건을 고정할 때 새 프로토콜 버전을 작성합니다.

```sh
python scripts/record_harness_validation.py --check
python scripts/validate_pilot.py --check-hashes
python scripts/validate_project_pool.py --check-hashes
```

재검증할 때는 `harness/README.md`의 검사를 실행하고 `python -m harness evaluate backend-001 tests/fixtures/backend --runtime python --output .local/harness-validation/backend-cli.json`로 CLI 경로도 확인합니다. CLI 출력은 덮어쓰기를 거절하므로 기존 파일을 보존한 뒤 새로운 경로를 사용합니다. 결과들을 동일한 raw 디렉터리의 지정 파일명으로 정리하고 `python scripts/record_harness_validation.py --raw <경로>`를 실행하면 소스 해시와 결과를 갱신합니다. 실제 실험의 비공개 매핑·대화·인증 정보를 이 기록에 합치지 않습니다.
