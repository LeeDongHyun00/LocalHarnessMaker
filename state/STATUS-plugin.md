## Current state

- Latest job: 2026-10-25 status-format-migration Role 2.
- Existing work and evidence are preserved under History.
- Integrate Roles 3/4 before any H3/live acceptance: this checkout still has historical controller/verifier parsers. plugin/v3_adapter.py alone contains the user-authorized v3 CLI spellings and the provisional verifier.ledger.ledger_request(ledger=Path, requirements=Path, session_id=str) formatter seam. Match that seam to Role 4's actual in-package ledger text; the current missing formatter fails open visibly and never substitutes plugin-authored wording.

## History

### Done

- Implemented the default v3 hook runtime, exact-model/version/pricing pin-check CLI, confined atomic artifacts, immutable evidence and append-only accounting-prefix validation; legacy v1/v2 routing and evidence remain explicit historical paths (.venv/bin/python -m pytest tests/plugin -q: 313 passed, 1 opt-in real Codex test skipped in 27.21s; mocked pin tests cover exact/renamed/missing/unobservable models, unverified versions, missing prices, timeout and app-server model/list responses).
- Added per-native-session phase locking/reservations, first-prompt requirements and explicit-answer question pauses, deterministic completion delegation, one executed-failure repair, stale audits, one separate ledger continuation, strict prior-session selection and ledger coverage/hash checks (.venv/bin/python -m pytest tests/plugin -q: 313 passed, 1 skipped in 27.21s; v3 stdin/stdout and state-machine fixtures cover success, disabled pin, pending questions, edited pending workspace, one repair, escalation, duplicate Stops, ledger publication/injection and rejection without older-ledger fallback).
- Updated installer snapshots/--check, executor instructions, README and host checks; added host-only v3 two-session preparation/structural audit while retaining historical demos (.venv/bin/python -m pytest tests/plugin -q: 313 passed, 1 skipped in 27.21s; .venv/bin/python -m plugin.v3_demo --help, plugin.host_checks --help and plugin.pin_check --help: each exit 0; bash -n plugin/install.sh plugin/demo.sh: exit 0; git diff --check -- plugin tests/plugin state/STATUS-plugin.md: exit 0).

- Added plugin.host_checks prepare/second/check and plugin/HOST-CHECKS.md with explicit host commands, isolated installation, interactive trust capture, fresh second sessions without hook-trust bypass, empty-PATH bundle installation, raw production-hook stream recording, evidence layout and offline rejection of contradictory captures (.venv/bin/python -m pytest tests/plugin -q: 272 passed, 1 opt-in live Codex test skipped in 18.57s; new host-check fixtures cover all three scenarios and eleven incomplete/false-silence cases; no live procedure was run).
- Added bounded SessionStart CLI-version checks against VERIFIED_VERSIONS.json, persisted cli_version, one advisory per session naming the probe command, resume detection and fail-open handling including unavailable handoff context (.venv/bin/python -m pytest tests/plugin -q: 272 passed, 1 skipped in 18.57s; fake-version tests cover listed/unlisted versions, once-per-session injection, resumed updates, timeout recovery and unavailable handoff).

- Recorded Claude's live exhaustion, generation and validation handoff-failure demonstrations on 2026-10-23, committed as 3ef1e84, at plugin/evidence/2026-10-23-{exhaustion,generation,validation}; every checker passes on the exported copies (.venv/bin/python -m plugin.handoff_failure_demo check --scenario SCENARIO --out plugin/evidence/2026-10-23-SCENARIO, run separately for all three: overall=pass each).
- Recorded the user's supplied successful GitHub CI result for OS-independent path fix 1550267 on Ubuntu/Python 3.11 and 3.14 (user host/CI report: both Python jobs passed; network-disabled session did not query GitHub).

- Made recorded-path comparisons filesystem-independent across two_session_demo, handoff_failure_demo and check_demo_evidence, with matching lexical aliases in portable export. Added identity-resolution checks of committed evidence/export plus rejection of unrelated workspaces, macOS aliases pointing elsewhere, symlinks and mismatched placeholders; committed evidence is unchanged (.venv/bin/python -m pytest tests/plugin -q: 252 passed, 1 opt-in live Codex test skipped in 16.36s; .venv/bin/python -m plugin.two_session_demo check --out plugin/evidence/2026-10-23-two-session: overall=pass; .venv/bin/python -m plugin.check_demo_evidence plugin/evidence/2026-10-22-real: overall=pass; git diff --name-only -- plugin/evidence: empty).

- Prepared host-only plugin.handoff_failure_demo day1/day2/check for real retry exhaustion and separately injected handoff generation/validation failures, with offline evidence rejection tests and documented Claude steps. Added portable export for future captures and kept committed evidence unchanged (.venv/bin/python -m pytest tests/plugin -q: 219 passed, 1 opt-in live test skipped in 20.38s; git diff --check -- plugin tests/plugin state/STATUS-plugin.md: exit 0).

