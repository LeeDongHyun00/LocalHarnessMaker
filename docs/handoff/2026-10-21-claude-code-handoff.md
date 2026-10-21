# Handoff to Claude Code - 2026-10-21

From: the Claude chat session that set up the project (Notion design, role prompts, codex-bridge).
To: Claude Code running on the user's Mac, acting as project manager per CLAUDE.md.

## 1. State of the repository at handoff

Repository: ~/Desktop/LocalHarnessMaker/LocalHarnessMaker, branch main, in sync with origin/main at commit ede9a31 (feat(eval): add audited baseline runner, metrics and first baseline A run).

Commits made today, in order: 764b86c lead skeleton, 8104ccb plugin probes, bb8f832 controller tests, 0bd9895 lead version 1 interfaces, b7ed814 plugin nested guard and stub loop, 96384a7 plugin 30-second control call, 45ce68c lead change summary, 03c5bfc controller codex_cli backend, 697add8 verifier rules and runner, ede9a31 eval runner.

Interfaces are frozen at schemas/VERSION = 1. Approved decision records: docs/decisions/0002 (judgment schema), 0003 (evaluation report schema), 0004 (codex_cli backend and HARNESS_NESTED guard). The measured hook contract is published at docs/hooks-contract.md.

Four worktrees exist beside the repository (lhm-plugin, lhm-controller, lhm-verifier, lhm-eval) with branches feature/plugin, feature/controller, feature/verifier, feature/eval. They were never used; all work happened on main in the main folder. Remove them when convenient: `git worktree remove ../lhm-NAME` and `git branch -d feature/NAME` for each.

## 2. Uncommitted work waiting for verification and commit

Three Codex jobs finished at 06:47 to 06:57 UTC and left changes in the working tree. The chat session could not verify or commit them because the Mac disconnected. Do this first.

For each: run the role's tests on the host, confirm `git status --porcelain` shows only the listed paths, then commit with the message below (plus attribution lines) and push.

| Role | Claimed tests | Paths | Message |
|---|---|---|---|
| Role 3 | .venv/bin/python -m pytest tests/controller -q -s: 131 passed | controller/, tests/controller/, state/STATUS-controller.md | feat(controller): add backend routing, judge and handoff commands |
| Role 4 | .venv/bin/python -m pytest tests/verifier -q: 125 passed, 6 skipped | verifier/, tests/verifier/, state/STATUS-verifier.md | feat(verifier): verify completion claims, bound feedback, and delegate judgments |
| Role 5 | .venv/bin/python -m pytest tests/eval -q: 55 passed, 2 skipped | eval/, tests/eval/, state/STATUS-eval.md | feat(eval): align reports and add audited harness orchestration |

What each job did:
- Role 3: codex_cli is now wired into --backend and is the default in controller/config.yaml; python -m controller judge and handoff exist; effort rules v1; BM25 case retrieval; a disabled local adapter (controller/LOCAL.md). Pending: live quality and cost comparison, local serving.
- Role 4: verifier/claims.py (claimed_without_evidence from the transcript format in docs/hooks-contract.md), reinstruct.py (failed items only, 300 chars, null at the limit), judge.py delegation validated against the judgment schemas. The six seatbelt tests are skipped inside Codex and must pass on the host.
- Role 5: reports now validate against schemas/evaluation-report.schema.json; audit rules also flag ~/.codex, the codex-bridge folder and the repository outside the task workspace; mocked harness-mode orchestration; public drafts of 100 single-session and 20 two-session tasks under eval/tasks/ with eval/GRADERS-PENDING.md listing 119 tasks that still need hidden graders.

Known problem: running all five test directories in one pytest invocation fails at collection because tests/eval/test_cli.py and tests/controller/test_cli.py share a basename (also test_check.py and others may collide). Running each directory separately works. Fix: a Role 1 job that adds `__init__.py` to every tests/ROLE/ directory or sets `--import-mode=importlib` in pyproject.toml, so that `make test` runs the whole suite. Do this before the first integration review.

Outstanding chat-side checks never completed: the per-role host test runs for the three jobs above.

## 3. Decisions already made by the user

