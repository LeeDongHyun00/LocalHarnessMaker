<h1 align="center">LocalHarnessMaker</h1>

<p align="center"><strong>Agent skills that let people who are not developers build small programs with Codex, talking the way they really talk.</strong></p>

<p align="center">
  <a href="https://github.com/LeeDongHyun00/superpowers-sp-plus/releases/tag/v7.0.1-sp.9"><img src="https://img.shields.io/badge/SP%2B-7.0.1--sp.9-0891b2?style=flat-square" alt="SP+ version 7.0.1-sp.9" /></a>
  <a href="https://github.com/obra/superpowers"><img src="https://img.shields.io/badge/based_on-Superpowers_7.0.1-24292f?style=flat-square" alt="Based on Superpowers 7.0.1" /></a>
  <a href="#install"><img src="https://img.shields.io/badge/works_with-Codex_CLI-7C3AED?style=flat-square" alt="Works with the Codex CLI" /></a>
  <a href="#results"><img src="https://img.shields.io/badge/tested_with-gpt--6.1--sol_medium-22c55e?style=flat-square" alt="Tested with gpt-6.1-sol at medium reasoning" /></a>
  <a href="https://github.com/LeeDongHyun00/superpowers-sp-plus/blob/sp-plus/LICENSE"><img src="https://img.shields.io/badge/license-MIT-24292f?style=flat-square" alt="MIT License" /></a>
</p>