- Recorded Claude's real two-session host demonstration on 2026-10-23 at de38626, retained in plugin/evidence/2026-10-23-two-session/ and committed as 4fa9ec2. Day 1 waited for approval, created result.txt, passed the real verifier at attempt 1 with zero re-instructions and saved a validated handoff retaining the random release label. Day 2 used a new session in the same project, received exactly that handoff in SessionStart/model context, used the label in its contract without user restatement and verified followup.txt after approval (.venv/bin/python -m plugin.two_session_demo check --out plugin/evidence/2026-10-23-two-session: approval_gates=true, context_visible=true, new_session=true, saved_handoff_validated=true, session_start_injected=true, user_restatement_needed=false, overall=pass).

- Prepared plugin.two_session_demo day1/day2/check with isolated real-mode sessions, a random day-1 decision, fixed follow-up without restatement, retained CLI-validation output/hash and an offline injection/context/artifact checker; documented host steps in plugin/DEMO-SCENARIO.md and README. Synthetic positive/negative fixtures and injected launch tests cover new-thread then approval routing; no live demo was run (.venv/bin/python -m pytest tests/plugin -q: 200 passed, 1 opt-in live test skipped in 14.35s).
- Verified --check accepts the newly registered 0.163.0-alpha.11.1 using an isolated installer and injected version probe; unverified-version diagnostics remain covered with a separate fake version (.venv/bin/python -m pytest tests/plugin -q: 200 passed, 1 skipped in 14.35s).

- Registered codex-cli 0.163.0-alpha.11.1 with plugin/evidence/2026-10-22-exec-0.163 from host commit 55f2b1d; the supplied probe passes offline with SessionStart/UserPromptSubmit/Stop/Stop, visible context and one continuation (.venv/bin/python -m plugin.check_probe_evidence --expected-version "codex-cli 0.163.0-alpha.11.1" plugin/evidence/2026-10-22-exec-0.163: context_visible=true, continued_once=true, exit_code=0).
- Recorded Claude's completed macOS EPERM/pipe-holding-grandchild verification, supplied by the user rather than run here: five host suite runs included 100 real process-tree repetitions; real Stop-hook SIGTERM, group SIGHUP and child-exit trees left zero processes in all three runs (host commit aa3c709; tests/plugin: 5/5 host runs passed, 100 repetitions; real Stop-hook tree checks: 3/3 runs, 0 survivors).
- Recorded Claude's passing live real-mode demo from host commit 232f23d and re-audited its retained evidence offline (.venv/bin/python -m plugin.check_demo_evidence plugin/evidence/2026-10-22-real: approval_gate=true, real_task_verified=true, overall=pass, max_hook_overhead_seconds=0.18847).
- Recorded completed host README installation checks supplied by the user: temporary HOME/CODEX_HOME installation and --check work, repeat installation is idempotent, timeout JSON values are integers and real ~/.codex is unchanged (Claude host report of README install/--check: passed, idempotent, integer timeouts, real ~/.codex unchanged; exact host shell log not supplied).

- Replaced active single-pin checks with plugin/VERIFIED_VERSIONS.json and its validated reader; the first entry retains 0.162.0-alpha.17.2 exec/TUI evidence. Probe/demo accept unlisted versions and save the exact installed identity; offline probe audit validates identity and optional expected version, and tests audit every registry entry against passing evidence (.venv/bin/python -m pytest tests/plugin -q: 185 passed, 1 opt-in live Codex test skipped in 14.66s).
- Allowed installation on unverified versions while --check returns 1 with a distinct Codex version unverified diagnostic and instructions to probe/audit/add evidence; hooks and skill checks remain independent and installed snapshots include the registry/reader (.venv/bin/python -m pytest tests/plugin -q: 185 passed, 1 skipped in 14.66s; fake CLI and isolated-home tests cover verified/unverified installation and diagnostics).
- Silenced ESRCH group warnings after leader exit while retaining bounded retry, member inspection, unexpected-error and unresolved-survivor diagnostics; corrected process fakes to keep returncode consistent with poll (.venv/bin/python -m pytest tests/plugin -q: 185 passed, 1 skipped in 14.66s; quiet ESRCH, EPERM/ESRCH cleanup paths and twenty real inherited-pipe trees passed).
- Updated plugin/README.md and recording sequence for the changing-version policy and evidence workflow (.venv/bin/python -m pytest tests/plugin -q: 185 passed, 1 skipped in 14.66s; all registry evidence audits passed offline).

