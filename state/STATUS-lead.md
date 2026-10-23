## Done

- Wrote decision 0009 as a definition-only proposal for task-level false done across all configurations, retaining the criterion metric and exposing the invalid-task population conflict; confirmed that the frozen report rejects the new metric name and stopped without schema/runtime changes (`.venv/bin/python -m pytest tests/lead -q`: 96 passed in 5.46s; inline `Draft202012Validator` mutation check: Confirmed version 1 rejects metrics.task_false_done_rate, additionalProperties=false).

- Published user-approved decision 0008, the version 2 W2/W3 schedule and a separate-record notice in the version 1 freeze document; recorded Fast/priority policy, A-only calibration, fresh frozen-set full runs and anti-contamination disclosure without changing evaluation files or interfaces (`.venv/bin/python -m pytest tests/lead -q`: 96 passed in 3.93s; `git diff --check -- docs/decisions/0008-task-set-v2.md docs/plan.md docs/eval-freeze.md state/STATUS-lead.md`: exit 0, no output).
- Wrote D-5 install-through-demo README, architecture and recorded-demo guide from code and committed evidence, including explicit evidence limits, deadlines/shutdown, evaluation boundaries and a pending fresh-clone host checklist (`.venv/bin/python -m pytest tests/lead -q`: 96 passed in 4.22s; `git diff --check -- README.md docs/architecture.md docs/demo.md state/STATUS-lead.md`: exit 0, no output).
- Rechecked all five committed demonstrations offline: single-session approval/real verification/handoff; new-session context without user restatement; exhaustion remaining-work injection; and no stale context after injected generation/validation failures (`.venv/bin/python -m plugin.check_demo_evidence plugin/evidence/2026-10-22-real`: overall=pass, approval_gate=true, real_task_verified=true, synthetic=false, attempts=1, reinstructions=0; `.venv/bin/python -m plugin.two_session_demo check --out plugin/evidence/2026-10-23-two-session`: overall=pass, saved_handoff_validated/session_start_injected/context_visible/new_session/approval_gates=true, user_restatement_needed=false; `.venv/bin/python -m plugin.handoff_failure_demo check --scenario exhaustion --out plugin/evidence/2026-10-23-exhaustion`: overall=pass, remaining_injected=true, stale_injected=false; matching generation and validation checker commands: both overall=pass, remaining_injected=false, stale_injected=false).
- Closed the version-registry publication follow-up: 0.163.0-alpha.11.1 is in plugin/VERIFIED_VERSIONS.json at commit 53cb8a9, alongside the original 0.162 history; no registry edit or live probe was performed here (`git show 53cb8a9:plugin/VERIFIED_VERSIONS.json`: entries for codex-cli 0.162.0-alpha.17.2 and codex-cli 0.163.0-alpha.11.1 with evidence directories).

- Published user-approved decision 0007 dated 2026-10-23 and aligned plan, controller/eval prompts and AGENTS.md wording: local Gemma/QLoRA dropped, parity not measured, C user-filled on 20 stratified tasks paired with harness, B single-session only, approved W1–W3 schedule and cap-only executor API-key fallback; no interface or eval changes (`.venv/bin/python -m pytest tests/lead -q`: 96 passed in 9.16s; `git diff --check -- AGENTS.md docs/decisions/0007-scope-cuts.md docs/plan.md prompts/03-controller-engineer.md prompts/05-eval-engineer.md state/STATUS-lead.md`: exit 0, no output).
- Recorded integration review 1 as written by Claude on 2026-10-23 in docs/weekly/2026-10-27.md; its lead inventory confirms D-3 was done earlier and decision 0006 was already published; host results are attributed, not rerun here (`rg -n 'Prepared by Claude|1 Lead' docs/weekly/2026-10-27.md`: lines 3 and 11 identify author/date and completed deliverables).

- Published user-approved decision 0006 and aligned AGENTS.md section 3.3, the hook contract verified-version list, plugin prompt and plan; retained all measured hook samples and marked 0.163.0-alpha.11.1 pending Claude's host probe, without interface changes (`.venv/bin/python -m pytest tests/lead -q`: 96 passed in 15.86s; `git diff --check -- AGENTS.md docs/decisions/0006-codex-version-policy.md docs/hooks-contract.md docs/plan.md prompts/02-plugin-engineer.md state/STATUS-lead.md`: exit 0, no output).

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

