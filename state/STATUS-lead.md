## Done

- Completed D-3 by recording the 2026-10-22 version 1 evaluation freeze at 7cdaf3b in docs/eval-freeze.md: all 120 task IDs, per-task counts, supplied digest and attributed Claude host validation/mutation evidence, immutable-version rule and family-cluster reporting decision; replaced only the plan source citation with the Notion page (inline public freeze inventory checks: 120 frozen version-1 tasks, 120 matching validation rows and expected test counts; `.venv/bin/python -m pytest tests/lead -q`: 96 passed in 19.81s).

- Fixed duplicate-basename collection with importlib mode while retaining all five testpaths; Makefile prefers the repository venv and preserves PYTHON overrides; added the lead regression test (`make test`: 563 collected across all five suites, zero collection errors, 553 passed, 9 skipped, 1 xfailed in 18.82s; `make test TEST_PATH='tests/lead -q -p no:cacheprovider'`: 96 passed in 4.14s; `make -n test PYTHON=python3`: python3 override retained).
- Finished D-3 plan and direction decision from the read-only Notion export, preserving schedule disagreements and the early 2026-10-21 version 1 freeze; renamed the D-3 decision reference in the lead prompt and clarified verifier rule 6 to include fail and unverifiable without changing interfaces (`python3` inline planning checks: four weeks, five roles per week, six milestones, approval/version and prompt wording passed; `make validate-schemas`: Validated 6 draft 2020-12 schemas and 8 examples).

- Verified the selected 19-file commit scope in a separate HEAD archive overlaid only with those files, excluding concurrent uncommitted role work (make validate-schemas with the workspace .venv Python in the isolated archive: 6 schemas and 8 examples validated; make test in that archive: 168 passed in 4.97s).
- Recorded "Status: approved by the user on 2026-10-21" in decisions 0002, 0003 and 0004; published their exact JSON schema/example content and set schemas/VERSION to 1 (make validate-schemas PYTHON=.venv/bin/python: Validated 6 draft 2020-12 schemas and 8 examples; make test PYTHON=.venv/bin/python: approved-record equality tests passed).
- Added judgment-input.schema.json, judgment.schema.json and evaluation-report.schema.json plus criterion.json, judgment.json and evaluation_report.json; retained existing contract/verdict/handoff shapes (make validate-schemas PYTHON=.venv/bin/python: 6 schemas and 8 examples validated).
- Extended local-only schema reference validation, required artifact inventory and deterministic timestamp-format checks without new dependencies; boundary tests reject missing schemas/examples, malformed criteria/reports, wrong metric intervals/units, invalid audit states, missing handoff evidence and unknown references (make test PYTHON=.venv/bin/python: 264 passed, 2 skipped; skips require external graders).
- Updated docs/interfaces.md, AGENTS.md section 3, and the two explicitly authorized controller/evaluation role prompts for the approved model order, shared three-call budget, nested guard, judgment/report contracts, access audit and API-equivalent accounting (make test PYTHON=.venv/bin/python: interface/prompt consistency tests passed).
- Published the approved installed-version hook contract with corrected evidence links; kept probe evidence and other roles' implementations unchanged (published evidence-link test passed; .venv/bin/python -m plugin.check_probe_evidence plugin/evidence/2026-10-21-exec plugin/evidence/2026-10-21-tui: both runs context_visible=true, continued_once=true, exit_code=0).

## Remaining

- D-4, next on 2026-10-27: read the four engineer STATUS files and review runtime evidence against version 1 interfaces; write the integration review with blockers, conflicts, schedule risks and scope-cut proposals. Repeat on 2026-11-03 and 2026-11-10; monitor interface blockers for the two-day limit. Reconcile the historical pending items below with current host evidence.
- Owning roles must implement and demonstrate version 1 runtime behavior: controller judge/handoff and shared-budget routing, all-hook HARNESS_NESTED bypass, verifier judgment delegation, and schema-valid evaluation report production. Shared contract publication is complete; runtime completion is not claimed.
- Review production handoff-save point, nullable transcript handling, other SessionStart sources, persisted trust and retry/approval behavior with Role 2. Startup probe evidence does not establish these remaining behaviors.
- D-5, by 2026-11-13: update README.md for verified installation/demo, write docs/architecture.md and docs/demo.md, and verify the two-session demo in a fresh clone with retained evidence.
- D-6, by 2026-11-15: write docs/slides/ and docs/qa.md with all four required questions.
- Pending host verification: opt-in real Codex integration, nested codex exec/live model calls, and six macOS Seatbelt tests cannot run in this noninteractive sandbox. Two external private-grader fixture tests also await trusted grader configuration. The full run skipped nine tests total; legacy top-level suites and remote CI were not run.
- Role 5 expected failure: tests/eval/test_runner.py::test_stop_e1_partial_report_is_invalid_with_counts reports that aggregate-only halt invalidity would require a frozen-schema revision. Recorded only; no schema or eval change was made by this lead session.

