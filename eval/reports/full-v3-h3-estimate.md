# Full v3 H3 STOP-3 estimate — DRAFT, NOT APPROVED

2026-10-25 construction checkpoint. The wrapped [config](../configs/full-v3-h3.yaml)
lists the same nine unfrozen `bug_fix` candidates as A. There are no ambiguous or
two-session tasks in this partial inventory. The completed population remains
54 tasks, including nine ambiguous and nine two-session tasks. No calls were made.
The current runner's `harness=true` remains the legacy loop; do not unwrap this
config as a substitute for plugin mode.

Let S=N+D required work sessions, Q eligible ambiguity clarification resumes,
and R<=S deterministic-failure repair workloads. Each completed session allows
two gpt-6-luna low calls, with no retries/fallback. A clarification or application
repair reuses that session's hook artifacts. Ledger continuation work is included
in the executor token scenario, without adding another Luna call.

| Component | Current candidate list | Planned completed population |
| --- | ---: | ---: |
| Tasks N | 9 | 54 |
| Second sessions D | 0 | 9 |
| Work sessions S | 9 | 63 |
| Clarification reserve Q | 0 | 9 |
| Application-repair reserve R | 9 | 63 |
| Sol workloads S+Q+R | 18 | 135 |
| Luna calls 2S | 18 | 126 |
| Combined STOP-3 units | 36 | 261 |

Without reserves the current list has 9 Sol workloads plus 18 Luna calls, or 27
combined units. Exec sessions may make several provider requests; these are
workload planning units. Charge actual native usage once, retain failed/invalid
costs, and do not bill unused reserves. Unknown usage/pricing stays null.

Use the existing offline `openai-fast-short-2026-10-23-v1` snapshot. Sol rates per
million tokens are $4/$0.2/$20 for uncached/cached/output; Luna rates are
$0.2/$0.02/$1. The unmeasured Sol workload of 20k uncached + 10k cached input
and 4k output costs $0.162000. Luna's 20k uncached + 2k cached input and 4k
output costs $0.008040. Reasoning tokens are included once in output.

| Scenario | Current 9 | Planned 54 |
| --- | ---: | ---: |
| No clarification/repair reserves | $1.602720 | $11.219040 |
| All clarification, no repair | $1.602720 | $12.677040 |
| All reserves | $3.060720 | $22.883040 |
| 2× tokens, all reserves | $6.121440 | $45.766080 |
| 5× tokens, all reserves | $15.303600 | $114.415200 |

These are spending scenarios, not evidence of the <=15% cost-per-pass goal or
the latency/control-cost targets. Deadlines remain 900 seconds per executor
process and 30 seconds per grading run, subject to host validation.

The user supplied approval/freeze of interface v3 on 2026-10-25. Production
plugin implementation, provenance, question pause/resume, ledger injection and
exec/resume compatibility still require host evidence. Disjoint pilot approval,
all 54 authored tasks, independent review and task freeze remain pending. Pin the
plugin/config/CLI/model/tier/prices and revise token estimates before seeking
spending approval. Any batch of ten or more paid calls, including this partial
H3 scope, requires its estimate reported first. Extra recoveries need a new bound.
