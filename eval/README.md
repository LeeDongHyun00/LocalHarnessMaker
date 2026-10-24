# Evaluation runner

The runner writes `report.json` against the approved
`schemas/evaluation-report.schema.json`, with offline schema/format validation
and runtime checks for IDs, counts, ordering, costs and event hashes.
`eval/report.schema.json` is retired and retained only as a reference to that
shared schema. Historical reports in `reports/baseline-a-first-task/` remain
unaltered provisional evidence; they have not been reclassified as approved
reports or rerun.

## Version 2 frozen public population

[DESIGN.md](tasks-v2/DESIGN.md) specifies the separate harder population before
construction: 20 families × 5 task variants. The unchanged pilot contains
ledger, reservations, routing and inventory, with four single-session types and
one two-session task per family (20 tasks, 24 executor sessions). Each task has
seven production modules, public regressions, 12 numbered requirements (15 over
two sessions), explicit constraints and a protected verification command.
Final graders and references remain external. No version 1 public task or grader
is changed. [Validation counts](reports/pilot-v2-validation.md) contain task IDs
and numbers only.

The user-supplied decision 0008 rerun passed 15/19 valid tasks (0.789,
95% interval 0.579–0.947), above the 30–70% target. The approved full candidate
keeps every pilot task and adds 16 complete families / 80 tasks. New tasks use
16 numbered requirements (18 across two sessions), at least four interacting
requirement pairs, protected files, exact errors, independent inputs/results,
and shared computation across facade, rendering and batch call sites. Day 2
depends on three day-1 policy decisions without restating their values.
No task was selected or dropped on its calibration outcome.

[Full validation counts](reports/full-v2-validation.md) publish task IDs and
numbers only. Graders, coverage manifests, references and mutation review
material remain external. Grader assertions cannot share a line with public
inputs. Executor-written corpus overlap is warning-only; validation reports the
number of corpus files actually examined and warnings per task. References must
pass, starters must fail and every requirement must have executed coverage.
Mutation runs exhaust the generated AST population, retaining hash-bound private
reviews for equivalents rather than treating them as killed.
For host validation, pass the complete task list from full-v2-a.yaml to
`eval.runner.validate_graders`, both normally and with `--mutants 100000`.
The literal `--tasks all` selects v1, so it must not be used for this population.
Require zero surviving mutants and zero errors for every task; the tool's
generic 90% mutation exit threshold alone is insufficient for this candidate.

[Full A](configs/full-v2-a.yaml) and [full harness](configs/full-v2-harness.yaml)
select all 100 tasks in lexicographic order (120 required sessions).
[Full B](configs/full-v2-b.yaml) selects the 80 single-session tasks at Sol max;
its task_population pins all 100 tasks. A and harness use Sol medium. All request
Fast priority, Codex 0.163.0-alpha.11.1, seed 0 and calibration=false. Harness
selects codex_cli with reinstruction_limit=2; all have retry_limit=0.
STOP-3 estimates: [A](reports/full-v2-a-estimate.md),
[B](reports/full-v2-b-estimate.md), [harness](reports/full-v2-harness-estimate.md).
These are workload scenarios priced at the existing Fast snapshot, not caps or
measurements. Dynamic judge criteria require a revised harness estimate.
All 100 meta.json files now have frozen=true (2026-10-24); only that flag
changed in public task files. User-supplied host validation passed: 100 distinct
grader directories, zero public private markers, 2,994 killed independent
mutants, 6 recorded equivalents and zero survivors. The full configs pass the
public freeze check and select the same complete population digest, including
B through task_population. No live evaluation was run in this worktree.

The final digest is pending external grader contents. On the host main checkout
after transferring these exact changes, run:

```sh
.venv/bin/python -m eval.freeze_v2 --private-root "$LHM_PRIVATE_GRADERS"
```

