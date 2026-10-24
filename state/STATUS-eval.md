## Done

- Authored the complete `bug_fix` shape as nine independent v3 candidates, with public inputs, smoke tests and `frozen=false` metadata; other shapes are unbuilt (inline inventory/config audit: 9 candidates, 9 unfrozen, two wrapped configs rejected, zero staged/deleted paths).
- Validated all nine private graders against references and untouched starters; retained requirement derivations and coverage privately (`.venv/bin/python -m eval.runner.validate_graders`, nine IDs in eval/tasks-v3/VALIDATION.md, trusted root supplied externally: exit 0, 9 valid/0 invalid, 50 reference checks pass, all nine starters fail, 30/30 requirements covered).
- Exhausted the generated and declared targeted mutation populations and retained hash-bound semantic reviews privately (`.venv/bin/python -m eval.runner.validate_graders --mutants 10000`, same nine IDs: exit 0, 350 generated + 18 targeted = 368 executed, 352 killed, 16 equivalent, 0 survivors/errors/unexecuted).
- Enforced public assertion independence and scanned the retained executor corpus; recorded an author structure-comparison table without claiming independent reviewer acceptance (validator: 0 shared assertion lines, 994 distinct corpus files from 2,754 examined occurrences, 0 corpus warnings; eval/tasks-v3/STRUCTURE-REVIEW.md: 36 pairs × three axes, independent host pairs 0).
- Filled both not-approved configs with the actual nine-task candidate list and updated partial/full STOP-3 scenarios; documented validation and pending gates in README, CHANGES and DESIGN (inline config audit: matching nine IDs, 9 required sessions, no second sessions; A 9 workloads/$1.458000, H3 18 Sol + 18 Luna/$3.060720/36 combined units; both strict loader refusals).
- Verified public starter smoke tests and v3 tooling regression tests (inline per-task `python -m unittest discover -s . -p test_*.py -v`: 9/9 public smoke passes; `.venv/bin/python -m pytest tests/eval -q`: 2123 passed in 467.32s; final targeted validator run: 45 passed in 16.58s, including three cases added after full-run collection).

## Remaining

- Continue authoring by complete shape: `feature_plus_test`, then `constrained_refactoring`, `multiple_requirements`, `two_session`, `ambiguous_requirement`; nine tasks each, 45 remaining. Keep the DESIGN inventory and domain balance. Preserve private coverage/reference/mutation validation and zero-survivor acceptance for each added shape.
- Author the ten disjoint calibration tasks and obtain the separate host pilot estimate/approval before A calls. Manually review five pilot outputs. The 60–85% target is unmeasured; do not select or tune held-out tasks using A/H3 outcomes.
- Complete all ambiguity author notes, deterministic question matchers and positive/unrelated fixtures privately, with exactly one omitted public policy axis per task. All nine ambiguity tasks are currently unbuilt. Complete all day-2 prompts and executable carryover coverage when authoring the two-session shape.
- Claude performs independent architecture/data-flow/failure-mechanism and public-to-hidden derivation review, including the recorded 36 author pairs and comparisons across all 54 tasks; host validation precedes a separate task freeze. No independent reviewer acceptance or frozen digest is claimed here.
- Implement and host-probe plugin mode after Role 1/2's production contract/implementation is available: provenance, question pause/resume, ledger injection/revision binding, artifact audit and pinned accounting. Current `harness=true` remains legacy orchestration. Do not replace hooks with runner control calls.
- After all 54 tasks are validated, replace the partial nine-task config lists with the complete identical ordered inventory and recompute/pin task/runtime/pricing identities and STOP-3 estimates. Obtain spending approval before ten-plus-call batches. No paid calls are authorized by these drafts.
- Run the full repository suite once on the host before merge; this session verifies only tests/eval. Do not resume stopped v2 recovery or alter historical task inputs, graders or reports.

## Decisions

- Finish whole shapes: the user explicitly permits a shape-complete partial session, so this checkpoint completes nine bug-fix tasks rather than leaving a scattered partial population.
- Use distinct parsers, transaction ownership, heap scheduling, Unicode layout, graph traversal, layered provenance, dependency snapshots and bucket aggregation: task implementations have independent structures and failure mechanisms, with no template family or shared error namespace.
- Keep every candidate unfrozen and configs wrapped/not approved: interface-v3 approval supplied by the user does not establish task acceptance, calibration, runnable H3 or spending approval.
- Exhaust all 350 generated and 18 targeted mutants, reviewing 16 semantic equivalences privately: v3 acceptance requires zero survivors/errors/unexecuted; timeouts are unresolved and the historical 90% threshold is insufficient.
- Separate author pair review from independent host review: the 36-pair table is a construction aid, and cannot satisfy DESIGN's independent reviewer requirement by itself.
- List only the nine constructed candidates in both configs: absent tasks must not appear as runnable inventory; retain the planned 54 tasks/63 sessions and explicit 45-task remainder separately.

## Verify commands

- `.venv/bin/python -m pytest tests/eval -q`
- `.venv/bin/python -m pytest tests/eval/test_v3_grader_validation.py tests/eval/test_validate_graders.py -q`
- `.venv/bin/python -m eval.runner.validate_graders --private-root "$LHM_PRIVATE_V3" --tasks TASK_IDS` (trusted parent supplies the external root; expand TASK_IDS from eval/tasks-v3/VALIDATION.md).
- `.venv/bin/python -m eval.runner.validate_graders --private-root "$LHM_PRIVATE_V3" --tasks TASK_IDS --mutants 10000`
- Inline inventory/config/scope audit: matching candidate IDs, unfrozen metadata, wrapped config refusal, allowed paths, no private-path bytes, no staged/deleted files.
- `git diff --check`
- `git diff --exit-code -- eval/tasks eval/tasks-v2 eval/prices.yaml schemas controller verifier plugin prompts AGENTS.md`

## Do not touch

- Work only in this r5/v2 worktree with its .venv; edit only eval/, tests/eval/, state/STATUS-eval.md and the authorized trusted storage. Never publish private locations, grader/reference/author-note content or private validation details.
- V1/v2 task files, graders, configs, retained reports, prices, shared schemas/interfaces and existing CLI flags. No .git writes, staging, commits, deletions or history rewriting.
- No network, live model calls, nested Codex, macOS sandbox-exec or plugin installation in this environment. Never share evaluation material with Role 3 or expose trusted graders to an executor/control context.
- Frozen metadata must remain false until the separate host-validation/freeze step. No calibrated quality, successful H3 execution or measured spending claim follows from offline task construction.
- Preserve the exact nine validated candidates and private reviews when continuing; any changes invalidate their relevant hash-bound evidence and require revalidation.

## Assumptions

- The user's supplied approval/freeze of interface v3 on 2026-10-25 is authoritative for this session despite stale proposed-status prose elsewhere; this work edits no interface file and makes no host compatibility claim.
- The user explicitly authorizes candidate/public and trusted-private authoring and permits completion by whole shape. This supersedes the previous STATUS file's design-only/no-private-access restrictions.
- The ten-task calibration material and pilot have not been completed; the requested authoring checkpoint remains uncalibrated and unfrozen. The 60–85% A target is a target, not evidence about these candidates.
- The existing offline Fast pricing scenario is retained without a network refresh; workload counts are planning units, not measured provider-request counts or spending limits.
- Author pair/equivalence review is the work of this session's author. Independent host review remains pending; no sub-agents, external reviewers or paid models were used.
