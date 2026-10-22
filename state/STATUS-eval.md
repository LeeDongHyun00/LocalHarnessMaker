## Done

- Prepared the version-1 freeze by changing only frozen=false to frozen=true in all 120 public task metadata files, retaining version=1; no other public task file changed (git diff --numstat -- eval/tasks: 120 meta.json files, each 1 insertion/1 deletion; .venv/bin/python -m pytest tests/eval -q: 336 passed, including all-task version/freeze assertions).
- Required every selected task to have an exact boolean true freeze flag before any external work, including checkpoint recovery, without changing shared interfaces (.venv/bin/python -m pytest tests/eval -q: 336 passed, including mixed-task missing/false/non-boolean rejection before subprocesses, private-grader loading or output creation).
- Updated eval/README.md and eval/CHANGES.md with freeze preparation, user-reported Claude host verification in 80205d3/ad7d7be and the pending final digest/Role 1 record (git diff --check -- eval tests/eval state/STATUS-eval.md: exit 0).

- Added deterministic reference-overlay mutation validation through grade(), with all requested operators, passing reference controls, bounded deadlines, private review/equivalence records, stale-record rejection and per-task acceptance checks (.venv/bin/python -m pytest tests/eval -q: 332 passed).
- Reviewed all 94 survivors from the initial expanded 1,985-mutant pass; strengthened 23 private graders for specification-defined behavior and recorded 71 equivalents privately (.venv/bin/python -m eval.runner.validate_graders --private-root "$PRIVATE_ROOT" --tasks all --mutants 10000 > "$PRIVATE_ROOT/mutation-after-full.jsonl": 120 tasks, 1914 killed, 71 recorded equivalent, 0 survived, exit 0; every task has a 1.00 non-equivalent kill rate).
- Kept validation/mutation copies and logs inside private temporary storage with cleanup, preserved evaluation retention, and isolated synthetic test retention under pytest storage (.venv/bin/python -m pytest tests/eval -q: 332 passed, including validation/mutation copy-location and cleanup checks).
- Added Claude transcript storage to protected audit roots, using the existing alias, case-insensitive canonicalization, symlink, denied-access and recursive ancestor behavior (.venv/bin/python -m pytest tests/eval -q: 332 passed).
- Revalidated all 120 tasks and updated only counts/hashes in the grader inventory; public originals remain 155 passed/443 failed and references 598 passed/0 failed (.venv/bin/python -m eval.runner.validate_graders --private-root "$PRIVATE_ROOT" --tasks all > "$PRIVATE_ROOT/validation-mutation-final.jsonl": 120 valid, 0 invalid, exit 0).
- Recomputed task-set SHA-256 ea8e9a6df55b22a01fc87a66298262f3cd7e738f8af8ca0853d3f877f5b9f12f without changing public task inputs (.venv/bin/python -m eval.runner.validate_graders --private-root "$PRIVATE_ROOT" --tasks all > "$PRIVATE_ROOT/validation-mutation-final.jsonl": matching task_set_sha256).
- Retained the approved M2 halt/recovery and tracked-public-input digest implementation from the reviewed commit (.venv/bin/python -m pytest tests/eval -q: 332 passed).

## Remaining

- Claude recomputes the final task-set digest on the host with python -m eval.runner.validate_graders using the private root. The earlier ea8e9a6df55b22a01fc87a66298262f3cd7e738f8af8ca0853d3f877f5b9f12f digest predates frozen=true and must not be recorded as the final freeze digest.
- Role 1 records the host-validated final digest in docs/eval-freeze.md. Public metadata freeze preparation is complete; SC-2 remains pending the digest record.
- Prepare and report the cost estimate for the 10-task baseline A/B pilot after host prerequisites and verified prices; obtain approval before the batch.
- Run the approved 10-task baseline A/B pilot on the host, retain reports/costs and manually re-check five baseline samples; obtain explicit approval before a full run.
- Human review of structural helper extraction and submitted regression coverage quality remains necessary; behavioral grading does not prescribe implementation details.
- Host verification remains pending for installed CLI executor/controller/verifier/resume compatibility, actual nested guard, retry behavior, complete event capture, aliases, process termination and sandbox behavior.
- Implement and host-verify two-session handoff execution/observations; private references and graders currently check final day-2 behavior without an executor.
- Obtain verified versioned prices and actual call accounting; complete done-claim denominator and hash-pinned paired local-minus-cheap_api parity. Missing observations remain undefined.
- D-3 through D-5 measurements remain pending; freezing the task metadata does not establish executor quality or measured cost.
- Run the full repository suite once before a future merge; this session ran only tests/eval and did not stage or commit.

