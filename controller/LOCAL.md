# Controller scope and host measurements

Decision [0007](../docs/decisions/0007-scope-cuts.md), approved 2026-10-23,
drops D-3 (local Gemma 4 12B, serving and constrained-decoding measurement) and
D-5 (QLoRA). Neither is pending work. Local-control comparison and parity are
not measured. The version 1 `local` selector, disabled configuration and
fail-closed adapter behavior remain unchanged; there is no cloud fallback from
local. Existing mock tests are protocol evidence only.

Unknown usage or prices remain unknown. Under the unchanged version 1 contract
schema, a started CLI call with unknown usage followed by successful HTTP
fallback still produces honest exit 2. Integration review 1 recommends keeping
this behavior; no interface revision is planned.

## D-4 primary-backend measurement

Run from the repository root on the host. This session prepared the command but
did not execute live calls. First preview its call count and cost estimate:

```sh
.venv/bin/python -m controller.measure_contracts --out /tmp/controller-d4.json
```

Without `--i-have-approval` it prints the plan and refuses to start (exit 1,
no model calls and no summary). After approval, Claude can run:

```sh
.venv/bin/python -m controller.measure_contracts --out /tmp/controller-d4.json --i-have-approval
```

This runs the existing `controller contract` CLI implementation with
`--backend codex_cli`, `--handoff none` and the curated seed case directory on
each of the 30 authored requests in `tests/controller/fixtures/requests-v1.json`.
Only request text is passed, never fixture answers. An internal backend factory
uses production routing with HTTP fallback disabled in memory. Each contract
command allows at most three generations total, including schema retries and
the single targeted quality regeneration. Transport failure stops the sample;
there are no HTTP or local calls. Production routing and CLI flags are unchanged.
Child Codex processes
retain the existing copied `HARNESS_NESTED=1` environment. Run only on a host
with a logged-in CLI and compatible installed Codex version.

The printed maximum is 90 calls and the estimate is USD 0.198000 with the current
price snapshot,
17,000 input and 1,000 output tokens per call, without cache discounts. These
planning token allowances are not limits; framing, output length and actual
usage can differ. Override them with `--estimated-input-tokens` and
`--estimated-output-tokens`. The estimate uses the versioned API-equivalent
snapshot in `controller/prices.yaml`, not subscription billing. It prints before
any call, including approved runs. No HTTP API key is required. HTTP cheap_api
is not measured in this run; its fallback verification still requires a key.

One JSON summary contains per-sample schema validity, assumptions count, counts
of command/file_exists/regex/llm_judge criteria, exit code, and latency and cost
from all `control_call` log records, including failed generations. Records retain
backend/model/pricing identity. Each sample reports `quality_gate_fired` and
`generations`; the production gate emits an observation before regeneration or
rejection, including rejection when no slot remains. `quality_gate_firings` counts
samples encountering the gate once each, even if a repeated deficiency causes
rejection. Totals include generations, USD, schema pass rate, assumptions,
criterion counts and llm_judge share among schema-valid contracts. Failed
contracts have null counts;
missing accounting propagates to null total cost, rather than zero. Failed calls
with measured usage remain in costs. Latency totals sum control-call latency,
not wrapper wall time. An existing summary path is refused. Temporary inputs
and outputs are not retained or added to the case library; this measures the
contract generator and does not collect training data. A completed measurement
returns 0 even if some samples fail; inspect its summary for quality results.

The revised production-pipeline host rerun by Claude remains pending. The earlier
mocked 30/30
schema results do not establish live schema quality, assumptions coverage,
semantic injection resistance or control/executor cost ratios.

## D-4 recorded host results (2026-10-23)

Claude produced these evidence files with the former single-call adapter. They
were read here, not edited or rerun. Both runs used the same 30 authored requests.

| Measurement | Before v2 | After v2, single-call adapter |
|---|---:|---:|
| Schema-valid contracts | 30/30 | 27/30 |
| Criteria | 39 | 38 |
| command / file_exists / regex / llm_judge | 4 / 10 / 13 / 12 | 6 / 11 / 12 / 9 |
| llm_judge share (valid outputs only) | 0.307692 | 0.236842 |
| llm_judge-only contracts | 11 | 5 |
| Contracts without command checks | 26 | 21 |
| Assumptions in valid outputs | 51 | 51 |
| API-equivalent USD (all calls) | 0.03600314 | 0.01779202 |
| Summed call latency, seconds | 237.186616 | 295.212116 |

Sources: `controller/evidence/2026-10-23-d4-before.json` and
`controller/evidence/2026-10-23-d4-after-v2.json`. The three after-v2 failures,
`ambiguous-tests`, `scoped` and `data-csv`, report "Measurement permits one
generation per sample; no retry": the adapter refused the gate's targeted
regeneration. These results do not measure production recovery; the smaller
valid-output population also limits check-share comparisons. The revised tool
preserves these files and prompts. Claude's host rerun with up to 90 generations,
the approval flag and the printed USD 0.198000 planning estimate is pending.