- Pinned the installed executor at codex-cli 0.162.0-alpha.17.2 in plugin/CODEX_VERSION (codex --version: codex-cli 0.162.0-alpha.17.2).
- Completed D-1 startup evidence for both interactive CLI and codex exec; Role 1 published the canonical document, resolving the earlier STOP-2 (.venv/bin/python -m plugin.check_probe_evidence plugin/evidence/2026-10-21-exec plugin/evidence/2026-10-21-tui: context_visible=true, continued_once=true, exit_code=0 for both; cat docs/hooks-contract.md: published by Role 1 on 2026-10-21 with user approval).
- Added the exact HARNESS_NESTED=1 silent fast path to the three lifecycle hooks and the original probe. Tests leave stdin open, poison imports/I/O/subprocesses, exercise stub precedence and unset/empty/0/true/01 normal behavior, and require exit 0 with zero bytes on both streams (.venv/bin/python -m pytest tests/plugin -q: 70 passed, 1 opt-in live test skipped in 4.93s).
- Implemented thin CLI delegation, unchanged schema-example stubs, approval/edit routing, reviewed-contract hashing, same-session resume state, bounded Stop continuation, fail-open handling and timing; each lifecycle hook has stdin/stdout tests with mocked CLIs (.venv/bin/python -m pytest tests/plugin -q: 70 passed, 1 skipped in 4.93s).
- Passed SC-2 with one initial Codex process: full fixture contract appears as developer context and the session waits for approval without verifier calls (HARNESS_STUB=1 HARNESS_CODEX_LIVE=1 HARNESS_CODEX_EVIDENCE=plugin/evidence/2026-10-21-d2 .venv/bin/python -m pytest tests/plugin/test_codex_integration.py -q: 1 passed in 17.98s; request-summary.json: contract_visible=true, approval_pending=true, verifier_calls=0).
- Completed D-2 in a fresh routing-only stub demo, with the summary displayed before scripted demo approval, exactly one re-instruction, two verifier calls and synthetic pass; all source and transcript logs are retained (HARNESS_STUB=1 bash plugin/demo.sh --out plugin/evidence/2026-10-21-d2-pass --scripted-approval: exit 0; .venv/bin/python -m plugin.check_demo_evidence plugin/evidence/2026-10-21-d2-pass: approval_gate=true, reinstructions=1, attempts=2, overall=pass, synthetic=true, real_task_verified=false, max_hook_overhead_seconds=0.192873).
- Added the executor skill and updated plugin/README.md with reproduction commands, limitations, change summary and assumptions; validated using isolated PyYAML tooling without changing repository dependencies (skill-creator/scripts/quick_validate.py plugin/skills/harness with temporary PYTHONPATH: Skill is valid!; README link audit: OK; bash -n plugin/demo.sh: exit 0).
- Applied the user's STOP-P3 prototype decision: synchronous controller contract calls now allow thirty seconds, UserPromptSubmit has a forty-second outer deadline, and each contract call logs latency on stderr including timeouts. Mocked ten/thirty-second successes and timeout handling preserve the approval gate and silent nested bypass (.venv/bin/python -m pytest tests/plugin -q: 73 passed, 1 opt-in live test skipped in 5.56s; git diff --check -- plugin tests/plugin state/STATUS-plugin.md: exit 0).

- Connected the pass path to controller handoff generation, CLI/local validation and publication for SessionStart; failing null re-instructions before the limit now warn and fail open, while exhaustion reports unmet evidence (.venv/bin/python -m pytest tests/plugin -q: 79 passed, 1 skipped in 18.17s; tests include pass-to-next-session injection and failed generation preserving an earlier handoff).
- Applied the 2026-10-22 caller deadlines, injected runner/clock budgeting and process-group timeout termination; exact nested guards remain unchanged (.venv/bin/python -m pytest tests/plugin -q: 79 passed, 1 skipped in 18.17s; injected Stop deadlines were 480/90/5 seconds and timeout sent SIGKILL to the child group with bounded reap).
- Added isolated installation, portable source/data snapshots, project instructions and distinct version/hooks/skill diagnostics; tests use temporary HOME/CODEX_HOME and a fake Codex version executable (.venv/bin/python -m pytest tests/plugin -q: 79 passed, 1 skipped in 18.17s; installer test checks three messages, installed CLI imports and a complete installed stub hook loop outside the checkout).
- Prepared real-mode demo capture/audit and a recording screen sequence without running Codex; real mode selects codex_cli, isolates HOME/CODEX_HOME/workspace and verifies exact result.txt contents plus handoff (.venv/bin/python -m pytest tests/plugin -q: 79 passed, 1 skipped in 18.17s; real-mode boundary test uses an injected runner only).
- Documented installation from a fresh clone, environment overrides, host reproduction, change summary and assumptions (bash -n plugin/install.sh plugin/demo.sh: exit 0; git diff --check -- plugin tests/plugin state/STATUS-plugin.md: exit 0).

