## Done

- Fixed H4 for executable lookup and runner spawn failures: CLI calls that never started record zero input/cached/output tokens and USD, retain actual backend/fallback reason, and contract/judge totals equal one mocked HTTP call (.venv/bin/python -m pytest tests/controller -q: 145 passed in 1.71s, including six never-started CLI command cases).
- Retained unknown accounting for started CLI deadline/nonzero/missing-final-message failures; tested contract exit 2 with no success stdout and preserved output after successful HTTP fallback, and schema-valid judge null totals (.venv/bin/python -m pytest tests/controller -q: 145 passed in 1.71s, including six started-process command cases).
- Split invalid-message and missing-CLI tests and added a same-model fallback regression that requires rejection before HTTP; documented H4 and the unresolved contract schema policy in controller/CHANGES.md (.venv/bin/python -m pytest tests/controller -q: 145 passed in 1.71s).
- Updated the reviewable change summary and role handoff; only controller/, tests/controller/ and this STATUS file were edited in this session (git diff --check -- controller tests/controller state/STATUS-controller.md: exit 0).
- Added approved codex_cli routing to all three required --backend selectors and selected codex_cli in controller/config.yaml; mocked CLI tests cover exact one-path stdout and error preservation (.venv/bin/python -m pytest tests/controller -q -s: 131 passed).
- Implemented a shared three-generation budget, one same-model CLI-to-HTTP transport fallback, environment-key/remaining-slot checks, guarded copied child environments on regeneration, configurable policy, and explicit errors without hidden local fallback (.venv/bin/python -m pytest tests/controller -q -s: 131 passed, including timeout/nonzero/unavailable CLI and exhausted-budget regressions).
- Implemented controller judge against the published input/output schemas with local reference resolution, pre-call input checks, code-owned criterion/model/usage, all three statuses, llm_judge evidence marker, model-conflict rejection, cache subset checks and summed/null retry/fallback accounting (.venv/bin/python -m pytest tests/controller -q -s: 131 passed).
- Implemented bounded text artifact snapshots with explicit omitted-evidence manifests; symlinks and unreadable/missing inputs fail before calls, and prompts require unverifiable when required evidence is unavailable (.venv/bin/python -m pytest tests/controller -q -s: 131 passed, including workspace exclusions/binary/size-limit and symlink tests).
- Implemented controller handoff with schema-valid input/output, unique matching criterion IDs, consistent verdict status, complete criterion coverage, and regeneration for contradicted or dropped completion state (.venv/bin/python -m pytest tests/controller -q -s: 131 passed, including trusted-verdict contradiction tests).
- Added effort rules v1, deduplicated normalized requirement segments and documented thresholds; effort/cost remain code-owned and preflight byte counts remain explicitly approximate (.venv/bin/python -m pytest tests/controller -q -s: 131 passed, including five effort levels, boundaries and requirement deduplication).
- Added deterministic BM25 top-three retrieval over curated contract JSONL, nested-library reading, duplicate suppression, stable ties and contract prompt v1; malformed cases fail before calls (.venv/bin/python -m pytest tests/controller -q -s: 131 passed, including codex_cli contract CLI with a retrieved case).
- Added a disabled-by-default local JSON-schema chat adapter, injectable transport, bounded requests, explicit identity/availability errors, null unknown pricing and LOCAL.md serving/memory verification limits (.venv/bin/python -m pytest tests/controller -q -s: 131 passed; local adapter exercised only through mocks).
- Expanded hand-authored samples to 30 and ran them through all three mocked adapters; fixtures are implementation evidence rather than model quality measurements (.venv/bin/python -m pytest tests/controller -q -s: Mocked codex_cli/cheap_api/local each schema=30/30 and ambiguous assumptions=8/8; original fixture report 10/10 and 4/4).
- Updated controller/CHANGES.md with the current behavior, verification limits and Assumptions (git diff --check -- controller tests/controller state/STATUS-controller.md: exit 0).

## Remaining

- Needs Role 1 decision: version 1 contract cost_estimate cannot represent unknown usage from a started CLI process followed by successful HTTP fallback. Keep the current honest exit 2 until Role 1 approves any interface revision; judge can already retain null totals. No schema change was attempted.
- Pending host verification: exercise the actual contract, judge and handoff CLIs with explicitly selected codex_cli and validate outputs; separately check configured HTTP fallback and production hook guard integration. Nested Codex, network, live model calls and macOS sandbox-exec were forbidden and were not attempted this session.
- Pending host verification, D-1: measure API-equivalent control cost against an executor baseline and empirically calibrate effort v1 from task outcomes. Existing thresholds have only synthetic/fixture calibration; no exact tokenizer dependency is presently needed.
- Pending host verification, D-3: select and verify the local llama.cpp/vLLM build, exact Gemma 4 12B artifact/alias, schema-constrained endpoint behavior, peak memory and latency; establish an approved API-equivalent local price snapshot before contract generation. Keep local.enabled=false until verified. STOP-C2/STOP-C4 apply if measured schema quality or GPU capacity fails.
- Pending host verification, D-4: compare real schema pass rate, assumptions, latency and API-equivalent cost across the 30 authored samples. Estimate/report cost before any paid batch of ten or more. SC-1/SC-2 live quality, SC-4 targets and SC-5 semantic injection resistance remain unmeasured.
- D-2 library population requires verified, permitted provenance; do not gather executor/paid-model output for training without the STOP-C3 terms review. The curated seed library is intentionally empty.
- Before merge: run the full repository suite once in a coordinated host session and verify packaging resources if wheel installation is required. No merge, staging or commit was performed; .git was read-only.
- D-5 remains optional and unstarted: no QLoRA work or model-output training data collection was authorized by this implementation.

