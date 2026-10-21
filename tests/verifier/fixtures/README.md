# Verifier fixtures

The three workspaces implement the shared FastAPI example. `ws_pass` returns
the required health payload. `ws_fail` and `ws_claimed` return a broken payload;
their tests assert the correct payload and will fail when the optional runtime
dependencies, FastAPI and httpx, are installed. No dependencies are vendored or
added to root configuration by Role 4.

The transcripts are synthetic JSONL objects with `role` and `content`. They
are fixtures for future done-claim work, not an installed Codex transcript
format specification. The current checker validates JSONL only and does not
extract or trust completion claims.

Run `.venv/bin/python tests/verifier/smoke.py` from the repository root. It
runs the full unchanged shared contract in every workspace, validates each
output against the verdict schema, and prints the actual statuses. Exit zero
means the checker successfully produced valid verdicts, not that the task
passed. The full contract cannot pass without judge delegation.

The golden unit tests use the first three mechanical criteria verbatim from
`schemas/examples/contract.json` and compare statuses with the corresponding
shared pass/fail examples. Command outcomes in those tests are explicitly
mocked. They do not establish a passing FastAPI integration or LLM judgment.
