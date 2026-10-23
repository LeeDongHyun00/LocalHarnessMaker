# Weekly delivery plan

Source: the Notion page [“AI Project: GPT Operating Harness”](https://app.notion.com/p/3ea42c8af69c80de8915f0e7a422d367), last edited 2026-10-21, and repository role prompts 01–05. Dates below are in 2026. This plan retains the original Notion schedule as history and maps each role's dated deliverables onto it; discrepancies remain explicit below.

Interfaces were frozen early on **2026-10-21**, with `schemas/VERSION = 1` and approved decisions 0002–0004. The original freeze milestone remains October 24. Publication is not evidence that runtime implementation or measurement is complete. Development ends November 13; the final presentation is November 16.

Codex versions may change: record every run/session version, compare same-version reports only (mixed versions are diagnostic), probe hooks and run a one-task audit smoke after changes before large runs, stop on a mid-run change, and retain verified versions with evidence; see [decision 0006](decisions/0006-codex-version-policy.md).

## Approved scope and execution windows (2026-10-23)

[Decision 0007](decisions/0007-scope-cuts.md) supersedes conflicting scope and
measurement dates in the original milestones and weekly role plan below.
[Decision 0008](decisions/0008-task-set-v2.md) adds the version 2 schedule
below and takes precedence over conflicting measurement timing for that set.
Local Gemma 4 12B (Controller D-3) and QLoRA (Controller D-5) are dropped;
parity is reported as not measured, retaining its version 1 definition/field.
Usage is not a constraint; completeness of the results is the goal. Continue the remaining work to completion
up to, but not including, the local LLM stage. An OPENAI_API_KEY for executor
codex exec is only a fallback if the subscription cap blocks a run.

| Window | Approved measurements |
|---|---|
| W1, through 10/30 | Harness-mode smoke and full A |
| W2, through 11/06 | Full harness and C on a stratified 20-task subset: 5 per task type, 20 different families. The user fills the 20 templates once; Claude does not, preserving evaluator independence. Compare harness and C on the same 20 tasks, paired. |
| W3, through 11/13 | B on the 100 single-session tasks only and final analysis. Compare handoff_success between harness and A. |

## Version 2 evaluation schedule (approved 2026-10-23)

Version 1 stays frozen and its results remain reported. The user-supplied
full A result (`eval/reports/full-a`, commit `a21eda2`, codex-cli
`0.163.0-alpha.11.1`) passed 115/120, including 100/100 single-session tasks;
this motivates a harder, separate set rather than changing version 1.
The execution windows below use decision 0007's W2/W3 deadlines, rather
than the historical weekly headings that follow.

| Window | Work and gate |
|---|---|
| W2, through 11/06 | Role 5 builds `eval/tasks-v2/` with `v2-` IDs and separate private graders; validates that every hidden test follows from the public prompt; calibrates on A only toward roughly 30–70% pass rate. Adjust difficulty at the design level, never select/drop tasks based on individual pilot outcomes. Then freeze with a separate record and digest before any full run. Role 1 publishes the supplied freeze evidence. |
| W2 and W3, through 11/13 | Run A, B and the harness fresh on frozen version 2, retaining decision 0007's comparison scopes. No harness change after the freeze may use version 2 results. |
| By 11/13 | Finish final analysis; report version 1 and version 2 separately, disclose which version 1 runs informed the 10/23 harness fixes, and retain tier evidence and pinned Standard-rate API-equivalent costs. |

Version 2 uses multi-file packages, explicit requirements/constraints and
two-session work that depends on day-1 decisions without user restatement
on day 2. Task count and exact freeze date await Role 5's evidence.
Codex development jobs and every version 2 evaluation configuration use
`service_tier = "priority"` (Fast). Record and verify the effective tier
from native session settings and state it in reports for like-for-like
comparisons. Pinned Standard rates remain the API-equivalent cost basis.
This plan records policy, not completed tier configuration or evaluation.

## Milestones (original dates; decisions 0007–0008 take precedence)

| Date | Notion milestone | Role deliverables / dependencies |
|---|---|---|
| 10/24 | Freeze contract schema, handoff format and verifier interface; subsequent changes require approval | Lead D-2 (already published 10/21); Plugin D-1 hook evidence/verified versions; Eval D-1 minimal noninteractive runner |
| 10/27 | Freeze evaluation set; baselines A and B measured | Lead D-3 plan, direction decision and task-set hash record; Plugin D-2 stub loop; Controller D-1 backends/effort rules; Verifier D-1 mechanical rules; Eval D-2 freeze and pilot-gated A/B runs |
| 11/03 | Luna input → contract approval → execution → verification → re-instruction loop; baseline C measured | Plugin D-3 real CLI connection/retry state; Controller D-2 contract generation/retrieval; Verifier D-2 claims/re-instruction/sandbox; Eval D-3 C and first system report |
| 11/10 | Two-session handoff demo and plugin packaging; local substitution dropped (0007) | Plugin D-4; Controller D-3 dropped (0007) and D-4 (11/10); Verifier D-3 (11/06) and D-4 (11/10); Eval D-4 handoff/human review; parity not measured |
| 11/13 | Development complete; comparison results final | Lead D-5 install-to-demo docs; Plugin D-5 recording scenario; Eval D-5 final report; Controller D-5 dropped (0007) |
| 11/16 | Final presentation | Lead D-6 slides/Q&A due 11/15; rehearsal 11/14–11/15 and final checks 11/16 |

## Week 1: 10/21–10/27 — Replanning, design and evaluation set

Reframe the two target weaknesses, exclude defensive-wording suppression, establish interfaces and the task set, secure the in-scope model environments, and confirm noninteractive evaluation is viable.

| Role | Work and dated deliverables |
|---|---|
| 1 Tech Lead | D-1 repository skeleton, root configuration, CI and STATUS files (10/22); D-2 schemas/examples/interfaces and version freeze (10/24, completed early 10/21); D-3 this plan, decision 0005 and `docs/eval-freeze.md` after Role 5 sends the hash (10/27); D-4 integration review (10/27). |
| 2 Plugin | D-1 verify three hooks, context injection, Stop continuation and exec behavior with logs; record verified Codex versions and probe evidence (10/24). D-2 reproducible stub loop and demo script (10/27). Role 1 publishes the hook contract. |
| 3 Controller | D-1 primary logged-in `codex_cli` Luna backend, same-model HTTP fallback, mocked golden tests, shared call budget/child guard, analyzer and effort rules v1 (10/27). Keep evaluation tasks out of case/template development. |
| 4 Verifier | D-1 command/file/regex rules, verdict output and pass/fail golden fixtures (10/27). Design checklist and claim/evidence checks against frozen interfaces. |
| 5 Evaluation | D-1 one-task runner with external private graders and post-exit grading (10/24); confirm hooks under exec using Role 2 evidence. D-2 freeze at least 100 single-session tasks across four types plus 20 two-session tasks, each with private graders; send hash to Lead (10/27). Run the 10-task A/B pilot, report cost, obtain approval before full runs. |

Week output: revised scope, frozen interfaces, frozen task set and A/B measurements. Private graders remain outside public workspaces; audit retained executor logs and grade only after executor/spawned work exits. A clean audit records no observed access, not read isolation.

## Week 2: 10/28–11/03 — Complete the Luna loop

| Role | Work and dated deliverables |
|---|---|
| 1 Tech Lead | D-4 integration review on 11/03; check CLI compatibility, interface blockers and scope/schedule risks. |
| 2 Plugin | D-3 connect real controller/verifier CLIs, preserve loop state, configurable retry limit defaulting to 3 (11/03). Skill presents the contract and waits for approval, then reports criterion evidence. |
| 3 Controller | D-2 complete contract generator/CLI, prompt template v1, verified-case JSONL storage and BM25 top-three retrieval (11/03). Compute tokens, effort and costs in code. |
| 4 Verifier | D-2 claim/evidence detection, bounded re-instruction, isolated command execution and complete CLI; connect to Role 2 hooks (11/03). |
| 5 Evaluation | D-3 user-filled static-template baseline C on the approved stratified 20-task subset, paired with the harness on those tasks; first proposed-system measurement and report v1 (11/03). Record primary CLI transport and HTTP fallback separately with API-equivalent accounting. |

Week output: a working approved-contract loop in Codex and first comparison against A (Sol medium), B (Sol max) and C (Sol medium with static template).

## Week 3: 11/04–11/10 — Handoff and packaging

| Role | Work and dated deliverables |
|---|---|
| 1 Tech Lead | D-4 integration review on 11/10; coordinate handoff evidence and packaging readiness. |
| 2 Plugin | D-4 SessionStart handoff injection, installer with version check and `--check`, packaging, and skill-only fallback when hooks fail (11/10). |
| 3 Controller | D-3 local Gemma backend dropped by decision 0007. D-4 handoff generator, judge, complete CLI and 30-fixture comparison of CLI/API schema validity, assumptions, latency and cost (11/10). |
| 4 Verifier | D-3 handoff validation, judge delegation and 20-report human-review sampling (11/06). D-4 fix observed misjudgments and publish `verifier/RULES.md` (11/10). |
| 5 Evaluation | D-4 two-session handoff success comparing harness with A and table of 20 human-reviewed samples (11/10). Compare matched runs with pinned task set, seed and executor settings, and the same recorded Codex version. |

Week output: two-session demo, packaged plugin and handoff measurements. Local control and QLoRA are dropped by decision 0007; parity is not measured.

## Week 4: 11/11–11/16 — Final comparison, documentation and presentation

| Role | Work and dated deliverables |
|---|---|
| 1 Tech Lead | D-5 README install-to-demo path, architecture and demo scenario including two sessions, with fresh-clone evidence (11/13). D-6 slides and Q&A (11/15): static templates, reasoning effort, local models and built-in Codex features. Coordinate rehearsal 11/14–11/15 and presentation 11/16. |
| 2 Plugin | D-5 demo script and screen-order recording scenario (11/13); support rehearsal of the packaged plugin. |
| 3 Controller | Stabilize measured failures by development end. D-5 QLoRA work is dropped by decision 0007. |
| 4 Verifier | Correct remaining comparison/human-review errors before 11/13; support final verification evidence. No additional dated role deliverable after D-4. |
| 5 Evaluation | D-5 final report, tables/charts, task-type breakdowns, sample sizes and bootstrap confidence intervals (11/13). Final A/B/C versus Luna harness comparisons within the approved task scopes; include false-done rate, cost per pass, attempts and handoff success. Report parity as not measured. Supply presentation numbers from retained reports. |

Notion reserves 11/11–11/13 for final experiments, human checks, fixes and documentation, 11/14–11/15 for slides/script/Q&A/demo rehearsal, and 11/16 for final checks and presentation. Decision 0007 already drops optional training and local-control work.

## Disagreements

| Topic | Notion schedule | Role prompt |
|---|---|---|
| Input analyzer | Week 1 designs difficulty-to-effort rules; week 2 implements token counting, difficulty, effort selection and cost calculation. | Controller D-1 requires `analyze.py` effort rules v1 by 10/27, and its First task starts token counting/cost implementation immediately. Both timings are retained. |
| Optional QLoRA | Week 3 lists an optional first trial; the model strategy and week 4 schedule place optional training in week 4. | Resolved by decision 0007 on 10/23: Controller D-5 is dropped, as is D-3 local control. |

## Assumptions

- The supplied export is the design baseline for this document; no live Notion access or external factual verification is implied.
- Dates are copied as calendar dates; weekday labels are omitted. Deliverables shown here are commitments, not completion claims, except the recorded early interface freeze.
- Role support work in week 4 maps Notion's shared stabilization/rehearsal tasks to existing ownership; it creates no new interface or role deliverable.
- D-3 and the task-set freeze record were completed earlier; no new measurement is inferred from this scope update.
