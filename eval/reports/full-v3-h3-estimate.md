# Full v3 H3 STOP-3 estimate — DRAFT, NOT APPROVED

2026-10-25: the [config](../configs/full-v3-h3.yaml) contains the same ordered
54 unfrozen tasks as A, including nine two-session and nine ambiguous tasks.
Plugin mode is design only; current `harness=true` is the legacy loop and must
not be used as H3. Sol is gpt-6.1-sol medium, requested priority/Fast, seed 0;
hooks use pinned gpt-6-luna low, no automatic retry/regeneration/fallback.

| Component | Count |
| --- | ---: |
| Tasks N | 54 |
| Second sessions D | 9 |
| Required sessions S=N+D | 63 |
| Clarification reserve Q | 9 |
| Application-repair reserve R | 63 |
| Sol workloads S+Q+R | 135 |
| Luna calls 2S | 126 |
| Combined STOP-3 units | 261 |

Without reserves: 63 Sol workloads plus 126 Luna calls, 189 combined units.
Each completed native session allows two Luna calls total; clarification and
application repair reuse that budget. Ledger bookkeeping is included in the
executor token scenario, not another application repair or Luna call. Charge
actual usage only, not unused reserves. Question-only pauses may consume only
the requirements call; the table reserves completed sessions.

Use the existing offline `openai-fast-short-2026-10-23-v1` snapshot, not a
network refresh. Sol rates per million tokens: $4 uncached input, $0.2 cached
input, $20 output. An assumed workload of 20k uncached + 10k cached input and
4k output costs $0.162000. Cached tokens are a subset of total input; reasoning
output is counted once. These are unmeasured scenarios, not spending limits.
Provider requests within an exec may exceed these workload planning units.
Retain native usage, failures and invalid costs; unknown accounting stays null.

Luna rates per million tokens: $0.2/$0.02/$1 uncached/cached/output. The assumed
20k uncached + 2k cached input and 4k output costs $0.008040 per call.

| Scenario | 54 tasks / 63 sessions |
| --- | ---: |
| No clarification/repair reserves | $11.219040 |
| All clarification, no repair | $12.677040 |
| All reserves | $22.883040 |
| 2× tokens, all reserves | $45.766080 |
| 5× tokens, all reserves | $114.415200 |

This does not establish the <=15% cost-per-pass goal, latency or control-cost
targets. Host hook/provenance/pause-resume/ledger/accounting evidence, Claude
review, disjoint calibration and separate freeze remain pending. Pin plugin,
CLI/model/tier, prices and population; revise estimates from the pilot before
approval of ten-plus paid calls. No calls were made. Extra recoveries require a
new bound; measured runtime and a hard spending cap remain unavailable.
