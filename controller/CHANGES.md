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