## Decisions

- Zero usage applies only before inference could start: constructor failure and runner spawn OSError spend no tokens; output handling after runner return cannot reset unknown usage to zero.
- Retain contract exit 2 after a started CLI leaves unknown usage, even when HTTP fallback succeeds: non-null cost_estimate cannot honestly represent the total under the approved schema; Role 1 owns any revision.
- Execute the user's priority order: approved backend routing, judge and handoff precede effort v1, retrieval and the mock-only local adapter.
- Keep one budget in RoutedBackend: fallback consumes a generation slot and cannot reset regeneration limits; fail/unverifiable are content results, not fallback triggers.
- Resolve published JSON Schema references from a local registry: validation must work offline without fetching schemas.
- Preserve unknown accounting as null in judgments and logs: incomplete usage does not imply free inference; contract's non-null schema requires an explicit internal error instead of fabricated numbers.
- Pin price references to date/model/SHA-256 and retain per-call route/event logs: retry/fallback evidence must identify actual backend and pricing, including failed calls.
- Bound artifact text and expose omissions: normal workspace metadata and binaries must not prevent judging available text or masquerade as inspected evidence.
- Keep local disabled pending host verification: mocked protocol tests do not establish server compatibility, hardware capacity or constrained-decoding quality.
- Retain byte-bound preflight features without a tokenizer dependency: provider token counts remain authoritative and no root dependency/interface change is needed.
- Treat JSONL library provenance as an owner-curated precondition: schema validation proves structure, not prior verifier success, and the controller never auto-collects cases.

## Verify commands

- .venv/bin/python -m pytest tests/controller -q
- git diff --check -- controller tests/controller state/STATUS-controller.md
- Pending host: python -m controller contract --prompt schemas/examples/prompt.json --handoff none --cases controller/case_library/seed --backend codex_cli --out /tmp/controller-contract.json
- Pending host: python -m controller judge --criterion schemas/examples/criterion.json --artifact PUBLIC_EVIDENCE_DIR --backend codex_cli --out /tmp/controller-judgment.json
- Pending host: python -m controller handoff --transcript TRANSCRIPT_PATH --contract CONTRACT_PATH --verdict VERDICT_PATH --backend codex_cli --out /tmp/controller-handoff.json
- Pending before merge: full repository test suite, coordinated with the owning roles.

## Do not touch

- Shared schemas/, root configuration, prompts/, verifier/, eval/, plugin/, other roles' tests/status and concurrent user/role changes; ownership is controller/, tests/controller/ and this STATUS file.
- eval/tasks/ is forbidden reading; do not tune against the evaluation set.
- .git is read-only in this session; do not stage, commit, rewrite history or delete files.
- Do not run network/live models, nested Codex or macOS sandbox-exec in this environment; all such checks are pending host verification.
- No verifier imports, new shared fields/interfaces, secrets in files, paid batches of ten or more without an estimate, or model-output training data without terms review.
- Keep local.enabled=false until host serving verification and never make local a hidden fallback.

## Assumptions

- Injected runners follow subprocess.run semantics: FileNotFoundError/PermissionError from spawn mean no process started; TimeoutExpired means a process started. Fixtures and transports are mocked and do not establish live CLI/HTTP availability.
- User approval of decisions 0002/0004 and the published schemas supersedes the old interface-blocked Remaining items; required CLI backend flags remain required despite the primary configuration selection.
- The existing gpt-6-luna rates are user-specified API-equivalent planning rates, not verified billed pricing; missing local prices stay unknown.
- Artifact evidence is bounded UTF-8 text with explicit omissions for .git/.venv/__pycache__/node_modules, binaries and byte limits; omitted material cannot support a pass that requires inspecting it.
- Exact preflight tokenization is not needed for these effort heuristics; provider accounting owns actual usage, and byte counts exclude protocol framing.
- A curated case library contains only previously verified, permitted contracts; this reader validates structure but cannot prove historical provenance.
- The local serving protocol and 12B weight-storage arithmetic are implementation targets/lower bounds, not measured compatibility, memory requirements or performance.
- Authored responses, runner events and local fixture prices verify plumbing only. No model calls or live benchmark comparisons ran this session.
- No PR exists; controller/CHANGES.md contains the reviewable summary and Assumptions. Only owned directories and this STATUS file belong in the eventual commit.
