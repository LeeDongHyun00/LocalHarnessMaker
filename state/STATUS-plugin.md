## Done

- Pinned the installed executor at codex-cli 0.162.0-alpha.17.2 in plugin/CODEX_VERSION (codex --version: codex-cli 0.162.0-alpha.17.2).
- Completed D-1 startup evidence for both interactive CLI and codex exec; Role 1 published the canonical document, resolving the earlier STOP-2 (.venv/bin/python -m plugin.check_probe_evidence plugin/evidence/2026-10-21-exec plugin/evidence/2026-10-21-tui: context_visible=true, continued_once=true, exit_code=0 for both; cat docs/hooks-contract.md: published by Role 1 on 2026-10-21 with user approval).
- Added the exact HARNESS_NESTED=1 silent fast path to the three lifecycle hooks and the original probe. Tests leave stdin open, poison imports/I/O/subprocesses, exercise stub precedence and unset/empty/0/true/01 normal behavior, and require exit 0 with zero bytes on both streams (.venv/bin/python -m pytest tests/plugin -q: 70 passed, 1 opt-in live test skipped in 4.93s).
- Implemented thin CLI delegation, unchanged schema-example stubs, approval/edit routing, reviewed-contract hashing, same-session resume state, bounded Stop continuation, fail-open handling and timing; each lifecycle hook has stdin/stdout tests with mocked CLIs (.venv/bin/python -m pytest tests/plugin -q: 70 passed, 1 skipped in 4.93s).
- Passed SC-2 with one initial Codex process: full fixture contract appears as developer context and the session waits for approval without verifier calls (HARNESS_STUB=1 HARNESS_CODEX_LIVE=1 HARNESS_CODEX_EVIDENCE=plugin/evidence/2026-10-21-d2 .venv/bin/python -m pytest tests/plugin/test_codex_integration.py -q: 1 passed in 17.98s; request-summary.json: contract_visible=true, approval_pending=true, verifier_calls=0).
- Completed D-2 in a fresh routing-only stub demo, with the summary displayed before scripted demo approval, exactly one re-instruction, two verifier calls and synthetic pass; all source and transcript logs are retained (HARNESS_STUB=1 bash plugin/demo.sh --out plugin/evidence/2026-10-21-d2-pass --scripted-approval: exit 0; .venv/bin/python -m plugin.check_demo_evidence plugin/evidence/2026-10-21-d2-pass: approval_gate=true, reinstructions=1, attempts=2, overall=pass, synthetic=true, real_task_verified=false, max_hook_overhead_seconds=0.192873).
- Added the executor skill and updated plugin/README.md with reproduction commands, limitations, change summary and assumptions; validated using isolated PyYAML tooling without changing repository dependencies (skill-creator/scripts/quick_validate.py plugin/skills/harness with temporary PYTHONPATH: Skill is valid!; README link audit: OK; bash -n plugin/demo.sh: exit 0).
- Applied the user's STOP-P3 prototype decision: synchronous controller contract calls now allow thirty seconds, UserPromptSubmit has a forty-second outer deadline, and each contract call logs latency on stderr including timeouts. Mocked ten/thirty-second successes and timeout handling preserve the approval gate and silent nested bypass (.venv/bin/python -m pytest tests/plugin -q: 73 passed, 1 opt-in live test skipped in 5.56s; git diff --check -- plugin tests/plugin state/STATUS-plugin.md: exit 0).

## Remaining

- D-3: live-verify the real controller/verifier routes (default HARNESS_BACKEND=codex_cli), which currently delegate without an automatic stub fallback. The state fields, configurable default limit N=3 and unmet-item warning are implemented and mocked-tested; full-contract latency and real outcome verification remain unproven. Apply the user's accepted thirty-second synchronous limit and retain latency logs; do not build an asynchronous design now.
- D-3/D-4: implement handoff generation before session completion using the controller CLI. Existing-handoff validation/injection is implemented and mocked-tested; no real handoff save/injection or two-session handoff demo has run.
- D-4: implement install.sh and its three distinct --check diagnostics, project template, packaging, persisted trust review, and installed-environment checks. The current hooks reference this repository's schemas, packages and skill; portable installation is not complete. SC-6 remains pending.
- D-5: produce the recording scenario and screen-order document. Preserve stub and real demo logs; current demo.sh deliberately supports stub mode only. bash plugin/install.sh --check and a real-mode demo remain unrun.
- Before merge: run the full suite once. SC-1/SC-2 have evidence; SC-3/SC-4 are unit-tested, SC-5 is measured only in the stub environment, and SC-6 remains pending.

## Decisions

