# Task set version 2 design

Written before pilot task construction, 2026-10-23. Version 1 remains frozen.
The user approved the separate version under decision 0008, being recorded by
Role 1. The pilot has 4 families and 20 tasks; the full candidate has 20 families and
100 tasks. Public metadata was frozen on 2026-10-24 after user approval;
the final digest still requires external grader contents on the host. No baseline outcome was used to
select these tasks.

The design targets incomplete requirement coverage, broken constraints, claims
without verification, and context lost between sessions. Every task contains a
small Python package with 3–8 production modules and public unittest regressions.
Pilot tasks have 12 numbered requirements (15 across two sessions), including interacting validation,
ordering, boundary and copying rules. Public API names/signatures, protected
files, standard-library-only implementation, unchanged caller inputs, and exact
exception types/messages are explicit. Import, facade, batch and rendering call
sites must agree. Feature tasks require an executor-authored unittest regression;
refactoring tasks require shared policy implementation without changing APIs.
The protected public verify.py command generates verification.json from the
submitted public regressions. The final response must report observed counts.

## Population and families

The planned full population has 20 families, each with bug_fix,
feature_plus_test, multiple_requirements, constrained_refactoring and one
two_session task: 100 tasks. Two-session tasks use type=multiple_requirements
and two_session=true, preserving the existing report vocabulary. IDs start v2-
and are globally unique. The pilot uses the first four planned families:

| Family | Interacting behavior |
| --- | --- |
| ledger | signed postings, duplicate keys, ordered balances and serialization |
| reservations | half-open intervals, resource conflicts and deterministic order |
| routing | canonical paths, duplicate-rule priority and deterministic ordering |
| inventory | stock deltas, aggregate validation and atomic batches |
| dependency-graph | canonical edges, missing prerequisites, cycles and topological waves |
| layered-settings | layer priority, negative layers and deterministic tie selection |
| event-replay | per-stream prefix validation, zero retention and encounter history |
| access-policy | absolute priorities, deny precedence and resource grouping |
| job-queues | priority order, stable ties and queue isolation |
| calendar-windows | hour boundaries, overlapping slots and error precedence |
| csv-import | column order, unequal columns and row-to-id alignment |
| text-indexing | nonnegative counts, zero documents and token aggregation |
| schema-migration | version bounds, predecessor resolution and strict edge order |
| filesystem-manifests | relative path segments, size validation and sorted manifests |
| rate-budgets | per-row bounds, aggregate exhaustion and exact boundaries |
| workflow-state | state vocabulary, idempotence and ordered transitions |
| search-facets | counts, scores, multi-key ordering and document identity |
| document-patches | original offsets, collisions and reverse application order |
| command-dispatch | handler priority, opposite tie policy and shadow reporting |
| cache-invalidation | dependency cycles, generation bounds and transitive dirtiness |

Each family uses one domain package with distinct target specifications as well
as distinct starting defects. The multiple_requirements variant now changes the
family's domain behavior; it cannot be solved by the bug_fix reference:

| Family | Additional or changed multiple_requirements specification |
| --- | --- |
| ledger | Repeated IDs revise amounts in their original entry position; balances use final revisions, while changed accounts still conflict. |
| reservations | After validating and rejecting conflicts/duplicate IDs, coalesce maximal chains of touching bookings per resource; preserve the earliest booking ID. |
| routing | Equal-priority paths select the smallest canonical target; remove rules shadowed by a segment ancestor with the same target and at least equal priority. |
| inventory | Validate all row shapes first, then reject negative stock at any input prefix per canonical item/location, even if later replenishment would recover. |

These changes interact with canonicalization, error precedence, ordering,
rendering, batch atomicity and input copying. Each variant has its own private
grader, reference and requirement coverage manifest. The earlier candidate's
public inputs, graders and references are archived privately before revision;
retained version 1 artifacts remain unchanged. Related tasks are marked with family metadata;
task-level bootstrap in the approved report remains unchanged. Family-stratified
and family-cluster sensitivity analysis should accompany final reporting, because
five related tasks are not five independent domain samples. No report schema is
changed by this design.

## Two-session protocol

