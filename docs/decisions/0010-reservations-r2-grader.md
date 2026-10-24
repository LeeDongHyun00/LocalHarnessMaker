# 0010: Reservations R2 grader ambiguity

Date: 2026-10-24

Status: proposed, awaiting the user.

## Context

Role 5's read-only diagnosis of 2026-10-24, recorded in Claude's
[weekly host note](../weekly/2026-10-21-host-verification.md#diagnosis-of-the-reservations-family-r5-diag-001-read-only-2026-10-24-0420-utc),
identifies an ambiguous public requirement in the frozen version 2 reservations
family. All five baseline A tasks and both baseline B reservations tasks run so
far fail exactly one hidden test, `test_R2_shapes`; both calibration pilots show
the same one-test failure on every valid reservations task. These are attributed
diagnostic findings, not measurements rerun by this lead session.

The five test bodies are identical. They expect an otherwise valid integer
endpoint to be rejected when it is an integer subclass, with booleans checked
separately. Public R2 says only that start and end are ints excluding bool;
the other 95 tasks explicitly require built-in integers. Every retained
implementation accepts integer subclasses and rejects booleans, a reasonable
reading of the reservations text. The preservation wording in feature_plus_test
and constrained_refactoring somewhat favors the stricter reading, but does not
remove the ambiguity. The references pass by inspection.

[Decision 0008](0008-task-set-v2.md) freezes the task set, including grader
contents. The [version 2 freeze record](../eval-freeze-v2.md) requires version 3
for task-set changes. An amended grader and revised frozen digest therefore
require an explicit user decision authorizing an exception to that policy;
this proposal supplies no such authorization.

## Options

| Option | Effect on comparison between configurations | Effect on the freeze |
|---|---|---|
| (a) Keep the graders and disclose the family | Preserve the original as-graded comparison, disclosing that the same ambiguous expectation affects every configuration. These failures cannot be attributed unambiguously to executor capability. | Keep all frozen inputs, graders and the original digest unchanged. |
| (b) Exclude the family from headline numbers as a disclosed grader defect | Compare every configuration on the same 95-task population, within its approved task scope; retain original results and disclose the exclusion. Never remove tasks selectively by configuration or outcome. | Keep graders and the original digest unchanged, but obtain user approval for the changed headline analysis population. |
| (c) Amend the five tests so both readings pass | Preserve boolean, non-integer, bound and exact-error checks; permit either acceptance or rejection of otherwise valid integer subclasses. Regrade every configuration equally from retained artifacts, keeping original and amended results distinguishable and comparing only like gradings. | Obtain user approval for the freeze-policy exception, publish a revised frozen digest, and retain the original digest/results as history. No silent replacement of the frozen graders or results. |

The 95-task population in (b) is the common family-excluded set, not a claim
that baseline B runs two-session tasks. Decision 0007's approved scopes still
apply: A/harness comparisons use that population, while comparisons involving
B use the same eligible single-session subset for both configurations.

## Recommendation

Role 5 recommends (c), with (b) for interim headline numbers until equal
regrading is complete, and (a) retained as the disclosed original comparison.
Claude concurs: the public prompt omits the distinction, the ambiguity affects
all configurations, and regrading retained artifacts is cheap and reproducible.
The decision belongs to the user. This recommendation is not accepted policy.

## Consequences if accepted

1. Role 5 amends the five graders in the private root, retaining the checks
   listed in (c), and reruns `validate_graders` and the freeze digest.
2. Claude verifies the amendment and validation on the host and records the
   new digest in `docs/eval-freeze-v2.md`, preserving the original identity and
   the user-approved exception to the freeze policy.
3. Every version 2 report is regraded equally with the amended graders from
   retained artifacts under the existing access-audit and post-exit grading
   rules. This requires no new executor or model calls.
4. The final evaluation reports both original and amended gradings, with their
   respective digests and populations. Interim family-excluded headlines are
   labeled and never substituted silently for the original comparison.

## Scope and verification

This record publishes a proposal only. Pending the user's decision, reports
remain as graded and the existing freeze remains in force. This session changes
no grader, task, report, digest, schema, CLI or hook interface and does not
inspect private test contents. Implementation and host verification remain
pending with their owners.

## Assumptions

- Failure counts, abstract test behavior and reference findings are supplied
  by the user and the linked Role 5/Claude diagnosis; no independent grading
  or live-run verification is claimed here.
- No remedy or freeze exception has been approved. The recommendation and
  conditional ownership steps do not authorize changes in another role's paths.
