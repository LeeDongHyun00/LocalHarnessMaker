## Done

- Prepared the A/B ten-task pilot: deterministic ten-family selection, type quotas 3 bug_fix/3 feature_plus_test/2 multiple_requirements/2 constrained_refactoring, identical task lists/seed/CLI/deadlines, medium versus max, harness off and zero retries; the exact bundled configs with the published estimate pass paid-batch preflight while other large batches remain blocked (.venv/bin/python -m pytest tests/eval -q: 342 passed in 19.41s).
- Replaced the offline price placeholder with openai-standard-short-2026-10-22-v1, recording the supplied official URL, checked_on, Standard tier, 272K context note and lack of provider date/version within the frozen schema; tested both model rates, single billing of cache/reasoning, null unsupported models/tiers/context and propagation through accounting/cost_per_pass (.venv/bin/python -m pytest tests/eval -q: 342 passed in 19.41s).
- Added per-executor-attempt tokens and native primary used_percent before/after observations to task results and run diagnostics; missing observations stay null and the first in-run snapshot is separate, without adding frozen report fields (.venv/bin/python -m pytest tests/eval -q: 342 passed in 19.41s, including telemetry and mocked runner diagnostics coverage).
- Wrote eval/reports/pilot-estimate.md, including ten initial calls plus zero retries per configuration, the recorded 58248/54656/524 token proxy, A $0.178896 and illustrative B $0.231296 at 2x output for ten tasks; documented cache/output sensitivities and non-predictable plan usage (.venv/bin/python -m pytest tests/eval -q: 342 passed, including $0.0178896 per-task Sol snapshot calculation).
- Updated eval/README.md and eval/CHANGES.md; accepted the user-supplied final freeze record at 7cdaf3b, digest b78913b04280f6696d419d2afdc96b152675973d82f05199ddef848986285d1f, without changing any frozen public task or historical report (git diff --check -- eval tests/eval state/STATUS-eval.md: exit 0; git diff --exit-code -- eval/tasks: exit 0).
- Earlier host grader validation and mutation evidence remains recorded in eval/CHANGES.md and docs/eval-freeze.md; this preparation did not repeat private validation (.venv/bin/python -m pytest tests/eval -q: 342 passed; all external model/executor calls in runner tests are mocked).

## Remaining

- Claude obtains pilot approval and runs eval/configs/pilot-a.yaml and pilot-b.yaml on the host with the private root already configured, retains native/event logs and diagnostics, reports actual cost/plan observations and manually re-checks five A samples. D-2/SC-5 measured pilot results remain pending; preparation is not approval.
- Verify host installed CLI executor/controller/verifier/resume compatibility, actual nested guard, transport retry behavior, full event capture, aliases, process termination and sandbox behavior. Native pre-run plan observations may be unavailable and must stay null.
- The existing runner metadata.task_set_sha256 fingerprints the selected public/private inputs, whereas docs/eval-freeze.md records all 120. Compare identical selected-set A/B hashes and retain the full frozen source-population digest in the estimate; resolve any future requirement to use the full-set digest in every subset report with Role 1 before headline publication.
- Review structural helper extraction and submitted regression quality manually; behavioral graders do not certify those properties.
- Implement and host-verify two-session handoff execution/observations before including those tasks.
- Complete control-call accounting, complete done-claim denominator and hash-pinned paired local-minus-cheap_api parity. Missing observations remain undefined.
- Obtain explicit approval before full measurement; D-3 through D-5 remain pending. Frozen tasks and prepared configs do not establish executor quality.
- Run the full repository suite once before a future merge; this session ran only tests/eval, and did not stage or commit.

## Decisions

- Keep provider provenance in the existing pricing source string: the shared version-1 schema rejects extra pricing/tier fields and must remain unchanged.
- Use the supplied Claude host pricing fetch: network is disabled and the user provided exact official rates and provenance.
- Treat Standard short context as the documented CLI baseline assumption, override with explicit native/exec tier evidence and leave unsupported pricing null: a subscription and unknown rates must never become fabricated zero-dollar usage.
- Select sorted unused families by ordered type quotas, with bug-chunk-tail's ID as its missing family key: both baselines get a reproducible ten-family sample independent of pilot results.
- Choose zero retries and a 600-second per-process timeout: keep identical bounded initial call counts while allowing max effort more time than the legacy first-task deadline.
- Permit only the exact bundled pilot configs with their published estimate through existing batch preflight: ten-task preparation must be reviewable without relaxing arbitrary large-batch rejection; Claude still needs pilot approval.
- Preserve genuine timestamp boundaries for before/after: the first native observation can follow usage and must not be relabeled as a pre-run sample; no report-schema change is needed for diagnostics.
- Preserve existing selected-task hashing: changing shared provenance semantics is outside this preparation; the estimate separately records the frozen full-set identity.

## Verify commands

- .venv/bin/python -m pytest tests/eval -q
- git diff --check -- eval tests/eval state/STATUS-eval.md
- git diff --exit-code -- eval/tasks
- Host only, after approval: .venv/bin/python -m eval run --config eval/configs/pilot-a.yaml --out eval/reports/pilot-a/
- Host only, after approval: .venv/bin/python -m eval run --config eval/configs/pilot-b.yaml --out eval/reports/pilot-b/
- Before a future merge only: full repository test suite once.

## Do not touch

- Frozen eval/tasks/, historical reports, docs/eval-freeze.md, controller/, verifier/, plugin/, shared schemas/configuration, other roles' tests/STATUS files and concurrent changes; never share task contents with Role 3.
- .git: no staging, commits, history rewrites or file deletion in this session.
- No executor, controller, judge, nested Codex, live API/model, network, macOS sandbox-exec or private-root lookup in this preparation session.
- Never publish private locations, graders, references, mutants or equivalence rationales. Tests use synthetic roots under pytest temporary storage only.

## Assumptions

- The user's supplied 2026-10-22 Claude host fetch is authoritative for the exact prices; the page provides no price-list version/date, so v1 is a local snapshot version.
- CLI baselines use Standard short context absent conflicting evidence; the run does not infer exact subscription billing from API-equivalent rates.
- The historical one-task usage is only a planning proxy. Max uses more output; 2x and 5x hold input/cache fixed for illustration, not measured forecasts or spending caps.
- Zero retry/reinstruction limits are the pilot preparation choice; resuming an interrupted process needs a revised budget if it adds a call.
- The user-supplied freeze commit/digest and existing Role 1 record supersede the previous pending-freeze status; no private validation or frozen-file change is needed here.
- Native account snapshots may lack a true before or post-exit observation; null and timestamped last-in-run evidence are the honest available diagnostics, not an exact per-task plan charge.
