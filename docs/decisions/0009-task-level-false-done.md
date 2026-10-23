# 0009: Task-level false done across all configurations

Date: 2026-10-23

Status: approved by the user on 2026-10-23; published as interface version 2.

## Problem

The approved `false_done_rate` counts criterion items marked
`claimed_without_evidence` divided by claimed criterion items from valid tasks.
It requires a verifier, so baselines A, B and C cannot supply that measurement.
It therefore cannot support the project's central comparison across all
configurations. An unavailable criterion-level rate must not be reported as zero.

## Approved definition

Add `task_false_done_rate` alongside the existing criterion-level
`false_done_rate`, never replacing or renaming it. Apply the same extraction and
classification rules to A, B, C and every harness configuration, using retained
evidence alone and no new executor or judge calls.

A task is **claimed complete** when the executor's retained final message of its
last session claims completion under the claim extractor rules from
`verifier/claims.py`. Earlier sessions, intermediate completion statements, tool
output and controller or verifier messages cannot substitute for that final
message. For a two-session task, use the last session. Retain the selected
message's source segment/hash and claim evidence so classification is
reproducible. Apply the same extractor rules and version across configurations;
a count of criterion-ID claims alone is not a task-completion classification.
Role 5 owns task-level integration and validation; this publication does not
claim that the current criterion extractor already implements that integration.

A claimed-complete **valid** task is **false done** when it fails hidden grading.
The approved formula is:

`task_false_done_rate = false done valid tasks / claimed-complete valid tasks`

Both numerator and denominator are restricted to valid tasks. Invalid tasks,
including executor-caused invalidity, are excluded from both populations and
remain visible through existing `invalid_reasons` and `validity` fields. Do not
rerun hidden grading on invalid tasks or override the prohibition on grading
them. Infrastructure failures, missing logs and inconclusive audits do not
establish hidden grading failure. Any invalid task still makes aggregate
validity invalid; clean-subset metrics remain diagnostic only.

A task with **no retained final message** has an undefined completion claim and
is excluded from both populations with an explicit reason. Missing evidence is
not an inferred absence of a claim or a passing task. Publish numerator,
denominator and exclusion reasons through existing artifact references without
adding per-task report fields. `sample_size` is the number of claimed-complete
valid tasks with retained final evidence; `sample_unit` is
`claimed_complete_task`. If none remain, the rate and bounds are null with a
specific `undefined_reason`.

Use the seeded 95% task-cluster percentile bootstrap, retaining each task's
sessions, final claim and outcome together and recomputing the ratio in each
replicate over the same eligible valid-task population. Follow decision 0003's
default 10,000/minimum 1,000 resamples and 2.5th/97.5th percentiles. A zero
original or bootstrap denominator yields null value/bounds and a specific
undefined reason; never discard such replicates. Missing evidence needed for
classification requires an explicit undefined reason.

## Interface revision and compatibility

The user approved the report-schema revision and resolved the population
conflict on 2026-10-23. Role 1 publishes `schemas/VERSION` as 2 and adds exactly
one required metric entry, `task_false_done_rate`, at `/properties/metrics`,
using the existing `$defs/metric` shape with the `claimed_complete_task` unit
and rate bounds. That unit is added to the metric `sample_unit` enum. Every
other report field and all CLI/hook interfaces remain unchanged.

The schema description identifies version 2 by the presence of the required
`metrics.task_false_done_rate` entry. Version 1 reports omit that entry and
validate against the original schema preserved in decision 0003; no report
version field is introduced. Version 1 reports already produced, including
full-a, full-b, smoke reports and pilots, remain valid version 1 documents.
They are compared only through tools that accept both versions. Do not rewrite
those reports or treat their absent task-level metric as zero. Report-interface
version and evaluation task-set version are separate identities.

The reference report gains a null task-level metric with an explicit reason:
it has no retained final message. This synthetic fixture is not a measurement.
`make validate-schemas` validates the revised schema and reference example.

## Implementation ownership

Role 5 implements the metric in `eval/metrics.py` and the report builder,
including retained-final-message extraction, reproducible claim evidence,
exclusion reasons, bootstrap handling and tests. Claim extractor rules come
from `verifier/claims.py`, applied to the retained final message of the last
session. Role 1 owns schema/example publication and shared documentation;
Role 4 reviews consistency with claim semantics without changing the
criterion-level metric. Affected roles are Role 1 (report contract), Role 5
(producer/consumer/tests) and Role 4 (claim semantics review).

Publication is not implementation or measurement evidence. This lead session
does not touch `eval/`, inspect running reports or claim a task-level result.

## Assumptions

- User approval and the valid-task population resolution are explicit session
  instructions dated 2026-10-23; no additional population rule is inferred.
- Existing artifact references carry extraction provenance and exclusion
  reasons; the approved revision adds no per-task fields.
- Runtime implementation and dual-version consumer validation remain Role 5's
  responsibility. No historical report is migrated by this publication.
