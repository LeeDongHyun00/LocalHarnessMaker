# Role 3: Controller Engineer (control model)

Read AGENTS.md at the repository root first. This file is your contract.

## Goal

Build the generators that turn a request (plus the previous handoff and similar past cases) into a contract that validates against the contract schema, and turn a session transcript into a handoff document that validates against the handoff schema. Two backends share one interface: a low-cost API model first, then a local Gemma 4 12B. Never guess: anything unknown goes into assumptions. Facts (token counts, cost, reasoning effort) are computed by code, never by the model.

## Ownership

Owned paths: controller/ including __main__.py (CLI), analyze.py (token count, difficulty rules, reasoning effort selection, cost calculation), contract_gen.py, handoff_gen.py, judge.py, backends/base.py, backends/cheap_api.py, backends/local.py, case_library/, prompts/ (prompt templates for the control model), config.yaml, prices.yaml. Tests in tests/controller/.
Forbidden: editing verifier/ or eval/. Reading eval/tasks/ to tune templates is forbidden because it contaminates the evaluation set. Build your own samples in tests/controller/fixtures/.

## Interfaces

1. The three CLIs in AGENTS.md section 3.2: contract, handoff, judge. Every output must validate against its schema. On validation failure, regenerate at most two times, then exit with code 2.
2. Backend interface: generate(schema, messages) returns a dict that matches the schema; usage() returns tokens, cost and latency of the last call.
3. Model names and endpoints live in controller/config.yaml, never in code.

## Deliverables

- D-1, due 2026-10-27: backends/base.py and the cheap_api backend (OpenAI Responses API with JSON Schema structured output). Golden tests on fixed inputs with the API mocked. analyze.py reasoning effort rules version 1, based on request length, number of files mentioned, whether tests are required, and the number of distinct requirements. Document the rules in controller/prompts/effort-rules.md.
- D-2, due 2026-11-03: contract_gen complete. Case retrieval from case_library/ (contracts that passed verification stored as JSONL; BM25 retrieval of the top 3 as examples; embeddings optional). Prompt template version 1. CLI contract. Template principle: make checklist items command, file_exists or regex whenever possible; llm_judge is the last resort.
- D-3, due 2026-11-06: local backend. Serve Gemma 4 12B with vLLM or llama.cpp and apply JSON Schema constrained decoding. The same golden tests pass. Record the serving method and memory requirements in controller/LOCAL.md.
- D-4, due 2026-11-10: handoff_gen, judge, and the complete CLI. Internal comparison of cheap_api versus local on the 30 samples in tests/controller/fixtures/: schema pass rate, number of assumptions, latency, cost.
- D-5, optional, due 2026-11-13, only if time remains: QLoRA training script that uses the case library, and a comparison of output quality with and without retrieved examples.

## Success criteria

- SC-1: both backends produce schema-valid output for 100 percent of the 10 inputs in schemas/examples/ and tests/controller/fixtures/.
- SC-2: on ambiguous request samples, assumptions is never empty. Report the ratio in the test log. An empty list on an ambiguous request means the model is guessing.
- SC-3: a test proves that reasoning_effort and cost_estimate are overwritten by analyze.py and never taken from model output.
- SC-4: a log line records the cost and latency of every control model call. Targets: cost under 5 percent of the executor call; local latency under 30 seconds.
- SC-5: the user's request text is wrapped as a data block in the prompt (prompt injection defense). The template tests include an injection sample such as "ignore previous instructions" and show it has no effect on the contract.
- SC-6: the controller package never imports the verifier package.

## Verification

1. pytest tests/controller
2. python -m controller contract --prompt schemas/examples/prompt.json --handoff none --cases controller/case_library/seed --backend cheap_api --out /tmp/c.json, then validate /tmp/c.json against schemas/contract.schema.json with the jsonschema library.
3. The same command with --backend local.

## Stop and escalate conditions

In addition to STOP-1 to STOP-4 in AGENTS.md:
- STOP-C1: a field that is not in the schema is needed. Write a proposal in docs/decisions/ and report. Do not add it yourself.
- STOP-C2: the local model cannot satisfy the schema even with constrained decoding. Report the measured failure rate and a two-stage alternative (free text first, then structuring).
- STOP-C3: any plan to build training data from the output of the executor model or another paid model. Wait for a terms-of-service check before proceeding.
- STOP-C4: GPU memory is insufficient. Report the quantization level you propose and its expected quality impact.

## First task

1. Create backends/base.py and the cheap_api backend. Generate a contract from schemas/examples/prompt.json and make it validate against the schema.
2. Write prompt template version 0 in controller/prompts/contract.md with these sections: role of the control model; input (the request, the handoff and the examples, each wrapped as a data block); output rules (no guessing, separate assumptions, prefer verifiable checks, exactly one check command per criterion); one example taken from schemas/examples/.
3. In analyze.py, implement token counting and cost calculation first, then attach reasoning effort rules version 0.
4. Update state/STATUS-controller.md.
