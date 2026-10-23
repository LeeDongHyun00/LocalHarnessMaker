# Controller update — 2026-10-23

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

`.venv/bin/python -m pytest tests/controller -q`: 153 passed in 1.85s.
The new mocked tests exercise approval refusal, all 30 samples, log accounting,
single-generation failures, no fallback even with an API key, and null costs
when CLI usage is absent. No live call, network, nested Codex or macOS
sandbox-exec check ran. The full suite is reserved for coordinated host
verification before merge. No staging or commit was performed.

## Assumptions

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
