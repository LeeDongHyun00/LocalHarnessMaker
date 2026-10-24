# Full v3 A STOP-3 estimate — DRAFT, NOT APPROVED

Design date: 2026-10-25. [Config template](../configs/full-v3-a.yaml) is not
runnable. No tasks, grader validation, frozen digest, v3 CLI compatibility pin
or live calibration exists yet. This draft is not spending authorization.

## Scope and count

54 tasks = 45 single-session + 9 two-session tasks; S=54+9=63 required Sol
sessions. Sol gpt-6.1-sol medium, requested priority/Fast, seed 0. No plugin,
controls, model retries, hidden-test feedback or quality re-instruction.
Clarification notes require hook questions, so A receives none. Count: 63
executor workload units, zero Luna calls. The optional C arm is excluded.

## Offline pricing scenario

Use existing `openai-fast-short-2026-10-23-v1` in `eval/prices.yaml`, supplied
by earlier host evidence, without a network refresh. Pin the exact snapshot
bytes/hash before execution. Sol rates per million tokens: uncached input $4,
cached input $0.2, output $20. Assume per executor workload 20,000 uncached +
10,000 cached input and 4,000 output including reasoning/ledger or final-response
work once. Cached input is part of total input, not additional billable input.

Per workload = (20,000×4 + 10,000×0.2 + 4,000×20)/1,000,000 = $0.162000.

| Scenario | Executor units | Luna calls | USD |
| --- | ---: | ---: | ---: |
| Planned workload | 63 | 0 | 10.206000 |
| 2× token workload | 63 | 0 | 20.412000 |
| 5× token workload | 63 | 0 | 51.030000 |

These are workload scenarios, not measured costs, hard token caps or a forecast
of pass rate/cost_per_pass. Native evidence must confirm the actual model,
effort, tier and request context eligibility. Missing usage/rates remains null,
never free because CLI login is used. Include failed and invalid sessions.
Infrastructure restarts or extra execution require a revised estimate/approval.
Default 900-second executor and 30-second grading deadlines are draft choices;
pin per-task exceptions and recompute the bound before approval.

## Approval prerequisites

Freeze and validate all tasks and author-note/matcher data; approve a separate
disjoint calibration pilot; pin task selection/digest, runtime/plugin probe,
Codex version and pricing; revise workload assumptions from retained evidence.
Report the resulting bound and cost to the user before the >=10-call batch.
Neither the presence of this estimate file nor a config name approves a run.

## Assumptions

- The 54-task allocation and token workload are design choices, not measurements.
- A and H3 will use identical frozen initial prompts, task selection and executor
  settings; the hook-only clarification advantage is disclosed separately.
