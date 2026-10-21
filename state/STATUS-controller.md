## Done

- Raised codex_cli.timeout_seconds and cheap_api.timeout_seconds to 35, updated the injected subprocess deadline assertion and the 120 s multi-call budget regression, and refreshed CHANGES; local configuration is unchanged (.venv/bin/python -m pytest tests/controller -q: 148 passed in 5.58s).
- Recorded Claude's user-supplied repeated live contract call under the former 25 s deadline with four Codex jobs sharing the subscription; not rerun here (python -m controller contract --prompt schemas/examples/prompt.json --handoff none --cases controller/case_library/seed --backend codex_cli --out OUT: passed, latency 20.0 s versus 15.6 s idle).
- Recorded Claude's user-supplied host verification of the previous deadline change (.venv/bin/python -m pytest tests/controller -q: 148 passed on host; changes remain uncommitted).
- Initially set codex_cli.timeout_seconds and cheap_api.timeout_seconds to 25 (superseded by 35 below); added deadline budget regressions and updated the injected CLI timeout assertion; local configuration is unchanged (.venv/bin/python -m pytest tests/controller -q: 148 passed in 3.43s).
- Recorded Claude's user-supplied 2026-10-22 host verification on codex-cli 0.162.0-alpha.17.2, gpt-6-luna, first call successful with no fallback; not rerun in this sandbox (python -m controller contract --prompt schemas/examples/prompt.json --handoff none --cases controller/case_library/seed --backend codex_cli --out OUT: exit 0, latency 15.6 s, wall 16.4 s, input/output tokens 16074/414, schema-valid, stdout exactly OUT plus newline).
- Recorded Claude's user-supplied host judge verification; unverifiable is a successful computation (python -m controller judge --criterion schemas/examples/criterion.json --artifact tests/verifier/fixtures/ws_pass --backend codex_cli --out OUT: exit 0, latency 14.4 s, wall 14.9 s, input/output tokens 15452/82, status unverifiable, schema-valid).
- Recorded Claude's user-supplied host handoff verification (python -m controller handoff --transcript tests/verifier/fixtures/transcript_pass.jsonl --contract schemas/examples/contract.json --verdict schemas/examples/verdict_pass.json --backend codex_cli --out OUT: exit 0, latency 13.2 s, wall 13.6 s, input/output tokens 16355/280, schema-valid).
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
- Pending host verification: configured HTTP fallback and production hook guard integration remain unverified. Claude verified the three primary codex_cli commands on 2026-10-22 as recorded in Done; Claude also verified a contract call under the former 25 s deadline with concurrent jobs. The revised 35 s deadlines, retry-budget behavior and Role 2's 120 s handoff integration still need host confirmation. Nested Codex, network, live model calls and macOS sandbox-exec are unavailable here and were not attempted.
- Pending host verification, D-1: measure API-equivalent control cost against an executor baseline and empirically calibrate effort v1 from task outcomes. Existing thresholds have only synthetic/fixture calibration; no exact tokenizer dependency is presently needed.
- Pending host verification, D-3: select and verify the local llama.cpp/vLLM build, exact Gemma 4 12B artifact/alias, schema-constrained endpoint behavior, peak memory and latency; establish an approved API-equivalent local price snapshot before contract generation. Keep local.enabled=false until verified. STOP-C2/STOP-C4 apply if measured schema quality or GPU capacity fails.
- Pending host verification, D-4: compare real schema pass rate, assumptions, latency and API-equivalent cost across the 30 authored samples. Record-only quality observation from Claude's live schemas/examples/prompt.json contract: SC-1 used llm_judge before regex and command criteria despite the template preference for mechanical checks and llm_judge as a last resort; do not infer broad quality from one sample or tune on eval/tasks/. Estimate/report cost before any paid batch of ten or more. SC-1/SC-2 live quality, SC-4 targets and SC-5 semantic injection resistance remain unmeasured.
- D-2 library population requires verified, permitted provenance; do not gather executor/paid-model output for training without the STOP-C3 terms review. The curated seed library is intentionally empty.
- Before merge: run the full repository suite once in a coordinated host session and verify packaging resources if wheel installation is required. No merge, staging or commit was performed; .git was read-only.
- D-5 remains optional and unstarted: no QLoRA work or model-output training data collection was authorized by this implementation.

## Decisions

- Raise both cloud per-call deadlines from 25 s to 35 s per Claude's user-approved revision: the repeated host contract call passed in 20.0 s with four Codex jobs sharing the subscription, versus 15.6 s idle. A 25 s deadline leaves only 5 s headroom under measured load, and this Mac has no API key for HTTP fallback after timeout. Three calls plus approximately 1 s startup each take 3 * (35 + 1) = 108 s, within judge's unchanged 120 s budget and handoff's revised 120 s budget being implemented by Role 2. Observed 15.6–20.0 s contract calls fit the plugin's approved 30 s budget; the plugin cuts off at 30 s even though the controller permits 35 s. Completion under further load and three contract attempts are not guaranteed. Keep the local 30 s deadline unchanged.
- Record the live criterion choice as a D-4 observation only: the current contract template already prefers command/file_exists/regex and reserves llm_judge for requirements objective checks cannot express; no prompt, fixture or frozen schema changes are warranted by this record-only request.
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

- Claude's host results are accepted as user-supplied evidence, not independently reproduced here; OUT is the supplied output placeholder, not a retained artifact path. The approximately 1 s startup allowance is a planning estimate, not a measured worst-case guarantee, and HTTP latency remains unmeasured.
- Injected runners follow subprocess.run semantics: FileNotFoundError/PermissionError from spawn mean no process started; TimeoutExpired means a process started. Fixtures and transports are mocked and do not establish live CLI/HTTP availability.
- User approval of decisions 0002/0004 and the published schemas supersedes the old interface-blocked Remaining items; required CLI backend flags remain required despite the primary configuration selection.
- The existing gpt-6-luna rates are user-specified API-equivalent planning rates, not verified billed pricing; missing local prices stay unknown.
- Artifact evidence is bounded UTF-8 text with explicit omissions for .git/.venv/__pycache__/node_modules, binaries and byte limits; omitted material cannot support a pass that requires inspecting it.
- Exact preflight tokenization is not needed for these effort heuristics; provider accounting owns actual usage, and byte counts exclude protocol framing.
- A curated case library contains only previously verified, permitted contracts; this reader validates structure but cannot prove historical provenance.
- The local serving protocol and 12B weight-storage arithmetic are implementation targets/lower bounds, not measured compatibility, memory requirements or performance.
- Authored responses, runner events and local fixture prices verify plumbing only. No model calls or live benchmark comparisons ran this session.
- No PR exists; controller/CHANGES.md contains the reviewable summary and Assumptions. Only owned directories and this STATUS file belong in the eventual commit.
