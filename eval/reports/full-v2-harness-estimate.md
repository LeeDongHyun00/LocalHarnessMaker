# Full v2 harness STOP-3 estimate — 2026-10-23

Offline preparation only; no model calls or run authorization. Config:
[full-v2-harness.yaml](../configs/full-v2-harness.yaml). The population is 100 tasks;
this selection has 100 tasks and 120 required executor sessions.
Sol uses medium effort, priority (Fast), seed 0, Codex
0.163.0-alpha.11.1. calibration=false; all 100 metadata files are frozen=true
as of 2026-10-24. The final public-plus-private digest awaits host computation
with `.venv/bin/python -m eval.freeze_v2 --private-root "$LHM_PRIVATE_GRADERS"`.
A/harness select the full population; B pins it through task_population. Obtain spending approval
on the host before launching this batch.

## Call accounting

retry_limit=0. The executor bound is 360 calls; the control bound is
420 generation calls; the combined bound is 780 calls.
The executor bound is 120 sessions × (reinstruction_limit 2 + 1) = 360.
Controls reserve 3 generation slots per command: 120 contracts plus 20
handoffs = 420 slots, including retries, regeneration and transport fallback.
The primary backend is codex_cli (Luna); fallback is accounted separately.
This bound excludes llm_judge criteria, which are generated dynamically:
for J judge criteria across the selected contracts, add 9J control slots
(3 generations × 3 verification rounds). Revise the bound after contracts
before approving a judge batch. Capacity recovery, operator restarts and
additional resumptions also need revised bounds.

## Fast pricing scenarios

Use the existing openai-fast-short-2026-10-23-v1 snapshot in eval/prices.yaml.
USD per million tokens: Sol input 4, cached input 0.2, output 20;
Luna input 0.2, cached input 0.02, output 1. Cached input is a subset of total
input. Reasoning tokens count once in output. The snapshot is the existing
user-supplied official-page/host observation; no network fetch occurred here.

Per executor planning workload: 20,000 uncached input + 10,000 cached input
+ 4,000 output tokens, costing $0.162000 per call.
Per control generation: 20,000 uncached + 2,000 cached + 4,000 output,
costing $0.008040 per slot. This gives $61.696800 at the stated
call bound; 2× and 5× token workload scenarios give $123.393600 and
$308.484000. These are planning scenarios, not measurements, hard token
limits or spending caps. Deadlines are 900 seconds per single-session process
and 1800 per process of a two-session task; grading deadline is 30 seconds.

## Assumptions

- Output/token budgets are workload assumptions, not calibration-derived
  forecasts. Max effort can spend more output/reasoning tokens than medium.
- Every actual process must retain native applied-tier evidence; an absent or
  different observed tier cannot be priced from this requested config.
- All failed, invalid, retry and fallback usage belongs in actual accounting;
  unknown usage/prices stay null. Host validation passed as supplied by the
  user; final digest computation and Role 1 publication remain pending. No live
  evaluation is run in this worktree.
