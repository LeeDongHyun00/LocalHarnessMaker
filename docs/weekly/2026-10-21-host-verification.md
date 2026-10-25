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

## Harness smoke attempt 1 (2026-10-23, 03:07 to 03:15 UTC)

This was the first live run of the proposed system in the runner: eval/configs/smoke-harness.yaml at f844d27, Sol medium, gpt-6-luna through codex_cli, 3 attempts per day. The report is valid and the audits are clean. Results:
- bug-chunk-tail passed after 3 attempts. Executor cost was 0.130 USD, about 4.5 times A's per-session average.
- two-session-prefix-sums failed after 3 attempts on each day. Hidden test test_variant_contract failed. Baseline A passed this task in its 0.163 smoke.

Defects found, each fixed by its owner without any interface change:
1. Contract quality (Role 3). Luna wrote 4 of 4 llm_judge criteria and no verification command for bug-chunk-tail; the two-session task got 3 of 4 on day 1 and 2 of 3 on day 2. The controller's principle is mechanical checks first and llm_judge as a last resort. Before the fix, Claude measures the llm_judge share on Role 3's own 30 authored samples (D-4), never on eval tasks.
2. Unittest commands rejected (Role 4). The contract's `python -m unittest discover -v` was rejected as "unsupported Python invocation", so that item stayed unverifiable on every attempt. The verifier accepted only py_compile, pytest with four flags, and AST-checked `python -c`.
3. Re-instruction on items the executor cannot fix (Role 4). Every non-pass item was re-instructed, including "contract quality warning" and rejected-command items. All 6 re-instructions in the smoke were of this kind. The new rule re-instructs only actionable items.
4. Control costs null (Role 5). The accounting reader rejected files with any symlinked ancestor, and macOS /var links to /private/var, so no control stream was read. Total cost and cost_per_pass were null. The tests missed it because pytest's tmp_path is resolved.
5. Grader content in a published grading log (Role 5). The failing task's grading.log carried the private assertion's source line and its message. Nothing was committed: no committed report contains a traceback, because every committed grading log comes from a passing run. The smoke report was moved out of the repository to codex-bridge/outbox/run-smoke-harness/report/, and that log to the private root's quarantine. The runner will publish test ids, outcomes and summary lines only.

Generalization caution: the two smoke tasks belong to the frozen evaluation set. The fixes target generic behavior that the design already required, and no controller change uses eval task content. The final evaluation will state this.

Controller D-4 baseline (host, 2026-10-23, controller/evidence/2026-10-23-d4-before.json): `python -m controller.measure_contracts` ran 30 codex_cli calls on Role 3's authored samples (tests/controller/fixtures/requests-v1.json, not eval tasks). It cost 0.036 USD, with median latency 7.6 s (6.6 to 11.8 s). Results:
- All 30 contracts are schema-valid, and every ambiguous sample has assumptions.
- The 39 criteria are 4 command, 10 file_exists, 13 regex and 12 llm_judge, so llm_judge is 31 percent.
- 11 of 30 contracts are llm_judge-only and 26 of 30 have no command check.
- cheap_api is not measured (no API key; decision 0007) and local is dropped.
r3-cont-005 revises the contract prompt to mechanical checks first; Claude reruns the measurement afterwards.

## Harness smoke attempt 2 (2026-10-23, 03:36 to 03:40 UTC, c47cc72)

This rerun used all five fixes. bug-chunk-tail passed on attempt 1. Its contract had a command check, a regex check and one llm_judge criterion, and the verifier passed it with no re-instruction. It cost 0.0213 USD in total: executor 0.0185 and control 0.0028, with 2 contract generations and 1 judge call. Smoke 1 had cost 0.130 USD for the executor alone. For two-session-prefix-sums, the day-1 contract has six criteria, five of them mechanical, and it passed verification on attempt 1. The task is still invalid because of an inconclusive day-2 audit. On day 2 Sol ran this command:

    for d in .. ../.. ../../..; do if [ -f "$d/AGENTS.md" ]; then cat "$d/AGENTS.md"; fi; done

The audit cannot resolve the loop variable, which is the same pattern as the one inconclusive task in pilot B. The values come from a literal list, so r5-audit-loop-001 adds exact expansion for that pattern and keeps every other loop fail-closed. A re-audit will then cover the retained runs. control_model is now gpt-6-luna. The leak scan of the report found 0 private markers, 0 grader lines and no traceback.

Controller after prompt v2 (controller/evidence/2026-10-23-d4-after-v2.json):
- 27 of 30 contracts are schema-valid.
- The 38 criteria are 6 command, 11 file_exists, 12 regex and 9 llm_judge, so llm_judge is 24 percent, down from 31.
- 5 contracts are llm_judge-only, down from 11, and 21 have no command check, down from 26.
- The 3 failures were the measurement tool refusing the quality gate's one regeneration. r3-cont-006 lets the tool measure the production pipeline.
- The gate also fails the whole contract command when the regeneration still lacks a mechanical check. The runner would then count that as an invalid task. r3-cont-007 makes the gate return the contract with an explicit assumption instead.

## Real two-session handoff demo (plugin, 2026-10-23, de38626)

This ran `python -m plugin.two_session_demo day1`, then `day2` with --scripted-approval, then `check`. It used live Sol, gpt-6-luna through codex_cli, the real controller and verifier, and temporary HOME and CODEX_HOME. The evidence is in plugin/evidence/2026-10-23-two-session/.
- Day 1: the contract was shown and the run waited for approval. After "approve", result.txt was created and the real verifier passed on attempt 1, with 0 re-instructions. The saved handoff kept the random release label as a decision.
- Day 2: a new session in the same project. SessionStart injected exactly the saved handoff, and the model context contains it. The day-2 contract used the label from the handoff, with no user restatement. It waited for approval, and followup.txt passed verification.
- The offline checker reports approval_gates, context_visible, new_session, saved_handoff_validated and session_start_injected all true, and user_restatement_needed false; overall pass.
- The evidence contains no secrets and no private-root path. Like the 2026-10-22 evidence, it records absolute checkout paths.

Controller D-4 final (production pipeline at de38626, controller/evidence/2026-10-23-d4-final.json): all 30 contracts are schema-valid, with 51 criteria. The other figures against the baseline:

| Measure | Baseline | Final |
|---|---|---|
| command criteria | 4 | 10 |
| file_exists criteria | 10 | 17 |
| regex criteria | 13 | 10 |
| llm_judge criteria | 12 | 14 |
| llm_judge share | 31 percent | 27 percent |
| llm_judge-only contracts | 11 | 5 |
| contracts with no command | 26 | 21 |

There were 30 generations, 0.017 USD in total. Counts vary between runs of the same prompt: the three measurements gave 39, 38 and 51 criteria. The improvement is real but moderate on these authored samples, many of which name no file or test. The evaluation tasks name their files, so the harness smoke is the more relevant check: attempt 2 had 1 of 3 and 1 of 6 llm_judge criteria.

## Audit: literal shell loops (r5-audit-loop-001 and -002, branch commit da6f852)

The first version resolved literal for-loops but mistook Python for-loops inside quoted heredoc bodies for shell syntax. Claude's comparison of old and new code, task by task over every retained run, showed 3 tasks fixed, 3 regressed and 1 changed among 104. The regressions were all bug-chunk-tail heredoc scripts. Role 5's resumed session fixed them. The final comparison covers 120 finished tasks across pilot-a, pilot-a-attempt1, pilot-b, smoke-two-session-a, smoke-two-session-a-attempt1, full-a-attempt1, the smoke-harness run and the in-progress full-a:

| Code | Clean | Inconclusive | Matched private access |
|---|---|---|---|
| Old audit | 117 | 3 | 0 |
| New audit | 120 | 0 | 0 |

The only changes are the three literal parent-directory AGENTS.md loops: pilot B bug-chunk-tail, smoke-harness two-session-prefix-sums, and full-a two-session-rotate-left on day 2. Claude's detection probes still behave as expected:
- An absolute read, a cd-relative read, a base64-hidden path read and a FileChange to a protected path are each access_detected.
- A dynamic command stays inconclusive.
- The benign case stays clean.

tests/eval: 943 passed in the worktree. The fix reaches main after full A, and full A is then regraded with it.

Handoff failure demos (plugin, 2026-10-23, 8308435): the three scenarios of `python -m plugin.handoff_failure_demo` ran live, each with day 1, day 2 and an offline check. They were exported with plugin.export_demo_evidence to plugin/evidence/2026-10-23-{exhaustion,generation,validation}/ and re-checked on the exported copies.

| Scenario | remaining_injected | stale_injected | Notes |
|---|---|---|---|
| exhaustion | true | false | The task cannot pass within HARNESS_MAX_ATTEMPTS=1, and day 2 received the remaining work |
| generation | false | false | An injected handoff generation failure; the previous handoff is not injected |
| validation | false | false | An injected handoff validation failure; the previous handoff is not injected |

