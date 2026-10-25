# Full v3 A STOP-3 estimate — DRAFT, NOT APPROVED

2026-10-25: the [config](../configs/full-v3-a.yaml) contains all 54 unfrozen
tasks in lexicographic ID order, identical to H3. There are 45 single-session
and nine two-session tasks: 63 required sessions, 63 Sol workloads, zero Luna
calls. Sol is gpt-6.1-sol medium, requested priority/Fast, seed 0. A sets
HARNESS_NESTED=1 and has no repair or clarification continuation.

Use the existing offline `openai-fast-short-2026-10-23-v1` snapshot, not a
network refresh. Sol rates per million tokens: $4 uncached input, $0.2 cached
input, $20 output. An assumed workload of 20k uncached + 10k cached input and
4k output costs $0.162000. Cached tokens are a subset of total input; reasoning
output is counted once. These are unmeasured scenarios, not spending limits.
Provider requests within an exec may exceed these workload planning units.
Retain native usage, failures and invalid costs; unknown accounting stays null.

| Scenario | 54 tasks / 63 sessions |
| --- | ---: |
| Assumed tokens | $10.206000 |
| 2× tokens | $20.412000 |
| 5× tokens | $51.030000 |

Claude's independent host review, disjoint calibration pilot/materials, manual
review of five pilot outputs and separate task freeze remain pending. Pin the
CLI/model/tier, population and pricing bytes before running. Refresh estimates
from the pilot and report before any ten-plus paid-call batch. No calls were
made or authorized by this draft; measured runtime and hard cost cap are absent.
