# Verifier first task — 2026-10-21

Implemented command, file-existence, and regex rules plus the `verifier check`
CLI. Commands compare exact exit codes and optional exact stdout, retaining
the last 50 stdout lines as evidence. Regex evidence includes up to ten matching
lines. Missing command dependencies, denied resources, invalid regexes, and
external file paths produce unverifiable results. Missing required files fail
file-existence checks. Every verdict is schema-validated; unverifiable items
prevent an overall pass. Empty/all-judge contracts warn on stderr.

The initial command runner accepts direct Python compile, pytest, and inline
checks, rejects unsupported commands and obvious destructive calls before
execution, and runs under macOS Seatbelt. The kernel denies all network access
and file writes outside the canonical workspace, including dynamic external
paths. Unsupported platforms fail closed. Commands have a 120-second default
timeout and process-group termination. Runner injection supports offline unit
tests without importing the controller. API credentials are not forwarded.

Added three FastAPI workspaces and synthetic transcripts, mechanical golden
tests derived from the shared example, and a repeatable smoke helper. Only
Role 4 paths and its STATUS file are changed. The canonical hook document
appeared during the session and was read; it publishes hook evidence but does
not yet define done-claim transcript parsing.

## Verification

`.venv/bin/python -m pytest tests/verifier -q` passed 67 tests. These cover
pass/fail/unverifiable outcomes for all three rules, exact stdout comparison,
evidence limits, schema validation, controller import independence, CLI exit
codes/stdout, contract quality warnings, pre-execution command rejection,
symlink escapes, and real macOS timeout/network/external-write enforcement.
Repeated mocked input produced identical verdicts; raw command stdout can
still contain nondeterministic values such as pytest timings.

Three real CLI runs against the unchanged shared contract each exited zero,
printed one artifact path, and emitted schema-valid failing verdicts. SC-1
compiled successfully in all workspaces; SC-2 and SC-3 were unverifiable
because FastAPI is absent; SC-4 was unverifiable because judge delegation is
not implemented. Measured verifier overhead excluding commands was
0.006–0.009 seconds in those three runs. These observations do not establish
a fully passing FastAPI integration or general production latency.

## Remaining scope

D-1 needs live FastAPI pass/fail fixture evidence once its optional runtime is
available. D-2 still needs claims.py, bounded re-instruction, broader command
support and sandbox hardening, and hook integration. `reinstruct_message` is
currently always null, so this first-task CLI must not yet drive a production
continuation loop. The claimed fixture is prepared but does not yet produce
`claimed_without_evidence`. D-3 handoff validation, judge delegation, and human
review sampling are unimplemented. The shared judge input/output interface
must be resolved by Role 1 first. No merge or full-suite run was performed.

## Assumptions

- Empty Remaining selects the First task for this session; later dated deliverables remain separate work.
- JSONL is provisional. Fixture `role`/`content` fields are synthetic and are not parsed as installed Codex reports.
- Schema resources are read from this source checkout; installed-wheel resources are unverified.
- The source-schema requirement of at least one verdict item is satisfied for an empty contract with the diagnostic ID `contract-quality`; no success criterion is invented or reported as passed.
- The initial runner deliberately supports a small set of Python checks on macOS. Rejecting unsupported commands is unverifiable, never pass.
- The static command filter is defense in depth. Full destructive-operation auditing, bounded output capture, read/secret isolation, and cross-platform isolation are not claimed complete by these first-task tests.
- No PR was requested or created. This change summary and the STATUS file preserve Assumptions for a future PR description.