- STOP-1 / STOP-L1: decision 0009 needs user approval for a report-schema revision and resolution of executor-caused invalid tasks in the numerator versus valid tasks only in the denominator. Do not implement in eval/metrics.py before approval/publication. D-6 docs/qa.md and docs/slides/outline.md are deferred by the explicit stop-at-definition instruction; resume those next after the blocker is resolved, with measured/pending labels and evidence sources only.

- Track decision 0008 with Role 5: W2 build/validate/A-only calibration of separate version 2, then receive its freeze inventory/digest/evidence and publish a separate freeze record before fresh full A/B/harness runs in W2/W3. Final analysis is due 2026-11-13; retain native priority-tier evidence, pinned Standard-rate accounting and disclosure of version 1 runs informing the 10/23 fixes. No version 2 result may inform a harness change after freeze. This session completes documentation only; no task construction, freeze or tier verification is claimed.
- Pending Claude host acceptance for D-5/SC-4: execute the fresh-clone checklist in docs/demo.md (clone, venv, disposable installation/--check, committed offline evidence checkers, schema validation, full suite and a fresh typed-approval real demo); retain log/commit/version and all skip/xfail reasons. Documentation and existing-capture audits are complete; fresh-clone acceptance is not done.
- Track decision 0006 run/session version recording, one-task audit smoke and mid-run detection through owning-role evidence. Registry publication is complete at 53cb8a9; registry membership alone does not prove all runtime version-policy behavior.

- D-4: integration review 1 was written early by Claude on 2026-10-23 in docs/weekly/2026-10-27.md; refresh on 10/27 if needed, then review on 11/03 and 11/10. Monitor interface blockers for the two-day limit and reconcile historical runtime pending items below with attributed host evidence. Keep this session away from docs/weekly/ and the running eval/.
- Owning-role integration follow-up: code now contains controller judge/handoff and shared-budget routing, hook nested guards and verifier delegation; the recorded demos establish only their exercised paths. Review remaining host integration/accounting evidence separately; do not infer complete evaluation validity from these demonstrations.
- Review persisted trust, nullable transcript/other SessionStart paths and terminal-closure/nested descendant shutdown with owning roles. Pass, exhaustion and injected generation/validation handoff paths now have committed demo evidence; the controller uses bounded subprocess.run without its own process-group cleanup owner.
- D-6, by 2026-11-15: write docs/slides/ and docs/qa.md with all four required questions.
- Pending host verification: opt-in real Codex integration, nested codex exec/live model calls, and six macOS Seatbelt tests cannot run in this noninteractive sandbox. Two external private-grader fixture tests also await trusted grader configuration. The full run skipped nine tests total; legacy top-level suites and remote CI were not run.
- Role 5 expected failure: tests/eval/test_runner.py::test_stop_e1_partial_report_is_invalid_with_counts reports that aggregate-only halt invalidity would require a frozen-schema revision. Recorded only; no schema or eval change was made by this lead session.

## Decisions

- Stop at decision 0009 definition and leave schemas/VERSION unchanged: /properties/metrics has additionalProperties=false, so the requested new name requires approval; D-6 cannot proceed in this explicitly stopped session.
- Preserve the requested formula and flag its population conflict: choosing how executor-caused invalid tasks affect the denominator would otherwise guess at a change to decision 0003.

- Adopt decision 0008, approved 2026-10-23: version 1 remains frozen/reported; harder version 2 tests the project claim, usage is not a constraint and result completeness is the goal. Use priority for Codex development jobs and all version 2 configurations, verified from native settings, with pinned Standard-rate API-equivalent costs.
- Limit this continuation to decision 0008, docs/plan.md, a separate-version-2-record notice in docs/eval-freeze.md and lead STATUS: the user prioritizes these documentation changes while host evaluation runs continue; no schema, CLI, hook or runtime change is needed.
- Historical D-5 session scope: edit only README.md, docs/architecture.md, docs/demo.md and this STATUS; do not stage/commit, run foreign tests, call models or disturb the host evaluation.
- Distinguish committed host captures, offline rechecks and pending fresh-clone acceptance: passing saved-evidence audits are not a new live run or persisted-trust/shutdown proof.

