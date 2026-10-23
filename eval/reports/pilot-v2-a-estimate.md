# Pilot v2 A STOP-3 estimate — 2026-10-23

Prepared offline. No executor, controller or judge calls were made. The batch
contains 16 single-session tasks and 4 two-session tasks: 24 planned executor
launches, zero control calls, retry_limit=0 and reinstruction_limit=0. Capacity
recovery or operator continuation can add calls and requires a revised bound.
Do not launch from this session. Host spending approval, calibration review and
candidate freeze are pending.

Configuration: gpt-6.1-sol, medium effort, priority service tier, seed 0,
codex-cli 0.163.0-alpha.11.1. Process deadlines are 900 seconds for singles and
1800 seconds for each process of a two-session task, not a combined two-day
budget. These are deadlines, not token or USD limits.

Historical pilot-A Standard-tier average was $0.02925724 per session, yielding
24 × $0.02925724 = $0.70217376 as an unadjusted planning proxy. V2 involves more
files and requirements, so 2×, 5× and 10× workload scenarios give Standard-tier
proxies of $1.40434752, $3.51086880 and $7.02173760. These are not spending caps
or measurements. The existing versioned snapshot covers Standard short-context
pricing only. Priority pricing is unavailable offline: the priority multiplier,
priority USD estimate and measured API-equivalent USD remain unknown until a
host-verified, versioned priority price snapshot is supplied. Do not apply the
Standard snapshot to priority calls. The runner records unknown costs as null.

## Assumptions

- The historical average is a workload proxy, not a v2 prediction; cache reuse,
  output and cross-session workload can differ substantially.
- Tier application must be confirmed by every executor process's native
  thread_settings_applied evidence. Missing/different tier invalidates the task.
- The pilot is unfrozen and cannot execute through the frozen-input runner yet.
  Commit, calibrate under an explicitly reviewed candidate freeze, then retain
  candidate hashes/outcomes if the design needs revision.
