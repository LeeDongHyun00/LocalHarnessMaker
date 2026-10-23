# Controller update — 2026-10-23

Contract prompt v2 now derives mechanical checks from request-named files,
Python modules/functions and tests. It requests py_compile for named Python
files, the named supported test command, or standard discovery with the runner
and discovery choice recorded as assumptions for review. unittest requests stay
with unittest. Missing behavior, dependencies and workspace facts remain unknown.
Scope/style requirements may still use llm_judge when objective checks cannot
express them. The template teaches only the approved py_compile, pytest,
unittest and read-only python -c command forms.

Generation now checks schema-valid contracts for mechanical success criteria
when lexical request hints identify files/modules, functions or tests. A
judge-only result gets one targeted regeneration; a repeated deficiency fails
explicitly. Schema retries and CLI-to-HTTP fallback continue sharing the existing
three-generation budget and usage accounting. The gate checks criterion types;
it does not prove command acceptance, meaningful test collection or behavioral
coverage. Its lexical recognition is not a complete natural-language parser.
Schemas, public CLI flags, analyze.py metadata and escaped data blocks are unchanged.

Added authored unittest/discovery fixtures and regressions for quality failure,
schema retries, fallback budget exhaustion, accounting and injection boundaries.
Updated existing golden responses to contain mechanical checks where required
and translate the direct script check into python -c. The original 30 measurement
request texts/IDs are unchanged; these mock responses do not measure model quality.

D-4 host measurements are recorded in LOCAL.md and STATUS. Before v2:
30/30 schema-valid, 39 criteria (4 command, 10 file_exists, 13 regex,
12 llm_judge; share 0.307692), 11 judge-only contracts and 26 without command
checks; 51 assumptions, USD 0.03600314 and 237.186616 s summed call latency.
After v2 with the old single-call adapter: 27/30 schema-valid, 38 criteria
(6 command, 11 file_exists, 12 regex, 9 llm_judge; share 0.236842), 5 judge-only
contracts and 21 without command checks; 51 assumptions, USD 0.01779202 and
295.212116 s. ambiguous-tests, scoped and data-csv failed because SingleCallBackend
refused the quality gate's targeted regeneration. These supplied host results
are not production recovery measurements; valid-output shares have different
populations. The evidence files remain untouched. Claude's revised host rerun
is pending.

Applied approved decision 0007: D-3 local Gemma 4 12B and D-5 QLoRA are
dropped. LOCAL.md and STATUS no longer describe them as pending work. The
version 1 local selector, disabled configuration and fail-closed adapter are
unchanged. Local comparison/parity is not measured.

Added `python -m controller.measure_contracts` for Claude's pending host D-4
measurement of the 30 authored requests. It prints call count and estimated
API-equivalent cost before any calls and refuses execution without
`--i-have-approval`. With the current snapshot and default planning allowances,
the estimate is USD 0.198000 for at most 90 calls. Each sample invokes the
existing contract CLI implementation using codex_cli and an internal injected
production RoutedBackend with HTTP fallback disabled in memory. Schema retries
and one targeted quality regeneration share production's three-generation
command budget; transport failures stop the sample. Production routing and public CLI flags remain unchanged.

The JSON summary records per-sample schema validity, assumptions count, counts
by check type, log-derived latency and cost, and totals including llm_judge
share, gate firings (one per affected sample), generations and USD. A code-owned
production gate log records detection even when the remaining budget prevents
regeneration. Per-sample costs and latency sum every logged generation, including
failed/rejected results. Failed samples retain their exit code and controller
errors; absent
contracts have null counts. Costs include measured failures and remain null
when accounting is incomplete. cheap_api is explicitly not measured. LOCAL.md
documents the preview, approved host command and interpretation.

Recorded Claude's completed primary gpt-6-luna contract/judge/handoff host calls
and the live plugin contract/handoff demo in STATUS. The measured latencies
15.6 s contract (20.0 s concurrent), 14.4 s judge and 13.2 s handoff informed
35 s deadlines (commit 0d57e36). These supplied results were not rerun here.
Remaining host work distinguishes HTTP fallback and production guard/retry
integration from the already completed primary CLI/demo checks.

The unknown contract cost_estimate case retains honest exit 2 under version 1;
no interface revision is planned, as directed by the user and integration
review 1. Unknown costs are never fabricated as zero.

## Verification

`.venv/bin/python -m pytest tests/controller -q`: 183 passed in 2.18s.
The new mocked tests exercise approval refusal, all 30 samples, log accounting,
quality/schema regeneration sequences, persistent quality rejection, final-slot
gate detection, three-call exhaustion, no fallback even with an API key, and
null costs when any CLI generation has unknown usage. No live call, network,
nested Codex or macOS
sandbox-exec check ran. The full suite is reserved for coordinated host
verification before merge. No staging or commit was performed.

## Assumptions

- When tests are mentioned without a runner, unittest discovery is a proposed
  dependency-free default for user review, not a verified project convention.
- The quality gate requires at least one mechanical criterion, as requested;
  it does not impose a check-type quota or rewrite generated criteria itself.
- Both recorded runs are host evidence. The revised host rerun preserves the
  original 30 prompts; new unittest samples exercise offline regressions only.
- The authored requests-v1 set is the D-4 population; the original ten samples
  overlap it and are not duplicated. Only request text is sent to the model.
- The estimate uses 17,000 input and 1,000 output tokens per generation
  without cache
  discounts. These are overridable planning allowances, not hard spending caps;
  price snapshot rates are the existing API-equivalent planning rates.
- The summary is an internal controller artifact, not a shared evaluation
  report. It measures codex_cli only; cheap_api and local remain not measured.
- Host verifications and commit identity are supplied by the user. The plugin
  evidence path is recorded without independently reading or rerunning it.
- No PR exists. This file supplies the reviewable change summary and Assumptions.
