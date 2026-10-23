## Done

- Updated eval README/CHANGES and verified the complete eval package using this worktree's .venv (`.venv/bin/python -m pytest tests/eval -q`: 943 passed in 83.58s).
- Restored pre-loop audit behavior for both supplied Python heredoc shapes, comparing complete audits with loop transformation disabled; covered item.started/completed pairs and native command/function/code-mode records (`.venv/bin/python -m pytest tests/eval/test_access_audit.py -q`: 464 passed in 5.44s).
- Preserved legacy treatment for heredoc data, quoted arguments, here strings and comments, including private matches and unresolved expansions; real unsupported shell loops remain inconclusive (`.venv/bin/python -m pytest tests/eval/test_access_audit.py -q`: 464 passed in 5.44s).
- Retained literal parent-directory loop resolution and synthetic protected traversal, symlink and recursive ancestor checks, with the expanded pilot-B directory/printf shape covered (`.venv/bin/python -m pytest tests/eval/test_access_audit.py -q`: 464 passed in 5.44s).
- Preserved frozen tasks and retained reports; checked patch whitespace (`git diff --exit-code -- eval/tasks eval/reports`: exit 0; `git diff --check -- eval tests/eval state/STATUS-eval.md`: exit 0).

## Remaining

- Host: repeat Claude's task-by-task old/new re-audit across all 104 finished retained tasks using this worktree's code and .venv. Acceptance is all 104 clean with no private matches, retaining the three literal-loop fixes and removing the bug-chunk-tail heredoc regressions. External logs/private roots were unavailable here; no retained outcome has been changed or claimed clean.
- Host: continue full baseline A in the main checkout without this worktree's changes. Verify control model/costs, grading publication and relative checkout paths from retained smoke evidence as needed.
- The user fills all twenty C skeletons once using only each public prompt/workspace, before any C run starts. Agents must never fill them or revise them from outcomes.
- Host: finish live capacity recovery/timeout and Role 3/4 integration verification; mocked tests do not establish live compatibility. Preserve full-a-attempt1 as historical interrupted-run evidence.
- Host: run C, reduced B and full harness under the approved spending workflow. B/C fingerprint all 120 population graders; historical subset digests cannot be relabeled as full-population digests.
- Run paired comparisons of harness versus A (120), B (100 singles) and C (20 singles); compare handoff_success with A. Local Gemma and QLoRA remain dropped; parity is not measured.
- Complete done-claim denominator observations, five valid pilot-A human reviews and twenty-sample review/reporting; inspect historical pilot evidence on the host before use.
- Run the full repository suite once before future merge. Only eval tests are authorized in this session. Do not stage or commit; use the final Commit plan.

## Decisions

- Exclude heredoc payloads/delimiters and comments only from loop discovery: data keeps the legacy operand, expansion and protected-path checks, and quoted arguments keep their existing raw boundaries.
- Compare full synthetic audit results against the pre-loop path by disabling only transformation: the regression tests must preserve statuses, errors, matches, hashes and evidence rather than merely accept a clean label.
- Keep commands mixing actual shell loops and heredoc/comment spans inconclusive: bounded unrolling must never rewrite data or let data hide unsupported shell syntax.
- Unroll only one bounded literal-list for loop with simple commands/if guards: inspect every substituted filesystem word through the existing protection checks without executing captured shell code.
- Preserve uncertainty for unsupported loop shapes and variable use: expansions/globs in the list, mutations anywhere else, arithmetic, nested/while loops, directory changes and indirect code cannot establish audit cleanliness.
- Detect loop keywords at command boundaries: ordinary search arguments such as `rg for solution.py` retain their previous behavior.
- Keep host re-audit read-only and pending: synthetic regression success does not establish the historical smoke/pilot outcomes or rewrite retained evidence.
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
- .venv/bin/python -m pytest tests/eval/test_access_audit.py -q
- Host only, for each retained run: .venv/bin/python -m eval.runner.reaudit --private-root "$LHM_PRIVATE_GRADERS" --out RETAINED_RUN_DIRECTORY
- Before future merge only: full repository suite once.

## Do not touch

- Edit only eval/, tests/eval/ and state/STATUS-eval.md in the separate r5/harness-smoke worktree, using its own .venv. Do not access or modify the main checkout running full baseline A. Role 3 may concurrently change its own paths here; preserve those changes.
- Frozen eval/tasks/, retained eval/reports/, controller/, verifier/, plugin/, schemas, CLI flags, root configuration and other roles' files. Never share tasks with Role 3.
- .git is read-only: no staging, commits, history rewrites or file deletion.
- No live executor/controller/judge calls, network, nested Codex, macOS sandbox-exec or real private-root lookup here. Synthetic graders exist only in tests.
- Never run Codex in grading copies or expose grader output to executor/controller context; never backfill historical provenance or relabel report digests.
- Keep C skeletons unfilled until the user authors them. Once any C run starts, no template revision is permitted.

## Assumptions

- Claude's 104-task old/new host comparison and the supplied heredoc failures are user-provided evidence. External reports/private graders were unavailable and were not inspected here; no 104-clean claim has been made. All new log/path fixtures are synthetic and no model calls were made.
- Repository-relative published references use the repository root; external runtime references remain absolute to preserve verifiable raw evidence.
- The user's supplied worktree/main-checkout split supersedes the prior STATUS instructions about working in the main checkout. No actual retained-run re-audit or new measurement is possible in this session.
