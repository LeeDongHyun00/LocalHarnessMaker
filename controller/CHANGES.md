# Controller First task — 2026-10-21

Implemented the shared backend protocol, an injectable standard-library HTTP
transport for the Responses API, and the initial contract CLI. Structured
output uses text.format with strict JSON Schema, with local validation against
the repository schema. Internal schema adaptation handles disjoint check types
and optional exact stdout without editing the shared interface. Validation
failures allow two regenerations; transport failures, refusals, and incomplete
responses fail without automatic paid retries.

The version-zero prompt keeps request, handoff, and example inputs in separate
JSON data blocks in a user message. Literal angle brackets and ampersands are
escaped to prevent delimiter breakout. System instructions reject role changes
inside task data. This is a prompt boundary defense, not a measured guarantee of
model resistance to semantic prompt injection.

Executor effort comes from deterministic request features. Actual token counts
come from provider accounting, and analyze.py calculates USD from standard
input, cached-input, and output rates. Contract metadata is overwritten in
code and includes every validation attempt. A preflight text utility reports a
conservative UTF-8 byte bound, explicitly not an exact tokenizer count. Every
HTTP attempt logs latency and known usage to stderr; unknown charges are null.

Model and endpoint settings live in config.yaml. Both YAML files deliberately
use JSON-compatible syntax so the existing jsonschema-only project dependency
set is sufficient. This session supports execution from the repository checkout;
distribution of non-Python resources in a wheel has not been verified.

## Verification

- `.venv/bin/python -m pytest tests/controller -q -s` exercises fixed mocked
  Responses API requests, ten hand-written request/contract cases, four
  ambiguous cases, all effort levels, schema adaptation, metadata replacement,
  bounded regeneration, usage accumulation, and CLI exit/stdout behavior.
- `.venv/bin/python -m tests.controller.mock_contract_cli contract --prompt
  schemas/examples/prompt.json --handoff none --cases controller/case_library/seed
  --backend cheap_api --out /tmp/localharness-controller-first-task.json` runs
  the real CLI with only HTTP replaced by a fixed offline response.
- Validate that artifact with `jsonschema.Draft202012Validator` against
  schemas/contract.schema.json. The STATUS file records observed results.

No paid model calls were made. OPENAI_API_KEY was not configured at session
start. Mocked schema and assumption ratios measure plumbing and fixture
coverage; live backend quality, injection resistance, cost relative to an
executor, and latency targets remain unmeasured. The local backend, BM25
retrieval, handoff generation, judge, and 30-sample comparison remain later
deliverables. The CLI rejects local and JSONL retrieval requests explicitly.
The judge's missing shared schema is already recorded by Role 1; no judge
interface was invented in this session.

## Assumptions

- An empty Remaining section selects only the role prompt's First task for
  this session; future dated deliverables remain in STATUS for continuation.
- The unspecified low-cost model uses configurable gpt-4.1-mini-2025-04-14
  at standard pricing. This does not imply verified account/model access.
- Existing root dependencies remain unchanged; configuration uses JSON syntax
  within YAML and HTTP uses the Python standard library.
- Synthetic provider usage and hand-written golden contracts are test fixtures,
  not training data or measured model output.

## Official documentation

- [Responses structured output and supported schemas](https://developers.openai.com/api/docs/guides/structured-outputs)
- [Configured model snapshot and capabilities](https://developers.openai.com/api/docs/models/gpt-4.1-mini)
- [Standard token pricing checked on 2026-10-21](https://developers.openai.com/api/docs/pricing)

# Backend selection update — 2026-10-21

The user selected the logged-in Codex CLI with gpt-6-luna as the primary
control backend, and gpt-6-luna over HTTP as fallback. Added the directly
callable `CodexCLIBackend`, which invokes `codex exec` with a schema file
generated from the existing strict wire adapter, request text on stdin, a new
initially empty temporary working directory, a copied environment with
`HARNESS_NESTED=1`, a read-only sandbox, ephemeral mode, and the low effort
override `model_reasoning_effort="low"`. The existing CLI `--backend` choices
remain unchanged while Role 1's related interface proposal awaits approval.

The installed `codex-cli 0.162.0-alpha.17.2` accepts the override; `-c`
configuration syntax appears in `codex exec --help`, and an offline strict
config parse reached the missing-prompt validation. A first schema-only probe
also confirmed that `--ask-for-approval` is not an `exec` option and was
removed. The subsequent live smoke call confirms the selected model, effort
override, schema file, token-event parsing, and final artifact validation work
together. The call finished in 12.117 seconds with 16,060 input tokens,
0 cached input tokens, 516 output tokens, and $0.001864 API-equivalent cost at
the user-specified rates. This is an estimate, not an API invoice.

The HTTP fallback's configured model and price key now use gpt-6-luna. The
user-provided rates are 0.10 USD per million input tokens, 0.01 cached input,
and 0.50 output. No HTTP backend call was made. Codex CLI choice wiring,
automatic fallback routing, and hook recursion guards depend on the pending
Role 1 interface decision and other roles' work; this change adds no CLI choice.

## Verification

- `.venv/bin/python -m pytest tests/controller/test_codex_cli.py
  tests/controller/test_backend.py -q -s`: 28 passed before the final usage
  edge case was added.
- `.venv/bin/python -m pytest tests/controller -q -s`: 73 passed; fixture-only
  mock rates and assumptions report 10/10 and 4/4.
- A live direct `CodexCLIBackend.generate` call with `schemas/examples/prompt.json`
  returned a contract that passed `Draft202012Validator` against
  `schemas/contract.schema.json`; the STATUS file records exact token and
  latency output.
- `codex login status`: `Logged in using ChatGPT`.
- `codex exec --help` and a strict-config CLI probe verified the installed
  flags and `model_reasoning_effort` configuration key.

## Assumptions

- The user-provided gpt-6-luna prices are planning rates for API-equivalent
  reporting, not a claim about the account's actual billed usage.
- A Role 1 approval is still required before adding `codex_cli` to any frozen
  backend CLI enum. Direct construction remains available for tests/smoke checks.

## Official documentation

- [Codex CLI overview and configuration](https://developers.openai.com/api/docs/libraries/openai-cli)
