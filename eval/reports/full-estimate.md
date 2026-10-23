# Full baseline STOP-3 estimate — 2026-10-22

Full runs remain on hold. Claude must host-verify the two-session smoke, review
pilot/audit evidence and ask the user again before either full configuration runs.
No executor or model call was made to prepare these files.

Both full configurations list all 120 frozen tasks in lexicographic ID order,
from freeze commit `7cdaf3b`, population digest
`b78913b04280f6696d419d2afdc96b152675973d82f05199ddef848986285d1f`.
Each uses seed 0, `codex-cli 0.163.0-alpha.11.1`, harness off, zero retries and
zero reinstructions. Timeouts are 600 seconds per single-session process,
1200 seconds per two-session process, and 20 seconds per grading process.
There are 100 single-session tasks and 20 two-session tasks: **140 executor
sessions per configuration**, 280 combined. Recovery may add billed attempts
and requires a revised estimate. No controller calls occur in these baselines.

Prices come from the existing offline snapshot
`openai-standard-short-2026-10-22-v1` in `eval/prices.yaml`: Sol input $2,
cached input $0.10, output $10 per million tokens. Cached input is a subset;
reasoning is charged within output once. These are API-equivalent USD, not a
subscription invoice. No current pricing lookup was performed.

Pilots used `codex-cli 0.162.0-alpha.17.2` and are diagnostic for 0.163 runs,
not a comparable quality baseline. The supplied 0.163 host hook probe passed;
a one-task audit compatibility smoke is still required before a large run.

The retained pilot report executor-call totals provide a planning proxy:

| Configuration | Pilot input | Pilot cached subset | Pilot output | Pilot USD (10 sessions) | Full sessions | Estimated full USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| full-a, Sol medium | 590,057 | 513,664 | 8,842 | 0.2925724 | 140 | 4.0960136 |
| full-b, Sol max | 742,077 | 659,328 | 19,902 | 0.4304508 | 140 | 6.0263112 |
| Combined | | | | | 280 | 10.1223248 |

Formula: `((input - cached) * 2 + cached * 0.10 + output * 10) / 1e6`.
Full estimates multiply the ten-session pilot totals by 14. Pilot-B costs remain
useful accounting observations even while its audit/quality requires host review.
The estimates are not spending caps: two-session work, retries, output length and
cache reuse can differ substantially. With the same pilot tokens and no cache
reuse the combined estimate is $41.323912.

User-supplied pilot plan deltas are approximately 0.4 percentage points per
medium task and 0.6 per max task. Assuming each fresh session has the same
average consumption gives about **56 percentage points for A**, **84 for B**,
**140 combined**. These linear projections do not account for quota windows or
resets. Rounded account-wide snapshots and concurrent activity prevent exact
per-task attribution; absent true before/after observations remain null.

## Assumptions

- The retained pilot token/cost totals and user-supplied plan deltas are planning
  inputs, not new measurements or evidence that full quality will match pilots.
- Each session of a two-session task is budgeted as one pilot session; no pilot
  has measured the two-session distribution yet.
- Standard short-context rates apply only where supported by retained evidence.
- Claude owns host validation and requesting full-run approval. This estimate
  and the presence of configurations do not authorize execution.