## Decisions

- Freeze public task metadata as version 1 on the user's explicit authorization: Claude independently verified graders and found no behavior-changing surviving mutant on the host.
- Reject unfrozen selected tasks in all evaluation runs before external work: the runner has no separate headline mode, and a boolean-only check preserves the frozen CLI/schema interfaces.
- Preserve every other public task byte and defer the final digest to the host: private graders are unavailable here and freeze flags participate in task-set hashing.

- Mutate application and submitted regression overlays: reproduce the full reference-artifact validation surface while preserving all private material outside public files.
- Require a passing reference control at the same deadline and count mutation nontermination as killed: a mutant must retain specified observable behavior, including completion.
- Bind manually reviewed equivalences to the complete overlay, mutated source, destination and public prompt/expected hashes: stale records cannot silently suppress new survivors.
- Keep validation storage private and temporary while preserving evaluation retention: validation has no executor audit evidence to retain, and must not scatter private copies.
- Compare the user's supplied sampled before rates with explicitly identified expanded after rates: the populations differ, so raw rates are not a paired causal estimate.
- Keep public expected test-group counts and task specifications unchanged: additional private cases exercise already stated behavior.

## Verify commands

- .venv/bin/python -m pytest tests/eval -q
- .venv/bin/python -m eval.runner.validate_graders --private-root "$PRIVATE_ROOT" --tasks all --mutants 10000 > "$PRIVATE_ROOT/mutation-after-full.jsonl"
- .venv/bin/python -m eval.runner.validate_graders --private-root "$PRIVATE_ROOT" --tasks all > "$PRIVATE_ROOT/validation-mutation-final.jsonl"
- git diff --check -- eval tests/eval state/STATUS-eval.md
- Before a future merge only: full repository test suite once.

## Do not touch

- controller/, verifier/, plugin/, shared schemas/configuration, other roles' tests/STATUS files, concurrent changes and docs/eval-freeze.md; never share task contents with Role 3.
- .git and historical reports; do not stage, commit, delete repository files or rewrite history.
- No executor, controller, judge or live model calls until host prerequisites and pilot authorization are satisfied.
- Never publish private locations, graders, references, mutants or equivalence rationales. Repository tests use synthetic roots under pytest temporary storage only.

## Assumptions

- The user's current report of Claude's host verification is accepted as authorization for the metadata freeze; it was not independently repeated in this sandbox.
- Historical review fields remain unchanged because the user permits only the frozen flag to change in public task files.
- No grader/reference writes or private-root access are authorized or needed in this session; the earlier private-write assumption below describes the previous session only.

- The previous mutation session used explicit private-write authorization; this session performs only public metadata freeze preparation, runner checks and documentation.
- PRIVATE_ROOT in verification commands is supplied explicitly by the trusted caller; its value is never persisted in public files or forwarded to executors.
- The user's earlier kill rates use a smaller mutation sample. The new all-operator pass covers all 1,985 generated candidates; after rates exclude manually reviewed equivalents.
- A passing submitted-test mutation is equivalent only if application behavior and specified submitted-test requirements remain satisfied; this does not certify test quality.
- Offline validation establishes public/reference discrimination and mutation sensitivity, not executor quality, task independence, read isolation or completed measurement deliverables.