- Accept synchronous control-model calls up to thirty seconds for the prototype, per the user's 2026-10-21 STOP-P3 decision: the call runs once per request before approval. This supersedes the role prompt's five-second threshold and asynchronous/cached-design escalation. Keep the subprocess deadline at thirty seconds, the UserPromptSubmit outer deadline at forty seconds, and latency_seconds plus aggregate cli_seconds logs.
- Record the user's approximately ten-second one-line gpt-6-luna codex exec measurement as user-reported: it motivates the accepted prototype latency but is not a full-contract benchmark or a measurement performed in this session.
- Keep the tested Codex pin: both interfaces worked on the installed version, so no upgrade or alternative continuation design is required.
- Put the nested comparison immediately after importing os in every hook entry point: nested calls must not import runtime helpers, read stdin, access state/config, spawn children or log anything, including timing.
- Keep _stub.py a CLI adapter rather than a lifecycle hook: its caller's child environment intentionally includes HARNESS_NESTED=1; the adapter still copies fixtures unchanged and makes no model calls.
- Use hooks.json in temporary Codex homes/workspaces for the demo: normal configuration and persisted hook trust are not changed.
- Preserve same-session approval state on resume/compact and reset it for a new session_id: codex exec resume must accept the already displayed contract without regenerating it or losing its approval gate. The required five-field state interface stays unchanged; phase/hash/session_id live in a private sidecar.
- Allow Stop only after explicit approval and preserve the verdict's exact re-instruction: the measured Stop continuation does not emit UserPromptSubmit, and a null re-instruction must never block completion.
- Keep the first failed D-2 run under plugin/evidence/2026-10-21-d2: the approval process timed out at 180 seconds after assistant commentary with no later tool/Stop event; partial logs, transcript and state are retained, and the root cause is not established.
- Make the successful fixture demo explicitly routing-only with no application or tools: actual task work is not needed to test the fixed synthetic contract/verdict adapters. All real criteria remain not done. User approval is scripted only with the explicit demo flag.
- Commit with explicit role-owned pathspecs only: use plugin/, tests/plugin/, state/STATUS-plugin.md; never git add -A or stage other roles' work.

## Verify commands

- codex --version
- .venv/bin/python -m pytest tests/plugin -q
- .venv/bin/python -m plugin.check_demo_evidence plugin/evidence/2026-10-21-d2-pass
- .venv/bin/python -m plugin.check_probe_evidence plugin/evidence/2026-10-21-exec plugin/evidence/2026-10-21-tui
- bash -n plugin/demo.sh
- git diff --check -- plugin tests/plugin state/STATUS-plugin.md
- Optional paid reproduction: HARNESS_STUB=1 bash plugin/demo.sh --out plugin/evidence/NEW-demo --scripted-approval. Omit --scripted-approval for typed user approval. New output directories only.
- Optional one-process live test: HARNESS_CODEX_LIVE=1 .venv/bin/python -m pytest tests/plugin/test_codex_integration.py -q. It stops at pending approval and makes no control-model call.

## Do not touch

- Other roles' code, tests, STATUS files, root configuration, schemas or CLI/hook interfaces; the canonical docs/hooks-contract.md is published and read-only for Role 2.
- Existing user changes and concurrent role commits/staging. Stage and commit only plugin/, tests/plugin/, state/STATUS-plugin.md with explicit pathspecs.
- Normal Codex configuration and installed hooks. The experiment trust bypass is not an installer design.
- Recorded evidence directories: use a new directory for another experiment; approval cannot be retried over existing evidence. Do not delete temporary workspaces, login symlinks or repository files under STOP-4.
- Never infer real task success, control-model latency, actual cost, fork/clear behavior, real handoff success or installed packaging from synthetic fixture verdicts.

## Assumptions

- The latest STOP-P3 decision changes the prototype's synchronous deadline and logging only; no fresh paid benchmark, asynchronous implementation, shared interface edit or model substitution is requested. Tests simulate elapsed time without waiting or calling a model.
- The latest instruction authorizes D-2 executor demonstrations and a scripted demo user after the summary is shown. Normal user sessions require actual approve/edit input; scripted approval is never injected by the production hooks.
- Temporary CODEX_HOME registration satisfies isolated hook testing, not normal installation or persisted trust. The existing CLI login is referenced outside the repository without reading/copying credential content or changing persistent configuration.
- The assigned executor is gpt-6.1-sol at low effort for fixture demonstrations. Controller model/effort selection remains controller-owned; real control API calls did not run, and no batch of ten paid calls was launched.
- The immutable shared FastAPI examples are synthetic test fixtures. Their zero cost estimates are not measured usage; the empty demo workspace intentionally meets the unavailable-app stop condition and proves routing only.
- A new session_id resets attempts/phase; the same session_id on resume/compact preserves them. Nullable transcript paths fail open before verifier invocation rather than fabricating a transcript.
- Skill validation required temporary PyYAML tooling because the repository and bundled interpreters lacked yaml. No shared dependencies or root configuration were changed.
- No PR was requested or created. Assumptions are recorded here and in plugin/README.md for a future PR description; full-suite and merge checks remain pending.
