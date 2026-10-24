# 0011: Pinned Luna hooks for Sol's measured weaknesses

Date: 2026-10-25

Status: accepted by the user on 2026-10-25. Direction approved; interface version 3 schema set approved by the user on 2026-10-25 at 01:55 KST, exactly as proposed in docs/interfaces-v3.md and schemas/ at commit d82b87a, and frozen. The question-pause policy and v3 hook CLIs are published in AGENTS.md sections 3.2–3.3; no new hook wire fields.

## Context

The user stopped version 2 harness recovery and approved Claude's
[proposal](../handoff/2026-10-25-v3-direction.md) in full. The
[weekly host record](../weekly/2026-10-21-host-verification.md), sections dated
2026-10-24 and 2026-10-25, supplies these measurements. They were not rerun here.

| Finding | Recorded evidence and limits |
| --- | --- |
| Sol medium saturates ordinary tasks | Version 1 A passes all 100 single-session tasks. Final v1 A passes 117/120 overall; harness 119/120. Paired pass difference +0.017, CI -0.017 to 0.050. |
| The old harness adds cost without a measurable gain over medium | Final v1 cost per pass: A $0.0329, harness $0.0435; ratio 1.32, CI 1.26 to 1.39. It ties B on single-session pass rate at 77 percent of B's cost, which does not establish the original claim against both A and B. |
| Sol max adds cost without measured quality improvement on v2 | Proposal summary: B pass 0.949 against A 0.95, about 1.2 times A's cost. Host stop state: B 75 pass, 4 fail, 1 invalid (79 valid); cost awaits the per-request pricing fix. This is diagnostic, not a valid complete paired comparison. |
| Dense-spec A results expose false completion | V2 A regrade is valid: 95/100 pass, CI 0.90 to 0.99; $15.06 total, $0.1585 per pass; task false done 4/76 (0.053), attempts 1.20; handoff 19/20. Five failures share the reservations R2 ambiguity in 0010. Earlier A capture had handoff 18/19; it is not the final regrade denominator. |
| The contract harness lowers quality on v2 as run | 62 pass, 15 fail, 23 invalid; 62/77 valid tasks pass (0.805, CI 0.714 to 0.896), task false done 6/27 (0.222), handoff 11/15, attempts 2.17. $14.01 total, $1.89 control (13.5 percent); cost per pass remains undefined pending recovery/accounting. Invalidity prevents a headline paired quality estimate. Recovery was stopped; do not present the diagnostic subset as a completed valid run. |
| Failure mechanisms are concrete | Luna wrote a wrong regex containing `- ` and commands naming nonexistent root modules; judge-heavy criteria (proposal: 19–58 percent), retries on non-executable evidence, and transcript-reconstructed handoffs added errors. Sol followed wrong checks over the request, lost day-2 context and assumed through ambiguity. |

The original claim—cheap control plus contract and verification beats A and B
on cost per pass—is answered negatively by versions 1 and 2. Their evidence
motivates a different design; it is not proof that the new hooks work.

## Decision

Build a hook system for `gpt-6.1-sol` at medium effort, using deterministic
checks and two `gpt-6-luna` calls per completed session at low effort. Replace
contract generation with a visible requirements table and replace judge
opinions with a final-message claim audit. The executor writes its memory.
Keep useful runtime, isolation, accounting and evaluation infrastructure.

The user's three confirmations are recorded explicitly:

1. Pin the control model to `gpt-6-luna`; never silently substitute another model.
2. Drop baseline B for version 3; baseline C remains optional and user supplied.
3. Decision 0010 is record-only. It does not authorize grader, digest or analysis-population changes and does not block version 3.

## Six design principles

1. Executable oracles: enforce project tests, protected-file hashes, named-file existence, configured public API signature snapshots and input-immutability probes. Luna never writes regexes or commands. Missing deterministic coverage is reported as unverifiable.
2. The context owner writes memory: Sol writes the decision ledger; the hook validates it and injects it next session. Luna does not reconstruct memory from transcripts.
3. Evidence-based, single retry: re-instruct at most once, only for an executed deterministic check that fails. Judge opinions and unverifiable items never trigger repair.
4. Ask before assuming: Luna surfaces ambiguities as user questions before work. Hooks do not choose answers. A noninteractive evaluation must supply the task author's prepared clarification through the same visible interaction.
5. Pinned control model: SessionStart checks the installed Codex version, exact model-list entry and pinned pricing coverage. A missing/renamed/unverifiable pin disables Luna hooks with a visible advisory; no substitution.
6. Visible value: publish the requirements table, per-requirement completion evidence and decision ledger. Measure requirements precision and report accuracy alongside outcome metrics and user feedback.

## Hook responsibilities

