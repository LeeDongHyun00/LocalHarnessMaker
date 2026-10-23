# Verifier CLI

Run from the repository root with Python 3.11 or newer:

```text
python -m verifier check --contract contract.json --workspace DIR --transcript PATH --attempt N --out verdict.json
python -m verifier validate-handoff --handoff handoff.json
python -m verifier sample --reports DIR --n 20
```

Success prints exactly one output path followed by a newline. Logs go to stderr.
Exit codes are 0 for successful computation (including a failed verdict), 1 for
input errors and 2 for internal errors. Errors print no success path.
`validate-handoff` validates without rewriting and prints the supplied path.
The existing check/verdict and handoff schemas and judgment semantics apply.
Command support and actionable retry categories are documented in [RULES.md](RULES.md).
A failed verdict can have null reinstruct_message before retry exhaustion when
only contract, verifier, budget or judge transport problems remain.

## Claim observations

Every successful `check` computation writes a companion file beside `--out`,
replacing its suffix with `.claims.json`: `verdict-2.json` produces
`verdict-2.claims.json`. Failed and unverifiable verdicts still produce this
file. Stdout continues to contain only the verdict path and newline.

```json
{
  "items": [
    {"id": "SC-1", "claimed": true, "clause": "SC-1 passed.", "status": "pass"},
    {"id": "SC-2", "claimed": false, "clause": "", "status": "fail"}
  ],
  "summary": {
    "claimed_items": 1,
    "claimed_and_pass": 1,
    "claimed_and_fail": 0,
    "claimed_and_unverifiable": 0,
    "unclaimed_items": 1
  }
}
```

`items` contains exactly one observation per contract criterion, in contract
order. `status` is copied from that criterion's verdict item, including judge,
quality-warning and budget-exhausted outcomes. `clause` is the first supporting
clause copied verbatim from the latest executor final report (the complete row
for tables), with outer whitespace trimmed. It is empty for
unclaimed criteria. No final report means all criteria are unclaimed. Empty
criteria produce empty items and zero counts; the synthetic `contract-quality`
verdict diagnostic is not a criterion and is excluded.

The summary partitions all criteria:
`claimed_items = claimed_and_pass + claimed_and_fail + claimed_and_unverifiable`;
`claimed_items + unclaimed_items = len(success_criteria)`.
It supplies the claim denominator without inferring claims from failure reasons.
For verdict-based confirmed false claims, use `claimed_and_fail / claimed_items`
when the denominator is positive. Preserve claimed-and-unverifiable separately:
uncertainty does not establish a false claim. These are verifier observations,
not trusted hidden-grader results or a measured evaluation-wide metric. The
evaluation runner must ingest the sidecars before it can use these counts.

Both artifacts are serialized from the same report observation and verdict,
after child-process cleanup. The sidecar is written first, then the verdict;
stdout is printed only after both writes succeed. An artifact write error exits
2 with empty stdout. The two writes are not a filesystem transaction: consume
neither artifact from an unsuccessful invocation, even if an older or partially
written file remains. Input/internal computation errors do not publish files.
The existing verdict schema, CLI arguments and exit-code meanings are unchanged.

Matching includes ID lists/ranges, all-criteria statements, status rows and
distinctive description words; see [RULES.md](RULES.md) for exact scope and
negative/exception handling. The labeled synthetic fixture is
`tests/verifier/fixtures/claim_reports.json`. Running
`.venv/bin/python -m pytest tests/verifier -q` prints its micro precision/recall
and TP/FP/FN in the terminal summary. Synthetic accuracy does not establish
accuracy on live reports; Claude's live harness run remains pending.

## Judge accounting on stderr

After each attempted judge delegation, `check` copies every captured child stderr
line starting with `control_call ` or `control_cli_events ` to its own stderr,
unchanged and in the original order. It copies no other child diagnostics and
does not parse or rewrite the forwarded JSON. `forwarded_control_calls` counts
the forwarded `control_call ` lines, including failed/retried calls. A missing
final newline receives a separating newline before the summary.

Immediately after the forwarded records, it writes exactly one summary line:

```text
judge_delegation {"accounting_complete":true,"backend":"codex_cli","criterion_id":"SC-4","forwarded_control_calls":2,"outcome":"completed"}
```

The prefix is exactly `judge_delegation ` and the JSON is compact with sorted
keys. Its fields are:

| Field | Value |
| --- | --- |
| `accounting_complete` | Boolean, following the rules below |
| `backend` | Requested backend string (`codex_cli`, `cheap_api` or `local`) |
| `criterion_id` | Delegated criterion ID string |
| `forwarded_control_calls` | Integer count of forwarded `control_call ` lines |
| `outcome` | `completed`, `failed`, `timeout` or `not_launched` |

`completed` means a valid judgment was returned, including judgments with status
fail or unverifiable. `failed` means delegation/validation failed after launch;
`timeout` means the judge deadline expired. `not_launched` means no child process
ever existed (for example, process creation failed).

`accounting_complete` is true only when no child existed and nothing was
forwarded, or when the child exited by itself, all stderr was read and at least
one `control_call ` line was forwarded. A nonzero child exit can therefore have
complete accounting. Timeout, verifier-killed children, truncated/unreadable
stderr and launched children without `control_call ` records always have false
accounting completeness. Child exit by signal is conservatively incomplete.

The records and summary are flushed before returning, including timeout,
shutdown and budget-limited delegation. A criterion never delegated (budget
exhausted before dispatch, mechanical checks or contract-quality rejection)
prints no delegation records. The existing `verifier elapsed_seconds=...`
timing line follows the delegation blocks; it remains a separate stderr record.
Consumers must count forwarded calls once and use summary completeness to
detect missing accounting. No accounting fields are added to verdict JSON or
stdout. The verifier never imports the controller.

## Human review sample

`sample` reads `DIR/report.json`, validates it offline against
`schemas/evaluation-report.schema.json`, and reads only verdict artifacts listed
in each task's `artifacts`. It recognizes `verdict.json`, `verdict-N.json` and
runner-prefixed names such as `day1-verdict-N.json`, including archived paths.
Absolute paths and paths relative to DIR are supported; verdicts must resolve
inside DIR, including symlinks. Every listed verdict is SHA-256 checked and
validated against the frozen verdict schema before sampling. Missing, changed,
invalid or multiply listed verdicts, and duplicate task IDs, are input errors.

Selection uses the fixed seed 42, independently of the evaluation's seed.
Candidates are sorted by task ID/artifact path, shuffled within each task type,
and selected in rounds across a seeded ordering of task types. The sample unit
is one verdict attempt; a task can appear more than once. Up to `--n` verdicts
are selected without replacement; `--n` defaults to 20 and must be positive.
An empty verdict pool produces an empty sample, with its count logged on stderr.

The output is `DIR/verifier-sample.json`; stdout contains that path and a newline.
It records the seed, requested/available counts, report SHA-256 and selected
verdicts. Each selection records task ID/type, artifact path/hash, attempt,
verdict overall result, all item IDs/statuses/evidence/reasons unchanged, the
task's final `task_outcome`, `final_grading_outcome` and invalid reasons from the
report. Missing grading remains null, including invalid/timeout/error tasks;
it is never inferred as pass or fail. Earlier attempts are explicitly compared
with the task's final grading, not an inferred attempt-specific hidden result.

The command opens no grader source, grading copy, grading log or executor log.
It does not rerun checks or call any model. Repeated runs on unchanged inputs
produce identical output bytes. Report and verdict inputs are never rewritten.
