## Current state

- Latest consolidation: 2026-10-25 v3-doc-config-corpus-consolidation Role 5.
- All 54 v3 candidates are authored, six shapes; 63 required sessions; metadata remains unfrozen.
- Canonical counts: eval/tasks-v3/VALIDATION.md; 24 cross-shape author pairs added; Claude host acceptance pending.
- Full A/H3 configs contain identical sorted inventories and remain draft_not_approved; plugin mode is design only.
- Pilot draft reserves ten disjoint IDs across all shapes (11 sessions); separate materials/private validation are not authored.
- Corpus exporter/tests/synthetic seed included; real retained-run export awaits the host.
- Continue from the latest dated Remaining section; older History construction remainders are superseded below.

## History

### Done

- Authored the complete `bug_fix` shape as nine independent v3 candidates, with public inputs, smoke tests and `frozen=false` metadata; other shapes are unbuilt (inline inventory/config audit: 9 candidates, 9 unfrozen, two wrapped configs rejected, zero staged/deleted paths).
- Validated all nine private graders against references and untouched starters; retained requirement derivations and coverage privately (`.venv/bin/python -m eval.runner.validate_graders`, nine IDs in eval/tasks-v3/VALIDATION.md, trusted root supplied externally: exit 0, 9 valid/0 invalid, 50 reference checks pass, all nine starters fail, 30/30 requirements covered).
- Exhausted the generated and declared targeted mutation populations and retained hash-bound semantic reviews privately (`.venv/bin/python -m eval.runner.validate_graders --mutants 10000`, same nine IDs: exit 0, 350 generated + 18 targeted = 368 executed, 352 killed, 16 equivalent, 0 survivors/errors/unexecuted).
- Enforced public assertion independence and scanned the retained executor corpus; recorded an author structure-comparison table without claiming independent reviewer acceptance (validator: 0 shared assertion lines, 994 distinct corpus files from 2,754 examined occurrences, 0 corpus warnings; eval/tasks-v3/STRUCTURE-REVIEW.md: 36 pairs × three axes, independent host pairs 0).
- Filled both not-approved configs with the actual nine-task candidate list and updated partial/full STOP-3 scenarios; documented validation and pending gates in README, CHANGES and DESIGN (inline config audit: matching nine IDs, 9 required sessions, no second sessions; A 9 workloads/$1.458000, H3 18 Sol + 18 Luna/$3.060720/36 combined units; both strict loader refusals).
- Verified public starter smoke tests and v3 tooling regression tests (inline per-task `python -m unittest discover -s . -p test_*.py -v`: 9/9 public smoke passes; `.venv/bin/python -m pytest tests/eval -q`: 2123 passed in 467.32s; final targeted validator run: 45 passed in 16.58s, including three cases added after full-run collection).

### Remaining

- Continue authoring by complete shape: `feature_plus_test`, then `constrained_refactoring`, `multiple_requirements`, `two_session`, `ambiguous_requirement`; nine tasks each, 45 remaining. Keep the DESIGN inventory and domain balance. Preserve private coverage/reference/mutation validation and zero-survivor acceptance for each added shape.
- Author the ten disjoint calibration tasks and obtain the separate host pilot estimate/approval before A calls. Manually review five pilot outputs. The 60–85% target is unmeasured; do not select or tune held-out tasks using A/H3 outcomes.
- Complete all ambiguity author notes, deterministic question matchers and positive/unrelated fixtures privately, with exactly one omitted public policy axis per task. All nine ambiguity tasks are currently unbuilt. Complete all day-2 prompts and executable carryover coverage when authoring the two-session shape.
- Claude performs independent architecture/data-flow/failure-mechanism and public-to-hidden derivation review, including the recorded 36 author pairs and comparisons across all 54 tasks; host validation precedes a separate task freeze. No independent reviewer acceptance or frozen digest is claimed here.
- Implement and host-probe plugin mode after Role 1/2's production contract/implementation is available: provenance, question pause/resume, ledger injection/revision binding, artifact audit and pinned accounting. Current `harness=true` remains legacy orchestration. Do not replace hooks with runner control calls.
- After all 54 tasks are validated, replace the partial nine-task config lists with the complete identical ordered inventory and recompute/pin task/runtime/pricing identities and STOP-3 estimates. Obtain spending approval before ten-plus-call batches. No paid calls are authorized by these drafts.
- Run the full repository suite once on the host before merge; this session verifies only tests/eval. Do not resume stopped v2 recovery or alter historical task inputs, graders or reports.

