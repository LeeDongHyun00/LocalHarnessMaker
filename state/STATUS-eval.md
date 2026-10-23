## Done

- Supported later read-only commands[i] display callbacks in the supplied complete const-array structure; verified all/allSettled, shorthand cmd plus literal options, nested Python quotes, synthetic alias access detection and rejection of every listed mutation before/inside/after the callback (`.venv/bin/python -m pytest tests/eval -q`: 1279 passed in 123.01s)
- Updated eval/CHANGES.md for the read-only callback follow-up and preserved frozen tasks, retained reports and schemas (`git diff --check -- eval tests/eval state/STATUS-eval.md`: exit 0; `git diff --exit-code -- eval/tasks eval/tasks-v2 eval/reports schemas`: exit 0)
- Resolved substitution-free command templates and immutable const/let string arrays through map, for-of and direct tool arguments; audited every element and verified native synthetic private-path detection plus fail-closed near misses (`.venv/bin/python -m pytest tests/eval -q`: 1218 passed in 114.77s)
- Recorded this parser correction in eval/CHANGES.md and preserved frozen task files, retained reports and schemas (`git diff --check -- eval tests/eval state/STATUS-eval.md`: exit 0; `git diff --exit-code -- eval/tasks eval/tasks-v2 eval/reports schemas`: exit 0)
- Enabled boolean calibration (default false) before freeze, with checkpoint/diagnostic/report-artifact labeling, stderr notice and compare refusal; enabled the v2 A pilot and revised its Fast planning estimate (`.venv/bin/python -m pytest tests/eval -q`: 1126 passed in 113.59s)
- Preserved the original Standard snapshot, pinned user-supplied Fast rates plus the Standard Sol 6 supplement, captured newly observed executor tiers per process, required control-call tier evidence and retained per-call pricing provenance across recovery; unknown tiers remain null (`.venv/bin/python -m pytest tests/eval -q`: 1126 passed in 113.59s)
- Implemented task_false_done_rate using retained last-session final messages and the verifier extractor's clause semantics, valid-task numerator/denominator, explicit missing-message exclusions, source hashes and seeded task-cluster bootstrap; retained criterion-level false_done_rate and added v1/v2 report-reader compatibility (`.venv/bin/python -m pytest tests/eval -q`: 1126 passed in 113.59s)
- Revised all four multiple_requirements target specifications, independent private graders/references and coverage manifests; archived the previous candidate privately and updated DESIGN plus the counts-only validation report (`.venv/bin/python "$LHM_PRIVATE_GRADERS/validate_distinct_pilot.py"`: 20 valid starter/reference pairs, 249 reference checks, 136 starter failures, 252/252 requirements covered, 1121 killed mutants, 18 reviewed equivalents, 0 unreviewed survivors, 20 public starter suites and 20 reference verification runs passing; prior bug-fix references fail 22 checks across the four changed task IDs)
- Preserved v1 public tasks, schemas and retained reports, and confirmed no private-root literal entered modified repository files (`git diff --exit-code -- eval/tasks schemas`: exit 0; offline snapshot/report/path checks: Standard snapshot unchanged, only the two authorized v2 planning/validation reports changed, 9 retained shared-schema reports valid, 1 provisional report unchanged, private-path scan clean)

## Remaining

- Host: transfer this read-only display follow-up at a safe boundary and re-audit the remaining const-array full-harness record. The user reports the template case is clean after 64a825b; host streams and the actual private grader root remain unavailable here.
- Review and transfer repository changes and the matching private v2 candidate artifacts at a safe boundary for other checkouts. Do not stage or commit here; use the final Commit plan on the host.
- Host: obtain spending approval for the 24-session baseline-A calibration using calibration=true. Run with the approved Codex version and observed priority tiers; retain candidate hashes and all outcomes. Calibration precedes freeze and is never headline evidence.
- After calibration: revise only at whole-family/type level if needed, build the remaining sixteen planned families, validate the whole population and publish its separate freeze through Role 1.
- Host recovery remains pending: regrade full B's interrupted terminal/Unicode framing and full harness's quoted heredoc. Use retained evidence first; source artifacts from other checkouts were not recovered in this session.
- Host: use the existing infrastructure-only rerun flow for eligible completed harness invalidities; checkpoint-only interrupted/capacity-limited runs resume their original command first. Never rerun a quality failure to improve the score.
- Preserve C skeletons for the user's authorship, paired comparison scope, five pilot-A reviews and twenty-sample reporting. Disclose historical v1 Luna control underpricing in the final evaluation; do not rewrite retained v1 reports or treat absent task-level metrics as zero.
- Run the full repository suite once before merge on the host. This session runs tests/eval only and makes no live executor/controller/judge calls.