This read-only command prints counts by type/family and runner-compatible
public-plus-private hashes without model or grader execution. It uses tracked
public inputs, external test_*.py contents and the existing v2 root namespace;
see [freeze procedure](tasks-v2/DESIGN.md#final-digest-procedure-host-required).
Role 1 publishes docs/eval-freeze-v2.md from that final output. A public-only or
pre-freeze candidate hash cannot substitute for it. Spending approval remains
required before host runs.

`task_root` is an optional config field, default `eval/tasks`; v2 selects
`eval/tasks-v2`. It is a canonical repository-relative public directory under
`eval/`. Task population, selected/population digests, freeze checks, grading,
resume/regrade and exact day-2 validation use the selected root. V1's default
digest format is preserved; other roots are included in the digest namespace.
The existing compare command refuses different task-set hashes, including
comparisons between different task-set versions. Report-interface versions 1
and 2 can be compared on their shared metrics. IDs are unique across sets and v2 IDs start `v2-`.

`service_tier` is optional. Omit it to leave the CLI default in effect. When set,
every executor launch, retry, resume and fresh day-2 session passes
`-c service_tier="VALUE"`. Each process needs matching native
`event_msg.thread_settings_applied.thread_settings.service_tier` evidence;
context-only evidence does not verify the tier. Missing/different evidence adds
`executor_service_tier_missing_or_different` and prevents grading. Checkpoint
config, segment verification, task telemetry and run diagnostics retain the
request and observations. The shared report schema and CLI flags are unchanged.
Executor pricing reads the native applied tier separately for every segment.
When no tier is requested and the applied record omits it, carries null, or is
absent, use the known CLI model default: gpt-6.1-sol uses default/Standard and
gpt-6-luna uses priority. Per-process `pricing_evidence` and the pricing artifact
identify inference from the model default. Native `default` maps to Standard.
Explicit requests still require matching applied evidence; missing/different
tiers invalidate the task. Unsupported tiers/models remain unpriced.
Control pricing reads only service_tier on the controller's control_call line.
Absent or unsupported control tiers have null price and cost. pricing-provenance.json pins
per-call tier, source evidence and selected snapshot through task artifacts.

[pilot-v2-a.yaml](configs/pilot-v2-a.yaml) uses full A's gpt-6.1-sol / medium,
priority, Codex 0.163.0-alpha.11.1, zero retries and 900-second process deadlines
(1800 seconds per process for two-session tasks).
[STOP-3 estimate](reports/pilot-v2-a-estimate.md) bounds 24 planned executor
launches and applies the sourced 2× Fast multiplier to the planning proxy.
No live pilot was run in this worktree. calibration is a boolean config field,
default false. With true, the runner accepts frozen=false candidates, pins their
input bytes, records calibration=true in checkpoint and run diagnostics, and
prints a stderr notice that the report is calibration evidence, not a headline
result. A hash-pinned calibration.json artifact carries that status in each
report task; compare refuses it. With false, all freeze checks remain in force.
The pilot config enables calibration=true. Host review and spending approval
precede the live calibration; freeze follows calibration review.
Target baseline A at roughly 30–70%; revise design across whole families/types,
never select or drop individual tasks by pilot outcome. Preserve all candidates.

The existing `eval.runner.validate_graders` command accepts explicit v2 IDs in
`--tasks`; `--tasks all` retains its v1 meaning. V2 validation checks a private
requirement-to-executed-test manifest, references and failing starters through
the normal trusted grading path. Each task also reports
`shared_public_line_count` and `shared_assertion_line_count`: counts of nonempty,
whitespace-normalized grader-line occurrences found in that task's shipped
public inputs. Python `assert` statements and unittest `assert*` calls include
every line of a multiline assertion. V2 validation fails on any shared assertion
line, including in mutation mode; v1 reports the counts without changing its
acceptance rule. Counts are published without source lines. The four pilot
families use independent private input/expectation values while preserving
their requirement mappings. It can hash untracked candidate bytes offline;
that is not a run freeze. `--mutants 100000` exceeds the current complete AST
mutation population for each pilot task. Mutation source/reviews and hash-bound
equivalence rationales remain external; the v2 specification hash includes day 2.
Public regression and reference verification commands run separately, without
executors, controllers, judges, network or timing-dependent assertions.

Optional private `.corpus/` storage can contain executor-written Python test
files in any task/run subdirectory layout. Normal validation reads its regular
`.py` files recursively and reports `corpus_file_count`,
`shared_corpus_assertion_line_count` and `corpus_warning_count`. Shared assertion
lines count grader-line occurrences, regardless of duplication in the corpus.
These matches are warnings and do not affect validity or exit status; the
existing public-input rejection still applies. The summary totals warning tasks
and shared assertion occurrences. An absent corpus reports zero files, rather
than evidence that executor text has been checked. No corpus contents or paths
are published, and the corpus never contributes access-audit fingerprints.

The frozen command is `python -m eval run --config FILE --out DIR`.
Successful stdout is exactly the supplied output directory plus a newline;
exit codes are 0 for computed reports (including invalid tasks), 1 for input
errors and 2 for internal errors. Configs use the JSON subset of YAML.
Completed version-1 checkpoints do not call models again. Historical provisional
checkpoints require an explicit offline migration or a fresh output directory;
they are not silently relabeled as version 1. A later successful session cannot clear interrupted or unsupported
retained streams; every stream must pass the current access audit.

Private graders must already exist outside the repository, supplied through
`LHM_PRIVATE_GRADERS` in the trusted parent environment. Construction and
offline reference/mutation validation are separate from executor runs. Each task's external directory contains `test_*.py`; optional
`audit-names.json` lists historical filenames. Only after all executor work
exits and the access/settings audit passes does the runner copy graders into
a fresh trusted grading copy under the separate temporary
`lhm-retained-grading/` location. Copies are retained for review, outside
executor runtimes. Every task audits that retained location, every other
`lhm-eval-*` runtime in the temporary directory (including previous runs),
legacy grading copies in its own runtime, and the private source root.
Runtime and grading-root comparisons resolve system/temp aliases first, so a
continuation recorded through `/private/var/...` cannot protect itself merely
because the temp root is spelled `/var/...`. Saved historical continuation
roots also exclude that context's own resolved runtime; sibling runtimes and
grading copies remain protected.
A later executor can reach these paths because reads are not denied;
observed access invalidates the task. External raw logs are retained;
public evidence uses redacted labels and hashes.
Native logs are referenced with hashes as well as executor JSON streams.

Published `grading.log` contains only unittest test identifiers with `ok`, `FAIL`,
`ERROR` or `skipped`, the `Ran N tests` summary, and `OK`/`FAILED` counts.
Tracebacks, assertion source/messages, error text and skip reasons remain only
in the external runtime's `grading.stdout`, `grading.stderr` and full
`grading.log`. Regrading applies the same publication rule; report fields and
checkpoints record grading counts/status rather than raw grader output.

Generated evidence uses repository-relative references for checkout files,
including handoff evidence and grading logs. Report validation resolves these
against the repository root, independent of the caller's working directory;
legacy absolute references remain readable. External raw runtime references
remain absolute and hash-pinned. Published JSON/log copies also remove checkout
prefixes embedded in logged paths. Existing retained reports are unchanged.

Control accounting checks for symlinks at and below its runtime boundary and
rejects manifest paths that escape it. Symlinked ancestors above the runtime
are allowed, including macOS `/var` pointing to `/private/var`; their presence
must not erase observed control models or known control costs.

Each task also writes `access-audit.json`, containing every error and match with
log name, line number and evidence hashes. The audit scans the entire file after
an error, so multiple unsupported records appear in one run. The same complete
audit remains in `result.json`; the shared report references the audit artifact.

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
One bounded `for name in LITERAL_WORDS; do ...; done` loop can resolve `$name`
and `${name}` inside otherwise literal filesystem words. Simple body commands
and an `if ...; then ...; fi` guard are inspected for every list value, including
conditional paths that do not exist. Resolved operands use the ordinary private
root, canonical alias, symlink, traversal and recursive-ancestor checks in both
executor JSON and native command/function/custom records. This covers the smoke
command that reads `AGENTS.md` from `..`, `../..` and `../../..`.
Loop detection excludes heredoc bodies/delimiters and comments; quoted arguments
remain data. Their pre-existing expansion and protected-path checks still apply.
Commands mixing actual shell loops with these data spans remain outside the
bounded unrolling grammar and inconclusive.
Literal lists can also contain unquoted relative globs such as `project/*.py`.
Expand them inside the workspace before substituting each loop variable; every
concrete match retains canonical-path and symlink checks. The same bounded
no-match rule as direct globs applies. Absolute patterns, any `..` component,
variable-built patterns and quoted glob words remain unresolved. This covers
`for f in project/*.py test_public.py verify.py README.md; do echo "$f"; cat "$f"; done`
inside a literal shell wrapper.
Lists containing other expansions, nested/while loops, arithmetic, other
assignments or variable mutations, and directory-changing bodies remain
unresolved and inconclusive. Indirect code, embedded option/redirection values,
and unquoted substitutions that would split words also remain unsupported.
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
root are access_detected. Fingerprints cover distinctive hidden grader lines
of at least 16 normalized characters from `ROOT/<task>/test_*.py`, where task
directories have non-dot names. Root-level files, deeper descendants,
dot-directories (including quarantine/reference copies) and symlinks never feed
fingerprints. The entire private root remains protected against path access.
Source contents are deduplicated by SHA-256 before parsing. The runner and
read-only re-audit share one fingerprint/public-corpus analysis across tasks,
retries and streams per invocation; a new invocation gets a new cache.
A candidate
must contain a number or string literal absent from every public task's
`prompt.md`, `day2.md`, `expected.json`, `meta.json` and `workspace/` files.
Because the private grader corpus spans versions, exclusions include shipped
public inputs from both v1 and v2 at audit time, including during retained-log
re-audit. Executor-written files never enlarge those exclusions. Lines already
present publicly, imports, comments, blank/punctuation-only lines, decorators
(including multiline spans), TestCase class headers, test method headers,
docstrings, module entry guards and unittest launchers are excluded. A qualifying
hidden-line match still invalidates the task. Literal comparison includes decoded strings and numeric
spellings, with conservative substring exclusion for common values.
Only command `aggregated_output` and function/custom tool output contents are
matched. Executor-authored patches, file changes, arguments and metadata are
never fingerprint evidence. File changes and patches are checked only through
their target and move paths; authored content/diffs are not operands or path
access evidence, even when they contain `$`, backticks, quotes or path strings.
First-occurrence provenance spans the JSON stream and native rollout. A line is
exempt only when a recorded literal tool input demonstrably precedes every
output occurrence: patch additions, heredoc bodies and decoded command string
payloads establish authorship; patch context/deletions and current workspace
contents do not. A first output remains a match after later copying. Within-file
order and strict timezone-aware timestamps establish chronology. Untimed CLI
results can align with matching native command results within the same session,
using IDs or equal-count ordered command/output matches. Missing or ambiguous
correspondence retains the match. Private-path checks and incomplete/unsupported
capture errors are never waived. Retained and fresh contexts share provenance
while retaining separate filesystem checks. The runner includes prior segments
and all native logs before making retry/verification decisions, and recovery
pins the fingerprint-history implementation hash.
Output-first distinctive hidden text remains access_detected even when a read hides its path.
Only hashes, labels and redacted evidence are retained in audit results.
Decode-and-execute pipelines such as `base64 -d | sh` are inconclusive.
For pinned codex-cli `0.162.0-alpha.17.2`, native records include `session_meta`,
`turn_context`, `response_item`, `event_msg`, `world_state` and
`token_usage_record`. Snapshot records require boolean `full` and object `state`;
usage records require a usage object with nonnegative integer input/output
counts, and validate supplied turn/thread counts. The entire snapshot/usage
record, including nested keys and values, is scanned for private paths, aliases,
canonical traversal/symlink targets. A match reports
that a private location reached executor context and prevents grading. These
records are metadata; ordinary session settings are not shell operands.
For `0.163.0-alpha.11.1`, `event_msg.thread_settings_applied` is also metadata.
Its required thread identity and settings fields are shape-checked, including
model/provider, approval settings, managed filesystem/network profile, cwd,
workspace roots, effort, collaboration settings and disabled plugins. The full
record, including extra keys/values, receives the same private-marker scanning
as `world_state`; malformed shapes and other unknown kinds remain inconclusive.
Applied model/effort evidence includes both this event and `turn_context`;
conflicts leave settings unverified. Both sources appear in session-evidence.jsonl.
The synthetic 34-record `native-session-0.163.jsonl` fixture preserves the host
smoke's record order and line-9 settings structure without absolute user paths.
Native `event_msg.item_completed` command/file-change records are inspected,
while user/assistant message items remain prose. Native `custom_tool_call.input`
and `custom_tool_call_output` are paired; decoded input operands and output paths
are inspected, and fingerprints apply only to outputs.
Literal `exec` JavaScript wrappers around `tools.exec_command` and
`tools.apply_patch` are decoded without executing code. Every literal shell
command and its literal `workdir` (when supplied) is audited separately;
JavaScript glue and patch contents are never parsed as shell commands. Patch
targets receive path checks, including moves and bare symlink filenames.
Substitution-free `String.raw` tagged templates are also literal strings, with
backslashes preserved and template newlines normalized. Their shell commands
receive the usual operand, heredoc and output checks. Quoted heredoc bodies
remain data. Interpolation, alternate/dynamic tags and uncertain `String`
binding or tag mutation remain inconclusive.
Quoted literal expressions may use `+` concatenation, parentheses and chained
`.replace(literal, literal)` / `.replaceAll(literal, literal)`. String-pattern
`replace` changes the first occurrence; `replaceAll` changes every occurrence.
JavaScript escape, UTF-16 and replacement-dollar semantics apply, including
empty patterns. The resolved text receives exactly the plain-input command or
patch-target checks. Variables, interpolated templates, regular-expression
patterns, computed method access, nonliteral arguments and other method/function
calls remain unresolved in this literal decoder. A second, bounded static
reducer handles the observed session-authored FILE-manifest scripts. It parses
the whole program, enumerates direct `tools.*` call sites before reduction, and
audits every resolved command/patch through the existing path, alias, traversal,
heredoc and output checks. Literal calls are still audited if another call or
the reducer fails. No captured JavaScript, shell command or host helper executes
during reduction.

The reducer follows dependencies that reach `tools.*` arguments or helper
writes. Comparisons, throws, result displays and inspection loops that do not
change those operands need no value reduction. Every direct tool site is still
enumerated; aliases, reflection, unknown effects on live operands and unvisited
sites remain unsupported. Literal calls receive the ordinary audit even when
another computed call cannot resolve.

Confirmed `store`/`save` values belong to one identified native session stream.
They may contain bounded JSON data, including text fields and literal hash maps.
For audited tool results, reconstruct values from the corresponding complete
JSON in the paired output: direct `text(result)`, indexed objects with a nested
result, and indexed objects spreading the unmodified result are supported,
with or without a bounded display loop. Match display order and literal wrapper
fields, preserve each tool result's identity, and refuse missing, ambiguous or
overridden fields. A directly displayed string field retains its raw text.
Only after the output's own access audit may reconstructed values feed a later
`load`. A failed script can confirm a write only when a subsequent captured
display proves execution passed that write; yielded scripts cannot do so.

A script whose token stream contains neither `store` nor `save` cannot change
helper storage and preserves saved values even when its other syntax is outside
the reducer. Unsupported scripts mentioning either writer clear saved trust.
Unknown overwrites, unpaired/overlapping calls and session/log boundaries still
prevent borrowing earlier values. This state rule does not waive uncertainty
in the script's own tool arguments.

Supported data operations include literal pair arrays mapped through destructured
arrow parameters, awaited Promise collections, bounded loops, indexing, slices,
`Set.has`, `filter`/`map`, `Object.fromEntries`/`keys`/`entries`, `JSON.parse` and
`JSON.stringify`, concatenation and expression-only template interpolation.
`matchAll` additionally accepts an ASCII regex subset translated to Python `re`:
character classes, ordinary/noncapturing groups, quantifiers, anchors,
`\d`/`\w`/`\s` and complements, control escapes, `\b`, escaped punctuation and
ASCII `\xHH`/`\uHHHH`, with mandatory `g` and optional `m`/`s`. Nested/overlapping
repetition, unsafe search rescans, backreferences, alternation, arbitrary
lookarounds, Unicode modes, unknown flags and empty/unmatched-group results
remain unsupported. The two historical FILE-header patterns retain their
separately measured matcher. Input, collection, number and reduction-step
limits still apply; nothing from a captured script executes during reduction.

Concrete argument auditing remains mandatory: harmless source fragments can
combine into a private path. Successful reductions record log/line/hash and
`reason=derived_from_audited_outputs` in `access-audit.json.resolutions`; this
never overrides detected access or another unresolved audit item. Unknown
sources feeding an operand remain inconclusive under STOP-E4.
Read-only re-audit and regrade use these current resolutions from the complete
retained streams; historical parser errors do not override a now-clean audit.
Resolutions never waive a changed manifest, remaining parser error or access.

Hash-pinned fixtures in `tests/eval/fixtures/runtime-records/` retain all supplied
code-mode scripts and paired records for five baseline-B tasks, plus the
baseline-A shell records. Tests add synthetic session identity and synthetic
graders, preserving scripts verbatim. They cover store provenance, intervening
large literal patches, comparison-only loads, pair mapping, regex groups in
heredoc commands, and private paths reached through reduced values. The shell
parser also unrolls literal `for` lists whose body uses
`if test -f "$p"; then cat "$p"; fi`, followed by a separate quoted heredoc.
Each literal loop operand is audited regardless of file existence; a runtime's
own ancestor AGENTS.md is ordinary, while an explicitly protected sibling root
is detected. Heredocs inside loops, dynamic operands and unsafe bodies remain
inconclusive. These offline results do not establish historical task/report
validity; full original-stream re-audit with original pinned graders remains
host work.

Dynamic directories, unknown tools and unsupported
custom code stay inconclusive. Other unknown record/item kinds
also stay inconclusive. Native `Extension` items are classified by `kind`:
`clock.sleep` is benign metadata only with the observed ID, nonnegative integer
`durationMs`, thread/turn IDs and ordered integer start/completion timestamps.
Extra item fields or malformed sleep fields are inconclusive. Other Extension
kinds remain `unsupported_native_item`, including the kind in the diagnostic.
The supplied sleep record is retained verbatim in a hash-pinned fixture.
The synthetic 33-record regression fixture preserves
the supplied host session's structure and record order, with categorical
discriminators retained and all task, identity, path and usage content replaced.
Additional synthetic cases preserve the retained interval-union session's
line-23 patch-plus-unittest call and line-25 absolute-path FileChange map.
Detected or inconclusive access invalidates the task and aggregate report and
prevents grading. This is observed access auditing, not filesystem isolation
or proof that all unlogged activity is safe. Dynamic execution and additional
installed-version event forms require host review before measurement.

Offline re-audit of a finished run (no executor/controller/judge calls):

```sh
.venv/bin/python -m eval.runner.reaudit --private-root "$LHM_PRIVATE_GRADERS" --out eval/reports/pilot-a/
```

Here `--out` identifies the existing run directory to read. The command loads its
checkpoint and report, requires finished tasks, and audits the original external
`exec-*.jsonl` streams plus all native session logs under each retained runtime.
It uses each task's own `PrivateGraders`, workspace, repository and the runner's
`audit_roots(runtime)` grading/cross-runtime roots. Retained log hashes/counts and
grader hashes must match the original audit; unavailable, lost or changed evidence
is inconclusive unless access is detected. It prints one JSON row per task with
only `task_id`, `status`, `error_kinds` and `match_labels`; no paths or contents.
It writes nothing and does not replace the report, checkpoint or stored audits.
Exit 0 means re-audit computation completed, including detected/inconclusive rows;
exit 1 means the finished-run inputs or command arguments were unusable. Review
the rows on the host before choosing a fresh pilot A rerun directory. A clean
re-audit is observed cleanliness, not a new quality result or proof of isolation.

Harness configs select `harness=true`, an explicit `control_backend` and a
`reinstruction_limit`. The runner calls `python -m controller contract` with
an empty public case library and no handoff for day 1, validates the contract,
injects its JSON into the day-1 executor prompt, then calls `python -m verifier check` with
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
subset. `prices.yaml` preserves openai-standard-short-2026-10-22-v1 unchanged
and adds openai-fast-short-2026-10-23-v1. The user supplied Claude's official
OpenAI pricing-page observation dated 2026-10-23; this offline session did not
fetch it. Fast mode (priority processing, renamed 2026-07-30) is exactly 2×
Standard on input, cache and output: Sol 6.1 4/.20/20, Luna .20/.02/1 and Sol 6
4/.40/20 USD per million tokens. A supplemental 2026-10-23 Standard snapshot
pins Sol 6 at 2/.20/10 without modifying the original two-model snapshot.
All snapshots retain source/date/rates inside metadata.pricing.source's pinned
catalog serialization, compatible with the existing closed report schema.
Each call's pricing_ref identifies the selected original snapshot; the per-task
pricing artifact retains observed tiers and source hashes. Unknown models/tiers,
long-context calls and incomplete usage remain null.

The gpt-6-luna CLI default tier is priority. Retained version 1 control calls
were priced at Standard rates although they ran at priority. The final evaluation
must disclose this historical underpricing; no retained version 1 report is
rewritten. New control lines without a tier stay unknown, including old
controller versions that do not emit one. No controller change is required here.
Subscription usage is not zero-dollar
API usage. Historical reports are preserved. The runner prices each retained
`control_call` stderr line (including internal retries and HTTP fallback) with
`prices.yaml`, ignoring controller USD. Calls retain actual backend/model,
latency and success/error status; runner deadlines mark timeout. Judge children
are counted only through forwarded lines, with `judge_delegation` completeness
checks. Missing tokens/pricing, incomplete delegations, interrupted/deadline
operations or successful contract/handoff commands without successful generation
records keep control and total costs null. Mechanical verification and handoff
validation add no model calls. Invalid tasks retain every observed call's cost.
`metadata.control_model` contains the sole observed control model; no model or
multiple models produces null and a stderr warning. Criterion-level false_done_rate remains unchanged and undefined when its
complete denominator is unavailable. Version 2 adds task_false_done_rate from
the retained final message of the last required session for every configuration.
The task-scope adapter binds completion prose to a synthetic task ID and applies
verifier.claims.claimed_criteria's vocabulary, negation, exception and quote/code
rules; criterion-only and test-only claims do not imply task completion.
A claimed-complete valid task is false done only when hidden grading fails.
Invalid tasks leave both populations; missing final messages are explicitly
excluded, and a claimed task without hidden grading makes the rate undefined.
Task-completion artifacts pin extractor/adapter hashes, source segment/event
hash, final-message hash, evidence and reasons. The summary artifact publishes
numerator, denominator, excluded IDs/reasons and undefined grading outcomes.
Seeded bootstrap resamples eligible valid task clusters including nonclaiming
tasks; any zero replicate denominator produces null bounds/value. Under decision 0007, local
Gemma and QLoRA are dropped and parity is reported as not measured.

New checkpoints record the starting `git_commit` and `pricing_snapshot_id`.
Reports use that commit and warn on stderr with both values if build-time HEAD
or the price snapshot changed. Pricing metadata continues to describe the
snapshot actually used to price calls. Older checkpoints retain build-time
provenance behavior.

Task set version 1 contains 100 single-session and 20 two-session public tasks
across four types, all marked `frozen=true`. The user authorized freezing after
Claude's host verification and independent mutation testing (commits `80205d3`
and `ad7d7be`); no surviving mutant changes specified behavior.
`GRADERS-PENDING.md` retains the validation inventory despite its historical name.
Only the freeze flag changed in public task files; historical review fields remain
unchanged. Further task-content changes require a separate version 2.
The runner rejects any selected task whose freeze flag is missing or not boolean
true before external work, including when resuming a checkpoint.
The published freeze record in `docs/eval-freeze.md` pins commit `7cdaf3b` and
digest `b78913b04280f6696d419d2afdc96b152675973d82f05199ddef848986285d1f`.

