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
a fresh trusted grading copy under the separate temporary
`lhm-retained-grading/` location. Copies are retained for review, outside
executor runtimes. Every task audits that retained location, every other
`lhm-eval-*` runtime in the temporary directory (including previous runs),
legacy grading copies in its own runtime, and the private source root.
A later executor can reach these paths because reads are not denied;
observed access invalidates the task. External raw logs are retained;
public evidence uses redacted labels and hashes.
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
unfinished tool evidence and unresolved operands make the audit inconclusive.
Shell commands use shlex, event cwd/workdir and tracked cd/pushd/popd locations.
Literal zsh/bash/sh `-c`/`-lc` wrappers are unwrapped before operand analysis;
single or double wrapper quotes do not count as quotes inside an operand.
Quote checks use each inner word's own spelling. Unresolved quoting/escaping
inside a path remains inconclusive.
A glob is bounded when its static directory prefix resolves inside the workspace
and no `..` component follows its first wildcard. Such globs may audit clean
even with no current matches. Concrete matches still resolve through symlinks
and are checked for protected access; globs outside that boundary remain
inconclusive unless protected access is detected. Values of rg `-g`/`--glob`,
find `-name`/`-iname`/`-path`, and grep `--include` are filter patterns rather
than filesystem operands. Recursive commands still audit their start paths,
including the current directory when implicit.
Parse failures, named-user tildes and other unresolved expansions remain
inconclusive; concrete canonical paths compare without case. Environment
variable expansion, including `$HOME`, remains conservative.
Recursive search/list/copy/archive operands covering an ancestor of a protected
root are access_detected. Grader lines of at least 16 normalized characters are
hashed across the private task family; matching tool output is access_detected.
Only hashes, labels and redacted evidence are retained in audit results.
Decode-and-execute pipelines such as `base64 -d | sh` are inconclusive.
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
subset. `prices.yaml` pins `openai-standard-short-2026-10-22-v1`, using the
user-supplied Claude host fetch of OpenAI pricing (checked 2026-10-22): Standard
tier, up to 272K input tokens. The source records the URL and absence of a
provider version/date. Unknown models/tiers, long-context turns and incomplete
tokens retain null costs; null propagates to accounting and cost_per_pass.
Standard is the CLI baseline assumption when no tier evidence is present;
observed non-Standard tiers override it. Subscription usage is not zero-dollar
API usage. Historical reports are preserved. Control CLI artifacts do not expose a complete
per-call accounting ledger; actual fallback transport/model and costs remain
unobserved. `control_model` and control costs stay null. Full done-claim
extraction and hash-pinned paired parity are pending; false_done_rate and parity
are undefined with reasons rather than incomplete headline measurements.

Task set version 1 contains 100 single-session and 20 two-session public tasks
across four types, all marked `frozen=true`. The user authorized freezing after
Claude's host verification and independent mutation testing (commits `80205d3`
and `ad7d7be`); no surviving mutant changes specified behavior.
`GRADERS-PENDING.md` retains the validation inventory despite its historical name.
Only the freeze flag changed in public task files; historical review fields remain
unchanged. Further task-content changes require a separate version 2.
The runner rejects any selected task whose freeze flag is missing or not boolean
true before external work, including when resuming a checkpoint.
Claude must recompute the final digest on the host with
`python -m eval.runner.validate_graders` and pass it to Role 1 for
`docs/eval-freeze.md`; the previous digest predates the metadata freeze.
Two-session tasks include a separate day-2 prompt; execution is rejected
before model calls until handoff orchestration/observation is implemented.

Offline verification:

```sh
.venv/bin/python -m pytest tests/eval -q
git diff --check -- eval tests/eval state/STATUS-eval.md
```

No executor model, nested Codex, network or macOS sandbox-exec is invoked in this
session. Live CLI compatibility, production retry/guard behavior and sandbox
operation are pending host verification. Freeze preparation is complete; the
final host digest and Role 1 record remain pending. No pilot, full run or
quality/cost comparison is claimed.

## Assumptions

- The user's priority order supersedes the older STATUS claim that the shared
  report interface is provisional; version 1 is approved.
- The user's report of Claude's host verification authorizes the version-1
  metadata freeze; private validation is not rerun in this sandbox.
- A reference-only compatibility schema retires the provisional definition
  without deleting a file or changing the shared interface.
- Model accounting absent from the frozen CLI output remains unknown; the
  runner does not infer actual fallback transport or model identity.

Incomplete runs halt without publishing a report and retain checkpoints for
recovery. A report requires the complete configured task set; this preserves the
shared schema without treating partial STOP-E1 evidence as a valid comparison.

Offline grader mutation validation uses
`.venv/bin/python -m eval.runner.validate_graders --private-root "$PRIVATE_ROOT" --tasks all --mutants 10000`.
The limit applies per task, across application and submitted regression overlays;
10000 currently covers every generated mutant. Operators replace comparisons,
swap binary addition/subtraction and boolean and/or, increment integer literals,
replace returns with None, drop slice bounds/steps, and remove not. Each mutant
has exactly one AST edit. Ordering is deterministic (manifest file order, then
AST traversal and operator order), with duplicate source results removed.

Mutation mode prints only task identifiers and killed/survived/equivalent counts.
It returns success only when each task kills at least 90% of its non-equivalent
mutants. A passing reference control is required under the same two-second
per-grading deadline; assertion failures and deadline expiry kill mutants.
At most four offline task validations run concurrently. No executor is launched.

Review data is written beneath the explicitly supplied private root, in
`.mutation-records/TASK.review.json`. Manually reviewed equivalences belong in
`.mutation-records/TASK.equivalences.json`, as an object mapping review IDs to
objects with a nonempty `reason`. IDs bind the entire reference overlay, mutated
source, target and public prompt/expected hashes. Survivors are never classified
equivalent automatically. Validation and mutation workspaces, logs and grading
copies stay under the private root and are cleaned on exit, including failures;
evaluation runs retain their existing grading-copy behavior.


## Ten-task A/B pilot preparation (2026-10-22)

`configs/pilot-a.yaml` and `configs/pilot-b.yaml` pin identical task lists, seed 0,
CLI version, zero retries, harness off and 600-second task deadlines. A uses
medium; B uses max. The [estimate](reports/pilot-estimate.md) documents deterministic
family selection, the 3/3/2/2 type split, token/cost calculations, assumptions
and host commands. The legacy single-task `configs/pilot.yaml` stays unchanged.
The exact bundled pilot configs with the published estimate pass the batch
preflight and print the estimate to stderr; other batches of ten or more calls
remain blocked. Host approval is still required before the pilot is run.

`run-diagnostics.json.executor_runs` and task `result.json.executor_runs` retain
per-attempt tokens and primary plan used_percent from native token_count events,
with timestamps and complete rate_limits. Before is the last native observation
at or before process start; after is the last during the process. Missing
observations stay null; first_observed_during_run is separate. This does not
claim a true pre/post measurement when the native log has no such sample.
Plan usage cannot be predicted from tokens. Existing raw/native evidence and
hash retention remain in place; no frozen report fields were added.

Task set v1 is frozen at `7cdaf3b`, full-set digest
`b78913b04280f6696d419d2afdc96b152675973d82f05199ddef848986285d1f`,
recorded in `docs/eval-freeze.md`. This supersedes the earlier pending-freeze
notes below/in historical changes. Pilot metadata currently fingerprints the
selected subset using the existing runner algorithm; compare identical A/B
subset hashes and retain the full source-population digest in the estimate.
SC-5 results, five manual A reviews, host prerequisites and full-run approval
remain pending. No executor/model or private-root access occurred in preparation.
