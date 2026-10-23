## Done

- Forwarded only captured control_call/control_cli_events lines in order on judge completion, failure, timeout and shutdown; added one compact sorted-key judge_delegation summary with launch/exit/EOF accounting facts and an explicit flush, preserving stdout/verdict/status semantics (.venv/bin/python -m pytest tests/verifier -q: 292 passed, 6 skipped in 3.94s; mocked judge children only).
- Implemented D-3 human-review sampling from schema-validated report.json and listed SHA-256-pinned verdicts, with seed 42, task-type rounds, exact item evidence/reasons, final grading/outcome context, input/internal errors and path-only stdout; no graders or logs are opened (.venv/bin/python -m pytest tests/verifier -q: 292 passed, 6 skipped; synthetic report fixtures and a real sample module entry point).
- Documented the exact stderr line protocol and all three verifier CLI commands in verifier/README.md; added the change summary and Assumptions in verifier/CHANGES.md (.venv/bin/python -m pytest tests/verifier -q: 292 passed, 6 skipped).
- Recorded Claude's completed host verifications supplied by the user: all six Seatbelt tests passed; real macOS EPERM and pipe-holding grandchild cleanup passed 10 of 10 runs, commits e927b73 and 7de2f99 (user-reported host results; exact host commands were not supplied and were not rerun in this sandbox).
- Recorded validate-handoff acceptance of a live controller handoff in the plugin real-mode demo on 2026-10-22 (user-reported host evidence: plugin/evidence/2026-10-22-real; exact host command was not supplied and was not rerun here).

- Separated direct-child exit detection from pipe EOF using 50 ms communicate slices and polling in the shared command/judge runner; completed children trigger immediate group cleanup and a 200 ms final drain, preserving their own exit code/output (.venv/bin/python -m pytest tests/verifier -q: 254 passed, 6 skipped).
- Added four real plain-Python trees covering command-rule and judge transport exits 0/7 with descendants holding stdout/stderr; each finishes within three seconds under a one-second deadline, preserves exact output, passes expected exit 0, and observes the descendant PID gone (.venv/bin/python -m pytest tests/verifier -q: 254 passed, 6 skipped in 2.88s).
- Added two real UTF-8 stdout/stderr capture cases and four injected no-EOF cases for bounded post-exit draining; retained timeout, budget, signal, launch-race and EPERM/ESRCH regressions with clocks accounting for communication slices (.venv/bin/python -m pytest tests/verifier -q: 254 passed, 6 skipped).
- Recorded Claude's user-supplied host verification and commit e927b73 as evidence before this change: six Seatbelt tests passed, SIGTERM left zero processes, and all five 6-second budget runs produced valid exit-0 verdicts (.venv/bin/python -m pytest tests/verifier -q: 250 passed on host, as reported by the user; stdout-holding background-child repro remained unfinished after 40 seconds).
- Updated verifier/CHANGES.md and this STATUS; six Seatbelt tests skipped in that sandbox; the then-pending real sandbox-exec repro was subsequently verified by Claude as recorded above (git diff --check -- verifier tests/verifier state/STATUS-verifier.md: exit 0, no output).

- Fixed killpg EPERM/ESRCH handling with exit-checked direct-child signaling and bounded reaping; timeout and shutdown reasons survive group/direct-child exit races, and completed groups are removed from ownership (.venv/bin/python -m pytest tests/verifier -q: 244 passed, 6 skipped).
- Restricted "cannot launch command" to Popen construction failures; later communication failures have a distinct execution reason, and cleanup OS errors cannot replace the original timeout (.venv/bin/python -m pytest tests/verifier -q: 244 passed, 6 skipped).
- Moved verdict writing and path stdout after successful shutdown-scope exit; injected unexpected final cleanup failures return 2, print no path, and leave an existing verdict unchanged (.venv/bin/python -m pytest tests/verifier -q: 244 passed, 6 skipped).
- Added 44 injected regressions for EPERM/ESRCH at TERM/probe/KILL, 6-/60-second budgets, TERM/HUP/INT shutdown, direct-child exit races, judge timeouts and final cleanup publication order; all new lifecycle tests use simulated time (.venv/bin/python -m pytest tests/verifier -q: 244 passed, 6 skipped in 2.87s).
- Recorded Claude's host verification as historical user-supplied evidence before this follow-up: all six Seatbelt checks passed and real SIGTERM shutdown left no survivors, but intermittent timeout EPERM broke exit/stdout conventions (.venv/bin/python -m pytest tests/verifier -q: 206 passed on the host, as reported by the user; real process-tree checks at budgets 6 and 60 seconds intermittently exited 1 with a path on stdout).
- Updated verifier/CHANGES.md and this STATUS for the macOS follow-up; no other role's paths were edited (git diff --check -- verifier tests/verifier state/STATUS-verifier.md: exit 0, no output).

