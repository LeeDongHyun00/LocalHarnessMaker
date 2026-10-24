# Full v3 A STOP-3 estimate — DRAFT, NOT APPROVED

2026-10-25 construction checkpoint. The wrapped [config](../configs/full-v3-a.yaml)
lists the nine authored `bug_fix` candidates only. They are unfrozen; 45 tasks
remain. The design still calls for 54 tasks and 63 sessions. These counts do not
approve a partial or full evaluation. No model calls were made.

| Scope | Tasks | Two-session tasks | Sol workloads | Luna calls |
| --- | ---: | ---: | ---: | ---: |
| Current candidate list | 9 | 0 | 9 | 0 |
| Completed population, pending construction | 54 | 9 | 63 | 0 |

Sol is gpt-6.1-sol medium, requested priority/Fast, seed 0. A disables hooks and
has no repair or clarification continuation. Provider requests within one exec
may exceed these workload counts; actual native accounting must be retained.

The existing offline snapshot `openai-fast-short-2026-10-23-v1` supplies rates
per million tokens of $4 uncached input, $0.2 cached input and $20 output.
The unmeasured scenario remains 20,000 uncached + 10,000 cached input and 4,000
output tokens per workload: $0.162000. Cached tokens are included in total input;
reasoning/output is counted once.

| Scenario | Current 9 | Planned 54 |
| --- | ---: | ---: |
| Assumed tokens | $1.458000 | $10.206000 |
| 2× tokens | $2.916000 | $20.412000 |
| 5× tokens | $7.290000 | $51.030000 |

Disjoint calibration material, approved A-only pilot and manual review of five
outputs remain pending. The 60–85% single-session target is unmeasured. Complete
the remaining shapes, independent structure/derivation review and host validation
before freezing public/private inputs. Pin the CLI, model/tier, population and
price snapshot before execution. Refresh estimates from the pilot; report cost
and obtain approval before a batch of ten or more paid calls. Current estimates
are workload scenarios, with no hard spending limit or runtime measurement.