### Decisions

- Finish whole shapes: the user explicitly permits a shape-complete partial session, so this checkpoint completes nine bug-fix tasks rather than leaving a scattered partial population.
- Use distinct parsers, transaction ownership, heap scheduling, Unicode layout, graph traversal, layered provenance, dependency snapshots and bucket aggregation: task implementations have independent structures and failure mechanisms, with no template family or shared error namespace.
- Keep every candidate unfrozen and configs wrapped/not approved: interface-v3 approval supplied by the user does not establish task acceptance, calibration, runnable H3 or spending approval.
- Exhaust all 350 generated and 18 targeted mutants, reviewing 16 semantic equivalences privately: v3 acceptance requires zero survivors/errors/unexecuted; timeouts are unresolved and the historical 90% threshold is insufficient.
- Separate author pair review from independent host review: the 36-pair table is a construction aid, and cannot satisfy DESIGN's independent reviewer requirement by itself.
- List only the nine constructed candidates in both configs: absent tasks must not appear as runnable inventory; retain the planned 54 tasks/63 sessions and explicit 45-task remainder separately.

### Verify commands

- `.venv/bin/python -m pytest tests/eval -q`
- `.venv/bin/python -m pytest tests/eval/test_v3_grader_validation.py tests/eval/test_validate_graders.py -q`
- `.venv/bin/python -m eval.runner.validate_graders --private-root "$LHM_PRIVATE_V3" --tasks TASK_IDS` (trusted parent supplies the external root; expand TASK_IDS from eval/tasks-v3/VALIDATION.md).
- `.venv/bin/python -m eval.runner.validate_graders --private-root "$LHM_PRIVATE_V3" --tasks TASK_IDS --mutants 10000`
- Inline inventory/config/scope audit: matching candidate IDs, unfrozen metadata, wrapped config refusal, allowed paths, no private-path bytes, no staged/deleted files.
- `git diff --check`
- `git diff --exit-code -- eval/tasks eval/tasks-v2 eval/prices.yaml schemas controller verifier plugin prompts AGENTS.md`

### Do not touch

- Work only in this r5/v2 worktree with its .venv; edit only eval/, tests/eval/, state/STATUS-eval.md and the authorized trusted storage. Never publish private locations, grader/reference/author-note content or private validation details.
- V1/v2 task files, graders, configs, retained reports, prices, shared schemas/interfaces and existing CLI flags. No .git writes, staging, commits, deletions or history rewriting.
- No network, live model calls, nested Codex, macOS sandbox-exec or plugin installation in this environment. Never share evaluation material with Role 3 or expose trusted graders to an executor/control context.
- Frozen metadata must remain false until the separate host-validation/freeze step. No calibrated quality, successful H3 execution or measured spending claim follows from offline task construction.
- Preserve the exact nine validated candidates and private reviews when continuing; any changes invalidate their relevant hash-bound evidence and require revalidation.

### Assumptions

- The user's supplied approval/freeze of interface v3 on 2026-10-25 is authoritative for this session despite stale proposed-status prose elsewhere; this work edits no interface file and makes no host compatibility claim.
- The user explicitly authorizes candidate/public and trusted-private authoring and permits completion by whole shape. This supersedes the previous STATUS file's design-only/no-private-access restrictions.
- The ten-task calibration material and pilot have not been completed; the requested authoring checkpoint remains uncalibrated and unfrozen. The 60–85% A target is a target, not evidence about these candidates.
- The existing offline Fast pricing scenario is retained without a network refresh; workload counts are planning units, not measured provider-request counts or spending limits.
- Author pair/equivalence review is the work of this session's author. Independent host review remains pending; no sub-agents, external reviewers or paid models were used.

## 2026-10-25 status-format-migration Role 5

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

## 2026-10-25 v3-doc-config-corpus-consolidation Role 5

### Done

