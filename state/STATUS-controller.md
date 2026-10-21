## Done

- Implemented the backend protocol, injectable Responses API HTTP transport, strict-schema adapter, local validation, and per-call usage/cost/latency logging without new root dependencies (.venv/bin/python -m pytest tests/controller -q -s: 61 passed).
- Implemented the initial contract CLI and bounded regeneration; code overwrites model metadata and sums usage across all attempts; input/internal errors use exit codes 1/2 and success prints one output path (.venv/bin/python -m pytest tests/controller -q -s: 61 passed, including CLI and metadata-override regressions).
- Added contract prompt v0 with escaped request/handoff/example data blocks, a shared-example excerpt, and documented effort rules v0 plus conservative preflight token bounds (.venv/bin/python -m pytest tests/controller -q -s: 61 passed, including delimiter injection and all five effort levels).
- Added ten hand-written mocked cases, including four ambiguous requests; recorded fixture-only schema and assumptions ratios (.venv/bin/python -m pytest tests/controller -q -s: Mocked schema pass rate: 10/10; ambiguous assumptions: 4/4).
- Exercised the real contract CLI with mocked HTTP and independently validated the generated artifact (.venv/bin/python -m tests.controller.mock_contract_cli contract --prompt schemas/examples/prompt.json --handoff none --cases controller/case_library/seed --backend cheap_api --out /tmp/localharness-controller-first-task.json: exit 0 and stdout /tmp/localharness-controller-first-task.json; independent Draft202012Validator check: VALID: offline mocked contract matches schemas/contract.schema.json).
- Wrote the controller-owned change summary with verification limits, assumptions, and official API references (controller/CHANGES.md reviewed; git diff --check: exit 0).
- Added a directly callable Codex CLI backend using a clean temporary working directory, strict wire schema, stdin prompt, read-only sandbox, ephemeral execution, `HARNESS_NESTED=1`, and configured low reasoning effort; retained unchanged CLI backend choices pending Role 1 approval (.venv/bin/python -m pytest tests/controller -q -s: 73 passed).
- Updated the HTTP API fallback to gpt-6-luna and configured API-equivalent user-specified token rates for both paths (test_codex_cli.py::test_api_fallback_model_and_rates_match_cli_estimate: passed).
- Completed one live gpt-6-luna Codex CLI smoke call on schemas/examples/prompt.json; output validated against schemas/contract.schema.json (direct `CodexCLIBackend.generate`: valid; latency 12.117 s; input 16060; cached input 0; output 516; API-equivalent cost $0.001864).
- Confirmed the installed CLI reasoning override key, `model_reasoning_effort`, via `codex exec --help`, an offline `--strict-config` parse, and the successful live invocation (codex-cli 0.162.0-alpha.17.2; the offline parse exited at `No prompt provided via stdin`, confirming config parsing completed).

## Remaining

- D-1, by 2026-10-27: calibrate and document effort rules v1, decide whether an exact preflight tokenizer dependency is needed with Role 1, and measure API cost against an executor baseline. Current preflight count is a UTF-8 byte bound; actual output metadata uses provider token counts.
- D-2, by 2026-11-03: implement BM25 top-three retrieval from verified JSONL cases, prompt v1, and complete contract generation quality checks. v0 rejects JSONL retrieval instead of silently ignoring it; no training data was collected.
- D-3, by 2026-11-06: implement the local Gemma 4 12B constrained-decoding backend, serving/memory documentation, and shared golden tests. The local CLI selection currently returns an explicit input error without an API fallback.
- Before D-4 judge implementation: obtain Role 1's approved criterion/output schema; the missing shared judge interface is already identified in state/STATUS-lead.md. Do not invent or edit that interface.
- D-4, by 2026-11-10: implement handoff and judge generation/CLI after interface resolution, expand to 30 own samples, and compare both backends. SC-1/SC-2 live quality, SC-4 cost/latency targets, and SC-5 semantic injection resistance remain unmeasured.
- Add `codex_cli` routing only after Role 1 approves the interface proposal in docs/decisions/0004-codex-cli-backend-and-nested-guard-proposal.md; this change tests the backend directly and leaves CLI enums unchanged.
- Before merge: run the full relevant suite once. Controller-owned tests passed; no merge was performed. The user subsequently requested staging all changes and creating a Conventional Commit.

