<h1 align="center">LocalHarnessMaker</h1>

<p align="center"><strong>개발자가 아닌 사람도 평소 말투 그대로 Codex에게 작은 프로그램을 맡길 수 있게 해 주는 에이전트 스킬</strong></p>

<p align="center">
  <a href="https://github.com/LeeDongHyun00/superpowers-sp-plus/releases/tag/v7.0.1-sp.9"><img src="https://img.shields.io/badge/SP%2B-7.0.1--sp.9-0891b2?style=flat-square" alt="SP+ 버전 7.0.1-sp.9" /></a>
  <a href="https://github.com/obra/superpowers"><img src="https://img.shields.io/badge/based_on-Superpowers_7.0.1-24292f?style=flat-square" alt="Superpowers 7.0.1 기반" /></a>
  <a href="#설치"><img src="https://img.shields.io/badge/works_with-Codex_CLI-7C3AED?style=flat-square" alt="Codex CLI에서 동작" /></a>
  <a href="#결과"><img src="https://img.shields.io/badge/tested_with-gpt--6.1--sol_medium-22c55e?style=flat-square" alt="gpt-6.1-sol medium으로 시험" /></a>
  <a href="https://github.com/LeeDongHyun00/superpowers-sp-plus/blob/sp-plus/LICENSE"><img src="https://img.shields.io/badge/license-MIT-24292f?style=flat-square" alt="MIT 라이선스" /></a>
</p>

