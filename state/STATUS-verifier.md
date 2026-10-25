## Current state

- Latest job: 2026-10-25 status-format-migration Role 4.
- Existing work and evidence are preserved under History.
- V3 first priority, pending host/Role 2/3 integration: wire the approved CLI operations and verifier.stop_text functions into native Stop/SessionStart; use python_identity.signature_snapshot_bytes for pre-edit baselines and supply retained claim-audit objects/accounting. Verify one application repair, one separate ledger continuation, refreshed final-message hashes, invalid-ledger advisory/no older-memory injection and two non-evaluation project/two-session smoke evidence. No live hooks, model calls or nested Codex ran here.

## History

### Done

- Implemented the user-approved v3 check and ledger-validate CLIs while retaining historical contract/handoff/sample operations; deterministic checks, confined native-session artifacts, exact immutable raw evidence, offline schema/provenance/accounting checks, canonical Python signature baselines and sandboxed argv execution have synthetic and actual-module-entry-point coverage (.venv/bin/python -m pytest tests/verifier -q: 669 passed, 8 host-only Seatbelt skips in 11.85s).
- Implemented durable one-repair reservation, round-two exhaustion/advice, duplicate-Stop result reuse, original-message retention, unsupported citation filtering and stale-audit updates; no v3 judge/controller/model calls are made (.venv/bin/python -m pytest tests/verifier -q: 669 passed, 8 skipped; 103 new v3 cases include every supported check kind's pass/fail/unverifiable outcomes and path/hash/continuation regressions).
- Published exact repair and ledger-writing texts in verifier/stop_text.py, with failed-row-only evidence rendering and an at-most-once, fsynced ledger-request marker; implemented Python ledger identity extraction, complete validation coverage/hash checks and atomic latest-ledger copying, including rejection of stale hashes and repeated validation of invalid ledgers (.venv/bin/python -m pytest tests/verifier -q: 669 passed, 8 skipped; schema-valid report/ledger artifacts and real CLI subprocess fixtures).
- Documented CLI behavior, baseline encoding, exact package integration locations and host limitations in verifier/README.md; marked retained v1/v2 judge behavior historical and updated this handoff (git diff --check -- verifier tests/verifier state/STATUS-verifier.md: exit 0, no output).

- Fixed sampling of the completed full-harness layout: version-1 report validation, repository-relative retained paths and hash-checked result.json inline verdicts, while preserving standalone verdict/day-1/day-2 support, task-type rounds and report grading context (.venv/bin/python -m verifier sample --reports eval/reports/full-harness --n 20 --out /tmp/lhm-verifier-review-78912e5238cc4e51a2bb6bfb13723f71.json: exit 0, stderr verifier sample selected=20 available=142 seed=42; all four task types represented).
- Added the user-requested optional sample --out with the existing default destination unchanged, plus synthetic retained-layout fixtures covering inline/standalone/coexisting verdicts, restarted two-session attempt numbers, grading provenance, determinism, input preservation and corrupt input errors (.venv/bin/python -m pytest tests/verifier -q: 566 passed, 8 host-only Seatbelt skips in 6.79s).
- Confirmed the external report and all 120 task result files were unchanged and documented the correction in verifier/README.md and verifier/CHANGES.md (.venv/bin/python inline read-only SHA-256 comparison before/after sampling: report and 120 task results unchanged: True; inline inventory: 142 verdicts and zero standalone verdict files).

- Added a complete verdict-N.claims.json sidecar for every successful check, with one claimed/clause/status observation per criterion, all five summary counts and unchanged schema/stdout/exit semantics; covered every claimed/unclaimed status, empty/all-judge criteria, no final report, budget exhaustion, deterministic bytes, module entry point and publication failures (.venv/bin/python -m pytest tests/verifier -q: 556 passed, 8 skipped in 5.78s).
- Extended lexical claim extraction to status tables/checklists, explicit all-criteria statements, inclusive numeric ID ranges and distinctive description words; retained negative/exception scope and final-report filtering, with exact supporting clauses shared by sidecars and claimed_without_evidence (.venv/bin/python -m pytest tests/verifier -q: 556 passed, 8 skipped; 56 labeled synthetic reports, precision=1.000000, recall=1.000000, TP=75, FP=0, FN=0 printed in the terminal summary).
- Documented the sidecar format, matching rules, synthetic measurement, write-failure semantics and pending runner/host integration in verifier/README.md, verifier/RULES.md, verifier/CHANGES.md and fixtures/README.md; no live report, model call or nested Codex ran (.venv/bin/python -m pytest tests/verifier -q: 556 passed, 8 host-only Seatbelt skips).

- Restricted judged-item re-instruction to status=fail; unverifiable judge reasons/evidence remain exact, overall=fail remains, and uncertainty uses no feedback detail/overflow slots, including mixed workspace failures (.venv/bin/python -m pytest tests/verifier -q: 476 passed, 8 skipped in 11.54s; mocked judge and direct feedback regressions at attempts 1–3).
- Classified malformed file_exists/regex paths as contract-caused before filesystem access: prose/whitespace, separators, absolute/drive-qualified paths, any parent traversal and globs do not retry; plausible missing paths remain workspace-caused/actionable (.venv/bin/python -m pytest tests/verifier -q: 476 passed, 8 skipped in 11.54s; lexical-validation and assembled-verdict regressions).
- Updated verifier/RULES.md and verifier/CHANGES.md with the measured futile-retry corrections, verification and explicit path-policy assumptions (.venv/bin/python -m pytest tests/verifier -q: 476 passed, 8 skipped; all eight skips are pending host Seatbelt verification).
- Reviewed the owned-path diff and confirmed no whitespace errors; concurrent Role 3 controller/test changes were left untouched (git diff --check -- verifier tests/verifier state/STATUS-verifier.md: exit 0, no output; git status --short: nine modified owned files plus concurrent Role 3 changes).
- Added unittest discover (-s/-p/-t, -v/-q/-b/-f/-k), local module/dotted/file targets and pytest -x/-k/-rA/--tb=short/-p no:cacheprovider with option-aware operands, path/symlink containment, shell rejection and unchanged -c AST checks/Seatbelt isolation (.venv/bin/python -m pytest tests/verifier -q: 369 passed, 8 skipped in 4.74s).
- Restricted feedback to fail and explicitly workspace-caused unverifiable items using internal workspace/contract/verifier/transport/budget categories; no actionable item yields null feedback with overall=fail preserved and no schema changes (.venv/bin/python -m pytest tests/verifier -q: 369 passed, 8 skipped; cause-category, mixed-status, missing-input, quality, budget and judge-result/delegation regressions).
- Documented command support and retry causes in verifier/RULES.md, linked README, and wrote the change summary/Assumptions in verifier/CHANGES.md; added host passing/failing unittest discover tests (.venv/bin/python -m pytest tests/verifier -q: 369 passed, 8 skipped; all eight Seatbelt cases pending Claude's host run for this change).
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

### Remaining

- V3 first priority, pending host/Role 2/3 integration: wire the approved CLI operations and verifier.stop_text functions into native Stop/SessionStart; use python_identity.signature_snapshot_bytes for pre-edit baselines and supply retained claim-audit objects/accounting. Verify one application repair, one separate ledger continuation, refreshed final-message hashes, invalid-ledger advisory/no older-memory injection and two non-evaluation project/two-session smoke evidence. No live hooks, model calls or nested Codex ran here.
- V3 host verification: run .venv/bin/python -m pytest tests/verifier/test_sandbox.py -v (all eight cases: six original plus two unittest discovery cases); exercise the new argv adapter's subdirectory cwd with the whole-workspace write boundary, no network/outside writes, raw output and process-tree cleanup. These boundaries are reused and mocked, not host-accepted by this session.
- V3 performance: measure deterministic report/ledger overhead separately from project command execution on the host; no live timing/quality/cost acceptance is claimed. Python-only extraction and the conservative existing command allowlist leave unsupported checks unverifiable.
- Historical pending integration, lower priority than v3: run claim extraction/sidecar generation on a live harness final report, manually compare every criterion claim/clause/status and reconcile summary counts; verify Role 5 ingestion supplies the false_done_rate denominator while preserving claimed-and-unverifiable separately. No live report or runner integration ran here; eval/ remains unchanged and synthetic accuracy does not measure live accuracy.

- Pending Claude's host run: all six existing Seatbelt tests and the two new passing/failing unittest discover cases. Host command: .venv/bin/python -m pytest tests/verifier/test_sandbox.py -v. Historical host passes below do not verify this change; no sandbox-exec ran here.
- Pending host integration for this change: rerun the proposed-system smoke and confirm judged unverifiable items and contract-invalid file/regex paths stop without spending remaining executor attempts, judge fail items still retry, and plausible missing paths remain actionable. Also confirm unittest criteria execute. No network, nested Codex, live model calls or sandbox-exec ran here.
- Pending host verification for this change: exercise the new judge_delegation/control_call/control_cli_events stderr protocol with the real controller and Role 5's parser, including failed/retried calls and timeout/budget paths. No network, nested Codex or live model calls ran here.
- Pending host verification: observe real controller/Codex descendants and the 450-second verifier budget within Role 2's 480-second hook deadline, including children creating their own sessions. Claude's completed macOS EPERM/pipe-holding process-tree checks are recorded in Done; those specific checks are no longer pending.
- Pending host verification: exercise Role 2's Stop/SessionStart loop, shared HARNESS_MAX_ATTEMPTS, judge delegation, transcript paths, retry exhaustion and production latency. Live controller handoff acceptance is already verified as recorded in Done.
- Pending host verification: exercise real FastAPI pass/fail/claimed fixtures and the controller judge CLI. The full-contract smoke helper invokes live judge calls; run only with host/live-call authorization.
- D-2: complete broader command support, bounded output capture, deterministic-evidence policy and sandbox auditing. The Python-only macOS subset does not establish general destructive-operation prevention, read isolation, cross-platform support or complete SC-4/SC-5.
- D-4: investigate further measured misjudgments after the host smoke. verifier/RULES.md now documents the reported live-smoke fixes and cause categories; broader comparison evidence remains pending.
- Before merge: run the full suite once on the host. This session ran only tests/verifier; .git is read-only and no staging, commit or merge was attempted.

### Decisions

- The user's explicit 2026-10-25 schema freeze and exact CLI authorization supersede the still-proposed labels in checked-in shared documents: implement only the two authorized v3 operations without editing shared interfaces or other roles' paths.
- V3 reservations are persisted in the completion report and an exclusive evidence/ledger-request.txt marker: duplicate Stops cannot spend another repair, audit or ledger request; Role 2 consumes the summary and exact package texts.
- Reuse the existing fail-closed Python/Seatbelt runner with an argv adapter and raw-byte capture: retain bounded execution, credential isolation and process-group cleanup without an unsandboxed fallback or historical behavior changes.
- Canonical Python AST snapshot encoding and ledger identity syntax are documented package helpers: Role 3 must use the same baseline helper; unsupported/ambiguous extraction is unavailable, never semantic guesswork.
- Retain invalid citations only in the immutable original audit snapshot, removing them from structured evidence references: unsupported claims cannot create invalid artifact paths/hashes or change deterministic verdicts.
- Preserve the last valid latest-ledger copy on invalid current input and require Role 2's prior-session identity gate: never silently inject older memory; repeated validation cannot rehabilitate a stale/invalid measured ledger.

- Honor the user's explicit sample --out request despite the earlier no-new-flags sampling decision: only the verifier-owned sampler CLI changes; shared schemas and other commands remain unchanged.
- Validate version-1 reports against the exact JSON schema preserved in decision 0003: decision 0009 preserves those reports without fabricating the absent task_false_done_rate metric.
- Rebase only the recognized eval/reports/DIR_NAME prefix into the supplied report directory: copied report paths resolve locally while containment and SHA-256 checks remain mandatory.
- Prefer listed standalone verdicts per task and otherwise use the listed result.json verdicts array: avoid sampling the same retained verdict twice; inline verdict_index preserves distinct sessions with restarted attempt numbers.

- Emit an additive verifier-owned sidecar explicitly requested by the user: preserve the frozen verdict schema, CLI arguments, stdout path and exit-code contract while exposing passing, failing, uncertain and unclaimed observations.
- Use one extraction result for the failure reason and the complete sidecar: the denominator and negative evidence must describe the same final report and verdict; exclude the synthetic contract-quality item from criterion counts.
- Use deterministic lexical description matching with at least two content words (one for a one-word vocabulary) and one word unique among criterion descriptions: reject ambiguous shared descriptions without model calls or inferred semantic paraphrases.
- Preserve verbatim first supporting clauses/table rows and scoped negatives/exceptions: global claims exclude named exception-tail criteria, and an unmapped global exception supplies no claim.
- Write the sidecar before the verdict after successful shutdown cleanup: a sidecar write failure preserves an existing verdict and returns internal exit 2 with no stdout; consumers must ignore both files from failed invocations because publication is not a two-file transaction.
- Report micro precision/recall on all labeled synthetic report/criterion pairs in pytest's terminal summary: the fixture is repeatable extractor evidence, not a claim of live harness accuracy or an evaluation-wide false-done measurement.

- Supersede the earlier workspace-judge retry rule: the user's first live measurement shows judge uncertainty can request evidence the workspace cannot contain; judged items retry only on fail and preserve unverifiable reasons without feedback.
- Validate file/regex paths lexically before resolving them: malformed contract prose, multiple operands, absolute paths, parent traversal and globs cannot be repaired by executor workspace edits; plausible missing paths remain workspace causes.
- Refine the earlier blanket H3 retry policy: retry fail items and explicitly workspace-caused mechanical unverifiable items only; contract/verifier/transport/budget defects and judge uncertainty do not justify executor retries.
- Carry explicit internal cause metadata through Execution/Result into reinstruct without serialized fields: preserve the verdict schema and valid judge reason/evidence while avoiding classification based on generated text.
- Retain conservative non-actionable command timeouts and unknown causes: a deadline alone cannot prove a workspace defect, especially when capped by the remaining verification budget.
- Parse selection expressions, discovery patterns and plugin disabling separately from paths: common test options must not be mistaken for workspace filenames, and arbitrary pytest plugins remain rejected.
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
- Earlier H3 decision (superseded by this session): every non-pass item was included, including contract-quality warnings; the live smoke established these retries could be futile.
- Keep the three-detail/count-rest overflow and 300-character format: the user explicitly requested preserving the existing policy.
- Keep grouped IDs in one clause and stop extraction at exception phrases: this fixes both reported claim errors while retaining explicit negative predicates and conservative unmapped prose handling.
- Mark only mechanically failed claimed criteria claimed_without_evidence: unverifiable is not proof of a failed assertion, unclaimed failures retain their own reason, and valid judge reasons remain unchanged.
- Keep fresh POSIX sessions and replace the earlier KILL-only judge teardown with the shared shutdown protocol: subprocess.run alone only kills the direct child.
- Retain HARNESS_JUDGE_TIMEOUT_SECONDS=120 as a per-judge limit and cap it by the user-approved 450-second overall budget: Role 2 owns the outer 480-second deadline.
- Validate deadline configuration before any check and use injected process runner, clock and signal functions for lifecycle tests: malformed settings must not spend calls, and this environment forbids live judge execution.
- Unset configuration in the autouse test fixture: ordinary tests now exercise real defaults, with explicit unset-default and override regressions.
- Keep measured response_item/message/assistant/final_answer/output_text parsing and the public workspace judge artifact: published exec/TUI evidence and the approved controller CLI remain the interface boundaries.
- Keep unavailable/malformed judge results unverifiable without verifier retries: the controller owns generation retry/fallback limits.

### Verify commands

- .venv/bin/python -m pytest tests/verifier -q (latest session: 669 passed, 8 skipped in 11.85s; skips require host Seatbelt).
- git diff --check -- verifier tests/verifier state/STATUS-verifier.md (latest session: exit 0, no output).

- .venv/bin/python -m verifier sample --reports eval/reports/full-harness --n 20 --out /tmp/lhm-verifier-review-78912e5238cc4e51a2bb6bfb13723f71.json

- .venv/bin/python -m pytest tests/verifier -q
- .venv/bin/python -m verifier validate-handoff --handoff schemas/examples/handoff.json
- git diff --check -- verifier tests/verifier state/STATUS-verifier.md
- Host only, pending Claude for this change: .venv/bin/python -m pytest tests/verifier/test_sandbox.py -v (six existing Seatbelt tests plus two new unittest discover cases).
- Host only with live-call authorization, pending: .venv/bin/python tests/verifier/smoke.py
- Host only before merge, pending: .venv/bin/python -m pytest

### Do not touch

- This v3 session: only verifier/, tests/verifier/ and state/STATUS-verifier.md are writable scope; shared schemas/CLIs/docs, controller/, plugin/, eval/, other roles' files and .git remain untouched. Never read eval/tasks*/ or private grader paths.

- schemas/, docs/, root configuration, other roles' implementations/tests/STATUS files, and concurrent changes. This session owns only verifier/, tests/verifier/ and state/STATUS-verifier.md.
- Shared schema, CLI and hook interfaces; never import controller into verifier or expose private graders to it.
- verifier/sandbox.py isolation rules; do not weaken safety to make nested sandbox tests pass.
- Existing harness/, experiments/, scripts/, plugin evidence and docs/hooks-contract.md.
- .git contents, staging, commits, file deletion, git history rewriting, external service configuration, secrets, network access, nested Codex, live model calls and sandbox-exec in the current environment.

### Assumptions

- This session follows the user's explicit v3 approval and priority order despite stale proposal wording in shared documents; no further approval or interface proposal is needed for the two supplied CLI shapes.
- All v3 artifact inputs are already retained in the canonical native-session directory; Role 2/3 own pin verification, trustworthy request/configuration derivation and visible question handling. The verifier validates references and does not invent user answers or executable oracles.
- The schema represents test_command as a requirement kind whose check type is command; no separate test_command check schema is added. Unsupported executable/language/platform support stays unverifiable or invalid rather than extending the shared schema.
- Signature baselines use the newly documented Python AST helper's canonical bytes; previous hash encodings are not inferred or guessed. Ledger constants accept a bare literal binding name or NAME = literal when its exact value must be pinned.
- Tests use injected command outcomes plus real verifier CLI subprocesses that do not invoke models/sandbox-exec. All eight existing host-only Seatbelt tests remain pending; historical passes do not validate this change. Only the verifier package suite ran; the full repository suite is still required before a future merge.
- No PR, staging or commit was performed; .git is read-only. The final report supplies the exact owned-path commit plan and a Conventional Commit message.

- The supplied external report is read-only. The files present during this session contain 142 inline verdicts across 120 task results, not the reported 147; no missing verdicts are invented or obtained from unlisted files. No standalone verdict artifacts are listed or present in that report snapshot.
- Source precedence is per task: listed standalone verdicts are authoritative when present; otherwise listed result.json supplies verdicts. The review unit remains a verdict, with all criterion items unchanged and final task grading alongside it, not an inferred per-attempt grading result.
- Inline verdict_path/verdict_sha256 identify the containing result.json; verdict_index is its zero-based array index. Result task ID/type must match report.json; grading always comes from report.json.
- This session's explicit sampling priority supersedes the older Remaining order. The worktree's .venv was used; no other role's paths, schemas, .git or external report were modified. The only external output is the requested review artifact in /tmp; no staging, commits, network, nested Codex, model calls or sandbox-exec ran.

- The user explicitly authorizes the new sidecar while retaining shared verdict/schema/CLI/hook interfaces. Its unspecified JSON shape is {items: [{id, claimed, clause, status}], summary: {claimed_items, claimed_and_pass, claimed_and_fail, claimed_and_unverifiable, unclaimed_items}}, documented in verifier/README.md; suffix replacement uses Path.with_suffix(".claims.json").
- A successful check includes fail/unverifiable verdicts; invalid input/internal computation failures cannot provide a complete trustworthy observation and publish no new files. An artifact write failure may leave partial/old files, which must not be consumed.
- Claim observations cover real contract criteria only, including judge uncertainty and budget/quality warnings. A missing final report yields zero claims; an empty criteria list yields zero counts, not the synthetic diagnostic as a criterion.
- Completion is any affirmative observation in the final report, retaining its first exact supporting clause (whole table row), trimmed only at the edges. Later contradictory claims are not reconciled; there is no stemming/synonym inference. Description overlap thresholds and table/status equivalents are the documented deterministic policy.
- Synthetic precision/recall counts criterion/report pairs. This session's 56 controlled reports have 75 positive labels; no live harness accuracy or numeric aggregate false_done_rate is claimed. Claude must verify live reports and Role 5 consumption on the host.

- Criterion paths use conservative single-token literal syntax: whitespace-containing filenames, prose/operand separators (; , | &), glob/expansion characters (* ? [ ] { }) and Windows drive/root spellings are rejected even if the filesystem could store such names. Safe ./ prefixes and names such as ..report.txt remain plausible.
- The user's futile-retry corrections take priority over Remaining's host checks and supersede the earlier workspace-judge retry rule and role-prompt rule 6. No shared schema, CLI or hook interface changes are needed.
- This session is confined to the separate worktree and its .venv; only owned verifier implementation/docs/tests/STATUS paths are edited. .git is read-only, with no staging or commits; no main-checkout or live-evaluation work is performed.
- Short option operands accept attached/separate spelling; unittest positional discovery START/PATTERN/TOP is also supported with the same path checks. Discovery patterns are filename globs, not directory operands.
- Schema-valid judge uncertainty retains the supplied reason/evidence as workspace review, but is never re-instructed. Delegation errors/timeouts are transport failures. A command timeout or unclassified failure is conservatively non-actionable.
- Current host verification remains pending for all eight Seatbelt cases regardless of historical host results. Only .venv/bin/python -m pytest tests/verifier -q ran in this session; other roles' concurrent files and .git were not modified.
- This session follows the user's unittest/pytest command support, actionable retry and host-pending STATUS priority order. This instruction supersedes role-prompt rule 6 and earlier H3 decisions; shared schemas, CLI flags and hook interfaces remain unchanged.
- The role prompt does not specify sample filename, seed, review format or handling of small pools: use verifier-sample.json, seed 42, documented review JSON and up to n verdicts (including an explicit empty result). These choices are recorded in verifier/README.md and verifier/CHANGES.md for review.
- Candidate verdict names follow the existing runner's verdict-N.json and prefixed/archived naming; plain verdict.json is also accepted. Absolute paths or report-relative paths must resolve inside the report directory. Duplicate references and hash/schema failures are input errors.
- Sample units are verdict attempts, so tasks may repeat; final_grading_outcome is the task's final report grading, not a fabricated per-attempt hidden result. Invalid/time-out/error tasks can retain null grading.
- Supplied host results are evidence from Claude reported by the user, not commands rerun here. They complete the specific Seatbelt, macOS EPERM/pipe-holding cleanup and live handoff acceptance items, but do not verify this session's new accounting protocol or live sampling.
- The post-exit drain bound is 200 ms; any output still unavailable after that bound is omitted while preserving the completed child's own exit code. Actual same-group descendants are killed before this drain.
- Same-state handoff entries may represent multiple artifacts or remaining steps; only contradictory done/remaining membership is rejected beyond the schema, without adding an unspecified uniqueness requirement.
- Re-instruction includes status=fail and explicitly workspace-caused mechanical unverifiable only. Judged unverifiable items never retry. Up to three actionable items receive details and further actionable items are counted; no actionable items ends feedback before exhaustion.
- Completion references now include IDs/lists/ranges, explicit all-criteria statements, status/checklist rows and distinctive description words per verifier/RULES.md. Generic all-done prose and semantic paraphrases remain unmapped; scoped negatives and exception tails remain conservative. This supersedes the earlier IDs-only assumption.
- HARNESS_MAX_ATTEMPTS defaults to 3 and HARNESS_BACKEND to codex_cli when unset. Verifier-local HARNESS_JUDGE_TIMEOUT_SECONDS defaults to 120 and HARNESS_VERIFY_BUDGET_SECONDS to 450; both must be finite and positive.
- The two-second reserve covers graceful group termination. Post-KILL reaping uses at most two 0.1-second waits per direct child; verdict serialization and scheduling use the margin before the 480-second outer deadline.
- Cleanup reaches signalable owned POSIX groups. Per user instruction, group EPERM/ESRCH is treated as gone or unsignalable; fallback can address only the known live direct child. Injected tests model descendants already exiting at that race; Claude reported the real macOS EPERM/pipe-holding cleanup passed 10/10. Separate-session controller/Codex descendants still require host verification. A direct SIGKILL to the verifier is uncatchable and cannot execute Python shutdown handlers.
- The public workspace is the judge artifact directory. Missing before/after material remains unverifiable under the rubric. Judge outcomes/controller calls remain mocked; real plain-Python helpers exercise run_judge transport without any controller/model call.
- Current transcript support is pinned to published exec/TUI evidence. Resume/compaction variants and installed-wheel schema resources remain unverified.
- No optional FastAPI/httpx provisioning, real macOS sandbox, live model or real controller integration was attempted here. Historical host results do not verify this job's changes.
- No PR was requested; verifier/CHANGES.md contains the change summary and Assumptions for a future PR. Other roles' concurrent changes were not edited, staged or committed.

## 2026-10-25 status-format-migration Role 4

### Done

- Format conversion only; see History / Done (python3 inline conversion audit: archived bytes restore exactly).

### Remaining

- See History / Remaining; format conversion only.

### Decisions

- See History / Decisions: format conversion only; existing decisions are unchanged.

### Verify commands

- See History / Verify commands; format conversion only.

### Do not touch

- See History / Do not touch; format conversion only.

### Assumptions

- See History / Assumptions; format conversion only.
## 2026-10-25 round-two-audit-retention Role 4

### Done

- Fixed audit selection after the initial deterministic report: retain the verified original audit, otherwise merge the supplied sidecar or canonical claim-audit.json; preserve audited source hashes, citation verification results and accounting, and refresh stale status on later Stop events (.venv/bin/python -m pytest tests/verifier -q: 682 passed, 8 host-only Seatbelt skips in 31.79s).
- Added 13 regression cases covering report/supplied/discovered audits, unchanged/changed final messages, rejected citation hashes, replacement-audit rejection, duplicate round-two freshness updates and no-audit unavailability; assert unchanged sidecar/accounting bytes (.venv/bin/python -m pytest tests/verifier -q: 682 passed, 8 skipped).

### Remaining

- Host/Role 1: rerun the read-only reference cross-role pipeline test with installed controller/plugin/verifier packages; it was read here, not executed or modified.
- Retain prior integration, host Seatbelt and performance work listed in the historical Remaining section; run the full suite once on the host before merge.

### Decisions

- Prefer a report's retained original over any replacement sidecar: later Stop events must preserve the single original audit and its mechanically verified citations.
- Load a sidecar when the prior report has no audited source or accounting reference: the frozen pipeline runs deterministic checks before controller claim-audit.
- Refresh stale to complete when current bytes again match the audited hash: freshness follows the current final message without a new provider call.
- Append this dated section with the six handoff headings: main already contains the append-only status-format migration; preserve this worktree's existing history verbatim.

### Verify commands

- .venv/bin/python -m pytest tests/verifier -q (682 passed, 8 host-only Seatbelt skips in 31.79s).
- git diff --check -- verifier tests/verifier state/STATUS-verifier.md (exit 0, no output).

### Do not touch

- Only verifier/, tests/verifier/ and this STATUS file are writable scope; shared interfaces, other roles' files, the external cross-role reference and .git remain read-only. Do not stage or commit.

### Assumptions

- No new interface or provider invocation is needed; later rounds mean round 2 and repeated Stop updates under the frozen round 1/2 CLI.
- The user's specific audit-retention fix takes priority over earlier host integration work. Cross-role/live-hook acceptance and the eight Seatbelt cases remain host verification, not results claimed by these local tests.
