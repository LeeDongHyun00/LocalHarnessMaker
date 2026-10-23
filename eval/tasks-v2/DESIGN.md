# Task set version 2 design

Written before pilot task construction, 2026-10-23. Version 1 remains frozen.
The user approved the separate version under decision 0008, being recorded by
Role 1. This pilot has 4 families and 20 tasks; all metadata stays frozen=false
until design calibration and a separate freeze. No baseline outcome was used to
select these tasks.

The design targets incomplete requirement coverage, broken constraints, claims
without verification, and context lost between sessions. Every task contains a
small Python package with 3–8 production modules and public unittest regressions.
Each task has 12 numbered requirements (15 across two sessions), including interacting validation,
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
| Planned expansion | dependency graph, layered settings, event replay, access policy, job queues, calendar windows, CSV import, text indexing, schema migration, filesystem manifests, rate budgets, workflow state, search facets, document patches, command dispatch, cache invalidation |

Each family uses one domain package but distinct starting defects and requested
changes across the five types. Related tasks are marked with family metadata;
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

Run baseline A first on the complete 20-task pilot with full A's model/effort.
Target roughly 30–70% pass rate. This session makes no live calls. If the pilot
misses that range, adjust difficulty at the design level (for example the number
of interacting call sites, atomicity scope or cross-session policy dependence)
across whole families/types. Rebuild and validate the resulting population as a
new candidate; retain all prior candidate identities and results. Never select,
drop or rewrite individual tasks based on their pilot outcome. Freeze only after
calibration; compare only reports with the same task-set digest. V1 results are
context, not a matched v2 quality comparison.
