# Executor transport outages — 2026-10-24

Classify terminal reconnect/transport failures consistently in run, regrade
and read-only reaudit as invalid with executor_transport_failure. Preserve
normal model timeouts/errors, explicit completion and non-transport terminal
failures. Retain redacted messages, JSONL line numbers and hashes in task
diagnostics and report-pinned infrastructure provenance. Track resolved live
retries, and stop before day 2 when day 1 exhausts transport recovery.

Permit proven transport failures in rerun_invalid through the existing reason
selector. Use fresh external runtimes with ordinary auditing/pricing, retain
prior spending and unknown costs, and record source causes, reruns and added
costs in diagnostics and report-pinned provenance. Incomplete audit evidence
remains invalid; fresh recovery permits only the proven deadline's absent
terminal event, never malformed/unresolved/access evidence. Keep live backoff
and resume within the configured retry budget.

Assumptions: the supplied 2026-10-24 outage messages define the recognized
family. Tests synthesize both retained shapes with mocked executor transports
and synthetic graders. No host report, actual private root or live model is
accessed; host regrade/rerun remains pending. Frozen tasks, shared interfaces
and CLI flags are unchanged.

Validation: focused classification/recovery/reaudit regressions — 85 passed
in 37.30s; updated existing provenance regression — 1 passed in 2.41s.
`.venv/bin/python -m pytest tests/eval -q` — 2048 passed in 384.64s.
`git diff --check` and the authorized-scope/STATUS audit pass: eleven paths,
six STATUS headings, frozen inputs/interfaces unchanged, zero staged/deleted
paths. No staging or commits occurred.

# Literal hash stores beside Unicode patches — 2026-10-24

Accept Unicode only in a direct single-literal `tools.apply_patch` payload
inside the bounded reducer. The recorded line-48 script stores a literal
`protected_hashes` object before such a patch; the line-51 paired output
confirms completion. Previously the whole-script ASCII gate rejected that
independent store. Other syntax/data keep their ASCII bounds, patch targets
still receive the ordinary audit, and unknown values never become stored
evidence merely because an unrelated patch result was displayed.

Preserve the complete 18-record call chain in a hash-pinned fixture with
synthetic paths. Both original lines 57 and 91 resolve as
`derived_from_audited_outputs`. A variant storing JSON from an undisplayed
tool result leaves both unresolved. Cover Unicode-boundary refusals,
failed/yielded output, protected patch targets and computed private operands.
The fixture's earlier truncated listing retains its protected-path finding;
resolving these loads does not waive unrelated evidence.

Assumptions: only the supplied call chain is available. Original host validity
and grading require a separate retained-stream re-audit; no host run, private
grader access or model call occurs here. Preserve frozen inputs, interfaces
and unstaged worktree scope.

Validation: focused store/code-chain/regrade regressions — 246 passed in 15.21s.
`.venv/bin/python -m pytest tests/eval -q` — 2019 passed in 363.40s.
`git diff --check` and the six-path scope/fixture/STATUS audit pass: 18
sanitized verbatim records, pinned hash, six STATUS headings, no source-location
leakage and zero staged/deleted paths.

# Protected listings, transport diagnostics and remaining code chains — 2026-10-24

Resolve only supported literal-basename ancestor listings backed by their own
unique, complete paired command output. Verify every positive filter and every
returned path; protect grading copies, private storage and all eval runtimes,
including the current one. Record `protected_listing_without_exposure` with
input/completion lines. Wildcards, unsafe names, second protected operands,
unknown command forms, missing/ambiguous output and truncation keep detection.
Pin the new listing implementation in regrade provenance.

Retain both supplied exec error items as transport diagnostics, without tool
classification. Reject malformed/expanded error records. Extend the bounded
reducer for both still-unresolved call chains: captured-delimiter regex split,
first regex match, positive literal loop steps, JSON indentation and displayed
parsed-field provenance. Preserve finite tool timing floats as inert metadata;
float serialization and mixed-type arithmetic stay unsupported.

Add synthetic-path/output fixtures for all six listings, both transport
messages and both full code-mode chains, plus refusal variants. The first
native listing explicitly says its output was truncated for persistence;
its complete exec version resolves, while that native record keeps
`protected_path`. Both unresolved chains required code changes and now resolve
offline. Original host streams/reports were not repaired or regraded here.

Assumptions: paired command completion records are the evidence for observed
listing output. The supplied excerpts do not establish complete historical
capture. Source locations and host paths are absent from the new fixtures.
All graders/model transports are synthetic or mocked. No frozen inputs,
shared schema/CLI flags, other checkout, staging or commits change.

Validation: focused listing/code-chain/regrade provenance regressions — 82
passed in 3.34s. `.venv/bin/python -m pytest tests/eval -q` — 2004 passed
in 372.36s. Nine fixture hashes / 50 synthetic records and the exact
18-path scope/STATUS audit pass; nothing is staged or deleted.

# Native sleep and post-exit day-1 recovery — 2026-10-24

Classify native Extension items by kind. Accept the observed clock.sleep shape
as benign metadata with strict duration/identity/timestamp validation; preserve
the supplied record verbatim in a hash-pinned fixture. Unknown kinds remain
unsupported_native_item with their kind in the diagnostic, and malformed or
expanded sleep items remain inconclusive.

Continue audit-blocked harness day 1 through the ordinary missed verifier call,
then handoff generation/validation and the existing day-2 runner. Re-audit all
retained streams and manifests before selection. Preserve a final-attempt exit
pin if present; when absent, record recovery-time bytes explicitly rather than
using the preceding attempt's hash. Keep the source runtime/checkpoint unchanged.
Task results and continuation provenance retain the snapshot, executor exit and
actual post-exit verification times, hash/digest version and verdict hash.
Non-harness and ordinary regrade hash requirements remain unchanged.

Regression re-audit/regrade tests confirm both FILE-header records and four
runtime code-mode sequences use their current resolutions and become clean,
without waiving residual errors/access or manifest checks. All model/executor
transports are mocked with synthetic graders; actual host recovery is pending.
No frozen tasks, reports, shared schemas or CLI flags change.

Assumptions: the supplied record is an excerpt. A recovery snapshot establishes
current retained workspace bytes, not historical exit-time integrity. Original
host logs/private graders are unavailable in this worktree.

Validation: recovery/native/resolution and existing legacy continuation
regressions — 148 passed in 106.84s; regrade provenance regression — 1 passed
in 2.95s. `.venv/bin/python -m pytest tests/eval -q` — 1923 passed in
369.23s. `git diff --check` and the final scope/fixture/STATUS audit pass:
11 exact authorized paths, six STATUS headings, zero staged/deleted paths,
verbatim fixture bytes and no source-record location in changed files.

# Runtime store provenance and computed operands — 2026-10-24

Resolve the five supplied baseline-B code-mode sequences with complete paired
result provenance, including indexed/spread displays, bounded JSON helper data,
comparison-only loads, destructured literal pair maps and safe ASCII matchAll
patterns in concatenated/template heredoc commands. Keep saved helper values
across scripts without storage-writer identifiers. For a later script failure,
require a captured postwrite execution witness before retaining the write;
yielded or unsupported writer scripts cannot establish trust.

Audit the concrete command after reduction, retaining STOP-E4 detection over
resolution reasons. Refuse unknown live sources/effects, conditional mutations,
unsupported regexes, transformed/ambiguous result fields and incomplete output.
Allow a separate quoted heredoc after a literal for-loop using test -f/cat;
audit each path, including private and protected sibling roots.

Preserve all supplied records as six hash-pinned JSONL fixtures with verbatim
scripts. Regression sessions add synthetic identity/graders and cover the real
sequences plus negative variants. Update earlier expectations for read-only
displays that cannot affect operands. No frozen task, retained report, schema,
CLI flag, other checkout or actual private-grader storage changes.

Assumptions: supplied records are evidence excerpts, not complete original
execution captures. Offline clean fixture audits do not change historical
quality/validity claims. Original-stream re-audit remains on the host with the
original pinned inputs and graders. Model calls are mocked; no live calls ran.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 1904 passed in
362.58s. Focused audit regressions — 729 passed in 9.20s. Verbatim fixture
comparison — six files / 72 records match the supplied evidence exactly.
`git diff --check` and the authorized-scope/STATUS audit pass: 14 exact paths,
six STATUS headings, zero staged/deleted paths, no source-record location in
changed repository files.

# Session-authored computed code-mode inputs — 2026-10-24

Add a bounded static reducer for the measured FILE-header scripts and retain
the existing literal-call audit when reduction fails. Enumerate all tool sites,
reduce computed arguments to concrete values, and apply the normal access
checks before recording derived_from_audited_outputs. Provenance alone is
insufficient: literal fragments can synthesize a private path, so the completed
argument must also be audited. No captured code or external tool executes.

Track only confirmed text stores in one native session stream. Publish stored
tool-result fields only after auditing a paired, complete raw result displayed
without transformation. Unknown/missing sources, unsupported operations,
ambiguous displays, failed/yielded scripts, unawaited Promise collections,
helper mutation and unresolved arguments remain
inconclusive. Preserve STOP-E4 access detection at the source tool output;
detected access still invalidates the task and report. Regrade provenance pins
the new reducer, and retained/fresh audit artifacts retain resolution reasons.

The supplied excerpt has two records, native lines 65 and 75 of one task, not
three. Preserve both complete scripts as fixtures. With confirmed synthetic
original_sources they resolve to two and one commands respectively; standalone
excerpts lack the earlier store and remain inconclusive. Add regressions for
private tool output, unknown sources, pure private-path synthesis, sequential
scripts, state boundaries and incomplete/altered output evidence.

Assumptions: the supplied excerpt is the complete evidence available here; the
third requested record and earlier store are unavailable. No full historical
session or quality result is inferred. All paths/graders and model transports
in tests are synthetic; no live model calls or other checkouts are used.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 1828 passed in
368.77s. `git diff --check` passes. Scope audit confirms 11 exact authorized
paths, branch r5/v2, six STATUS headings and zero staged/deleted paths;
frozen task files, retained reports, shared interfaces and other checkouts are
unchanged. The source-record location is absent from changed repository files.

# Retained verbatim inputs and recovery accounting — 2026-10-24

The real 1,419-character patch record contains four escaped Add File bodies
followed by a literal-array for-of loop and a command display wrapper. The
previous synthetic test omitted that loop. Resolve every literal loop command,
including the read-only command display, while rejecting rebinding, mutation,
aliases and nonliteral operands. Keep the original source bytes in fixtures.
Recognize static non-path control calls, including both retained write_stdin
interrupts; command/path arguments and dynamic inputs remain unresolved.

Recover the continuation report's 119 overwritten provenance files by
reconstructing the exact legacy fallback bytes and requiring their SHA-256 to
match the original report pin. Never adopt overwritten bytes or replace a
historical pin. Read-only inspection accepts all 120 task provenance entries.
Regrade fills the unpriced day-2 call only from its complete retained usage and
exit-captured omitted/null tier, with verified settings and no requested tier.
Use the model default and retain all already priced historical calls. The
supplied day-2 counts yield $0.0331696; missing usage or unsupported tiers stay
unknown. Preserve the new inference in the next report's provenance.

The harness task's judge delegation and Fast prices are complete. Its null
control total instead comes from rerun_history.control_usd=null with no prior
calls. Recognize only the recorded prelaunch file collision with no executor
segments and the exact initial contract manifest pin; normalize that empty
trial to zero in fresh recovery and retained regrade. Other failed/launched or
unpriced calls retain unknown costs. The verbatim logs yield control_usd
$0.00468372 and task total $0.03405012. Retained-evidence regrade repeats without
changing known historical prices or source files.

