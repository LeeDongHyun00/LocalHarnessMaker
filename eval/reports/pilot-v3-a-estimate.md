# Pilot v3 A STOP-3 estimate — DRAFT, NOT APPROVED

2026-10-25: [pilot config](../configs/pilot-v3-a.yaml) reserves ten distinct
`cal-v3-` IDs under `eval/calibration-v3`. No calibration materials or private
validation exist yet. The draft is not runnable and does not authorize calls.

Selection rule, fixed before outcomes: two separate tasks each for bug fix,
feature plus test, constrained refactoring and multiple requirements; one each
for two-session and ambiguous requirements. IDs, implementations and fixtures
must be disjoint from all 54 evaluation tasks. This all-shape rule replaces
DESIGN's earlier two-per-single-session-shape plan. Do not substitute held-out
tasks. Report two-session and ambiguity results separately; the ten-task rate
cannot calibrate the 45-single-session target by itself.

Nine single-session tasks plus one two-session task require 11 Sol workloads,
zero Luna calls. A uses gpt-6.1-sol medium, requested priority/Fast, seed 0,
HARNESS_NESTED=1, no repair and no hook-mediated clarification reply.

Use the existing offline `openai-fast-short-2026-10-23-v1` snapshot, not a
network refresh. Sol rates per million tokens: $4 uncached input, $0.2 cached
input, $20 output. An assumed workload of 20k uncached + 10k cached input and
4k output costs $0.162000. Cached tokens are a subset of total input; reasoning
output is counted once. These are unmeasured scenarios, not spending limits.
Provider requests within an exec may exceed these workload planning units.
Retain native usage, failures and invalid costs; unknown accounting stays null.

| Scenario | 10 tasks / 11 sessions |
| --- | ---: |
| Assumed tokens | $1.782000 |
| 2× tokens | $3.564000 |
| 5× tokens | $8.910000 |

Author and independently validate the separate materials, pin CLI/model/tier,
prices and calibration digest, then obtain host pilot approval before this
11-workload batch. Manually review at least five A outputs and disclose grader
issues. No model quality, runtime, spending limit or full-run approval is inferred.
