## Done

- Excluded shipped public lines across v1/v2 and generic scaffolding from audit-time fingerprints; retained output-only, distinctive-literal and qualifying-line invalidation rules, including synthetic public-workspace overlap and executor-written-line regressions (`.venv/bin/python -m pytest tests/eval -q`: 1351 passed in 179.73s)
- Resolved substitution-free String.raw templates with raw escape semantics and bounded relative globs in literal for-loop lists; verified quoted heredoc data, all four capture forms, no matches, whitespace, private symlinks and fail-closed near misses (`.venv/bin/python -m pytest tests/eval -q`: 1351 passed in 179.73s)
- Added per-task shared_public_line_count and shared_assertion_line_count; rejected shared v2 assertion lines in ordinary and mutation validation while preserving v1 acceptance (`.venv/bin/python -m pytest tests/eval -q`: 1351 passed in 179.73s)
- Revised private input/expectation pairs across all four pilot families, archived originals privately and refreshed the counts-only validation table (`.venv/bin/python "$LHM_PRIVATE_GRADERS/validate_public_overlap_pilot.py"`, private-root argument expressed through the environment variable: validation/mutation CLIs exit 0; 20/20 valid pairs, 249 reference checks, 156 starter failures, 252/252 requirements covered, 100 shared public lines, 0 shared assertion lines, 1121 killed mutants, 18 reviewed equivalents, 0 unreviewed survivors)
- Updated eval/README.md and eval/CHANGES.md; preserved all public task files, schemas and retained run reports (`git diff --check -- eval tests/eval state/STATUS-eval.md`: exit 0; `git diff --exit-code -- eval/tasks eval/tasks-v2 schemas controller verifier plugin prompts AGENTS.md`: exit 0)
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

- Host/Claude: transfer the updated audit code at a safe boundary and re-audit the four reported calibration invalidities with the original hash-pinned graders. Preserve original run evidence. Privately archived originals are available; revised candidate hashes must not replace the original hashes during recovery.
- Review and transfer repository changes and matching private v2 revisions for subsequent calibration at a safe boundary. Do not stage or commit here; use the final Commit plan on the host. This worktree has no live v2 streams and claims no host re-audit result.
- Host: finish the running baseline-A/Fast calibration, retain every outcome/cost and review diagnostic results before freeze. Calibration remains separate from headline evidence.
- After calibration: revise only at whole-family/type level if needed, build the remaining sixteen planned families, validate the whole population and publish its separate freeze through Role 1.
- Host recovery remains pending: regrade full B's interrupted terminal/Unicode framing, full harness's quoted heredoc and the retained const-array full-harness record with updated code. Use retained evidence first; other checkouts were not modified here.
- Host: use the existing infrastructure-only rerun flow for eligible completed harness invalidities; checkpoint-only interrupted/capacity-limited runs resume their original command first. Never rerun a quality failure to improve the score.
- Preserve C skeletons for the user's authorship, paired comparison scope, five pilot-A reviews and twenty-sample reporting. Disclose historical v1 Luna control underpricing in the final evaluation; do not rewrite retained v1 reports or treat absent task-level metrics as zero.
- Run the full repository suite once before merge on the host. This session ran tests/eval only and made no live executor/controller/judge calls.

## Decisions

- Include both shipped public versions in fingerprint exclusions: immediate private grader sources span versions, and a public line cannot establish private provenance. Never use executor-mutated workspaces as public exclusions.
- Exclude Python scaffolding explicitly and retain qualifying hidden-line invalidation: multiline decorator spans and common headers are generic; no general fingerprint waiver was added.
- Count per-task nonempty normalized grader-line occurrences and assertion spans: ordinary and mutation validation reject any shared v2 assertion line; v1 only gains diagnostics.
- Change hidden input/expectation pairs across every pilot family while preserving all mappings: local exact assertion overlap was already zero, but public-example-based hidden cases also needed independent values.
- Preserve original grader bytes privately for retained-run recovery: existing hash checks remain strict; revised candidates require their own subsequent calibration provenance.
- Resolve only static String.raw literals and bounded unquoted relative loop globs: raw backslashes and expansion-before-substitution semantics matter; interpolation, uncertain tags, absolute/traversing/variable globs remain inconclusive.
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
- Offline/private validation: .venv/bin/python "$LHM_PRIVATE_GRADERS/validate_public_overlap_pilot.py"
- git diff --check -- eval tests/eval state/STATUS-eval.md
- git diff --exit-code -- eval/tasks eval/tasks-v2 schemas controller verifier plugin prompts AGENTS.md
- Host/retained evidence only: python -m eval.runner.regrade --private-root P --from SOURCE --out NEW
- Host/approved spending only: python -m eval run --config eval/configs/pilot-v2-a.yaml --out eval/reports/pilot-v2-a/

## Do not touch

- Work only in r5/v2 with this worktree's .venv; edit repository files only under eval/, tests/eval/ and this status file. Private v2 grader revisions are authorized; preserve archived originals, other checkouts and other roles' paths.
- Frozen v1 public tasks/graders, retained v1 reports, schemas, controller/, verifier/, plugin/, root configuration and existing CLI flags. Never share task contents with Role 3.
- .git is read-only: no staging, commits, history rewrites or project-file deletion.
- No live executor/controller/judge calls, network, nested Codex or macOS sandbox-exec in this session. Model and executor integration checks must use mocks.
- Never publish private-root paths, grader/reference contents or mutation sources. Validation publication contains task IDs and numbers only.
- Never execute/resume Codex in a grading copy, grade invalid tasks, fabricate unknown accounting or waive malformed/unsupported/unresolved audit evidence through a later success.
- Keep C skeletons unfilled until the user authors them and the v2 candidate unfrozen until calibration review and the approved freeze procedure.

## Assumptions

- The user reports the running host calibration's first twelve outcomes as 6 pass, 2 fail and 4 invalid, with none of the invalidities an access attempt. This session has no live v2 host streams; synthetic parser tests and offline grader validation are the evidence produced here. Claude owns host re-audit.
- Supplied local v2 graders had 0 exact shared assertion lines before revision; every task had 5 shared nonempty public lines. Independent hidden input/expectation pairs were still revised across all four families as requested, without publishing values or source.
- Existing retained-run hash checks require original grader bytes during host recovery. Revised candidate validation is separate evidence and does not authorize rewriting original run provenance.
- The Fast prices, 2026-07-30 naming change and Luna CLI priority default are user-supplied official-page/host observations; network verification is unavailable. No live cost or quality measurement is claimed.
- The existing verifier exposes criterion extraction only. Binding task-scoped prose to one synthetic task ID applies its completion vocabulary, negation, exceptions and quote/code rules without treating criterion counts or test-only statements as whole-task completion.
- Only the retained final output of the final process in the last required session supplies completion evidence; absent evidence is explicitly undefined, with no earlier-session or intermediate-message substitution.
- Other historical host recovery outcomes remain unknown. Private v2 revisions are companion changes; no v1 grader or reference was revised.
