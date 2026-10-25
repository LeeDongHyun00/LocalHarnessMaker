## Current state

- Latest job: 2026-10-25 r1-process-001 Role 1 (format consolidation).
- Lead checks: 151 passed, 2 failed; Role 4 audit merge defect remains open.
- Next: Role 4 fixes late audit merge; rerun lead checks before host merge validation.
- Earlier integration, v3 freeze, smoke and presentation work remains under History / Remaining.

## History

### Done

- Published the user-approved frozen v3 schema/artifact set from d82b87a (2026-10-25, 01:55 KST), exact hook CLIs, hook-event mapping, pending-question unchanged-workspace exit, production caller boundaries and role implementation start; synchronized decision 0011, interfaces, plan and prompts (`.venv/bin/python -m pytest tests/lead -q`: 141 passed in 10.12s; `make validate-schemas`: Validated 11 draft 2020-12 schemas and 13 examples).
- Preserved every approved schema/example/marker byte, including original proposal metadata, while schemas/VERSION remains 3 and now denotes the frozen set (`python3` inline git ls-tree/git show byte comparison against d82b87a: 25 tracked schema/marker/example files byte-for-byte unchanged; VERSION=3).

- Published accepted decision 0011 with attributed v1/v2 findings and invalidity/grader limits, six design principles, hook table, pinned Luna/B-dropped/C-optional/0010-record-only confirmations, held-out v3 freeze rule and success criterion; added 0010's record-only note and resolved 0011 in the plan (`.venv/bin/python -m pytest tests/lead -q`: 141 passed in 31.97s; measurements are attributed host records, not rerun).
- Drafted interface version 3 requirements, completion-report, ledger, pin-check and Luna-call schemas with examples; exact workspace artifact paths, runner collection/accounting contract, fail-closed pin, kind/check mappings, single repair and separate ledger bookkeeping; retained all six historical schemas and report fields unchanged (`make validate-schemas`: Validated 11 draft 2020-12 schemas and 13 examples).
- Updated AGENTS.md, docs/interfaces-v3.md, the historical interface-page notice, plan and all five role prompts for the new schedule/ownership and real A/H3 hooks; the schema set remains proposed, not frozen; added lead boundary tests and updated historical version/count assertions (`.venv/bin/python -m pytest tests/lead -q`: 141 passed in 31.97s).

- Confirmed the required six STATUS headings and byte-for-byte preservation of all historical schemas/examples; the owned diff has no whitespace errors (`python3` inline HEAD-byte/heading audit: STATUS headings match; 6 historical schemas and 8 examples are byte-for-byte unchanged; `git diff --check -- AGENTS.md docs/decisions/0010-reservations-r2-grader.md docs/decisions/0011-pinned-luna-hook-direction.md docs/interfaces.md docs/interfaces-v3.md docs/plan.md docs/validate_schemas.py prompts/01-tech-lead.md prompts/02-plugin-engineer.md prompts/03-controller-engineer.md prompts/04-verifier-engineer.md prompts/05-eval-engineer.md schemas tests/lead state/STATUS-lead.md`: exit 0, no output).

- Published proposed decision 0010 with attributed reservations R2 diagnosis, three comparison/freeze options, Role 5/Claude recommendation and conditional owner steps; linked it under Open decisions in docs/plan.md. No decisions index exists in docs/decisions/README.md or AGENTS.md, so no index edit was made (`.venv/bin/python -m pytest tests/lead -q`: 104 passed in 4.20s).

- Published docs/eval-freeze-v2.md with the supplied 2026-10-24 Claude host evidence at main commit 9097281: digest, 100-task/20-family inventory, validation, calibration, shared-template limitation, immutable version 2 and post-freeze anti-contamination rule; moved fresh full A/B/harness runs to W2 in docs/plan.md. Host findings are attributed, not rerun here (`.venv/bin/python -m pytest tests/lead -q`: 104 passed; `git diff --check -- docs/eval-freeze-v2.md docs/plan.md state/STATUS-lead.md`: exit 0, no output).

- Published user-approved interface version 2 under decision 0009: required task_false_done_rate, claimed_complete_task unit, valid-task-only numerator/denominator, missing-final exclusions and version 1 compatibility; updated example, AGENTS.md, interfaces and Role 5 prompt without changing eval/ or any other report field (`make validate-schemas`: Validated 6 draft 2020-12 schemas and 8 examples; `.venv/bin/python -m pytest tests/lead -q`: 104 passed in 4.07s).
- Added lead regression checks for version 2 requirements, rate/unit/null boundaries, preservation of all version 1 fields and continued validity of the original version 1 example; recorded implementation follow-up for Role 5 and left staging/commits to the host (`.venv/bin/python -m pytest tests/lead -q`: 104 passed in 4.07s; `git diff --check -- AGENTS.md docs/interfaces.md docs/decisions/0009-task-level-false-done.md prompts/05-eval-engineer.md schemas tests/lead state/STATUS-lead.md`: exit 0, no output).

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