- Addressed R2-DL-1, R2-HOOK-1/2, R2-DL-2/3 and R2-INST-5 with a shared owned-group runner for hooks, installer, demo and probe: catchable signals, deadlines, non-timeout exceptions and normal exits use TERM, up to two seconds of grace, KILL survivors, and bounded reap; spawn-time signals are deferred until ownership is recorded (.venv/bin/python -m pytest tests/plugin -q: 131 passed, 1 skipped in 13.22s; fake cooperative/stubborn child trees cover SIGTERM/SIGHUP/SIGINT, normal exits, timeouts, OSError and the spawn/register window without real sleeps).
- Applied revised Stop 660s, verifier 480s, handoff 120s, validation 5s and unchanged contract 30s/UserPromptSubmit 40s; reserved four seconds for cleanup and tied Runtime defaults to the integer hooks.json deadlines. Documented the controller's 35s deadline and the approved contract cutoff exception, replacing the stale 180s claim (R2-DL-6; .venv/bin/python -m pytest tests/plugin -q: 131 passed, 1 skipped in 13.22s; direct default-budget equality and cumulative injected-clock tests passed).
- Fixed R2-INST-1, R2-HOOK-5 and R2-DL-5 by rendering JSON integer timeouts, preflighting bounded integer overrides and diagnosing timeout type/value mismatches in installed registration (.venv/bin/python -m pytest tests/plugin -q: 131 passed, 1 skipped in 13.22s; fractional/non-finite/out-of-range overrides leave targets absent, and --check rejects floats, strings, booleans and changed values).
- Fixed R2-HOOK-4 and R2-INST-4 with the .local-harness-maker project marker and a canonical ancestor gate before timing, runtime imports, state or logs; unmarked lifecycle/probe hooks return 0 with no output or writes (.venv/bin/python -m pytest tests/plugin -q: 131 passed, 1 skipped in 13.22s; silent unmarked hooks, descendants, siblings and symlink escapes are covered).
- Fixed R2-HOOK-3 by generating/validating handoffs on retry exhaustion as well as pass; failed generation/validation archives old context under a unique stale name and exhaustion still reports unmet items (.venv/bin/python -m pytest tests/plugin -q: 131 passed, 1 skipped in 13.22s; exhaustion generation, next-session injection and failed-generation/validation non-injection tests passed).
- Fixed R2-INST-2/3/7 and R2-DL-4 with environment/PATH/app-bundle binary resolution, bounded version probes, a distinct missing-CLI diagnostic, persisted semantic registration checks, full preflight and repairable/idempotent installs; retained unrelated hooks and project instructions (.venv/bin/python -m pytest tests/plugin -q: 131 passed, 1 skipped in 13.22s; fake version executables and injected probes only, all installer targets use temporary HOME/CODEX_HOME).
- Fixed R2-HOOK-6 with malformed-session archiving/reset and temporary-file/replace publication for state JSON (.venv/bin/python -m pytest tests/plugin -q: 131 passed, 1 skipped in 13.22s; malformed JSON/metadata and atomic replacement tests passed).
- Fixed R2-DEMO-6 with initial, post-request and immediately-before-approval workspace inventories; real-mode collection/audit rejects task entries before approval, including unexpected files inside .harness (.venv/bin/python -m pytest tests/plugin -q: 131 passed, 1 skipped in 13.22s; early-write collection and each corrupted-snapshot audit were rejected).
- Updated README and recording sequence for revised behavior and limitations; no live Codex, model call, installation in a real home, stage or commit was performed (bash -n plugin/install.sh plugin/demo.sh: exit 0; git diff --check -- plugin tests/plugin state/STATUS-plugin.md: exit 0).

- Corrected the host-reproduced R2-DL-2 inherited-pipe hang: run_group now checks leader exit through 50ms communicate slices and independent poll, starts group shutdown immediately on leader exit, then bounds final draining to 250ms before returning the leader's status/output. Existing injected signal/deadline/non-timeout-exception cleanup remains covered (.venv/bin/python -m pytest tests/plugin -q: 132 passed, 1 skipped in 6.60s).
- Added an executed real process-tree regression: a child starts a pipe-holding grandchild in its group and exits 3; run_group must preserve stdout/stderr, return in under 3s despite a 5s call deadline, and leave no live grandchild. The real tree uses only 0.01/0.1s sleeps; a finally block kills the test group on failure (.venv/bin/python -m pytest tests/plugin -q: 132 passed, 1 skipped in 6.60s; test_exited_child_with_grandchild_holding_pipes_returns_promptly passed).
- Updated README for exit detection independent of EOF and the bounded final drain; no Codex/model call, real-home configuration, stage or commit was performed (git diff --check -- plugin tests/plugin state/STATUS-plugin.md: exit 0).

- Fixed EPERM/ESRCH cleanup races on all group signal/liveness paths: reap leaders before bounded retries, enumerate non-zombie members with bounded shell-free ps, recheck PGIDs before individual signals, then reap and verify survivors. OS/listing/reap errors log to stderr without replacing normal results, deadlines or shutdown signals (.venv/bin/python -m pytest tests/plugin -q: 174 passed, 1 skipped in 13.56s).
- Parameterized the real inherited-pipe process tree for twenty consecutive cases in one session, requiring exit code 3, exact captured output, return within three seconds of the leader's exit announcement and no live grandchild. Added transient/persistent EPERM/ESRCH injection for normal exit, timeout, SIGTERM/SIGHUP/SIGINT, plus individual-signal/reap errors and process-list filtering (.venv/bin/python -m pytest tests/plugin -q: 174 passed, 1 opt-in Codex test skipped in 13.56s; all twenty real-tree cases passed).
- Documented fallback signalling, zombie-aware verification, stderr diagnostics and sandbox limits; no Codex/model calls, real configuration changes, stage or commit were performed (git diff --check -- plugin tests/plugin state/STATUS-plugin.md: exit 0).

