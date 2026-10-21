# Controller update — 2026-10-21

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

`.venv/bin/python -m pytest tests/controller -q -s`: 131 passed. The original
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
