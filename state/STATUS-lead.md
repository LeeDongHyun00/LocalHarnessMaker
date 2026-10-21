## Done

- Verified the selected 19-file commit scope in a separate HEAD archive overlaid only with those files, excluding concurrent uncommitted role work (make validate-schemas with the workspace .venv Python in the isolated archive: 6 schemas and 8 examples validated; make test in that archive: 168 passed in 4.97s).
- Recorded "Status: approved by the user on 2026-10-21" in decisions 0002, 0003 and 0004; published their exact JSON schema/example content and set schemas/VERSION to 1 (make validate-schemas PYTHON=.venv/bin/python: Validated 6 draft 2020-12 schemas and 8 examples; make test PYTHON=.venv/bin/python: approved-record equality tests passed).
- Added judgment-input.schema.json, judgment.schema.json and evaluation-report.schema.json plus criterion.json, judgment.json and evaluation_report.json; retained existing contract/verdict/handoff shapes (make validate-schemas PYTHON=.venv/bin/python: 6 schemas and 8 examples validated).
- Extended local-only schema reference validation, required artifact inventory and deterministic timestamp-format checks without new dependencies; boundary tests reject missing schemas/examples, malformed criteria/reports, wrong metric intervals/units, invalid audit states, missing handoff evidence and unknown references (make test PYTHON=.venv/bin/python: 264 passed, 2 skipped; skips require external graders).
- Updated docs/interfaces.md, AGENTS.md section 3, and the two explicitly authorized controller/evaluation role prompts for the approved model order, shared three-call budget, nested guard, judgment/report contracts, access audit and API-equivalent accounting (make test PYTHON=.venv/bin/python: interface/prompt consistency tests passed).
- Published the approved installed-version hook contract with corrected evidence links; kept probe evidence and other roles' implementations unchanged (published evidence-link test passed; .venv/bin/python -m plugin.check_probe_evidence plugin/evidence/2026-10-21-exec plugin/evidence/2026-10-21-tui: both runs context_visible=true, continued_once=true, exit_code=0).

## Remaining

- Owning roles must implement and demonstrate version 1 runtime behavior: controller judge/handoff and shared-budget routing, all-hook HARNESS_NESTED bypass, verifier judgment delegation, and schema-valid evaluation report production. Shared contract publication is complete; runtime completion is not claimed.
- Review production handoff-save point, nullable transcript handling, other SessionStart sources, persisted trust and retry/approval behavior with Role 2. Startup probe evidence does not establish these remaining behaviors.
- D-3, by 2026-10-27: read the Notion design/plan, write docs/plan.md and the direction-change decision, and record the task-set hash supplied by Role 5 in docs/eval-freeze.md. No hash was supplied in this task.
- D-4: read the four engineer STATUS files and write integration reviews on 2026-10-27, 2026-11-03 and 2026-11-10; monitor interface blockers for the two-day limit.
- D-5, by 2026-11-13: update README.md for verified installation/demo, write docs/architecture.md and docs/demo.md, and verify the two-session demo in a fresh clone with retained evidence.
- D-6, by 2026-11-15: write docs/slides/ and docs/qa.md with all four required questions.
- External private-grader fixture tests require the trusted grader configuration; two tests were skipped in the current local role-suite run. Legacy top-level Docker/Chromium suites and remote CI were not run by this interface task.

## Decisions

- Treat FILE1/FILE2/FILE3 as decisions 0002/0003/0004: those are the three proposals immediately preceding the user's explicit approval and implementation request.
- Publish version 1 on 2026-10-21: the user approved the bundle and explicitly requested VERSION=1 before the planned 2026-10-24 freeze.
- Preserve approved schema/example content exactly: active artifacts match the JSON blocks in the approved records; existing contract/verdict/handoff shapes remain unchanged.
- Use gpt-6-luna via logged-in codex_cli as primary, same-model cheap_api fallback and local Gemma as stage two: the user's approved model/transport order.
- Use audited external private graders in fresh post-exit copies and invalidate observed access/inconclusive capture: the user's STOP-E4 decision replaces the earlier deny-read prerequisite without claiming filesystem isolation.
- Update only the two named role prompts outside normal lead ownership: the user explicitly authorized those paths; controller/plugin/verifier/eval implementations and other STATUS files remain untouched.
- Stage an explicit allowlist only, never git add -A: the user requires a scoped commit/push, and other roles have concurrent uncommitted changes.

## Verify commands

- make validate-schemas PYTHON=.venv/bin/python
- make test PYTHON=.venv/bin/python
- .venv/bin/python -m plugin.check_probe_evidence plugin/evidence/2026-10-21-exec plugin/evidence/2026-10-21-tui
- git diff --check -- AGENTS.md docs/interfaces.md docs/validate_schemas.py prompts/03-controller-engineer.md prompts/05-eval-engineer.md schemas tests/lead state/STATUS-lead.md
- git show --stat HEAD
- git ls-remote --heads origin main

## Do not touch

- Version 1 interfaces without new user approval, a decision record and a version increment.
- Other roles' implementation files/tests/STATUS, including concurrent controller, verifier, plugin and eval work. Only prompts/03-controller-engineer.md and prompts/05-eval-engineer.md are explicit cross-role exceptions for this task.
- Existing harness/, experiments/, scripts/, legacy tests and unrelated user edits.
- No git add -A, broad staging, foreign-path commit, deletion, history rewrite, hook registration or external configuration change.
- Keep the canonical hook contract and captured evidence; never replace measured evidence with a placeholder or claim production behavior from startup probes.

## Assumptions

- The approval placeholders identify the immediately preceding three proposals and DATE is 2026-10-21 in the user's timezone.
- A separate published judgment-input schema is the approved input validator, referencing the existing contract item rather than duplicating/changing it.
- This task publishes shared contracts, examples/tests and instructions; implementation changes in other roles' runtime packages remain their responsibility.
- Synthetic prices, paths, hashes, usage and CIs remain fixtures. No paid model call, real pricing/account eligibility result or runtime-backend completion is inferred.
- Version 1 validation needs deterministic timestamp checks even when optional jsonschema date-time dependencies are absent; the local validator enforces timestamp syntax/calendar validity without changing dependencies or approved schemas.
- Commit and push are explicitly authorized; only the named shared changes, lead tests/STATUS, the necessary shared validator and previously approved canonical hook document are included. Concurrent role work and the older untracked proposal-session change summary remain outside the commit.