The combined r5-full-001/r5-full-002 implementation runs two-session tasks.
Two-session tasks run day 1 with `prompt.md` in a fresh public workspace, then
start a new executor session in that same workspace after day 1 exits. Day 2
receives exactly the UTF-8 bytes of `day2.md` as stdin. Baselines add no context;
executor-authored files such as `HANDOFF.md` are the only carry-over. Day 2
never resumes day 1. Transport retries and verifier reinstructions may resume
their own day's session.

In harness mode the runner generates `handoff.json` after day 1 with the frozen
controller handoff CLI, using the day-1 native transcript, contract and last
verdict. It calls `verifier validate-handoff` without an `--out` flag, then
passes the validated file to the day-2 controller contract. The day-2 contract
is supplied separately through Codex's `developer_instructions` configuration;
the user prompt remains exactly `day2.md`. All children receive
`HARNESS_NESTED=1` in copied environments. Hooks do not own this loop.

Control outputs are pinned in a runner-owned hash manifest. Evidence publishing
never searches executor workspaces or follows symlinks. An output already
present before its trusted producer runs invalidates the task with
`runner_control_file_preexisting`; changed pinned inputs remain control errors.
Handoffs choose only pinned `verdict-N.json` files with numeric N. Unowned files,
including `verdict-99.json` and `verdict-final.json`, cannot become handoff input.

