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
