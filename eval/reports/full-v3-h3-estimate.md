# Full v3 H3 STOP-3 estimate — DRAFT, NOT APPROVED

Design date: 2026-10-25. [Config template](../configs/full-v3-h3.yaml) is not
runnable; current `harness=true` is the old runner loop, not plugin mode.
No model calls, installation, private grader work or freeze is authorized.
Read [plugin-mode design](../README.md#version-3-plugin-mode--design-only-2026-10-25)
and [task design](../tasks-v3/DESIGN.md) with this estimate.

## Session, clarification and retry budget

N=54 tasks, D=9 two-session tasks, S=N+D=63 work sessions. Sol gpt-6.1-sol
medium and gpt-6-luna low, both requested priority/Fast, seed 0. The plugin
gets exactly two Luna calls per completed work session: requirements table and
completion claim audit. Deterministic checks, pin checks and ledger validation
make no Luna calls. There are no control retries, regeneration, LLM judgments,
handoff reconstruction or automatic transport fallback.

Allow Q<=9 fixed-author-note clarification resumes (one per ambiguous task),
only after the hook asks, and R<=63 one-executable-failure retries (one per
session). No other quality retry is permitted. A clarification resume reuses
the session/table; a check-failure continuation reuses the Luna audit. A
question-only pause must not spend the completion call early. Ledger writing
is Sol work through the plugin's ordinary Stop continuation and included in
executor tokens, not a third Luna call or runner-generated handoff.

| Budget component | Calculation | Upper bound |
| --- | --- | ---: |
| Required executor workloads | N+D | 63 |
| Clarification resume workloads | Q | 9 |
| Executable-failure retry workloads | R | 63 |
| All executor workloads | S+Q+R | 135 |
| Luna calls | 2S | 126 |
| Combined STOP-3 planning units | 3S+Q+R | 261 |

Before extra workloads the combined count is 189, or 198 including all nine
clarifications. The retry reserve accounts for extra Sol work even if Stop
continuation stays inside the initial exec process. Exec sessions themselves
can contain multiple provider requests: these are conservative budget units,
not measured request counts. Actual native usage is charged once per segment,
with no separate double charge for reserved internal continuations. Missing
or unexpected call records require investigation and retained costs; never
drop them to make the count match. Unused reserves are not billed spending.

## Offline pricing scenario

Use existing snapshot `openai-fast-short-2026-10-23-v1` in `eval/prices.yaml`,
from prior user-supplied host evidence; no network refresh here. Pin its bytes
and hash before a run. USD per million tokens:

| Model | Uncached input | Cached input | Output |
| --- | ---: | ---: | ---: |
| gpt-6.1-sol | 4 | 0.2 | 20 |
| gpt-6-luna | 0.2 | 0.02 | 1 |

Executor workload assumption: 20,000 uncached + 10,000 cached input and 4,000
output tokens = $0.162000. Include final response and routine ledger work.
Luna workload: 20,000 uncached + 2,000 cached input and 4,000 output tokens =
$0.008040. Cached input is a subset of total input; output includes reasoning
once. These deliberately conservative inherited workloads are not observed v3
usage or hard limits. The proposed under-10-second Luna latency and under-2%
control-cost target are unmeasured; this scenario does not establish them.

| Scenario | Sol units | Luna calls | USD |
| --- | ---: | ---: | ---: |
| No clarification/retry reserve used | 63 | 126 | 11.219040 |
| All clarification, no failure retry | 72 | 126 | 12.677040 |
| All clarification and single-retry reserves | 135 | 126 | 22.883040 |
| 2× tokens at all-reserves count | 135 | 126 | 45.766080 |
| 5× tokens at all-reserves count | 135 | 126 | 114.415200 |

The all-reserves arithmetic is 135×0.162 + 126×0.008040. Compare with A's
$10.206000 workload scenario, not a quality prediction. This conservative
budget does not imply H3 meets the approved <=15% cost_per_pass overhead goal;
that requires measured spending, pass counts and uncertainty from matched runs.
Unknown usage/pricing stays null. Include failed/invalid trials and any observed
protocol-violating extra calls, retaining actual model/backend/tier identity.

## Approval prerequisites

Role 1/2 must confirm the AGENTS.md artifact contract, question pause/resume,
two-call lifecycle, one-retry cap, ledger injection and supported plugin install.
Probe production hooks under the pinned CLI's exec/resume before a live run.
Then validate/freeze the 54 tasks plus author notes/matchers, pin build/config,
snapshot and population hashes, approve a separate disjoint pilot and revise
token estimates. Draft deadlines: 900 seconds per executor process, 30 seconds
for trusted grading; any per-task exceptions must be pinned with the estimate.
At >=10 calls report the exact revised scope/cost and obtain user approval.
Extra clarification turns, additional calls, transport recovery or operator
restarts require a new bound; no automatic recovery batch is included.

## Assumptions

- Artifact locations and schemas come from AGENTS.md; no exact paths or new
  hook/CLI interfaces are specified by this draft estimate.
- A logical work session includes clarification/ledger/check continuations but
  only one table and one claim audit; day 2 is a new session and adds two calls.
- Model/tier token workloads are offline scenarios. No spending approval or
  implementation/quality claim follows from creating these files.