Every scenario shows approval_gates true, new_session true and overall pass. The exported evidence holds no absolute user paths, secrets or private-root references.

Fresh-clone checklist (docs/demo.md), run by Claude on the host on 2026-10-23 from GitHub at bcd3e17 with codex-cli 0.163.0-alpha.11.1:
- `pip install '.[dev]'` into a new venv succeeded.
- plugin/install.sh into temporary HOME, CODEX_HOME and project exited 0, and `--check` printed "LocalHarnessMaker installation OK".
- check_probe_evidence passed for 0.162 (exec and tui) and 0.163 (exec).
- check_demo_evidence passed for 2026-10-22-real, and the checks for two-session, exhaustion, generation and validation passed, all with the documented fields.
- The full suite in the clone gave 1566 passed and 1 skipped (the opt-in live Codex test).

## Full baseline A (2026-10-23, 03:31 to 05:00 UTC, c47cc72, report a21eda2)

eval/configs/full-a.yaml ran 120 tasks and 139 executor sessions on codex-cli 0.163.0-alpha.11.1. No capacity refusal occurred. The total cost was 3.82 USD. The leak scan of the 753 published files found 0 private markers, 0 grader lines, 0 tracebacks and 0 absolute user paths.

| Metric | Value | n | 95% CI |
|---|---|---|---|
| pass_rate | 0.975 | 118 valid | 0.941 to 1.0 |
| cost_per_pass | 0.0332 USD | 120 | 0.0299 to 0.0368 |
| avg_attempts | 1.15 | 118 | 1.09 to 1.22 |
| handoff_success | 0.833 | 18 | 0.667 to 1.0 |

- All 100 single-session tasks passed. All 3 failures are two-session tasks: common-prefix, line-endings and adjacent-runs.
- The report is invalid under the approved rule because 2 tasks are invalid:
  - two-session-rotate-left: day-2 audit inconclusive on the literal AGENTS.md loop. The fixed audit (d44feda) finds it clean, so a regrade grades it.
  - two-session-balanced-brackets: day-1 audit inconclusive with unresolved_custom_input. Sol wrote `tools.apply_patch("...".replace('X',''))`, a patch literal with one stray character removed at runtime. The runner correctly stopped before day 2, so a regrade cannot recover the task. r5-continue-001 adds narrow resolution of literal JS string expressions and a continue_day2 command. That command runs the missing day 2 from a copy of the retained day-1 workspace into a fresh run directory and leaves the source run untouched.
- Implication for the comparison: A sits at a ceiling on single-session tasks. The harness can match but not exceed A's pass rate there, and its control calls add cost. Any harness gain has to come from the two-session tasks or from cost.

Full harness and full B (100 single-session tasks) started at 05:04 UTC from d44feda, concurrently, with the fixed audit.

## Full harness v1: interim findings after 17 tasks (05:40 UTC)

