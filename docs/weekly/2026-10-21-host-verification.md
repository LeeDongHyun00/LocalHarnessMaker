# Host verification - 2026-10-21

Claude Code checked the three Codex jobs from handoff section 2 on the Mac at HEAD bd6857d (equal to origin/main), with .venv Python 3.14.2. Bridge jobs c05 to c07 had already committed them at 13:51 UTC, so this check confirms them after the fact.

## Test runs and commit checks

| Role | Commit | Codex claim | Host result |
|---|---|---|---|
| Role 3 | e1e220e | 131 passed | 131 passed |
| Role 4 | 2751ac8 | 125 passed, 6 skipped | 131 passed; the six seatbelt tests in tests/verifier/test_sandbox.py pass on the host |
| Role 5 | 0963556 | 55 passed, 2 skipped | 55 passed, 2 skipped (tests/eval/test_task_fixture.py: external graders not configured) |

Command per role: `.venv/bin/python -m pytest tests/ROLE -q`. Unchanged suites: tests/lead 95 passed; tests/plugin 73 passed, 1 skipped (opt-in real Codex call). `make test` still fails at collection on the duplicate basename tests/eval/test_cli.py (handoff 5.2).

Ownership: each commit touches only its role's paths, its tests directory and its STATUS file. Secrets: the three diffs contain no API keys and no private grader path or contents. The tracked eval/reports/baseline-a-first-task/checkpoint.json holds only the runtime temp path.

Not run: tests/verifier/smoke.py. It needs FastAPI, which is not installed, and it makes live judge calls (handoff 5.6).

## Contract review of the three commits

Method: one reviewer per commit plus one reviewer for tests and claims. An independent agent tried to refute each finding; refuted findings are omitted. Claude re-read the code behind every high finding.

High:

| ID | Role | Where | Finding | Rule broken |
|---|---|---|---|---|
| H1 | 5 | eval/runner/audit.py:201-214 | Relative operands are resolved against the workspace whatever `cd` ran first. Only `$` and backtick count as unresolved, so globs, quote splitting, `~user`, `find -exec` and recursive grep from an ancestor of the private root are not caught. `cd / && cat <root without leading slash>/TASK/*` reads the graders, the audit returns clean, and the task is graded valid. `cd ~ && cat .codex/auth.json` is also clean. | AGENTS.md 3.4: unresolved operands are inconclusive, traversal must be inspected; decision 0003 invariant 4 |
| H2 | 5 | eval/runner/core.py:96 and 185, audit.py:111 | Grading copies, which contain the private graders, are retained in sibling TMPDIR/lhm-eval-* runtimes and never removed. The audit roots cover only the current task's copy, so a later task's executor can read an earlier task's graders and the audit stays clean. This also holds across separate runs. Task families share functions and specs, so an earlier task's graders largely cover later tasks. | AGENTS.md 3.4: never expose a grading copy to later executor turns; eval/README.md claims the copy never enters a later turn |
| H3 | 4 | verifier/reinstruct.py:19-21 | Only status=fail items are re-instructed. If every unmet item is unverifiable (missing file, ModuleNotFoundError, judge timeout), the verdict is overall=fail with reinstruct_message=null at attempt 1. plugin/hooks/_runtime.py:179 and eval/runner/core.py:304 then end the loop with retries left. | AGENTS.md 3.1: null only on pass or retry exhaustion; 3.3; schemas/examples/verdict_fail.json re-instructs an unverifiable item |
| H4 | 3 | controller/backends/routing.py:82, contract_gen.py:71 | A codex CLI that never started (not on PATH, or spawn OSError) is recorded as unknown usage instead of zero. The summed usage is then unknown, so `contract` exits 2 after a paid cheap_api fallback when an API key is set, and `judge` reports null usage even though only the HTTP call ran. config.yaml uses executable "codex", which is not on PATH in a plain Terminal (CLAUDE.md 2). | AGENTS.md 3.2: fallback on CLI unavailability; decision 0002: usage sums every call |

Medium:

