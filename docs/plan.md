# Weekly delivery plan

Source: the Notion page [“AI Project: GPT Operating Harness”](https://app.notion.com/p/3ea42c8af69c80de8915f0e7a422d367), last edited 2026-10-21, and repository role prompts 01–05. Dates below are in 2026. This plan retains the Notion schedule and maps each role's dated deliverables onto it; discrepancies remain explicit below.

Interfaces were frozen early on **2026-10-21**, with `schemas/VERSION = 1` and approved decisions 0002–0004. The original freeze milestone remains October 24. Publication is not evidence that runtime implementation or measurement is complete. Development ends November 13; the final presentation is November 16.

Codex versions may change: record every run/session version, compare same-version reports only (mixed versions are diagnostic), probe hooks and run a one-task audit smoke after changes before large runs, stop on a mid-run change, and retain verified versions with evidence; see [decision 0006](decisions/0006-codex-version-policy.md).

## Milestones

| Date | Notion milestone | Role deliverables / dependencies |
|---|---|---|
| 10/24 | Freeze contract schema, handoff format and verifier interface; subsequent changes require approval | Lead D-2 (already published 10/21); Plugin D-1 hook evidence/verified versions; Eval D-1 minimal noninteractive runner |
| 10/27 | Freeze evaluation set; baselines A and B measured | Lead D-3 plan, direction decision and task-set hash record; Plugin D-2 stub loop; Controller D-1 backends/effort rules; Verifier D-1 mechanical rules; Eval D-2 freeze and pilot-gated A/B runs |
| 11/03 | Luna input → contract approval → execution → verification → re-instruction loop; baseline C measured | Plugin D-3 real CLI connection/retry state; Controller D-2 contract generation/retrieval; Verifier D-2 claims/re-instruction/sandbox; Eval D-3 C and first system report |
| 11/10 | Local controller substitution, two-session handoff demo, plugin packaging | Plugin D-4; Controller D-3 (11/06) and D-4 (11/10); Verifier D-3 (11/06) and D-4 (11/10); Eval D-4 parity/handoff/human review |
| 11/13 | Development complete; comparison results final | Lead D-5 install-to-demo docs; Plugin D-5 recording scenario; Eval D-5 final report; Controller optional D-5 only if time remains |
| 11/16 | Final presentation | Lead D-6 slides/Q&A due 11/15; rehearsal 11/14–11/15 and final checks 11/16 |

## Week 1: 10/21–10/27 — Replanning, design and evaluation set

Reframe the two target weaknesses, exclude defensive-wording suppression, establish interfaces and the task set, secure model/GPU environments, and confirm noninteractive evaluation is viable.

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
| 5 Evaluation | D-3 human-filled static-template baseline C, first proposed-system measurement and report v1 (11/03). Record primary CLI transport and HTTP fallback separately with API-equivalent accounting. |

Week output: a working approved-contract loop in Codex and first comparison against A (Sol medium), B (Sol max) and C (Sol medium with static template).

## Week 3: 11/04–11/10 — Local controller, handoff and packaging

| Role | Work and dated deliverables |
|---|---|
| 1 Tech Lead | D-4 integration review on 11/10; coordinate local substitution, handoff evidence and packaging readiness. |
| 2 Plugin | D-4 SessionStart handoff injection, installer with version check and `--check`, packaging, and skill-only fallback when hooks fail (11/10). |
| 3 Controller | D-3 serve Gemma 4 12B via vLLM or llama.cpp with constrained JSON output; golden tests and memory/serving documentation (11/06). D-4 handoff generator, judge, complete CLI and 30-fixture comparison of CLI/API/local schema validity, assumptions, latency and cost (11/10). |
| 4 Verifier | D-3 handoff validation, judge delegation and 20-report human-review sampling (11/06). D-4 fix observed misjudgments and publish `verifier/RULES.md` (11/10). |
| 5 Evaluation | D-4 local-controller measurement, two-session handoff success and table of 20 human-reviewed samples (11/10). Compare matched runs with pinned task set, seed and executor settings, and the same recorded Codex version. |

Week output: interchangeable local control, two-session demo, packaged plugin, parity and handoff measurements. Notion also lists an optional first QLoRA trial here; see Disagreements.

## Week 4: 11/11–11/16 — Final comparison, documentation and presentation

| Role | Work and dated deliverables |
|---|---|
| 1 Tech Lead | D-5 README install-to-demo path, architecture and demo scenario including two sessions, with fresh-clone evidence (11/13). D-6 slides and Q&A (11/15): static templates, reasoning effort, local models and built-in Codex features. Coordinate rehearsal 11/14–11/15 and presentation 11/16. |
| 2 Plugin | D-5 demo script and screen-order recording scenario (11/13); support rehearsal of the packaged plugin. |
| 3 Controller | Stabilize measured failures by development end. Optional D-5 QLoRA case-library training and quality comparison with/without retrieved examples (11/13), only if time remains. |
| 4 Verifier | Correct remaining comparison/human-review errors before 11/13; support final verification evidence. No additional dated role deliverable after D-4. |
| 5 Evaluation | D-5 final report, tables/charts, task-type breakdowns, sample sizes and bootstrap confidence intervals (11/13). Final A/B/C versus Luna/local runs; include false-done rate, cost per pass, attempts, handoff success and parity. Supply presentation numbers from retained reports. |

Notion reserves 11/11–11/13 for final experiments, human checks, fixes and documentation, 11/14–11/15 for slides/script/Q&A/demo rehearsal, and 11/16 for final checks and presentation. Optional training is the first scope cut if time slips.

## Disagreements

| Topic | Notion schedule | Role prompt |
|---|---|---|
| Input analyzer | Week 1 designs difficulty-to-effort rules; week 2 implements token counting, difficulty, effort selection and cost calculation. | Controller D-1 requires `analyze.py` effort rules v1 by 10/27, and its First task starts token counting/cost implementation immediately. Both timings are retained. |
| Optional QLoRA | Week 3 lists an optional first trial; the model strategy and week 4 schedule place optional training in week 4. | Controller D-5 is optional and due 11/13. No training date is moved or chosen here. |

## Assumptions

- The supplied export is the design baseline for this document; no live Notion access or external factual verification is implied.
- Dates are copied as calendar dates; weekday labels are omitted. Deliverables shown here are commitments, not completion claims, except the recorded early interface freeze.
- Role support work in week 4 maps Notion's shared stabilization/rehearsal tasks to existing ownership; it creates no new interface or role deliverable.
- `docs/eval-freeze.md` waits for Role 5's frozen task-set hash; no hash or measurement is inferred from public task drafts.