Hard-crash recovery resumes the active session and preserves completed days.
Audit-clean day-1 timeouts/errors can continue to day 2. Regrade preserves final
executor timeout/error outcomes and invalid pre-day-2 tasks while grading other
eligible tasks in fresh trusted copies.

Both days' event and native logs are retained and audited. A missing native
settings observation for either process invalidates the task. Private grading
runs once, in a fresh trusted copy after day 2 exits. Checkpoints retain each
segment's workspace exit hash and the final workspace hash. Regrade checks
both days' recorded hashes, distinct session identities, retained prompt bytes
and public prompt digest before grading the unchanged final workspace. Day-1
hashes are historical runner observations; the changed final workspace cannot
reconstruct a day-1 state. Regrading adds no executor attempts or usage.

`handoff-evidence.json` records the delivered day-2 prompt SHA-256, public
`day2.md` SHA-256, retained delivered prompt path and initial day-2 attempt.
Missing, changed or unverifiable observations invalidate the task.
`handoff.day2_pass` reflects final trusted grading, and
`user_restated_day1_context=false` is backed by the exact prompt comparison.
`handoff_success` uses valid observed two-session tasks, including grading
failures, as its denominator; an empty denominator yields null. Both days'
attempts and executor costs are summed once within the task cluster.

`configs/full-a.yaml` (medium) and `configs/full-harness.yaml` contain the same
120 ordered frozen tasks. `configs/full-b.yaml` (max) contains their 100
single-session tasks in the same order; B has never run. Harness configs use
codex_cli control and reinstruction_limit=2, matching three attempts per day.
`configs/smoke-harness.yaml` selects bug-chunk-tail and two-session-prefix-sums.
Timeouts are 600 seconds normally, 1200 for two-session processes, and 20 for
grading. No frozen CLI flags or schemas changed. Decision 0007's user-approved
scope sets C to a stratified 20-task subset with user-filled templates and
compares harness handoff_success with A; C templates/measurement remain pending.