| ID | Role | Where | Finding |
|---|---|---|---|
| M1 | 5 | eval/runner/core.py:369 | checkpoint.json in --out stores unredacted audit matches, so a run with detected access writes the private grader path under eval/reports/NAME/. |
| M2 | 5 | eval/runner/report.py:158 | A run halted by STOP-E1 writes a partial report with validity=valid and the full task-set hash. The halt reason appears only in run-diagnostics.json. |
| M3 | 4 | verifier/claims.py:90 | "All done except SC-3" marks SC-3 as claimed, so a failing SC-3 gets claimed_without_evidence. |
| M4 | 4 | verifier/claims.py:72 | "SC-1, SC-2, SC-3 done." credits only one of the three IDs. |
| M5 | 4 | verifier/judge.py:20 and 35 | The verifier kills the controller judge at 120 s, below the controller's 180 s per-call deadline, and the codex grandchild keeps running after the kill. |

Low, to fix in the same jobs:
- Role 3: test_codex_cli.py:160 is named for a missing CLI but never reaches that path. The same-model guard on fallback (routing.py:78) is untested.
- Role 4: no test checks that an unclaimed failing criterion keeps its own reason (test_claims.py:66). conftest.py:18 always sets HARNESS_MAX_ATTEMPTS and HARNESS_BACKEND, so the claimed defaults are never exercised.
- Role 5: the harness loop counts reinstruction segments against retry_limit (core.py:312). Runtime-invariant failures exit 1 instead of 2 (__main__.py:36). The unresolved-operand test (test_access_audit.py:133) passes through a different code path. The seeded-bootstrap test (test_report.py:24) does not depend on the seed. The retired-schema shim test (test_report.py:72) substitutes its $ref. One STATUS-eval Done bullet cites a path instead of a command.

Unsettled: reinstruct.py:23 details at most three failed items and counts the rest. STATUS-verifier records this as an assumption, and it conflicts with the per-item rule only when descriptions are short.

## Consequences for the plan

The executor sandbox does not deny reads, so the access audit is the only isolation control. Until H1 and H2 are fixed, an executor can read private graders while its task is graded valid, so no evaluation result counts as evidence. This blocks the 10-task pilot (handoff 5.4). H3 breaks the retry loop the plugin relies on and must be fixed before the Role 2 live demo (handoff 5.3). H4 must be fixed before the Role 3 live smoke (handoff 5.5), or that smoke must run with an absolute codex path in config.

## Fix jobs on 2026-10-22

Claude ran the jobs directly with codex-cli 0.162.0-alpha.17.2 (gpt-6.1-sol) from the repository root. Prompts, events and final reports are in ../codex-bridge/outbox/JOB/. Plan usage (primary weekly window) went from 4 to 7 percent across the five jobs.

| Job | Scope | Codex claim | Host result | Commit |
|---|---|---|---|---|
| r4-fix-001, Role 4, high | H3, M3, M4, M5, low items | 151 passed, 6 skipped | 157 passed, including the six seatbelt tests. Probes: an unverifiable-only verdict is re-instructed at attempt 1 of 3 and null at 3 of 3; "All done except SC-3" claims nothing; comma lists credit every ID; the judge runs in its own process group | 3545c19 |
| r5-fix-001, Role 5, medium | H1, H2, M1, low items | 88 passed, 2 skipped, 1 xfailed | Same. Every review bypass and cross-task grading-copy read is access_detected, and no private root appears under --out. Regression: 54 of 59 real Codex commands audited inconclusive | 5faf49d |
| r5-fix-002, Role 5, high, resumed | The regression: wrapped `/bin/zsh -lc` commands and workspace globs | 306 passed, 2 skipped, 1 xfailed | Same. 48 of 59 real commands clean; all detections unchanged | 1846896 |
| r3-fix-001, Role 3, medium | H4, low items | 145 passed | 145 passed. contract with codex missing exits 0 after one cheap_api call | 9ebad81 |
| r1-cont-001, Role 1, medium | Unified collection, docs/plan.md, decision 0005, rule 6 wording | make test with zero collection errors | make test: 777 passed, 3 skipped, 1 xfailed. make validate-schemas: 6 schemas and 8 examples | b212873 |