- Consolidated the 54 validation rows from the six shape-session sources into VALIDATION.md, retaining per-shape evidence with links to canonical counts: 225 covered requirements, 325 reference checks, 3,168 mutants, 2,980 killed, 188 equivalent, zero survivors/errors; these are prior author results, not fresh private validation (`.venv/bin/python /tmp/check_v3_consolidation.py`: PASS, 54 validation rows and totals reconcile).
- Added 24 cross-shape author comparisons with separate architecture/data-flow/failure columns, covering all six shapes; refreshed DESIGN, README and CHANGES (`.venv/bin/python /tmp/check_v3_consolidation.py`: PASS, 24 pairs with differing shapes).
- Filled both full-run configs with the same lexicographically ordered 54 IDs and updated estimates for 63 required sessions; all metadata remains frozen=false and configs draft_not_approved (`.venv/bin/python /tmp/check_v3_consolidation.py`: PASS, balanced inventory, session counts and draft refusals).
- Added the draft A calibration config and estimate: ten reserved disjoint IDs, all six shapes, 11 sessions, calibration=true; materials remain unauthored (`.venv/bin/python /tmp/check_v3_consolidation.py`: PASS, ten unique non-evaluation IDs and draft refusal).
- Included the corpus session's four new files; replaced the private directory literal with runtime environment/supplied-root basenames plus the generic placeholder, using neutral synthetic tests (`.venv/bin/python /tmp/check_v3_consolidation.py`: PASS, changed corpus sources/fixtures contain no retired literal).

- Verified the eval package including corpus regressions (`.venv/bin/python -m pytest tests/eval -q`: 2147 passed in 444.64s, exit 0).

### Remaining

- Claude independently reviews all-population architecture/data flow/failure mechanisms and public-to-hidden derivations; rerun trusted private validation on the host before the separate freeze. This supersedes History's remaining 45-task authoring/config inventory items; all 54 public tasks now exist.
- Author the ten reserved disjoint calibration tasks, their private references/graders/coverage and independent validation. The new pilot config is a reservation only. Obtain host pilot approval, run A and manually review at least five outputs; do not reuse or select the 54 held-out tasks based on outcomes. The 60–85% target remains unmeasured.
- Implement/host-probe actual plugin mode, including provenance, question pause/resume, ledger revision binding, captured artifacts and exact Luna accounting; current harness=true is legacy orchestration. Prior ambiguity-session notes record completed matchers/fixtures, and two-session notes record day-2/carryover evidence; validate them independently on the host.
- Export available retained report/native streams on the host into the corpus with explicit rebaseline review; only the synthetic seed is present here. Do not infer original-run audit certification from sanitized replay.
- Freeze public/private inputs only after host review and calibration; pin population, CLI/model/tier, plugin and prices, refresh estimates and obtain spending approval before ten-plus paid calls. Run the full repository suite once before merge; this session runs only tests/eval. No paid calls, real-hook evidence or private-grader reruns occurred here.

### Decisions

- Keep per-shape files as evidence notes with canonical count links: preserve session evidence without competing validation tables.
- Use lexicographic full-run order for both arms: paired inventories must agree exactly.
- Reserve a separate cal-v3 namespace/root with two tasks per first four shapes and one per two-session/ambiguity shape: satisfy user-requested all-shape coverage while keeping all 54 evaluation tasks held out. Materials remain explicit future work.
- Keep draft wrappers and unfrozen task bytes: documentation consolidation does not establish host acceptance, calibration, plugin compatibility or spending approval.
- Derive private basenames at use time and retain neutral synthetic fixtures: prevent host directory names from entering repository sources while preserving export/rebaseline behavior and existing flags.

### Verify commands

- `.venv/bin/python -m pytest tests/eval -q` (2147 passed in 444.64s, exit 0).
- `.venv/bin/python /tmp/check_v3_consolidation.py` (PASS: inventories, unfrozen metadata, draft refusal, validation totals, cross-shape pairs, privacy/scope/staging checks).
- `git diff --check` (exit 0).
- `git diff --name-only -- eval/tasks eval/tasks-v2 eval/prices.yaml schemas controller verifier plugin prompts AGENTS.md` (empty output).
- `git diff --cached --name-only` (empty output).

### Do not touch

- Only eval/, tests/eval/ and state/STATUS-eval.md are authorized. No task prompt, workspace or meta.json edits; no historical task/report/schema/CLI changes.
- No private-root discovery/access, network, model calls, plugin installation, staging, commits, deletions or history rewriting in this session. Keep .git read-only.
- Preserve prior STATUS dated sections and History; this consolidation alone refreshes Current state. No sub-agents.