Regression fixtures retain both complete code-mode inputs and the supplied
report/checkpoint accounting values, stderr, manifests and provenance. Tests
use local temporary copies, synthetic graders and mocked model transports.
No frozen tasks, report schemas, CLI flags or source evidence copies change.

Assumptions: no model calls or actual private graders are available. Read-only
pricing/provenance checks are not a host regrade or a new quality measurement.

Validation: focused verbatim/parser checks passed: 196 tests in 32.03s.
The full tests/eval run on the final parser version is in progress.

# Version 2 audit shapes and control deadline classification — 2026-10-24

Add exact regressions for a code-mode apply_patch single string containing
three absolute Add File headers. The existing literal decoder and patch-header
extractor already resolve this shape; no additional JavaScript evaluation is
introduced. Check all Add File, Update File, Delete File and Move to targets,
including canonical private paths reached through a workspace alias. Patches
built from a variable remain inconclusive.

Treat static pkill, pgrep and killall operands as process-name patterns. A
single-quoted regular expression's dollar anchor no longer makes the operand
unresolved. Other commands retain their operand rules; shell expansions and
redirections continue through the conservative audit.

Classify a failed control CLI with a structured
`control_failure {"reason":"deadline"}` stderr line as control_timeout,
independently of backend configuration. Runner-enforced control process timeouts
receive the same classification. Keep the task and aggregate invalid, retain
pinned stderr/accounting, and preserve infrastructure-only rerun eligibility.
Non-deadline and malformed failure records keep control_cli_error. No schema or
CLI flag changes.

Assumptions: Role 3 emits the line prefix control_failure followed by a JSON
object with reason=deadline. Host records and the actual private grader root
are unavailable here; all model transports are mocked. Host re-auditing and
report recovery remain pending.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 1722 passed in
369.66s. `git diff --check -- eval tests/eval state/STATUS-eval.md` passes.
Scope audit: 10 exact authorized paths, r5/v2, six STATUS headings, zero staged
paths; frozen inputs, retained reports and shared interfaces are unchanged.

# Recovery control costs and mixed-snapshot provenance — 2026-10-24

Use the executor's tier resolver for pinned control_call records: explicit
service_tier first, then the known model default when omitted/null. Record the
inference in pricing_evidence; unknown models, unsupported tiers and incomplete
usage remain unknown. rerun_invalid, rerun_unaccounted and continue_day2 reuse
the normal runner's hash-pinned fresh stderr and control accounting.

Preserve completed tasks' calls, costs and provenance artifacts when the normal
runner builds a recovery report. Rebuilding those files previously changed
their bytes while the recovery wrapper kept the earlier artifact hashes. The
read-only recovered3 copy has 119 such stale pricing-provenance hashes; its
fresh selected task's hash matches. No retained report was modified here.

Pin each referenced snapshot's complete-content SHA-256 in call provenance,
and verify it against the metadata catalog independently of the top-level
snapshot_id. Validate call pricing_ref/model membership across all catalog
snapshots. Accept legacy evidence without the new per-snapshot pins, preserve
historical accounting, and continue rejecting altered artifacts or snapshots.
All changes use eval-owned artifact content; schemas and CLI flags are unchanged.

Regression coverage includes retained v1 reports with Standard calls plus fresh
Fast controls, a one-task invalid/unaccounted rerun followed by checkpoint reuse
and two regrades, day-2 control stream pins, explicit/default/unknown tiers and
provenance tampering.

Assumptions: reported host outcomes remain host observations. This session uses
this worktree's .venv, synthetic graders and mocked model transports only; host
regeneration from the original pinned source remains pending.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 1690 passed in
313.94s. `git diff --check` passes. Scope audit: 11 exact authorized paths,
six STATUS headings, zero staged paths and no report-copy path in changed files.
Frozen tasks, retained reports and shared interfaces remain unchanged.

# Version 2 baseline B population regression — 2026-10-24

Confirm full-v2-b.yaml already lists all 100 tasks in task_population, in
full-v2-a order, while selecting only the 80 single-session tasks for execution.
Add a synthetic-grader regression that computes the real configured digests
for A, B and harness and requires population equality while preserving B's
distinct selected-task digest. No config or frozen task bytes change.

Update B's estimate with the user-supplied host population digest
12e7574905a6c6e4f7f49a85eacad38899fa5f0d221a3c93939a83ab13b6f041
and distinguish its 80-task selection digest. The host digest was not recomputed
here; no private grader root or live models were accessed. Costs are unchanged.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 1665 passed in
295.50s. Scope/config/STATUS audit passes for four authorized changed paths,
unchanged frozen tasks/configs, six STATUS headings and zero staged/untracked
paths. `git diff --check` passes.

# Version 2 public freeze — 2026-10-24

Freeze all 100 v2 meta.json files by changing only frozen=false to true after
the user-approved decision 0008 procedure. Preserve all task contents and v1
files. Population: 20 bug_fix, 20 feature_plus_test, 40 multiple_requirements
(including 20 two-session), 20 constrained_refactoring; 20 families of five.
User-supplied independent host validation: 100 distinct grader directories,
zero public private markers, 2,994 mutants killed, 6 equivalents, zero survivors.

The final digest is not computed here: external private graders are unavailable.
Add read-only `python -m eval.freeze_v2 --private-root "$LHM_PRIVATE_GRADERS"`
to print inventory and the exact runner-compatible tracked-public-plus-private
population/selection digests on the host. DESIGN.md records the 2026-10-24 public
freeze, digest procedure and pending Role 1 publication. Existing full-v2 configs
already specify calibration=false, priority Fast and codex-cli
0.163.0-alpha.11.1; update their estimates to reflect the frozen metadata without
changing scenario costs or call bounds. Verify real runner freeze/digest
selection using mocked graders and no executor calls; preserve unfrozen-input
refusal coverage. No schema or existing CLI flag changes, model calls, staging
or commits.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 1664 passed in
331.06s. HEAD byte comparison confirms all 100 metadata files changed only
the freeze flag; exact scope check passes for 110 authorized paths with zero
staged paths. `git diff --check -- eval tests/eval state/STATUS-eval.md` passes.

# Host recovery, default-tier pricing and eligibility diagnostics — 2026-10-24

When a legacy workspace pin fails both digest algorithms and the report has no
workspace artifact entries, compare the retained non-cache files with the
trusted published TASK/workspace copy. Require identical bytes/file sets and
runtime file mtimes at or before the matching recorded exits. Preserve the
pinned-artifact path and historical hashes. Regrade, rerun, continuation and
retained-context audits record `workspace_verification: published_workspace_copy`
with comparison counts; regrade retains the published copy for later recovery.

For unrequested executor tiers, omitted/null applied tiers use the model's CLI
default: Sol 6.1 Standard and Luna priority. Per-process evidence and pricing
provenance label the inference; explicit native default maps to Standard.
Explicit requests still require matching native applied evidence. Control
accounting and retained historical report costs remain unchanged.

Allow valid null-cost interrupted/resumed tasks with missing usage to qualify
for rerun_unaccounted even without historical tier/price evidence. Archive those
unknowns under the existing replacement policy. Keep complete-usage/price-only
gaps, missing controls, unmarked gaps and access/audit failures ineligible.
Refusals identify safe failed conditions, including through CLI stderr.

Regression coverage uses synthetic retained workspaces/logs and mocked executor,
controller and judge protocols. Host reruns and actual recovery metrics remain
pending; no private grader root, model call, network, staging or commit was used.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 1,662 passed in
357.51s. Focused eligibility/CLI checks after the diagnostic refinement —
21 passed in 28.73s; published-copy boundary checks — 12 passed in 14.66s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` — exit 0.

# Full unfrozen version 2 population — 2026-10-24

Record the user-supplied calibration result (15/19 valid tasks, 0.789,
95% interval 0.579–0.947) and retain all twenty pilot tasks unchanged. Add the
remaining sixteen families / eighty tasks with sixteen numbered requirements
per single-session task and eighteen across two days. Make interacting policies,
shared call paths, exact constraints and structured day-1 records explicit in
the public prompts. Keep graders, coverage, references and mutation material
external; publish task IDs and numbers in reports/full-v2-validation.md.

Offline validation: 100 references pass, 100 starters fail, 1,564 requirements
have executed mappings, and all 100 graders are distinct. Public assertion
line overlap is zero. Exhaustive AST mutation validation records 6,092 killed,
49 explicitly reviewed/hash-bound equivalents and zero survivors. Input pins
and candidate enumeration are checked independently after all mutation runs.
Against 376 actual corpus files, retain 20 task warnings / 224 assertion-line
occurrences; these diagnostics do not waive public-input overlap failures.

Add lexicographic full-v2 A and harness selections over 100 tasks / 120 sessions,
and B over 80 single-session tasks at Sol max with the 100-task population pin.
A/harness use Sol medium; all request Fast priority and Codex
0.163.0-alpha.11.1. Harness uses codex_cli and reinstruction_limit=2. Matched
STOP-3 estimates use the existing Fast snapshot with 120/80/780 call bounds
before dynamic judges. New config tests verify population parity and refusal
before any external call while unfrozen.

Validation: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/eval -q`
— 1611 passed in 233.65s. `git diff --check -- eval tests/eval state/STATUS-eval.md`
— exit 0. Scope checks: 1,068 changed files, zero protected/pilot changes,
zero private-root occurrences and zero staged changes.

All metadata remains frozen=false and full configs use calibration=false.
Claude's host validation, separate freeze and approved benchmark execution remain
pending. No live model, nested Codex, network, staging or commit operation was
performed; v1 tasks/graders, retained reports and shared interfaces are unchanged.

# Continuation roots, legacy workspace recovery and literal loops — 2026-10-23

Resolve temp roots, runtime roots and grading roots before comparison. Exclude
the task's own runtime from sibling protection under either system spelling,
including persisted historical continuation contexts. Keep sibling runtimes,
private roots, aliases and grading copies protected.

Add a legacy-only fallback when both workspace digest algorithms fail: match
every non-cache retained file against the source report's published workspace
artifact hashes, require identical file sets and bound all file mtimes by
matching checkpoint/report exit timestamps. Apply it to regrade, infrastructure
reruns and day-2 source/copy verification, including retained-context audits
and read-only re-audit selection. Preserve historical pins and record
`workspace_verification: published_artifact_hashes` plus compared counts in task
provenance and regrade diagnostics. Refuse absent pins, changed/missing/extra
files, late mtimes, symlinks and unknown/explicit-v2 versions.

Accept a newline between a literal loop's `done` and the following command.
Absolute literal list entries already use ordinary operand resolution; cover
the supplied absolute AGENTS.md loop shape in all four executor/native capture
forms. Keep private-root/alias/traversal detection and unresolved dynamic lists.

Validation: new offline recovery-boundary regressions plus the updated existing
regrade provenance assertion — 58 passed in 29.35s.
`.venv/bin/python -m pytest tests/eval -q` — 1608 passed in 176.19s.
Authorized-path/frozen-file/branch/STATUS-heading checks passed and
`git diff --check -- eval tests/eval state/STATUS-eval.md` exited 0. All model
and executor calls are mocked. No host report was repaired, private grader
storage accessed, frozen task or shared interface changed, or file staged.

# Replacement of interruption-only accounting gaps — 2026-10-23

Add `eval.runner.rerun_unaccounted` for finished reports containing valid tasks
with null executor costs caused by recorded infrastructure interruptions. Use
the existing fresh-runtime/regrade engine, replace selected outcome/accounting,
and preserve old spending and outcomes in hash-referenced provenance. Keep the
existing `rerun_invalid` policy of accumulating prior spending unchanged.

