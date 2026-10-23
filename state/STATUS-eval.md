## Done

- Resolved quoted JavaScript literal expressions using concatenation and literal replace/replaceAll chains, preserving first-occurrence, replacement-dollar, escape and UTF-16 semantics; synthetic native patch/private-path/near-miss regressions pass (`.venv/bin/python -m pytest tests/eval -q`: 1023 passed in 97.92s).
- Added the host continuation command with strict audit-only eligibility, copied-workspace exit-hash verification, normal runner day-2 orchestration, exact prompt bytes, fresh sessions, post-exit grading, retained accounting and continuation provenance (`.venv/bin/python -m pytest tests/eval -q`: 1023 passed in 97.92s).
- Preserved separate historical/new audit contexts with log/workspace hash checks; covered source immutability, protected source access, changed evidence, copy corruption, symlinks, version drift, known control costs and regrading other tasks once; retained re-audit/regrade support includes configured population hashes (`.venv/bin/python -m pytest tests/eval/test_continue_day2.py -q`: 33 passed in 15.15s; final `.venv/bin/python -m pytest tests/eval -q`: 1023 passed in 97.92s).
- Updated eval README/CHANGES and this handoff; frozen public tasks and retained reports remain unchanged (`git diff --check -- eval tests/eval state/STATUS-eval.md`: exit 0; `git diff --exit-code -- eval/tasks eval/reports`: exit 0).

## Remaining

- Host: re-audit full A using this worktree's audit implementation and the real retained logs/private root. The user reports full A at a21eda2: 120 tasks, 115 pass, 3 fail, 2 invalid; these outcomes were not inspected or rewritten here.
- Host: run `.venv/bin/python -m eval.runner.continue_day2 --private-root "$LHM_PRIVATE_GRADERS" --from eval/reports/full-a --out eval/reports/full-a-continued` with the recorded CLI version, pricing and approved spending workflow. It should regrade rotate-left and continue balanced-brackets only if all real day-1 logs are now clean. Confirm selection, hashes, timestamps/gap, added costs and the final full report; no historical cleanliness or recovered pass is claimed here.
- Preserve the main checkout's in-progress full harness/full B runs. Transfer this worktree's changes only when the host operator can do so without changing code under active runs.
- The user fills all twenty C skeletons once from public inputs before C starts; agents must never fill them or revise them from outcomes. B/C must fingerprint all 120 population graders.
- Host: complete live capacity/timeout recovery and Role 3/4 integration verification; finish C, reduced B and full harness under the approved workflow. Keep interrupted historical runs as evidence.
- Run paired harness comparisons with A (120), B (100 singles), C (20 singles), and handoff_success with A. Complete done-claim observations, five valid pilot-A human reviews and twenty-sample reporting. Local Gemma/QLoRA remain dropped; parity is not measured.
- Run the full repository suite once before merge on the host. Only eval tests were authorized here. Do not stage or commit in this session; use the final Commit plan.

## Decisions

- Resolve only quoted literals, literal concatenation/parentheses and replace/replaceAll with two quoted literal arguments: all other expressions remain inconclusive, and resolved text uses existing operand/patch-target auditing.
- Continue only tasks with exactly incomplete_access_audit and missing_two_session_handoff_observation, no prior detected access or day-2 observation, consistent day-1 evidence and a clean current re-audit: a new successful session cannot erase unsupported historical evidence.
- Reuse the normal runner from a copied checkpoint and fresh external runtime: version checks, model/effort, deadlines, retry limits, exact day2.md bytes, harness controls and nested guard retain their recorded behavior.
- Preserve the original config byte hash as source provenance and separately hash its materialized semantic copy: no original raw config bytes are fabricated.
- Audit copied historical logs using their original workspace context and pinned bytes/workspace hash; audit new logs against the new workspace with the source runtime protected: moving logs must not create false historical matches or exempt new accesses.
- Regrade every other task before day-2 execution, using fresh trusted grading copies and unchanged accounting: selected tasks lack day-2 evidence and are not graded during that pass.
- Account new control streams separately with continuation call IDs: filename ordering can shift old ordinal IDs, so source calls/costs are retained and new calls counted once. Unknown accounting remains null.
- Record continuation source/code/config hashes, both days' timestamps, gap, copy check and added calls/costs in diagnostic/task artifacts: shared report schemas and existing CLI flags remain unchanged.
- Preserve prior heredoc/literal-loop auditing, private grading publication, checkout-relative references, capacity recovery and C-template decisions: no task/report or unrelated implementation changes were made.

## Verify commands

- .venv/bin/python -m pytest tests/eval -q
- .venv/bin/python -m pytest tests/eval/test_continue_day2.py -q
- git diff --check -- eval tests/eval state/STATUS-eval.md
- git diff --exit-code -- eval/tasks eval/reports
- Host only: .venv/bin/python -m eval.runner.reaudit --private-root "$LHM_PRIVATE_GRADERS" --out eval/reports/full-a
- Host only: .venv/bin/python -m eval.runner.continue_day2 --private-root "$LHM_PRIVATE_GRADERS" --from eval/reports/full-a --out eval/reports/full-a-continued

## Do not touch

- Edit only eval/, tests/eval/ and state/STATUS-eval.md in r5/harness-smoke with its own .venv. Do not access/change the main checkout while full harness/full B run there; preserve other roles' work.
- Frozen eval/tasks/, retained eval/reports/, controller/, verifier/, plugin/, schemas, existing CLI flags, root configuration and other roles' paths. Never share task contents with Role 3.
- .git is read-only: no staging, commits, history rewrites or file deletion.
- No live executor/controller/judge calls, network, nested Codex, macOS sandbox-exec or real private-root lookup here. All new grader/path fixtures are synthetic.
- Never execute Codex in a grading copy, copy old grading artifacts into continued runtimes, expose grader contents to controller/executor context, backfill exit hashes or relabel report digests.
- Source runs and source runtimes are immutable during regrade/continuation. Incomplete continuation output requires host review; the fresh-output command does not resume it automatically.
- Keep C skeletons unfilled until the user authors them; do not revise templates after C starts.

## Assumptions

- Full-A totals, the rotate-left fix and balanced-brackets failure shape are user-provided host evidence. Actual retained logs/private graders were unavailable; regression results do not establish recovered historical outcomes.
- The retained checkpoint supplies the recorded semantic configuration, and the host provides its matching CLI version, pinned pricing snapshot and existing login. Source config/report provenance remains pinned while the normalized config copy has a separate hash.
- The user's worktree/main-checkout split supersedes older instructions to run full A in this session. No live calls, real regrade/continuation, staging or commits were performed.
- A clean access audit means no access was observed in supported retained evidence; it does not prove filesystem isolation.