### Assumptions

- The user's 54-task inventory is authoritative and matches public discovery; original shape-session validation is consolidated as recorded evidence, not re-certified without private storage.
- No disjoint calibration materials exist in this worktree: the ten-task pilot config reserves future materials rather than silently using held-out tasks. Its single two-session task requires 11 sessions; report ambiguity/carryover separately from difficulty calibration.
- Existing offline Fast prices remain uncalibrated planning inputs; no cost cap, paid execution approval or successful plugin runtime is inferred.

## 2026-10-25 v3-freeze-host-handoff Role 5

### Done

- Set frozen=true in all 54 version 3 metadata files, changing only that field; confirmed six shapes with nine tasks each and nine two-session tasks (`.venv/bin/python /tmp/audit_v3_freeze.py`: PASS, 54 metadata-only freezes and matching inventories).
- Added eval/freeze_v3.py for Claude's host invocation, printing the digest, task count, shape counts and two-session count; shared runner hashing includes tracked public files and the full private snapshot, including coverage/references/responder data (synthetic digest/config regression tests: `.venv/bin/python -m pytest tests/eval/test_frozen_v3.py -q`: 10 passed in 0.45s; real freeze command intentionally not run).
- Unwrapped full-v3-a into the standalone runner configuration, retained its estimate, and added host-filled task_set_sha256 placeholders to A and draft H3; runner rejects unfilled/mismatching pins before execution (`.venv/bin/python -m pytest tests/eval/test_frozen_v3.py -q`: 10 passed, including filled A estimate matching, H3 refusal and pre-execution mismatch rejection).
- Updated README and CHANGES with host procedure, evaluator pilot waiver and private-snapshot constraints; verified only authorized paths changed, no prompt/workspace/v1/v2/staged changes (`.venv/bin/python /tmp/audit_v3_freeze.py`: PASS; `git diff --check`: exit 0).
- Verified the eval package (`.venv/bin/python -m pytest tests/eval -q`: 2157 passed in 470.47s, exit 0).

### Remaining

- Claude runs `.venv/bin/python -m eval.freeze_v3 --private-root "$LHM_PRIVATE_V3"` on the host and fills both task_set_sha256 placeholders from its output. Send inventory/digest and host evidence to Role 1 for publication. No host digest or private validation is claimed here.
- Implement and host-probe actual plugin mode, including provenance, question pause/resume, ledger revision binding, artifact capture and pinned accounting; H3 remains draft_not_approved. Carry forward this item from v3-doc-config-corpus-consolidation.
- Carry forward the retained-run corpus export/rebaseline item from v3-doc-config-corpus-consolidation; synthetic replay does not certify original access audits.
- Confirm host CLI/model/tier/pricing pins and spending approval before full paid batches; run the full repository suite once on the host before merge. Full A measures difficulty without selecting or tuning tasks; disclose any result outside the target band.
- Earlier pending host-review, mandatory disjoint-pilot and unfrozen-population items are superseded by the user-supplied host acceptance and weekly evaluator decision. The optional disjoint pilot reservation remains unbuilt, not a freeze gate.

### Decisions

- Freeze now without a disjoint calibration pilot: user reports Claude accepted all 54 tasks after host review (60 mutants per task, zero errors/survivors and no private references in public inputs), with the evaluator waiver recorded in docs/weekly/2026-10-21-host-verification.md.
- Hash the complete supplied version 3 private snapshot using relative filenames and bytes, excluding interpreter/test caches: include notes/matchers without guessing their undocumented storage namespace; additional retained private records are pinned too. Future validation/run outputs must remain outside this immutable snapshot.
- Add an optional internal configuration digest pin and enforce it before executor work: the existing runner had population IDs but no explicit expected-digest field; no CLI flag, report schema or historical digest algorithm changes are needed.
- Retain the existing baseline CLI pin for A and keep H3 wrapped: A uses the current standalone runner, whereas actual plugin mode and hook compatibility remain future work.
- Append this handoff without refreshing Current state: this is a freeze job, not the single consolidation job authorized to rewrite that block.

### Verify commands

