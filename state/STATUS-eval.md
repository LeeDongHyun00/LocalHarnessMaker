## Done

- Verified all eval tests and updated eval documentation (`.venv/bin/python -m pytest tests/eval -q`: 686 passed in 79.93s).
- Preserved frozen tasks/retained reports and checked patch whitespace (`git diff --exit-code -- eval/tasks eval/reports`: exit 0; `git diff --check -- eval tests/eval state/STATUS-eval.md`: exit 0).

- Fixed control accounting under symlinked runtime ancestors while rejecting runtime/file/child links and manifest escapes (focused `.venv/bin/python -m pytest tests/eval/test_control_accounting.py tests/eval/test_runner.py -q -k 'symlinked_parent or links_within_runtime or failing_grader_content or checkout_paths'`: 8 passed, 162 deselected).
- Restricted published grading output to unittest identifiers/status and totals; full logs remain external; failing/error/skipped synthetic graders cover initial publication and regrading (same focused command: 8 passed, 162 deselected).
- Added repository-relative evidence paths and checkout-prefix normalization, with validation from another working directory, completed-run resume, regrading and legacy absolute-reference compatibility (same focused command: 8 passed, 162 deselected).

## Remaining

- Host: verify the three fixes with a fresh smoke destination and external retained report; check control model/costs, grading publication and relative checkout paths. No evaluation run is in progress here.
- The user fills all twenty C skeletons once using only each public prompt/workspace, before any C run starts. Agents must never fill them or revise them from outcomes.
- Host: finish live capacity recovery/timeout and Role 3/4 integration verification; mocked tests do not establish live compatibility. Preserve full-a-attempt1 as historical interrupted-run evidence.
- Host: run C, reduced B and full harness under the approved spending workflow. B/C fingerprint all 120 population graders; historical subset digests cannot be relabeled as full-population digests.
- Run paired comparisons of harness versus A (120), B (100 singles) and C (20 singles); compare handoff_success with A. Local Gemma and QLoRA remain dropped; parity is not measured.
- Complete done-claim denominator observations, five valid pilot-A human reviews and twenty-sample review/reporting; inspect historical pilot evidence on the host before use.
- Run the full repository suite once before future merge. Only eval tests are authorized in this session. Do not stage or commit; use the final Commit plan.

## Decisions

- Bound control-file symlink checks to the runtime: macOS `/var` is an acceptable ancestor; links at/below the runtime and manifest escapes remain rejected.
- Publish grading identifiers/status and summary lines only: path redaction cannot remove assertion source, messages or other private grader content reliably.
- Keep full grading logs only in external runtimes: published report/checkpoint grading fields contain counts/status and safe log references.
- Resolve repository-relative report references against the repository root: validation must work outside the checkout, with historical absolute references still accepted.
- Normalize regenerated/copied review evidence without altering retained sources: historical reports, frozen tasks, interfaces and accounting provenance remain intact.
- Preserve prior capacity recovery, static-template, population-hash and paired-comparison decisions: this patch changes only the user-prioritized smoke defects.

## Verify commands

- .venv/bin/python -m pytest tests/eval -q
- git diff --check -- eval tests/eval state/STATUS-eval.md
- git diff --exit-code -- eval/tasks eval/reports
- Host only: .venv/bin/python -m eval run --config eval/configs/smoke-harness.yaml --out FRESH_REPORT_DIRECTORY
- Before future merge only: full repository suite once.

## Do not touch

- Edit only eval/, tests/eval/ and state/STATUS-eval.md in the main checkout. Other roles may work concurrently in their own paths; preserve their changes.
- Frozen eval/tasks/, retained eval/reports/, controller/, verifier/, plugin/, schemas, CLI flags, root configuration and other roles' files. Never share tasks with Role 3.
- .git is read-only: no staging, commits, history rewrites or file deletion.
- No live executor/controller/judge calls, network, nested Codex, macOS sandbox-exec or real private-root lookup here. Synthetic graders exist only in tests.
- Never run Codex in grading copies or expose grader output to executor/controller context; never backfill historical provenance or relabel report digests.
- Keep C skeletons unfilled until the user authors them. Once any C run starts, no template revision is permitted.

## Assumptions

- The host smoke outcome is user-provided evidence; the external report is unavailable here and was not inspected. New executor/controller behavior is mocked and private graders are synthetic.
- Repository-relative published references use the repository root; external runtime references remain absolute to preserve verifiable raw evidence.
- Main-checkout work and concurrent Role 3/4 changes are authorized by the user; earlier isolated-branch instructions in this status are superseded.