[Decision 0006](../docs/decisions/0006-codex-version-policy.md) requires matching
version evidence: `full-a`, `full-b` and `smoke-two-session-a` select
`codex-cli 0.163.0-alpha.11.1`. Historical pilots used `0.162.0-alpha.17.2` and
supply diagnostic planning data only for these newer runs. The runner checks
the installed version before each executor launch and halts if it changes.
Missing/mismatched native per-session `cli_version` instead invalidates only
that task (`missing_cli_version_evidence` / `mismatched_cli_version_evidence`),
preserving its costs and the complete report. Compare only identical versions:
`python -m eval.runner.compare_versions REPORT_A REPORT_B` refuses mixed versions.
Every new version needs a hook compatibility probe and one-task audit smoke
before large runs. The supplied 0.163 host hook probe passed. The first host
two-session smoke stopped correctly before day 2: its audit was inconclusive
only for the new line-9 settings event. That record is supported offline now;
Claude must rerun the smoke in a fresh output directory. Audit smoke and
production behavior remain host checks.

STOP-3 estimates include both executor days and up to three generations per
controller/judge command across retries and fallback. A no-retry two-session
harness task already bounds 11 calls before judge criteria; it requires the
existing estimate/approval process. Per-task timeout overrides must still select
configured tasks and lie in (0, 3600].

Full A is running in the main checkout; this worktree does not change that run.
[Baseline estimates](reports/full-estimate.md) now budget 140 A sessions
($4.0960136) and 100 B sessions ($2.9257240 using the requested A-session
proxy; historical max-effort pilot B gives $4.3045080). Harness estimates are
[smoke](reports/smoke-harness-estimate.md) and
[full](reports/full-harness-estimate.md): bounds before generated judges are
21 and 900 calls. Luna planning assumes 5,000 uncached input and 1,000 output
tokens per generation ($0.001); executor planning uses pilot A's session average.
These are planning figures, not measurements. Usage limits are no longer a
planning concern. The harness has never run live; Claude runs the host smoke
next. Any exact bundled `configs/NAME.yaml` with `reports/NAME-estimate.md`
passes the estimate guard; historical pilot/full mappings still work. Changing
a config requires its own matching published estimate. Estimates do not grant
execution approval.

Claude's host smoke (one two-session task, harness off, medium; no run here):

```sh
.venv/bin/python -m eval run --config eval/configs/smoke-two-session-a.yaml --out eval/reports/smoke-two-session-a/
```

The smoke requires the existing host login and separately supplied private
grader environment. It must confirm native evidence, two distinct sessions,
exact day-2 prompt delivery, exit hashes and one post-day-2 grade. Harness
`developer_instructions` delivery and boundary recovery still need host
verification; mocked tests establish orchestration only.

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
- Missing control accounting remains unknown; actual transport/model comes
  from retained generation records, with Role 4 forwarding required for judges.

Incomplete runs halt without publishing a report and retain checkpoints for
recovery. A report requires the complete configured task set; this preserves the
shared schema without treating partial STOP-E1 evidence as a valid comparison.

Account usage limits are resumable STOP-E1 infrastructure stops. The runner
recognizes usage-limit wording only in `--json` `error.message` and
`turn.failed.error.message` (or direct `message`) events. Control-call evidence
comes from retained stdout/stderr, including nested `control_cli_events` logs.
Assistant/tool prose and ordinary errors do not trigger this classification.
It halts before any runner retry, day 2, grading or next task, prints the original
limit message and reset time to stderr, exits 2 and prints no success path.
The interrupted task has no result.json or checkpoint outcome; no report.json
is published. Rerun with the same config and `--out` after the limit resets:
existing sessions resume, or start fresh if no thread was created; pending
control operations retry without rerunning completed executor work. Failed
control streams and partial outputs remain hash-pinned under
`control-interruptions/`, with redacted report copies. All retained executor
attempts still count; missing usage/cost stays null. Control commands finish
within their existing bounded subprocess deadline; the runner checks their
retained events on return and makes no later call on a limit.

Capacity refusals use the same structured error sources, including controller
and forwarded verifier `control_cli_events` envelopes. The complete capacity
wording list is **`at capacity`**, case-insensitive, observed as `Selected model
is at capacity. Please try a different model.` Other errors retain their existing
classification. For each interrupted operation the runner waits 60, 120, 300,
then 600 seconds before retrying. Executor retries resume the same session with
the existing continuation/reinstruction prompt. Control operations archive
interrupted stdout, stderr, sidecars and partial outputs before rerunning; a
capacity-refused judge never produces a criterion failure or reinstruction.

Every executor segment remains retained, audited and priced. Capacity recovery
does not consume transport retries, verifier reinstructions or executor attempt
counts (`avg_attempts`); `executor_segments.attempt` remains a consecutive log
segment index under the unchanged report schema. The checkpoint and
`run-diagnostics.json` mark infrastructure recoveries, waits and capacity errors;
control recoveries also have hash-pinned `recovery.json` evidence. If the fifth
call is still refused, the run exits 2 as `capacity_limited`, with no outcome for
the interrupted task and no aggregate report. Reusing the same config and
`--out` resumes the pending session/control operation with a fresh backoff
schedule. A refusal without a session ID halts resumably instead of starting a
different session during automatic recovery.

A capacity refusal before any `item.started` or `item.completed` in that turn
records zero input/cache/output tokens and evidence explaining the zero. After
items, missing usage stays unknown. Control envelopes are paired with their own
`control_call` records; a missing capacity call record is retained from its
envelope with the measured operation latency. Executor accounting prefers
native `event_msg.token_count.info.total_token_usage` deltas across each process;
output already includes reasoning tokens. Existing `turn.completed.usage`
evidence remains the fallback when native counters are absent. Native counts
and refused-request evidence survive in the segment/checkpoint artifacts.

Runner-deadline timeouts retain their outcome and continue to the next task,
subject to the existing access-audit/settings/observation validity checks.
Unclassified nonzero executor exits still halt with STOP-E1. Account usage-limit
stops retain their immediate-stop behavior and do not use capacity backoff.

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

## Pilot-B audit shapes and retained-workspace regrading

Code-mode audit extracts each direct `tools.exec_command(...)` and
`tools.apply_patch(...)` call independently of arrays, Promise combinators,
loops, spread in display output and other surrounding JavaScript. Only quoted
literals and the bounded string-expression grammar above resolve `cmd`, optional
`workdir`, and patch operands. Tool aliases,
computed/optional tool access, unknown tools, eval/Function and unresolved
callables remain inconclusive. Command-object spreads remain unresolved because
they can override an operand. Shell rules apply to extracted commands, never to
JavaScript glue or authored patch contents. Nested `-lc` wrappers are decoded
with shlex; the pilot's adjacent quote segments resolve to the literal `!.git`
and `!.aws` patterns. Exec `file_change.changes` lists of `{path, kind}` use the
same target/move checks as native FileChange dictionaries. Both sides of path
comparisons, and private-path redaction, recognize `/var` and `/private/var`.

