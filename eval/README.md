# Evaluation runner

The runner writes `report.json` against the approved
`schemas/evaluation-report.schema.json`, with offline schema/format validation
and runtime checks for IDs, counts, ordering, costs and event hashes.
`eval/report.schema.json` is retired and retained only as a reference to that
shared schema. Historical reports in `reports/baseline-a-first-task/` remain
unaltered provisional evidence; they have not been reclassified as approved
reports or rerun.

The frozen command is `python -m eval run --config FILE --out DIR`.
Successful stdout is exactly the supplied output directory plus a newline;
exit codes are 0 for computed reports (including invalid tasks), 1 for input
errors and 2 for internal errors. Configs use the JSON subset of YAML.
Completed version-1 checkpoints do not call models again. Historical provisional
checkpoints require an explicit offline migration or a fresh output directory;
they are not silently relabeled as version 1. Interrupted or unsupported
streams remain invalid even after a later successful continuation.

Private graders must already exist outside the repository, supplied through
`LHM_PRIVATE_GRADERS` in the trusted parent environment. This session does not
create them. Each task's external directory contains `test_*.py`; optional
`audit-names.json` lists historical filenames. Only after all executor work
exits and the access/settings audit passes does the runner copy graders into
a fresh trusted grading copy. That copy never enters a later executor turn.
External raw logs and private copies are retained; public evidence is redacted.
Native logs are referenced with hashes as well as executor JSON streams.

Every executor, resume and control child uses a copied environment containing
`HARNESS_NESTED=1`. Executor environments exclude private locations and API keys.
The runner uses a temporary Codex home and the existing external auth symlink;
it never copies credentials or changes global configuration.

The access audit checks tool command, file-change, function-call and tool-result
events for private grader sources/copies, `~/.codex`, the sibling `codex-bridge`
folder and this repository outside the task workspace. URL/JSON encodings,
relative traversal, existing symlink aliases, denied attempts and retries are
covered. Assistant prose is excluded. Missing, truncated, unknown, unpaired or
unfinished tool evidence and unresolved variables make the audit inconclusive.
Detected or inconclusive access invalidates the task and aggregate report and
prevents grading. This is observed access auditing, not filesystem isolation
or proof that all unlogged activity is safe. Dynamic execution and additional
installed-version event forms require host review before measurement.

Harness configs select `harness=true`, an explicit `control_backend` and a
`reinstruction_limit`. The runner calls `python -m controller contract` with
an empty public case library and no handoff, validates the contract, injects
its JSON into the executor prompt, then calls `python -m verifier check` with
native transcript evidence and the public workspace. Only its bounded non-null
re-instruction resumes the same executor session. It supplies
`HARNESS_BACKEND` and `HARNESS_MAX_ATTEMPTS` in the verifier's copied environment.
Private grading is outside this loop. Contract/verdict artifacts and control
stdout/stderr are retained. `configs/harness-mocked.yaml` is a host-verification
candidate, not a measured run. Unit tests mock every controller/verifier/model
subprocess; synthetic grading remains a local process.

Reports compute seeded task-cluster bootstrap metrics (10000 resamples;
minimum 1000). Invalid tasks leave quality samples but retain costs. Any zero
original/bootstrap denominator or missing accounting produces null values and
bounds. Output tokens already include reasoning; cached input is an input
subset. `prices.yaml` explicitly pins an **unpriced offline placeholder**, not
verified market rates: no cost is fabricated and subscription usage is not
zero-dollar API usage. Replace this snapshot with verified versioned rates
before measured comparisons. Control CLI artifacts do not expose a complete
per-call accounting ledger; actual fallback transport/model and costs remain
unobserved. `control_model` and control costs stay null. Full done-claim
extraction and hash-pinned paired parity are pending; false_done_rate and parity
are undefined with reasons rather than incomplete headline measurements.

There are 100 single-session and 20 two-session public task drafts across four
types. New tasks are marked `frozen=false`, `review_status=draft` and
`grader_status=pending`. `GRADERS-PENDING.md` names all 119 candidates needing
external graders. The older bug-chunk-tail has historical grader evidence but
still needs host revalidation. Related variants share 25 families: task diversity,
specifications and negative/reference grader checks need review before freeze.
Two-session candidates include a separate day-2 prompt; execution is rejected
before model calls until handoff orchestration/observation is implemented.

Offline verification:

```sh
.venv/bin/python -m pytest tests/eval -q
git diff --check -- eval tests/eval state/STATUS-eval.md
```

No executor model, nested Codex, network or macOS sandbox-exec is invoked in this
session. Live CLI compatibility, production retry/guard behavior, private graders
and sandbox operation are pending host verification. No pilot, freeze, full run
or quality/cost comparison is claimed.

## Assumptions

- The user's priority order supersedes the older STATUS claim that the shared
  report interface is provisional; version 1 is approved.
- Public candidates may be prepared without graders, but are not eligible for
  measurement or freeze until independently graded and reviewed.
- A reference-only compatibility schema retires the provisional definition
  without deleting a file or changing the shared interface.
- Model accounting absent from the frozen CLI output remains unknown; the
  runner does not infer actual fallback transport or model identity.
