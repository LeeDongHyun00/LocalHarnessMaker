## Done

- Added the narrow missing-terminal exception for explicitly interrupted segments in runner/re-audit/regrade, preserving all other inconclusive checks; covered hard and graceful interruption followed by same-session completion and regrade (`.venv/bin/python -m pytest tests/eval -q`: 1092 passed in 103.45s).
- Reused schema-valid manifest-pinned contracts before the first executor launch and archived verified partial control preparation; changed/unowned files still fail safely (`.venv/bin/python -m pytest tests/eval -q`: 1092 passed in 103.45s).
- Added infrastructure-only fresh reruns with retained-evidence regrading for other tasks, access-match refusal, source/config/input/version/pricing checks, source immutability, per-task/run provenance and prior/new accounting preserved across resume/regrade (`.venv/bin/python -m pytest tests/eval -q`: 1092 passed in 103.45s).
- Added SIGINT/SIGTERM stop diagnostics and exit 130 without tracebacks for run, rerun, continuation and regrade; covered signals before executor launch and during checkpoint cleanup (`.venv/bin/python -m pytest tests/eval -q`: 1092 passed in 103.45s).
- Fixed newline-only JSONL framing in audit, telemetry, limit detection, control accounting and redaction; masked heredoc bodies before shell tokenization while retaining unquoted-expansion uncertainty and protected-path checks (`.venv/bin/python -m pytest tests/eval -q`: 1092 passed in 103.45s).
- Updated README/CHANGES and retained the committed v2 pilot, frozen v1 inputs and historical reports without edits (`git diff --check -- eval tests/eval state/STATUS-eval.md`: exit 0; `git diff --exit-code -- eval/tasks eval/tasks-v2 eval/reports`: exit 0).
- Verified the requested separate command surface and worktree without model calls (`.venv/bin/python -m eval.runner.rerun_invalid --help`: exit 0, --private-root/--from/--out/--reasons listed; `git symbolic-ref --short HEAD`: r5/v2).

## Remaining

- Host: transfer these changes only at a safe boundary for the other checkouts. Regrade full B to recover partition-sign's interrupted terminal and line-endings' Unicode JSONL framing, and full harness to recover round-robin's quoted heredoc. These actual source artifacts/private graders were unavailable here; no host outcome recovery is claimed.
- Host: use `python -m eval.runner.rerun_invalid --private-root P --from SOURCE --out NEW --reasons control_cli_error,runner_control_file_preexisting` for the completed harness source's pre-launch stable-unique invalidity. Inspect retained source/selection provenance. For checkpoint-only interrupted/capacity-limited runs, resume the original command/config/output first.
- Host: review the previously committed aa41a35 v2 candidate and priority pricing, apply an explicitly reviewed candidate freeze and obtain spending approval before its 24-session baseline-A calibration. Preserve all candidates; revise difficulty by whole families/types, never by individual pilot outcome.
- After v2 calibration: build the remaining sixteen planned families, validate the population and publish its separate freeze through Role 1. This session did not touch eval/tasks-v2/.
- Preserve main-checkout measurements and earlier follow-ups: C authored once by the user, reduced B/full harness workflow, paired comparisons, five pilot-A reviews and twenty-sample reporting. Do not reinterpret v1 results as matched v2 evidence.
- Run the full repository suite once before merge on the host. Only tests/eval ran here. Review the final Commit plan; no staging or commits were performed.

## Decisions

- Exempt only missing_terminal_event for exit_code=-2/interrupted=true captures: all bytes/access matches and other audit errors remain evidence; completed resume evidence is retained separately.
- Archive pinned partial pre-launch outputs and reuse validated pinned contracts: resume must not adopt executor-authored or changed control files, and no source evidence is deleted.
- Select fresh reruns using invalid reasons plus causal infrastructure evidence: ordinary outcomes, precision-only audit errors and unexplained invalidity use retained-evidence regrading; any candidate access match refuses before calls.
- Start rerun tasks from public starters in new runtimes: source/grading workspaces never reach the executor. Fresh attempts/segments describe new execution; provenance retains original segments/log references, and all calls/costs remain counted once, with unknown costs null.
- Preserve the original SIGINT/SIGTERM diagnostic across checkpoint cleanup and return 130: both control preparation and executor interruption must exit without a traceback.
- Parse heredoc boundaries before shell tokenization and frame JSONL on newline only: quoted body syntax and Unicode line separators inside string values are data, while unquoted expansions and protected-path checks remain conservative.
- Preserve optional v2 task-root/service-tier behavior and the approved report schema/CLI flags: this change adds only the explicitly requested separate rerun operation.

## Verify commands

- .venv/bin/python -m pytest tests/eval -q
- git diff --check -- eval tests/eval state/STATUS-eval.md
- git diff --exit-code -- eval/tasks eval/tasks-v2 eval/reports
- .venv/bin/python -m eval.runner.rerun_invalid --help
- Host/offline: python -m eval.runner.regrade --private-root P --from SOURCE --out NEW
- Host/approved spending only: python -m eval.runner.rerun_invalid --private-root P --from SOURCE --out NEW --reasons control_cli_error,runner_control_file_preexisting

## Do not touch

- Work only in r5/v2 with this worktree's .venv; edit only eval/, tests/eval/ and this status file. Preserve all other checkouts and roles' paths.
- Frozen eval/tasks/, eval/tasks-v2/, retained reports, private production graders, schemas, controller/, verifier/, plugin/, root configuration and existing CLI flags. Never share task contents with Role 3.
- .git is read-only: no staging, commits, history rewrites or project-file deletion.
- No live executor/controller/judge calls, network, nested Codex, macOS sandbox-exec or real private-root lookup in this environment. Use synthetic private fixtures and mock model/executor calls.
- Never execute/resume Codex in a grading copy, expose private content, fabricate accounting or waive malformed/unsupported/unresolved/unfinished audit evidence through later success. The interrupted missing-terminal exception is the only new audit exemption.
- Keep C skeletons unfilled until the user authors them, and keep the v2 candidate unfrozen until the reviewed host freeze step. Priority pricing remains unverified by this session.

## Assumptions

- The four host failures and absence of access attempts are user-supplied context; actual host evidence was unavailable. Regression tests use synthetic retained runs and a representative heredoc with the specified mixed raw-regex quotes/backslashes.
- SOURCE for rerun_invalid is a completed schema-valid report/checkpoint. Checkpoint-only interrupted/capacity-limited runs resume normally first; no historical exit hash is invented for fresh-selected pre-launch failures.
- --reasons selects any matching recorded invalid reason, followed by the infrastructure eligibility checks. Other tasks are regraded from retained evidence; a reason string alone never authorizes rerunning a quality outcome.
- Earlier v2 pilot difficulty, priority rates and host measurement quality remain unmeasured/unverified here. Existing deadline and freeze decisions are unchanged.