Select only missing executor usage with interruption/capacity evidence, clean
historical/current audits, known control costs, supported pinned prices, and
unchanged retained inputs/logs/control/workspaces. Refuse other null-cost causes,
recoverable complete usage and every access match. A missing hard-restart exit
pricing capture requires independently timestamp-bounded native applied tier
records; later resume settings cannot establish the interrupted process's price.
Regrade every unselected task and retain any fresh quality failure. Record task
IDs, reasons, replaced outcomes/calls/costs/segments, replacement policy and
fresh outcomes/costs in per-task provenance and run diagnostics.

Retain the last timestamp-bounded native cumulative counters per interrupted
rollout as `partial_usage` in segment/result/checkpoint/telemetry evidence and
replacement provenance. Label them cumulative-session lower bounds and never
use them for costs. Recover them before resume and during retained regrade;
new interrupted native deltas are never promoted to complete billable usage.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 1551 passed in
161.86s. Focused partial-usage/replacement/restart regressions — 72 passed in
27.91s before the final missing-pin case. `git diff --check -- eval tests/eval
state/STATUS-eval.md` exited 0; authorized-path/frozen-file/STATUS-heading/branch
checks passed. Models and executors are mocked; no host report, private grader storage, frozen task, shared schema,
existing CLI flag or other checkout is changed. No staging or commits.

# Versioned workspace digests and post-verifier pins — 2026-10-23

Exclude bytecode and Python tool caches from new v2 workspace digests and use
the same ignore patterns for trusted/published workspace copies. Record
workspace_digest_version in checkpoint task/segment pins. Preserve the exact v1
algorithm; match unversioned historical pins under v1 or v2 without rewriting
them. Enforce the recorded algorithm throughout regrade, day-2 copying and
retained audit contexts, infrastructure reruns, re-audit and republication.
Unknown versions and unmatched existing pins fail closed. Historical read-only
operations without a workspace pin retain their previous behavior.

Record harness workspace pins after verifier checks, including error and
pending-verification recovery paths. Launch verifier Python with -B and
PYTHONDONTWRITEBYTECODE=1 without changing the parent environment. Inner command
arguments are verifier-owned; cache exclusions also cover explicit compilation
and tool caches. Preserve executor capture timing, shared report schemas, CLI
flags, frozen tasks and retained reports.

Add offline regressions for cache-only changes, source/mode/link changes,
legacy v1 compatibility, version selection, unreadable directories,
post-verifier retry timing and recovery consumer checks. Models are mocked;
no retained host run was repaired here.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 1510 passed in
142.90s; digest regressions — 34 passed in 9.75s. Authorized-path and STATUS
heading checks passed; `git diff --check -- eval tests/eval state/STATUS-eval.md`
exited 0.

# Explicit recovery of unpinned executor captures — 2026-10-23

Add optional `--allow-unpinned` to republication. Recover only regular
`exec-N.stderr` and `final-N.md` captures from the recorded runtime or BACKUP/TASK,
with the same redaction and destination-conflict checks. Existing control/log
pins are always enforced. Without the flag, publication and counts stay as
before; missing captures remain skipped even with the flag.

Record per-capture artifact entries in
`run-diagnostics.json.republication.artifacts`, containing task_id, path,
sha256 of the published redacted bytes and provenance=republished_unpinned.
The frozen shared report schema accepts path/sha256 only; its artifact
references retain that shape. Preserve existing diagnostics, refresh any
report references to the changed diagnostics hash, and refuse altered
provenance. Preflight all tasks before writing, and reuse identical evidence
without duplicate records or repeated metadata writes. CLI output contains
only task IDs and counts, including opt-in published_unpinned counts.

Runtime capture pinning already shipped in 6dbc684. Strengthen mocked runner
tests for both stderr and final messages: require persisted per-segment hashes
before trusted grading and verify each capture restores without the flag.
No retrospective checkpoint pins, model calls, grading, workspace copies or
metric/classification rewrites are introduced by republication.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 1476 passed in
139.70s. Focused republication/runtime checks — 70 passed in 12.11s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- tests/eval/test_access_audit.py tests/eval/test_audit_performance.py eval/tasks eval/tasks-v2 eval/reports schemas controller verifier plugin prompts AGENTS.md` — exit 0.
Authorized scope/STATUS-format check passed; branch r5/v2. No retained report,
frozen task, shared schema, private storage or other checkout was changed.
No staging, commits or live executor/controller/judge calls were performed.

## Assumptions

- The requested provenance field belongs to the richer diagnostic artifact
  entries; report artifact references remain valid under the frozen schema.
- Claude's 34 published/6 skipped smoke-copy result is a user-supplied host
  observation. This session uses only synthetic runtimes and mocked executors.
- Restored final messages enable later retained-evidence classification;
  republication itself preserves historical metrics and classifications.

# macOS evidence publication and offline republication — 2026-10-23

Bound symlink checks to the runtime/source root. Permit system aliases above
that boundary; reject root/inner links and traversal. Share the check across
publication, control guards/accounting, day-2 copy validation, infrastructure
reruns and static templates. Preserve the existing workspace publication rule.

Add `python -m eval.runner.republish --private-root P --out REPORT_DIR
[--runtime-root BACKUP]` for completed v1/v2 runs. Preflight all tasks against
checkpoint control pins, executor/native audit hashes and byte counts, segment
metadata and existing publication pins/bytes. Restore only allowlisted redacted
evidence from recorded runtimes or BACKUP/TASK, retain the normal flattened
day-2/interruption layout, and update only per-task report artifact entries.
Never invoke models/graders, copy workspaces or rewrite checkpoints, metrics,
costs, results or task-completion classifications. Success output contains only
counts and task IDs; input failures contain no paths or evidence contents.

The sampled historical full-A/full-B/smoke checkpoints do not pin executor
stderr/final bytes. Count those captures as unpinned and skip them; do not
fabricate retrospective hashes. Pinned controls (including control stderr) and
audited events remain restorable. New executor segments pin events, stderr and
any final message immediately on exit in internal evidence_sha256 manifests.

Synthetic regressions create an explicit symlinked parent, rather than relying
on pytest's resolved tmp_path. Cover normal runner publication/pins, continuation
copying, infrastructure reruns, static templates, backup-only recovery, v1/v2,
redaction/newlines, repeated runs, unchanged non-artifact report fields,
workspace exclusion, all-task preflight, altered/missing evidence, inner links,
manifest links and conflicting destinations/artifact references.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 1448 passed in
132.21s. `git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- tests/eval/test_access_audit.py tests/eval/test_audit_performance.py eval/tasks eval/tasks-v2 eval/reports schemas controller verifier plugin prompts AGENTS.md` — exit 0. Branch/scope check: r5/v2; only authorized paths changed.
No retained report, frozen public task, private storage or other checkout was
modified; no live executor/controller/judge call was made.

## Assumptions

- Claude owns the five host republications and the external BACKUP/RUN/TASK
  layout. Host backups and private graders were unavailable in this sandbox.
- A historical file without a retained pin cannot be verified merely because
  it exists in a backup. Its contents must not be adopted as trusted evidence.
- Republication runs after all host runner activity has stopped; it preserves
  historical raw external references and does not migrate executor segments.

# First-occurrence fingerprints and executor corpus warnings — 2026-10-23

Track each qualifying fingerprint's first tool-input/output provenance across
executor JSON and native rollout streams. Decode literal command payloads and
patch additions; context/deletion lines and current workspace files never
establish authorship. Exempt later echoed output only when an authored input
provably precedes every output occurrence. Earlier output remains access evidence
after copying, and private-path checks remain independent.

Use within-stream record order, strict timezone-aware timestamps and matching
command-result anchors within a known session. Match exact command/output
representations with IDs, or equal-count ordered repetitions in one native and
one CLI stream. Unknown session identity, unequal repetitions, missing timestamps
without an anchor and unresolved cross-stream order keep the fingerprint match.
Do not use caller path order as chronology. Retained/fresh filesystem contexts
share only provenance, and malformed/incomplete evidence still invalidates.

Audit accumulated executor/native history before runner continuation decisions.
Pin fingerprint_history.py in retained recovery implementation hashes. Keep
existing access and performance probes unchanged; update only the recovery hash
inventory expectation to include the new implementation file.

Normal grader validation optionally reads regular Python files recursively from
private .corpus/ storage. Report corpus_file_count,
shared_corpus_assertion_line_count and corpus_warning_count per task, with warning
task/shared-line totals in the summary. Counts describe grader-line occurrences,
so duplicate corpus copies do not inflate them. Corpus matches never change
validity or exit status; v2 public assertion copies still fail validation. An
absent corpus has zero files. Publish no corpus/grader contents or private paths.

Regression coverage includes patch/heredoc/printf/Python/raw-template writes
followed by cat or test execution, output-first opaque/private reads followed by
copying, cross-stream timestamps and untimed duplicates, repeated results,
ambiguous chronology, session-ID reuse, retained contexts, per-line provenance
and mocked harness retries. Corpus tests cover missing/populated corpora, both
task versions, warning-only CLI output, duplicate lines and public-copy failure.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 1406 passed in
138.46s. Existing access/performance probes remain unchanged; the initial full
run exposed extra Python parses of plain shell operands, corrected before the
passing rerun. `git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- tests/eval/test_access_audit.py tests/eval/test_audit_performance.py eval/tasks eval/tasks-v2 eval/reports schemas controller verifier plugin prompts AGENTS.md` — exit 0.
Scope/private-path scan passed. No live evaluation or real corpus validation
was performed; retained reports and private files were not modified.

## Assumptions

- Claude's 22 shared executor-written assertion lines across 20 pilot tasks are
  user-supplied findings. The actual corpus will be supplied later; this session
  uses synthetic graders/logs/corpus files and makes no model calls.
- Corpus layout is unspecified. Read regular .py files recursively below
  .corpus/ across task/run directories. File count distinguishes an absent
  corpus from a checked corpus with no matching assertion lines.
- Ambiguous cross-stream chronology cannot establish input-first authorship.
  Retain the fingerprint match rather than infer order from filenames or waive
  malformed/incomplete evidence. Host re-audit remains Claude's task.

# Calibration pilot audit corrections — 2026-10-23

Exclude shared public lines across both shipped task-set versions at audit time,
because the private grader corpus spans v1 and v2. Exclude generic imports,
comments, blank/punctuation-only lines, decorator spans, TestCase headers and
test method headers. Preserve distinctive-literal filtering, output-only
fingerprints, immutable shipped-input exclusions and fail-closed detection of
qualifying hidden lines. Synthetic regressions cover graders sharing public
workspace, prompt and day-2 lines across versions, plus generic scaffolding and
executor-written lines that must remain eligible.

Report per-task shared_public_line_count and shared_assertion_line_count in
offline grader validation. Count nonempty normalized line occurrences; assertion
spans include Python assert statements and assert* calls. Reject shared assertion
lines for v2 in ordinary and mutation validation; v1 reports counts without
changing its acceptance rule. Revise private input/expectation pairs across all
four pilot families, preserve every requirement mapping and archive originals
privately. Refresh the counts-only validation table. Current local graders had
zero exact shared assertion lines before the revision as well.

Decode substitution-free String.raw templates as literals with raw backslashes
and normalized newlines. Audit their contained shell command normally, including
quoted heredoc data. Interpolation, other/dynamic tags and uncertain String
bindings remain inconclusive. Expand bounded relative globs in literal for-loop
word lists before variable substitution. Preserve concrete symlink/private-path
detection and reject absolute, parent-traversing, variable-built and quoted glob
words. Regression cases cover executor JSON plus native command/function/custom
records, no matches, whitespace in matches, suffixes and private symlinks.

Offline candidate validation: 20/20 valid starter/reference pairs, 249 reference
checks, 156 starter failures, 252/252 requirement mappings covered, 100 shared
public lines, 0 shared assertion lines, 1121 killed mutants, 18 reviewed
equivalents and 0 unreviewed survivors. Per-task IDs and counts are in
reports/pilot-v2-validation.md. No live executor/controller/judge calls were made.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 1351 passed in
179.73s. Offline validation and mutation CLIs — exit 0.
`git diff --check -- eval tests/eval state/STATUS-eval.md` — exit 0.
Frozen public tasks, schemas, retained run reports and other roles remain unchanged.

## Assumptions

- The host's four invalidities and absence of access attempts are user-supplied
  findings. This session verifies synthetic logs and offline graders; Claude
  owns host retained-run re-audit and recovery.
- Host retained-run recovery must use the original hash-pinned graders with the
  updated audit code. Revised private candidates have different hashes and are
  for subsequent calibration; privately archived originals preserve recovery.

# Read-only command-array display callbacks — 2026-10-23

Resolve the retained const-array shape with a later
`results.forEach((result, i) => text({command: commands[i], result}))` callback.
Permit indexed reads only in this read-only display grammar, after the single
collection use. Continue auditing every command element independently. Existing
support for `Promise.allSettled`/`Promise.all` and shorthand `cmd` followed by
literal options now has explicit regression coverage.

Retain whole-input binding checks. Index assignments/updates, push, splice, pop,
shift, unshift, sort, reverse, aliases and reassignment before, inside or after
the callback remain inconclusive. Computed indices, transformed values, opaque
callbacks and reads before the collection use also remain inconclusive.

Add a synthetic JavaScript fixture preserving the supplied complete structure,
including a Python one-liner with embedded double quotes. Verify native audit
cleanliness and access detection through a middle-element synthetic alias.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 1279 passed in
123.01s. `git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks eval/tasks-v2 eval/reports schemas` — exit 0.

## Assumptions

- The user reports commit 64a825b and a clean host re-audit of the template case.
  The const-array host record still needs re-audit after this follow-up. This
  session uses synthetic evidence only, without host streams or private graders.

# Code-mode templates and immutable command arrays — 2026-10-23

Decode substitution-free backtick literals with JavaScript escape and newline
semantics. Accept quoted strings and these templates in const/let command arrays
used once through a direct tool argument, map callback or for-of loop. Expand
every element into a separate audited command without evaluating JavaScript.

Require one binding and one collection use, direct element arguments, and no
rebinding, mutation, aliases, extra uses or scope escapes. Interpolation,
nonliteral array elements, unsupported argument forms and uncertain identifier
identity remain inconclusive. Preserve existing command/path checks and access
invalidation, including a private-path command in a middle array element.

Regression tests replay native custom_tool_call records with both exact host
shapes, const/let bindings, quoted/template elements, map/for-of/direct-array
uses, and synthetic private paths. Near misses cover interpolation, nonliterals,
reassignment, push/splice/index mutation, aliases, repeated uses, transformed
elements, scope escapes and escaped identifiers.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 1218 passed in
114.77s. `git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks eval/tasks-v2 eval/reports schemas` — exit 0.

## Assumptions

- Supplied input shapes describe the two host failures. Actual host streams and
  private graders are unavailable; this session verifies synthetic evidence
  only. Retained-evidence recovery remains a host step.

# Restart recovery, selective reruns and audit precision — 2026-10-23

Exempt only missing terminal events in explicitly interrupted executor segments;
retain every other inconclusive rule in run, re-audit and regrade. Reuse valid
manifest-pinned pre-launch contracts and archive verified partial preparation
without deleting evidence. SIGINT/SIGTERM retain stop diagnostics and exit 130
without a traceback, including control preparation and executor cleanup.

Add `eval.runner.rerun_invalid` with the requested private-root/source/output/
reason selector. Require infrastructure causes, re-audit before selection,
refuse access matches and changed manifests, and start eligible tasks in fresh
runtimes. Regrade unselected tasks from retained evidence. Retain prior costs
once, propagate unknown accounting, and pin per-task/run rerun provenance.

Use newline-only JSONL framing in audit, native telemetry, control accounting,
limit detection and redaction. Find heredoc boundaries before shell tokenization;
quoted body data cannot corrupt parsing of later compile/test commands.
Regression coverage includes mixed raw-regex quotes/backslashes, Unicode line
separators, hard restarts, pre-launch files, signals, rerun refusal, provenance,
source immutability and accounting across resume/regrade.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 1092 passed in
103.45s. `git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks eval/tasks-v2 eval/reports` — exit 0.
No task files, retained reports, report schemas or existing CLI flags changed.

## Assumptions

- The supplied four host failures are infrastructure/parser cases without access
  attempts. Host artifacts and private graders are unavailable here; recovery is
  verified using synthetic retained runs and mocked model/executor calls.
- Fresh reruns require a completed source report; halted checkpoint-only runs
  use the existing resume path first. Host outcome recovery remains pending.

# Version 2 candidate pilot and executor service tier — 2026-10-23

Add optional task_root and service_tier configuration. Keep default v1 hashes,
CLI defaults, frozen tasks and report schema unchanged. Select public inputs,
full populations, freeze checks, digests, regrade and day-2 observations from
the configured root. Namespace nondefault-root digests so compare rejects
cross-set reports. Pass explicit tiers on every executor launch and verify
native applied settings per process; missing/different tier invalidates before
grading. Retain tier requests and evidence in checkpoints and diagnostics.

Write the v2 design before constructing a 4-family, 20-task unfrozen pilot.
Public packages include regression tests, constraints and generated verification
artifacts; private graders, references, requirement coverage and mutation reviews
remain external. Candidate validation supports explicit v2 IDs and untracked
candidate hashing without relaxing frozen-input execution. Mutation equivalence
records include day-2 specification bytes. Publish only per-task numerical
validation results in reports/pilot-v2-validation.md.

Add pilot-v2-a configuration and the 24-launch STOP-3 estimate. Priority pricing
is unavailable in the pinned offline snapshot; retain null costs and require
host verification before spending. Calibration, candidate freeze and the planned
remaining 16 families are pending. No live model calls, staging or commits.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 1058 passed in
122.14s. `git diff --exit-code -- eval/tasks` — exit 0.

# Literal JavaScript expressions and day-2 continuation — 2026-10-23

Decode quoted string expressions using literal concatenation and literal
`replace`/`replaceAll` chains without evaluating JavaScript. Preserve first-only
string-pattern replacement, replacement-dollar substitutions, empty patterns,
escapes and UTF-16 semantics. Resolved command/workdir/patch inputs pass through
the existing access checks. Synthetic native regressions cover the stray-X
patch wrapper, replacement into a private path, and unresolved near misses.

Add the host-only `python -m eval.runner.continue_day2 --private-root P --from
SOURCE --out NEW` command. Select only audit-recoverable pre-day-2 invalid tasks,
requiring all retained day-1 logs clean under current code and unchanged
manifests. Regrade other tasks, copy the selected workspace/evidence into a
fresh external runtime, verify its exit hash, and reuse the normal runner's
version checks, exact prompt delivery, harness orchestration and retries.
Grade completed eligible work once after exit in a fresh trusted copy.

Preserve source evidence and accounting, append new calls/costs, and record
source/code/config hashes, copy checks, both days' timestamps and their gap.
Copied day-1 logs retain their original audit context with hash checks; new
access to the source runtime remains protected. Re-audit/regrade understands
continued evidence, and regrade checks full-population hashes where configured.
No frozen tasks, retained reports, shared schemas or existing CLI flags change.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 1023 passed in 97.92s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks eval/reports` both exited 0. Mocked executors
only; no model calls, real private-root lookup, staging or commits occurred.

