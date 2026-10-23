# Full harness planning estimate — 2026-10-23

Planning numbers only, not measurements or spending caps. Config
`eval/configs/full-harness.yaml` preserves full A's ordered 120-task population:
100 single-session plus 20 two-session tasks, 140 sessions. Sol medium,
seed 0, Codex 0.163.0-alpha.11.1, no transport retries, three attempts per day.
The harness has never run live; host smoke precedes measurement.

| Component | Paid-call upper bound before generated judges | Expected planning USD |
| --- | ---: | ---: |
| Executor | 420 | 4.0960136 for 140 initial sessions; 12.2880408 at 420 |
| Contract and handoff | 480 generations (140 contracts + 20 handoffs, each up to 3) | 0.320 normally; 0.960 at bound |
| Judge | 3 generations per delegated criterion per verification | 0.002 per generation |

Executor proxy: pilot A $0.2925724 / 10 = $0.02925724 per session.
Initial executor plus fixed control planning total: $4.4160136 before judges;
maximum-at-proxy total $13.2480408 before judges. These extrapolate historical
0.162 pilot tokens and cache reuse, not observed 0.163/harness consumption.

## Assumptions

- Each control generation uses 15,000 uncached input and 1,000 output tokens.
  Luna input $0.10, cached input $0.01 and output $0.50 per million in
  `openai-standard-short-2026-10-22-v1` gives $0.002 per generation.
- With J delegated criteria summed across all day contracts, the paid-call bound
  is `900 + 9*J`. Expected judge USD is $0.002 per actual delegation when one
  generation suffices; its bound is $0.018*J. Internal retries, regenerations
  and cheap_api fallback share each command's three-generation budget.
- Both days are budgeted separately; recovery can add calls and needs a revised
  estimate. Generated judge counts revise the guard before executor work.
- Usage limits are no longer a planning concern. Scope follows user-approved
  decision 0007: B has 100 single-session tasks; C uses 20 stratified tasks with
  user-filled templates; handoff compares harness with A. Local Gemma/QLoRA
  are dropped; parity is not measured.

Host control-call observations supplied by the user: judge 15,442 input / 58 output;
contract 14,603 input / 251 output. Planning rounds input to 15,000 and retains
1,000 output per generation; observed calls are examples, not run averages.
