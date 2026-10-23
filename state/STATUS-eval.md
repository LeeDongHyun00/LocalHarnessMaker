## Done

- Prepared seed-0 metadata-only C selection with five tasks per type and twenty families, twenty unfilled skeletons, human-only fill-once rules, config and estimate (.venv/bin/python -m pytest tests/eval -q: 649 passed in 60.49s).
- Added static-template preflight before processes, exact day-1 harness-wrapper injection, report artifact hashes, checkpoint hashes and changed-template resume refusal (.venv/bin/python -m pytest tests/eval -q: 649 passed, including real mocked-runner injection and completed-run resume drift).
- Added paired finished-report JSON/Markdown comparison with provenance refusal, matched valid intersections, diagnostic invalid handling, per-type metrics, handoff and seeded 10000-resample task-cluster intervals (.venv/bin/python -m pytest tests/eval -q: 649 passed, including CLI output, mismatches, pairing and undefined denominators).
- Fixed line-start control markers and zero-delegation accounting exceptions; suppressed absent-control-model warnings for standalone baselines; updated smoke/full harness planning to 15000 input and 1000 output tokens per generation (.venv/bin/python -m pytest tests/eval -q: 649 passed, including embedded markers, all-judge contracts and pinned budget exhaustion).
- Added full-population hashing for B/C with independent selected-input checkpoint hashes and drift refusal (.venv/bin/python -m pytest tests/eval -q: 649 passed, including synthetic population-versus-selected digest and changed-unselected-grader checks).
- Preserved this worktree's isolation and documented the changes (git symbolic-ref --short HEAD: r5/harness-smoke; git rev-parse --short HEAD: 9c81ecb; git diff --check -- eval tests/eval state/STATUS-eval.md: exit 0; git diff --exit-code -- eval/tasks eval/reports/pilot-a eval/reports/pilot-b: exit 0).

## Remaining

- The user fills all twenty C skeletons once using only each public prompt/workspace, before any C run starts. Agents must never fill them or revise them from outcomes.
- Host: integrate Role 4 forwarding/delegation implementation; run smoke-harness with a fresh destination and real grader population. Verify contract, day-2 contract, judge retries/fallback, handoff, reinstruction, model/effort, access audit, termination, nested guards and developer instructions. Mocked evidence does not establish live compatibility.
- Host: run C, reduced B and full harness under approved spending workflow. New B/C configs fingerprint all 120 population graders before selecting executor tasks. Existing subset-hash reports cannot be relabeled or compared to full-population reports.
- Run paired comparison commands documented in eval/README.md for harness versus A (120), B (100 singles), C (20 singles); compare handoff_success with A. No live reports were generated here. Local Gemma and QLoRA stay dropped; parity is not measured.
- Complete done-claim denominator observations, five valid pilot-A human reviews and twenty-sample review/reporting; inspect historical pilot audit/version/cost evidence on the host before using it.
- Run the full repository suite once before future merge. Do not stage or commit in this sandbox; final response supplies a Commit plan.

## Decisions

- Keep C guidance entirely human-authored: template fields use the exact token __HUMAN_FILL__; preparation never reads outcomes, private graders or references.
- Pin template bytes for every selected task at run start: missing/unfilled templates block processes, and resume checks include completed tasks; report artifacts retain the actual injected bytes.
- Add optional task_population to subset configs: selected-only fingerprints would make B/C incomparable with full A under mandatory digest equality. Hash full population contents for reports and selected inputs separately for checkpoints; no frozen task or shared schema changes.
- Keep comparison as python -m eval.runner.compare: existing run CLI flags and report schemas remain unchanged; compare_versions supplies version equality checks.
- Use the intersection valid in both reports for comparison metrics: any invalid matched task makes all output diagnostic, and comparison cost scope is explicit. Report-level all-attempted costs remain unchanged.
- Preserve undefined bootstrap results: zero denominators or missing costs null the value and bounds rather than dropping resamples.
- Retain control accounting from r5-harness-001: exact generation/delegation records, pinned process sidecars, retries/fallback repricing and incomplete-accounting null propagation remain in place.

## Verify commands

- .venv/bin/python -m pytest tests/eval -q
- git diff --check -- eval tests/eval state/STATUS-eval.md
- git diff --exit-code -- eval/tasks eval/reports/pilot-a eval/reports/pilot-b
- Host only, after Role 4 integration: .venv/bin/python -m eval run --config eval/configs/smoke-harness.yaml --out eval/reports/smoke-harness/
- Host only, after human preparation and spending approval: .venv/bin/python -m eval run --config eval/configs/full-c.yaml --out eval/reports/full-c/
- .venv/bin/python -m eval.runner.compare eval/reports/full-harness/report.json eval/reports/full-c/report.json --out eval/reports/compare-c/
- Before future merge only: full repository suite once.

## Do not touch

- Main checkout or its running full A; only eval/, tests/eval/ and state/STATUS-eval.md in this worktree are editable.
- Frozen eval/tasks/, retained pilot measurements, controller/, verifier/, plugin/, schemas, CLI flags, root configuration and other roles' files. Never share tasks with Role 3.
- .git is read-only: no staging, commits, history rewrites or file deletion.
- No live executor/controller/judge calls, network, nested Codex, macOS sandbox-exec or real private-root lookup here. Synthetic private graders exist only in tests.
- Never run Codex in grading copies or expose grader results to executor/controller context; never backfill historical provenance or relabel report digests.
- Keep C skeletons unfilled until the user authors them. Once any C run starts, no template revision is permitted.

## Assumptions

- This session starts on r5/harness-smoke at 9c81ecb with its own .venv; decision 0007 is supplied by the user but absent here. No shared decision record was edited.
- A config's optional task_population defines its source universe; host B/C has access to all 120 frozen population graders for content hashing, while only selected tasks execute. Legacy configs retain selected-only behavior.
- The frozen population digest b78913b04280f6696d419d2afdc96b152675973d82f05199ddef848986285d1f and freeze commit 7cdaf3b remain authoritative; actual population hashes are recomputed on the host, not fabricated here.
- The legacy bug-chunk-tail metadata has no family field: derive chunk-tail from its public task ID, explicitly recorded in the selection procedure.
- Comparison direction is left minus right and left/right for ratios; harness is the left argument. Executor effort may differ for B; model, seed, population, version and pricing must agree.
- Luna planning uses 15000 uncached input and 1000 output tokens ($0.002 per generation), informed by user-supplied host call observations. Executor proxies remain historical pilot-A averages, not measurements or spending caps.
- Role 4 integration and live compatibility remain unverified; completed mocked tests authorize no spending. The full repository suite remains a future pre-merge requirement.
