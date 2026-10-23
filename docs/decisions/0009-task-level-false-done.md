# 0009: Task-level false done across all configurations

Date: 2026-10-23

Status: definition-only proposal; blocked by STOP-1 / STOP-L1 pending user approval of a report-schema revision. No interface change or implementation is authorized by this record.

## Problem

The approved `false_done_rate` counts criterion items marked
`claimed_without_evidence` divided by claimed criterion items from valid tasks.
It requires a verifier, so baselines A, B and C cannot supply that measurement.
It therefore cannot support the project's central comparison across all
configurations. An unavailable criterion-level rate must not be reported as zero.

## Proposed definition

Add `task_false_done_rate` alongside the existing criterion-level
`false_done_rate`, never replacing or renaming it. Apply the same extraction and
classification rules to A, B, C and every harness configuration, using retained
evidence alone and no new executor or judge calls.

A task is **claimed complete** when the executor's final message of its last
session claims that the task is finished under the claim extractor's rules.
Earlier sessions, intermediate completion statements, tool output and controller
or verifier messages cannot substitute for that final message. For a two-session
task, use the last session. Retain the selected message's source segment/hash and
claim evidence so the classification is reproducible. Do not substitute a count
of criterion-ID claims for this task-level decision: baseline messages need not
contain criterion IDs. The task-level extractor rules and version must be fixed
and applied identically across configurations before comparison; their
implementation and validation remain pending.

A claimed-complete task is **false done** when it fails hidden grading or ends
invalid for an executor-caused reason supported by retained evidence. Keep the
reason and evidence for executor attribution. Infrastructure failures, missing
logs and inconclusive audits alone do not establish executor fault or hidden
grading failure. Missing final-message evidence is an unknown observation, not
an inferred absence of a claim. Do not rerun hidden grading on invalid tasks or
override the existing prohibition on grading invalid tasks.

The requested formula is:

`task_false_done_rate = false done tasks / claimed-complete valid tasks`

This formula has an unresolved population conflict: its numerator includes
executor-caused invalid tasks while its denominator excludes invalid tasks.
It can exceed one, or have a zero denominator despite observed false-done
tasks. Decision 0003 also excludes invalid tasks from quality samples and marks
any report containing an invalid task invalid. These rules are not silently
changed here. User approval must resolve the population treatment before
implementation; this definition is not yet an executable rate specification.
Executor-caused invalidity must remain visible in retained evidence, and an
invalid aggregate must not become a valid headline comparison.

Use the seeded 95% task-cluster percentile bootstrap, retaining each task's
sessions, final claim and outcome together and recomputing the ratio in each
replicate. Follow decision 0003's default 10,000/minimum 1,000 resamples and
2.5th/97.5th percentiles. A zero original or bootstrap denominator yields null
value/bounds and a specific undefined reason; never discard such replicates.
Missing evidence needed for classification also requires an explicit undefined
reason. Publish the numerator, denominator and unresolved/invalid cases for
audit; do not turn unknown observations into passing tasks. Final sample-unit
and invalid-population rules require approval with the schema revision.

## Schema finding and implementation ownership

`schemas/evaluation-report.schema.json`, at `/properties/metrics`, is an object
of named entries, but it is **not extensible**: `additionalProperties` is false
and `properties` permits exactly `pass_rate`, `false_done_rate`, `cost_per_pass`,
`avg_attempts`, `handoff_success` and `parity`. Consequently a new
`task_false_done_rate` name is rejected. `$defs/metric/properties/sample_unit`
also has a closed enum with no explicit claimed-complete-task unit.

**A schema change requires the user's approval, a decision record and an
increment of `schemas/VERSION`. Stop at this definition.** Do not overload an
existing metric name, change its unit, or write an extra entry into version 1.
No schema/example, CLI, hook or runtime file is changed by this proposal.

After approval and interface publication, Role 5 owns implementation in
`eval/metrics.py`, evidence extraction/integration and its tests. Role 1 owns
the approved schema/example and shared-documentation changes; Role 4 should
review consistency with criterion claim semantics without changing that metric.
Affected roles are Role 1 (report contract), Role 5 (producer/consumer/tests)
and Role 4 (claim semantics review). This session does not edit or inspect the
running evaluation's reports and claims no measured task-level result.

## Assumptions

- The request authorizes the additional metric's definition, not a frozen-schema
  revision; it explicitly requires stopping if that revision is necessary.
- Executor attribution and task-level claim extraction need reproducible rules
  before retrospective measurements can be compared. Existing criterion claim
  counts alone do not establish task completion claims for all baselines.
- The numerator/denominator conflict is reported for approval rather than
  resolved by guessing a different population or silently changing decision 0003.
