# 파일럿 평가 도구

기존 `pilot-v1` 입력을 재생성하지 않고 제출 서비스의 기능을 평가합니다. 이 디렉터리, 원본 카드와 평가용 어댑터는 개발 모델에게 제공하지 않습니다. 정상 참조 앱과 결함 앱은 `tests/fixtures/`에 있으며 GPT 6.1 SOL의 개발 결과물이 아닙니다.

## 준비

저장소 루트에서 Python 3.12, Docker와 Node 런타임 이미지를 준비합니다. 네트워크 설치는 환경의 기존 프록시·CA 설정을 사용합니다.

```sh
python -m pip install -r requirements-evaluation.txt
python -m playwright install chromium
docker pull python@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e
docker pull node@sha256:a9f5f7c91a432850b2a8a7797adf5eadb6c733ceed61167806cee7ea7fbc29df
python -m unittest tests.test_harness -v
python -m unittest tests.test_integration -v
```

이미지 digest와 확인한 도구 버전은 `runtime-lock.json`에 있습니다. Python·Node 제출물 평가 이미지를 각각 고정한 것이며, 두 런타임·Codex·의존성 설치를 포함하는 공통 **개발** 이미지를 고정한 상태는 아닙니다. 제출물의 의존성은 운영자가 같은 설치 정책으로 미리 준비해야 합니다. 평가 컨테이너에는 설치용 외부 통신을 제공하지 않습니다.

## 공통 자료와 배정 요청만 내보내기

```sh
python -m harness prepare backend-001 A /workspace/lhm-runs/run-001-input
```

새 디렉터리에 `COMMON_CONTEXT.md`와 `TASK.md`만 생성합니다. 기존 디렉터리를 덮어쓰지 않습니다. 이것은 입력의 최소 공개 패키징이며, 호스트 Codex를 이 디렉터리에서 실행하는 것만으로 파일 접근이 격리되지는 않습니다. 실제 개발 CLI의 파일·네트워크 도구 격리는 다음 단계에서 검증해야 합니다. 공개 GitHub 저장소를 개발 모델이 읽어 숨은 원본을 얻는 경로도 통제해야 합니다.

## 제출 서비스 평가

```sh
python -m harness evaluate backend-001 /workspace/lhm-runs/submission-001 \
  --runtime python --output /workspace/lhm-private-results/submission-001.json
```

`run.json`의 `start_command`를 쉘 문자열로 해석하지 않고 인수 배열로 실행합니다. `ready_url`은 공통 계약의 `/` 또는 `/equipment`입니다. 각 인수 시나리오는 소스를 복사한 새 컨테이너·저장 볼륨에서 시작합니다. B7은 해당 컨테이너를 정상 재시작하며 같은 볼륨을 유지합니다. 새 컨테이너의 작업 디렉터리는 `/work`이고 입력·로그·모델 인증·평가기·Docker 소켓을 마운트하지 않습니다.

평가 입력은 코드·설치 의존성으로 구성한 새 배포 디렉터리여야 합니다. 개발 중 생긴 저장 데이터를 그대로 복사하면 “저장 기록이 없는 서버”라는 초기 조건을 만족하지 못할 수 있습니다. 실제 제출물의 README에서 저장 위치를 확인해 빈 저장소 준비 방법을 운영자가 검토해야 합니다. 원래 첫 제출 snapshot은 보존하고 평가용 빈 저장소의 준비 내역을 별도로 기록합니다. 이 조건을 확인하지 못하면 제품 실패로 단정하지 않고 측정 준비를 보류합니다. 참조 앱 외 실제 제출물의 저장소 준비 어댑터는 다음 연결 확인에서 검증할 항목입니다.

서비스는 UID 1000, 읽기 전용 루트, 작업용 볼륨과 임시 디렉터리, capability 제거 및 자원 제한으로 실행됩니다. `--network=none`으로 외부 경로를 끊고, 호스트의 loopback 평가 포트에서 Docker exec 표준 입출력 파이프로 서비스의 loopback 포트에 요청을 전달합니다. 평가 브라우저에는 배정된 서비스 포트에만 연결하는 별도 로컬 프록시를 사용합니다. 외부 호스트와 다른 로컬 포트로 향하는 HTTP·WebSocket CONNECT를 거절하고 service worker를 끕니다. HTTP 요청의 origin 검사도 함께 사용합니다. 파이프·프록시 비용은 평가 도구의 비용이며 앱 성능 개선 지표로 사용하지 않습니다. 컨테이너는 공유 커널을 사용하므로 적대적인 커널 공격까지 격리했다고 주장하지 않습니다.

컨테이너·볼륨과 파이프는 정상 종료 및 예외 때 제거합니다. 작업이 강제 종료된 경우 `lhm-app-*`, `lhm-data-*` 자원을 확인하고 해당 실행의 자원만 정리합니다. 빈 디렉터리·디렉터리 권한과 내부 상대 심볼릭 링크를 보존합니다. 컨테이너에 복사한 디렉터리도 UID 1000이 소유하도록 하여 런타임 캐시·저장 폴더의 권한 오류를 막습니다. 호스트·숨은 경로를 가리키는 링크, 절대 링크와 특수 파일은 거절합니다. `.git`, `.local`, `__pycache__`는 산출물 범위에서 제외합니다.