- Confirmed the final owned changes have no whitespace errors (`git diff --check -- AGENTS.md docs/decisions/0011-pinned-luna-hook-direction.md docs/interfaces-v3.md docs/interfaces.md docs/plan.md prompts/ tests/lead/test_hook_interfaces_v3.py state/STATUS-lead.md`: exit 0, no output).

### Remaining

- Coordinate owning-role work: Role 2 pin-check/guard/advice/ledger injection; Role 3 independent prompt/calibration design and pinned client/accounting; Role 4 deterministic completion/single repair/Stop ledger request; Role 5 v3 task design and real-plugin artifact collection, A/H3 configs and estimates. No runtime implementation or live acceptance is established by this lead publication.
- Publish a separate v3 freeze record after Role 5 supplies the held-out inventory/digest and reference/starter/mutation/shared-line validation. Freeze before full A/H3 runs. Keep v1/v2 task sets, graders, reports and prior freezes historical and unchanged; no H3 evaluation on them.
- Track 10/28–11/03 real smokes on two non-evaluation projects, actual hook compatibility, model/version/pricing pin failures, question/answer interaction, complete accounting, application repair and ledger sequencing. The proposal's under-10-second calls, under-2-percent control cost and about-two-hour full configurations remain unmeasured targets/estimate.
- Track 11/04–11/08 A/H3 paired runs and human sample, then 11/09–11/13 recovery/final analysis. Success requires preserved quality, pass-rate agreement within paired interval, at least half task false done and at most 15 percent extra cost per pass. Undefined/inconclusive evidence cannot establish success; no numeric equivalence margin is authorized.
- D-4 integration reviews: 10/27, 11/03, 11/10; Claude prepared the first early. Monitor two-day blockers, schedule slips, stale-audit report accuracy and ledger-continuation effects on retained final-message claims. Do not substitute earlier messages in the task-level metric.
- Refresh D-5 README/architecture/demo for implemented v3 hooks by 11/13 and obtain fresh-clone/live host evidence. Existing v1/v2 demo captures are historical, not H3 acceptance. D-6 slides and Q&A by 11/15; presentation 11/16, with the original negative result stated plainly.
- Host performs the full suite once before merge and real compatibility/installation/Codex/sandbox tests. This restricted session runs lead tests only; no staging or commit. Nested Codex/live calls/macOS sandbox-exec/network remain unavailable here.

### Decisions

- Adopt user-approved 0011, accepted 2026-10-25: the original claim is answered negatively; build deterministic hooks plus two low-effort pinned Luna calls and evaluate only A/H3 on held-out v3. B is dropped, C optional, 0010 record-only.
- Freeze schema version 3 from d82b87a, approved by the user 2026-10-25 at 01:55 KST: approval is now explicit, schemas/VERSION stays 3, Roles 2–5 implement now; later schema changes require a new decision, user approval and version increment. Preserve the approved bytes including proposal metadata.
- Use a workspace-only artifact root .localharness/v3/ with SHA-256 session directories, fixed artifact filenames and per-call JSONL: the runner collects and prices hook outputs without orchestrating control calls. Extra pin-check/Luna-call schemas make those formats locally verifiable.
- Supersede handoff only on the new hook path with executor-written ledger: retain old schemas/CLIs/artifacts unchanged for v1/v2 history; no Luna transcript reconstruction or llm_judge on H3.
- Enforce one call per phase with no automatic fallback/regeneration: failures count toward the two-call session budget; keep old command budgets only for historical consumers. Unknown usage stays null and conflicting model identity fails closed.
- Permit an unchanged-workspace pending-question pause without audit or ledger: the first-prompt hook instructs asking and ending the turn before any file changes; no new wire fields or assumed answers.
- Audit once before application repair and mark changed final messages stale: a second audit would exceed the chosen phase budget. Request ledger writing once as separate bookkeeping, preserving application claims/evidence in the final response; no extra app repair or recursive ledger retry.
- Distinguish A and H3 child guards: A uses HARNESS_NESTED=1, H3 removes it for real hooks, controller-owned nested Codex always sets it; never mutate parent configuration/environment.
- Preserve the user's no-quality-loss rule and report paired uncertainty: an interval containing zero alone is not proof of equivalence; no numeric margin was supplied.

### Verify commands

- .venv/bin/python -m pytest tests/lead -q
- make validate-schemas
- git diff --check -- AGENTS.md docs/decisions/0010-reservations-r2-grader.md docs/decisions/0011-pinned-luna-hook-direction.md docs/interfaces.md docs/interfaces-v3.md docs/plan.md docs/validate_schemas.py prompts/01-tech-lead.md prompts/02-plugin-engineer.md prompts/03-controller-engineer.md prompts/04-verifier-engineer.md prompts/05-eval-engineer.md schemas tests/lead state/STATUS-lead.md