## Decisions taken on 2026-10-22

The user told Claude to proceed with the recommended options for the open decisions, and set LHM_PRIVATE_GRADERS for Role 5 jobs; the path stays out of repository files.

1. M2, halted runs, with no schema change. A run halted by STOP-E1 writes no report.json and exits 2 (the run is incomplete). It prints the halt reason and the counts on stderr, and it keeps checkpoint.json and run-diagnostics.json so that a later run with the same --out resumes. The full report is written only when every configured task has a result. This replaces the strict xfail tests/eval/test_runner.py::test_stop_e1_partial_report_is_invalid_with_counts.
2. Deadlines. Every caller outlasts its callee, and every caller kills the callee's whole process group on expiry. Initial values:
   - UserPromptSubmit: hook timeout 40 s, contract call 30 s (both unchanged, user-approved).
   - Stop: hook timeout 600 s; inside it, verifier check 480 s and controller handoff 90 s.
   - Verifier judge: 120 s (unchanged).
   - Controller codex_cli: the per-call deadline (now 180 s) will be set from Luna latencies that Claude measures on the host, so that three calls fit inside the judge deadline. Until then the callers cut it off.
3. Dynamic execution. Python and cat heredoc scripts stay inconclusive under AGENTS.md 3.4. The 10-task pilot reports how many tasks this invalidates. The policy is revisited, through a Role 1 decision record, only if that share exceeds 10 percent of pilot tasks.
4. Task families. Keep the 25 related families of four task types plus the 20 two-session tasks: the task type is the experimental factor, and rebuilding the set before the 2026-10-27 freeze would leave no time for validated graders. Reports keep the task-cluster metrics of decision 0003. Claude's final evaluation also reports family-cluster bootstrap intervals, and a claim counts only if it holds under them.
5. Bridge. Use the bridge only for private-write jobs, run with --once so that it exits after the job. All other jobs run directly.
6. Plan usage. No change: the pilot reports usage before any full run, and a full run needs the user's explicit approval.
7. Minor. docs/plan.md cites the local path of the Notion export. The Role 1 job that records the freeze hash will cite the Notion page instead.

## Later on 2026-10-22

Live control calls on the host (codex_cli, gpt-6-luna, first call, no fallback): contract 15.6 s with the machine idle and 20.0 s under four concurrent Codex jobs, judge 14.4 s, handoff 13.2 s. All three outputs were schema-valid, and stdout was exactly the output path.

Revisions to decision 2 (deadlines):
- Controller per-call deadline, codex_cli and cheap_api: 35 s (commit 0d57e36). Three calls take about 108 s, which fits the 120 s judge budget.
- Stop hook timeout 660 s. Inside it: verifier check 480 s, with the verifier's own overall budget of 450 s (HARNESS_VERIFY_BUDGET_SECONDS); controller handoff 120 s; validate-handoff 5 s; and a cleanup reserve.
- UserPromptSubmit stays at 40 s with a 30 s contract call (user-approved). This path is a documented exception: the plugin cuts the contract call off before the controller's 35 s deadline, so the controller's fallback cannot run there.
- Timeouts in hooks.json are JSON integers. Every hooks.json verified on the host used integers.

Further decisions:
8. Process shutdown. Every harness process that starts children (the plugin hooks and verifier check) follows one protocol. On SIGTERM, SIGHUP, SIGINT or its own deadline, it sends SIGTERM to its child process groups, waits 2 s, then SIGKILLs the groups still alive. After a child exits normally, it kills that child's group. A review reproduced orphaned verifier, controller and test processes after the hook was terminated.
9. Project scoping. The installer marks the target project. Hooks exit with no output and no writes outside a marked project, so a user-level install does not touch other work.
10. Handoff when retries run out. The Stop hook also writes a validated handoff, whose remaining list carries the unmet items. If generating it fails, the previous handoff is renamed so that it is not injected as current.