### Remaining

- Integrate Roles 3/4 before any H3/live acceptance: this checkout still has historical controller/verifier parsers. plugin/v3_adapter.py alone contains the user-authorized v3 CLI spellings and the provisional verifier.ledger.ledger_request(ledger=Path, requirements=Path, session_id=str) formatter seam. Match that seam to Role 4's actual in-package ledger text; the current missing formatter fails open visibly and never substitutes plugin-authored wording.
- Host-only v3 verification: after integration run .venv/bin/python -m plugin.host_checks v3-prepare --out /tmp/lhm-v3-host-capture, follow its two interactive session scripts/explicit question-answer instructions, then run v3-check. Verify exact installed model/list protocol, pin disablement, fresh-session hook trust, requirements table/pause, real completion/one repair, ledger writing and injection on two non-evaluation smoke projects. No Codex/model/sandbox-exec was run here; timing, two-call cost targets and real model-context acceptance remain unmeasured.
- Role 1 updates docs/hooks-contract.md with active v3 sequencing, explicit question-ID/answer JSON, adapter/message seam, pending live compatibility and optional PreToolUse deferral. The Role 2 prompt does not own that document, so it was not edited. Retained compatibility evidence exposes only measured SessionStart/UserPromptSubmit/Stop behavior; no pre-tool hook was registered.

- Claude runs the prepared trust, bundle and silence captures from plugin/HOST-CHECKS.md after host evaluation capacity is available, then runs plugin.host_checks check on each capture and its copied review directory. These procedures are offline-tested; live results remain pending. macOS sandbox isolation remains a separate unprepared host check.
- Pending host measurement: revised Stop 660s / check 480s / handoff 120s / validation 5s budgets and Role 4's internal 450s verifier budget, plus contract cutoff at 30s inside 40s despite the controller's 35s deadline. SIGINT/deadline/exception cleanup with real controller/verifier/Codex descendants remains separate from the completed host SIGTERM/SIGHUP/child-exit checks.
- Before merge: coordinating role runs the full suite once. This job runs only tests/plugin; .git is read-only and all work remains unstaged/uncommitted. Do not disturb the in-progress host evaluation or edit eval/, controller/ or verifier/.

### Decisions

- Implement the schema freeze and four v3 CLI operation shapes supplied explicitly by the user: that authorization supersedes the still-proposed wording in checked-in shared documents without editing another role's paths.
- Use a thin v3 adapter and retain explicit HARNESS_INTERFACE_VERSION=2 for historical demos/tests (HARNESS_STUB=1 also remains historical): the production default is v3 and legacy retry/backend defaults do not leak into it.
- Require explicit user-authored question-ID/value JSON instead of inferring natural-language mappings: silence or an ambiguous answer never makes requirements ready and never spends another Luna call.
- Keep verifier-owned repair/ledger text and fail open on absent package integration: do not invent a second verification loop or present mocked cross-package behavior as live H3 acceptance.

- Record host/CI completions as user-supplied evidence and rerun only the failure-demo offline checkers: network, live models, Codex, sandbox-exec and real-home writes are prohibited in this session.
- Use an interactive trust-establishment session followed by a fresh exec session, with no hook-trust bypass in either launch; retain diagnostic wrappers around the production hooks: actual hook invocation and distinct session IDs prevent skipped/untrusted hooks from passing as silence or persisted trust.
- SessionStart adds an advisory once per session for an unlisted discovered CLI version, including a probe command; bounded probe and registry failures fail open: the explicit user request supersedes the role prompt's old STOP-P2 blocking instruction without changing shared interfaces.

- Canonicalize recorded paths using POSIX lexical normalization and only /private/var, /private/tmp and /private/etc aliases; compare any placeholder-bearing path exactly: evidence semantics must not depend on the checking host filesystem or arbitrary symlinks. Keep real source/destination filesystem safety checks in the exporter.

- Use HARNESS_MAX_ATTEMPTS=1 in copied demo child environments and one deliberately impossible mechanical criterion: exhaustion needs no paid re-instruction loop, while real Stop saves remaining work for a fresh session.
- Inject generation/validation failures only at the selected CLI boundary through a temporary interpreter wrapper: keep the real hooks, task verification and fresh day-2 SessionStart, with validation failure occurring only after real pending-handoff generation.
- Retain raw future captures outside the repository and export placeholder paths to fresh evidence directories: preserve original raw bytes, document the transformation and recompute the exported saved-handoff validation hash. Existing committed evidence is unchanged.

- Prepare the two real sessions as separate host commands with a random day-1 release-label decision and a fixed day-2 prompt omitting that label: this makes approval and recovery reviewable before further live calls.
- Require real saved-handoff CLI validation plus local schema validation, exact SessionStart/model-context matching, distinct threads, both approval gates, passing verdicts and exact follow-up bytes: offline fixtures validate the checker without claiming live D-4/D-5 success.