1. Direction: a Codex plugin (three hooks plus a skill) that makes GPT-6.1 Sol finish tasks, follow intent and hand off between sessions. Defensive-wording suppression is out of scope.
2. Control model: GPT-6 Luna through the local Codex login (codex exec --model gpt-6-luna), verified working on 2026-10-21 (reply LUNA_OK, 10 seconds, 18.5k input tokens). The HTTP API with the same model is the fallback. Local Gemma 4 12B is the second stage.
3. STOP-E4 resolution: access-audit isolation. Private graders live outside the repository in LHM_PRIVATE_GRADERS, are copied into a grading copy only after codex exec exits, and any executor access to that path invalidates the run.
4. STOP-P3 resolution: a synchronous control-model call of up to 30 seconds inside UserPromptSubmit is accepted for the prototype.
5. Schema additions approved: judgment input and output schemas, evaluation report schema, codex_cli backend value and HARNESS_NESTED=1 guard.
6. Branch policy: everyone works on main in one folder; commits stage only the owning role's paths; the user approves merges and pushes.

## 4. Decisions still open for the user

1. The private grader root path. Role 5 used an external directory during its first run but its value is intentionally not recorded anywhere in the repository. Ask the user, or choose a new one such as ~/lhm-private, then set LHM_PRIVATE_GRADERS in the shell that runs Codex jobs for Role 5. Until then, the 119 drafted tasks have no hidden graders and no evaluation can run.
2. Plan usage budget. Both executor and control model draw on the ChatGPT subscription (plan_type prolite in the first run; primary window used_percent 2.0 after one task). The 10-task pilot must report usage before the full run of 100 plus 20 tasks per configuration.
3. Whether to keep the bridge running. It is optional once Claude Code drives Codex directly.

## 5. Next steps in order

1. Verify and commit the three pending jobs (section 2). Push.
2. Role 1 job: fix the test basename collision so `make test` runs all suites; write docs/plan.md and docs/decisions/0005-direction.md (0001 is taken by the eval isolation proposal); record the task-set hash later.
3. Role 2 job (D-3 and D-4): connect the real controller and verifier CLIs with HARNESS_BACKEND=codex_cli, implement handoff generation at the Stop hook, install.sh with --check, packaging. Then a host-side live demo of the full loop with the stub replaced by Luna: this needs real codex exec and must be run by Claude, not inside a job.
4. Role 5 job with LHM_PRIVATE_GRADERS set: write hidden graders for the 119 tasks, freeze task set v1, compute the hash, hand it to Role 1 for docs/eval-freeze.md. Then the 10-task pilot for baselines A and B; report usage; ask the user; full run.
5. Role 3 job: live smoke of codex_cli on schemas/examples/prompt.json (host-side, by Claude), then the local Gemma backend (D-3, needs the GPU decision).
6. Role 4 host verification: run the six seatbelt tests and the FastAPI smoke (tests/verifier/smoke.py) on the Mac.
7. First integration review on 2026-10-27.

## 6. Tools and locations

- Role prompts: prompts/01-tech-lead.md to prompts/05-eval-engineer.md. Shared rules: AGENTS.md.
- Bridge: ../codex-bridge (bridge.py, README.md in Korean, outbox/ holds every job's final.md, status.json and events.jsonl). Job history today: luna-check-001, p1-commit-pending-001 (showed .git is read-only), c01 to c04 (git_commit jobs), r3-cont-001, r4-cont-001, r5-cont-001-public.
- Codex binary: ../codex-bridge/codex-path.txt.
- Design document: Notion page "AI Project: GPT Operating Harness" (Korean); role prompts also mirrored on its subpage, but the repository copies are the current ones.
- Legacy material from the earlier project direction (harness/, experiments/, scripts/, top-level tests/test_harness.py and tests/test_integration.py) is preserved and not part of the role suites.

## 7. Things learned today that are easy to get wrong

- Codex cannot commit inside its sandbox; it also cannot run nested codex or seatbelt. Plan jobs around this.
- codex exec --json does not expose the applied reasoning effort; Role 5 verifies it from the native session JSONL (turn_context).
- Spotlight (mdfind) does not find the codex binary; it lives inside ChatGPT.app.
- Two sessions of the same role in one folder corrupt each other's work. The chat session once saw a lead commit absorb plugin files for this reason.
- Hooks fire under codex exec and in the TUI; Stop with decision=block and reason continues the turn once, and the second Stop carries stop_hook_active=true. This is the measured behavior the plugin relies on.