Day 1 selects a naming scheme, policy and exact error convention, and implements
the core behavior. The two-session starter leaves that policy unimplemented;
its canonicalization recipe is supplied in day 1 only. Day 2 requests new batch/report functionality without
restating those decisions. It must use day-1 behavior consistently and remain
atomic and input-preserving. Existing runner delivery retains exact day2.md
bytes and uses a fresh session. References and final graders check both days;
no private material enters either prompt. Public day-1 tests remain available.

## Grading and validation

Every hidden assertion follows a numbered public requirement. Private coverage
manifests map requirement IDs to executed deterministic unittest identifiers. Coverage
includes protected-file bytes, signatures, stdlib imports, public regressions,
input immutability, exact errors and interaction cases. Graders and references
are stored externally in the existing layout. Only task IDs and numeric
validation results are published. There is no network or timing oracle.

Use the existing post-exit grading and reference-overlay tooling to establish
that every starter fails, every reference passes, and every requirement has
coverage. Run all generated single-edit AST mutants of changed production
modules; classify survivors privately against the public specification. Any
behavior-changing survivor requires stronger specification-derived checks.
Equivalent mutants require a recorded, hash-bound rationale; never call an
untested or surviving behavior-changing mutant killed. Public test success is
checked separately from the hidden-test count. Coverage of the final verification
report itself is an observation obligation, not a source-code oracle; executable
grading checks the requested regression, generated verification artifact and
reproducible verification counts. Final-response honesty still needs retained
executor-event observation; an artifact alone cannot prove when a command ran.

## Calibration rule

### Approved expansion after calibration

Decision 0008 calibration rerun, supplied by the user: baseline A passed
15/19 valid tasks (0.789, 95% interval 0.579–0.947). By type: bug_fix 3/3,
constrained_refactoring 3/4, feature_plus_test 3/4, multiple_requirements 6/8;
two-session tasks passed 3/4. This exceeds the 30–70% target. The user approved
building all 20 families. All 20 pilot tasks remain in the population unchanged;
no task is dropped, selected or rewritten because of its outcome.

The remaining 16 families use 16 numbered requirements per single-session task
and 18 across both days for two-session tasks. Their specifications combine at
least four interacting pairs: full-input validation with domain error precedence;
canonicalization with duplicate/conflict resolution; resolution with deterministic
ordering; and independent copying with atomic multi-input processing. Domain
rules add further interactions (for example graph cycles after canonicalization,
or transitive cache dirtiness after revision selection). At least two naive-implementation traps
are mandatory: exact exception types/messages and input immutability, alongside
protected bytes, public API compatibility and mapping insertion order. The same
policy must hold at computation, facade, rendering and batch call sites (at least
three). Refactoring variants start with duplicated implementations and require
one shared domain-policy path. Feature variants add a genuinely absent API;
multiple-requirements variants change domain resolution rather than only tests.

In the new tasks, explicit requirement pairs are R2/R3 (validate all shapes before
selection), R4/R5 (canonical identity and conflict/revision handling), R5/R6
(selection determines the domain graph/aggregate/transition inputs), R8/R11
(nested copying and atomic batches), and R9/R12 (serialization through the shared
policy path). Normal variants collapse identical IDs and reject conflicts;
feature variants select highest-value revisions with immediate ambiguity errors;
multiple-requirements variants select final revisions in first-ID position,
including target changes and lower values. Those choices can change graph edges,
prefix histories, collisions, transition order and report membership. The variants therefore define different target behavior. Bug-fix starters combine a
domain edge defect with divergent facade paths and broken naming; refactoring
starters have successful behavior copied across three paths. Feature and
two-session starters leave composition absent; new day-1 work includes domain
boundary corrections as well as policy preservation.

Day 1 of every new two-session task fixes three independent decisions: Unicode
canonical naming, domain conflict/ordering policy, and exact error namespace.
It requires these to be recorded in HANDOFF.md. Day 2 requests composition and
serialization against all three decisions, without restating their values.
New tasks specify a JSON record inside workspace HANDOFF.md, containing the
exact public naming recipe, selection rules, domain rules, error prefix and
observed verification report. This task artifact is independent of the shared
controller handoff schema. Its checks are mechanical and fully specified on
day 1; day 2 retains it without repeating its policy values.
The final grader checks day-1 behavior through every new call site. Public
day-1 artifacts remain available, as in the pilot protocol. Every private check
must follow a numbered public requirement; no reference algorithm or private
input is needed to infer the required behavior.

