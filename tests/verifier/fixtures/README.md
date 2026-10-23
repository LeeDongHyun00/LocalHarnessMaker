# Verifier fixtures

The three workspaces implement the shared FastAPI example. `ws_pass` returns
the required health payload. `ws_fail` and `ws_claimed` return a broken payload;
their tests assert the correct payload and will fail when the optional runtime
dependencies, FastAPI and httpx, are installed. No dependencies are vendored or
added to root configuration by Role 4.

The transcripts contain synthetic report text in the measured Codex JSONL
structure: `response_item`, payload `type=message`, `role=assistant`,
`phase=final_answer`, and `content` entries with `type=output_text`. The source
for this structure is `docs/hooks-contract.md` and its exec/TUI transcript
excerpts. Unit tests read both captured excerpts and confirm `SECOND_REPLY`
is the last report. Earlier final reports, commentary, tools and user text
cannot supply claims for the latest report. Flat role/content fixtures are
rejected. Criterion IDs, numeric ranges, explicit all-criteria statements,
status/checklist rows and distinctive description words can supply claims;
generic "all done" prose is not mapped to criteria. The lexical rules are in
verifier/RULES.md.

`claim_reports.json` contains labeled synthetic final-report text and criterion
descriptions, covering positive and negative ID/list/range, collective,
description, table and checklist cases. Each expected list is the set of claimed
IDs, independent of the criterion's eventual check result. The verifier suite
checks every case and prints micro precision/recall over criterion/report pairs,
with TP/FP/FN. These controlled examples do not measure live-report accuracy.

Run `.venv/bin/python tests/verifier/smoke.py` from the repository root. It
runs the full unchanged shared contract in every workspace, validates each
output against the verdict schema, and prints the actual statuses. Exit zero
means the checker successfully produced valid verdicts, not that the task
passed. This is now a live host check: the full contract delegates SC-4 to
`python -m controller judge`, once for each workspace. It can launch nested
Codex/model calls; do not run it inside the Codex sandbox or without live-call
authorization. It was not run in the current offline session.

The golden unit tests use the first three mechanical criteria verbatim from
`schemas/examples/contract.json` and compare statuses with the corresponding
shared pass/fail examples. Command outcomes in those tests are explicitly
mocked. They do not establish a passing FastAPI integration or LLM judgment.
The claimed fixture regression injects failing command outcomes and asserts
`claimed_without_evidence` while retaining the mechanical failure output.