Evaluation set: Role 5 wrote and validated private graders for all 120 tasks (80205d3, ad7d7be). Claude checked them on the host:
- 120 of 120 valid.
- No private path and no task-specific grader line in any public file.
- Independent mutation testing of the references: 1021 of 1067 mutants killed, and every inspected survivor in the twelve weakest tasks was behavior-equivalent.

The task set was frozen at 7cdaf3b with digest b78913b04280f6696d419d2afdc96b152675973d82f05199ddef848986285d1f, recorded in docs/eval-freeze.md (57a9606). The validation runs of r5-graders-001 had left 1019 grading copies in the system temporary directory; Claude moved them into the private root, and r5-graders-002 stopped validation runs from leaving such copies. ~/.claude is now a protected audit root, because Claude's transcripts live there.

## Host checks after the plugin and verifier fixes (2026-10-22)

- Commits: plugin ccdf683; verifier e927b73 and 7de2f99. make test on the host: 972 passed, 1 skipped (the opt-in real Codex test).
- Real process trees on the host:
  - plugin Stop hook: SIGTERM, group SIGHUP, and a child that exits while its grandchild holds the pipe each leave 0 processes. An unmarked directory gets 0 bytes of output and no .harness/.
  - verifier check under sandbox-exec: SIGTERM leaves 0 processes; a 6 s budget gives a valid verdict in 5 of 5 runs; a command that exits 0 while a grandchild holds stdout passes in 0.3 s. Before the fixes this case waited past 40 s and left the grandchild behind.
- Install: the README procedure works in a temporary HOME and CODEX_HOME. --check reports missing hooks and a missing skill separately, a reinstall is idempotent, hook timeouts are integers (10/40/660), and the real ~/.codex was unchanged.
- Live demo, plugin/evidence/2026-10-22-real (232f23d):
  - Request stage: gpt-6-luna generated the contract (14603 input and 251 output tokens). The executor showed the summary and stopped at the approval gate with an empty workspace.
  - After approval: result.txt was created, the real verifier passed on attempt 1, and a validated handoff was saved.
  - plugin.check_demo_evidence: approval_gate true, real_task_verified true, maximum hook overhead 0.19 s.
  - Contract quality note: Luna described "ok\n" as two bytes; the executor flagged it, and the check itself was correct.
- Prices: OpenAI's official pricing page (developers.openai.com/api/docs/pricing, read 2026-10-22, standard tier, context up to 272K), USD per 1M tokens:
  - gpt-6.1-sol: input 2.00, cached input 0.10, output 10.00;
  - gpt-6-luna: input 0.10, cached input 0.01, output 0.50.
  At these prices the recorded baseline A task (58248 input, 54656 cached, 524 output) comes to about 0.018 USD.
- Plan usage: the primary weekly window was 4 percent at 2026-10-21 06:57 UTC and 21 percent at 2026-10-22 01:52 UTC. In between, the Codex development jobs used 26.7M input tokens (1.35M uncached) and 0.37M output tokens. Resumed long sessions were the most expensive; r2-cont-003 alone sent 5.0M input tokens. The window resets at 2026-10-28 04:03 UTC.

## Codex version change and policy (2026-10-22)

At about 03:57 UTC the ChatGPT app updated its bundled codex CLI from 0.162.0-alpha.17.2 to 0.163.0-alpha.11.1. No other codex binary exists on the Mac. Every run before that used 0.162.0-alpha.17.2: all 30 pilot executor sessions, according to their native session_meta cli_version and their report metadata, and every development job up to 03:50 UTC. The first two-session smoke after the change stopped before any model call: the runner reported "Installed Codex version differs from pinned configuration". The hook probe likewise refuses the new version.