## Assumptions

- Full A results and the balanced-brackets day-1 failure are user-provided host
  evidence. This session uses synthetic paths/graders; historical regrading and
  day-2 execution remain host work with the recorded CLI version and pricing.
- The source checkpoint supplies the recorded semantic configuration; its
  original config byte hash is retained and the materialized copy is separately
  hashed. A fresh output command does not resume an incomplete continuation.

# Heredoc regression in literal-loop audit — 2026-10-23

Restrict loop discovery to shell syntax. Heredoc payloads/delimiters and comments
are excluded from discovery; quoted arguments already retain their raw word
boundaries. Original text still receives the same operand, expansion, private
marker, canonical-path and output checks as before literal-loop resolution.
This restores Python scripts passed through quoted heredocs without hiding
protected-path evidence or clearing previously unresolved expansions. Mixed
actual shell loops and heredoc/comment spans remain outside bounded unrolling.

Both supplied shapes are synthetic regressions: py_compile followed by nested
Python loops, and PYTHONDONTWRITEBYTECODE=1 with a case list and tuple-unpacking
loop. Tests compare complete audits against the pre-loop-resolution behavior,
cover item.started/completed pairs and native command/function/code-mode records,
and retain the literal parent-directory loop fixes. Additional data cases cover
tab-stripped/multiple/escaped heredocs, quoted arguments and here strings.

Claude's host comparison across 104 finished tasks is user-provided evidence:
three literal-loop tasks became clean, while Python heredoc scripts regressed.
Rechecking all 104 for clean audits with no private matches remains host work;
this session cannot inspect those logs or the real private root. Retained
reports and frozen tasks are unchanged; no model calls, staging or commits.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 943 passed in 83.58s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks eval/reports` both exited 0.

## Assumptions

- The retained host logs are unavailable here. Pre-change behavior is compared
  by disabling only loop transformation while retaining all legacy audit checks
  and identical synthetic log bytes; no host outcome is inferred from tests.

# Literal for-loop access audit — 2026-10-23

Resolve one bounded literal-list `for` loop without executing shell code. Each
`$name`/`${name}` filesystem word is expanded for every literal value and passed
through the existing canonical/private-root, symlink, traversal and recursive
access checks. Conditional operands are inspected even when absent. Executor
JSON, native command items, function calls and custom JavaScript wrappers share
the same parser.

Regression coverage includes the exact smoke command reading parent
`AGENTS.md` files, synthetic private-root traversal and symlink access (including
a later list value), and recursive access through an ancestor alias. Dynamic or
glob lists, command substitution, arithmetic, nested/while loops, mutations
before/inside/after the loop and directory-changing bodies remain inconclusive.
Unsupported embedded options, redirections and executable code also retain
uncertainty. No shell command from a captured record is executed by this audit.

Host re-audit of the retained second harness smoke and pilot B is pending.
No retained report, frozen task, shared interface or CLI flag changed. This
session uses only this worktree's `.venv`, synthetic private locations and
mocked model calls; the main-checkout baseline A remains separate.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 875 passed in 78.68s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks eval/reports` both exited 0.

## Assumptions

- The supplied smoke/pilot failures describe unavailable host evidence. These
  regressions establish parser behavior, not the retained runs' audit outcomes.

# Smoke accounting and publication fixes — 2026-10-23

Control accounting accepts symlinked ancestors above the runtime (macOS `/var`),
while rejecting links at/below the runtime and absolute/traversing manifest
entries. Hash-pinned control envelopes retain observed models and priced costs.

Published grading logs now allow only unittest identifiers/status and summary
lines. Full stdout/stderr and the combined grading log stay in the external
runtime. Synthetic failing/error/skipped graders verify that assertion source,
assertion/error messages and skip reasons appear nowhere in either the initial
published report directory or its regraded copy.

