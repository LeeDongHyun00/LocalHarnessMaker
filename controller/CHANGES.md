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

Claude's supplied before-measurement is 30/30 schema-valid, 39 criteria (4 command,
10 file_exists, 13 regex, 12 llm_judge), 11 contracts containing only llm_judge and
26 without command checks. The host evidence file was not edited. The after-run
is pending host verification: compare llm_judge share and contracts without
mechanical criteria, including quality-gate failures. The unchanged measurement
adapter allows one call per sample, so it records requests needing a quality
retry as failures rather than measuring production regeneration recovery.

Applied approved decision 0007: D-3 local Gemma 4 12B and D-5 QLoRA are
dropped. LOCAL.md and STATUS no longer describe them as pending work. The
version 1 local selector, disabled configuration and fail-closed adapter are
unchanged. Local comparison/parity is not measured.

Added `python -m controller.measure_contracts` for Claude's pending host D-4
measurement of the 30 authored requests. It prints call count and estimated
API-equivalent cost before any calls and refuses execution without
`--i-have-approval`. With the current snapshot and default planning allowances,
the estimate is USD 0.066000 for at most 30 calls. Each sample invokes the
existing contract CLI implementation using codex_cli and an internal injected
single-generation adapter, without HTTP fallback or regeneration. Production
routing and public CLI flags remain unchanged.

The JSON summary records per-sample schema validity, assumptions count, counts
by check type, log-derived latency and cost, and totals including llm_judge
share. Failed samples retain their exit code and controller errors; absent
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

`.venv/bin/python -m pytest tests/controller -q`: 176 passed in 1.98s.
The new mocked tests exercise approval refusal, all 30 samples, log accounting,
single-generation failures, no fallback even with an API key, and null costs
when CLI usage is absent. No live call, network, nested Codex or macOS
sandbox-exec check ran. The full suite is reserved for coordinated host
verification before merge. No staging or commit was performed.

## Assumptions

- When tests are mentioned without a runner, unittest discovery is a proposed
  dependency-free default for user review, not a verified project convention.
- The quality gate requires at least one mechanical criterion, as requested;
  it does not impose a check-type quota or rewrite generated criteria itself.
- The supplied before-run is host evidence. The after-run must preserve the
  original 30 prompts; new unittest samples exercise offline regressions only.
- The authored requests-v1 set is the D-4 population; the original ten samples
  overlap it and are not duplicated. Only request text is sent to the model.
- The estimate uses 17,000 input and 1,000 output tokens per sample without cache
  discounts. These are overridable planning allowances, not hard spending caps;
  price snapshot rates are the existing API-equivalent planning rates.
- The summary is an internal controller artifact, not a shared evaluation
  report. It measures codex_cli only; cheap_api and local remain not measured.
- Host verifications and commit identity are supplied by the user. The plugin
  evidence path is recorded without independently reading or rerunning it.
- No PR exists. This file supplies the reviewable change summary and Assumptions.
