# Full baseline planning estimate — 2026-10-23

Planning numbers, not measurements or spending caps. Full A is already running
in the main checkout. This worktree does not alter that running code. Full B
has never run and now selects only the 100 single-session tasks, in full A order,
under the user's decision 0007 scope. Both pin Codex 0.163.0-alpha.11.1,
seed 0, no harness, retries or reinstructions. No control model calls occur:
expected control USD is $0 for both baselines.

| Configuration | Paid executor calls upper bound | Pilot A session proxy USD | Expected executor USD |
| --- | ---: | ---: | ---: |
| A medium: 100 singles + 20 two-session | 140 | 0.02925724 | 4.0960136 |
| B max: 100 singles | 100 | 0.02925724 | 2.9257240 |
| Combined | 240 | | 7.0217376 |

Pilot A tokens: input 590,057, cached subset 513,664, output 8,842.
Pilot B: input 742,077, cached subset 659,328, output 19,902.
Snapshot `openai-standard-short-2026-10-22-v1` Sol rates per million:
input $2, cached $0.10, output $10. Cost formula:
`((input-cached)*2 + cached*0.10 + output*10)/1e6`.
Reasoning stays inside output once. The requested pilot-A session-average proxy
is used for both rows. Max effort can cost more: using pilot B instead gives
$4.3045080 for 100 B sessions and $8.4005216 combined. Pilot B is a diagnostic
alternative estimate, not a new measurement.

## Assumptions

- The requested A-average proxy does not adjust for B's max effort; its
  max-specific historical alternative is supplied above.
- Historical pilots used Codex 0.162.0-alpha.17.2; their per-session costs are
  diagnostic planning proxies for 0.163, not comparable quality measurements.
- Each day of a two-session A task has the average pilot-A session cost.
  Output, cache reuse and two-session work may differ; recovery adds calls.
- Usage limits are no longer a planning concern. No new model calls were made
  to prepare estimates. Harness control estimates and Luna token assumptions
  are in `full-harness-estimate.md` and `smoke-harness-estimate.md`.
