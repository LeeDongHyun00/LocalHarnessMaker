## Done

- Added 0.163.0-alpha.11.1 thread_settings_applied metadata validation and full-record private-marker scanning; unknown kinds remain inconclusive. Added the synthetic 34-record native fixture with the exact line-9 settings structure (.venv/bin/python -m pytest tests/eval -q: 596 passed in 56.24s).
- Added applied-thread model/effort telemetry beside turn_context, conflict rejection, retained session evidence and a two-session 0.163 regression that reaches day 2 and grades once (.venv/bin/python -m pytest tests/eval -q: 596 passed).
- Added resumable STOP-E1 usage-limit handling for executor error/turn.failed events and control_cli_events stderr envelopes; stderr preserves the supplied limit/reset text, and the interrupted task gets no outcome/report (.venv/bin/python -m pytest tests/eval -q: 596 passed, including exact event-pair, CLI stderr, no-thread recovery and whole-loop halt tests).
- Preserved pending verifier/control operations, completed days and hash-pinned interrupted control streams/partial outputs across same-output recovery; eventual reports include archived evidence and retain unknown costs (.venv/bin/python -m pytest tests/eval -q: 596 passed, including all six two-session control stages, repeated limits and verifier reinstruction recovery).
- Updated eval/README.md and eval/CHANGES.md; preserved frozen tasks and retained pilots, with no staging or commits (git diff --check -- eval tests/eval state/STATUS-eval.md: exit 0; git diff --exit-code -- eval/tasks eval/reports/pilot-a eval/reports/pilot-b: exit 0).

## Remaining

- Claude reruns eval/configs/smoke-two-session-a.yaml on the host in a fresh output directory. Confirm both days' native/event audits, settings, distinct sessions, exact day2.md, exit hashes and one post-day-2 grade. The attempt1 invalid report remains unchanged and uncommitted.
- Host-verify harness controller/verifier compatibility, developer_instructions delivery, retries, nested guards, termination, usage-limit recovery and production sandbox behavior. New CLI versions require a hook probe and audit smoke under decision 0006.
- Re-audit retained pilots with the matching private root; inspect every error/access match and rerun pilot B in a fresh directory if exit hashes are missing. Compare only identical Codex versions; historical 0.162 pilots are diagnostic for 0.163 runs.
- Manually review five valid pilot-A samples and A/B provenance/costs, then have Claude ask the user again before full runs. Configurations and estimates are not authorization.
- Review structural helper extraction and submitted regression quality manually; behavioral graders do not certify those properties.
- Complete control per-call accounting, full done-claim denominator and hash-pinned paired local-minus-cheap_api parity; D-3 through D-5 measurements remain pending.
- Run the full repository suite once before a future merge. Only tests/eval ran here; no staging or commits.

## Decisions

- Continue from committed b04f9b0: the two-session implementation was already complete; this session changes compatibility and infrastructure recovery only.
- Treat thread_settings_applied as metadata: its full record receives private-path checks without interpreting ordinary settings as shell operands; malformed shapes and other unknown kinds remain inconclusive.
- Require model/effort agreement across turn_context and thread_settings_applied: neither source can erase conflicting applied evidence.
- Classify structured usage-limit failures as resumable infrastructure stops: halt the task loop before runner retries, grading or another task, without recording the interrupted task's outcome.
- Archive interrupted control outputs and persist pending verification separately from executor transport: retries preserve evidence and avoid rerunning completed executor work.
- Detect control limits after the bounded CLI returns: existing nested control_cli_events logs supply evidence without changing frozen interfaces or other-role paths.
- Keep missing accounting unknown and reset text verbatim: quota stops do not establish zero cost or a reset timezone.

## Verify commands

- .venv/bin/python -m pytest tests/eval -q
- git diff --check -- eval tests/eval state/STATUS-eval.md
- git diff --exit-code -- eval/tasks eval/reports/pilot-a eval/reports/pilot-b
- Host only, fresh destination: .venv/bin/python -m eval run --config eval/configs/smoke-two-session-a.yaml --out eval/reports/smoke-two-session-a-attempt2/
- Host only: .venv/bin/python -m eval.runner.reaudit --private-root "$LHM_PRIVATE_GRADERS" --out eval/reports/pilot-a/
- Host only: .venv/bin/python -m eval.runner.reaudit --private-root "$LHM_PRIVATE_GRADERS" --out eval/reports/pilot-b/
- Host only, hash-bearing source/fresh destination: .venv/bin/python -m eval.runner.regrade --private-root "$LHM_PRIVATE_GRADERS" --from SOURCE --out NEWDIR
- Before comparison: .venv/bin/python -m eval.runner.compare_versions REPORT_A REPORT_B
- Before future merge only: full repository suite once.

## Do not touch

- Frozen eval/tasks/, retained reports including eval/reports/smoke-two-session-a-attempt1/, docs/eval-freeze.md, controller/, verifier/, plugin/, shared schemas/configuration and other roles' tests/STATUS files. Never share tasks with Role 3.
- .git is read-only: no staging, commits, history rewrites or file deletion. Exclude the uncommitted host smoke report from the commit plan.
- No full measurement until Claude asks the user again and receives approval; configuration validation and estimates do not authorize calls.
- No executor/controller/judge model calls, network, nested Codex, macOS sandbox-exec or private-root lookup in this sandbox. Tests use synthetic graders only.
- Never backfill historical exit hashes, mutate source regrade runs, run Codex in grading copies or expose grader output to executor/controller context.

## Assumptions

- b04f9b0 contains the completed two-session work. The user's supplied host smoke stopped before day 2 and is invalid solely because line 9 was unsupported; this session inspected only the authorized native rollout and made no host/private-grader measurement.
- Freeze commit 7cdaf3b and digest b78913b04280f6696d419d2afdc96b152675973d82f05199ddef848986285d1f remain authoritative. Frozen task content and historical pilots are unchanged.
- The supplied usage-limit error and turn.failed events carry the same message; both nested error.message and direct message are supported. Reset text is relayed without inferring a timezone.
- Control commands may finish existing internal retries/fallbacks before returning their retained structured events; eval halts on return and issues no subsequent call. No other-role implementation was changed.
- The offline price snapshot and retained pilot totals remain planning inputs, not new measurements; unobserved accounting stays null. Historical pilots use 0.162.0-alpha.17.2 and full/smoke configurations select 0.163.0-alpha.11.1.
- Checkpoints and runner manifests remain trusted evidence. Mocked regression success establishes orchestration only; Claude owns host verification, pilot review and renewed full-run approval.
