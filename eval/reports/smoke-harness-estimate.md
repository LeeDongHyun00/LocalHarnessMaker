# Harness smoke planning estimate — 2026-10-23

Planning numbers only, not measurements or spending caps. Config:
`eval/configs/smoke-harness.yaml`, two tasks, three sessions (both days counted),
Sol medium, seed 0, no transport retries, up to three executor attempts per day.
The harness has never run live. Host smoke follows this offline work.

| Component | Paid-call upper bound before generated judges | Expected planning USD |
| --- | ---: | ---: |
| Executor | 9 | 0.08777172 for three initial sessions; 0.26331516 at nine |
| Contract and handoff | 12 generations (3 contracts + 1 handoff, each up to 3) | 0.004 normally; 0.012 at bound |
| Judge | 3 generations per delegated criterion per verification | 0.001 per generation |

Executor proxy: pilot A $0.2925724 / 10 sessions = $0.02925724 per session.
Diagnostic pilot uses Codex 0.162; smoke pins 0.163.0-alpha.11.1.
Expected total before judges: $0.09177172 for initial sessions and one generation
per control command, or $0.27531516 at the stated generation bounds.

## Assumptions

- Each control generation uses 5,000 uncached input and 1,000 output tokens.
  Snapshot `openai-standard-short-2026-10-22-v1`: Luna $0.10 input,
  $0.01 cached input and $0.50 output per million; hence $0.001/generation.
  Internal regenerations and HTTP fallbacks each consume one of three slots.
- With J delegated criteria summed across day contracts, the total bound is
  `21 + 9*J` paid calls; executor 9, fixed control 12, judges at most 9*J.
  Expected judge USD assumes one generation per delegation ($0.001 each);
  at the bound it is $0.009*J. Actual generated contracts revise the guard.
- Each day of a two-session task costs one pilot session on average.
  Live compatibility, Role 4 delegation forwarding and real usage remain unmeasured.
- Usage limits are no longer a planning concern. Recovery may add paid calls.