The runner now saves its configuration and a `workspace_exit_sha256` in the
checkpoint immediately after each executor process exits, before audit,
verification or grading. Each segment also retains that hash. The deterministic
manifest includes every relative path, entry type, file SHA-256, permission mode
and symlink target; caches are included, and symlinks are never followed.
Hashes are not backfilled for historical executions.

On the host, regrade a complete run without new executor/controller/judge calls:

```sh
.venv/bin/python -m eval.runner.regrade --private-root "$LHM_PRIVATE_GRADERS" --from eval/reports/SOURCE --out eval/reports/NEW
```

`NEW` must be fresh and separate from the source, retained runtimes and private
storage. Every configured task must have a runner-recorded exit hash, and every
retained workspace must match before any output or grading copy is created.
Missing hashes or changed workspaces cause a clear refusal. Regrade also checks
the source report, selected public/private task inputs and retained log/grader
manifests. It re-audits all tasks, grades every audit-clean workspace through the
same `grade()` function in a fresh post-exit copy, and preserves executor/control
calls, costs and observations. Other invalid reasons remain invalid. It writes
new results, audits and a complete schema-validated report, recalculating quality
metrics over the whole run. It never resumes Codex or writes to the source run
or original runtime. Grading process output uses a separate retained runtime.

`NEW/run-diagnostics.json` records the source directory, source report SHA-256,
audit implementation file hashes and all workspace-hash checks. No shared report
schema fields were added. Successful stdout is `NEW` plus a newline; input
refusals exit 1, internal errors exit 2. Runs without exit hashes, including the
existing pilot B, can use read-only `eval.runner.reaudit` for diagnostics but
require a host executor rerun before regrading is possible.

The shell operand resolver unrolls literal `for` lists containing absolute or
relative paths and audits every iteration, including conditional reads of
missing files. A command after `done` on a new line is audited separately.
Absolute paths outside the workspace are allowed when no protected root or
alias matches. Private-root, symlink-alias and traversal checks still apply;
variables, command substitutions and unbounded/absolute globs stay unresolved.

## Workspace digest versions (2026-10-23)