## Decisions

- Record evaluation task-set version 1 as frozen on 2026-10-22 with the user-supplied digest: Claude host verification supplies private validation evidence, while public metadata and counts are independently checked in this session. Any task-set change requires version 2 and a new freeze record.
- Preserve task-cluster report metrics and require family-cluster intervals in Claude's final evaluation: user-approved decision 4 of 2026-10-22 retains the interfaces and qualifies final claims.
- Treat FILE1/FILE2/FILE3 as decisions 0002/0003/0004: those are the three proposals immediately preceding the user's explicit approval and implementation request.
- Publish version 1 on 2026-10-21: the user approved the bundle and explicitly requested VERSION=1 before the planned 2026-10-24 freeze.
- Preserve approved schema/example content exactly: active artifacts match the JSON blocks in the approved records; existing contract/verdict/handoff shapes remain unchanged.
- Use gpt-6-luna via logged-in codex_cli as primary, same-model cheap_api fallback and local Gemma as stage two: the user's approved model/transport order.
- Use audited external private graders in fresh post-exit copies and invalidate observed access/inconclusive capture: the user's STOP-E4 decision replaces the earlier deny-read prerequisite without claiming filesystem isolation.
- Keep role-prompt edits limited to session authorization: the earlier interface session authorized prompts 03/05; this continuation authorizes the D-3 path in prompt 01 and wording only in prompt 04. Runtime packages and other STATUS files remain untouched.
- Leave staging and commits to the host: this session has read-only .git and explicit instructions not to stage or commit; concurrent role changes remain outside the commit plan.
- Use importlib collection rather than test-package markers: the user explicitly selected this fix and prohibited __init__.py additions in other roles’ test directories.
- Retain both schedule sources without resolution: the supplied Notion schedule and role prompt commitments differ on analyzer timing and optional QLoRA.

## Verify commands

- .venv/bin/python -m pytest tests/lead -q
- git diff --check -- docs/eval-freeze.md docs/plan.md state/STATUS-lead.md
- make validate-schemas PYTHON=.venv/bin/python
- make test PYTHON=.venv/bin/python
- .venv/bin/python -m plugin.check_probe_evidence plugin/evidence/2026-10-21-exec plugin/evidence/2026-10-21-tui
- git diff --check -- AGENTS.md docs/interfaces.md docs/validate_schemas.py prompts/03-controller-engineer.md prompts/05-eval-engineer.md schemas tests/lead state/STATUS-lead.md
- make test
- make test TEST_PATH='tests/lead -q -p no:cacheprovider'
- make -n test PYTHON=python3
- git diff --check -- Makefile pyproject.toml prompts/01-tech-lead.md prompts/04-verifier-engineer.md docs/plan.md docs/decisions/0005-direction.md docs/changes/2026-10-22-lead.md tests/lead/test_pytest_config.py state/STATUS-lead.md

## Do not touch

- Version 1 interfaces without new user approval, a decision record and a version increment.
- Other roles' implementation files/tests/STATUS, including concurrent controller, verifier, plugin and eval work. Only the specifically requested prompt 01 D-3 path and prompt 04 wording edits are authorized in this continuation.
- Existing harness/, experiments/, scripts/, legacy tests and unrelated user edits.
- No git add -A, broad staging, foreign-path commit, deletion, history rewrite, hook registration or external configuration change.
- Keep the canonical hook contract and captured evidence; never replace measured evidence with a placeholder or claim production behavior from startup probes.

## Assumptions

- The approval placeholders identify the immediately preceding three proposals and DATE is 2026-10-21 in the user's timezone.
- A separate published judgment-input schema is the approved input validator, referencing the existing contract item rather than duplicating/changing it.
- This task publishes shared contracts, examples/tests and instructions; implementation changes in other roles' runtime packages remain their responsibility.
- Synthetic prices, paths, hashes, usage and CIs remain fixtures. No paid model call, real pricing/account eligibility result or runtime-backend completion is inferred.
- Version 1 validation needs deterministic timestamp checks even when optional jsonschema date-time dependencies are absent; the local validator enforces timestamp syntax/calendar validity without changing dependencies or approved schemas.
- The supplied Notion export is the historical design baseline; external evidence figures are attributed to that design and were not independently verified. Calendar dates are preserved without weekday labels.
- Week 4 support work maps Notion stabilization/rehearsal tasks onto existing ownership; it adds no interface or role deliverable.
- The frozen task-set digest and private validation/mutation findings are the user-supplied Claude host evidence; private grading was not rerun here. No live backend success, local GPU availability or new private measurement is inferred.
- Current user instructions supersede the previous session’s commit authorization: do not stage/commit, change external configuration, or edit CLAUDE.md, docs/handoff/ or docs/weekly/.