- Added shared process-group ownership for judge and sandbox commands, TERM/HUP/INT shutdown with TERM/two-second grace/KILL, bounded reaping, normal-exit descendant cleanup and launch-race protection; CLI shutdown exits 2 with stderr only (.venv/bin/python -m pytest tests/verifier -q: 200 passed, 6 skipped).
- Added finite positive HARNESS_VERIFY_BUDGET_SECONDS=450 validation before checks; remaining budget caps command/judge timeouts with a two-second reserve, unstarted checks become unverifiable, verdicts remain schema-valid with exit 0 and H3 feedback (.venv/bin/python -m pytest tests/verifier -q: 200 passed, 6 skipped).
- Tested both launch sites with injected runner/clock/signals and fake child trees, including timeout cleanup within the budget, cooperative exit, shared grace, launch-time deduction and deferred signal delivery; no lifecycle test uses real sleeps (.venv/bin/python -m pytest tests/verifier -q: 200 passed, 6 skipped in 2.15s).
- Preserved sandbox command filtering, environment and Seatbelt profile; the six real Seatbelt tests skipped here and real macOS process-tree cleanup remains pending host verification (.venv/bin/python -m pytest tests/verifier -q: 200 passed, 6 skipped, all six skips in tests/verifier/test_sandbox.py).
- Updated verifier/CHANGES.md and this STATUS; only owned implementation/tests/status paths were edited (git diff --check -- verifier tests/verifier state/STATUS-verifier.md: exit 0, no output).

- Implemented D-3 validate-handoff: offline shared-schema validation, done/remaining overlap rejection, unchanged input bytes, exact supplied-path stdout, no --out flag, input exit 1 and internal exit 2 with stderr-only errors; 19 new cases include the reference handoff through the real module entry point (.venv/bin/python -m pytest tests/verifier -q: 170 passed, 6 skipped).
- Confirmed the approved command accepts the checked-in reference handoff without controller/model execution (.venv/bin/python -m verifier validate-handoff --handoff schemas/examples/handoff.json: exit 0, stdout exactly schemas/examples/handoff.json followed by a newline).
- Fixed H3: every non-pass item receives bounded retry feedback before exhaustion, including all-unverifiable and contract-quality cases; the reference failure verdict's named targets and all 243 five-item status mixes are checked (.venv/bin/python -m pytest tests/verifier -q: 151 passed, 6 skipped).
- Fixed M3/M4: exception phrases exclude later IDs, comma-separated lists share completion predicates, and per-item negatives retain their scope; an unclaimed mechanical failure retains its own reason (.venv/bin/python -m pytest tests/verifier -q: 151 passed, 6 skipped).
- Fixed M5: judge launches in its own process group, kills the group and reaps the child on timeout/errors/completion; timeout remains unverifiable; injected runner/clock/signal tests cover controller and grandchild cleanup without sleeps (.venv/bin/python -m pytest tests/verifier -q: 151 passed, 6 skipped).
- Added finite positive HARNESS_JUDGE_TIMEOUT_SECONDS configuration with the existing 120-second default, validated before execution; verified unset HARNESS_MAX_ATTEMPTS=3 and HARNESS_BACKEND=codex_cli defaults without fixture-injected values (.venv/bin/python -m pytest tests/verifier -q: 151 passed, 6 skipped).
- Claude completed the prior host Seatbelt verification on 2026-10-21; this is historical evidence before that job; Claude's subsequent host completion is recorded above (.venv/bin/python -m pytest tests/verifier -q: 131 passed; .venv/bin/python -m pytest tests/verifier/test_sandbox.py -v: 25 passed, as supplied by the user and docs/weekly/2026-10-21-host-verification.md).
- Retained mechanical checks, measured exec/TUI final-report parsing, claimed_without_evidence, schema validation, quality warnings, deterministic mocked verdicts, timing logs and controller import independence (.venv/bin/python -m pytest tests/verifier -q: 151 passed, 6 skipped).
- Retained approved judge criterion serialization, schema/accounting checks, backend selection and copied HARNESS_NESTED=1 environment; valid judge status/reason/evidence remain unchanged (.venv/bin/python -m pytest tests/verifier -q: 151 passed, 6 skipped; all judge processes mocked).
- Kept only the six real macOS Seatbelt tests skipped in this sandbox, without changing verifier/sandbox.py (.venv/bin/python -m pytest tests/verifier -q: 151 passed, 6 skipped with explicit pending-host reasons).
- Updated verifier/CHANGES.md and this status with the review fixes, evidence, decisions and assumptions (git diff --check -- verifier tests/verifier state/STATUS-verifier.md: exit 0, no output).