11. Codex version policy (user decision: the version may keep changing). Do not hold or roll back versions. Record the installed version in every run. Compare only reports produced with the same version (SC-3); a mixed-version comparison is diagnostic only. When the version changes, rerun the hook compatibility probe and a one-task audit compatibility smoke before any large run. A run must stop if the version changes in the middle of it. The plugin keeps a list of verified versions instead of a single pin. CLAUDE.md section 2 records the procedure, and Role 1 records decision 0006.

## Codex usage limit reached (2026-10-22, about 13:15 UTC)

The Role 5 job r5-full-002 (two-session runner fixes and the version policy) ended with "You've hit your usage limit ... try again at Oct 28th, 2026 1:03 PM". A minimal gpt-6-luna call afterwards failed with the same message, so every Codex call, development or evaluation, is blocked until 2026-10-28 13:03 KST (04:03 UTC), the weekly reset. The binding limit is not the primary window shown in the session logs (69 percent at the end): the last rate_limits record names limit_id "premium" with no percentage, so the remaining budget for gpt-6.1-sol and gpt-6-luna cannot be read from the logs.

Usage between 01:52 and 13:15 UTC: eleven development jobs sent 13.7M input tokens (0.64M uncached) and 0.16M output tokens; the pilots (30 sessions) and the two-session smoke attempt came on top. At API prices the day's development jobs would have cost about 4 USD.

State of r5-full-002: no final report and no Commit plan. The working tree holds its unfinished changes (10 files, about 1700 patch lines, plus eval/configs/full-a.yaml, full-b.yaml, smoke-two-session-a.yaml, eval/reports/full-estimate.md and eval/runner/compare_versions.py). Claude backed them up outside the repository (codex-bridge/outbox/r5-full-002/partial-backup/, base commit 55f2b1d). tests/eval: 530 passed, 1 failed (the new STOP-3 guard test, test_paid_call_guard_includes_two_day_control_and_fallbacks, which builds a config the loader rejects; Codex was fixing it when the limit hit). STATUS-eval.md and CHANGES.md still describe r5-full-001 (504 passed).

Claude re-ran the review reproductions against the unfinished tree with mocked executors: evidence publishing no longer takes files from the workspace or through symlinks (F1, R5-TS-2); regrade accepts runs with invalid two-session tasks and keeps timeouts as timeouts (R5-TS-3, R5-TS-4); a runner crash during a session resumes instead of raising KeyError (R5-TS-5); a day-1 timeout or executor error now continues to day 2 (R5-TS-1), so the reviewers' old expectation of a halt no longer applies. F2 (pre-created day-2 contract) and the STOP-3 count were not re-checked. The full configurations are on codex-cli 0.163.0-alpha.11.1.

Nothing from this job is committed. It needs Codex to finish: the failing test, F2 and STOP-3 verification, STATUS, CHANGES and a Commit plan.

## 2026-10-23: scope approval, full baseline A and harness preparation

The usage window restarted early (0 percent at 02:00 UTC). r5-full-003 finished the interrupted two-session work (b04f9b0). r5-compat-001 added the 0.163 thread_settings_applied record and the usage-limit halt (c0c9bb3). The 0.163 two-session smoke was then valid and passed (9a997e3). Integration review 1 is docs/weekly/2026-10-27.md.

12. Scope (user decision, 2026-10-23): all five proposals in integration review 1 are approved. Local Gemma and QLoRA are dropped, and parity is reported as not measured. C runs on a stratified 20-task subset whose templates the user fills. B runs on the 100 single-session tasks only. The schedule is W1 to W3, and an API key is a fallback only. The user also said usage limits are no longer a concern: continue to completion up to, but not including, the local LLM stage. Role 1 records this as decision 0007.

Full baseline A started at 02:26 UTC from b9ac131: eval/configs/full-a.yaml, 120 tasks, 140 executor sessions, codex-cli 0.163.0-alpha.11.1. Logs are in codex-bridge/outbox/run-full-a/.