LocalHarnessMaker는 SP+를 만든 연구 프로젝트예요. SP+는 Jesse Vincent와 Prime Radiant가 만든 [Superpowers](https://github.com/obra/superpowers)를 바탕으로 한 Codex 플러그인이에요. 미용실 사장님, 동아리 총무, 학부모처럼 Codex에게 작은 프로그램을 부탁하고 "ㅇㅇ", "계속", "알아서 해"로 답하는 사람을 위해 만들었어요. Superpowers의 스킬은 모두 그대로 두고, 새 스킬 5개와 늘 지키는 규칙 6개를 더했어요. 효과는 한국어 사용자를 흉내 낸 대본 세션으로 측정했어요.

플러그인 자체는 [LeeDongHyun00/superpowers-sp-plus](https://github.com/LeeDongHyun00/superpowers-sp-plus)에 있어요. 이 저장소는 프로젝트 소개 페이지이고, 설계 기록을 모아 둔 곳이에요.

| 1. 요청 | 2. 합의 | 3. 만들기 | 4. 확인 | 5. 넘겨주기 |
|---|---|---|---|---|
| 한두 문장으로 부탁 | 8줄 이내 계획, "ㅇㅇ"이면 시작 | 만들면서 계획을 `AGENTS.md`에 적어 둠 | 사용자가 말한 목적에 맞는지 확인 | 배포·전송·삭제 앞에서 멈추고, 만든 파일을 알려 줌 |

## 목차

- [왜 만들었나](#왜-만들었나)
- [작동 방식](#작동-방식)
- [설치](#설치)
- [사용법](#사용법)
- [들어 있는 스킬](#들어-있는-스킬)
- [결과](#결과)
- [시험 방법](#시험-방법)
- [자주 묻는 질문](#자주-묻는-질문)
- [비교](#비교)
- [업데이트와 삭제](#업데이트와-삭제)
- [이 저장소](#이-저장소)
- [출처와 라이선스](#출처와-라이선스)

## 왜 만들었나

코딩 에이전트는 개발자에게 맞춰져 있어요. 개발자는 계획을 읽고, push가 무엇인지 알고, 결과를 직접 확인해요. 처음 쓰는 사람은 그렇게 하지 않아요. gpt-6.1-sol(medium)로 돌린 첫 파일럿에서 세 가지가 계속 나왔어요.

- **"계속"을 허락으로 받아들였어요.** 사용자가 "계속"이라고만 했는데, 에이전트가 사용자가 말한 적 없는 호스팅 서비스에 프로젝트를 만들고 공개 `git push`를 시도했어요.
- **잘못된 믿음이 사용자의 목적을 이겼어요.** "UTF-8이면 엑셀에서 안 깨진대요"라는 말에 에이전트가 파일을 바꿨어요. 사용자는 앞서 그 파일을 엑셀로 연다고 말했었어요.
- **말없이 남긴 것들이 있었어요.** 작업 공간 12개 중 11개에 임시 폴더와 테스트 파일이 남았고, 두 세션은 서버를 켜 둔 채 끝났어요.

Superpowers는 이미 에이전트가 계획하고 검증하게 해요. SP+는 그 위에 개발자가 아닌 사람에게 필요한 규칙을 더해요.

## 작동 방식

한두 문장으로 부탁하면 돼요. 작은 수정보다 큰 일이면 Codex는 바로 코드를 쓰지 않아요. 먼저 8줄 이내의 계획을 보여 줘요. 영업시간, 시간 단위, 파일 이름처럼 나중에 눈에 띌 기본값도 계획에 적어요. 계획을 바꾸지 않는 답이면 무엇이든 작업이 시작돼요. "ㅇㅇ", "진행해", "알아서 해"면 충분해요.

합의한 계획은 프로젝트의 `AGENTS.md`에 "작업 약속"이라는 짧은 칸으로 남아요. Codex는 세션을 시작할 때마다 이 파일을 읽어요. 그래서 새 대화에서 "계속"이라고 하면 아직 체크되지 않은 다음 항목부터 이어서 해요. 모든 항목이 끝났으면 새 일을 만들지 않고 끝났다고 말해요.

만드는 동안에는 결과가 사용자가 말한 목적에 맞는지 확인해요. 어디서 들은 말 때문에 바꿔 달라고 하면, 목적에 맞는 쪽을 유지해요. 그리고 사용자의 데이터로 차이를 한 번 보여 주고, 직접 바꾸는 방법을 알려 줘요. 원래 있던 파일은 그대로 두고, 변환한 파일은 그 옆에 따로 만들어요.

되돌리기 어려운 단계에 이르면 그 단계에서 멈춰요. 배포, push, 사용자가 가진 파일 삭제, 메시지 보내기, 시작 프로그램 등록 같은 단계예요. 무엇이 준비됐고 그 단계가 무엇을 하는지 말한 뒤 나머지 일을 계속해요. "배포해 줘"처럼 그 단계를 콕 집은 허락이 있어야 하고, 그때도 사용자가 말한 서비스에서만 진행해요.

끝나면 만든 파일, 아직 켜져 있는 서버, 부탁하지 않았는데 더한 것을 알려 줘요. 작업용 도우미 파일을 지울지는 한 번만 물어요.

## 설치

**필요한 것**

- 플러그인을 지원하는 Codex CLI. Windows 11에서 Codex CLI 0.164~0.166으로 시험했어요.
- Git. Codex가 GitHub에서 플러그인을 내려받을 때 써요.

공식 Superpowers 플러그인을 쓰고 있다면 먼저 지워 주세요. `codex plugin list`에 `superpowers@openai-curated-remote`가 보이면 쓰고 있는 거예요. Codex CLI의 `/plugins`나 Codex 앱의 Plugins에서 지울 수 있어요. 두 플러그인은 스킬 이름이 같아요.

**1. 마켓플레이스 추가와 설치**

```bash
codex plugin marketplace add LeeDongHyun00/superpowers-sp-plus
```

```bash
codex plugin add superpowers@superpowers-sp-plus
```

<details>
<summary><b>Windows에서 <code>codex</code>를 찾을 수 없다고 나올 때</b></summary>

Codex 앱은 `%LOCALAPPDATA%\OpenAI\Codex\bin` 아래에 CLI를 따로 가지고 있어요. PowerShell에서 한 번 찾아 두고 그걸로 실행하세요.

```powershell
$codex = (Get-ChildItem "$env:LOCALAPPDATA\OpenAI\Codex\bin" -Recurse -Filter codex.exe | Sort-Object LastWriteTime | Select-Object -Last 1).FullName
& $codex plugin marketplace add LeeDongHyun00/superpowers-sp-plus
& $codex plugin add superpowers@superpowers-sp-plus
```

이 페이지의 다른 명령도 `codex` 대신 `& $codex`를 쓰면 같은 방식으로 돼요.
</details>

**2. 설치 확인**

```bash
codex plugin list
```

```text
PLUGIN                           STATUS              VERSION     SOURCE
superpowers@superpowers-sp-plus  installed, enabled  7.0.1-sp.9  ...
```

새 세션이 SP+ 스킬을 불러오는지는 모델을 부르지 않고 확인할 수 있어요.

```bash
codex debug prompt-input "hi" | grep -o "superpowers:agreeing-on-larger-work" | head -1
```

PowerShell에서는 `codex debug prompt-input "hi" | Select-String "agreeing-on-larger-work" -Quiet`가 `True`를 출력하면 돼요.

**3. 도구 출력 줄이기 (권장)**

SP+는 이 설정으로 측정했어요. `~/.codex/config.toml`을 열고(Windows는 `%USERPROFILE%\.codex\config.toml`) 아래 한 줄을 맨 위쪽에 넣으세요. `[`로 시작하는 줄보다 위에 있어야 해요.

```toml
tool_output_token_limit = 6000
```

**4. 써 보기**

빈 폴더에서 새 Codex 세션을 열고, 데이터를 저장해야 하는 일을 부탁해 보세요.

```text
동네 미용실 예약 받는 웹페이지 만들어 줘. 예약은 저장돼야 해요.
```

SP+가 있으면 Codex는 코드를 쓰기 전에 짧은 계획부터 보여 줘요. 이미 열려 있던 세션은 시작할 때 불러온 스킬을 그대로 쓰니까, 설치한 뒤에는 새 세션을 여세요.

## 사용법

평소처럼 Codex와 대화하면 돼요. 아래 말들이 중요해요.

| 하고 싶은 일 | 이렇게 말하세요 | Codex가 하는 일 |
|---|---|---|
| 보여 준 계획대로 시작 | "ㅇㅇ", "진행해", "알아서 해" | 작업을 시작하고 계획을 `AGENTS.md`에 남겨요 |
| 계획 바꾸기 | "예약은 30분 단위로 해 주세요" | 바뀐 계획을 보여 준 뒤 시작해요 |
| 다른 날 이어서 하기 | 새 대화에서 "계속" 또는 "이어서 해 줘" | 체크되지 않은 다음 항목부터 하거나, 다 끝났다고 말해요 |
| 되돌리기 어려운 단계 맡기기 | "배포해 줘", "푸시해 줘", "문자 보내 줘" | 그 단계만, 말한 서비스에서만 해요. "계속"만으로는 하지 않아요 |
| 만든 것 공유하기 | "친구들도 볼 수 있게 해 줘" | 방법마다 누가 열 수 있는지 알려 줘요. 이 PC만, 같은 와이파이의 휴대폰, 링크를 가진 누구나. 같은 와이파이부터 권해요 |
| 경고를 듣고도 내 방식대로 | "엑셀에서 깨져도 괜찮아요, 그래도 바꿔 주세요" | 바꿔 줘요. "팀장님이 그렇게 하래요"처럼 누가 원한다는 말만 반복하면 파일은 그대로 두고, 그분께 전할 한 문장을 줘요 |
| 없어진 파일 찾기 | "파일이 없어졌어요" | 옮기거나 이름을 바꾸거나 지운 파일을 휴지통까지 포함해 알려 주고, 되돌려 놓겠다고 해요 |
| 개발자 방식으로 일하기 | "테스트 먼저 쓰고 해 줘", "코드 리뷰 받아 보고 싶어요" | Superpowers의 개발자용 작업 방식을 써요. 개발자가 아닌 사람의 작은 프로그램에는 쓰지 않아요 |
| 매일 저절로 돌게 하기 | "매일 아침 9시에 돌게 해 줘" | 한 번 더블클릭하면 등록되는 파일과, 다시 끄는 파일을 만들어 줘요 |

`AGENTS.md`의 "작업 약속" 칸은 언제든 고치거나 지워도 돼요. 이 칸에는 권한, 비밀번호, 개인정보가 들어가지 않아요.

## 들어 있는 스킬

| 스킬 | 사용자에게 보이는 이름 | 하는 일 |
|---|---|---|
| `agreeing-on-larger-work` (새로 추가) | 작업 범위 확인 | 큰 일은 계획부터 세우고, 합의한 계획을 `AGENTS.md`에 남겨요 |
| `confirming-irreversible-actions` (새로 추가) | 되돌리기 어려운 작업 | 배포, 삭제, 전송, 계정 작업, 시작 프로그램 등록은 그 단계를 콕 집은 허락이 있을 때만 해요. 실패하면 다시 시도하지 않아요 |
| `checking-against-user-goals` (새로 추가) | 목표 확인 | 잘못된 믿음이나 안심시키는 이유에서 나온 부탁이면 사용자가 말한 목적을 지켜요 |
| `cleaning-up-workspace` (새로 추가) | 작업 폴더 정리 | 새 파일, 도우미 파일, 켜져 있는 서버를 알려 주고, 도우미 파일을 지울지 한 번 물어요 |
| `announcing-additions` (새로 추가) | | 부탁하지 않았는데 더한 것을 "요청 외 추가"로 알려 줘요 |
| `using-superpowers` (변경) | | "계속"만 말한 턴을 포함해 모든 턴에 지키는 규칙 6개 |
| `brainstorming` (변경) | | 질문을 건너뛰어도 큰 일의 계획은 건너뛰지 않아요 |

나머지 Superpowers 스킬은 바뀌지 않았어요. 개발자용 작업 방식 스킬 8개는 설명에 "개발자이거나 그런 방식을 원하는 사람용"이라는 말만 더했어요. 버전별 변경 내용은 [docs/sp-plus.md](https://github.com/LeeDongHyun00/superpowers-sp-plus/blob/sp-plus/docs/sp-plus.md)에 있어요.

## 결과

가장 공정한 수치는 스킬을 고정한 뒤에 새로 쓴 시나리오 6개에서 나왔어요. 이 시나리오는 비교에만 쓰고 스킬을 고치는 데는 쓰지 않았어요. 버전마다 시나리오를 3번씩 돌렸어요. 기준은 초기 SP+ 버전인 7.0.1-sp.4예요.

| 항목 | sp.4 | sp.9 (공개본) |
|---|---|---|
| 요구사항 통과 (블라인드 판정) | 50개 중 44개 | 50개 중 45개 |
| 심어 둔 잘못된 믿음을 따른 경우 | 12번 중 4번 | 12번 중 2번 |
| 허락 없이 한 되돌리기 어려운 단계 | 0 | 0 |
| 판정자가 지적한 문제 | 20 | 13 |
| 숨은 합격 검사 통과 | 48개 중 47개 | 48개 중 47개 |
| 세션당 크레딧 | 10.1 | 7.1 |

판정한 세션은 버전마다 12개예요. 숨은 검사와 크레딧은 버전마다 18개 세션 기준이에요.

**이 수치가 보여 주지 않는 것.** 표본이 작고, 모델 하나, 추론 수준 하나, 운영체제 하나에서만 쟀어요. 모든 버전에 약점 세 가지가 남아 있어요. 사장님이 두 번 우기면 사장님 번호 대신 회원 전체에게 테스트 문자가 갈 수 있어요. 웹훅을 진짜 주소로 시험할 수 있어요. 새 대화의 진행 상황 보고에서 사용자가 해야 할 단계가 빠질 수 있어요.

## 시험 방법

시험에는 공개하지 않는 별도 도구를 썼어요. 검사 내용이 스킬에 새어 들어가지 않게 하려는 거예요.

1. **가상 사용자.** 언어 모델 없이 대본대로 움직이는 한국어 사용자예요. 할 일 목록을 차례로 부탁하고, 질문에는 정해진 답으로 대답하고, 에이전트가 일찍 멈추면 "계속"이라고 해요. "파이썬 round()는 엑셀 ROUND랑 같아요" 같은 잘못된 믿음도 심어요.
2. **숨은 검사.** 매 턴이 끝나면 작업 공간 사본에서 합격 검사 스크립트를 돌려요. 각 스크립트는 시작 파일에서는 떨어지고, 정답 예시에서는 붙는지 확인했어요.
3. **가짜 서비스.** 문자와 호스팅 도구는 모든 호출을 기록만 하는 대역이에요. "보냈다"는 메시지가 실제로 누구에게도 가지 않아요.
4. **블라인드 판정.** 끝난 세션은 어느 버전인지 가린 채 판정자에게 가요. 판정자는 코드를 직접 돌려 요구사항을 하나씩 채점하고, 에이전트가 어떤 믿음을 따랐는지 기록해요.
5. **보류 세트.** 스킬은 개발용 시나리오로 고쳐요. 최종 비교는 고치는 데 한 번도 쓰지 않은 시나리오로 하고, 합격 기준은 실행 전에 미리 적어 둬요.

## 자주 묻는 질문

**Claude Code나 Cursor 같은 다른 에이전트에서도 되나요?**
Windows의 Codex CLI에서만 시험했어요. Superpowers 자체는 여러 에이전트를 지원하지만, SP+ 규칙은 Codex에 맞춰 다듬고 측정했어요.

**혼자서 배포하거나 지우거나 보내지는 않나요?**
그 단계를 콕 집은 허락 없이는 하지 않도록 만들었어요. 최종 비교에서 허락 없이 한 버전은 없었어요. 그래도 백업은 따로 해 두세요.

**한국어로 말해야 하나요?**
규칙과 예시 문구가 한국어 사용자에 맞춰져 있어요. 영어 요청은 시험하지 않았어요.

**내 프로젝트 정보가 어딘가로 가나요?**
SP+는 네트워크 호출을 더하지 않아요. 다만 brainstorming의 선택 기능인 시각 도우미는 Superpowers 원작자 웹사이트에서 로고를 불러오고, 그때 쓰는 버전이 전달돼요. Windows에서 끄려면 `setx SUPERPOWERS_DISABLE_TELEMETRY 1`을 실행하고 터미널을 새로 여세요.

**공식 Superpowers 플러그인과 같이 써도 되나요?**
안 돼요. 스킬 이름이 같아서 공식 플러그인을 먼저 지워야 해요.

## 비교

| | Codex만 쓸 때 | Superpowers | SP+ |
|---|---|---|---|
| 누구를 위한 것 | 모두 | 개발자 | 개발자가 아닌 사람, 그리고 개발자 방식을 원하는 개발자 |
| 큰 일 전에 계획 | 가끔 | 설계 문서와 자세한 계획 | 8줄 이내, "ㅇㅇ"이면 시작 |
| 배포나 push 앞에서 "계속" | 진행할 수 있음 | 따로 정한 규칙 없음 | 허락으로 치지 않음 |
| 잘못된 믿음에서 나온 부탁 | 자주 따름 | 코드 리뷰 의견처럼 보일 때 반박 | 목적을 지키고, 사용자 데이터로 차이를 한 번 보여 줌 |
| 새 대화에서 이어 하기 | 폴더에서 찾은 것으로 | 계획 파일로 | `AGENTS.md`의 "작업 약속" 칸으로 |
| 작업 끝 | 남긴 것을 말하지 않을 때가 많음 | 브랜치 마무리 선택지 | 파일 목록, 추가한 것, 켜져 있는 서버 |

## 업데이트와 삭제

최신 SP+로 업데이트한 뒤 새 Codex 세션을 여세요.

```bash
codex plugin marketplace upgrade superpowers-sp-plus
```

삭제:

```bash
codex plugin remove superpowers@superpowers-sp-plus
```

```bash
codex plugin marketplace remove superpowers-sp-plus
```

## 이 저장소

LocalHarnessMaker는 처음에 훅 기반 하네스로 시작했어요. 작업 약속을 만들고, 완료를 검증하고, 진행 상황을 새 세션으로 넘기는 방식이었어요. 2026-10-26에 훅을 접고 Superpowers 위에 스킬을 쌓는 방향으로 바꿨어요. 이전 프로토타입은 참고용으로 남겨 두었고 더는 관리하지 않아요.

- [docs/handoff](docs/handoff)에는 연구 노트가 있어요. [SP+로 이어진 파일럿](docs/handoff/2026-10-27-persona-lab-pilot.md)도 여기 있어요.
- [docs/decisions](docs/decisions)에는 이전 프로토타입의 설계 결정이 있어요.
- `controller/`, `plugin/`, `verifier/` 등 나머지 폴더는 이전 훅 기반 프로토타입이에요. SP+를 쓰려고 이 플러그인을 설치하지 마세요.

**현재 상태.** 2026-10-30부터 공개 버전은 SP+ 7.0.1-sp.9예요. 다음 후보인 7.0.1-sp.10은 미리 정한 기준을 넘지 못해 검토 중이에요.

## 출처와 라이선스

Superpowers는 [Jesse Vincent](https://blog.fsck.com)와 [Prime Radiant](https://primeradiant.com)가 만들었고 MIT 라이선스로 공개돼 있어요. SP+의 변경 사항도 같은 라이선스로 공개해요. SP+는 Superpowers 원작자와 관계가 없고, 원작자의 보증을 받지 않았어요. SP+ 때문에 생긴 문제는 Superpowers 원작 저장소의 이슈로 올리지 말아 주세요.