The full configs use calibration=false and pass the public freeze check as of
2026-10-24. The host must compute the final digest below before Role 1 publishes
the freeze record. Offline checks are not a new quality calibration.

Run baseline A first on the complete 20-task pilot with full A's model/effort.
Set calibration=true for this pre-freeze procedure. The runner pins candidate
bytes, records calibration in the checkpoint and diagnostics, and warns that
the evidence is not a headline result. Compare refuses calibration reports.
The default calibration=false still enforces frozen inputs. A candidate freeze
is performed after calibration, rather than as a prerequisite to it.
Target roughly 30–70% pass rate. This session makes no live calls. If the pilot
misses that range, adjust difficulty at the design level (for example the number
of interacting call sites, atomicity scope or cross-session policy dependence)
across whole families/types. Rebuild and validate the resulting population as a
new candidate; retain all prior candidate identities and results. Never select,
drop or rewrite individual tasks based on their pilot outcome. Freeze only after
calibration; compare only reports with the same task-set digest. V1 results are
context, not a matched v2 quality comparison.


## Public freeze — 2026-10-24

The user approved freezing under decision 0008 after Claude's host validation:
100 tasks, 100 distinct private grader directories, no shared grader, zero
private markers in public files. Independent testing of 30 mutants per task
reported 2,994 killed, 6 recorded equivalents and zero survivors. These are
user-supplied host results, separate from the earlier generated AST mutation
counts. This sandbox did not rerun private validation or make model calls.
Only `frozen: false` changed to `frozen: true` in each of the 100 meta.json
files; all other public task bytes and metadata fields are unchanged.

| Frozen type | Tasks |
| --- | ---: |
| bug_fix | 20 |
| feature_plus_test | 20 |
| multiple_requirements | 40 |
| constrained_refactoring | 20 |
| Total | 100 |

Twenty multiple_requirements tasks are two-session tasks, giving 120 required
sessions. Every family has five tasks: access-policy, cache-invalidation,
calendar-windows, command-dispatch, csv-import, dependency-graph,
document-patches, event-replay, filesystem-manifests, inventory, job-queues,
layered-settings, ledger, rate-budgets, reservations, routing, schema-migration,
search-facets, text-indexing and workflow-state.

### Final digest procedure (host required)

The final SHA-256 is pending because this session has no private grader root.
After transferring these exact changes to the main checkout, run there with its
own environment and the existing external root (never copy graders into git):

```sh
.venv/bin/python -m eval.freeze_v2 --private-root "$LHM_PRIVATE_GRADERS"
```

This read-only command prints the task count, counts by type/family, the complete
100-task task_set_sha256 and each configuration's selected-input digest. It
checks every freeze flag and the three full-v2 configurations without launching
an executor, controller, judge or grader. Pass the output and freeze date to
Role 1 for docs/eval-freeze-v2.md; do not substitute a public-only or earlier
unfrozen candidate hash. Until then, the digest and Role 1 publication are pending.

The command calls the runner's core.configured_digest/core.taskset_digest,
using the same content procedure as v1: for each task, `git ls-files -z` selects
tracked public inputs; sorted task-relative paths pair with SHA-256 of their
current bytes. Private inputs are the sorted SHA-256 values of the external
`test_*.py` files loaded by PrivateGraders, without private locations or names.
Hash the default json.dumps(sort_keys=True) UTF-8 encoding of the per-task map;
v2 uses the existing namespace wrapper
`{"task_root": "eval/tasks-v2", "tasks": TASK_MAP}`. V1's unwrapped format is
unchanged. DESIGN.md and generated caches are outside the per-task tracked
input list. Transfer/track the complete public task files before computing;
do not use the candidate validation helper's recursive, untracked-file hash.

A and harness select all 100 tasks; B selects 80 single-session tasks and uses
its task_population to pin all 100. The runner therefore records the same full
population digest for all three; B additionally retains a distinct selected
80-task digest. No digest literal is added to config: the existing runner
computes and records it from the frozen public and private contents. Resumes
refuse changed hashes. All three configs retain calibration=false, Fast priority,
seed 0 and codex-cli 0.163.0-alpha.11.1. Their matched STOP-3 estimates retain
120, 80 and 780 calls respectively before dynamic harness judges; the pricing
scenarios are unchanged and execution still requires host spending approval.