LocalHarnessMaker is the research project behind **SP+**, a Codex plugin built on [Superpowers](https://github.com/obra/superpowers) by Jesse Vincent and Prime Radiant. SP+ is for a salon owner, a club treasurer or a parent who asks Codex for a small program and then answers "ㅇㅇ", "계속" or "알아서 해". It keeps every Superpowers skill, adds five skills and six standing rules, and was measured in scripted sessions with simulated Korean users.

The plugin itself lives in **[LeeDongHyun00/superpowers-sp-plus](https://github.com/LeeDongHyun00/superpowers-sp-plus)**. This repository is the project's front page and keeps its design records.

```
   ASK              AGREE             BUILD              CHECK              HAND OVER
┌──────────┐    ┌───────────┐    ┌────────────┐    ┌──────────────┐    ┌──────────────┐
│ a short  │───▶│ plan of 8 │───▶│ builds and │───▶│ against what │───▶│ stops before │
│ request  │    │ lines max,│    │ notes the  │    │ you said the │    │ deploy, send,│
│ in plain │    │ any "yes" │    │ plan in    │    │ result is for│    │ delete; lists│
│ words    │    │ starts it │    │ AGENTS.md  │    │              │    │ its files    │
└──────────┘    └───────────┘    └────────────┘    └──────────────┘    └──────────────┘
```

## Contents

- [Why](#why)
- [How it works](#how-it-works)
- [Install](#install)
- [Using it](#using-it)
- [What's inside](#whats-inside)
- [Results](#results)
- [How it was tested](#how-it-was-tested)
- [Common questions](#common-questions)
- [How it compares](#how-it-compares)
- [Update and uninstall](#update-and-uninstall)
- [This repository](#this-repository)
- [Credits and license](#credits-and-license)

## Why

Coding agents are tuned for developers, who read the plan, know what a push does and check the result. A beginner does none of that. In our first pilot with gpt-6.1-sol at medium reasoning, three things kept happening:

- **"계속" was read as permission.** After a bare "continue", the agent created a project on a hosting service the user had never named and tried a public `git push`.
- **A wrong belief won over the user's goal.** Told that plain UTF-8 never breaks in Excel, the agent changed the file, although the user had said earlier that they would open it in Excel.
- **Leftovers nobody mentioned.** Temporary folders and test files stayed behind in 11 of 12 workspaces, and two sessions left a server running.

Superpowers already makes the agent plan and verify. SP+ adds the rules a non-developer needs on top of that.

## How it works

You ask for something in a sentence or two. If it is more than a small change, Codex does not start writing code. It shows a plan of at most eight lines, with the defaults you would notice later, such as opening hours, time units and file names. Any reply that does not change the plan starts the work: "ㅇㅇ", "진행해" or "알아서 해".

The agreed plan goes into a short "작업 약속" section of your project's `AGENTS.md`. Codex reads that file at the start of every session, so "계속" in a new conversation continues with the next unchecked item. When everything is done, it says so instead of inventing new work.

While it builds, it checks the result against what you said the result is for. If you ask for a change because of something you heard, it keeps the version that serves your goal, shows you the difference once with your own data, and tells you where you can change it yourself. Files you had stay as they are, and converted copies go next to them.

When it reaches a step that is hard to undo, such as publishing, pushing, deleting your files, sending messages or registering a startup task, it stops at that step. It says what is ready and what the step would do, then carries on with the rest. It takes the step only after a yes that names it, such as "배포해 줘", and only on the service you named.

At the end it lists the files it made, any servers still running and anything it added that you did not ask for. It asks once whether to remove its helper files.

## Install

**Requirements**

- The Codex CLI with plugin support. SP+ was tested with Codex CLI 0.164 to 0.166 on Windows 11.
- Git, which Codex uses to download the plugin from GitHub.

If you use the official Superpowers plugin (`codex plugin list` shows `superpowers@openai-curated-remote`), uninstall it first from `/plugins` in the Codex CLI or from Plugins in the Codex app. Both plugins use the same skill names.

**1. Add the marketplace and install**

```bash
codex plugin marketplace add LeeDongHyun00/superpowers-sp-plus
```

```bash
codex plugin add superpowers@superpowers-sp-plus
```

<details>
<summary><b>Windows: <code>codex</code> is not recognized</b></summary>

The Codex app keeps its own copy of the CLI under `%LOCALAPPDATA%\OpenAI\Codex\bin`. In PowerShell, find it once and run the commands through it:

```powershell
$codex = (Get-ChildItem "$env:LOCALAPPDATA\OpenAI\Codex\bin" -Recurse -Filter codex.exe | Sort-Object LastWriteTime | Select-Object -Last 1).FullName
& $codex plugin marketplace add LeeDongHyun00/superpowers-sp-plus
& $codex plugin add superpowers@superpowers-sp-plus
```

Every other command on this page works the same way with `& $codex` in place of `codex`.
</details>

**2. Check the install**

```bash
codex plugin list
```

```text
PLUGIN                           STATUS              VERSION     SOURCE
superpowers@superpowers-sp-plus  installed, enabled  7.0.1-sp.9  ...
```

To see that a new session will load the SP+ skills, without calling the model:

```bash
codex debug prompt-input "hi" | grep -o "superpowers:agreeing-on-larger-work" | head -1
```

In PowerShell, `codex debug prompt-input "hi" | Select-String "agreeing-on-larger-work" -Quiet` prints `True`.

**3. Keep tool output small (recommended)**

SP+ was measured with this setting. Open `~/.codex/config.toml` (on Windows `%USERPROFILE%\.codex\config.toml`) and add this line near the top, above every line that starts with `[`:

```toml
tool_output_token_limit = 6000
```

**4. Try it**

Start a new Codex session in an empty folder and ask for something that stores data, for example:

```text
동네 미용실 예약 받는 웹페이지 만들어 줘. 예약은 저장돼야 해요.
```

With SP+, Codex answers with a short plan before it writes any code. A session that was already running keeps the skills it started with, so open a new one after installing.

## Using it

Talk to Codex as usual. These are the replies that matter:

| You want to | Say | What Codex does |
|---|---|---|
| start a plan as shown | "ㅇㅇ", "진행해", "알아서 해" | starts the work and keeps the plan in `AGENTS.md` |
| change the plan | "예약은 30분 단위로 해 주세요" | shows the changed plan, then starts |
| continue another day | "계속" or "이어서 해 줘" in a new conversation | continues with the next unchecked item, or says that everything is done |
| hand over a step that is hard to undo | "배포해 줘", "푸시해 줘", "문자 보내 줘" | takes exactly that step, on the service you named. "계속" alone never counts |
| share what it built | "친구들도 볼 수 있게 해 줘" | says who could open it with each option: only this PC, phones on the same Wi-Fi, or anyone with the link. It offers the same Wi-Fi first |
| keep your version after a warning | "엑셀에서 깨져도 괜찮아요, 그래도 바꿔 주세요" | makes the change. A repeat that only says who wants it ("팀장님이 그렇게 하래요") changes no file and gets one sentence you can pass on |
| find a missing file | "파일이 없어졌어요" | lists what it moved, renamed or deleted, the Recycle Bin included, and offers to put it back |
| work like a developer | "테스트 먼저 쓰고 해 줘", "코드 리뷰 받아 보고 싶어요" | uses the Superpowers developer workflows. For a non-developer's small program it skips them |
| run something by itself every day | "매일 아침 9시에 돌게 해 줘" | prepares a file you double-click once, and one that turns it off again |

You can edit or delete the "작업 약속" section in `AGENTS.md` at any time. It never holds permissions, passwords or personal data.

## What's inside

| Skill | Shown to users as | What it does |
|---|---|---|
| `agreeing-on-larger-work` (new) | 작업 범위 확인 | Plans larger work first and keeps the agreed plan in `AGENTS.md` |
| `confirming-irreversible-actions` (new) | 되돌리기 어려운 작업 | Publishing, deleting, sending, account actions and startup tasks only after a yes that names them, with no retry after a failed attempt |
| `checking-against-user-goals` (new) | 목표 확인 | Keeps the user's stated goal when a request rests on a wrong belief or a reassuring reason |
| `cleaning-up-workspace` (new) | 작업 폴더 정리 | Reports new files, helpers and running servers, and asks once about removing helpers |
| `announcing-additions` (new) | | Lists unrequested additions under "요청 외 추가" |
| `using-superpowers` (changed) | | Six standing rules that hold on every turn, including a bare "계속" |
| `brainstorming` (changed) | | Skipping questions does not skip the plan for larger work |

All other Superpowers skills are unchanged. Eight developer workflow skills now say in their descriptions that they are for developers, or for people who ask for that way of working. The changes in each version are listed in [docs/sp-plus.md](https://github.com/LeeDongHyun00/superpowers-sp-plus/blob/sp-plus/docs/sp-plus.md).

## Results

The fairest numbers come from six scenarios written after the skills were frozen and used for nothing else. Each version ran each scenario three times. The baseline is an early SP+ version, 7.0.1-sp.4.

| Measure | sp.4 | sp.9 (published) |
|---|---|---|
| Requirement checks passed, blind review | 44 of 50 | 45 of 50 |
| Planted wrong beliefs followed | 4 of 12 | 2 of 12 |
| Hard-to-undo steps taken without a yes | 0 | 0 |
| Problems flagged by reviewers | 20 | 13 |
| Hidden acceptance checks passed | 47 of 48 | 47 of 48 |
| Credits per session | 10.1 | 7.1 |

Reviewed sessions: 12 per version. Hidden checks and credits: 18 sessions per version.

**What this does not show.** These are small samples on one model, one reasoning level and one operating system. All versions still share three weak spots. An owner who insists twice may get a test message sent to every member instead of only to the owner's own number. A webhook may be tested against the real address. A status report in a new conversation may leave out the step the user still has to do.

## How it was tested

Testing used a separate harness that is not public, so that the checks cannot leak into the skills.

1. **Personas.** Scripted Korean users, with no language model in the loop, send a backlog of requests, answer questions from a fixed map, say "계속" when the agent stops early, and plant a wrong belief such as "파이썬 round()는 엑셀 ROUND랑 같아요".
2. **Hidden checks.** After every turn, an acceptance script runs on a copy of the workspace. Each script was checked against the starting files, where it must fail, and a reference solution, where it must pass.
3. **Fake services.** Messaging and hosting tools are stand-ins that record every call, so a "sent" message never reaches anyone.
4. **Blind review.** Each finished session is anonymized. A separate reviewer runs the code, grades every requirement and records which beliefs the agent followed.
5. **Held-out set.** Fixes are made on a development set. The final comparison uses scenarios that were never used for fixing, with pass criteria written before the run.

## Common questions

**Does SP+ work with Claude Code, Cursor or other agents?**
It has been tested only with the Codex CLI on Windows. Superpowers itself supports many agents, but the SP+ rules were tuned and measured on Codex.

**Will it publish, delete or send anything on its own?**
It should not take such a step without a yes that names it, and in the final comparison no version did. Keep your own backups anyway.

**Do I have to speak Korean?**
The rules and example phrases are written for Korean users. English requests were not tested.

**Does it send anything about my project?**
SP+ adds no network calls. Brainstorming's optional visual companion loads the Superpowers logo from the upstream authors' website, which reveals the version in use. To turn that off on Windows, run `setx SUPERPOWERS_DISABLE_TELEMETRY 1` and open a new terminal.

**Can I keep the official Superpowers plugin as well?**
No. Both use the same skill names, so uninstall the official one first.

## How it compares

| | Codex alone | Superpowers | SP+ |
|---|---|---|---|
| Who it is for | everyone | developers | non-developers, and developers who ask for developer workflows |
| Plan before larger work | sometimes | design document and detailed plan | eight lines at most, started by "ㅇㅇ" |
| "계속" before deploying or pushing | may go ahead | no rule for it | never counts as a yes |
| A request based on a wrong belief | often followed | pushed back on when it looks like code review feedback | goal kept, difference shown once with the user's data |
| Picking up in a new conversation | from what it finds in the folder | from plan files | from the "작업 약속" section in `AGENTS.md` |
| End of work | leftovers often not mentioned | branch finishing options | file list, extras and running servers |

## Update and uninstall

Update to the latest SP+, then start a new Codex session:

```bash
codex plugin marketplace upgrade superpowers-sp-plus
```

Uninstall:

```bash
codex plugin remove superpowers@superpowers-sp-plus
```

```bash
codex plugin marketplace remove superpowers-sp-plus
```

## This repository

LocalHarnessMaker started as a hook-based harness that wrote a task contract, verified completion and carried progress into a new session. On 2026-10-26 the project dropped hooks and moved to skills built on Superpowers. The earlier prototype stays here for reference and is not maintained.

- [docs/handoff](docs/handoff) holds the running research notes, including [the pilot that led to SP+](docs/handoff/2026-10-27-persona-lab-pilot.md).
- [docs/decisions](docs/decisions) holds the design decisions of the earlier prototype.
- `controller/`, `plugin/`, `verifier/` and the other folders are the earlier hook-based prototype. Do not install that plugin to get SP+.

**Status.** SP+ 7.0.1-sp.9 is the published version since 2026-10-30. A later candidate, 7.0.1-sp.10, did not meet its pre-written criteria and stays under review.

## Credits and license

Superpowers is by [Jesse Vincent](https://blog.fsck.com) and [Prime Radiant](https://primeradiant.com), released under the MIT License. SP+ changes are released under the same license. SP+ is not affiliated with or endorsed by the Superpowers authors. Problems caused by SP+ do not belong in the upstream Superpowers issue tracker.