- Adopt decision 0007, approved 2026-10-23, superseding the historical local-stage and optional-training decisions below: complete all remaining approved work before the local LLM stage; usage limits are no longer a concern, while executor API billing remains a cap-block fallback only.
- Historical decision-0007 session scope: update decision 0007, plan, prompts 03/05, the planned-local wording in AGENTS.md and lead STATUS; leave the host evaluation and all runtime/interfaces unchanged.

- Adopt user-approved decision 0006 dated 2026-10-22: versions may change without holding or rollback; record run/session versions, compare same-version reports only, require a fresh hook probe and one-task audit smoke after changes, stop on mid-run changes and retain verified-version evidence.
- Limit this continuation to decision 0006, AGENTS.md section 3.3, conflicting version-policy wording in the hook contract/plugin prompt/plan and this STATUS: the user explicitly authorized these owned paths without any interface change.

- Record evaluation task-set version 1 as frozen on 2026-10-22 with the user-supplied digest: Claude host verification supplies private validation evidence, while public metadata and counts are independently checked in this session. Any task-set change requires version 2 and a new freeze record.
- Preserve task-cluster report metrics and require family-cluster intervals in Claude's final evaluation: user-approved decision 4 of 2026-10-22 retains the interfaces and qualifies final claims.
- Treat FILE1/FILE2/FILE3 as decisions 0002/0003/0004: those are the three proposals immediately preceding the user's explicit approval and implementation request.
- Publish version 1 on 2026-10-21: the user approved the bundle and explicitly requested VERSION=1 before the planned 2026-10-24 freeze.
- Preserve approved schema/example content exactly: active artifacts match the JSON blocks in the approved records; existing contract/verdict/handoff shapes remain unchanged.
- Use gpt-6-luna via logged-in codex_cli as primary, same-model cheap_api fallback and local Gemma as stage two (historical; local stage dropped by decision 0007): the earlier approved model/transport order.
- Use audited external private graders in fresh post-exit copies and invalidate observed access/inconclusive capture: the user's STOP-E4 decision replaces the earlier deny-read prerequisite without claiming filesystem isolation.
- Keep role-prompt edits limited to session authorization: the earlier interface session authorized prompts 03/05; this continuation authorizes the D-3 path in prompt 01 and wording only in prompt 04. Runtime packages and other STATUS files remain untouched.
- Leave staging and commits to the host: this session has read-only .git and explicit instructions not to stage or commit; concurrent role changes remain outside the commit plan.
- Use importlib collection rather than test-package markers: the user explicitly selected this fix and prohibited __init__.py additions in other roles’ test directories.
- Retain the historical analyzer timing disagreement: decision 0007 resolves the QLoRA disagreement by dropping training and supersedes conflicting measurement dates with the approved W1–W3 windows.

## Verify commands

- .venv/bin/python -m pytest tests/lead -q
- git diff --check -- docs/decisions/0009-task-level-false-done.md state/STATUS-lead.md

- git diff --check -- docs/decisions/0008-task-set-v2.md docs/plan.md docs/eval-freeze.md state/STATUS-lead.md
- .venv/bin/python -m pytest tests/lead -q
- git diff --check -- README.md docs/architecture.md docs/demo.md state/STATUS-lead.md
- .venv/bin/python -m plugin.check_demo_evidence plugin/evidence/2026-10-22-real
- .venv/bin/python -m plugin.two_session_demo check --out plugin/evidence/2026-10-23-two-session
- .venv/bin/python -m plugin.handoff_failure_demo check --scenario exhaustion --out plugin/evidence/2026-10-23-exhaustion
- .venv/bin/python -m plugin.handoff_failure_demo check --scenario generation --out plugin/evidence/2026-10-23-generation
- .venv/bin/python -m plugin.handoff_failure_demo check --scenario validation --out plugin/evidence/2026-10-23-validation
- git show 53cb8a9:plugin/VERIFIED_VERSIONS.json

