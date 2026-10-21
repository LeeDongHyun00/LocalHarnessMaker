## Done

- Implemented the backend protocol, injectable Responses API HTTP transport, strict-schema adapter, local validation, and per-call usage/cost/latency logging without new root dependencies (.venv/bin/python -m pytest tests/controller -q -s: 61 passed).
- Implemented the initial contract CLI and bounded regeneration; code overwrites model metadata and sums usage across all attempts; input/internal errors use exit codes 1/2 and success prints one output path (.venv/bin/python -m pytest tests/controller -q -s: 61 passed, including CLI and metadata-override regressions).
- Added contract prompt v0 with escaped request/handoff/example data blocks, a shared-example excerpt, and documented effort rules v0 plus conservative preflight token bounds (.venv/bin/python -m pytest tests/controller -q -s: 61 passed, including delimiter injection and all five effort levels).
- Added ten hand-written mocked cases, including four ambiguous requests; recorded fixture-only schema and assumptions ratios (.venv/bin/python -m pytest tests/controller -q -s: Mocked schema pass rate: 10/10; ambiguous assumptions: 4/4).
- Exercised the real contract CLI with mocked HTTP and independently validated the generated artifact (.venv/bin/python -m tests.controller.mock_contract_cli contract --prompt schemas/examples/prompt.json --handoff none --cases controller/case_library/seed --backend cheap_api --out /tmp/localharness-controller-first-task.json: exit 0 and stdout /tmp/localharness-controller-first-task.json; independent Draft202012Validator check: VALID: offline mocked contract matches schemas/contract.schema.json).
- Wrote the controller-owned change summary with verification limits, assumptions, and official API references (controller/CHANGES.md reviewed; git diff --check: exit 0).

## Remaining

- Complete the First task's live cheap_api smoke check when OPENAI_API_KEY is configured: run the contract CLI on schemas/examples/prompt.json, validate against schemas/contract.schema.json, and record actual usage/latency. No live generation is claimed; this environment had no configured key. At most three model calls are possible per command.
- D-1, by 2026-10-27: calibrate and document effort rules v1, decide whether an exact preflight tokenizer dependency is needed with Role 1, and measure API cost against an executor baseline. Current preflight count is a UTF-8 byte bound; actual output metadata uses provider token counts.
- D-2, by 2026-11-03: implement BM25 top-three retrieval from verified JSONL cases, prompt v1, and complete contract generation quality checks. v0 rejects JSONL retrieval instead of silently ignoring it; no training data was collected.
- D-3, by 2026-11-06: implement the local Gemma 4 12B constrained-decoding backend, serving/memory documentation, and shared golden tests. The local CLI selection currently returns an explicit input error without an API fallback.
- Before D-4 judge implementation: obtain Role 1's approved criterion/output schema; the missing shared judge interface is already identified in state/STATUS-lead.md. Do not invent or edit that interface.
- D-4, by 2026-11-10: implement handoff and judge generation/CLI after interface resolution, expand to 30 own samples, and compare both backends. SC-1/SC-2 live quality, SC-4 cost/latency targets, and SC-5 semantic injection resistance remain unmeasured.
- Before merge: run the full relevant suite once. Controller-owned tests passed; no merge was performed. The user subsequently requested staging all changes and creating a Conventional Commit.

## Decisions

- Begin with the First task: the controller STATUS file had no items under Remaining.
- Use the standard-library HTTP transport and JSON-compatible YAML: root dependency/configuration edits are owned by Role 1 and are unnecessary for this initial implementation.
- Keep a separate API wire-schema adapter: strict structured output requires complete required-key lists and supported unions while repository artifacts must retain the original schema semantics.
- Keep computed metadata outside the model's requested schema and overwrite it in code: effort and billing facts must never originate from generated content.
- Sum provider usage and code-calculated cost across regenerations: the artifact should account for every paid validation attempt, not just the successful call.
- Log null costs when provider usage is unknown: transport failure does not prove a zero charge.
- Scope this session to the First task and offline evidence: credentials are absent and later deliverables have separate prerequisites; mocked results must not be presented as live model measurements.
- Keep source-checkout execution as the verified packaging scope: wheel resource inclusion has not been tested or changed.

## Verify commands

- .venv/bin/python -m pytest tests/controller -q -s
- .venv/bin/python -m tests.controller.mock_contract_cli contract --prompt schemas/examples/prompt.json --handoff none --cases controller/case_library/seed --backend cheap_api --out /tmp/localharness-controller-first-task.json
- .venv/bin/python -c 'import json; from jsonschema import Draft202012Validator; from pathlib import Path; artifact = Path("/tmp/localharness-controller-first-task.json"); Draft202012Validator(json.loads(Path("schemas/contract.schema.json").read_text())).validate(json.loads(artifact.read_text())); print("VALID: offline mocked contract matches schemas/contract.schema.json")'
- git diff --check
- Pending live check with a configured environment key: .venv/bin/python -m controller contract --prompt schemas/examples/prompt.json --handoff none --cases controller/case_library/seed --backend cheap_api --out /tmp/localharness-controller-live.json

## Do not touch

- Shared schemas/, root configuration, and other roles' implementation/tests/status files; controller ownership is controller/, tests/controller/, and this STATUS file.
- eval/tasks/ is forbidden reading for Role 3; do not tune prompts against the evaluation set.
- Existing harness/, experiments/, scripts/, and concurrent role/user edits.
- No verifier imports, invented judge schema, interface changes, secrets in files, model-output training data, paid batches of ten or more, deletion, history rewriting, or external service configuration changes.

## Assumptions

- The empty initial Remaining section authorizes the First task for this session, not automatic implementation of every later dated deliverable.
- The unspecified cheap model defaults to configurable gpt-4.1-mini-2025-04-14 at standard rates checked in official documentation on 2026-10-21; account access is not verified.
- Config YAML uses the JSON subset so no YAML/SDK/tokenizer dependency needs to be added to root configuration.
- Provider usage is the authority for actual token counts; preflight byte bounds are explicitly not exact tokenizer counts or complete API framing estimates.
- Hand-written fixtures and synthetic usage verify implementation behavior only; they do not prove live schema reliability, model assumption quality, injection immunity, relative cost, or latency targets.
- No PR was created; controller/CHANGES.md records the change summary and Assumptions within the owned path.
