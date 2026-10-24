# Verifier CLI

## Version 3 hook operations

Implemented under the user's 2026-10-25 approval of decision 0011, the schema
freeze and these CLI additions. The checked-in proposal labels do not supersede
that approval. Use this worktree's `.venv/bin/python`:

```text
python -m verifier check --requirements FILE --workspace DIR --session-id ID --artifacts DIR --round N [--claim-audit FILE] [--final-message FILE]
python -m verifier ledger-validate --ledger FILE --workspace DIR --session-id ID --artifacts DIR
```

`DIR` for artifacts must be the exact canonical workspace directory
`.localharness/v3/sessions/<sha256-of-UTF-8-session_id>/`. Requirements and ledger
inputs must be its `requirements.json` and `ledger.json`; optional audit and
final-message inputs must already be retained within that session directory.
Paths reject absolute relative-artifact references, parent traversal and
symlinks (including aliases that point inside). Workspace paths may contain
spaces. All JSON publication is atomic; evidence files are immutable,
content-addressed snapshots under `evidence/`. Session-directory locking
serializes concurrent checks, ledger validation and bookkeeping reservation.

`check` validates the requirements schema, native ID/directory, contiguous
R-n rows, prompt hash/source excerpts, question references and successful
requirements call reference. Accounting is checked offline for schema, phase,
session/model identity, duplicate calls/phases and the two-call limit. Pin
availability and trusted code derivation remain Role 2/3 responsibilities.
The verifier never imports controller or calls a model on this path.

Every row produces pass, fail or unverifiable. `file_exists` retains the exact
file bytes or a missing-file observation. `file_unchanged` compares the exact
bytes with the pre-edit SHA-256. `signature_snapshot` uses non-importing Python
AST extraction; capture baselines with
`verifier.python_identity.signature_snapshot_bytes(source_bytes, identifiers)`.
Its canonical bytes are compact UTF-8 JSON pairs `[requested_identifier,
observed_signature]`, in configured order, followed by a newline. Identifiers
can be qualified names or signature spellings; missing signatures become null
and differ from a baseline containing them. Body-only edits preserve signatures.
Other languages, syntax/extraction failures and ambiguous bindings are
unverifiable. This is a shared helper for Role 3's pre-edit capture, not a new CLI.

`named_command` and `test_command` requirement kinds both use schema check type
`command`. The argv adapter reuses the Python allowlist (`-c`, `py_compile`,
unittest/discovery and pytest); unsupported executables/options are unavailable.
It executes with `shell=False`, a bounded deadline, process-group cleanup,
credential-free environment and the existing Seatbelt network/outside-write
denials. `cwd` is confined inside the workspace; the write boundary stays the
whole workspace, including its artifact directory. Commands are never run
unsandboxed. A host without usable Seatbelt reports unverifiable.
`input_immutability` retains before/after bytes and compares declared input
hashes as well as the probe's expected exit. Missing pre-probe dependencies,
exceptions, denied resources, timeouts and runner errors are unverifiable;
completed differing exits, missing named outputs and changed hashes/signatures
fail. Assertion/test failures remain deterministic failures. Raw stdout/stderr
are preserved, including non-UTF-8 bytes; JSON execution evidence retains argv,
cwd, exit, expected exit and deadline. Excerpts are limited to 2,000 characters.
Unavailable checks and unanswered questions cannot pass or authorize repair.

`check` writes `completion-report.json` and exits 0 whenever it publishes a
report, including failures. Its only stdout is one JSON line:

```json
{"overall":"fail","failed_rows":["R-1"],"unverifiable_rows":[],"retry_warranted":true}
```

Overall pass requires at least one row and every row passing. Computation,
provenance or publication errors exit 2 with stderr and no summary. Total budget
defaults to `HARNESS_VERIFY_BUDGET_SECONDS=450`, with the existing two-second
cleanup reserve; each command is capped at 120 seconds. Checks not started
within budget stay unverifiable. No `llm_judge` is allowed or delegated here.

The audit input is exactly the completion schema's `claim_audit` object. The
verifier checks its original-message hash, cited files/hashes/excerpts, known
row IDs and successful claim-audit call reference. Bad citations become
unsupported and are removed from structured references; the original audit is
retained in immutable evidence for inspection. A malformed/unverifiable audit
or missing final message produces an unavailable audit. Audit opinions never
override check status or cause repair. After repair/bookkeeping the original
audited message/hash is preserved and a changed current message marks it stale;
no new audit is requested. Historical lexical claims extraction remains in
`verifier.claims` for existing consumers.

Round 1 reserves `retry.used=1` and the failing IDs before publishing its first
`retry_warranted=true` summary. Only executed deterministic failures reserve it.
Round 2 requires this persisted reservation, retains the original failed IDs,
never warrants another repair and advises human review on repeated failure.
Duplicate rounds reuse checked results, refresh final-message/audit freshness
and return `retry_warranted=false`; they cannot spend another repair or audit.
Requirements must remain unchanged between rounds. Immutable report snapshots
retain earlier rounds in `evidence/`; the canonical report is the latest state.

Role 2 imports the exact Stop texts from [stop_text.py](stop_text.py):
`REPAIR_INSTRUCTION` through `repair_instruction(report, artifacts)` and
`LEDGER_REQUEST` through `reserve_ledger_request(artifacts)`. Use the repair
renderer only when the CLI summary warrants retry; it renders only failed rows
and their verified concrete evidence. The ledger reservation writes
`evidence/ledger-request.txt` before returning its text and returns `None` on
duplicate Stops. It requires repair to settle first. This separate bookkeeping
request allows no application edits, requires `validation=null`, and preserves
the application completion claims/evidence in the final response. An invalid
ledger gets an advisory, never another bookkeeping block. After that final
message, call `check` again with the settled round to refresh freshness without
re-running checks. Role 2 remains responsible for issuing native Stop blocks
and consuming these durable reservations exactly once.

