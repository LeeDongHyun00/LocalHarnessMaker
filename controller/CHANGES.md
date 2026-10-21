# Controller update — 2026-10-22

Cloud deadlines now use 35 s for both codex_cli and cheap_api, superseding
the initial 25 s setting. Claude's repeated host contract call passed under the
25 s deadline but took 20.0 s with four Codex jobs sharing the subscription,
compared with 15.6 s idle. No API key is configured on this Mac, so a CLI timeout
would fail without HTTP fallback; the revised setting provides more headroom.
The original contract/judge/handoff latencies were 15.6/14.4/13.2 s on
codex-cli 0.162.0-alpha.17.2 with gpt-6-luna. STATUS records the user-supplied
evidence; no live calls ran here.

Three deadlines plus approximately 1 s startup per call total
3 * (35 + 1) = 108 s, within judge's unchanged 120 s budget and the handoff
budget Role 2 is raising to 120 s. The observed 15.6–20.0 s contract latency
fits the plugin's approved 30 s budget, but the controller deadline exceeds it:
the plugin enforces the 30 s cutoff. This does not guarantee contract completion
under further load or leave time for three attempts. Local configuration is
unchanged. Regression tests pin the cloud deadlines and bound the worst CLI/HTTP
combination against the revised 120 s smallest multi-call caller budget.

D-4 observation only: the live example contract put SC-1 llm_judge before regex
and command criteria despite the mechanical-check preference already present in
the template. No prompt tuning, evaluation-task reading or schema changes were
performed. HTTP fallback, production hook integration and the real D-4 comparison
remain pending host verification, including the new deadline behavior.

H4 is fixed: CLI executable lookup failure and runner spawn OSError record zero
input, cached-input and output tokens and zero API-equivalent USD. The route log
retains the actual CLI backend and fallback reason. With approved HTTP fallback,
contract and judge totals therefore equal the HTTP call's measured usage when
the CLI never started. The OSError handler that assigns zero surrounds only the
runner call; output-file errors after the runner returns retain measured or
unknown usage.

A CLI process that started and then failed, exceeded its deadline or supplied no
usage retains unknown accounting where measurements are missing. After a valid
HTTP fallback, judge reports null totals; contract still exits 2 with
"Generation has no reliable usage accounting", prints no success path and
preserves existing output. This is the honest result under the version 1
contract schema, whose cost_estimate forbids null. Role 1 must decide whether to
revise that interface; this change does not alter schemas or fabricate zero for
started processes.

The approved `codex_cli` selector is available on contract, judge and handoff;
`--backend` remains required. Configuration selects it as primary. Command-scoped
routing shares a maximum of three generation calls across regeneration and one
CLI-to-HTTP fallback. Only CLI transport failures allow that transition, with
the same model, an environment API key and a remaining slot. Later calls stay
HTTP. Local never falls back to cloud. Every child invocation uses an isolated
read-only workspace, injectable runner, piped input, bounded timeout and a copied
environment with HARNESS_NESTED=1.

Judge validates the published single-criterion input before generation, requests
only status/reason/evidence, and supplies identity and summed usage in code.
Fail and unverifiable remain successful computations. Evidence must contain
llm_judge; conflicting provider identity is an internal error. Unknown counts,
costs and prices stay null. Price references pin the existing snapshot by date,
model and SHA-256. CLI JSONL events and per-call backend/model/pricing/accounting
are logged separately from the one-path success stdout. Contract's required
numerical accounting still fails explicitly if any call has unknown cost/usage.

Judge reads a deterministic UTF-8 artifact snapshot with a configured byte cap.
Its omitted manifest records excluded dependency/VCS directories, non-text files
and oversized evidence. Prompts require unverifiable when needed evidence is
unavailable. Missing/unreadable paths and symlink evidence are input errors.
No artifact commands are executed. Handoff validates contract/verdict IDs and
status consistency before generation; output must cover every criterion once,
with only passed criteria in done and every other criterion in remaining.
All three commands preserve existing artifacts on generation failure.

Effort v1 deduplicates normalized requirement segments while retaining the
existing explainable thresholds and code-owned metadata. Contract prompt v1
accepts up to three positive BM25 matches from schema-valid contract JSONL files.
Library owners must curate previously verified cases; the reader does not prove
historical verification, collect cases or create training data. The seed library
remains empty. Thirty hand-authored samples exercise all three adapters offline.

The local adapter sends strict JSON-schema constraints to a configurable loopback
chat-completions server. It is disabled by default pending host verification of
the server build, model alias, constrained output and memory. LOCAL.md documents
that boundary and weight-storage arithmetic without claiming measured serving
requirements. Local prices remain unknown; no zero cost is fabricated.

## Verification

`.venv/bin/python -m pytest tests/controller -q`: 148 passed in 5.58s, including
three deadline checks for the revised settings. Previous H4 coverage remains green. New mocked
CLI/HTTP regressions cover all three never-started cases for contract and judge,
unknown accounting after deadline/nonzero/missing-final-message failures, exact
path stdout, output preservation, schema validation, per-call records and the
same-model fallback guard. Invalid-message and missing-CLI tests are separate.
The original
fixture report is 10/10 schema-valid and 4/4 ambiguous assumptions. Each adapter's
expanded mocked report is 30/30 schema-valid and 8/8 ambiguous assumptions.
Tests include fallback exhaustion, unavailable CLI, nonzero exit and timeout,
partial/unknown accounting, model conflicts, injected request delimiters,
code-owned metadata, handoff contradictions, retrieval and CLI output/error rules.

No network, nested Codex, live model or macOS sandbox-exec checks ran this session.
Live quality, semantic injection resistance, actual local memory/latency, empirical
effort calibration and control/executor cost ratios remain pending host work.
The full repository suite remains a before-merge check; no merge, staging or
commit was performed. Only controller paths, tests/controller and its STATUS
were changed. Shared interfaces and other roles' implementation remain untouched.

## Assumptions

- Host measurements are user-supplied Claude evidence, not rerun here. The 1 s
  per-call startup allowance is approximate; HTTP latency is not yet measured.
- The approved decisions and published schemas supersede old STATUS interface
  blockers. No new shared interface is needed.
- No exact preflight tokenizer dependency is necessary for this implementation:
  byte counts serve only as effort features; provider counts own accounting.
- The existing gpt-6-luna snapshot contains user-specified API-equivalent planning
  rates, not verified billed prices. Synthetic test prices are fixtures only.
- Artifact context is bounded UTF-8 text; omitted evidence is explicitly visible
  to the judge. Configured exclusions are .git, .venv, __pycache__ and node_modules.
- Local serving compatibility, capacity and pricing require host verification
  before enablement. The mock suite cannot establish model quality or speed.
- No PR exists. This file supplies the change summary and Assumptions for review.
