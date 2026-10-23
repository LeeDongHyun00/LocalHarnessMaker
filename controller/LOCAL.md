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
limits each sample to one CLI generation: no regeneration, HTTP fallback or local
calls. Production routing and CLI flags are unchanged. Child Codex processes
retain the existing copied `HARNESS_NESTED=1` environment. Run only on a host
with a logged-in CLI and compatible installed Codex version.

The printed estimate is 30 calls and USD 0.066000 with the current price snapshot,
17,000 input and 1,000 output tokens per call, without cache discounts. These
planning token allowances are not limits; framing, output length and actual
usage can differ. Override them with `--estimated-input-tokens` and
`--estimated-output-tokens`. The estimate uses the versioned API-equivalent
snapshot in `controller/prices.yaml`, not subscription billing. It prints before
any call, including approved runs. No HTTP API key is required. HTTP cheap_api
is not measured in this run; its fallback verification still requires a key.

One JSON summary contains per-sample schema validity, assumptions count, counts
of command/file_exists/regex/llm_judge criteria, exit code, and latency and cost
from the `control_call` log record. The record retains backend/model/pricing
identity. Totals include schema pass rate, assumptions, criterion counts and the
llm_judge share among schema-valid contracts. Failed contracts have null counts;
missing accounting propagates to null total cost, rather than zero. Failed calls
with measured usage remain in costs. Latency totals sum control-call latency,
not wrapper wall time. An existing summary path is refused. Temporary inputs
and outputs are not retained or added to the case library; this measures the
contract generator and does not collect training data. A completed measurement
returns 0 even if some samples fail; inspect its summary for quality results.

Host execution and live D-4 quality remain pending. The earlier mocked 30/30
schema results do not establish live schema quality, assumptions coverage,
semantic injection resistance or control/executor cost ratios.
