## Done

- Created the unfrozen hand-written `bug-chunk-tail` task with prompt, initial workspace, metadata, expected conditions and exactly three private unittest cases; the fixture validation rejects the buggy code with 3 failures and accepts a correction with 3 passes (.venv/bin/python -m pytest tests/eval -q: 2 passed in 0.32s).
- Recorded installed Codex version and CLI options without a model call (codex --version: codex-cli 0.162.0-alpha.17.2; codex exec --help: --sandbox, --json, --output-last-message, --config and resume available).
- Reproduced a private-grader read from outside the active workspace under the diagnostic CLI's built-in :workspace profile and stopped under STOP-E4; this is not direct exec evidence (.venv/bin/python eval/runner/check_isolation.py: exit 1; sandbox child exit 0; HIDDEN_GRADER_READABLE; log in eval/reports/preflight-2026-10-21/isolation.log).
- Wrote the change summary and escalation with candidate isolation fixes; no model evaluation or runtime reasoning-effort claim is complete (.venv/bin/python -c 'from pathlib import Path; paths = ["eval/reports/preflight-2026-10-21/README.md", "docs/decisions/0001-eval-isolation-proposal.md"]; assert all(Path(p).is_file() for p in paths); print("2 report files present")': 2 report files present).

## Remaining

- Resolve STOP-E4 using docs/decisions/0001-eval-isolation-proposal.md. Prove the exact executor environment cannot read private graders or grading copies through any enabled tool, including after resume, before invoking a model.
- Complete First task: run the fixture in baseline A with gpt-6.1-sol at medium, confirm applied reasoning effort from JSON events, grade in a separate copy and retain the result and logs. No paid calls have been made in this session.
- Complete D-1 runner: configuration YAML, independent task loop, schema-validated result JSON, timeout, retry, failure isolation, interruption checkpoints and session resume; implement pass_rate. Coordinate the missing shared evaluation report schema with Role 1 before requiring an interface change.
- Read Role 2's installed-version hook evidence when available; state/STATUS-plugin.md was empty and docs/hooks-contract.md absent at this session's inspection. Do not rely on hooks for runner correctness.
- Prepare the 10-task A/B pilot, report its cost estimate and obtain approval before full runs. Respect STOP-3 for any batch of 10 or more paid calls.
- Continue scheduled D-2 through D-5: expand and freeze 100 tasks plus 20 two-session tasks, provide the hash to Role 1, manually re-check five baseline A results, then run approved baselines and systems and report the defined metrics with confidence intervals. No freeze or full-run authorization is claimed.

## Decisions

- Start from First task: the role STATUS had no Remaining items or Done evidence.
- Halt before paid execution under STOP-E4: the built-in workspace diagnostic sandbox successfully opened the private grader outside the workspace.
- Keep runtime claims narrow: the diagnostic helper requires a named permission profile, so :workspace evidence does not verify exec --sandbox workspace-write or applied reasoning effort.
- Keep private checks in trusted grading copies: the initial task workspace contains only public source and no grading tests.
- Keep all generated task artifacts provisional: no task-set freeze has occurred and shared interfaces remain unchanged.
- Use an escalation proposal in docs/decisions/: AGENTS.md explicitly permits that path when a role must stop and propose a cross-role change.

## Verify commands

- .venv/bin/python -m pytest tests/eval -q
- codex --version
- .venv/bin/python eval/runner/check_isolation.py (expected exit 1 reproduces STOP-E4; do not treat this as a passing isolation check)
- cat eval/reports/preflight-2026-10-21/isolation.log
- git diff --check

## Do not touch

- controller/, controller/case_library/, verifier/, plugin/, other role tests and other role STATUS files.
- Shared schemas, CLIs and hook interfaces; only Role 1 may change them after a decision record and version increment.
- Unrelated existing user edits, legacy harness/, experiments/ and root configuration.
- Do not expose task-set contents to Role 3, launch paid evaluation before resolving STOP-E4, or mark diagnostic results as model measurements.
- Do not delete files, rewrite Git history or change external service configuration without STOP-4 escalation.

## Assumptions

- The user instruction to execute Role 5 invokes First task because the initial STATUS was empty; it does not authorize a future full experiment.
- The initial hand-written fixture uses Python and standard-library unittest grading; its expected.json and meta.json are provisional task artifacts, not changes to shared schemas.
- A demonstrated private-grader read under the built-in workspace diagnostic sandbox warrants STOP-E4 before a paid run; no model access or direct exec leakage was observed.
- Hidden tests must be inaccessible to the executor, not merely omitted from its prompt or copied outside its current directory.
- No unspecified spending limit, model price, hook behavior, reasoning-effort application, task-set hash or evaluation result was inferred.