- Confirmed the final owned-path diff has no whitespace errors (git diff --check -- verifier tests/verifier state/STATUS-verifier.md: exit 0, no output).

## Remaining

- Pending host verification for this change: exercise the new judge_delegation/control_call/control_cli_events stderr protocol with the real controller and Role 5's parser, including failed/retried calls and timeout/budget paths. No network, nested Codex or live model calls ran here.
- Pending host verification: observe real controller/Codex descendants and the 450-second verifier budget within Role 2's 480-second hook deadline, including children creating their own sessions. Claude's completed macOS EPERM/pipe-holding process-tree checks are recorded in Done; those specific checks are no longer pending.
- Pending host verification: sample a completed proposed-system evaluation report after Role 5 writes it; synthetic schema-valid reports cover D-3 locally. Do not touch the host's in-progress evaluation.
- Pending host verification: exercise Role 2's Stop/SessionStart loop, shared HARNESS_MAX_ATTEMPTS, judge delegation, transcript paths, retry exhaustion and production latency. Live controller handoff acceptance is already verified as recorded in Done.
- Pending host verification: exercise real FastAPI pass/fail/claimed fixtures and the controller judge CLI. The full-contract smoke helper invokes live judge calls; run only with host/live-call authorization.
- D-2: complete broader command support, bounded output capture, deterministic-evidence policy and sandbox auditing. The Python-only macOS subset does not establish general destructive-operation prevention, read isolation, cross-platform support or complete SC-4/SC-5.
- D-4: investigate measured misjudgments and write verifier/RULES.md when comparison evidence exists.
- Before merge: run the full suite once on the host. This session ran only tests/verifier; .git is read-only and no staging, commit or merge was attempted.

## Decisions

- Preserve raw captured accounting record order and emit/flush one summary per attempted delegation: Role 5 must bill child judge calls without changing verdict schemas or judgment semantics.
- Track process launch, natural exit and complete stderr independently of verdict validity: nonzero exits may have complete accounting, while timeout, killed children, missing records and bounded-drain truncation cannot claim completeness.
- Use the explicitly requested D-3 CLI from the role prompt and write DIR/verifier-sample.json with no new flags or shared schema: provide the frozen path-only stdout convention within verifier-owned files.
- Sample verdict attempts in fixed-seed rounds across task types and include final task grading separately: reviewers can distinguish verifier judgments from final hidden-test outcomes, including missing/invalid grading.
- Open only report.json and recognized, listed, hash-checked verdicts resolving inside its directory: human review needs no grader source, grading copy or grading log.