`ledger-validate` extracts every listed Python identifier without importing
workspace code. Names are explicit function/class/import/assignment bindings;
qualified nested names are supported. Signatures use canonical AST spelling
(including async, argument annotations/defaults and return annotations).
Constants are literal bindings, either a bare name or `NAME = literal` for an
exact syntax-tree value. Referenced paths must be confined Python files; names
in strings/comments, unsupported languages, ambiguous bindings, missing or
changed identifiers cannot establish validity. This validates identity/presence,
not the wisdom of decisions. It checks decision/open-item IDs, exact previous
validation coverage and all prior file/identifier hashes when revalidating,
then fills a fresh hook-owned validation block. Executor-populated validation
never bypasses extraction. Valid ledgers are copied atomically to
`.localharness/v3/latest-ledger.json` under a separate root lock. Invalid current
ledgers do not replace the last valid copy; Role 2 must enforce the latest prior
session identity and must not silently inject an older copy. To revalidate for
SessionStart, validate the selected prior session's `ledger.json` against the
current workspace and compare its identity with the selected latest ledger;
an advisory prevents injection.

Ledger exit codes: 0 valid (stdout supplied ledger path), 1 invalid (stdout
visible advisory), 2 internal error (stderr only). Structurally valid ledgers
with missing/mismatched identifiers are saved with `validation.status=invalid`;
malformed schema/identity inputs are preserved and rejected.
An invalid measured validation remains invalid on repeated validation; recording
new hashes must not silently rehabilitate a stale ledger. A fresh executor
ledger is required in a later authorized session, without another Stop loop.

Verification: `.venv/bin/python -m pytest tests/verifier -q`. The v3 fixtures
cover pass/fail/unverifiable for every supported check/requirement kind,
path escapes, exact raw evidence, unsupported citations, stale audits,
round/Stop idempotence, bookkeeping reservation, ledger extraction/coverage/hash
validation and schema validation. Subprocess check outcomes are injected;
these fixtures are not host command-isolation acceptance. All eight existing
Seatbelt cases (six original plus two unittest cases), live Stop/SessionStart,
two-project smoke runs, Role 2/3 baseline/audit integration and host timing remain
pending. No nested Codex, network, model or sandbox-exec runs are required here.

## Historical version 1/2 operations

The remainder describes retained contract/judge/handoff and review behavior.
Its judge and retry rules do not apply to the version 3 hook operations above.

Run from the repository root with Python 3.11 or newer:

```text
python -m verifier check --contract contract.json --workspace DIR --transcript PATH --attempt N --out verdict.json
python -m verifier validate-handoff --handoff handoff.json
python -m verifier sample --reports DIR --n 20 [--out FILE]
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
`schemas/evaluation-report.schema.json` for version 2, or the original schema
preserved in decision 0003 for version 1. Version 1 is identified by the absent
`metrics.task_false_done_rate`; no metrics are added or inferred.

The command reads verdict artifacts listed in each task's `artifacts`. It
recognizes `verdict.json`, `verdict-N.json` and runner-prefixed names such as
`day-1-verdict-N.json` and `day-2-verdict-N.json`, including archived paths.
When a task has no listed standalone verdicts, it reads that task's listed
`result.json` and uses its inline `verdicts` array. Standalone verdicts take
precedence per task, so retained copies are counted once. Result task ID/type
must match the report. Each source file is SHA-256 checked and every verdict is
validated against the frozen verdict schema before sampling.

Absolute paths, paths relative to DIR and repository-relative
`eval/reports/DIR_NAME/...` paths are supported. Repository-relative paths are
rebased into DIR, so a report copied from another checkout remains readable.
Sources must resolve inside DIR, including symlinks. Missing, changed, invalid
or multiply listed sources, and duplicate task IDs, are input errors.

Selection uses the fixed seed 42, independently of the evaluation's seed.
Candidates are sorted by task ID/artifact path, shuffled within each task type,
and selected in rounds across a seeded ordering of task types. The sample unit
is one verdict attempt; a task can appear more than once. Up to `--n` verdicts
are selected without replacement; `--n` defaults to 20 and must be positive.
An empty verdict pool produces an empty sample, with its count logged on stderr.

The default output is `DIR/verifier-sample.json`; `--out FILE` writes to the
supplied path, allowing read-only source reports. The output parent must exist.
Stdout contains only the output path and a newline.
It records the seed, requested/available counts, report SHA-256 and selected
verdicts. Each selection records task ID/type, artifact path/hash, attempt,
verdict overall result, all item IDs/statuses/evidence/reasons unchanged, the
task's final `task_outcome`, `final_grading_outcome` and invalid reasons from the
report. Missing grading remains null, including invalid/timeout/error tasks;
it is never inferred as pass or fail. Earlier attempts are explicitly compared
with the task's final grading, not an inferred attempt-specific hidden result.
For inline verdicts, `verdict_path` and `verdict_sha256` identify the result file
and `verdict_index` is the zero-based index in its `verdicts` array. This retains
distinct sessions even when their attempt numbers restart.

The command opens no grader source, grading copy, grading log or executor log.
It does not rerun checks or call any model. Repeated runs on unchanged inputs
produce identical output bytes. Report and verdict inputs are never rewritten.