## Decisions

- Begin with the First task: the controller STATUS file had no items under Remaining.
- Use the standard-library HTTP transport and JSON-compatible YAML: root dependency/configuration edits are owned by Role 1 and are unnecessary for this initial implementation.
- Keep a separate API wire-schema adapter: strict structured output requires complete required-key lists and supported unions while repository artifacts must retain the original schema semantics.
- Keep computed metadata outside the model's requested schema and overwrite it in code: effort and billing facts must never originate from generated content.
- Sum provider usage and code-calculated cost across regenerations: the artifact should account for every paid validation attempt, not just the successful call.
- Log null costs when provider usage is unknown: transport failure does not prove a zero charge.
- The original First task implementation was offline. The user later selected a logged-in Codex CLI smoke check, which ran once; user-provided API-equivalent rates do not claim actual billed pricing.
- Codex CLI model selection is implemented as a directly callable backend pending Role 1 approval before adding it to the shared CLI interface.
- Keep source-checkout execution as the verified packaging scope: wheel resource inclusion has not been tested or changed.

## Verify commands

- .venv/bin/python -m pytest tests/controller -q -s
- .venv/bin/python -m tests.controller.mock_contract_cli contract --prompt schemas/examples/prompt.json --handoff none --cases controller/case_library/seed --backend cheap_api --out /tmp/localharness-controller-first-task.json
- .venv/bin/python -c 'import json; from jsonschema import Draft202012Validator; from pathlib import Path; artifact = Path("/tmp/localharness-controller-first-task.json"); Draft202012Validator(json.loads(Path("schemas/contract.schema.json").read_text())).validate(json.loads(artifact.read_text())); print("VALID: offline mocked contract matches schemas/contract.schema.json")'
- git diff --check
- Live smoke evidence: `CodexCLIBackend.generate` on schemas/examples/prompt.json; validated against schemas/contract.schema.json, 12.117 seconds, 16,060 input tokens, 0 cached input tokens, 516 output tokens, $0.001864 API-equivalent estimate.
- Installed CLI checks: `codex --version` (codex-cli 0.162.0-alpha.17.2), `codex exec --help`, and offline `codex exec --strict-config --config 'model_reasoning_effort="low"' --output-schema /dev/null - </dev/null` (exit 1: `No prompt provided via stdin`, after successful config parsing).

## Do not touch

- Shared schemas/, root configuration, and other roles' implementation/tests/status files; controller ownership is controller/, tests/controller/, and this STATUS file.
- eval/tasks/ is forbidden reading for Role 3; do not tune prompts against the evaluation set.
- Existing harness/, experiments/, scripts/, and concurrent role/user edits.
- No verifier imports, invented judge schema, interface changes, secrets in files, model-output training data, paid batches of ten or more, deletion, history rewriting, or external service configuration changes.
- Do not expose `codex_cli` in any `--backend` choices until the Role 1 interface decision is approved; preserve existing user edits in non-controller paths.

## Assumptions

- The empty initial Remaining section authorizes the First task for this session, not automatic implementation of every later dated deliverable.
- The user selected gpt-6-luna through logged-in Codex CLI as primary and HTTP fallback, with CLI invocation available only by direct backend construction until Role 1's interface approval.
- gpt-6-luna's API-equivalent USD report uses the user-specified input/cached/output rates; it is not actual billed usage.
- Config YAML uses the JSON subset so no YAML/SDK/tokenizer dependency needs to be added to root configuration.
- Provider usage is the authority for actual token counts; preflight byte bounds are explicitly not exact tokenizer counts or complete API framing estimates.
- Hand-written fixtures and synthetic usage verify implementation behavior only. One live sample passed schema validation but does not prove broader model quality, assumption quality, injection immunity, relative cost, or latency targets.
- No PR was created; controller/CHANGES.md records the change summary and Assumptions within the owned path.
