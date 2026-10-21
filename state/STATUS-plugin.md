## Done

- Pinned the installed executor at codex-cli 0.162.0-alpha.17.2 in plugin/CODEX_VERSION (codex --version: codex-cli 0.162.0-alpha.17.2).
- Added isolated hook registration and a bounded, fail-open capture probe for the First task; version calls are injectable for tests and normal user configuration is untouched (.venv/bin/python -m pytest tests/plugin -q: 10 passed in 0.42s).
- Captured all three real hooks under codex exec, both developer-context markers, one Stop continuation, and a second Stop with stop_hook_active=true; exit 0, two assistant messages (.venv/bin/python -m plugin.check_probe_evidence plugin/evidence/2026-10-21-exec: context_visible=true, continued_once=true, events=[SessionStart, UserPromptSubmit, Stop, Stop], exit_code=0).
- Repeated the experiment in the interactive CLI with a terminal recording; exit 0 after /quit, two assistant messages (.venv/bin/python -m plugin.check_probe_evidence plugin/evidence/2026-10-21-tui: context_visible=true, continued_once=true, events=[SessionStart, UserPromptSubmit, Stop, Stop], exit_code=0).
- Prepared plugin/hooks-contract.draft.md with complete captured inputs/outputs, evidence links, official documentation, and limitations; wrote plugin/README.md as the change summary (relative-link and whitespace audit: Draft and README relative links: OK; Plugin source, documentation and JSON whitespace: OK).
- Checked the tracked diff for whitespace errors; full-suite and merge checks were not run in this role session (git diff --check: exit 0).

## Remaining

- Resolve STOP-2: Role 1 must review docs/decisions/2026-10-21-plugin-hooks-contract-proposal.md and promote plugin/hooks-contract.draft.md to docs/hooks-contract.md, fixing relative evidence links. D-1 is not complete until the canonical document is published. No interface change is requested.
- D-2: implement the thin production hooks with HARNESS_STUB=1, immutable schema-example stubs, executor approval skill, and plugin/demo.sh. The marker experiment is not a generated contract or a passing stub-loop demo. Add SC-1 tests with mocked controller/verifier CLIs and the SC-2 integration test that launches codex exec once.
- D-3: connect the real controller/verifier CLIs, session state with the required five fields, default configurable limit N=3, and visible unmet-item reporting when the limit is reached. Confirm where handoff generation runs before the session ends.
- D-4: implement handoff validation/injection, install.sh including distinct --check diagnostics, templates, packaging, and production fail-open/timing checks. Review persisted hook trust instead of using the experiment bypass in installation.
- D-5: produce the recording scenario and screen-order document; keep stub and real demo logs. bash plugin/install.sh --check and bash plugin/demo.sh in both modes remain unrun because those scripts do not exist yet.
- Before merge: run the full suite once. Production SC-1 through SC-6 are not claimed complete by the experiment-only tests.

## Decisions

- Start with the role's First task: this STATUS file had empty Done and Remaining sections at session start.
- Keep the tested Codex pin: both interfaces worked on the installed version, so no upgrade or alternative continuation design is required.
- Use hooks.json in a temporary Codex home and a temporary workspace: exercise real loading without registering hooks in the user's regular configuration.
- Use the official Stop fields decision=block and reason: both runs delivered the reason as a user hook_prompt and continued within the same turn; UserPromptSubmit did not fire again for automatic continuation.
- Keep the canonical docs/hooks-contract.md absent pending Role 1 review: AGENTS.md section 2 restricts Role 2 to owned paths and requires a proposal plus stop for another role's path; the role prompt says Role 1 merges that document.
- Keep experiment results separate from production claims: startup and bounded marker continuation are proven, while approval, contract generation, retry exhaustion, handoff, installed packaging, and control-call latency are not.

## Verify commands

- codex --version
- .venv/bin/python -m pytest tests/plugin -q
- .venv/bin/python -m plugin.check_probe_evidence plugin/evidence/2026-10-21-exec plugin/evidence/2026-10-21-tui
- git diff --check
- For a new paid experiment, prepare a fresh evidence directory with .venv/bin/python -m plugin.probe --mode exec --out plugin/evidence/NEW-exec or --mode tui --out plugin/evidence/NEW-tui, then review and run the printed command. Preparation alone does not run the model.

## Do not touch

- Other roles' code, tests, STATUS files, root configuration, schemas, or CLI/hook interfaces. docs/hooks-contract.md requires Role 1 publication; only the required proposal is written under docs/decisions/.
- Existing user changes and concurrent role commits. A lead commit appeared during this session and included some in-progress probe files; it was not rewritten or amended.
- Normal Codex configuration and installed hooks. The experiment trust bypass is not an installer design.
- Recorded evidence directories: use a new directory for another experiment. Do not delete temporary workspaces, credentials symlinks, or repository files under STOP-4.
- Never claim nullable transcript-path handling, resume/compact/fork behavior, production timing below one second, or controller latency from these startup-only measurements.

## Assumptions

- The First task authorizes two isolated executor experiments, each with one bounded continuation, using the existing local login. No controller API calls or batch of ten paid calls ran.
- Temporary CODEX_HOME registration satisfies the requested compatibility experiment; it does not establish normal plugin installation or persisted hook trust.
- The assigned executor is gpt-6.1-sol. Low effort was selected only for marker replies; controller effort computation remains outside this role.
- The role's instruction that Role 1 merges the hook contract is implemented as a draft in plugin/ plus the mandatory docs/decisions/ proposal; no ownership override is assumed.
- Both inputs reported permission_mode=bypassPermissions despite the temporary config requesting read-only sandboxing and never approval; no sandbox-enforcement claim is made. No tools were requested or observed in the model replies.
- No PR was requested or created; Assumptions are recorded here and in the plugin documentation for a future PR description.