| Hook (Codex event) | Component | Owner | Behavior | Luna call |
| --- | --- | --- | --- | --- |
| SessionStart | pin-check | Role 2 | Verify version, exact Luna model and price snapshot; mechanically validate/inject previous ledger; advise and disable Luna hooks on pin failure | none |
| UserPromptSubmit, first prompt | requirements table | Role 3 | Restate numbered requirements and open questions; code derives checks from request/configuration; show the table to the user | 1, low effort |
| PreToolUse, optional | protected-file guard | Role 2 | Block edits to files marked protected; version compatibility must be measured before enabling | none |
| Stop | completion report | Roles 4 and 3 | Execute deterministic checks/project tests; Luna audits final-message claims and evidence; allow one repair only for executed check failure | 1, low effort |
| Stop, after report | decision ledger | Role 4 | Request schema-shaped ledger from executor via Stop continuation; validate schema and identifiers against workspace | none |
| Stop, repeated failure | escalation advice | Role 2 | Recommend higher reasoning effort or human review in report; never change effort automatically | none |

Target each Luna call below 10 measured seconds and combined control cost well
under 2 percent of Fast executor cost. These are targets, not measurements.
The frozen hook budget counts failures and permits no regeneration or
transport fallback beyond the two calls (one per phase). Historical three-call
controller commands retain their old contracts outside this hook path.

## Interfaces and ownership

Role 1 publishes the frozen requirements, completion-report, ledger, pin-check
and per-call accounting schemas/examples approved on 2026-10-25 at 01:55 KST
from commit `d82b87a`. `schemas/VERSION` remains 3 and denotes the frozen set.
[The frozen interface](../interfaces-v3.md) defines exact artifact paths,
check derivation, accounting and retry/ledger sequencing. AGENTS.md section 3
publishes frozen hook CLIs and event mapping, including the unchanged-workspace
pending-question exit without claim audit or ledger continuation. Roles 2–5
start implementation now. Any later frozen v3 schema change requires a new
decision, explicit user approval and a version increment.

The ledger supersedes `handoff.schema.json` only on the new hook path. Retain
all old schemas, CLIs and reference artifacts for version 1/2 history. Retire
`llm_judge` on the new hook path; the historical contract/verdict/judgment
schemas remain unchanged. The runner's plugin mode runs Codex with the plugin
installed and collects artifacts; it does not orchestrate control calls.

## Evaluation and success criterion

Role 5 builds 50–60 held-out version 3 tasks: bug fixes, feature plus test,
constrained refactoring, dense requirements, two-session work and ambiguities
with author-prepared answers so asking can help. Each task has its own
structure, rather than sharing one template family. Validate references,
starters, mutation scores and shared lines, calibrate separately, then freeze
before any full run. Keep the existing private-grader access audit and
post-exit trusted grading.

Run only A (Sol medium alone) and H3 (Sol medium plus installed hooks), paired
on identical tasks, seeds, Codex version, executor settings and tier. C is
optional. Measure pass rate, task-level false done, cost per pass,
handoff_success and attempts, plus requirements-table precision (human sample
against private grading) and completion-report accuracy. Human review and
private grading remain outside controller/executor context. Use seeded paired
95 percent task-cluster bootstrap intervals and pinned API-equivalent pricing;
retain actual tier evidence and report all executor/control costs, including
failed calls and retries. Missing accounting stays unknown.

H3 must match A's pass rate within the paired interval, at least halve the
task-level false-done rate, and cost no more than 15 percent above A per passing
task. Any quality loss fails the design. A confidence interval containing zero
alone does not establish equivalence or excuse an observed quality loss.
No numeric noninferiority margin is authorized; report the paired difference,
interval and uncertainty without inventing one. Undefined rates or costs
cannot establish success.

## Freeze consequence and schedule

Versions 1 and 2 informed this design and remain historical evidence only.
Do not evaluate H3 on them, complete the stopped recovery, modify frozen tasks
or graders, or silently relabel old reports. Version 3 is the only evaluation
set for H3. A design change informed by frozen v3 outcomes requires a new
held-out version under the same anti-contamination rule.

| Dates (2026) | Work |
| --- | --- |
| 10/25–10/27 | Direction approval, Role 1 decision/plan/interfaces; Role 3 prompt/calibration design; Role 5 v3 task design |
| 10/28–11/03 | Role 2 pin-check/ledger injection; Role 4 report/retry; Role 5 build/freeze v3; live smoke on two non-evaluation projects |
| 11/04–11/08 | Full A and H3 runs (proposal estimate about two hours each at Fast tier); human report sample |
| 11/09–11/13 | Recovery, paired analysis and final document stating the original negative result across v1/v2/v3 |

Development ends 2026-11-13; presentation 2026-11-16. The estimate does not
approve a paid batch: Role 5 must report calibrated call/cost estimates first.

## Scope and verification

This publication records approval of the frozen schemas/examples and changes
owned documentation and lead validation tests only. It implements no hooks, controller, verifier or
runner and runs no model calls. Historical reports are untouched. Lead tests
and schema validation establish structural consistency, not live compatibility,
pin availability, timing, cost targets or evaluation success.

## Assumptions

- User approval and measurements come from the supplied proposal and host note; no independent live or private-grader measurement is claimed.
- Artifact paths, check mappings, two-call failure policy and ledger sequencing are approved interface choices; publication does not establish runtime implementation.
- The paired-interval wording supplies no equivalence margin. The report must retain uncertainty and the user's separate rule that any quality loss fails.
