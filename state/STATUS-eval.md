## Done

- Completed combined r5-full-001/r5-full-002 two-session orchestration: fresh day-2 session, exact day2.md, runner-owned handoff/contract delivery, per-day audits/settings/exit hashes, one final grade, handoff observations and summed costs (.venv/bin/python -m pytest tests/eval -q: 537 passed in 46.12s).
- Hardened control evidence publishing and inputs: manifest-only files, no workspace/symlink adoption, specific runner_control_file_preexisting reason and numeric pinned verdict selection; forged verdict-99.json/verdict-final.json cannot replace verdict-1.json (.venv/bin/python -m pytest tests/eval -q: 537 passed).
- Preserved active-session crash recovery, audit-clean day-1 timeout/error continuation and regrade timeout/error/invalid-task behavior (.venv/bin/python -m pytest tests/eval -q: 537 passed).
- Applied decision 0006: native missing/mismatched cli_version invalidates only its task, retains costs and permits report.json; pre-session installed-version changes still halt; comparison helper rejects mixed versions (.venv/bin/python -m pytest tests/eval -q: 537 passed).
- Fixed STOP-3 test's stale timeout override without changing loader validation; the guard budgets 11 calls for one two-session harness task including controller retries/fallbacks (.venv/bin/python -m pytest tests/eval -q: 537 passed).
- Prepared full-a/full-b and smoke-two-session-a on codex-cli 0.163.0-alpha.11.1, 120 frozen tasks/140 sessions per full configuration, shared seed/pilot limits and published USD 4.10/6.03 estimate; updated combined README/CHANGES (.venv/bin/python -m pytest tests/eval -q: 537 passed, including configuration inventory checks).
- Preserved frozen public tasks and retained pilots; checked whitespace for all owned changes (git diff --check -- eval tests/eval state/STATUS-eval.md: exit 0; git diff --exit-code -- eval/tasks eval/reports/pilot-a eval/reports/pilot-b: exit 0).

## Remaining

- Claude host-runs eval/configs/smoke-two-session-a.yaml in a fresh directory using the existing login/private grader environment; confirm native/event audits, distinct sessions, exact day2.md, exit hashes and one post-day-2 grade. No live calls were made here.
- Host-verify harness controller/verifier compatibility, developer_instructions delivery, retries, nested guards, termination, crash recovery and production sandbox behavior. New CLI versions require a hook probe and audit smoke under decision 0006.
- Re-audit retained pilots with the matching private root; inspect every error/access match and rerun pilot B in a fresh directory if exit hashes are missing. Compare quality only across identical Codex versions; historical 0.162 pilots are diagnostic for 0.163 runs.
- Manually review five valid pilot-A samples and A/B provenance/costs, then have Claude ask the user again before full runs. Configurations and estimate are not authorization.
- Review structural helper extraction and submitted regression quality manually; behavioral graders do not certify those properties.
- Complete control per-call accounting, full done-claim denominator and hash-pinned paired local-minus-cheap_api parity; D-3 through D-5 measurements remain pending.
- Run the full repository suite once before a future merge. Only tests/eval ran here; no staging or commits.

## Decisions

- Preserve r5-full-001/r5-full-002 changes and finish their regressions/documentation together: the interrupted session's work remains uncommitted and was not redone.
- Start day 2 fresh in the same public workspace and preserve exact prompt bytes: the benchmark measures workspace/handoff continuity without runner restatement of day 1.
- Pin control bytes in a persisted runner manifest and select only numeric pinned verdicts: executor-created inputs cannot be adopted or published as trusted evidence.
- Record runner_control_file_preexisting in addition to control_cli_error for fresh-output collisions: F2 now has a specific diagnostic without relaxing existing checks.
- Invalidate native version-evidence failures per task before grading and again during report building: bad evidence must not suppress the whole report, while installed-version changes still halt the run.
- Keep unknown control costs, done-claim denominator and parity unknown: frozen CLIs lack complete per-call accounting; missing usage is never free usage.
- Use identical full task ordering/seed and pilot retry limits, with 600/1200-second process and 20-second grading deadlines: A/B share population and limits.
- Retain bounded per-event protected-path caching: every call, match and unresolved operand remains audited.

## Verify commands

- .venv/bin/python -m pytest tests/eval -q
- git diff --check -- eval tests/eval state/STATUS-eval.md
- git diff --exit-code -- eval/tasks eval/reports/pilot-a eval/reports/pilot-b
- Host only: .venv/bin/python -m eval run --config eval/configs/smoke-two-session-a.yaml --out eval/reports/smoke-two-session-a/
- Host only: .venv/bin/python -m eval.runner.reaudit --private-root "$LHM_PRIVATE_GRADERS" --out eval/reports/pilot-a/
- Host only: .venv/bin/python -m eval.runner.reaudit --private-root "$LHM_PRIVATE_GRADERS" --out eval/reports/pilot-b/
- Host only, hash-bearing source/fresh destination: .venv/bin/python -m eval.runner.regrade --private-root "$LHM_PRIVATE_GRADERS" --from SOURCE --out NEWDIR
- Before comparison: .venv/bin/python -m eval.runner.compare_versions REPORT_A REPORT_B
- Before future merge only: full repository suite once.

## Do not touch

- Frozen eval/tasks/, retained pilot reports, docs/eval-freeze.md, controller/, verifier/, plugin/, shared schemas/configuration and other roles' tests/STATUS files. Never share tasks with Role 3.
- .git is read-only: no staging, commits, history rewrites or file deletion. The final commit plan lists all 15 uncommitted owned paths, including eval/runner/compare_versions.py.
- No full measurement until Claude asks the user again and receives approval; configuration validation and estimates do not authorize calls.
- No executor/controller/judge model calls, network, nested Codex, macOS sandbox-exec or private-root lookup in this sandbox. Tests use synthetic graders only.
- Never backfill historical exit hashes, mutate source regrade runs, run Codex in grading copies or expose grader output to executor/controller context.

## Assumptions

- Freeze commit 7cdaf3b and digest b78913b04280f6696d419d2afdc96b152675973d82f05199ddef848986285d1f remain authoritative; no public task content changed.
- The offline price snapshot openai-standard-short-2026-10-22-v1 and retained pilot tokens/costs are planning inputs, not new measurements. Historical pilots use 0.162.0-alpha.17.2; full/smoke configurations select 0.163.0-alpha.11.1 under decision 0006.
- Full estimates multiply ten-session pilot totals by 14 and budget each fresh day as one session. Supplied 0.4/0.6 plan percentage-point deltas ignore quota resets and concurrent usage; absent before/after observations remain null.
- The previously recorded 0.163 host hook probe result is supplied evidence; one-task audit smoke and production compatibility remain host work.
- Checkpoints are trusted runner evidence. Day-1 exit hashes are historical observations and cannot be reconstructed from the changed final workspace; regrade checks final workspace and retained day/log/prompt provenance.
- Claude owns host verification, pilot review and renewed full-run approval. Mocked success establishes orchestration behavior only.