- git diff --check -- AGENTS.md docs/decisions/0007-scope-cuts.md docs/plan.md prompts/03-controller-engineer.md prompts/05-eval-engineer.md state/STATUS-lead.md
- rg -n 'Prepared by Claude|1 Lead' docs/weekly/2026-10-27.md

- git diff --check -- AGENTS.md docs/decisions/0006-codex-version-policy.md docs/hooks-contract.md docs/plan.md prompts/02-plugin-engineer.md state/STATUS-lead.md

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

- This session: eval/, docs/weekly/, docs/handoff/, CLAUDE.md, schemas/, other roles' paths and read-only .git; no staging, commits, network, nested Codex or live model calls. Only decision 0009 and lead STATUS were edited.

- Version 1 interfaces without new user approval, a decision record and a version increment.
- Other roles' implementation files/tests/STATUS, including concurrent controller, verifier, plugin and eval work. This continuation edits only docs/decisions/0008-task-set-v2.md, docs/plan.md, docs/eval-freeze.md and lead STATUS; do not edit CLAUDE.md, docs/weekly/ or docs/handoff/.
- Existing harness/, experiments/, scripts/, legacy tests and unrelated user edits.
- No git add -A, broad staging, foreign-path commit, deletion, history rewrite, hook registration or external configuration change.
- Keep the canonical hook contract and captured evidence; never replace measured evidence with a placeholder or claim production behavior from startup probes.

## Assumptions

- Decision 0009 is a definition-only proposal because the user explicitly requires a stop if the metric needs a schema change. No resolution of the invalid-task population conflict or task-level extractor implementation is assumed.
- No PR was requested; decision 0009 and this STATUS supply the change summary and assumptions for a future PR. The current commit plan is limited to these two files; historical commit scopes below do not apply to this session.

- Decision 0008 approval, baseline A figures/commit/version and the CLI Fast description are user-supplied facts; no host or network verification was performed. W2/W3 use decision 0007’s through-11/06 and through-11/13 windows. Version 2 task count, exact freeze date and digest await owning-role evidence.
- Historical D-5 assumption: that session documented current code and committed evidence only. Fresh-clone and live acceptance are assigned to Claude on the host after the active evaluation finishes; no result is inferred in advance.
- No PR was requested; these decisions, assumptions and documented verification results are the change summary for a future PR description. The commit plan contains only the four documentation/status paths edited here.

- No additional scope assumption: decision 0007 approval and the usage-limit clarification are explicit user instructions dated 2026-10-23. Integration review 1 is attributed Claude host evidence; this offline documentation session does not independently verify its measurements.

- Decision 0006 uses the user-supplied host facts, corroborated by the existing CLAUDE.md section 2 and host-verification decision 11; no new assumption about 0.163.0-alpha.11.1 compatibility or runtime implementation is made.

- The approval placeholders identify the immediately preceding three proposals and DATE is 2026-10-21 in the user's timezone.
- A separate published judgment-input schema is the approved input validator, referencing the existing contract item rather than duplicating/changing it.
- This task publishes shared contracts, examples/tests and instructions; implementation changes in other roles' runtime packages remain their responsibility.
- Synthetic prices, paths, hashes, usage and CIs remain fixtures. No paid model call, real pricing/account eligibility result or runtime-backend completion is inferred.
- Version 1 validation needs deterministic timestamp checks even when optional jsonschema date-time dependencies are absent; the local validator enforces timestamp syntax/calendar validity without changing dependencies or approved schemas.
- The supplied Notion export is the historical design baseline; external evidence figures are attributed to that design and were not independently verified. Calendar dates are preserved without weekday labels.
- Week 4 support work maps Notion stabilization/rehearsal tasks onto existing ownership; it adds no interface or role deliverable.
- The frozen task-set digest and private validation/mutation findings are the user-supplied Claude host evidence; private grading was not rerun here. No live backend success, local GPU availability or new private measurement is inferred.
- Current user instructions supersede the previous session’s commit authorization: do not stage/commit, change external configuration, or edit CLAUDE.md, docs/handoff/ or docs/weekly/.