- `.venv/bin/python -m pytest tests/eval -q` (2157 passed in 470.47s, exit 0).
- `.venv/bin/python -m pytest tests/eval/test_frozen_v3.py -q` (10 passed in 0.45s).
- `.venv/bin/python /tmp/audit_v3_freeze.py` (PASS: metadata-only freeze, inventory, estimate, draft, ownership and staging checks; temporary session audit, not a committed tool).
- `git diff --check` (exit 0).

### Do not touch

- Only eval/, tests/eval/ and state/STATUS-eval.md are authorized; preserve v1/v2 files, report schemas, CLI flags and every v3 prompt/workspace byte.
- Do not locate/access the real private root or run the real freeze command here; no network, model calls, plugin installation, staging, commits, deletion or history rewriting. Keep .git read-only; no sub-agents.
- Preserve completed dated STATUS sections and History; leave H3 draft until the plugin-mode runner exists.

### Assumptions

- The user's host-review handoff and the matching weekly evaluator decision are authoritative; sandbox tests do not re-certify private validation or measure A/H3 quality.
- The host-supplied root is a separate, complete version 3 snapshot containing graders, coverage, references and all ambiguity author notes/matchers. The broader private-root hash requires that snapshot to remain immutable.
- A retains codex-cli 0.163.0-alpha.11.1 from the existing baseline configurations; the installed host version must match. Existing estimate files remain uncalibrated scenarios, not spending approval.

## 2026-10-25 v3-filled-digest-test-fix Role 5

### Done

- Replaced the placeholder assertion with matching 64-character lowercase hex digest checks for A/H3; load the filled A config directly and retain its estimate match and H3 draft rejection (`.venv/bin/python -m pytest tests/eval/test_frozen_v3.py -q`: 10 passed, 1 skipped in 0.52s).
- Added optional host comparison against eval.freeze_v3.freeze_summary when LHM_PRIVATE_V3 is set; otherwise skip only that host test; mocked runner checks reject a mismatching digest and accept the filled digest through real frozen metadata/public-input checks before checkpoint writing or executor work (`.venv/bin/python -m pytest tests/eval -q`: 2157 passed, 1 skipped in 469.27s, exit 0).

### Remaining

- Run the optional host digest regression with LHM_PRIVATE_V3 supplied; the user reports Claude already ran freeze_v3 and filled both config pins, superseding the prior placeholder-fill remainder. This sandbox does not independently certify the private snapshot.
- Carry forward plugin-mode implementation/host probing, retained-run corpus export/rebaseline, host runtime/pricing/spending gates and the full repository suite before merge from v3-freeze-host-handoff; this narrowly scoped fix changes none of them.

### Decisions

- Test the filled configuration directly: host freeze output has replaced the placeholders, so readiness must validate the persisted digest rather than require placeholder text or substitute a synthetic config.
- Mock private loading and computed digest for runner acceptance, stopping before checkpoint writing: exercise enforcement against actual frozen public inputs without private access or executor calls.
- Append this section only: the user requested one dated section and this is not a consolidation job.

### Verify commands

- `.venv/bin/python -m pytest tests/eval -q` (2157 passed, 1 skipped in 469.27s, exit 0).
- `.venv/bin/python -m pytest tests/eval/test_frozen_v3.py -q` (10 passed, 1 skipped in 0.52s).
- `git diff --check` (exit 0 after STATUS append).

### Do not touch

- Preserve all existing freeze changes, every task file, v1/v2 inputs and shared interfaces; this session edits only tests/eval/test_frozen_v3.py and appends state/STATUS-eval.md.
- Keep .git read-only; no staging, commits, network, model calls, private-root discovery, deletion or history rewriting.

### Assumptions

- The user-supplied host digest 7645e003ed4ef52c43d58555f494c7554ee468c5e628b5d95e22c37a30b5b01d and Claude's host freeze run are authoritative handoff evidence; LHM_PRIVATE_V3 is unset here, so local tests cannot re-certify that private hash.
- The complete planned freeze commit includes eval/CHANGES.md, eval/README.md, both full-v3 configs, eval/runner/core.py, eval/freeze_v3.py, eval/runner/frozen_v3.py, tests/eval/test_frozen_v3.py, state/STATUS-eval.md and all 54 eval/tasks-v3/*/meta.json files; no staging or commit was requested.