- Follow the 2026-10-22 user-approved changing-version policy: no hold, rollback or STOP-P2 single-pin refusal; CODEX_VERSION stays as the historical first identity, and VERIFIED_VERSIONS.json is the compatibility history.
- Treat unlisted versions as unverified rather than incompatible: installation warns and proceeds, --check reports failure until evidence is listed, and probes can collect the evidence needed for promotion.
- Suppress only ESRCH group warnings after leader exit: retain the earlier defensive retries and member fallback so real survivors and unexpected cleanup errors remain diagnosable.

- Handle group errors inside plugin-owned code without importing verifier: reap before three group attempts separated by 10ms, then enumerate live group members and recheck membership before signalling each PID. Preserve the original run result/exception and report errors on stderr.
- Verify post-KILL live membership for up to 300ms using ps states, excluding zombies: orphan exit-record collection belongs to init/launchd. Inspection denial explicitly reports unverified cleanup; the known direct leader still receives a fallback attempt.
- Measure the twenty real-tree cases from the leader's exit announcement with a three-second cleanup limit and separate startup allowance: scheduling delays before leader exit must not masquerade as inherited-pipe hangs.

- Apply the latest user-approved review decisions in this turn over the prior STATUS deadline/cleanup/stale-handoff policy: Stop 660s, verifier call 480s, handoff call 120s, validate 5s, SessionStart 10s, UserPromptSubmit 40s and contract 30s. Role 4 owns HARNESS_VERIFY_BUDGET_SECONDS=450; this role does not edit verifier code.
- Reserve four seconds per hook for TERM grace (up to two seconds), bounded parent reap (0.5s), final drain (0.25s) and overhead: child calls are capped by the remaining cumulative budget. SIGTERM/SIGHUP/SIGINT unwind owned groups; repeated signals are ignored during cleanup, and spawn-time signals are deferred until registration. Normal completion also cleans leftover group members.
- Document the contract path as the approved caller/callee deadline exception: controller per-call timeout is now 35s (0d57e36), but the plugin cuts contract generation off at 30s, preventing fallback triggered by that controller deadline. Do not alter controller-owned deadlines.
- Keep outer hook values in hooks.json and Runtime consistent, with a direct regression assertion: installation/demo serialize integers and pin the same runtime budget. Overrides use integer seconds bounded at 86400, minimum 5 for outer hooks and 1 for child calls; reject invalid settings before target writes.
- Opt projects in with a .local-harness-maker file and resolve cwd ancestors canonically before timing/runtime/state/logging: children inherit opt-in while siblings and symlink escapes do not. Preserve the exact HARNESS_NESTED=1 guard before all imports except os; disable bytecode writes in hook entry points as well.
- Generate a handoff after pass or retry exhaustion; publish only after CLI and schema validation: on failure rename old context to handoff.stale.UUID.json so SessionStart cannot inject it as current. Exhaustion still shows unmet criteria even when handoff fails. Preserve all archived files.
- Make installation a fully preflighted, repairable operation on explicit targets: update managed snapshots/skill/hooks, preserve unrelated registrations and instructions, and atomically replace individual files. Rerunning repairs an interrupted install; no cross-file transaction or deletion is claimed.
- Persist installed outer timeouts in install.json and compare event/script registrations semantically: --check ignores install-time override absence and checking interpreter identity, but rejects JSON timeout type/value or embedded-runtime-budget mismatch. Resolve the executable through HARNESS_CODEX, PATH, then the ChatGPT macOS bundle, with a bounded probe and distinct missing-CLI diagnostic.
- Archive malformed session metadata and reset rather than disabling the plugin: state and session JSON files are each published with temporary-file/replace atomicity. Required shared state fields and CLI/hook interfaces remain unchanged.
- Require observed pre-approval task inventories to be empty in real demo evidence: save before request, after request and immediately before submitting approval; exclude managed harness metadata and marker, but include unexpected task entries inside .harness. Snapshots do not establish absence of transient writes later removed.
- Preserve approval gating, same-session resume/hash checks and the Codex version pin: no new model call, version upgrade, interface change, normal-home installation or deletion is authorized here. Direct-user demo executors leave HARNESS_NESTED unset so hooks run; their children set it in copied environments.

- Detect leader exit independently of pipe EOF with 50ms communicate slices and poll, then drain only after group shutdown with a 250ms bound: inherited descriptors cannot defer cleanup to the CLI deadline. Preserve buffered stdin/output across slices and return the leader's actual exit status. Timeout and catchable-signal shutdown keep the existing TERM/grace/KILL protocol.

### Verify commands

- .venv/bin/python -m pytest tests/plugin -q
- bash -n plugin/install.sh plugin/demo.sh
- git diff --check -- plugin tests/plugin state/STATUS-plugin.md
- .venv/bin/python -m plugin.v3_demo --help
- .venv/bin/python -m plugin.host_checks --help
- .venv/bin/python -m plugin.pin_check --help