Two operating rules follow from how the runner works:
- The report records `git rev-parse HEAD` and reads eval/prices.yaml when it is built, at the end of the run. Claude therefore commits nothing on main while a measurement runs. Verified job results wait and are committed after the run's report. Role 5 now records the commit at run start (r5-harness-001).
- A measurement must not see code changes in the paths it uses: eval/ for every run, plus controller/ and verifier/ for harness runs, because the runner launches them as fresh subprocesses. Role 5 works in a separate git worktree (../lhm-r5-harness, branch r5/harness-smoke, its own .venv) while a run is in progress. A shared venv would not isolate it, because the editable install maps every package to the main checkout.

Jobs during the run:
- r2-cont-006: adds 0.163 to plugin/VERIFIED_VERSIONS.json, records the host checks in STATUS, and prepares the real two-session handoff demo (plugin/two_session_demo.py). Host: tests/plugin 200 passed, 1 skipped. Commit held.
- r1-cont-004: decision 0007, plan and role prompt wording. Host: tests/lead 96 passed. Commit held.

Gap found while preparing the harness smoke: harness-mode reports leave control costs and control_model null, so the harness's cost_per_pass would be null. Judge calls inside `verifier check` discard the controller's control_call usage lines. The controller logs one control_call line per generation, including retries and the fallback. Two jobs fix this without any interface change:
- r4-cont-006 forwards the judge children's control_call and control_cli_events lines on stderr, with one judge_delegation summary line per criterion.
- r5-harness-001 prices every control call from those lines with eval/prices.yaml, keeps unknown usage null, and adds the harness smoke, full harness and reduced B configurations with their STOP-3 estimates.

Host verification of the three jobs (commits held until full A is reported):
- r3-cont-004 (controller): tests/controller 153 passed. Decision 0007 is applied: the local selector stays, and the contract exit-2 behavior is unchanged. It adds `python -m controller.measure_contracts`, a 30-sample codex_cli measurement gated by --i-have-approval; it estimates 0.066 USD and Claude runs it after the commits.
- r4-cont-006 (verifier): tests/verifier 298 passed on the host, the six Seatbelt tests included. A live `verifier check` with one file_exists and one llm_judge criterion passed in 7 s. Its stderr carried the real controller control_call line (gpt-6-luna, 15442 input, 58 output tokens, 0.0015732 USD) and the summary `judge_delegation {"accounting_complete":true,...,"outcome":"completed"}`. It also adds `verifier sample`.
- r5-harness-001 (eval, worktree): tests/eval 621 passed in the worktree venv. Its parser read the live verifier stderr above: one judge call priced at 0.0015732 USD from eval/prices.yaml, the controller's own figure. Setting accounting_complete to false gave null. Configs: smoke-harness, with 2 tasks and reinstruction_limit 2; full-harness, which is full A with harness true, codex_cli and reinstruction_limit 2; and full-b, now the 100 single-session tasks. Committed on branch r5/harness-smoke as 9c81ecb. Review notes went to r5-baseline-c-001: markers matched anywhere in a line, zero delegations treated as incomplete for all-judge contracts, a spurious control_model warning for non-harness runs, and estimates that assume 5000 input tokens per control call against about 15000 measured.

Full A attempt 1 halted at 03:00 UTC after 40 of 120 tasks. Task two-session-pairwise-edges failed on day 2 after 74 s with exit 1. Its --json stream ended with the following error and turn.failed events:

    Selected model is at capacity. Please try a different model.

The runner recorded the task as outcome "error", an audit-clean valid failure, and stopped with STOP-E1. 39 of the 40 finished tasks passed. A capacity error is a service condition, not a model outcome, and the runner has no rule for it yet. Counting it would understate A, so the attempt is kept as diagnostic evidence only: eval/reports/full-a-attempt1/, with no report.json. Full A restarts from scratch after the Role 5 fix (r5-capacity-001). Claude's leak scan of the attempt found 0 private markers and 0 distinctive grader lines, with 717 lines indexed at family-level sharing.

After the held commits (879245e, 53cb8a9, 605b970, 4f23d59) and the cherry-picked Role 5 commits (f2e8d9e, 1b945de), the full suite on main gives 1396 passed and 1 skipped (the opt-in live Codex test).
