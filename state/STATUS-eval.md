## Done

- Implemented approved M2 without shared interface changes: STOP-E1 exits 2, prints halt/count diagnostics, retains checkpoint and diagnostics, publishes no partial report, and resumes with the same output directory; replaced the strict xfail and removed the STOP-1 blocker (.venv/bin/python -m pytest tests/eval -q: 321 passed).
- Made task-set hashing use tracked public inputs only, excluding ignored/untracked generated files; tracked edits still change identity and missing/symlinked tracked inputs are rejected (.venv/bin/python -m pytest tests/eval -q: 321 passed).
- Created and validated external graders and private final-state reference overlays for all 120 tasks, with family-batch STATUS/summary checkpoints; retained the existing bug-chunk-tail grader after revalidation (.venv/bin/python -m eval.runner.validate_graders --private-root "$PRIVATE_ROOT" --tasks all > "$PRIVATE_ROOT/validation-final-with-hash.jsonl": exit 0, 120 valid/0 invalid; originals 155 passed/443 failed, references 598 passed/0 failed; bug-chunk-tail original 0/3, reference 3/0).
- Added reusable isolated grader validation and synthetic-root tests; published per-task counts/grader hashes and enumerated every public specification/metadata change; public workspace sources remain unchanged (.venv/bin/python -m pytest tests/eval -q: 321 passed; git diff --name-only -- eval/tasks: 377 prompt/metadata files, no workspace source changes).
- Computed the all-task fingerprint through the runner's taskset_digest: 32af2a304d8131ae5291668b502520952cbd5da930eee73d3e1536ba4c58f643 (.venv/bin/python -m eval.runner.validate_graders --private-root "$PRIVATE_ROOT" --tasks all > "$PRIVATE_ROOT/validation-final-with-hash.jsonl": exit 0, task_count=120, valid_count=120, matching task_set_sha256).

## Remaining

- Claude reviews the task/grader validation and public specification changes; Role 1 records the freeze. All public tasks still have frozen=false; no freeze document was written.
- Human review of structural helper extraction and submitted regression coverage quality remains necessary: behavioral graders deliberately do not prescribe implementation details.
- Pending host verification: installed CLI executor/controller/verifier/resume compatibility, actual nested guard, retry behavior, complete event capture, aliases, process termination and sandbox behavior. Network, nested execution, live calls and macOS sandbox-exec are unavailable here and were not attempted.
- Implement and host-verify two-session handoff execution/observations; current private references and graders check the final day-2 state without any executor.
- Obtain verified versioned prices and actual per-call accounting; complete done-claim denominator and hash-pinned paired local-minus-cheap_api parity. Missing observations remain undefined.
- Estimate and obtain approval for the 10-task pilot, manually re-check five baseline samples, then obtain explicit full-run approval. D-2 through D-5 measurements remain pending.
- Run the full repository suite once before a future merge; this session ran only tests/eval and did not stage or commit.

## Decisions

- Halt without a report and retain recovery evidence: the approved M2 decision supersedes the earlier schema-change proposal.
- Hash only version-controlled public files plus private grader contents: generated files cannot silently change task identity.
- Keep 25 related families and 20 two-session tasks: preserve the approved experimental task-type factor and disclose family correlation.
- Make submitted unittest requirements explicit: bug fixes need one method, features/refactorings two, multiple-requirement/two-session tasks three; refactoring originals already satisfy functional behavior.
- Keep graders behavioral: refactoring variants exercise both public APIs; multiple-requirement variants check the public docstring; two-session variants check both APIs, batch semantics and handoff evidence.
- Keep all reference implementations and grader sources private and apply references only to copies: no public workspace execution, model calls or private source disclosure.

## Verify commands

- .venv/bin/python -m pytest tests/eval -q
- .venv/bin/python -m eval.runner.validate_graders --private-root "$PRIVATE_ROOT" --tasks all > "$PRIVATE_ROOT/validation-final-with-hash.jsonl"
- git diff --check -- eval tests/eval state/STATUS-eval.md
- Before a future merge only: full repository test suite once.

## Do not touch

- controller/, verifier/, plugin/, shared schemas/configuration, other roles' tests/STATUS files, or concurrent changes; never share task contents with Role 3.
- .git and historical reports; do not stage, commit, delete repository files or rewrite history.
- No executor, controller, judge or live model calls until host prerequisites and pilot authorization are satisfied.
- Never publish private locations, reference implementations or grader contents. Repository tests use synthetic private roots only.

## Assumptions

- The user's 2026-10-22 priority order and private-write authorization supersede stale STATUS restrictions and the obsolete M2 blocker.
- PRIVATE_ROOT in verification commands is a trusted shell variable supplied explicitly; no private location is stored in repository files or inherited by executors.
- Public regression-method minimums clarify delivery requirements rather than changing family algorithms; quality/structural compliance still require reviewer inspection.
- Validation counts test methods/groups, with errors counted as failures; it establishes negative/reference discrimination, not executor quality, task independence or read isolation.
- The task-set fingerprint is a candidate for Claude verification and Role 1 freeze recording, not evidence of a completed evaluation run.