### Do not touch

- This session: eval/, plugin/, controller/, verifier/, task sets/private graders, docs/weekly/, docs/handoff/, docs/evaluation/, CLAUDE.md, root configuration, other roles' tests/STATUS and read-only .git. Do not stage/commit, delete files, rewrite history, change external configuration, use network, spawn agents or invoke nested/live models/macOS sandbox-exec.
- Historical v1/v2 schema bodies/examples/report fields, task sets, grader contents/digests and measured captures. The current schema marker denotes frozen hook interfaces, not a report migration.
- No unapproved revision of frozen v3 interfaces and no tuning H3 on frozen v3 outcomes. Implementation belongs to Roles 2–5 in their owned paths.

### Assumptions

- Direction approval and measured findings are explicit user instructions and attributed Claude proposal/host evidence dated 2026-10-24/25; this offline session did not remeasure them. V2 harness has 23 invalid tasks and stopped recovery; its subset is diagnostic. B pricing at the stop was pending; the proposal's about-1.2x figure is attributed, not recomputed.
- The approval time, commit identity, CLI operations and question-pause policy are supplied explicitly by the user; no independent host observation is claimed. This documentation publication establishes no runtime compatibility or implementation evidence.
- Expected command exit defaults to configured zero-success convention only when unspecified; unsupported/ambiguous oracles stay unavailable and user questions remain unanswered until visible clarification. A ledger presence/hash check does not establish decision quality.
- No numeric equivalence/noninferiority margin was supplied. The proposal's two-hour Fast run estimate and timing/control-cost targets remain estimates/targets, not measurements or paid-batch approval.
- No PR is requested in this read-only .git session. This STATUS/0011 provide the change summary and Assumptions; the final Commit plan lists only owned changes. Historical Done evidence below is retained as history, not current H3 acceptance.

## 2026-10-25 status-format-migration Role 1

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

## 2026-10-25 r1-process-001 Role 1

### Done

- Added cross-role v3 adapter/CLI fixture regressions with mocked Luna, both verifier rounds, supported citations, accounting, immutable evidence and ledger publication; checks remain red on the owning-role defect rather than relaxing the contract (.venv/bin/python -m pytest tests/lead -q: 151 passed, 2 failed in 40.18s; both cases reached valid ledger publication before failing on ignored audits).
- Added specification-driven CLI help coverage for all 11 section-3.2 signatures across 10 parsers, including retained historical modes (same pytest command: all 10 CLI-help cases passed; no argument drift observed).
- Converted all five STATUS files to dated append-only jobs and <=10-line current blocks, preserving legacy content under History; documented worktree/disjoint-path parallel jobs and consolidation (python3 inline archive/format audit: all five archives restore byte-for-byte to HEAD, six ordered job headings valid).
- Added the 40-line final-report cap, change-only README/CHANGES rule and no-brief-restatement rule to all five prompts; wrote docs/changes/2026-10-25-contract-tests-and-status.md (python3 inline prompt audit: all five prompts contain all three reporting rules).
- Verified schema preservation and offline validity without editing runtime packages or frozen interfaces (make validate-schemas: Validated 11 draft 2020-12 schemas and 13 examples; git diff --quiet -- controller verifier plugin schemas: exit 0).

### Remaining

- Role 4: fix verifier/v3_report.py's late audit merge; an existing round-1 report currently prevents reading the supplied claim-audit.json. Both unchanged-message and stale-message regressions fail with status=unavailable, claims=[] and luna_call=null. Preserve original audit provenance and the two-call budget.
- Rerun .venv/bin/python -m pytest tests/lead -q after the owning-role fix; CI is intentionally failing on this defect. The host runs the full suite once before merge and the real installation/compatibility/sandbox checks.
- Continue all earlier integration, v3 freeze, smoke, evaluation and presentation items in History / Remaining in their existing order; this process job does not establish live H3 acceptance.

### Decisions

- Keep cross-package failures visible in CI: the user explicitly requested defects for owning roles, without runtime edits or a weakened specification.
- Keep legacy dates/content in History and use dated migration metadata only: existing prose does not establish historical job boundaries.
- Use r1-process-001 as this consolidation job ID: the request supplied no job ID and authorized a concrete reviewable result.

### Verify commands

- .venv/bin/python -m pytest tests/lead -q
- make validate-schemas
- git diff --quiet -- controller verifier plugin schemas
- git diff --check -- AGENTS.md prompts state tests/lead docs/changes/2026-10-25-contract-tests-and-status.md

### Do not touch

