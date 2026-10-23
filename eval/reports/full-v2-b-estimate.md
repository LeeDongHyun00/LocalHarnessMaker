# Full v2 b STOP-3 estimate — 2026-10-23

Offline preparation only; no model calls or run authorization. Config:
[full-v2-b.yaml](../configs/full-v2-b.yaml). The population is 100 tasks;
this selection has 80 tasks and 80 required executor sessions.
Sol uses max effort, priority (Fast), seed 0, Codex
0.163.0-alpha.11.1. calibration=false; all 100 metadata files are frozen=true
as of 2026-10-24. The user-supplied host public-plus-private population digest is
`12e7574905a6c6e4f7f49a85eacad38899fa5f0d221a3c93939a83ab13b6f041`.
A/harness select the full population; B already pins the same ordered 100 tasks
through task_population for its report's task-set digest. B executes only its
80 selected single-session tasks; their separate selected-task digest is
`3af558f5f0993bcac598c4f71772b14e884ea54a106a4988b2dd3d2f23a12b09`.
Obtain spending approval on the host before launching this batch.

## Call accounting

retry_limit=0. The executor bound is 80 calls; the control bound is
0 generation calls; the combined bound is 80 calls.
There are no control/judge calls or quality reinstructions. Recovery or operator continuation requires a revised bound.

## Fast pricing scenarios

Use the existing openai-fast-short-2026-10-23-v1 snapshot in eval/prices.yaml.
USD per million tokens: Sol input 4, cached input 0.2, output 20;
Luna input 0.2, cached input 0.02, output 1. Cached input is a subset of total
input. Reasoning tokens count once in output. The snapshot is the existing
user-supplied official-page/host observation; no network fetch occurred here.

Per executor planning workload: 20,000 uncached input + 10,000 cached input
+ 12,000 output tokens, costing $0.322000 per call.
Per control generation: 20,000 uncached + 2,000 cached + 4,000 output,
costing $0.008040 per slot. This gives $25.760000 at the stated
call bound; 2× and 5× token workload scenarios give $51.520000 and
$128.800000. These are planning scenarios, not measurements, hard token
limits or spending caps. Deadlines are 900 seconds per single-session process
and 1800 per process of a two-session task; grading deadline is 30 seconds.

## Assumptions

- Output/token budgets are workload assumptions, not calibration-derived
  forecasts. Max effort can spend more output/reasoning tokens than medium.
- Every actual process must retain native applied-tier evidence; an absent or
  different observed tier cannot be priced from this requested config.
- All failed, invalid, retry and fallback usage belongs in actual accounting;
  unknown usage/prices stay null. Host validation passed as supplied by the
  user; Role 1 publication of the supplied host digest remains pending.
  No live evaluation is run in this worktree.