Generated JSON, log copies and artifact references use repository-relative
checkout paths. Validation resolves references from the repository root and
accepts historical absolute references. Regrading normalizes copied historical
review logs without changing the retained source; comparison source references
use the same path convention. External runtime references remain absolute.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 686 passed in 79.93s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks eval/reports` both exited 0.
Frozen tasks and retained reports remain unchanged. No model calls, real private
grader lookup, staging or commits. Host smoke verification remains pending.

## Assumptions

- The host smoke result is user-provided evidence; its external report is not
  available or inspected here. All new grader/executor coverage is synthetic.
- Relative published references use the repository root, while external runtime
  references retain their absolute locations for evidence verification.

# Capacity recovery and timeout continuation — 2026-10-23

Recognize only case-insensitive `at capacity` in structured `error` and
`turn.failed` events, including controller and forwarded judge stderr envelopes.
Retain executor segments and resume the same session after 60/120/300/600-second
waits, independent of attempt/retry/reinstruction limits. Control operations
archive interrupted evidence before rerunning. Exhausted recovery halts with no
task outcome and resumes from the same `--out`; capacity never becomes a failed
criterion, reinstruction or control CLI error. Checkpoints and run diagnostics
mark infrastructure recovery and waits; control recovery evidence is hash-pinned.

Zero tokens apply only to capacity refusals before any item event. Partial work
with missing usage remains unknown. Native cumulative token-count deltas retain
executor work across resumes; output already includes reasoning. Each control
envelope affects its own call, including interrupted envelope-only evidence with
measured operation latency. Final executor timeouts continue the task loop;
unclassified nonzero exits keep STOP-E1 and usage limits still halt immediately.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 678 passed in 79.26s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks eval/reports` both exited 0.
Mocked recovery tests cover both exact error events, one-wait success, exhausted
recovery and later resume, contract/verifier/handoff/day-2 operations, zero versus
unknown usage, native deltas, timeout continuation and unchanged usage limits.
No model calls, live private-root lookup, retained report edits, staging or commits.

## Assumptions

- The user's two observed capacity events define the entire capacity vocabulary;
  no other service-error wording or retry classification is added.
- This worktree is r5/harness-smoke at f844d27, with its own `.venv`; main's
  concurrent smoke and historical full-a-attempt1 evidence are untouched.
- Live validation and full-run measurements remain host work. Report schema and
  CLI flags remain unchanged; recovery classification is retained in artifacts.

# Harness accounting, configurations and run provenance — 2026-10-23

Price each hash-pinned controller/verifier `control_call` stderr record with the
eval price snapshot, including retries and codex_cli-to-cheap_api fallback.
Retain actual model/backend/status/latency and ignore controller USD. Delegation
completeness/count checks and missing model/tokens propagate unknown control
and total costs. Invalid tasks retain costs. Mechanical verification and
validate-handoff add no calls. Single observed control model fills metadata;
none or multiple models produces a warning and null. Operation sidecars retain
exit/deadline evidence and survive usage-limit and interrupt recovery.

Add smoke/full harness configurations with two reinstructions (three attempts
per day), reduce full B to 100 single-session tasks, and publish planning
estimates. The estimate guard accepts exact bundled NAME configurations with
NAME-estimate.md while retaining historical pilot/full mappings. Headline
harness cost comparison remains pending live measurement. Decision 0007 drops
local Gemma/QLoRA and parity measurement, assigns C a user-filled stratified
20-task subset, and compares handoff with A. No frozen tasks changed.

New checkpoints capture starting git commit and pricing snapshot ID. Reports
use the recorded commit, warn with both values on HEAD/snapshot drift, and
preserve build-time behavior for older checkpoints. Prices in report metadata
still identify the snapshot actually used to price the retained calls.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 621 passed in 57.81s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks eval/reports/pilot-a eval/reports/pilot-b`
both exited 0. Tests use mocked models and synthetic local graders only.

## Assumptions

- Role 4 will supply the exact judge forwarding/delegation records described by
  the user. This worktree does not include or modify that implementation.
- Mocked tests establish accounting/orchestration, not live compatibility;
  Claude runs the host smoke next. No model/network/private-root lookup occurs.
- Luna planning uses 5,000 uncached input and 1,000 output tokens per generation;
  executor planning uses pilot A's session average. Full B also shows its
  historical max-effort pilot alternative. Planning estimates are not measurements.
- Only eval-owned paths change in r5/harness-smoke at b9ac131. Main's running
  full-A process and worktree are untouched. No staging or commits.

# 0.163 audit compatibility and usage-limit recovery — 2026-10-23

Support the host smoke's line-9 `event_msg.thread_settings_applied` as non-tool
metadata. Validate its thread/settings envelope and nested permissions and
collaboration fields; scan the complete record for private markers, including
extra keys, aliases and canonical traversal. Other unknown kinds and malformed
settings remain inconclusive. Telemetry combines its applied model/effort with
turn_context, rejects conflicts and publishes both evidence sources. A synthetic
34-record fixture preserves the supplied native structure without user paths.

Usage-limit error/turn.failed events now halt the entire run as resumable
STOP-E1 infrastructure failures, with the original message/reset time on stderr
and no interrupted-task outcome or report. Detection also reads control CLI
stderr's nested control_cli_events, without changing controller/verifier code.
The runner makes no further call after observing the limit. Same-output recovery
resumes the active executor or pending control step and preserves completed days.
Interrupted control streams/partial outputs are archived, hash-pinned, redacted
and referenced by the eventual report; missing accounting remains null.

Regressions cover both native versions, full-record private-marker injections,
malformed settings, conflicting telemetry, the exact supplied usage-limit event
pair, CLI stderr/reset time, no-thread recovery, loop-wide halt, all six
two-session control stages, repeated limits and verifier reinstruction recovery.
Validation: `.venv/bin/python -m pytest tests/eval -q` — 596 passed in 56.24s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks eval/reports/pilot-a eval/reports/pilot-b`
both exited 0. Only synthetic graders/local grading subprocesses were used.

## Assumptions

- b04f9b0 contains the completed two-session work. Claude's uncommitted smoke
  report is retained unchanged and excluded from this commit plan.
- The supplied host smoke was invalid/inconclusive before day 2; mock regression
  success does not establish host compatibility. Claude reruns a fresh smoke.
- Control CLIs retain bounded execution and may perform their existing internal
  retry/fallback before returning. Eval detects their structured limit evidence
  on return; no frozen interface or other-role implementation is changed.
- Reset text is relayed verbatim; no timezone or missing usage is inferred.
  No model calls, private-root lookup, staging or commits occurred here.

# r5-full-001 and r5-full-002 — 2026-10-23

The combined uncommitted change runs frozen two-session tasks as two fresh
sessions in one public workspace. Day 2 receives exact day2.md bytes; harness
contracts arrive separately through developer_instructions. Runner-owned
handoff generation and validation use the frozen CLIs. Both days retain native
and event audits, settings, distinct identities, delivered-prompt hashes and
exit hashes before one trusted grade. Attempts and executor costs sum once.

Evidence publishing uses the runner's hash manifest, excludes workspace files
and refuses symlinks. Preexisting control outputs invalidate the task with
runner_control_file_preexisting; modified pinned files remain control errors.
Only manifest-pinned, numerically named verdicts can feed handoff generation.
Forged verdict-99.json and verdict-final.json cannot replace verdict-1.json.

Hard-crash recovery resumes the active session without repeating completed days.
An audit-clean day-1 timeout/error can continue to day 2. Regrade preserves final
executor timeout/error outcomes, retains invalid pre-day-2 tasks and grades the
remaining eligible tasks without executor calls. Missing handoff observations
invalidate rather than disappearing from quality denominators.

Decision [0006](../docs/decisions/0006-codex-version-policy.md) governs version
provenance. Full A/B and the two-session smoke select codex-cli
0.163.0-alpha.11.1; historical 0.162 pilots are diagnostic planning inputs only.
Every native session must supply matching cli_version evidence. Missing or
mismatched evidence invalidates that task and retains costs while report.json
still records every task. A pre-session version change still halts the run.
The comparison helper refuses mixed codex_version reports. New versions require
a hook probe and one-task audit smoke before a large run; the supplied 0.163
host hook probe passed, while audit smoke/production verification remain pending.

Full configurations select all 120 frozen tasks, seed 0 and pilot retry limits;
two-session processes get 1200 seconds, others 600, grading 20. The published
estimate budgets 140 sessions each, USD 4.0960136/6.0263112 and approximately
56/84 plan percentage points. STOP-3 also budgets controller retries/fallbacks
and judge criteria: one no-retry two-session harness task already bounds 11
paid calls. The failing guard test now clears an obsolete task timeout when it
changes task selection; loader validation is unchanged. No full run is approved.
A bounded per-event audit cache preserves exhaustive detection while avoiding
repeated identical protected-path resolution in large-call events.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 537 passed in
46.12 seconds. `git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks eval/reports/pilot-a eval/reports/pilot-b`
both exited 0.
All calls are mocked except local synthetic grading subprocesses. No network,
model calls, private-root lookup, staging or commits occurred. Host measurements
and five manual pilot-A reviews remain pending.

## Assumptions

- Frozen task content and historical pilot artifacts remain unchanged.
- Pilot session token/cost averages and supplied plan deltas are estimates for
  both days; they are neither new quality evidence nor spending caps.
- Host compatibility of contract delivery, real native capture and production
  recovery remains unverified here. The supplied probe result is host evidence.
- Complete control-call accounting, done-claim denominator and paired parity
  remain unknown; absent accounting is never inferred as zero.

# Evaluation changes — 2026-10-21 offline session

New runner reports validate against the approved shared evaluation report
schema, including formats and runtime ID/count/cost/order/hash checks. The
provisional local schema is a compatibility reference only. Historical baseline
artifacts remain unchanged; legacy checkpoints require an explicit migration.
The eval CLI now prints the supplied output directory as frozen in version 1.

The tool-event access audit invalidates protected Codex-home, sibling-bridge,
repository-outside-workspace and private-grader accesses. Incomplete, missing,
unsupported and unresolved evidence is inconclusive and prevents grading.
Assistant-only path prose is not an access. Raw external streams and hashes
remain available; public review evidence is redacted.

Harness mode calls the frozen contract and verifier CLIs through injectable
bounded subprocesses, injects the validated contract, and resumes only on a
non-null bounded verifier re-instruction. Contract/verdict failures and observed
access stop the task before private grading. Tests mock model/control calls.

Public inventory now contains 100 single-session and 20 two-session unfrozen
drafts; the 119 new candidates need external graders and diversity/specification
review. No hidden task graders or live executor calls were created. The pending
list is `eval/GRADERS-PENDING.md`.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 55 passed, 2 skipped
(external grader configuration absent). Host-only checks remain pending.

## Assumptions

- Version 1 is approved and supersedes the previous STATUS's provisional-schema
  description; shared interfaces were not edited.
- Public draft preparation is authorized without private graders. Related family
  variants need review before the task set can be frozen.
- Unobserved pricing, control-call accounting and full claim denominators remain
  undefined. No quality/cost result follows from mock tests.


## 2026-10-22 host-review remediation

H2: retained grading copies now live outside executor runtimes. All sibling
runtimes, including prior runs, and the retained grading location are audited.
Four mocked cross-task/cross-run tests cover glob and absolute copy reads.
H1: shell parsing tracks directories, resolves concrete globs/quotes, handles
event workdir/cwd, compares paths without case, and rejects unresolved operands.
Recursive ancestor searches are detected. Hashed normalized grader lines detect
tool-output disclosure independently of command construction. Ordinary workspace
commands remain clean. Dynamic unlogged execution still requires host review.
M1: checkpoint results use the same redaction as public result files; audit
matches retain labels instead of raw candidate paths. An integration test scans
every file under --out for both source-root spellings.
Low items: transport retries reset for each reinstruction segment; post-call
report/usage ValueErrors become internal ReportError; unresolved guards have
direct cases; bootstrap tests require seed-sensitive intervals; the shim test
resolves the actual unchanged relative reference from the shim file's URI.