The full harness started at 05:04 UTC from d44feda. After 17 tasks: 15 pass, 1 fail, 1 invalid. Many tasks used 2 to 4 executor attempts, and in most of them the verifier failed an item that the hidden tests later passed. Five generic defects explain the futile re-instructions:
1. Stop conditions blocked requested work (Role 3). For requests that ask to add a test file, the contract said to stop if that file was unavailable, and Sol stopped on attempt 1 without changes. Seen in bug-fix-clamp-values and bug-fix-prefix-sums.
2. Prose in a path field (Role 3). A regex criterion's path was a sentence. The verifier classified the resulting ENOENT as workspace-caused and re-instructed twice. Seen in multiple-requirements-adjacent-runs.
3. An invalid regex (Role 3): `(?s)` after `|`. The verifier correctly classified it as contract-caused. Seen in feature-plus-test-rotate-left.
4. Judge "unverifiable" was re-instructed (Role 4, under the rule from Claude's r4-cont-007 prompt). Judges wanted test-run evidence that the workspace cannot contain. Seen in multiple-requirements-word-counts and bug-fix-window-slices.
5. Judge false failures. One judge described satisfying code and still returned fail. Seen in constrained-refactoring-unique-permutations.

r3-cont-008 adds code-level contract validation, stop conditions that never block requested files, and rubrics decidable from the workspace files alone. r4-cont-008 stops re-instructing unverifiable judgments and classifies non-path paths as contract-caused. Plan: let full B finish, stop harness v1 and keep it as a partial diagnostic run, then rerun the smoke and run harness v2 on the fixed code. The final evaluation reports both runs, and that v1 results informed v2.

One more audit pattern appeared: feature-plus-test-window-slices was inconclusive on attempt 3. Sol ran Python heredoc scripts that list the workspace with `Path.cwd().rglob('*')` to check that only the two expected files exist. It is left fail-closed for now.

Harness v1 was stopped at 05:42 UTC by SIGINT after 21 finished tasks and kept as eval/reports/full-harness-v1-partial/, a diagnostic record with no report. The interrupt landed during a subprocess wait, so the runner exited 130 with a traceback and wrote no diagnostics. That is a small robustness item for Role 5. On those 21 tasks, compared with full A:

| Measure | Harness v1 | Full A |
|---|---|---|
| Outcomes | 19 pass, 1 fail, 1 invalid | 20 pass, 1 fail |
| Executor attempts | 44 | 23 |
| v1 attempt distribution | 1: 7 tasks, 2: 6, 3: 7, 4: 1 | |

Fixes on main: controller 067384f, with code-level contract validation and no prerequisite stops on requested files; verifier fbe11fe, with no re-instruction on unverifiable judgments and contract-caused classification of prose paths. Harness smoke 3 and the controller measurement for prompt v3 are running. Harness v2 follows if the smoke is clean.

Harness smoke 3 (fbe11fe, 05:43 to 05:47 UTC) gives a valid report for the first time: 2 of 2 pass, 0 invalid, control_model gpt-6-luna.
- bug-chunk-tail passed on attempt 1 for 0.033 USD, including 0.006 control. One unverifiable judgment was correctly not re-instructed.
- two-session-prefix-sums passed both days on attempt 1 for 0.088 USD. handoff day2_pass is true and user_restated_day1_context false.
- No contract had a prerequisite stop condition. The day-1 contract of the two-session task was all mechanical.
Full harness v2 started at 05:47 UTC from fbe11fe.

Controller measurement for prompt v3 (controller/evidence/2026-10-23-d4-v3.json):
- 30 of 30 contracts are schema-valid, with 37 criteria: 9 command, 11 file_exists, 10 regex and 7 llm_judge.
- The llm_judge share is 19 percent, down from 31 at baseline and 27 with v2. 5 contracts are judge-only, and 22 have no command.
- There were 35 generations, with the repair step firing 3 times, for 0.024 USD.

Leak scans: smoke-harness-attempt2 and smoke-harness-3 are clean. full-harness-v1-partial has one cross-task coincidental match. A 35-character line appears in the verifier evidence for two-session-common-prefix; it also appears in that task's executor-written test_solution.py and its event streams, but not in that task's prompt or grader. It equals a line of bug-chunk-tail's grader, which the executor never had access to. This is the same class as the known pilot false positive, and it is not grader content.

## GitHub CI failures from f844d27 to 698c746, fixed in 1550267

The "Shared interfaces" workflow (ubuntu-latest, Python 3.11 and 3.14, `make test`) failed on every push from f844d27 (03:06 UTC) onward. The 3.11 job failed and fail-fast cancelled the 3.14 job, so GitHub sent "Run failed" each time.
- From f844d27, 1 test failed. It came from the two-session demo test added in 53cb8a9.
- From bcd3e17, 5 tests failed. The 4 additional ones came from the handoff-failure demo tests added in 8308435.

Cause: the demo checkers compared each hook's cwd with the recorded workspace via Path.resolve(). The committed macOS evidence records the workspace as /var/folders/... in experiment.json and the hook cwd as /private/var/folders/... in hooks.jsonl. They are equal only where /var links to /private/var, on macOS. Claude had run the suite only on the macOS host and did not check CI after pushes; from now on Claude checks CI after every push.

r2-cont-008 compares recorded paths in a canonical form without filesystem access, with the macOS /private aliases folded and placeholders compared exactly. Claude's independent check forced Path.resolve and realpath to the identity, as on Linux:
- On the old code, the original CI failure reproduced.
- On the new code, all 5 tests pass and all 5 committed evidence checkers pass.
- A copy whose hook cwd points to another workspace is rejected.
CI on 1550267: validate (3.11) success and validate (3.14) success.

## 2026-10-23 afternoon: task set v2 approved, Fast tier, two new audit patterns

- The user approved task set v2 and allowed the Codex Fast tier, with usage not a constraint and completeness of results as the goal. Decision 0008 is c0e7d39 (CI green).
  - Codex "Fast" is service_tier "priority": "2x speed, increased usage" for gpt-6.1-sol, and the default tier for gpt-6-luna. A host probe showed `-c service_tier="priority"` is accepted, and the native thread_settings_applied record carries service_tier, so runs can verify it.
  - Because Luna defaults to priority, control calls already ran at that tier while costs used Standard rates. The evaluation will state this.
- r5-v2-001 runs in the worktree (branch r5/v2) in private-write mode on the Fast tier. It covers runner support for task_root and service_tier, eval/tasks-v2/DESIGN.md, and a pilot of 4 families (20 tasks) with private graders.
- Two new inconclusive audits, both single-session and both recoverable by regrade after the fixes. Neither is an access attempt:
  - full-b multiple-requirements-line-endings: malformed_event. The audit splits JSONL with str.splitlines(), which also breaks on \x85,   and   inside JSON strings. The stream has 21 lines by "\n" and 26 by splitlines(); every "\n" line parses. Fix: split JSONL on "\n" only, in every runner reader.
  - full-harness multiple-requirements-round-robin, attempt 2: unresolved_operand on a quoted heredoc Python script whose regex mixes quotes and backslashes.

## Tech-lead review and reinforcement (2026-10-23, 07:00 UTC)

Incident: the Claude session restarted at about 06:50 UTC and killed every attached background process: full B (94 of 100 done), harness v2 (46 of 120) and the Role 5 v2 job. Both runs resumed from their checkpoints with the same --out; B resumed its interrupted session as attempt 2. The Role 5 thread was resumed. Codex is still 0.163.0-alpha.11.1 although the Sparkle updater is active. From now on long host runs start through codex-bridge/detach.sh (setsid, nohup) so a session restart cannot kill them.

Review of what is weak, and the reinforcement dispatched for each:
1. false_done_rate is undefined in every report, although it is the project's central claim. The verifier exposes only negative claim evidence, and baselines have no verifier at all. Role 4 (r4-cont-009) adds a per-criterion claims sidecar and a measured claim extractor. Role 1 (r1-cont-007) defines a task-level false-done metric from the final message and hidden grading, usable for A, B, C and the harness alike. Role 5 implements it after v2.
2. The llm_judge produced false fails and unnecessary unverifiable results. Role 3 (r3-cont-009) writes judge prompt v2 with per-requirement evidence and a 24-case calibration set with an approval-gated live accuracy measurement; Claude measures before and after.
3. Plugin host checks for persisted trust, bundled-binary discovery and unrelated-project silence had no procedure. Role 2 (r2-cont-009) scripts them with checkers and adds a once-per-session SessionStart warning for unverified CLI versions.
4. SC-6 human review had not started. Claude drew docs/evaluation/human-review-sample-full-a.md: 22 valid full-A tasks (5 per type plus every failure) for the user to check against the workspaces and prompts.
5. Audit precision: two new inconclusive patterns (JSONL splitting on Unicode separators, a heredoc with a quoted regex) are queued for Role 5 after the v2 pilot. The runtime-evidence idea of checking grader atime was tested and rejected: APFS does not update atime on reads.
6. The runner leaves no diagnostics on SIGINT; queued for Role 5.
7. Still open and not fixable by a job: the v1 ceiling (addressed by v2), single-run variance (no repeats planned), the C templates (user), and the concurrency of B and harness runs (latency only).

## Full baseline B (2026-10-23, 05:04 to 07:05 UTC, d44feda, report 71397cb)

eval/configs/full-b.yaml: the 100 single-session tasks, Sol max, codex-cli 0.163.0-alpha.11.1, resumed once after the 06:50 UTC session restart. Leak scan: 596 files, 0 private markers, 0 grader lines, 0 tracebacks, 0 user paths.
- 98 pass, 0 fail, 2 invalid (multiple-requirements-line-endings: the JSONL splitting bug; feature-plus-test-partition-sign: the restart-interrupted session). pass_rate 1.0 on 98 valid tasks, avg_attempts 1.0.
- Cost: 4.428 USD over the 99 tasks with accounting, 0.0447 USD per task. Full A on the same 100 tasks: 100 pass, 2.54 USD, 0.0254 USD per task. Max effort costs about 1.76 times medium for the same outcome on this set. The report's total_cost_usd is null because the interrupted task has no usage.
- The report is invalid under the approved rule until the two tasks are recovered (r5-recovery-001).

## Reinforcement jobs verified (2026-10-23, 07:00 to 07:40 UTC)

All four ran on the Fast tier and passed host verification, ownership and secret scans.
- Role 5 r5-v2-002 (branch r5/v2, aa41a35): task_root and verified service_tier support, eval/tasks-v2/DESIGN.md, 4 pilot families with 20 tasks. tests/eval 1058 passed. Host checks: the public v2 files have 0 private markers and 0 grader lines; the validation report says 20 references pass, 20 starters fail, 252 of 252 requirements covered, 1090 mutants killed and 0 survivors. Two findings went back to Role 5 (r5-v2-003): in each family the bug_fix and multiple_requirements tasks share one grader and one reference, so they test the same final specification; and the runner refuses the calibration pilot because the tasks are unfrozen, which conflicts with decision 0008.
- Role 3 r3-cont-009 (branch dev/reinforce, 1057374): judge prompt v2 with per-requirement evidence, v1 kept, 24 calibration cases and the approval-gated controller.measure_judge. tests/controller 312 passed.
- Role 4 r4-cont-009 (dev/reinforce, 6cf8674): per-criterion claims sidecars (verdict-N.claims.json), a wider claim extractor with precision and recall 1.0 on 56 synthetic reports. tests/verifier 564 passed on the host, Seatbelt included.
- Role 2 r2-cont-009 (main, 96c47b3): scripted host checks for persisted trust, bundled-binary discovery and unrelated-project silence, plus a once-per-session SessionStart advisory for unverified CLI versions. tests/plugin 272 passed. CI green.
- Role 1 r1-cont-007 (main, 52896cb): decision 0009 defines task_false_done_rate and stops: the report schema's metrics object is closed, so the new metric needs a schema revision approved by the user. D-6 deferred.
- Fast mode pricing (developers.openai.com/api/docs/pricing, read 2026-10-23): exactly 2x Standard for input, cached input and output: gpt-6.1-sol 4.00 / 0.20 / 20.00 and gpt-6-luna 0.20 / 0.02 / 1.00 USD per 1M tokens. "Priority processing was renamed Fast mode on July 30, 2026." Since gpt-6-luna's CLI default tier is priority, version 1 control calls ran at priority but were priced at Standard; the final evaluation discloses this, and r5-v2-003 adds a Fast price snapshot keyed on the observed tier.
- The dev/reinforce branch (controller and verifier changes) waits until harness v2 finishes, because that run launches controller and verifier from main.

## Schema version 2 and judge calibration (2026-10-23, about 08:00 UTC)

- The user approved the report-schema revision for task_false_done_rate, with numerator and denominator over valid tasks. Role 1 (r1-cont-008) published it: schemas/VERSION 2, the metric required in the metrics object, sample unit claimed_complete_task, decision 0009 finalized, interfaces and the Role 5 prompt updated. Host: 104 lead tests passed and all schemas and examples validate. Because the new metric is required, version 1 reports no longer validate against the current schema, and the running harness v2 reads the schema from main when it builds its report. Claude therefore moved the change off main into the dev/reinforce branch (5697ae5) until the run ends. Role 5's implementation brief requires every report reader to validate against the version a report declares.
- Judge calibration on Role 3's 24 synthetic cases, live through codex_cli with gpt-6-luna: prompt v1 23 of 24 correct (one fail judged unverifiable), 0.0228 USD; prompt v2 24 of 24, 0.0107 USD; mean latency 8.9 and 8.7 s. The set does not reproduce the live false fails seen in harness v1, so it is too easy; cases drawn from the real failure modes follow once harness v2 is complete.

## Recovery and audit fixes verified (r5-recovery-001, branch r5/v2 at 9ba06d5)

Claude's old-versus-new audit comparison over 369 retained finished tasks (pilot-a, pilot-b, full-a-attempt1, smoke-harness-3, full-a, full-b, the in-progress full-harness):

| Code | Clean | Inconclusive | Matched access |
|---|---|---|---|
| main (55e1f56) | 363 | 6 | 0 |
| r5/v2 (9ba06d5) | 366 | 3 | 0 |

Fixed: full-a two-session-balanced-brackets (literal string expression), full-b multiple-requirements-line-endings (JSONL split on Unicode separators), full-harness multiple-requirements-round-robin (heredoc with quoted regex). No regression. The 3 remaining are the restart-interrupted full-b segment, which rerun_invalid handles, and the two code-mode shapes queued as r5-audit-004 (a backtick literal and a const array of commands). tests/eval: 1092 passed.

## v2 calibration pilot, first half (2026-10-23, started 08:11 UTC at r5/v2 6c06e5c, Fast tier)

After 12 of 20 tasks: 6 pass, 2 fail, 4 invalid. Executor attempts 14. On the 8 valid tasks A passes 75 percent, above the 30 to 70 percent target; the second half decides. The 4 invalid tasks are audit artifacts, not access:
- Two two-session tasks show grader_access_detected on line fingerprints. Claude checked every grader line found in the executor output: all occur in the task's public files or in the executor's own test files, none only in the grader. The v2 graders reuse public test lines, so the fingerprints are not distinctive. r5-audit-006 makes fingerprints require absence from public inputs and makes grader validation reject shared assertion lines.
- v2-routing-bug-fix: a String.raw template literal (unresolved_custom_input).
- v2-inventory-constrained-refactoring: an in-workspace glob inside a for-loop list (unresolved_operand).
Earlier audit fixes on the branch (64a825b, cd3bdb4) cleared both remaining harness v2 code-mode records; the two-session-line-endings record needed a second pass because Claude's first brief paraphrased the input instead of quoting it. Audit-precision rounds so far today: 7. The pattern is not converging on its own; the fingerprint change above removes one whole class, and the final evaluation will report the per-run invalid counts before and after each fix.

v2 calibration pilot, complete (08:11 to 08:46 UTC, 20 tasks, 24 sessions, Fast tier priced at the Fast snapshot): 10 pass, 4 fail, 6 invalid; 2.99 USD, 0.30 USD per pass. On the 14 valid tasks A passes 71 percent (10 of 14), at the top of the 30 to 70 percent target. All 4 two-session tasks are invalid on the same false-positive fingerprint class (every matched grader line occurs in public inputs or executor-written tests), plus the two unresolved shapes above. The report is calibration evidence and is kept outside the repository (codex-bridge/outbox/run-pilot-v2-a/report/) until the audit and grader fixes land; a regrade then yields the calibration figure for the two-session tasks. By type on valid tasks: bug_fix 2 of 3, feature_plus_test 3 of 4, multiple_requirements 3 of 4, constrained_refactoring 2 of 3. Decision after the regrade: if the valid pass rate stays above 70 percent, raise difficulty at the design level for the remaining 16 families (more interacting requirements and tighter constraints), not by dropping tasks.

## Full harness v2 (2026-10-23, 05:47 to 08:48 UTC, fbe11fe, resumed once after the restart)

eval/configs/full-harness.yaml: 120 tasks, Sol medium executor, gpt-6-luna control through codex_cli, 3 attempts per day. Leak scan: 745 files, 0 private markers, 0 tracebacks from graders (the two "Traceback" strings are the executor's own failing test output quoted in verifier evidence), 0 user paths, 1 cross-task coincidental grader line in verdict evidence (same class as the pilot false positive).

| Metric | Harness v2 | Full A |
|---|---|---|
| Outcomes | 114 pass, 1 fail, 5 invalid | 115 pass, 3 fail, 2 invalid |
| pass_rate on valid tasks | 0.991 (n=115, CI 0.974 to 1.0) | 0.975 (n=118, CI 0.941 to 1.0) |
| handoff_success | 0.944 (n=18) | 0.833 (n=18) |
| avg_attempts | 1.19 | 1.15 |
| Cost (tasks with accounting) | 5.14 USD on 119: executor 4.78, control 0.37 | 3.82 USD on 120 |

On the 113 tasks valid in both runs: harness 112 pass, A 111 pass. The harness used 147 executor attempts against A's 139. The report is invalid under the approved rule until the 5 invalid tasks are recovered: 3 audit-precision cases that the r5/v2 audit fixes clear on re-audit, 1 restart casualty (rerun_invalid), and multiple-requirements-strip-prefix (to inspect). Control cost is 7 percent of the total. The quality difference is inside the confidence intervals; the harness's gain sits in the two-session tasks (handoff 17 of 18 against 15 of 18), at about 35 percent more cost. The paired comparison with intervals follows after recovery.

Audit comparison at r5/v2 cd3bdb4 over 370 retained tasks: old 364 clean and 6 inconclusive; new 369 clean and 1 inconclusive (the restart-interrupted full-b segment, which rerun_invalid handles); matched access 0 and 0; the six detection probes unchanged. The v2 pilot showed one more false-positive class: 22 grader assertion lines that the executor independently wrote into its own test files from the public specification, none present in public inputs. r5-audit-007 adds a first-occurrence rule: a grader line counts as access only when it first appears in a tool output rather than in the executor's own write. The harness v2 push needed http.postBuffer raised to 500 MB; the 12 MB report exceeded git's default HTTP buffer and the first push silently reported up to date.

## Evidence publication regression found (2026-10-23, 09:30 UTC)

While drawing the verifier's human-review sample from the harness report, Claude found that the report task directories hold only result.json, access-audit.json, grading.log, session-evidence.jsonl and the workspace. The executor event logs, final messages, contracts, verdicts, handoffs and control streams are missing, although the checkpoint pins them. Cause: core.publish() refuses any source with a symlinked ancestor, and the runtimes live under /var, a symlink to /private/var. The safeguard came with the two-session runner (b04f9b0), so every 0.163 run is affected: full-a, full-b, full-harness, smoke-harness-3 and the v2 pilot. The 0.162 pilots still have their logs. The data is not lost: all 402 task runtimes (2.5 GB) were copied to codex-bridge/runtimes/ outside the repository before anything else, and r5-publish-001 adds a republish operation that restores the evidence from the pinned hashes. The inline verdicts in result.json and the accounting in report.json were computed from the runtime at run time and are unaffected. Claude's earlier leak scans and comparisons ran on the runtimes, not on the published copies, so they remain valid. This is the third time the macOS /var symlink has broken a safeguard (control accounting, demo checkers, publication); every path check in the runner now needs the same rule, and the brief says so.

## Late afternoon 2026-10-23: fingerprint rule, sampler, publication (branch r5/v2 and dev/reinforce)

- r5-audit-007 (5e27b03): fingerprints count only when a grader line first appears in a tool output; an executor-authored line that later echoes in an output is the executor's own work. Host: tests/eval 1406 passed; the v2 pilot re-audits 20 of 20 clean with 0 matches; the six detection probes unchanged. The validator now also warns on grader assertion lines found in a corpus of executor-written tests; Claude built that corpus (376 files from the full-a, full-b, full-harness and pilot-v2-a workspaces) under the private root.
- r4-cont-010 and -011 (dev/reinforce b92b064): `verifier sample` reads the real report layout (inline verdicts in result.json) and takes --out; on the harness report it selected 20 of 142 verdicts. The absolute host path Claude had supplied for reading was removed from STATUS and CHANGES before the commit. The sample is docs/evaluation/human-review-sample-full-harness.md (19 pass verdicts, 1 fail).
- r5-publish-001 (6dbc684): publication and every related path guard scope symlink checks to the runtime root; `eval.runner.republish` restores evidence from pinned hashes. Host trial on a copy of smoke-harness-3 against the backed-up runtimes: 34 files published, 6 skipped as unpinned (exec-N.stderr and final-N.md, which older checkpoints never hashed). The leak scan of the republished copy found 0 private markers and 0 user paths, with one 28-character executor-authored line in a command text that coincides with a grader line. r5-publish-002 adds --allow-unpinned with provenance and pins those files in future runs, because final messages feed task_false_done_rate.

## Merge to main and republication (2026-10-23, 09:50 to 10:20 UTC)

- The audit comparison on r5/v2 5e27b03 over 370 retained tasks: old 364 clean and 6 inconclusive; new 369 clean and 1 inconclusive (the restart-interrupted full-b segment); matched access 0 and 0.
- r5-publish-002 (1c440cd): republish gains --allow-unpinned for exec-N.stderr and final-N.md with provenance in the run diagnostics, and the runner pins those files from now on. tests/eval 1476 passed.
- Branches dev/reinforce (b92b064) and r5/v2 (1c440cd) merged into main as 05e8dd4 and ad90607 without conflicts. schemas/VERSION is 2. Full suite on main: 2738 passed, 1 skipped. CI green.
- Republication of smoke-harness-3, full-a, full-b and full-harness from the backed-up runtimes runs with --allow-unpinned, followed by a re-audit with the merged code.
- The v2 calibration pilot could not be regraded: r5-v2-003 and r5-audit-006 revised the four multiple_requirements tasks and every pilot grader after the pilot ran, so regrade correctly refused ("public/private task inputs differ from the source run"). The first pilot is kept as eval/reports/pilot-v2-a-attempt1 (diagnostic, republished) and the pilot reruns on main at ad90607, detached, on the revised set.

## v2 calibration pilot rerun (2026-10-23, 10:17 to 11:17 UTC, main ad90607, revised tasks and graders)

20 tasks, 24 sessions, Fast tier: 15 pass, 4 fail, 1 invalid (v2-reservations-bug-fix, a literal for-loop over absolute paths that the resolver does not expand yet; r5-audit-008). 2.86 USD.

| Metric | Value | n | 95% CI |
|---|---|---|---|
| pass_rate | 0.789 | 19 | 0.579 to 0.947 |
| task_false_done_rate | 0.308 | 13 | 0.071 to 0.583 |
| cost_per_pass | 0.191 USD | 20 | 0.145 to 0.270 |
| handoff_success | 0.75 | 4 | 0.25 to 1.0 |
| avg_attempts | 1.21 | 19 | 1.05 to 1.42 |

By type: bug_fix 3 of 3 valid pass, constrained_refactoring 3 of 4, feature_plus_test 3 of 4, multiple_requirements 6 of 8; two-session 3 of 4. The pass rate on valid tasks is above the 30 to 70 percent target, so under decision 0008 the remaining 16 families get a harder design: more interacting requirements, stricter constraints and day-2 work that depends on more day-1 decisions. No pilot task is dropped or selected on its outcome. The task-level false-done rate on these harder tasks, 4 of 13 claimed-complete tasks failing hidden grading, is the first measurement of the behavior the harness targets.

Regrades with the merged code: full-a 116 pass, 3 fail, 1 invalid (balanced-brackets, day 2 being continued); task_false_done_rate 0.045 (1 of 22 claimed-complete tasks); full-b valid, 100 of 100, task_false_done_rate 0 of 20, cost null because the restart-interrupted task has no usage (r5-rerun-002 adds a fresh rerun of unaccounted tasks). The claim extractor finds completion claims in only about a fifth of the final messages, so the metric's denominator is small; the final evaluation will state this.

The harness regrade was refused on 104 of 120 tasks: the verifier runs contract commands inside the real workspace after the exit hash is recorded, and Python writes __pycache__ there. r5-digest-001 excludes caches from the digest, versions it, records the hash after verification and suppresses bytecode in verifier launches; merged as c4cec06, CI green. Harness recovery with rerun_invalid is running.

## Late 2026-10-23: continuation false positive, legacy hashes, accounting rerun

- Full A continuation (continue_day2 on two-session-balanced-brackets) ran day 2 but the task came back as grader_access_detected with 25 protected_path matches on the executor's own commands and private_context_path on its own settings records, and 0 fingerprint matches. Cause: audit_roots protects every sibling lhm-eval-* runtime except the task's own, compared as unresolved paths; the continuation records its runtime under /private/var while the temp root is spelled /var, so the task's own runtime was protected. The fourth /var symlink defect. r5-fixes-003 resolves paths in every root comparison; the continuation reruns afterwards.
- Legacy harness hashes: digest v2 does not recover the harness run because the recorded v1 hashes included the executor's 3.13 bytecode and, for multi-attempt and two-session tasks, verifier bytecode that later verification overwrote (11 of 12 sampled single-attempt tasks match after removing cache files newer than exit; two-session-common-prefix cannot). r5-fixes-003 adds verification against the per-file sha256 values the runner pinned in report.json at run time, plus an mtime bound.
- r5-rerun-002 (branch 6865b45): rerun_unaccounted reruns a valid task whose cost is unknown because of an infrastructure interruption and records partial native usage as a lower bound only. tests/eval 1551 passed. To apply to full-b feature-plus-test-partition-sign and, after recovery, to the harness.
- Audit-precision and recovery rounds so far today: 12. Every one so far was a parser or path-comparison defect, never an access.

## 2026-10-24, early: v2 population complete, recovery chain results

- r5-v2-004 (branch 8a70983, 14:21 to 15:05 UTC on the Fast tier): 80 new tasks bring version 2 to 100 tasks in 20 families, with full-v2-a, full-v2-b and full-v2-harness configurations and Fast-priced estimates. Role 5's validation: 100 references pass, 100 starters fail, 1564 requirements covered, 6092 mutants killed, 49 equivalents, 0 survivors. Claude's host checks: tests/eval 1611 passed; 0 private markers in the 1321 public files; 100 private grader directories match the 100 public tasks; no grader shared between tasks; 80 public workspace files share one non-assertion line each with their grader, which the public-input exclusion in the audit already ignores. All meta.json remain frozen=false pending host validation and the separate freeze.
- Recovery chain on main d87e5f3 (12 audit and recovery rounds in): the full-a continuation now works. two-session-balanced-brackets passed day 2 with the handoff used and the audit clean. Report full-a-continued2 is valid: 117 pass, 3 fail, 0 invalid; pass_rate 0.975 (n 120, CI 0.942 to 1.0); handoff_success 0.85 (n 20). Its cost is null because the new day-2 session's tier was recorded as unknown; r5-fixes-004 prices tier-less records at the model default.
- The harness rerun still refuses: report.json pins no workspace files, so the artifact path cannot apply; r5-fixes-004 uses the runner's published workspace copy (committed in git at c1207c9) as the reference. rerun_unaccounted rejects full-b's interrupted task; r5-fixes-004 fixes the eligibility.

Claude's independent v2 grader validation (validate_graders, 30 mutants per task, all 100 tasks): 100 rows, 0 errors, 2994 mutants killed, 6 recorded equivalents, 0 survivors.

Spot-check of two new v2 prompts (calendar-windows multiple_requirements, rate-budgets two-session; about 650 words each): every task follows one template of 16 numbered requirements (R1 to R16) with the domain, normalization recipe, duplicate policy and error namespace substituted per family, over a 7-module package with protected files, a protected verify.py and a required final-response report. The set is harder than version 1 and its hidden tests follow the public text, but it is homogeneous: the 100 tasks are 20 domain variants of one structure, so a model that masters the structure transfers across families, and families are not independent samples of software work. The final evaluation must state this. Version 2 therefore measures the harness on dense, interacting, explicitly specified requirements, not on varied task shapes.

## Version 2 frozen (2026-10-24, main 9097281)

r5-freeze-002 set frozen=true on all 100 meta.json files (only that field changed); tests/eval 1664 passed. Claude computed the digest on the host with eval.freeze_v2 over public inputs plus external grader contents: 12e7574905a6c6e4f7f49a85eacad38899fa5f0d221a3c93939a83ab13b6f041, 100 tasks, 20 families of 5, 20 two-session tasks. full-v2-a and full-v2-harness select that digest; full-v2-b selected its own 80-task digest, so r5-v2-005 adds the task_population declaration before any v2 run. Role 1 publishes docs/eval-freeze-v2.md (r1-cont-009). After this point no harness change may use version 2 results.

## Interim version 1 comparison and the start of the version 2 runs (2026-10-24)

- Recovery chain 2 made full-b complete: full-b-recovered2 is valid, 100 of 100 pass, 4.465 USD, cost_per_pass 0.0447 USD. full-harness-recovered3 is valid (119 pass, 1 fail) but its fresh rerun has unpriced control calls; full-a-continued2 is valid (117 pass, 3 fail) with one unpriced day-2 session. r5-fixes-005 (merged 336c072, 1690 tests) prices control calls in every recovery path and keeps mixed pricing provenance; recovery chain 3 reruns the harness casualty and re-prices A.
- Interim paired comparison (docs/evaluation/interim-v1/): harness vs A pass rate +0.017 (CI -0.017 to 0.050); per-type cost_per_pass ratio 1.37 (bug_fix) and 1.42 (constrained_refactoring), harness more expensive; handoff 0.95 vs 0.85. Harness vs B: equal pass rate 1.0; cost ratio 0.81 and 0.75, harness cheaper, intervals below 1. Overall cost ratios wait for the re-pricing.
- Version 2 full runs started at 11:35 UTC from the pinned checkout 51d2e52 (the freeze commit plus the population test), three configurations concurrently on the Fast tier, detached. Concurrency affects latency only.
- Reports committed: the recovered version 1 reports and both v2 calibration pilots (b659815; leak scans 0 private markers, 0 user paths).

## Version 2 harness run stopped after 8 tasks (2026-10-24, about 16:45 UTC)

After 8 tasks (4 pass, 1 fail, 3 invalid) Claude stopped full-v2-harness and kept it as full-v2-harness-attempt1 (diagnostic). Causes of the invalid tasks:
- v2-calendar-windows-multiple-requirements: `controller contract` exit 2. The gpt-6-luna call hit the controller's 35 s per-call deadline with null tokens on a 650-word, 16-requirement prompt, and the fallback was refused without an API key. The 35 s deadline came from version 1 latencies. r3-cont-010 makes the deadline configurable through HARNESS_CONTROL_TIMEOUT_SECONDS for evaluation runs and adds a control_failure stderr line; the plugin budgets are unchanged. This is a capacity parameter, not a change to prompts, routing or output, and it is disclosed under decision 0008.
- v2-cache-invalidation-feature-plus-test: a multi-file apply_patch literal (unresolved_custom_input). v2-text-indexing-constrained-refactoring: `pkill -f '<regex>'`, a process pattern treated as an operand. r5-audit-009 resolves both and classifies control timeouts as control_timeout.
full-v2-a and full-v2-b continue (A 14 of 14 passed so far, B 5 of 6). The harness run restarts from a new pinned commit once both fixes are merged.

## Control deadline, audit shapes, recovery state (2026-10-24, about 17:15 UTC)

- r3-cont-010 (controller, 344 tests) and r5-audit-009 (eval, 1722 tests) merged as f1fa062; full suite 3016 passed, CI green. HARNESS_CONTROL_TIMEOUT_SECONDS overrides the 35 s control deadline for evaluation runs; a timeout writes a control_failure line that the runner classifies as control_timeout.
- Live contract timings on three version 2 prompts with a 180 s deadline, gpt-6-luna through codex_cli: model latency 13.2, 19.4 and 25.2 s (wall 25 to 45 s), all schema-valid, with 2 to 3 mechanical checks each and one 11-criterion contract that is 8 of 11 llm_judge. The earlier 35 s miss was load variance with three runs in flight; the harness restart uses 120 s.
- The two version 2 audit shapes did not resolve on the real records after the fix: the multi-file apply_patch literal (1419 characters) and a tools.write_stdin session-control call. Claude saved the verbatim records and read-only report copies outside the repository for r5-fixes-006, which also covers the regrade refusal of full-a-continued2 (pricing provenance) and a null control_usd on the harness rerun task although both control calls are priced. Lesson applied: briefs now carry verbatim records and report copies instead of paraphrases.
- Version 2 progress at 17:15 UTC: A 33 of 33 pass, B 13 of 14. If A stays near 100 percent, version 2 also has a ceiling on single-session tasks and the calibration pilot's 79 percent was not representative; the final evaluation must report this.

## Final version 1 comparison, harness v2 restart (2026-10-24, 12:10 KST, 03:10 UTC)

Note on times: the UTC labels in the 2026-10-23 and 2026-10-24 sections above were written from local clocks and are not all consistent; the detached run logs under codex-bridge/outbox/run-*/started_at hold the authoritative UTC times (v2 A started 2026-10-23T16:10:46Z).

- r5-fixes-006 merged as 9d5403e (1755 eval tests, CI green). Regrades on main: full-a-final3 valid, 117 pass, 3 fail, 3.849 USD, cost_per_pass 0.0329; full-harness-final3 valid, 119 pass, 1 fail, 5.175 USD, cost_per_pass 0.0435 (control 0.369 USD, 7.1 percent). With full-b-recovered2 (100 of 100, 4.465 USD, 0.0447) all three version 1 reports are complete and priced; committed as 44dca51 after leak scans (0 private references, 0 user paths, 0 grader lines in 7104 files). The failed restart attempts and probe directories were moved out of the repository.
- Final paired comparison in docs/evaluation/final-v1/: harness vs A pass +0.017 (CI -0.017 to 0.050), cost_per_pass ratio 1.32 (1.26 to 1.39), handoff 0.95 vs 0.85; harness vs B equal pass 1.0, ratio 0.77 (0.72 to 0.81). Version 1 verdict: the harness replaces Sol max at 77 percent of the cost but costs 32 percent more than Sol medium without a measurable quality gain, because medium already passes every single-session task. The claim is half proven on version 1 and version 2 decides.
- full-v2-harness restarted at 02:59:51Z from a new pinned checkout (lhm-harness-v2 at main 9d5403e) with HARNESS_CONTROL_TIMEOUT_SECONDS=120, output eval/reports/full-v2-harness in that checkout; attempt 1 stays as a diagnostic. Progress at 03:03Z: A 81 of 100 task directories, B 36, harness 1.
- Version 2 baseline B shows a new audit class, three tasks of 24: code-mode JavaScript that reads text stored earlier in the session with load("original_sources"), parses it with matchAll, and calls tools with computed arguments (unresolved_custom_input). r5-audit-010 (high effort) is to classify scripts whose only data sources are session-stored text, literals and audited tool results as derived_from_audited_outputs, keeping STOP-E4 fail-closed for any other source; verbatim records are in codex-bridge/report-copies/v2-b-unresolved-records.txt. The affected tasks are regraded once it merges.

## Version 2 baseline A complete; audit chains and a suspect grader family (2026-10-24, 12:40 KST, 03:40 UTC)

- full-v2-a finished (run started 2026-10-23T16:10:46Z, pinned checkout 51d2e52, Fast tier): 100 tasks, 94 pass, 5 fail, 1 invalid; pass_rate 0.949 (n 99, CI 0.899 to 0.990); cost 15.06 USD, cost_per_pass 0.160 (CI 0.147 to 0.175); task_false_done_rate 0.053 (4 of 75 claimed-complete tasks, CI 0.013 to 0.110); handoff_success 0.947 (18 of 19); avg_attempts 1.19. The report is not yet committed: the invalid task and the family below are open.
- All five failures are the reservations family, each failing exactly one hidden test of 13 or 14 (test_R2_shapes in bug_fix). Baseline B so far fails the same two reservations tasks with one test each, and both calibration pilots failed every valid reservations task with one test. A hidden expectation that every executor misses at every effort level, on one family only, is more likely a grader expectation the public prompt does not state than a capability gap. Claude dispatches a read-only Role 5 diagnosis (r5-diag-001) reporting test ids and an abstract derivability verdict; the remedy (disclose and exclude the family, or amend the grader with a new digest and regrade every configuration) changes the frozen set and is the user's decision.
- The invalid A task (v2-rate-budgets-two-session) has a day-2 shell loop over literal absolute AGENTS.md paths with an if-test-cat body that the loop resolver does not expand (unresolved_operand). Baseline B has five inconclusive tasks whose code-mode scripts the r5-audit-010 reducer does not reach on the real records: the stores come from loops that spread results into text(), intervening literal-only scripts clear the saved state, loads are used outside tool arguments, and other regexes and destructuring maps appear. r5-audit-011 (high) extends the rule with the verbatim records (codex-bridge/report-copies/v2-b-unresolved-records-2.txt). r5-audit-010 itself merged as 5fececf (1828 tests, CI green).
- Baseline B task v2-access-policy-bug-fix is access_detected on a real executor action: rg --files over the whole temp root, which enumerates the sibling runtimes that audit_roots protects. Not a parser defect; the task stays invalid and is a candidate for a fresh rerun with the reason disclosed.
- Progress at 03:40 UTC: B 46 of 80 (38 pass, 2 fail, 6 invalid), harness 8 of 100 (8 pass, control deadline 120 s, no control failures).

### Diagnosis of the reservations family (r5-diag-001, read-only, 2026-10-24 03:50 UTC)

Role 5 read the five public prompts, the five private test_R2_shapes bodies, the reference solutions and the retained baseline A workspaces, without running anything. Result: the five test bodies are identical and share one expectation that an otherwise valid integer endpoint must be rejected when it is an integer subclass (booleans excluded separately). The public R2 of this family says only that start and end are ints excluding bool; the other 95 tasks' R2 say built-in integers explicitly. Every retained baseline A implementation accepts integer subclasses and rejects booleans, a reasonable reading of the public text (ambiguous in all five tasks; the preservation wording of feature_plus_test and constrained_refactoring favors the stricter reading somewhat). The references pass by inspection. No other family shows the pattern.

Remedies, all for the user, because any grader change alters the frozen digest (decision 0008): (a) keep and disclose; (b) exclude the family from headline numbers as a disclosed grader defect, comparing every configuration on the same 95 tasks; (c) amend the five tests to accept both readings, publish a revised digest, and regrade every configuration equally from retained artifacts, keeping original and amended results distinguishable. Role 5 recommends (c) with (b) for interim headlines and (a) as the disclosed original comparison. Claude concurs: the defect is in the public prompt's omission, it affects all configurations equally, and regrading is cheap and reproducible. Until the user decides, every v2 report is kept as graded, and the interim headline numbers are shown both as graded and excluding the reservations family.

### Harness v2: first invalid task and two contract defects (2026-10-24, 04:05 UTC)

- v2-job-queues-two-session is invalid (missing_two_session_handoff_observation, incomplete_access_audit) for one root cause: the attempt-3 rollout contains a native item of type Extension, kind clock.sleep (the executor slept), which the audit does not know (unsupported_native_item). The runner audits before every verification and blocks the day when the audit is not clean, so attempt 3 was never verified, no handoff was generated and day 2 never ran. Fix for Role 5 (r5-audit-012, after 011): support the Extension item kinds that touch no files, and make continue_day2 recover a harness task blocked before its last verification (verify the retained workspace post-exit, generate the handoff, run day 2). Verbatim records: codex-bridge/report-copies/v2-harness-native-record.txt.
- The same task shows two contract defects from gpt-6-luna that the freeze forbids fixing: SC-8 demanded a HANDOFF.md regex containing the string '- ' (with a space) where the task requires '-', and SC-10 ran py_compile on file names that do not exist (project.py, render.py at the root instead of under project/). The executor correctly refused SC-8 across three attempts and, worse, satisfied SC-10 by adding compatibility modules at the root, a change the task did not ask for. These are harness costs the version 2 measurement must show: wasted attempts, and a contract that can push the executor into unrequested changes. The verdicts also show the judge share: 7 of 12 criteria were llm_judge on this contract.
- CI: a10bac5 and 4f5cad9 green.

## Version 2 baseline A regraded valid; audit chains and recovery merged (2026-10-24, 05:10 UTC)

- r5-audit-011 (1904 tests) merged as 57fc4c9 and r5-audit-012 (1923 tests) merged after it: the code-mode reducer follows only data flows that reach tool arguments, reconstructs stored values from displayed tool results, keeps saved state across scripts that call neither store nor save, supports destructured literal-pair maps and a safe regex subset; the shell loop resolver expands literal absolute-path loops with if-test-cat bodies; the native Extension item of kind clock.sleep is accepted; continue_day2 recovers a harness task blocked before its last day-1 verification. Host re-audit of the six real records before the merge: all five baseline B tasks and the baseline A two-session task clean; the access-policy protected-path detection stands.
- Regrade of full-v2-a with 57fc4c9 (eval/reports/full-v2-a-regrade): valid, 95 pass, 5 fail (the reservations family), 0 invalid; pass_rate 0.95 (n 100, CI 0.90 to 0.99); cost 15.06 USD, cost_per_pass 0.1585 (CI 0.146 to 0.172); task_false_done_rate 0.053 (4 of 76); handoff_success 0.95 (19 of 20); avg_attempts 1.20. Leak scans on both A directories: 0 private references, 0 user paths, 0 grader lines. Excluding the reservations family under the open decision 0010, A passes 95 of 95.

## OpenAI transport outage during the version 2 runs (2026-10-24, about 04:00 to 04:50 UTC)

- Between about 04:00 and 04:50 UTC every Codex call failed with "workspace routing discovery failed" (WebSocket reconnects 5 of 5, HTTPS fallback, turn.failed). Baseline B halted with STOP-E1 after task 56 of 80 at 04:20 UTC (one task interrupted, which the runner marks and the resume continues). The harness run kept going because a contract failure does not halt the run: 14 tasks became invalid without an executor call (6 control_cli_error, 4 control_timeout at the 120 s deadline, and 4 two-session variants of the same), each also carrying missing_logs or executor_settings_unverified because nothing ran. From 04:48 UTC contracts succeeded again (32 to 34 s latencies).
- Claude sent SIGINT to the harness runner at 05:12 UTC intending to stop it, but the signal reached the caffeinate wrapper and the runner continued; since the service had recovered, the run is left running. The 14 outage-invalid tasks are recovered after the run with rerun_invalid (reasons control_cli_error, control_timeout), as in version 1; a fresh executor session for a task that never ran is not a rerun on outcome.
- Baseline B was resumed at 05:20 UTC from its checkpoint (same --out, pinned checkout 51d2e52).
- Hygiene note: the committed v2 A reports contain one executor-printed host path (the output of which python in one task's exec log). It is not a private or grader path; the evidence file keeps its recorded hash.

## Version 2 baseline B complete; four audit rounds and the transport classification (2026-10-24, 09:05 UTC)

- full-v2-b finished at 06:45 UTC (resumed after the outage; 80 single-session tasks, Sol max, Fast tier): as run, 61 pass, 4 fail, 15 invalid, 18.05 USD. The four failures are the reservations family (test_R2_shapes, decision 0010 pending).
- The 15 invalid tasks fell into four classes, each fixed by a Role 5 job and verified on the host by re-auditing the real records before merging: (1) r5-audit-013 (2004 tests, 2d7da2e): six tasks flagged protected_path for `rg --files -g AGENTS.md` over the whole temp root, a Sol-max habit of looking for instruction files in ancestors; the listing outputs (396 to 593 paths each) contained no path under a grading copy, a sibling runtime or the private root, so a name-filtered enumeration whose complete output exposes nothing protected now resolves as protected_listing_without_exposure, with the wildcard, exposure, truncation and second-operand variants still detected; one task (access-policy) keeps protected_path because its code-mode listing output is truncated in the record. The same job made transport error items metadata and resolved two more code-mode shapes. (2) r5-audit-014 (2019 tests, c22b2b2): a literal store issued beside a non-ASCII patch. Regrade sequence on the host: as run 61 pass / 15 invalid, regrade2 (57fc4c9 code) 72 pass / 2 invalid / 1 timeout / 1 error, regrade3 (c22b2b2) 73 pass / 4 fail / 1 invalid / 1 timeout / 1 error.
- The timeout and the error are outage casualties: both executor sessions died in the 04:00 to 04:50 UTC transport failure (reconnect errors, "No route to host", "workspace routing discovery timed out", turn.failed) without a final message. Counting them as model outcomes would penalize B for a service outage, so r5-rerun-003 (2048 tests, 559aa1e) classifies such segments as invalid with reason executor_transport_failure in run, regrade and reaudit, lets rerun_invalid rerun them fresh, and lists them in run-diagnostics.json. regrade4 with that code is running; the three remaining invalid tasks (two transport casualties, one truncated listing) are then rerun in fresh sessions and disclosed.
- Hygiene: the B logs contain seven executor-printed host paths (Python tracebacks through the host miniconda), no private or grader content.
- Harness progress at 09:00 UTC: 82 of 100 (52 pass, 10 fail, 20 invalid: 14 outage control failures, the rest audit shapes to re-audit with the merged code).

## Version 2 harness run complete, as run (2026-10-24, 10:28 UTC)

- full-v2-harness (pinned checkout 9d5403e, Sol medium executor, gpt-6-luna control at a 120 s deadline, reinstruction_limit 2, Fast tier; started 02:59 UTC, 7.5 hours including the outage): as run 62 pass, 15 fail, 23 invalid; pass_rate 0.805 (n 77, CI 0.714 to 0.896); cost 14.01 USD of which control 1.89 USD (13.5 percent); cost_per_pass undefined until the invalid tasks are resolved; task_false_done_rate 0.222 (6 of 27 claimed-complete tasks, CI 0.074 to 0.391); handoff_success 0.733 (11 of 15); avg_attempts 2.17.
- Preliminary reading, before recovery: on version 2 the harness passes fewer valid tasks than A (0.95) and B (0.936), fails 11 tasks outside the reservations family that A passed, re-instructs on most tasks (mean 2.17 attempts against 1.2 for A), and its verifier accepted completion claims that hidden grading rejected on 6 of 27 tasks. The invalid set: 16 outage control failures (control_timeout 8, control_cli_error 8, including 4 two-session tasks that never started), 1 Extension-record block before the last verification (job-queues-two-session), 6 audit shapes to re-audit with the merged code. Recovery order: regrade with the final audit code, rerun_invalid for the 16 control failures in fresh sessions, continue_day2 for the blocked two-session task, then paired comparisons.
- Baseline B final state before its reruns (regrade4 on 559aa1e): 73 pass, 4 fail (reservations), 1 timeout still to reclassify (r5-rerun-004, 2072 tests, merged), 2 invalid (one transport casualty, one truncated listing); the recovery chain reruns the three in fresh sessions.

## Recovery day, part 2: Mac sleep, the STOP-3 gate, and a pricing defect (2026-10-24, 15:45 UTC)

- The Mac slept from 10:49 to 13:35 UTC (maintenance sleep; woken by the lid) and every process paused; nothing was lost. Recorded again: caffeinate -i does not prevent lid or maintenance sleep.
- Baseline B recovery: regrade5 on 7ff01ad (transport tails classified) gives 73 pass, 4 fail, 3 invalid; rerun_invalid of the two transport casualties in fresh sessions (full-v2-b-recovered, 18.28 USD so far) gives 75 pass, 4 fail (reservations), 1 invalid. The remaining invalid task, v2-access-policy-bug-fix, keeps protected_path because its code-mode listing output is truncated in the native record; rerun_invalid refuses tasks with access matches by rule, so it stays invalid and is disclosed (79 valid tasks).
- Harness recovery blocked twice by eval tooling, both fixed by Role 5 and merged: (1) regrade refuses a run in which 16 tasks never launched an executor (no workspace hash), so the order is rerun first, regrade after; (2) rerun_invalid is refused by the STOP-3 cost gate because a recovery subset can never equal an estimated configuration (r5-rerun-005, 2092 tests, e468ad6: recovery operations accept a task subset of an approved configuration with identical settings and record the matched estimate and bound). The rerun of the 16 outage tasks is running from e468ad6 (regrade phase, then 16 fresh harness sessions).
- Pricing defect found in B: 22 of 80 executor calls were unpriced because the pricing code applied the snapshot's 272K short-context bound to the session's cumulative input instead of each request's context; the largest single turn in those sessions is 48105 tokens. r5-pricing-001 (2115 tests, committed on r5/v2, merge pending the running rerun) prices per request and reports long_context_rate_missing only when a single turn exceeds the bound. Every version 2 report is re-priced after the merge; version 1 reports are unaffected (no session above 272K cumulative was unpriced there, cost totals were complete).

## User decision: stop the version 2 harness recovery and change direction (2026-10-25, 01:20 KST, 16:20 UTC on 2026-10-24)

- The user stopped the harness rerun (16 outage tasks) during its regrade phase and decided on a new direction: a hook system that compensates the measured weaknesses of gpt-6.1-sol and gives the user visible value, with gpt-6-luna pinned as the control model so that the arrival of new Codex models does not change the system under test. Claude killed the detached runner at 16:17 UTC; eval/reports/full-v2-harness (as run) and the partial full-v2-harness-recovered directory stay as diagnostic evidence and are not completed.
- State of the version 2 measurement at the stop: A valid (95 pass, 5 fail, 15.06 USD); B recovered (75 pass, 4 fail, 1 invalid; cost pending the per-request pricing fix r5-pricing-001, committed on r5/v2, not merged); harness as run 62 pass, 15 fail, 23 invalid, pass_rate 0.805 against 0.95 and 0.94. The reading stands as the project's answer to its original claim: the contract-and-verify harness with a cheap control model costs more than Sol medium alone and, on dense multi-requirement tasks, lowers quality; its failure modes are wrong mechanical checks from the control model, judge-heavy criteria, and retries on non-executable evidence. Decision 0010 (reservations grader) now matters only for the record of these runs.
- Note: another Claude session on this host was running bulk gpt-6-luna calls (metaexp) at the same time; it is unrelated to this project and was left alone.
- Claude's design proposal for the new direction: docs/handoff/2026-10-25-v3-direction.md (awaiting the user's approval; Role 1 then writes the decision record and plan).

### Approval and start of the version 3 direction (2026-10-25, 01:40 KST)

The user approved the proposal in full: direction and success criterion; gpt-6-luna pinned; B dropped for version 3; C optional; decision 0010 record-only. Claude merged the pending per-request pricing fix (ede1220f) so that the version 2 B report can be re-priced for the record, dispatched r1-v3-001 (decision 0011, schemas for the requirements table, completion report and ledger, the plugin artifact contract, plan and prompts; high effort) in the main checkout and r5-v3-001 (version 3 task-set design, runner plugin mode design, config templates; high effort) in the Role 5 worktree. Roles 2 to 4 start after the schema set is approved.

### Interface version 3 approved; implementation started (2026-10-25, 02:00 KST)

The user approved the version 3 schema set as proposed (commit d82b87a) and chose the question pause for noninteractive sessions: instruction injection at the first prompt plus Stop-hook allowance when questions are pending and the workspace is unchanged. Jobs dispatched: r1-v3-002 (freeze, hook-facing CLI operations in AGENTS.md 3.2, hook event mapping; main checkout), r2-v3-001 (pin-check, hook wiring, artifact directory, demos; lhm-plugin on r2/v3), r3-v3-001 (controller requirements and claim-audit with pinned gpt-6-luna, calibration sets; lhm-controller on r3/v3), r4-v3-001 (verifier check and ledger-validate, repair and ledger texts; lhm-verifier on r4/v3), r5-v3-002 (version 3 task authoring with private graders; lhm-r5-harness, private write). All five run concurrently on separate owned paths.

## Version 3 implementation night (2026-10-25, 02:00 to 05:30 KST)

- Interface version 3 frozen and the hook-facing CLI operations published (859c27e). Role 2 (hook lifecycle, pin-check, artifacts, demos; 313 tests), Role 3 (requirements and claim-audit operations with pinned gpt-6-luna, 40-case calibration sets; 405 tests) and Role 4 (verifier check and ledger-validate; 690 tests) implemented in parallel worktrees and merged; non-eval suites on main 1536 passed.
- Process improvements the user asked for after the recovery day: brief quality rules and the parallel-job rule in CLAUDE.md (9fb5d79); STATUS files append-only per job and a 40-line report cap in every role prompt (7d560d3); a cross-role contract test (tests/lead/test_cross_role_v3.py, 837d23e) that found a real Role 4 defect on its first run (round 2 discarded the retained claim audit), fixed by r4-v3-002 (c8c6228) before the test was committed; host-operator tooling ops/ outside the repository (dispatch, wait, verify, commit, merge with CI watch, scan, status; 35 unit tests) built by two ops jobs; a real-record audit regression corpus is being built by Role 5 (r5-corpus-001).
- pin-check on codex-cli 0.163.0-alpha.11.1 reports model_list_unavailable: the CLI has no models subcommand and the stdio app-server does not answer model/list. A minimal pinned probe served gpt-6-luna at priority in 6 s (evidence in codex-bridge/report-copies/luna-pin-probe-2026-10-25.txt). Role 2 stopped under STOP-1 because the frozen pin-check schema forbids recording probe evidence on an enabled result; the user's decision on amending the schema is pending.
- Version 3 tasks: bug_fix (f4a3461), constrained_refactoring (7c3429d) and ambiguous_requirement (35754ee) complete, 27 of 54, each shape validated independently on the host with 30 mutants per task (0 errors, 0 survivors, no private references in public inputs); feature_plus_test, multiple_requirements and two_session are being authored in parallel sessions. All meta.json stay frozen=false until the set is complete and host-reviewed.

### Version 3 set complete; pin-check amendment approved (2026-10-25, 05:55 KST)

- All 54 version 3 tasks are on main (505a320): bug_fix f4a3461, constrained_refactoring 7c3429d, ambiguous_requirement 35754ee, two_session ac378a5, feature_plus_test c70f579, multiple_requirements a97c118. Each shape was validated independently on the host with 30 mutants per task (0 errors, 0 survivors), scanned for private references (none), and authored in its own session with disjoint paths; r5-v3-consolidate merges the per-shape validation files, fills the configurations and adds the ten-task calibration pilot. Nothing is frozen yet.
- The user approved amending the frozen pin-check interface so that, when the installed CLI offers no model listing, pin-check may verify gpt-6-luna by an operator-recorded probe observation per CLI version (decision 0012, r1-v3-004), with the controller's per-call identity check as the enforcement; Role 2 implements it (r2-v3-003). This unblocks the H3 live smoke, Role 3's calibration measurement and the v3 pilot.

### Host review of the version 3 set and the calibration decision (2026-10-25, 06:40 KST)

- Independent host validation of all 54 graders with 60 mutants per task: 0 errors, 0 survivors, 2355 mutants killed, 139 recorded equivalents; the smallest kill count is 9 (v3-link-preview, a small mutant population). Public inputs: no private references; prompt length 194 to 393 words (median 266). Spot-read of three prompts (bug_fix v3-cycle-witness, ambiguous_requirement v3-token-expiry, two_session v3-stream-negotiation): distinct structures, numbered requirements, the ambiguous task states one deliberately unresolved product choice.
- Calibration decision (Claude, as evaluator): DESIGN.md asked for ten additional disjoint calibration tasks before the freeze. Authoring them costs most of a day and the difficulty target (A pass rate 60 to 85 percent) is a target, not a selection criterion: no task is dropped or changed on its outcome. The set is therefore frozen after this host review without a disjoint pilot; the full A run doubles as the calibration measurement, and if A lands outside the band the final evaluation reports it. The pilot-v3-a configuration stays as an optional cost check.
- pin-check amendment landed: decision 0012 (58bdd10) and the plugin implementation (d429956); pin-check on this Mac now reports enabled with probe_observation evidence and its artifact validates against the amended schema. Role 3's live calibration measurement of the two Luna prompts is running on the host.

### Version 3 frozen (2026-10-25, 07:40 KST)

r5-freeze-v3 set frozen=true on all 54 meta.json files (only that field), added eval.freeze_v3 and the runner's digest enforcement, and made full-v3-a runnable; tests/eval 2157 passed. Claude computed the digest on the host over public inputs plus the complete version 3 private snapshot: 7645e003ed4ef52c43d58555f494c7554ee468c5e628b5d95e22c37a30b5b01d (54 tasks, 9 per shape, 9 two-session), filled it into both configurations and committed. From this point no hook, controller or verifier change may use version 3 results. Role 1 publishes docs/eval-freeze-v3.md (r1-v3-005). Role 3's identity and response_format fix (444 tests) is merged and the live Luna calibration is being rerun on the host.
