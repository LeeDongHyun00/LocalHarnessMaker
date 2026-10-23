# Role 3: Controller Engineer (control model)

Read AGENTS.md at the repository root first. This file is your contract.

## Goal

Build the generators that turn a request (plus the previous handoff and similar past cases) into a contract that validates against the contract schema, and turn a session transcript into a handoff document that validates against the handoff schema. Three backend selectors share one interface: codex_cli is primary using gpt-6-luna through the logged-in CLI; cheap_api is HTTP fallback using that same model; local remains a version 1 selector, but Gemma 4 12B implementation and measurement are dropped by [decision 0007](../docs/decisions/0007-scope-cuts.md). Never guess: anything unknown goes into assumptions. Facts (token counts, cost, reasoning effort) are computed by code, never by the model.

## Ownership

Owned paths: controller/ including __main__.py (CLI), analyze.py (token count, difficulty rules, reasoning effort selection, cost calculation), contract_gen.py, handoff_gen.py, judge.py, backends/base.py, backends/codex_cli.py, backends/cheap_api.py, backends/local.py, case_library/, prompts/ (prompt templates for the control model), config.yaml, prices.yaml. Tests in tests/controller/.
Forbidden: editing verifier/ or eval/. Reading eval/tasks/ to tune templates is forbidden because it contaminates the evaluation set. Build your own samples in tests/controller/fixtures/.

## Interfaces

Version 1 is approved in AGENTS.md section 3 and decisions 0002–0004. Schema
publication does not establish live backend availability or implemented CLIs.

1. contract, handoff and judge retain their existing flags and exit/path-stdout rules. --backend is required and accepts codex_cli, cheap_api, local. Select codex_cli explicitly in primary configuration. Every output validates against its published schema.
2. Backend generate(schema, messages) returns validated JSON; usage() reports code-measured accounting. Models, endpoints, executable paths, deadlines and fallback policy live in controller/config.yaml, never hardcoded. The CLI reuses login; HTTP uses an environment key, never copied CLI credentials.
3. Set HARNESS_NESTED=1 in a copied environment for every controller-owned Codex subprocess, retry/resume/repair or wrapper; never mutate parent environment/config. Inject the subprocess runner, use shell=False, pipe requests and apply deadlines. Read --json as logs/usage and --output-last-message as final JSON; locally validate regardless of strict --output-schema support.
4. One total budget permits at most three generation calls across CLI, output regeneration and HTTP fallback. Only CLI transport unavailability/failure/deadline may transition once to cheap_api with the same gpt-6-luna, configured key and remaining slot. Remaining retries stay HTTP. Ordinary fail/unverifiable judgments do not trigger fallback; local is never an implicit fallback. Missing credentials/budget or unavailable local backend is an explicit error.
5. judge --criterion accepts exactly one full llm_judge success_criteria item, validated with schemas/judgment-input.schema.json. Emit criterion_id, status, reason, evidence, model, usage using judgment.schema.json. Code owns identity/usage; criterion_id matches input, evidence contains llm_judge, status is pass/fail/unverifiable. Preserve unverifiable, and reject non-judge criteria before calls.
6. Usage includes nullable input/cached/output tokens and usd, measured latency_seconds, cost_basis=api_equivalent_usd and nullable pricing_ref. Sum all calls, including failed/fallback calls. Cache tokens are an input subset. Use versioned API-equivalent prices for CLI/API/local; missing counts/prices remain null rather than zero. Retain per-call actual backend/model/prices and fallback reasons for the evaluation report.

## Deliverables

- D-1, due 2026-10-27: backends/base.py, primary codex_cli backend and cheap_api fallback (same gpt-6-luna, JSON Schema output). Golden tests mock subprocess and HTTP, including the shared three-call budget, fallback transition and child environment guard. analyze.py reasoning effort rules version 1, based on request length, number of files mentioned, whether tests are required, and the number of distinct requirements. Document the rules in controller/prompts/effort-rules.md.
- D-2, due 2026-11-03: contract_gen complete. Case retrieval from case_library/ (contracts that passed verification stored as JSONL; BM25 retrieval of the top 3 as examples; embeddings optional). Prompt template version 1. CLI contract. Template principle: make checklist items command, file_exists or regex whenever possible; llm_judge is the last resort.
- D-3, dropped by [decision 0007](../docs/decisions/0007-scope-cuts.md), approved 2026-10-23: local Gemma 4 12B backend, serving and constrained-decoding work.
- D-4, due 2026-11-10: handoff_gen, judge, and the complete CLI. Internal comparison of primary codex_cli and HTTP cheap_api on the 30 samples in tests/controller/fixtures/: schema pass rate, number of assumptions, latency, cost.
- D-5, dropped by [decision 0007](../docs/decisions/0007-scope-cuts.md), approved 2026-10-23: optional QLoRA training and its quality comparison.

## Success criteria

- SC-1: all implemented backends produce schema-valid output for 100 percent of the 10 inputs in schemas/examples/ and tests/controller/fixtures/.
- SC-2: on ambiguous request samples, assumptions is never empty. Report the ratio in the test log. An empty list on an ambiguous request means the model is guessing.
- SC-3: a test proves that reasoning_effort and cost_estimate are overwritten by analyze.py and never taken from model output.
- SC-4: a log line records the API-equivalent USD cost and latency of every control model call. Targets: cost under 5 percent of the executor call; the former local latency target is out of scope under decision 0007.
- SC-5: the user's request text is wrapped as a data block in the prompt (prompt injection defense). The template tests include an injection sample such as "ignore previous instructions" and show it has no effect on the contract.
- SC-6: the controller package never imports the verifier package.

## Verification

1. pytest tests/controller
2. python -m controller contract --prompt schemas/examples/prompt.json --handoff none --cases controller/case_library/seed --backend codex_cli --out /tmp/c.json, then validate /tmp/c.json against schemas/contract.schema.json with the jsonschema library.
3. Repeat with explicit --backend cheap_api when its environment key is configured. Local verification is dropped by decision 0007; the selector is retained. Validate judge input/output fixtures against their published schemas; record missing accounting as unknown. No paid batches of ten or more without the required estimate/approval.

## Stop and escalate conditions

In addition to STOP-1 to STOP-4 in AGENTS.md:
- STOP-C1: a field that is not in the schema is needed. Write a proposal in docs/decisions/ and report. Do not add it yourself.
- STOP-C2: the local model cannot satisfy the schema even with constrained decoding. Report the measured failure rate and a two-stage alternative (free text first, then structuring).
- STOP-C3: any plan to build training data from the output of the executor model or another paid model. Wait for a terms-of-service check before proceeding.
- STOP-C4: GPU memory is insufficient. Report the quantization level you propose and its expected quality impact.

## First task

1. Create backends/base.py, primary codex_cli and HTTP cheap_api fallback using the approved model/guard/budget. Generate a contract from schemas/examples/prompt.json and make it validate against the schema.
2. Write prompt template version 0 in controller/prompts/contract.md with these sections: role of the control model; input (the request, the handoff and the examples, each wrapped as a data block); output rules (no guessing, separate assumptions, prefer verifiable checks, exactly one check command per criterion); one example taken from schemas/examples/.
3. In analyze.py, implement token counting and cost calculation first, then attach reasoning effort rules version 0.
4. Update state/STATUS-controller.md.