## Decisions

- Permit later indexed display reads only inside a read-only forEach text callback: the supplied retained record logs commands[i] after its single collection use; every mutation, alias and unsupported extra reference must still prevent binding resolution.
- Decode substitution-free templates and one-use literal command arrays without executing JavaScript: expand every array element into an independently audited command, and retain inconclusive outcomes for interpolation, nonliterals, rebinding, mutation, aliases, unsupported uses or unsupported binding identity/scope.
- Permit an explicit calibration procedure before freeze: the default freeze rule remains, candidate bytes remain hash-pinned, and calibration status is persisted through recovery and refused by compare.
- Keep the original Standard snapshot intact and add dated tier snapshots: schema-compatible metadata serializes their complete pins in the existing source field; per-call artifacts retain tier/source/pricing_ref evidence.
- Capture newly emitted native applied settings at process exit: later resumes cannot reprice earlier calls. Control calls without an observed tier remain unknown, including existing controller versions without that field.
- Preserve original costs during retained-evidence recovery: catalog extensions must preserve every historical pin; fresh calls use new observations and historical calls remain explicitly identified.
- Give multiple_requirements distinct domain specifications within every pilot family: revised behavior interacts with canonicalization, ordering, aggregation/conflicts, rendering and batches, and the bug-fix references do not satisfy it.
- Apply verifier.claims.claimed_criteria through an eval-owned task-scope adapter: no verifier code or criterion-level metric changes. Retain final-message/segment and extractor/adapter hashes for reproducibility.
- Exclude invalid tasks and missing final messages from both task-claim populations: a claimed valid task lacking hidden grading remains in the denominator but makes the rate undefined, rather than establishing failure or silently shrinking the denominator.
- Infer report-interface version from presence of task_false_done_rate as approved in decision 0009: reverse exactly the two v2 schema additions for v1 validation, without editing schemas or migrating source reports.

## Verify commands

- .venv/bin/python -m pytest tests/eval -q
- Host/private validation only: .venv/bin/python "$LHM_PRIVATE_GRADERS/validate_distinct_pilot.py"
- git diff --check -- eval tests/eval state/STATUS-eval.md
- git diff --exit-code -- eval/tasks eval/tasks-v2 eval/reports schemas
- Host/retained evidence only: python -m eval.runner.regrade --private-root P --from SOURCE --out NEW
- Host/approved spending only: python -m eval run --config eval/configs/pilot-v2-a.yaml --out eval/reports/pilot-v2-a/

## Do not touch

- Work only in r5/v2 with this worktree's .venv; edit only eval/, tests/eval/ and this status file. Preserve other checkouts, private companion artifacts and other roles' paths.
- Frozen v1 public tasks/graders, retained v1 reports, schemas, controller/, verifier/, plugin/, root configuration and existing CLI flags. Never share task contents with Role 3.
- .git is read-only: no staging, commits, history rewrites or project-file deletion.
- No live executor/controller/judge calls, network, nested Codex or macOS sandbox-exec in this session. Model and executor integration checks must use mocks.
- Never publish private-root paths, grader/reference contents or mutation sources. Validation publication contains task IDs and numbers only.
- Never execute/resume Codex in a grading copy, grade invalid tasks, fabricate unknown accounting or waive malformed/unsupported/unresolved audit evidence through a later success.
- Keep C skeletons unfilled until the user authors them and the v2 candidate unfrozen until calibration review and the approved freeze procedure.

## Assumptions

- The user reports 64a825b was committed and the template record re-audited clean; the supplied full const-array structure supersedes the earlier brief. Synthetic native custom_tool_call regressions verify this follow-up, and the const-array outcome awaits host re-audit.
- The Fast prices, 2026-07-30 naming change and Luna CLI priority default are user-supplied official-page/host observations; network verification is unavailable. No live cost or quality measurement is claimed.
- The existing verifier exposes criterion extraction only. Binding task-scoped prose to one synthetic task ID applies its completion vocabulary, negation, exceptions and quote/code rules without treating criterion counts or test-only statements as whole-task completion.
- Only the retained final output of the final process in the last required session supplies completion evidence; absent evidence is explicitly undefined, with no earlier-session or intermediate-message substitution.
- Other historical host recovery outcomes are still unknown. Private v2 artifacts are local companion changes and must remain paired with the revised public candidate; no v1 private grader was edited.