- Poll direct-child exit between at most 50 ms communicate slices: inherited pipes must not delay normal-exit cleanup or fabricate a criterion timeout, and built-in POSIX selectors drain stdout/stderr together.
- Save the direct child's exit code, KILL its group immediately, then drain at most 200 ms: background descendants are cleanup targets and their pipe lifetime does not determine the command verdict.
- Test controlled real Python trees without sandbox-exec or controller calls, alongside injected stuck-pipe cases: exercise actual inherited descriptors within the permitted environment while preserving sandbox isolation rules.

- Treat killpg EPERM/ESRCH as gone or unsignalable and fall back only to the known Popen child if alive: follow the user's macOS protocol without signaling a reused exited-child PID.
- Preserve timeout/shutdown across signaling, polling, reaping and pipe-close OS races: cleanup must not fabricate a launch failure or escape from the final CLI scope.
- Classify launch failure at Popen construction and publish the verdict only after scope cleanup: keep the original criterion reason and prevent success-path stdout with an error exit.

- Track judge and sandbox groups in one CLI shutdown scope: detached sessions require explicit forwarding, and all groups share one two-second grace period.
- Defer Python shutdown exceptions during launch until PID registration, without blocking signals across fork: avoid orphaning a newly launched child or inheriting a blocked SIGTERM mask.
- Use immediate group KILL after successful completion, TERM/grace/KILL on abnormal exits, and bounded reaping/closed pipes: leave no unbounded communicate or wait in verifier cleanup.
- Default total verification budget to 450 seconds and reserve two seconds before dispatch: follow the user's selected protocol while retaining existing per-criterion limits and valid budget-failure verdicts.

- Preserve the original --handoff argument as a string for stdout: converting it to Path for display would normalize supplied relative path spelling.
- Separate handoff input errors from validator infrastructure failures: unreadable/invalid input exits 1, while schema-loading and unexpected validator errors exit 2 without stdout.
- Check done/remaining overlap after schema validation without a contract: contradictory states are detectable locally; contract membership, coverage and artifact existence need additional context.
- Treat every non-pass item as unfinished for rule 6: the user's H3 instruction and frozen null-on-pass-or-exhaustion invariant supersede the previous status=fail-only interpretation, including contract-quality warnings.
- Keep the three-detail/count-rest overflow and 300-character format: the user explicitly requested preserving the existing policy.
- Keep grouped IDs in one clause and stop extraction at exception phrases: this fixes both reported claim errors while retaining explicit negative predicates and conservative unmapped prose handling.
- Mark only mechanically failed claimed criteria claimed_without_evidence: unverifiable is not proof of a failed assertion, unclaimed failures retain their own reason, and valid judge reasons remain unchanged.
- Keep fresh POSIX sessions and replace the earlier KILL-only judge teardown with the shared shutdown protocol: subprocess.run alone only kills the direct child.
- Retain HARNESS_JUDGE_TIMEOUT_SECONDS=120 as a per-judge limit and cap it by the user-approved 450-second overall budget: Role 2 owns the outer 480-second deadline.
- Validate deadline configuration before any check and use injected process runner, clock and signal functions for lifecycle tests: malformed settings must not spend calls, and this environment forbids live judge execution.
- Unset configuration in the autouse test fixture: ordinary tests now exercise real defaults, with explicit unset-default and override regressions.
- Keep measured response_item/message/assistant/final_answer/output_text parsing and the public workspace judge artifact: published exec/TUI evidence and the approved controller CLI remain the interface boundaries.
- Keep unavailable/malformed judge results unverifiable without verifier retries: the controller owns generation retry/fallback limits.

## Verify commands

- .venv/bin/python -m pytest tests/verifier -q
- .venv/bin/python -m verifier validate-handoff --handoff schemas/examples/handoff.json
- git diff --check -- verifier tests/verifier state/STATUS-verifier.md
- Host command: .venv/bin/python -m pytest tests/verifier/test_sandbox.py -v (the six Seatbelt checks are already verified by Claude; this command was not rerun here).
- Host only with live-call authorization, pending: .venv/bin/python tests/verifier/smoke.py
- Host only before merge, pending: .venv/bin/python -m pytest

