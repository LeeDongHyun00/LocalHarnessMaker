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