- .venv/bin/python -m pytest tests/plugin -q (latest: 272 passed, 1 opt-in live Codex test skipped in 18.57s).
- Host only: .venv/bin/python -m plugin.host_checks prepare --scenario trust --out /tmp/lhm-trust-DATE; follow plugin/HOST-CHECKS.md for the recorded interactive session and second/check commands. Repeat separately for silence; bundle needs prepare/check only. No procedure was run in this session.
- Offline after host capture: .venv/bin/python -m plugin.host_checks check --out /tmp/lhm-trust-DATE (repeat for bundle/silence and copied review directories).

- Host only, one scenario/stage at a time: .venv/bin/python -m plugin.handoff_failure_demo day1 --scenario exhaustion --out /tmp/lhm-DATE-exhaustion --scripted-approval
- Host only: .venv/bin/python -m plugin.handoff_failure_demo day2 --scenario exhaustion --out /tmp/lhm-DATE-exhaustion
- Offline: .venv/bin/python -m plugin.handoff_failure_demo check --scenario exhaustion --out /tmp/lhm-DATE-exhaustion (repeat with generation/validation and distinct directories).
- Future captures: .venv/bin/python -m plugin.export_demo_evidence --source /tmp/lhm-DATE-exhaustion --out plugin/evidence/DATE-exhaustion; then rerun the matching offline checker.

- Host only: .venv/bin/python -m plugin.two_session_demo day1 --out plugin/evidence/DATE-two-session
- Host only: .venv/bin/python -m plugin.two_session_demo day2 --out plugin/evidence/DATE-two-session
- Offline after host capture: .venv/bin/python -m plugin.two_session_demo check --out plugin/evidence/DATE-two-session
- .venv/bin/python -m plugin.check_probe_evidence --expected-version "codex-cli 0.163.0-alpha.11.1" plugin/evidence/2026-10-22-exec-0.163

- .venv/bin/python -m pytest tests/plugin -q (latest: 252 passed, 1 skipped in 16.36s)

- .venv/bin/python -m pytest tests/plugin -q
- bash -n plugin/install.sh plugin/demo.sh
- git diff --check -- plugin tests/plugin state/STATUS-plugin.md
- Host only: follow plugin/README.md temporary HOME/CODEX_HOME installation and --check commands; the installer invokes the pinned Codex version command.
- Host only: bash plugin/demo.sh --real --out plugin/evidence/DATE-real --scripted-approval
- After host capture: .venv/bin/python -m plugin.check_demo_evidence plugin/evidence/DATE-real
- Optional host stub reproduction: HARNESS_STUB=1 bash plugin/demo.sh --out plugin/evidence/NEW-stub --scripted-approval

### Do not touch

- controller/, verifier/, eval/, schemas/, prompts/, shared root files, docs/hooks-contract.md and other roles' STATUS files; user-authorized paths in this worktree are plugin/, tests/plugin/ and state/STATUS-plugin.md only.
- .git is read-only: do not stage or commit. Preserve all historical evidence and demos, exact HARNESS_NESTED=1 zero-byte guards and copied child environments. Never run the live host scripts in this sandbox.

- This session: .git is read-only; do not stage or commit. Host evaluations are in progress; leave eval/, controller/ and verifier/ untouched.

- Other roles' code, tests, STATUS files, root configuration, schemas or CLI/hook interfaces; the canonical docs/hooks-contract.md is published and read-only for Role 2.
- Existing user changes and concurrent role commits/staging. Stage and commit only plugin/, tests/plugin/, state/STATUS-plugin.md with explicit pathspecs.
- Normal Codex configuration and installed hooks. Use explicit temporary HOME/CODEX_HOME targets; the demo trust bypass is not proof of persisted trust.
- Recorded evidence directories: use a new directory for another experiment; approval cannot be retried over existing evidence. Do not delete temporary workspaces, login symlinks or repository files under STOP-4.
- Never infer real task success, control-model latency, actual cost, fork/clear behavior, real handoff success or installed packaging from synthetic fixture verdicts.

### Assumptions

- The user's 2026-10-25 schema freeze/CLI instructions are the current authority; no separate approval or shared interface edit is needed in this session.
- Explicit question-ID/answer JSON is a local recording convention with no new hook wire field. Unstructured answers remain pending rather than being guessed.
- verifier.ledger.ledger_request is a provisional private formatter seam only; its final name/signature is not asserted to exist in this historical checkout. Roles 3/4 integration and real host execution remain pending.
- A read-only strings inspection found model/list, ModelListParams, clientInfo and nextCursor in the installed binary, supporting the non-generating app-server probe choice; it does not prove runtime protocol compatibility. Unsupported or incomplete responses disable Luna.

- Claude's 3ef1e84 live demonstration results and 1550267 Ubuntu/Python 3.11/3.14 CI completion are user-supplied evidence; only retained demo checkers and offline plugin tests ran here.
- New trust/silence procedures assume macOS /usr/bin/script and normal interactive acceptance of isolated hook trust. Their two executor sessions use stub control calls, not real task execution. Bundle discovery runs the actual installer with empty PATH/no HARNESS_CODEX; no new live host result is claimed.
- The version probe observes the executable currently selected by HARNESS_CODEX/PATH/the app bundle, not the old in-memory image after replacement. Nonstandard launches must set HARNESS_CODEX to their executable. No subprocess version probe in the tests uses the real Codex binary.