| H1 command case | Before | After |
|---|---|---|
| cd /, root without leading slash | clean | access_detected |
| cd .. twice | clean | access_detected |
| cd ../.. | clean | access_detected |
| glob hiding root suffix | clean | access_detected |
| quoted path splitting | clean | access_detected |
| ~user path | clean | inconclusive |
| find ancestor -exec cat | clean | access_detected |
| grep -rh ancestor | clean | access_detected |
| uppercase home/.CODEX | clean | access_detected |
| cd ~, relative .codex | clean | access_detected |

Evidence: `PYTHONPATH=. .venv/bin/python /tmp/lhm_compare.py` compared the
HEAD audit module with the working module, using synthetic roots only; all ten
before results were clean. Permanent parameterized tests retain every case.
`.venv/bin/python -m pytest tests/eval -q`: 88 passed, 2 skipped, 1 xfailed.

STOP-1 / M2 proposal for Role 1: allow aggregate validity=invalid with an
explicit halt/count reason when the reported task IDs differ from the configured
task set, even if all attempted tasks are valid. Keep audit-clean failures valid
quality samples and preserve their costs. The frozen schema's allOf currently
requires status=valid in this case. No schema field is needed, but revising this
frozen invariant requires user approval, a decision record and schemas/VERSION
increment. No shared or other-role path was changed. The strict xfail reproduces
STOP-E1 after 1 of 2 tasks; M2 is not fixed.

## Assumptions

- Keep grading copies in one retained temporary location instead of deleting
  files under STOP-4; all tasks audit that location and other temporary runtimes.
- A concrete wildcard expansion can establish access; unknown expansion stays
  inconclusive. Named-user tilde expansion is deliberately unresolved.
- Resolve the compatibility shim relative to its actual URI using an offline
  registry; its existing relative $ref needs no shared-schema modification.
- This session supplies no live model, isolation or production measurement.

## 2026-10-22 wrapped-command regression

Unwrapped literal executor shell displays with shlex before examining the
inner command. Quote provenance now belongs to each inner argument, so a
wrapper closing quote or another argument's quotes cannot invalidate a path.
Workspace-bounded globs are resolved even without matches; concrete symlink
matches still undergo protected-path checks. Glob/filter option values are
excluded from filesystem operand analysis. Recursive start paths, including
implicit current directories, remain audited. make variable values retain
their own quote provenance for the observed TEST_PATH corpus case.

The fixture contains 42 distinct non-heredoc commands selected from the
59-entry host corpus. It records source indices and the source SHA-256.
The external design-note path was rewritten as fixtures/notion-design.md;
all referenced paths are synthesized inside a temporary workspace. Commands
are replayed as JSON log records and are never executed. No absolute user,
home or private-root path was copied into the fixture.

| Fixture audit status | Before (5faf49d) | After |
|---|---:|---:|
| clean | 4 | 42 |
| inconclusive | 38 | 0 |
| access_detected | 0 | 0 |

The table below uses the existing prompt-file read for each shell wrapper.

| Wrapper | Before | After |
|---|---|---|
| /bin/zsh -lc single quotes | inconclusive | clean |
| /bin/zsh -lc double quotes | inconclusive | clean |
| /bin/bash -lc single quotes | inconclusive | clean |
| /bin/bash -lc double quotes | inconclusive | clean |
| sh -c single quotes | inconclusive | clean |
| sh -c double quotes | inconclusive | clean |

Per-case results use C=clean, I=inconclusive and D=access_detected.
Wrapped columns use the executor's `/bin/zsh -lc` display. Workspace
files exist for the requested glob examples; unmatched glob cases are
included separately. Therefore some unwrapped glob cases already audit
clean before this patch, while their wrapped forms are inconclusive.

| Ordinary command | Before unwrapped | Before wrapped | After unwrapped | After wrapped |
|---|---|---|---|---|
| `cat prompts/01-tech-lead.md` | C | I | C | C |
| `ls *.py` | C | I | C | C |
| `cat src/*.py` | C | I | C | C |
| `pytest -q tests/test_*.py` | C | I | C | C |
| `find . -name '*.py'` | C | I | C | C |
| `rg -n def -g '*.py' .` | C | I | C | C |
| `rg --files -g '*.py'` | C | I | C | C |
| `rg --glob '*.py' def .` | C | I | C | C |
| `rg --glob='*.py' def .` | C | I | C | C |
| `find . -iname '*.PY'` | I | I | C | C |
| `find . -path './src/*.py'` | C | I | C | C |
| `grep -r --include='*.py' def .` | C | I | C | C |
| `grep -r --include '*.py' def .` | C | I | C | C |
| `ls unmatched*.py` | I | I | C | C |
| `cat src/missing*.py` | I | I | C | C |
| `ls missing*/file` | I | I | C | C |
| `cd src && cat *.py` | C | I | C | C |

| Protected or unresolved case | Before unwrapped | Before wrapped | After unwrapped | After wrapped |
|---|---|---|---|---|
| cd / | D | D | D | D |
| cd .. twice | D | D | D | D |
| cd ../.. | D | D | D | D |
| root-name glob | D | I | D | D |
| quote-split path | D | I | D | D |
| ~user | I | I | I | I |
| find -exec | D | I | D | D |
| grep -rh | D | I | D | D |
| uppercase home/.CODEX | D | D | D | D |
| cd ~ | D | I | D | D |
| absolute private path | D | D | D | D |
| ../ traversal | D | D | D | D |
| cross-task/run absolute retained copy | D | D | D | D |
| cross-task/run retained-copy glob | D | D | D | D |
| external retained glob | D | D | D | D |
| external runtime glob | D | I | D | D |
| decode-and-execute | I | I | I | I |
| internal split path unresolved | I | I | I | I |
| ancestor find | D | I | D | D |
| ancestor rg --files | D | I | D | D |
| ancestor grep -rh PATTERN | D | I | D | D |
| ancestor ls -R | D | I | D | D |
| ancestor du | D | I | D | D |
| ancestor tar -cf archive.tar | D | I | D | D |
| ancestor rsync -a | D | I | D | D |
| ancestor cp -r | D | I | D | D |
| private-line fingerprint | D | D | D | D |

The external retained/runtime glob rows correspond to
`cat ../../lhm-retained-grading/grading-*/test_*.py` and
`cat ../../lhm-eval-*/workspace/solution.py`. Cross-task and cross-run
integration tests also cover absolute and glob reads, both wrapped and
unwrapped, requiring an invalid task, no grading, and aggregate invalidity.

Evidence: `PYTHONPATH=. .venv/bin/python /tmp/lhm_compare_wrappers.py`
compared the 5faf49d audit snapshot with this patch using synthetic roots;
42 fixture results changed from 4 C / 38 I to 42 C / 0 I. Additional
replay checked all three wrappers with both quote styles: I to C in all
six cases. The baseline snapshot was byte-compared with git show 5faf49d.
`.venv/bin/python -m pytest tests/eval -q`: 306 passed, 2 skipped, 1 xfailed.
The M2 strict-xfail function, including its decorator, was AST-compared
with 5faf49d and is unchanged. M2 STOP-1 remains open.

Pending host verification: replay full installed-version event streams
and confirm real executor/resume, process termination, nested guards and
sandbox behavior. No nested Codex, live model/API, network or macOS
sandbox-exec call was made. Dynamic execution retains the documented
caveat; unknown variable expansion and decode-and-execute stay unresolved.

### Assumptions

- The 42 distinct non-heredoc corpus commands provide a representative
  regression fixture; replaying all 59 live captures remains a host check.
- A bounded glob with no matches is resolved for auditing even if the
  actual shell command would fail; audit cleanliness does not imply
  command success.
- Optional HOME expansion was left unchanged; only literal shell
  unwrapping, operand quoting and workspace glob/pattern handling changed.


## 2026-10-22 approved recovery and grader validation

M2 now halts before report construction, exits 2 through the existing CLI, and
prints STOP-E1 with attempted/configured counts on stderr. Checkpoint and run
diagnostics survive; the same output directory resumes and publishes only the
complete configured task set. The strict xfail was replaced with halt/recovery
and CLI stream/exit tests. The earlier schema-change proposal below is superseded
by the approved no-report decision; no shared schema or CLI changed.

The task-set digest reads only `git ls-files` public inputs and private grader
content hashes. Ignored caches and untracked generated files cannot enter it;
tracked edits still change the digest. Missing/symlinked tracked inputs fail
validation. Public workspace files were inspected as text only; every grading
execution used independent copies.

The standalone `python -m eval.runner.validate_graders --private-root
"$PRIVATE_ROOT" --tasks all` validates through the runner's `grade()` function.
References are private overlays, never included in grader sources or executor
workspaces. Output contains task IDs, counts and hashes only. All 120 tasks
failed on untouched copies and passed with references applied: 598 test methods,
155 passed/443 failed on original copies, 598 passed/0 failed on reference copies.
The existing bug-chunk-tail grader passed revalidation unchanged (0/3 original,
3/0 reference). Per-task counts and every grader SHA-256 are published in
`eval/GRADERS-PENDING.md` without locations or test contents.

Public task review retained the 25 related families, 100 single-session tasks
and 20 two-session tasks. It clarified observable submission requirements:
bug fixes require at least one public unittest method; feature and constrained
refactoring variants require at least two; multiple-requirement and two-session
variants require at least three. This makes regression-test delivery explicit,
including for refactoring originals whose behavior already passes. Graders check
both refactoring entry points and input preservation, without prescribing the
helper implementation. Multiple-requirement variants also check the requested
public docstring. Two-session graders check both APIs, batch order, empty batch,
input preservation, exception identity and handoff verification evidence.
Structural helper extraction and regression coverage quality remain human review
items; behavioral validation alone does not certify them. Family correlations
remain relevant to later metric interpretation.

Every changed public task file is enumerated below. For each task, `prompt.md`
adds the submission requirements; `expected.json` replaces pending three-group
metadata with five external groups and their pass condition; `meta.json` records
specification review/external validation while retaining `frozen=false`.
The listed `day2.md` files additionally clarify final regression coverage and
handoff verification evidence. No public workspace source or existing task ID
was changed. Bug-chunk-tail public files are unchanged.

| Task directory under eval/tasks/ | Changed files |
| --- | --- |
| bug-fix-adjacent-runs | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-balanced-brackets | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-clamp-values | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-common-prefix | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-flatten-once | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-inclusive-range | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-interleave | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-interval-union | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-invert-groups | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-last-index | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-line-endings | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-merge-counts | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-pairwise-edges | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-parse-pairs | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-partition-sign | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-prefix-sums | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-rotate-left | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-round-robin | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-select-columns | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-stable-unique | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-strip-prefix | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-unique-permutations | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-window-slices | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-word-counts | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-adjacent-runs | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-balanced-brackets | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-clamp-values | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-common-prefix | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-flatten-once | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-inclusive-range | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-interleave | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-interval-union | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-invert-groups | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-last-index | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-line-endings | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-merge-counts | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-ordinal-labels | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-pairwise-edges | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-parse-pairs | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-partition-sign | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-prefix-sums | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-rotate-left | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-round-robin | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-select-columns | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-stable-unique | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-strip-prefix | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-unique-permutations | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-window-slices | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-word-counts | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-adjacent-runs | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-balanced-brackets | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-clamp-values | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-common-prefix | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-flatten-once | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-inclusive-range | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-interleave | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-interval-union | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-invert-groups | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-last-index | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-line-endings | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-merge-counts | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-ordinal-labels | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-pairwise-edges | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-parse-pairs | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-partition-sign | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-prefix-sums | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-rotate-left | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-round-robin | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-select-columns | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-stable-unique | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-strip-prefix | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-unique-permutations | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-window-slices | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-word-counts | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-adjacent-runs | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-balanced-brackets | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-clamp-values | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-common-prefix | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-flatten-once | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-inclusive-range | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-interleave | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-interval-union | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-invert-groups | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-last-index | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-line-endings | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-merge-counts | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-ordinal-labels | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-pairwise-edges | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-parse-pairs | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-partition-sign | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-prefix-sums | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-rotate-left | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-round-robin | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-select-columns | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-stable-unique | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-strip-prefix | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-unique-permutations | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-window-slices | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-word-counts | `prompt.md`, `expected.json`, `meta.json` |
| two-session-adjacent-runs | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-balanced-brackets | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-clamp-values | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-common-prefix | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-flatten-once | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-inclusive-range | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-interleave | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-interval-union | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-invert-groups | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-last-index | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-line-endings | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-merge-counts | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-pairwise-edges | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-partition-sign | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-prefix-sums | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-rotate-left | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-stable-unique | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-strip-prefix | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-window-slices | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-word-counts | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |

## 2026-10-22 mutation and validation hygiene

Strengthened 23 external graders after reviewing all survivors from a deterministic
1,985-mutant offline pass. Tests remain limited to public prompt/expected behavior;
public tasks, workspaces and expected test-group counts are unchanged. The initial
pass killed 1,891 mutants. Review identified 23 behavioral gaps and 71 equivalent
mutants; equivalence rationales and generated source remain private.

Added `--mutants N` to the standalone grader validator, covering all requested AST
operator families, both application/regression overlays, exact runner grading,
passing reference controls, bounded deadlines, private review records and a 90%
per-task non-equivalent kill threshold. Reference/specification changes invalidate
recorded equivalences. Mutation stdout contains task IDs and counts only.

Validation/mutation runtimes and grading copies now stay under the explicitly
supplied private root and are cleaned on exit. Evaluation retention is unchanged.
Synthetic runner tests use pytest temporary storage. Claude transcript storage is
protected alongside Codex storage, with alias, case-insensitive, symlink, denied
access and recursive ancestor coverage.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 332 passed. All 120 untouched
and reference task pairs validate: originals 155 passed/443 failed, references
598 passed/0 failed. `GRADERS-PENDING.md` changes only 23 rows' grader hashes;
method/group counts remain unchanged. Publication checks found no private path or
task-specific grader line in 550 public evaluation/test/status files. No executor
or model calls were made; no freeze document was written.

Assumptions: the user's earlier sampled rates describe a different, smaller mutant
population. Report them as the supplied before values; the new deterministic pass
covers every generated mutant, including submitted-test overlays. Passing test-only
mutations are equivalent only when the specified application behavior and submitted
test requirements remain satisfied. Behavioral grading still leaves structural
helper extraction and regression quality for human review.

The final mutation command exited 0 for all 120 tasks: 1,914 killed, 71 recorded
equivalent, zero survived/errors. Every task kills 100% of its non-equivalent
mutants (raw aggregate 1,914/1,985). The expanded initial/final candidate populations
are identical; this session's raw count improved from 1,891 to 1,914 killed.

| Task ID | Supplied sampled before | Expanded after, excluding equivalents | Killed / equivalent |
| --- | --- | --- | --- |
| multiple-requirements-clamp-values | 0.55 | 1.00 | 12 / 6 |
| two-session-clamp-values | 0.55 | 1.00 | 13 / 6 |
| bug-fix-clamp-values | 0.67 | 1.00 | 8 / 2 |
| feature-plus-test-clamp-values | 0.71 | 1.00 | 10 / 4 |
| feature-plus-test-ordinal-labels | 0.73 | 1.00 | 24 / 3 |
| multiple-requirements-ordinal-labels | 0.73 | 1.00 | 25 / 3 |
| constrained-refactoring-clamp-values | 0.75 | 1.00 | 12 / 4 |
| constrained-refactoring-ordinal-labels | 0.82 | 1.00 | 26 / 3 |
| bug-fix-last-index | 0.83 | 1.00 | 11 / 0 |
| feature-plus-test-last-index | 0.83 | 1.00 | 12 / 0 |
| multiple-requirements-last-index | 0.83 | 1.00 | 12 / 0 |
| bug-fix-inclusive-range | 0.86 | 1.00 | 14 / 1 |

Reproduction commands (PRIVATE_ROOT is supplied explicitly by the trusted caller):

```sh
.venv/bin/python -m eval.runner.validate_graders --private-root "$PRIVATE_ROOT" --tasks all --mutants 10000 > "$PRIVATE_ROOT/mutation-after-full.jsonl"
.venv/bin/python -m eval.runner.validate_graders --private-root "$PRIVATE_ROOT" --tasks all > "$PRIVATE_ROOT/validation-mutation-final.jsonl"
```

The second command exited 0 with 120 valid/0 invalid and task-set SHA-256
`ea8e9a6df55b22a01fc87a66298262f3cd7e738f8af8ca0853d3f877f5b9f12f`.
Host review and Role 1 freeze recording remain pending. No staging or commit was
attempted; the full repository suite remains a future pre-merge check.

## Version 1 task-set freeze preparation — 2026-10-22

Set `frozen=true` in all 120 `eval/tasks/*/meta.json` files, retaining
`version=1`. A comparison against HEAD verified that only the freeze flag
changed in each metadata file and no other public task file changed. No grader,
reference, inventory hash or task specification was changed. The user authorized
this freeze after Claude's host verification in `80205d3` and `ad7d7be` and
independent mutation testing with no behavior-changing survivor.

The runner now rejects any selected task without an exact boolean true freeze
flag before version probing, private-grader loading, output creation or model
execution. This also applies to checkpoint recovery. No CLI, schema or hook
interface changed. Inventory tests require all 120 tasks to remain at version 1
and frozen; synthetic runner tests cover mixed frozen/unfrozen task sets,
missing flags and non-boolean flags without invoking external processes.

The prior task-set digest predates this metadata change and is not the final
freeze digest. Claude must run `python -m eval.runner.validate_graders` with the
private root on the host, then pass the final digest to Role 1 for
`docs/eval-freeze.md` (SC-2 remains pending that record). The pilot cost estimate,
approval and 10-task A/B pilot remain pending. No executor, controller, judge,
nested Codex or network call was made; no staging or commit was attempted.

Assumptions: the user's report of independent host verification is the basis for
freezing; private validation cannot be repeated in this sandbox. Historical task
review fields remain unchanged under the metadata-only instruction.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 336 passed in 33.41s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` — exit 0.

## 2026-10-22 ten-task pilot preparation

Replaced the offline price placeholder with snapshot
`openai-standard-short-2026-10-22-v1`, using the user's supplied Claude host fetch
of OpenAI pricing. The existing schema-compatible source string records the URL,
Standard tier, 272K context boundary and absence of a provider version/date;
checked_on is 2026-10-22. Sol input/cache/output rates are 2/0.10/10 USD per
million, Luna 0.10/0.01/0.50. Existing per-call accounting feeds totals and metrics
from this snapshot, bills cached and reasoning tokens once, and preserves null
for unknown models/tiers, long context or incomplete usage. Explicit native tier
evidence overrides the documented Standard default assumption.

Added pilot-a/pilot-b configs with ten identical single-session tasks from ten
families, deterministic 3/3/2/2 type quotas, seed 0, pinned CLI, zero retries,
600-second executor deadlines and harness off. Only effort differs (medium/max).
The exact bundled configs with their published estimate pass the existing paid
batch preflight and print the estimate to stderr; other large batches still
fail. This is preparation, not pilot approval. The estimate reports ten calls
per config, $0.178896 for A and illustrative $0.231296 for B at 2x output, plus
cache/output sensitivities. No maximum cost or plan-percent prediction is claimed.

Existing telemetry kept native token_count snapshots but aggregated attempts.
Added per-attempt tokens and timestamped primary used_percent before/after
observations to task results and run-diagnostics, without changing the frozen
report schema. Missing before/after observations remain null; first observed
inside the process is separately labeled, and after means last in-run sample.
Account rounding/concurrency still prevents an exact per-task consumption claim.

The user supplied final freeze commit 7cdaf3b and full-set digest
b78913b04280f6696d419d2afdc96b152675973d82f05199ddef848986285d1f,
now recorded by Role 1 in docs/eval-freeze.md. This supersedes pending-freeze
notes above. No public task, historical report, shared interface or other role's
path changed. Existing selected-task hash semantics are documented in the
estimate; the full frozen population hash is retained separately there.

Assumptions: trust the supplied host price fetch in this offline session;
Standard short context is the CLI baseline absent conflicting evidence; one
historical task is only a planning proxy; max uses more output and 2x/5x are
illustrative; zero retries bounds the initial batch. Claude must run approved
pilots on the host, retain evidence, review five A samples and obtain approval
before full measurement. No executor/controller/judge/model call, private-root
lookup, network call, staging or commit occurred here.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 342 passed in 19.41s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks` — exit 0. The old placeholder-cost assertion
was updated to verify the snapshot's computed executor/accounting/metric value.

## 2026-10-22 native-session pilot audit remediation

The user reports that Claude's host pilot A at d38a5da produced ten invalid,
ungraded tasks, each reporting unsupported `world_state` at native line 7.
The supplied retained session was read only to inspect its record structure.
This session did not rerun, rewrite or grade `eval/reports/pilot-a/`.

The audit now accepts and checks the basic shape of native `world_state` and
`token_usage_record`. Full record text, including nested keys, is scanned for
private markers and canonical aliases. A disclosure explicitly reports that
the private location reached executor context. Unknown top-level/native item
kinds and unresolved operands remain inconclusive.

Native custom calls were already recognized, but their `input` was not parsed
for shell operands, and tools nested in `event_msg.item_completed` were skipped.
The audit now inspects both, decodes literal shell/patch calls in native `exec`
JavaScript without execution, resolves patch/change paths and command arrays,
and fingerprints tool inputs as well as outputs. Unsupported dynamic custom
code stays inconclusive. Assistant prose remains excluded from access checks.

Each task writes a redacted `access-audit.json` with all errors/matches, including
errors after unknown records and errors accompanying detected access. Results
retain the same audit; the shared report references the artifact and gives an
explicit metadata disclosure reason without a schema or CLI change.