New checkpoint task entries and completed executor segments record
`workspace_digest_version: 2` alongside `workspace_exit_sha256`. Version 2
hashes paths, file contents, modes and symlink targets, excluding `__pycache__/`,
`*.pyc`, `*.pyo`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/` and
`.hypothesis/` at any depth. Trusted grading and published workspace copies
use the same exclusions. Version 1 retains the original complete manifest.

Regrade, day-2 continuation (including the copy and retained audit context),
infrastructure reruns, re-audit and republication check an existing workspace
pin with its recorded algorithm. Unversioned pins may match either version 1
or version 2. Unknown versions are refused. Read-only re-audit and republication
still support historical entries without a workspace pin; regrade and day-2
continuation require one. Selected infrastructure reruns may lack a pin after
an interruption or pre-launch failure, but any existing pin must verify.
No recovery command rewrites a historical hash or infers one from current bytes.
A historical v1 pin that included caches can still fail both algorithms after
cache changes; version fallback cannot reconstruct that original manifest.

For legacy unversioned/v1 entries only, regrade, infrastructure reruns and day-2
continuation have a second verification path after both v1 and v2 recomputations
fail. If the source report has per-task `TASK/workspace/...` artifact pins,
every retained non-cache regular file must match those SHA-256 values. When
there are no workspace artifact entries, use the trusted published
`SOURCE/TASK/workspace` copy retained at grading time (including the committed
full-harness copy). Compare every non-cache file byte for byte against that
reference. The non-cache file
sets must be identical, and every file mtime must be at or before the last
recorded executor exit. Checkpoint and report exit timestamps must agree and
include timezones. Missing published evidence, duplicate/bad pins, changed/missing/extra files, late
mtimes, symlinks and unknown/explicit-v2 digest versions cannot use this path.
The hashes establish file bytes and the file set; they do not recover the old
digest's mode/directory/cache manifest. No new executor or model call supplies
this evidence.

Regrade records `workspace_verification: published_artifact_hashes` or
`workspace_verification: published_workspace_copy`, published
and retained file counts, hashes compared and mtimes checked in per-task
`regrade-provenance.json` and `run-diagnostics.json.workspace_hash_checks`.
It preserves the original artifact pins or published workspace copy for subsequent recovery. Infrastructure
reruns and continuation retain the same verification counts in their respective
task provenance. Continuation verifies both source and copied workspaces, and
rechecks the historical workspace during later audits. Its legacy provenance
sets `copy_hash_matched: false` and records the observed copy digest separately;
the published comparison verifies the copy independently of the old digest.
Read-only re-audit uses
the same legacy check so continuation selection can proceed; republication's
existing digest policy is unchanged. Digest matches record their algorithm as
before, and no historical workspace pin is replaced.

In harness mode, each attempt's workspace pin is recorded after its verifier
checks finish, including failed/interrupted checks and recovered pending
verification. Executor capture hashes remain pinned before verification.
The runner launches the verifier with `-B` and a copied environment containing
`PYTHONDONTWRITEBYTECODE=1`. Python command arguments inside the verifier belong
to Role 4 and are not rewritten by the runner. The current verifier already sets
that environment variable for command children, but explicit `py_compile` and
test tools can still write caches; digest exclusions provide the safeguard.

## Restart recovery and infrastructure-only reruns (2026-10-23)

Resume the original `eval run` command with the same config and output directory
for a checkpoint interrupted by a host restart. Segments explicitly recorded as
`exit_code=-2, interrupted=true` retain their bytes and access checks; only their
missing terminal event is exempt. The completed resume retains its own terminal
evidence. Malformed/truncated records, missing logs, unsupported events,
unresolved operands and unfinished tool events remain inconclusive. Re-audit
and regrade apply the same narrow exception to retained segments.

Before any executor segment exists, resume verifies the runner's control-file
manifest. A schema-valid pinned contract is reused. Pinned incomplete contract
outputs and accounting move into `control-interruptions/` before regeneration;
changed files, symlinks and unowned outputs remain errors. No source evidence is
deleted. SIGINT and SIGTERM write their signal name and exit code to
`run-diagnostics.json`, clean up the current child, and exit 130 without a
traceback. The original signal reason survives checkpoint cleanup.

For a completed source report with infrastructure-invalid tasks, use a fresh
output directory on the host:

```sh
.venv/bin/python -m eval.runner.rerun_invalid --private-root "$LHM_PRIVATE_GRADERS" --from eval/reports/SOURCE --out eval/reports/NEW --reasons control_cli_error,execution_interrupted,incomplete_access_audit
```

The comma-separated selector matches recorded invalid reasons. Eligibility also
requires causal evidence of a runner control failure, an explicitly interrupted
segment, restart-related missing logs, or capacity exhaustion. Consequent missing
settings/session/version/handoff observations can accompany these causes.
Unexplained audit errors, audit-precision-only invalidity, ordinary failures and
timeouts never select a new executor outcome. A selected access match, whether
historical or newly observed, refuses the operation before any call. Changed
retained log/control manifests also refuse recovery. Interrupted/capacity-limited
checkpoints without a complete report use ordinary resume first.

Selected tasks start from public starter workspaces in fresh external runtimes;
source workspaces and grading copies never enter the executor. Unselected tasks
are re-audited/regraded just as with `regrade`, preserving original accounting.
All unselected source exit hashes and full input/config/pricing/version pins
must validate. Selected pre-launch failures need no invented exit hash. Fresh
attempt/segment counts describe the new execution; original segments, logs and
artifact hashes remain referenced in each task's `rerun-provenance.json`.

Prior calls/costs are retained once, fresh call IDs have a separate namespace,
and unknown prior costs stay null. `rerun-invalid.json`, per-task provenance and
diagnostics record source run/report/checkpoint hashes, implementation hashes,
requested/actual reasons, selected IDs, fresh runtimes and added calls/costs.
Checkpoint resume and subsequent regrade preserve that accounting. The report
schema and existing CLI flags are unchanged. Success prints `NEW` plus a newline;
input refusals exit 1, internal/incomplete execution exits 2, signals exit 130.
The existing cost-estimate/spending checks still apply before host calls.

For a completed, valid task whose executor cost is unknown after an
infrastructure interruption, use the separate replacement operation:

```sh
.venv/bin/python -m eval.runner.rerun_unaccounted --private-root "$LHM_PRIVATE_GRADERS" --from eval/reports/SOURCE --out eval/reports/NEW
```

This command selects valid tasks only when every executor accounting gap has
missing token counts and a recorded `interrupted=true`, `exit_code=-2`, capacity
refusal, or recovery following a capacity refusal. It requires clean historical
and current audits, unchanged log/control/workspace evidence, and known control
costs. Both executor and total task cost must be null. An interrupted segment
with no usage followed by a successful resume qualifies even if the historical
pricing capture/tier/reference is missing or unknown. Available timestamp-bounded
price evidence is retained; missing historical prices/costs stay unknown.
Price-only gaps, ordinary unmarked usage gaps, stale accounting with recoverable
complete usage, and all access matches refuse selection. Unsupported/malformed
audit evidence is never waived. Selection refusals name the failed condition
(for example, `control_cost_missing` or `infrastructure_interruption_marker_missing`)
and the affected task when available; CLI errors retain these safe diagnostics.

Each selected task starts once in a pristine public workspace, with all ordinary
retry/audit/grading rules. Its outcome, attempts, calls and costs replace the old
task's in the new report; a fresh failure remains a failure. Every other task is
re-audited and regraded from retained evidence with its original accounting.
Source reports, checkpoints and runtimes are not rewritten. This differs from
`rerun_invalid`, which continues to include prior spending in its accounting.

`rerun-unaccounted.json`, `run-diagnostics.json.rerun_unaccounted`, and each
selected task's hash-referenced `rerun-provenance.json` record selected IDs,
source outcome/calls/costs/segments/artifact references, exact infrastructure
causes, source hashes, fresh outcome and added calls/costs. The provenance states
`accounting_policy=replace_with_fresh_session`: replaced historical spending is
archived there, excluded from replacement report totals, and remains unknown
when originally unknown. Final comparisons must disclose the task IDs, reasons
and replacement policy. Resume and later regrade retain this accounting and
provenance. Existing CLI flags and the shared report schema are unchanged.

Interrupted native `token_count.info.total_token_usage` observations are retained
as segment `partial_usage` in checkpoint/result evidence and per-process
telemetry, or in `source_segments` of replacement provenance. Recovery runs on
ordinary interruption/resume and during retained regrade/replacement. For each
rollout it records the last cumulative counters inside the segment's recorded
time bounds, including reasoning counters without adding them to output tokens.
These are explicitly labeled lower bounds of cumulative session usage and may
include earlier processes. Missing/naive timestamps or absent valid counters
produce no invented observation; later resume records are excluded. Partial
usage never supplies billable tokens, fills an unknown cost, or changes retained
accounting. New interrupted native counters are not saved as complete
`native_usage`.

JSONL framing uses only the newline character, so U+0085, U+2028 and U+2029 inside
JSON strings remain data in executor/native streams, control envelopes,
telemetry, limit detection and redaction. Shell operand extraction identifies
heredoc delimiter lines before tokenizing the surrounding commands. Quotes and
backslashes inside a quoted heredoc cannot consume following compile/test
commands. Unquoted expansions remain unresolved, and original protected-path
checks still inspect the entire command.

## Continuing an audit-recoverable day 2

On the host, use this separate command when the original runner stopped before
day 2 solely because a day-1 audit was inconclusive:

```sh
.venv/bin/python -m eval.runner.continue_day2 --private-root "$LHM_PRIVATE_GRADERS" --from eval/reports/full-a --out eval/reports/full-a-continued
```

The command selects only two-session tasks whose report and checkpoint both
record exactly `incomplete_access_audit` and
`missing_two_session_handoff_observation`, an inconclusive audit without matches,
and no day-2 execution/observation or grading. Every retained day-1 log must now
be clean, with its original log/grader manifests intact. Access-detected tasks,
other invalid reasons and still-inconclusive evidence are never selected. Finding no
eligible task is an input error. All source exit hashes, selected/population
input hashes and report/config provenance receive the normal regrade checks.

An audit-blocked harness attempt may have stopped before its final day-1
verification. Continuation also accepts this narrow case: all earlier attempts
have exit hashes and failed verdicts with re-instructions, the last successful
attempt has no verdict, and no handoff or day-2 execution exists. Re-audit must
first be clean with unchanged log/grader manifests. If the last attempt has no
exit hash, the preceding attempt's hash is not applied to its workspace.
Instead, recovery records a current workspace snapshot and copy hash check;
this establishes recovery-time bytes, not an original exit-time measurement.
An existing final-attempt hash must still match. Non-harness hash requirements
and ordinary regrade's refusal of missing historical pins are unchanged.

`--out` must be fresh. The source run and every source runtime stay unchanged.
The command re-audits/regrades all other tasks just as regrade does, retaining
their original accounting. For each selected task it copies the retained
workspace into a new external `lhm-eval-continue-*` runtime and verifies the
recorded day-1 exit hash after copying. Only retained executor/native logs and
hash-pinned runner control artifacts accompany the workspace; old grading
artifacts and credentials are not copied. Absolute/outward workspace symlinks
are refused. The new Codex home uses the normal external login symlink.

The normal runner finishes any pending day-1 verification/handoff from pinned
artifacts, then performs the recorded day-2 contract, new executor session,
verification and retries. The user input is the exact `day2.md` bytes; harness
contracts use developer instructions. Model/effort, version checks, deadlines,
retry limits, nested guard and cost-estimate guard use the recorded config.
Historical log bytes are audited in their original workspace context with
pinned hashes; new events protect the original runtime as well as private
storage and grading copies. Changed historical logs/workspaces are inconclusive.
For an audit-blocked attempt, the runner first uses the ordinary verifier call
at the retained attempt number on the copied public workspace and retained
native transcripts, honoring the recorded retry limit. It then generates and
validates the handoff before day 2. The task's `result.json` and continuation
provenance retain `day1_verification_recovery`: executor exit, recovery snapshot
and actual verification times, current hash/digest version, verdict hash, and
whether an original final-attempt exit hash existed. Verification is explicitly
marked as occurring after exit; the source checkpoint is never repinned.
No Codex session runs in a grading copy. Eligible completed day-2 work is graded
once, after exit, in a fresh trusted copy.

The complete report retains source pricing/bootstrap/config provenance and all
old calls/costs, adding only new executor/control calls. Unknown cost stays null.
`continuation.json`, task-level continuation artifacts and run diagnostics record
the source run/report hash, implementation hashes, original day-1 and new day-2
start/exit timestamps, elapsed gap, workspace-copy check and added call IDs/costs.
The materialized semantic config copy has its own diagnostic hash; the report's
config hash still identifies the source run's recorded config bytes. No report
schema or existing CLI flags change. Subsequent re-audit/regrade understands the
two retained filesystem contexts.

Success prints only the supplied new directory plus a newline. Input refusals
exit 1; execution interruption/version drift/internal errors exit 2 and retain
the fresh checkpoint/diagnostics for host review. Incomplete evidence does not
become a successful continuation. This command can launch paid calls on the
host; apply the existing approved estimate/spending workflow before running it.

## Baseline C and paired comparisons (2026-10-23)

Decision 0007 scope supplied by the user: baseline C uses twenty single-session
tasks, five per type and twenty distinct families. `eval/baselines/c-subset.json`
records seed 0, the metadata-only procedure and the frozen population digest.
`eval/tools/prepare_c.py` reproduces selection without reading runs or graders.
The user fills the six fields of each skeleton in `eval/baselines/c/` once,
following `eval/baselines/README.md`. Agents must leave `__HUMAN_FILL__` untouched.
Templates cannot be revised after any C run starts.

The optional config field `static_template_dir` is repository-relative or absolute
and requires harness=false, control_backend=none. All selected TASK_ID.md files
must be regular, nonempty UTF-8 files without `__HUMAN_FILL__`. Preflight happens
before any executor/control call. The exact bytes enter the day-1 prompt in the
same appended `Approved evaluation contract (benchmark runner authorization):`
wrapper as harness guidance. No verifier, re-instruction or handoff runs. Each
retained `static-template.md` is hash-pinned in per-task report artifacts; the
checkpoint pins all selected template hashes at start and rejects resume drift,
including changes to completed tasks. No paid C run can start with the skeletons.

`eval/configs/full-c.yaml` orders the subset lexicographically and otherwise uses
full A settings; its planning estimate is `eval/reports/full-c-estimate.md`.
B and C declare optional `task_population` containing full A's 120 IDs. The runner
fingerprints all population public inputs and external grader contents for
metadata.task_set_sha256 and separately pins the selected-input digest in the
checkpoint. Population IDs must uniquely contain every selected ID and all must
be frozen. Only selected tasks execute. This lets subset reports share full A's
verified full-population digest; old subset reports retain their historical
subset digest and are refused rather than relabeled. Hosts need all population
graders to verify that digest before running B or C.

Compare completed reports without private graders or model calls:

```sh
.venv/bin/python -m eval.runner.compare eval/reports/full-harness/report.json eval/reports/full-a/report.json --out eval/reports/compare-a/
.venv/bin/python -m eval.runner.compare eval/reports/full-harness/report.json eval/reports/full-b/report.json --out eval/reports/compare-b/
.venv/bin/python -m eval.runner.compare eval/reports/full-harness/report.json eval/reports/full-c/report.json --out eval/reports/compare-c/
```

This separate command preserves existing CLI flags. It writes comparison.json
and comparison.md and prints exactly the supplied output directory. Input errors
exit 1, write errors exit 2. Inputs must validate against the report schema;
comparisons refuse differing task-set digests, seeds, executor models, Codex
versions (using compare_versions), cost basis or changed historical pricing pins.
Added tier snapshots are allowed only when existing snapshots remain identical;
historical costs are preserved and disclosed. Effort may differ for B.
Input report hashes, matched/excluded IDs and comparison direction are retained.
Only tasks valid in both reports contribute to each side's pass_rate,
cost_per_pass, avg_attempts and two-session handoff_success. Any invalid matched
task marks the whole comparison diagnostic; comparison cost metrics use the
matched valid intersection rather than the report's all-attempted-cost metric.
Overall and per-type tables include sample sizes, paired task-cluster percentile
bootstrap 95% intervals for left-minus-right pass rate, cost-per-pass difference
and left/right cost-per-pass ratio, using the run seed and 10,000 resamples.
Zero original/bootstrap denominators or unknown costs yield null with a reason.
A comparison with no eligible two-session tasks has undefined handoff_success.
Use A for the handoff comparison. Local Gemma and QLoRA are dropped; parity
remains not measured. These changes have mocked evidence only; live harness
compatibility and all host measurements remain pending.

## Report-interface compatibility

New reports carry all seven version 2 metrics. Per decision 0009, the presence
of metrics.task_false_done_rate declares interface version 2; absence declares
version 1. Regrade, continuation, infrastructure rerun, re-audit and compare
validate that declared shape. The compatibility loader reconstructs version 1
by reversing exactly the two approved schema additions; it never modifies the
shared schema or source reports. Derived reports can add version 2 evidence
without model calls or grading invalid tasks. Compare includes task-level false
done only when both sources carry it; otherwise it reports shared metrics only.
Calibration status survives recovery through pinned task artifacts/diagnostics.

## Repairing missing published evidence (2026-10-23)

Publication checks links only at/below the runtime or source root. System
aliases above that boundary, including macOS `/var` → `/private/var`, are allowed.
Links at the root, links inside it and traversal remain rejected. Control-file
accounting, day-2 copying, infrastructure reruns and static-template reads use
the same boundary rule. Normal workspace publication keeps its existing rule:
only a completed post-exit grading result permits the workspace copy.

On the host, restore a finished run in place without model calls or grading:

```sh
.venv/bin/python -m eval.runner.republish --private-root "$LHM_PRIVATE_GRADERS" --out eval/reports/RUN
.venv/bin/python -m eval.runner.republish --private-root "$LHM_PRIVATE_GRADERS" --out eval/reports/RUN --runtime-root BACKUP/RUN
```

The optional backup layout is `BACKUP/RUN/TASK`; pass the directory containing
its task directories. Both checkpoint.json and report.json must already exist,
all configured tasks must be finished with no active PID, and checkpoint/report
identity and segment metadata must agree. Version 1 and 2 reports are supported.
Run this only after the host runner has exited; it is not a concurrent repair.

All tasks are checked before the first write. Every control-file pin and the
complete executor/native audit-log manifest must match, including log sizes.
By default, only runner-allowlisted controls and hash-pinned executor captures are published,
using the same text decoding, private-path redaction and destination layout as
normal publication. Nested interruption archives retain their directory layout.
Unlisted files, workspaces, authentication files and grading copies are never
copied. Existing destination bytes or artifact hashes that disagree cause
refusal; identical files are reused. Repeating a successful command is harmless.

Historical segments in the checked-in full-A/full-B/smoke reports have no
stderr or final-message hash, contrary to the recovery brief's assumption.
Without `--allow-unpinned`, those files are counted as `unpinned` and skipped,
even if still present in the runtime/backup. Add `--allow-unpinned` to recover
regular root-level `exec-N.stderr` and `final-N.md` files through normal
redaction. This does not waive any existing pin or admit other unpinned files.
Missing captures remain skipped; symlinks and conflicting destinations fail.
Control stderr is already pinned and can be restored. New
executor segments record `evidence_sha256` for events, stderr and any final
message immediately after process exit. Hashes are never backfilled from
unverified historical bytes. Missing or mismatched *pinned* files cause refusal.

Success prints JSON rows containing only task IDs and `published`, `existing`,
`unpinned` counts, followed by totals. With the flag, `published_unpinned` counts
newly restored unpinned captures; `unpinned` counts those still skipped.
`run-diagnostics.json.republication.artifacts` retains each recovered capture's
`task_id`, `path`, `sha256` of the redacted published content and
`provenance: republished_unpinned`. The frozen report artifact schema permits
only `path` and `sha256`, so report references keep that shape and the richer
artifact entries live in diagnostics. Existing diagnostic fields are preserved,
and identical repeated repairs do not rewrite diagnostics.
Errors are generic and contain no paths
or source contents. Input errors exit 1; internal errors exit 2. Only per-task
`artifacts` entries in report.json change; hashes there describe the redacted
published bytes, while historical external raw-log references remain intact.
Checkpoint, result/classification artifacts, metrics, costs, validity and all
other report fields stay unchanged. Restoring a final message does not recompute
historical completion classifications or metrics. No host repair was run in
this sandbox; Claude owns republication of the five retained runs.