- No additional product assumptions were required for the user-specified portability fix. Identity Path.resolve tests simulate the missing macOS aliases on Linux; Ubuntu/Python 3.11 and 3.14 CI completion was subsequently supplied by the user (1550267). No live models, Codex, network, real configuration changes, staging or commits ran in this session.

- Claude's supplied host run/commit account is accepted as host evidence and corroborated by the retained offline checker; this session performed no live Codex/model calls, installation, network access, staging or commit.
- The failure demonstrations deliberately inject CLI errors, rather than asserting a naturally occurring provider/validation failure. Their seed is synthetic old context; their lifecycle, controller generation where not intercepted, verification and executor sessions are real host operations subsequently completed by Claude (3ef1e84).
- Day 2 only needs to reach approval to demonstrate handoff receipt or stale-context absence. It is not a claim that remaining work was completed. Future evidence is committed only after portable export/review; raw operational capture remains host-local.

- The user's supplied host results and commits are accepted as host evidence; only the probe/demo evidence audits and plugin tests were rerun here. No live Codex, model, network, sandbox-exec or real-home installation ran.
- The requested two-session preparation covers the pass path. Exhaustion, stale-context rejection and persisted trust retain separate host checks; the demo proves receipt and success without user restatement, not exclusive causal reliance on the handoff.

- This job's explicit changing-version instructions supersede the role prompt pin and STOP-P2 text. No shared schema, production CLI or hook interface changes are needed.
- The observed 0.163.0-alpha.11.1 update is user-supplied information; this session never invoked Codex, live models, sandbox-exec or the real-home installer. Passing host probe evidence was supplied by the user and re-audited offline in this session.
- No PR, stage or commit was performed. Copy these assumptions and the README change summary into any future PR; the final report supplies an exact unstaged commit plan.

- The latest STOP-P3 decision changes the prototype's synchronous deadline and logging only; no fresh paid benchmark, asynchronous implementation, shared interface edit or model substitution is requested. Tests simulate elapsed time without waiting or calling a model.
- The latest instruction authorizes D-2 executor demonstrations and a scripted demo user after the summary is shown. Normal user sessions require actual approve/edit input; scripted approval is never injected by the production hooks.
- Temporary CODEX_HOME registration satisfies isolated hook testing, not normal installation or persisted trust. The existing CLI login is referenced outside the repository without reading/copying credential content or changing persistent configuration.
- The assigned executor is gpt-6.1-sol at low effort for fixture demonstrations. Controller model/effort selection remains controller-owned; real control API calls did not run, and no batch of ten paid calls was launched.
- The immutable shared FastAPI examples are synthetic test fixtures. Their zero cost estimates are not measured usage; the empty demo workspace intentionally meets the unavailable-app stop condition and proves routing only.
- A new session_id resets attempts/phase; the same session_id on resume/compact preserves them. Nullable transcript paths fail open before verifier invocation rather than fabricating a transcript.
- Skill validation required temporary PyYAML tooling because the repository and bundled interpreters lacked yaml. No shared dependencies or root configuration were changed.
- No PR was requested or created. Assumptions are recorded here and in plugin/README.md for a future PR description; full-suite and merge checks remain pending.

- The latest review decision authorizes these revised plugin deadlines; controller per-call deadline 35s is user-reported from commit 0d57e36 and remains read-only for this role.
- Fresh-clone installation assumes Python 3.11+, repository dependencies installed into a retained Python environment, and the pinned host Codex executable. Network/package installation was not attempted here.
- No PR was requested or created. The future PR should copy the Assumptions in plugin/README.md and this STATUS; the final report supplies only an unstaged commit plan.

- The marker filename, one-day timeout ceiling and minimum outer deadline of five seconds are plugin implementation choices: they make project opt-in explicit and reserve cleanup capacity. All are documented in plugin/README.md.
- SIGKILL is outside the catchable shutdown protocol; guaranteeing cleanup for that case would require an external supervisor. No claim of SIGKILL-owner cleanup is made.
- The user reports Claude host-verified the previous 79-passed/1-skipped job but did not commit it. That evidence applies to the prior implementation, not this revised protocol; current new behavior has offline tests only.

- The user reports host verification of the previous 131-passed/1-skipped revision and successful SIGTERM/SIGHUP/unmarked-directory checks. Those host claims are supplied evidence, not commands run here; only the new direct process-tree regression and plugin suite were executed in this turn.
- The sandbox forbids ps. The regression therefore checks PID liveness directly and, on Linux, treats an orphan zombie as exited pending init reaping. It requires no live descendant; collection of orphan exit records belongs to init/launchd.

- This session assumes host ps enumeration is available for the macOS fallback. The workspace sandbox denies ps; transient/persistent EPERM/ESRCH member enumeration is injected in unit tests, while actual trees verify no live grandchildren via PID probes. Claude's repeated macOS process-tree checks were subsequently completed on the host, as recorded above.

## 2026-10-25 status-format-migration Role 2

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