- Runtime packages, other roles' tests, evaluation artifacts/task sets/graders, frozen schema bytes, docs/weekly, docs/handoff, docs/evaluation, root configuration and read-only .git. Other-role STATUS edits are format conversion only.
- No staging, commits, deletion, history rewriting, network, live model calls, nested Codex, macOS sandbox-exec or sub-agents in this session.

### Assumptions

- This session performs the single format-consolidation job; other-role migration records reference their preserved legacy work without changing its meaning.
- Synthetic pin evidence and a mocked Luna client exercise package contracts only. No installed-Codex/provider/command-isolation acceptance is inferred.
- Shared verifier check help must retain both documented modes; flags are compared to their documented union and unconditional requirements to their intersection. Actual v3 behavior is exercised by the integration test.

## 2026-10-25 r1-pin-observed-001 Role 1

### Done

- Published accepted decision 0012, the two model verification sources, version-specific operator procedure and unchanged controller identity enforcement; synchronized AGENTS.md section 3 and docs/interfaces-v3.md while retaining frozen version 3 (.venv/bin/python -m pytest tests/lead -q: 171 passed in 13.21s).
- Added only the closed model_evidence object and its enabled-result requirement to the pin-check schema, preserving existing enabled reason_codes and all other constraints; added listing/probe synthetic examples and the offline example mapping (make validate-schemas: Validated 11 draft 2020-12 schemas and 14 examples).
- Added source, required-field, unknown-field, nullable-value, timestamp, hash and enabled-reason regression coverage; reused the repository's deterministic RFC 3339 checker because optional jsonschema format dependencies are absent (.venv/bin/python -m pytest tests/lead -q: 171 passed in 13.21s; initial run: 3 timestamp-test failures, corrected in the test helper).
- Confirmed the requested additive scope and historical preservation without runtime edits (python3 inline HEAD structural/byte comparison: Pin-check change is exactly additive; 23 other tracked schema/example/marker files unchanged; VERSION=3; git diff --check -- AGENTS.md docs/interfaces-v3.md docs/decisions/0012-pin-check-observed-service.md docs/validate_schemas.py schemas tests/lead state/STATUS-lead.md: exit 0, no output).

### Remaining

- Role 2 must implement the approved version-specific luna_observation registry and pin-check evidence integration in owned paths; Role 3 retains per-call identity enforcement. The additive schema still requires checks.model_listed=true and a model_list artifact when enabled. Any required relaxation needs a separate approved interface change; do not fabricate listing evidence. Synthetic examples do not establish a working no-listing runtime path.
- The prior r1-process-001 late audit-merge regressions now pass in this checkout; host full-suite-before-merge and real installation/compatibility/sandbox validation remain pending. This session does not attribute or certify an owning-role runtime fix.
- Continue History / Remaining integration, held-out v3 freeze, smokes, evaluation and presentation work in its existing order. No live H3 acceptance is established here.

### Decisions

- Publish 0012 at version 3 as an explicit exception to the normal increment rule: the user approved this exact amendment at 05:55 KST and required the set to stay frozen at version 3.
- Preserve all pre-existing schema constraints and record the legacy listing limitation: the user authorized only an additive model_evidence change, not relaxation of checks/model_list or runtime implementation.
- Append this job without refreshing Current state: this is an ordinary amendment job, not a status consolidation job.

### Verify commands

- .venv/bin/python -m pytest tests/lead -q
- make validate-schemas
- git diff --check -- AGENTS.md docs/interfaces-v3.md docs/decisions/0012-pin-check-observed-service.md docs/validate_schemas.py schemas tests/lead state/STATUS-lead.md
- python3 inline structural comparison against HEAD removing only model_evidence and then.required; byte comparison of all other tracked schemas/examples/VERSION.

### Do not touch

- Runtime packages, plugin/VERIFIED_VERSIONS.json, other roles' tests/STATUS, eval artifacts/task sets/private graders, docs/weekly, docs/handoff, docs/evaluation, root configuration and read-only .git. Do not stage, commit, delete files, rewrite history, change external configuration, use network, invoke live/nested models or spawn sub-agents.
- Historical schemas/examples and all frozen interfaces except the exact user-approved 0012 addition. Subsequent changes require their own decision, explicit approval and version increment.

### Assumptions

- The 05:55 KST approval, installed-CLI listing failure and six-second priority Luna probe are supplied host evidence, not independently measured here. The external evidence file and its user-referenced Role 2 history digest were not available as a verifiable observation in this checkout; no digest or native thread identity is invented.
- Both examples are synthetic schema fixtures. Their existing enabled listing fields are retained to satisfy unchanged constraints and do not prove that probe-only enablement is implemented.
- No PR is requested; this append supplies the change summary and Assumptions. The host owns full-suite validation, staging and committing after reviewing runtime integration.