Added a synthetic 33-record JSONL fixture preserving the supplied session's
record order, containers and categorical discriminators. Task text, identities,
paths, timestamps and numeric content are synthetic. Regressions cover a clean
fixture; private paths in both metadata kinds, custom arguments and outputs;
keys/encodings/traversal/symlink/grading-copy aliases; argument/output fingerprints;
shell, patch and file-change operands; malformed metadata; unknown kinds; and
complete persisted diagnostics preventing grading.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 385 passed in 23.65s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks` — exit 0. No model/executor/controller/judge
call, network call, private-root lookup, staging or commit occurred.

Assumptions: the supplied host session is structural evidence for the pinned
CLI only; arbitrary new formats remain unsupported. Usage metadata acceptance
does not change token accounting. Claude will rerun pilot A on the host and
decide how to retain the old report; a passing offline suite is not a measured
pilot result. The user reports the previous plan cost as about one percentage
point of the weekly window; no new plan consumption was measured here.

## 2026-10-22 fingerprint false-positive remediation and offline re-audit

The user reports Claude's host verification of the native-record fix (385 tests
passed), followed by a false-positive pilot A re-audit: an executor-authored
`file_change` matched shared grader boilerplate. This supersedes the preceding
section's argument-fingerprint behavior. Fingerprints now inspect only command
`aggregated_output` and function/custom tool outputs. Path and operand checks
continue inspecting inputs, patches, file changes and native metadata.

Hidden line selection now requires a number/string literal absent from all
public task prompts, day-2 prompts, expected/meta JSON and workspace files. It
also excludes publicly present normalized lines, docstrings, module entry guards
and unittest launchers. Decoded string/numeric equivalents and conservative
substring checks exclude shared examples. The existing 16-character normalized
minimum remains. Fingerprints still cover graders across the private root, but
only hashes and labels enter audit artifacts.

Added `python -m eval.runner.reaudit --private-root PATH --out EXISTING_RUN_DIR`.
This read-only diagnostic uses finished checkpoint runtimes, every retained
executor/native log, the task's own PrivateGraders and the runner's workspace,
repository and grading/cross-runtime settings. It checks retained log and grader
manifests, keeps access matches when evidence errors coexist, and prints only
task IDs, statuses, error kinds and match labels. It makes no executor/control
call and never rewrites reports, checkpoints or audit artifacts.

Synthetic regressions cover honest unittest submissions and pytest output with
shared examples/boilerplate, every public-file category and cross-task examples,
equivalent literal spellings, authored arguments/patches/file changes/metadata,
and hidden-line reads via cat/sed/grep/Python output with no private path.
Re-audit cases cover real audit roots, multiple tasks, sanitation, missing/changed
retained evidence, incomplete runs and byte-for-byte artifact immutability.

Assumptions: `--out` names the finished source run, not a destination; Claude has
the matching private root and original external runtimes on the host. Public
files stay frozen. This offline change adds no pilot quality result; Claude must
re-audit pilot A on the host before rerunning it. No model call, private-root
lookup, pilot artifact change, staging or commit occurred here.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 425 passed in 33.24s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks` — exit 0. The full repository suite is
deferred to a future merge; only the owned eval tests ran here.

## 2026-10-22 shell and file-change operand separation

The user reports Claude committed the fingerprint fix as `d73b41f` and re-audited
pilot A on the host: 9/10 tasks clean, versus 10/10 inconclusive before the fixes.
Read the two indicated records in the authorized retained interval-union runtime.
Line 23 combines a literal apply_patch with a literal unittest command; line 25
is a FileChange map. Their authored assertion contains `$`, which triggered a
whole-record unresolved-operand check.

Shell expansion/quoting rules now apply to decoded shell commands and their
directories only. Every supported literal `tools.exec_command` call is checked,
including its workdir. JavaScript glue is not a shell command. Concatenated or
otherwise dynamic commands/directories and unknown tools stay inconclusive.
The literal decoder skips quoted patch contents that resemble nested tool calls.
FileChange and apply_patch inputs supply only target/move paths to access checks;
content/diff text cannot trigger shell errors, path matches or fingerprints.
Canonical protected paths, symlinks and traversal checks remain in force.

Added 29 synthetic cases using the real line-23/25 envelopes: unittest is clean,
protected reads and later commands are detected, dynamic/unknown calls are
inconclusive, and authored `$`, backticks, quotes and private-looking strings
stay clean at workspace targets. Native/list FileChanges and literal custom,
code-mode and function-call patches cover protected targets, symlinks and moves.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 454 passed in 47.54s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks` — exit 0.

## Assumptions

- The user's 9/10 result and commit identity are supplied host evidence. No real
  private graders are available here, and no host acceptance result is claimed.
- Claude will rerun the read-only re-audit with the matching private graders;
  the target is 10/10 clean unless actual protected access is detected. Reports,
  frozen tasks and CLI/schema interfaces remain unchanged. No model call,
  private-root lookup, staging or commit occurred in this session.

## 2026-10-22 bounded grader corpus and payload processing

Claude's supplied host check passed 454 eval tests, but re-audit exceeded nine
minutes with a stack inside ast.walk. The user reports 14,669 test files under
the private root, only 120 immediate task graders and 847 unique contents;
recursive enumeration included validation/mutation/reference storage.

Fingerprint inputs now come only from `ROOT/<non-dot-task>/test_*.py`, without
following symlink directories/files. Dot storage, root-level tests and deeper
descendants never feed fingerprints. PrivateGraders.load also requires an
immediate non-dot task directory. Whole-root path protection remains in force,
including every dot-directory and its copies.

SHA-256 content deduplication precedes AST parsing. One invocation-scoped cache
shares the public-corpus/distinctive-line/fingerprint analysis across all tasks,
streams and retries in both the runner and read-only re-audit. It is discarded
between invocations; task-specific manifest hashes still read current files.
AST nodes are collected once per unique grader, and literal source extraction
uses precomputed byte offsets instead of repeatedly splitting the entire file.

The code-mode decoder now matches at source offsets and builds its remainder in
one pass rather than copying the remaining source for each call. A boundary on
the generic path regex prevents quadratic retries across long slash-free words.
The previous command-only shell and path-only FileChange/patch fix is retained.

Nine new regressions cover 120 task graders plus 5,000 quarantined duplicate
copies, exact fingerprint equality, no dot-file reads, one parse per unique
content, cache lifetime and rejected non-task paths. Large-payload cases cover
200 KB patches, commands and malformed literals, 3,000 sequential tool calls,
and a 1 MB FileChange. Corpus analysis across 120 tasks and each large-payload
audit must finish within five seconds. Runner and multi-task re-audit tests
also assert one corpus computation per invocation and fresh analysis next time.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 463 passed in 34.19s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks eval/reports/pilot-a` — exit 0. Frozen public
tasks and pilot artifacts are unchanged; no model call, private-root lookup,
staging or commit occurred.

## Assumptions

- Public inputs and immediate task graders are immutable within one invocation;
  the cache is in memory only and is never reused by a later invocation.
- The host counts, hang and 454-test result are user-supplied evidence. Claude
  must rerun with the matching private root; acceptance remains under one minute
  with 10/10 tasks clean unless a task actually accessed a protected path. These
  synthetic checks do not establish that host result or pilot quality.

## 2026-10-22 pilot-B shapes and offline regrading

Replaced code-mode whole-source allowlisting with lexical direct-call extraction.
Promise combinators, arrays, loops and display spreads no longer make literal
shell calls unresolved. Dynamic command/workdir operands, aliases, computed tool
access, unknown tools and eval/Function remain inconclusive. Synthetic regressions
cover the supplied parallel-call shape, the exact nested-quoting rg wrapper,
list-form exec file changes, protected targets and macOS temporary-path aliases.
Path comparisons and private-root redaction now cover both `/var` spellings.
Earlier protected-access regressions remain in the eval suite.

The runner records workspace content manifests at executor exit and saves the
configuration in its checkpoint. Added `python -m eval.runner.regrade
--private-root PATH --from DIR --out NEWDIR`: all-task re-audit and fresh-copy
`grade()` execution with unchanged executor accounting, regenerated metrics and
a schema-valid report. It refuses historical missing hashes and mismatches;
source reports/runtimes remain read-only. Separate diagnostics retain source
report and audit-code hashes plus every workspace check. No report schema,
frozen task, pilot artifact or shared interface was edited.

Tests use synthetic graders, mocked executors and local grading subprocesses.
They cover hash refusal before output, source/runtime immutability, fresh copies,
all-task recovery from historical inconclusive audits, parity with current runner
fixture outcomes, and CLI success/refusal output. Host pilot acceptance and the
new pilot-B executor run remain Claude's work.

### Assumptions

- The supplied host results at `96583d3` are historical user evidence: A has
  10/10 valid/clean, pass rate 1.0 and cost per pass USD 0.029; B has 9/10 invalid
  with unresolved_custom_input/unresolved_operand errors. This session did not
  reproduce these measurements or access real private graders.
- Retained checkpoint/report evidence is trusted runner output. Regrading
  requires matching public/private task inputs and exact retained workspaces;
  it cannot establish exit-time integrity for an older run without hashes.

## 2026-10-23 — C preparation, paired comparison and accounting review

Prepared the seed-0 metadata-only twenty-task C subset, twenty unfilled human
skeletons, fill-once rules, standalone config and planning estimate. Added static
template preflight, exact harness-wrapper injection, report artifact hashes and
checkpoint drift refusal. Optional full task populations let B/C reports verify
the same frozen digest as full A while checkpointing selected inputs separately.

Added `python -m eval.runner.compare LEFT RIGHT --out DIR`: schema/provenance
checks, matched valid tasks, diagnostic invalid handling, overall/per-type
metrics, paired 10,000-resample intervals, hash-pinned source reports and JSON /
Markdown output. Existing run CLI flags and shared schemas are unchanged.

Control markers now match only at line start. Zero-delegation accounting permits
all-judge quality-warning contracts and pinned budget-skipped judge items;
other missing judge evidence remains unknown. Standalone runs no longer warn
about an absent control model. Harness estimates now use 15,000 input and 1,000
output tokens per Luna generation ($0.002), based on supplied host observations.

No public task, retained measurement, private grader, other checkout or git index
was modified. Verification and remaining host work are recorded in STATUS-eval.

Verification: `.venv/bin/python -m pytest tests/eval -q` — 649 passed in
60.49s. Frozen task and pilot-report diffs are empty; no full repository suite
was run in this session.

# Calibration, observed-tier pricing and interface v2 metrics — 2026-10-23

Add boolean calibration (default false) for the decision 0008 pre-freeze pilot.
Calibration checkpoints, run diagnostics and pinned report artifacts identify
nonheadline evidence, stderr explains that status, and compare refuses it.
The baseline-A pilot and estimate enable calibration before its later freeze.

Preserve the original Standard snapshot, add the user-supplied 2026-10-23 Fast
snapshot at 2× Standard and a separate Standard Sol 6 supplement. Capture newly
emitted native applied tiers at each process exit; control calls require a tier
on their control_call line. Unknown tiers remain null. Per-call artifacts and
schema-compatible metadata pin tier/rate/source provenance. Recovery preserves
historical accounting. README records Luna's priority CLI default and the
retained v1 control-cost underpricing for disclosure in the final evaluation.

Give all four multiple_requirements variants materially different family
specifications and independent private graders/references/coverage. Archive the
previous candidate privately. Revalidate all twenty starter/reference pairs and
the changed references' complete mutation populations. The counts-only report
records 249 reference checks, 136 starter failures, 252/252 covered requirements,
1121 killed mutants, 18 reviewed equivalents and zero unreviewed survivors;
20 starter public suites and 20 reference verification commands pass.

Implement task_false_done_rate using the retained final message of the last
required session, a task-scope adapter applying verifier.claims.claimed_criteria,
valid-task populations and seeded task-cluster bootstrap. Pin final/segment and
extractor hashes, evidence, numerator/denominator and exclusions through existing
artifacts. Preserve criterion-level false_done_rate. Missing final messages are
excluded with reasons; missing hidden grading never establishes false done.
Version-aware schema validation supports retained v1 reports in regrade,
continuation, rerun, re-audit and compare; task-level comparison requires v2 on
both sides. No retained v1 report, schema or existing CLI flag is changed.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 1126 passed in
113.59s. All nine retained shared-schema reports validate by declared version;
the provisional report remains unchanged. `git diff --check -- eval tests/eval
state/STATUS-eval.md` and `git diff --exit-code -- eval/tasks schemas` pass.
The four prior bug-fix references fail 22 checks against the revised variants.

## Assumptions

- Pricing is the user's supplied official-page observation; network verification
  and live executor/controller/judge calls are unavailable in this session.
- The existing verifier exposes criterion extraction only. The eval-owned adapter
  binds task-scoped completion prose to one synthetic ID, uses the same clause
  rules and excludes criterion-only/test-only statements; no verifier edit occurs.
- The new candidate remains unfrozen. Paid calibration, later freeze and the
  full repository check before merge remain host work.