## Do not touch

- schemas/, docs/, root configuration, other roles' implementations/tests/STATUS files, and concurrent changes. This session owns only verifier/, tests/verifier/ and state/STATUS-verifier.md.
- Shared schema, CLI and hook interfaces; never import controller into verifier or expose private graders to it.
- verifier/sandbox.py isolation rules; do not weaken safety to make nested sandbox tests pass.
- Existing harness/, experiments/, scripts/, plugin evidence and docs/hooks-contract.md.
- .git contents, staging, commits, file deletion, git history rewriting, external service configuration, secrets, network access, nested Codex, live model calls and sandbox-exec in the current environment.

## Assumptions

- This session follows the user's judge-accounting, host-status and D-3 priority order. The requested sample command is authorized by the current task and role prompt; check/validate-handoff flags, shared schemas and hook interfaces remain unchanged.
- The role prompt does not specify sample filename, seed, review format or handling of small pools: use verifier-sample.json, seed 42, documented review JSON and up to n verdicts (including an explicit empty result). These choices are recorded in verifier/README.md and verifier/CHANGES.md for review.
- Candidate verdict names follow the existing runner's verdict-N.json and prefixed/archived naming; plain verdict.json is also accepted. Absolute paths or report-relative paths must resolve inside the report directory. Duplicate references and hash/schema failures are input errors.
- Sample units are verdict attempts, so tasks may repeat; final_grading_outcome is the task's final report grading, not a fabricated per-attempt hidden result. Invalid/time-out/error tasks can retain null grading.
- Supplied host results are evidence from Claude reported by the user, not commands rerun here. They complete the specific Seatbelt, macOS EPERM/pipe-holding cleanup and live handoff acceptance items, but do not verify this session's new accounting protocol or live sampling.
- The post-exit drain bound is 200 ms; any output still unavailable after that bound is omitted while preserving the completed child's own exit code. Actual same-group descendants are killed before this drain.
- Same-state handoff entries may represent multiple artifacts or remaining steps; only contradictory done/remaining membership is rejected beyond the schema, without adding an unspecified uniqueness requirement.
- Rule 6 failed items means status other than pass, as explicitly instructed; this replaces the prior contrary assumption. Up to three items receive details and further items are counted.
- Only explicit criterion IDs and done/completed/implemented/passing terms count. Generic completion prose and semantic paraphrases are not inferred; exception tails remain conservatively unclaimed.
- HARNESS_MAX_ATTEMPTS defaults to 3 and HARNESS_BACKEND to codex_cli when unset. Verifier-local HARNESS_JUDGE_TIMEOUT_SECONDS defaults to 120 and HARNESS_VERIFY_BUDGET_SECONDS to 450; both must be finite and positive.
- The two-second reserve covers graceful group termination. Post-KILL reaping uses at most two 0.1-second waits per direct child; verdict serialization and scheduling use the margin before the 480-second outer deadline.
- Cleanup reaches signalable owned POSIX groups. Per user instruction, group EPERM/ESRCH is treated as gone or unsignalable; fallback can address only the known live direct child. Injected tests model descendants already exiting at that race; Claude reported the real macOS EPERM/pipe-holding cleanup passed 10/10. Separate-session controller/Codex descendants still require host verification. A direct SIGKILL to the verifier is uncatchable and cannot execute Python shutdown handlers.
- The public workspace is the judge artifact directory. Missing before/after material remains unverifiable under the rubric. Judge outcomes/controller calls remain mocked; real plain-Python helpers exercise run_judge transport without any controller/model call.
- Current transcript support is pinned to published exec/TUI evidence. Resume/compaction variants and installed-wheel schema resources remain unverified.
- No optional FastAPI/httpx provisioning, real macOS sandbox, live model or real controller integration was attempted here. Historical host results do not verify this job's changes.
- No PR was requested; verifier/CHANGES.md contains the change summary and Assumptions for a future PR. Other roles' concurrent changes were not edited, staged or committed.
