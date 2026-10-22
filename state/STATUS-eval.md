## Done

- Added deterministic reference-overlay mutation validation through grade(), with all requested operators, passing reference controls, bounded deadlines, private review/equivalence records, stale-record rejection and per-task acceptance checks (.venv/bin/python -m pytest tests/eval -q: 332 passed).
- Reviewed all 94 survivors from the initial expanded 1,985-mutant pass; strengthened 23 private graders for specification-defined behavior and recorded 71 equivalents privately (.venv/bin/python -m eval.runner.validate_graders --private-root "$PRIVATE_ROOT" --tasks all --mutants 10000 > "$PRIVATE_ROOT/mutation-after-full.jsonl": 120 tasks, 1914 killed, 71 recorded equivalent, 0 survived, exit 0; every task has a 1.00 non-equivalent kill rate).
- Kept validation/mutation copies and logs inside private temporary storage with cleanup, preserved evaluation retention, and isolated synthetic test retention under pytest storage (.venv/bin/python -m pytest tests/eval -q: 332 passed, including validation/mutation copy-location and cleanup checks).
- Added Claude transcript storage to protected audit roots, using the existing alias, case-insensitive canonicalization, symlink, denied-access and recursive ancestor behavior (.venv/bin/python -m pytest tests/eval -q: 332 passed).
- Revalidated all 120 tasks and updated only counts/hashes in the grader inventory; public originals remain 155 passed/443 failed and references 598 passed/0 failed (.venv/bin/python -m eval.runner.validate_graders --private-root "$PRIVATE_ROOT" --tasks all > "$PRIVATE_ROOT/validation-mutation-final.jsonl": 120 valid, 0 invalid, exit 0).
- Recomputed task-set SHA-256 ea8e9a6df55b22a01fc87a66298262f3cd7e738f8af8ca0853d3f877f5b9f12f without changing public task inputs (.venv/bin/python -m eval.runner.validate_graders --private-root "$PRIVATE_ROOT" --tasks all > "$PRIVATE_ROOT/validation-mutation-final.jsonl": matching task_set_sha256).
- Retained the approved M2 halt/recovery and tracked-public-input digest implementation from the reviewed commit (.venv/bin/python -m pytest tests/eval -q: 332 passed).

## Remaining

- Host reviewer verifies private mutation/equivalence records and the new task-set digest; Role 1 records the freeze. All public tasks remain unfrozen; no freeze document was written.
- Human review of structural helper extraction and submitted regression coverage quality remains necessary; behavioral grading does not prescribe implementation details.
- Host verification remains pending for installed CLI executor/controller/verifier/resume compatibility, actual nested guard, retry behavior, complete event capture, aliases, process termination and sandbox behavior.
- Implement and host-verify two-session handoff execution/observations; private references and graders currently check final day-2 behavior without an executor.
- Obtain verified versioned prices and actual call accounting; complete done-claim denominator and hash-pinned paired local-minus-cheap_api parity. Missing observations remain undefined.
- Estimate and obtain approval for the 10-task pilot, manually re-check five baseline samples, then obtain explicit full-run approval. D-2 through D-5 measurements remain pending.
- Run the full repository suite once before a future merge; this session ran only tests/eval and did not stage or commit.

## Decisions

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

- The user's current priority order and explicit private-write authorization govern this session; no network, nested execution or model calls are needed for this work.
- PRIVATE_ROOT in verification commands is supplied explicitly by the trusted caller; its value is never persisted in public files or forwarded to executors.
- The user's earlier kill rates use a smaller mutation sample. The new all-operator pass covers all 1,985 generated candidates; after rates exclude manually reviewed equivalents.
- A passing submitted-test mutation is equivalent only if application behavior and specified submitted-test requirements remain satisfied; this does not certify test quality.
- Offline validation establishes public/reference discrimination and mutation sensitivity, not executor quality, task independence, read isolation or completed measurement deliverables.
