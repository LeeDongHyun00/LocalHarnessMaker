## Done

- Drafted the v3 population and plugin-mode runner design, plus non-runnable A/H3 config and estimate templates; current runner behavior is unchanged (`.venv/bin/python` inline design audit: PASS, 54 unique task briefs, six shapes × nine, 18 domains × three, both templates rejected by strict loader, 63-session/261-budget-unit arithmetic).
- Preserved the earlier per-request context-pricing implementation as historical work; v2 harness recovery is stopped by the user's 2026-10-25 direction (prior session `.venv/bin/python -m pytest tests/eval -q`: 2115 passed in 388.16s; this is historical evidence, not this session's result).
- Verified the unchanged evaluation package and design-only scope; updated CHANGES and this handoff (`.venv/bin/python -m pytest tests/eval -q`: 2115 passed in 523.80s; `git diff --check`: exit 0; inline scope/STATUS audit: PASS, eight exact authorized paths, r5/v2, worktree .venv, six headings, zero staged/deleted paths, v3 DESIGN only; frozen inputs/reports/interfaces unchanged).

## Remaining

- Role 1/2: confirm the approved v3 artifact contract in AGENTS.md and referenced schemas, including question-only pause/resume, hook-write provenance, ledger injection receipts and report/workspace revision binding. This design deliberately leaves exact artifact paths there; do not implement a competing interface.
- After that contract and implementation authorization: implement plugin mode within existing CLI entry points, with production exec/resume compatibility evidence, isolated Codex homes, hook-only author-note replies, artifact audit/collection, Luna accounting and existing report artifact references. Current harness=true still means the legacy external loop.
- In a separately authorized authoring session: create disjoint calibration material and the 54 independent v3 tasks, references, external graders and author-note/matcher data; enforce every validation gate in eval/tasks-v3/DESIGN.md. No task files or private data exist for v3 in this worktree yet.
- On the host after a separate pilot estimate/approval: calibrate A on disjoint tasks, manually review five pilot outputs, then validate/freeze the held-out population and all matcher/scoring/runtime/pricing pins through Role 1. Do not tune on held-out outcomes.
- Replace draft task/version/hash placeholders, recompute STOP-3 bounds and report costs for user approval before A/H3 full runs; collect the preregistered 20-task human review. B is dropped; C is optional and separately scoped/estimated.
- Before merge, the host runs the full repository suite once. This session runs only tests/eval. Do not resume the stopped v2 harness recovery; historical v1/v2 evidence remains unchanged.

## Decisions

- Prioritize the approved 2026-10-25 v3 direction: it supersedes this STATUS file's former v2 harness-recovery queue, and leaves retained reports/frozen inputs intact.
- Use 54 distinct briefs, nine per shape and three per domain: independent structures address v2's homogeneous task ceiling while keeping 45 single-session tasks and nine two-session tasks (63 work sessions).
- Deliver a fixed author note only on an eligible hook-table question: A has no hook and gets no reply, even to executor prose; disclose and separately analyze this information advantage.
- Design against the artifact contract in AGENTS.md: Role 1 owns paths/schemas, and pause/resume/provenance confirmation is an implementation prerequisite rather than an interface edit here.
- Wrap both configs and leave tasks null: the existing strict loader must reject these not-approved templates and cannot accidentally run legacy harness orchestration as H3.
- Budget two Luna calls per logical work session with no model retries/fallback and one executable-failure retry only: H3's draft reserves 135 executor workloads plus 126 Luna calls, including nine clarification resumes; actual costs come from complete native/JSONL usage once.
- Record human-review results through existing artifact path/hash references: shared report metrics/schema/flags remain unchanged; pre-retry reports retain their assessed revision and missingness is disclosed.

## Verify commands

- `.venv/bin/python -m pytest tests/eval -q`
- `.venv/bin/python` inline design audit: task/shape/domain counts, template JSON/YAML and loader refusal, session/call/cost arithmetic.
- `.venv/bin/python` inline scope/STATUS audit: eight exact paths, branch r5/v2, local .venv, six ordered headings, no staged/deleted files and no v3 task inputs.
- `git diff --check`
- `git diff --exit-code -- eval/tasks eval/tasks-v2 eval/configs/full-v2-a.yaml eval/configs/full-v2-b.yaml eval/configs/full-v2-harness.yaml eval/prices.yaml schemas controller verifier plugin prompts AGENTS.md tests/eval`

## Do not touch

- Only eval/, tests/eval/ and state/STATUS-eval.md may change; use this r5/v2 worktree and its .venv. Do not edit other role paths or other checkouts.
- Frozen v1/v2 tasks, configs, retained reports, prices, report schema and existing CLI flags; no v3 task files, actual graders, references or author-note fixtures in this design session.
- Actual private grader roots and host runtimes: do not locate/access them. Never share task contents with Role 3 or expose graders to executor/control context.
- .git is read-only: no staging, commits, history rewriting or deletion. No network, model calls, nested Codex or macOS sandbox-exec.
- No live plugin install, spending approval, frozen digest, successful H3 execution or measured v3 quality/cost claim is established by these design files.
- Keep optional C templates for the user's authorship. Do not restart abandoned v2 harness recovery or reinterpret legacy report fields for v3 objects.

## Assumptions

- The user-approved v3 direction and 2026-10-24/25 host findings are the supplied design basis; this offline session makes no new host measurement. Existing tests may create their ordinary synthetic fixtures; no actual evaluation graders are authored or accessed.
- The exact 54-task balance, 20-task sample allocation, two-reviewer adjudication, matcher rules, question-pause lifecycle, deadlines and token workloads are explicit design choices requiring validation before implementation/freeze, not unspecified facts silently assumed.
- Role 1 is defining the artifact contract concurrently; this checkout still exposes the legacy interfaces. Exact plugin paths/schema details are referenced to AGENTS.md, without guessing or editing them.
- The two-call budget applies to a logical work session across clarification, deterministic retry and ledger continuations; these do not authorize additional Luna calls. Question-only pause behavior requires Role 1/2 confirmation.
- Fast snapshot openai-fast-short-2026-10-23-v1 is an existing offline planning reference; requested model/tier/context must be verified on the host before actual pricing. Draft USD scenarios are not spending caps or proof of the cost-per-pass goal.