프론트엔드는 제출물별 UI 연결표가 필요합니다.

```sh
python -m harness evaluate frontend-001 /workspace/lhm-runs/submission-002 \
  --runtime node --adapter /workspace/lhm-private-results/submission-002-ui.json \
  --output /workspace/lhm-private-results/submission-002.json
```

`tests/fixtures/frontend/ui-adapter.json`의 구조를 참고해 평가 담당자가 실제 화면을 보고 label·role 또는 CSS 선택자를 연결합니다. 이 파일의 선택자를 실제 제출물에 강제하지 않습니다. 어댑터의 `artifact_digest`에는 `harness.packages.artifact_digest(source)` 값을 넣습니다. 소스가 바뀌면 매핑을 다시 검토합니다. 실제 없는 control·filter는 해당 값을 `null`로 기록하면 제품의 미충족으로 판정합니다. 매핑이 틀리거나 미완료인 경우와 구분합니다. 등록·검색·필터·소비의 자동 상호작용과 Tab 도달·키보드 활성화를 검사하고, 목적을 알아볼 수 있는지와 보이는 포커스는 별도로 검수합니다. 키보드 시나리오의 입력값 설정에는 Playwright `fill`이 사용되므로 네이티브 날짜 입력의 모든 키 입력 동작을 자동 검증했다고 표현하지 않습니다. 실제 제출물은 사람이 전체 키보드 흐름도 확인해야 합니다.

F7.2의 사람 검수 값이 없으면 `not_evaluated`입니다. 참조 앱의 검수 값은 명시적 label·네이티브 버튼·포커스 스타일을 갖춘 **평가기 테스트용 설정**이며 실제 개발 결과에 대한 블라인드 사람 평가 점수가 아닙니다. 없는 날짜는 일반 텍스트 입력과 네이티브 날짜 입력을 구분합니다. 후자는 브라우저의 값 거절·유효성 안내를 확인하며 앱 저장소를 직접 수정하지 않습니다.

각 요구사항의 모든 시나리오가 통과해야 요구사항이 통과합니다. `fail`은 제품의 미충족, `not_evaluated`는 환경·평가 도구 오류나 미완료 검수입니다. 후자는 완료로 세거나 모델 수정 요청으로 바꾸지 않습니다. 새 평가 결과 파일은 기존 파일을 덮어쓰지 않습니다. 평가 전후 입력 digest도 검사합니다.

```sh
python -m harness correction backend-001 /workspace/lhm-private-results/submission-001.json
```

모든 미충족 요구사항의 원래 `correction_feedback`만 critical 우선·숫자 ID 순서로 반환합니다. 테스트 구현과 다른 군은 제공하지 않습니다. 실제 교사 세션에 질문·피드백을 연결하고 회차·시간·사용량을 제한하는 실행기는 아직 준비하지 않았습니다.

## 첫 제출·최종 제출의 익명 패키징

```sh
python -m harness package backend-001 /workspace/lhm-runs/submission-001 \
  --public /workspace/lhm-judge-packages \
  --private /workspace/lhm-private-mappings \
  --metadata /workspace/lhm-private-results/run-001-metadata.json
```

`metadata` JSON에 run ID·실험군·모델·회차·first/final 구분을 기록합니다. 대응표는 저장소 및 공개 패키지 밖의 0700 디렉터리에 0600 파일로 생성합니다. 첫 제출과 최종 제출은 각각 새 무작위 artifact ID로 저장합니다. 자동 덮어쓰기를 막고 파일 bytes·mode·링크의 일치 여부를 검사합니다. 패키지 파일 mtime은 중립화합니다. `.git` 같은 운영 파일을 제외한 제출 코드 자체는 편집하지 않습니다.

공개 폴더에는 익명 manifest, 산출물과 모든 군에 동일한 평가 체크리스트만 포함합니다. **운영자 검수 전에는 평가자에게 공개하지 않습니다.** README·파일명·코드에 모델·프롬프트·실험군 정보가 들어 있는지 확인해야 합니다. 누출이 있다면 소스를 조용히 고치지 않고 해당 제출물의 블라인드 한계 또는 판정 보류를 기록합니다. 기술은 코드에서 추론할 수 있습니다.

```sh
python -m harness review-package /workspace/lhm-judge-packages/artifact-ID \
  --private /workspace/lhm-private-mappings --reviewer operator-name
python -m harness judge-order /workspace/lhm-judge-packages
```

`review-package`는 검수가 끝났다는 운영자 명시 기록입니다. 미검수 패키지나 snapshot 이후 변한 산출물이 있으면 `judge-order`가 거절합니다. 순서는 호출마다 독립 무작위화하므로 평가자별 순서 파일을 한 번 저장해 사용합니다. 실제 평가자 계정의 파일 권한·GitHub 접근을 분리하고 검증하는 일은 남아 있습니다. 이 도구의 디렉터리 분리만으로 그 접근 통제가 완료됐다고 표현하지 않습니다.
