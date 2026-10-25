# Delivery plan, version 3 direction

Dates are in 2026. Source: user-approved [Claude proposal](handoff/2026-10-25-v3-direction.md)
and [decision 0011](decisions/0011-pinned-luna-hook-direction.md), accepted
2026-10-25. This schedule replaces the v2 recovery/A-B-harness schedule from
decisions 0007–0008. Development ends 11/13; presentation 11/16.
The original Notion design [AI Project: GPT Operating Harness](https://app.notion.com/p/3ea42c8af69c80de8915f0e7a422d367)
and v1/v2 freeze records remain history.

## Direction and evidence

The original claim is answered negatively: v1 harness cost per pass is 32
percent above Sol medium without a measurable quality gain; v2 A passes 95/100
while the stopped harness passes 62/77 valid tasks with 23 invalid and more
attempts (2.17 versus 1.20). The v2 harness result is diagnostic, not a completed
valid comparison. V2 A's five failures share the reservations grader ambiguity.
See 0011 and the attributed [host record](weekly/2026-10-21-host-verification.md)
for populations, costs and uncertainty. Do not complete the stopped recovery.
0010 is record-only; no grader/digest amendment is authorized.

Build visible requirements, deterministic evidence checks, a claim audit and an
executor-written decision ledger. Pin `gpt-6-luna`, two low-effort calls per
completed session, one per phase; no silent substitution or LLM-written check
commands. Repair once only on executed deterministic failure. Local Gemma and
QLoRA remain dropped. Retain working runtime/audit/accounting infrastructure.

## Approval and freeze gates

The direction is accepted; the [version 3 schema/artifact set](interfaces-v3.md)
was approved by the user on 2026-10-25 at 01:55 KST exactly as proposed at
commit `d82b87a` and is frozen. `schemas/VERSION = 3` denotes the frozen set.
Roles 2–5 start implementation now using AGENTS.md sections 3.2–3.3 for frozen
hook CLIs and event mapping. Later schema changes require a new decision,
explicit user approval and a version increment.

V1 and v2 informed the design, so H3 is evaluated on held-out v3 only. Retain
old schemas/reports/freezes as history without rewriting them. The
[version 3 task set](eval-freeze-v3.md) was frozen on 2026-10-25 after Claude's
host review: 54 tasks, nine per shape, nine two-session tasks and 18 domains.
Claude computed the public-plus-complete-private-snapshot digest with
`eval.freeze_v3`:
`7645e003ed4ef52c43d58555f494c7554ee468c5e628b5d95e22c37a30b5b01d`.
The host record states that A and H3 select this digest. No hook, controller or
verifier change may use frozen v3 results; decision 0008's anti-contamination
rule applies to the new design. An outcome-informed change needs a new
held-out version. H3 stays not approved until actual runner plugin mode exists
and the host smoke passes.

Claude skipped the separate calibration pilot by evaluator decision recorded
in [the weekly host review, 2026-10-25](weekly/2026-10-21-host-verification.md).
Full A doubles as the calibration measurement; disclose a miss of the 60–85
percent single-session difficulty target without changing the frozen set.
The optional pilot config is a cost check, not completed calibration.

Retain decision 0006: record native version/tier/model/effort in every run,
probe a changed Codex version and run a one-task audit compatibility smoke
before large runs, stop on a mid-run version change. Compare identical versions
and settings; registry membership alone does not prove production behavior.

## Schedule

| Dates | Work and gate |
| --- | --- |
| 10/25 | Direction and interface approval recorded; v3 task set frozen after Claude host review at 07:40 KST. Publish the freeze record and digest; separate calibration pilot skipped. |
| 10/25–10/27 | Next: full A run on frozen v3, also the calibration measurement; retain native settings, access audits and accounting. Role 5 reports call/cost estimates before a batch of ten or more paid calls. |
| 10/25–11/03 | Next H3 gates: live hook smoke on two non-evaluation projects and Role 5 actual plugin-mode runner, including question pause/resume, accounting, application repair and ledger sequencing. H3 remains not approved until plugin mode exists and the host smoke passes. Keep implementation independent of frozen v3 outcomes. |
| 11/04–11/08 | After the gates pass, full H3 on the same frozen population/settings as A; retain tier, logs, hook artifacts and all accounting. Human review sample of requirements/reports. About two hours per configuration remains a proposal estimate; refresh cost estimates from A before paid batches. |
| 11/09–11/13 | Paired A/H3 comparison and final evaluation document covering v1/v2/v3, the original negative result, calibration outcome and separate ambiguity results. Recover only without outcome-driven tuning on frozen v3. Complete packaging, fresh-clone docs and two-session demo. Development ends 11/13. |
| 11/14–11/16 | Rehearsal; Role 1 slides/Q&A by 11/15; final presentation 11/16. |

Integration reviews remain 10/27, 11/03 and 11/10 (the first was prepared early
by Claude). Monitor two-day interface blockers and escalate schedule slips.

## Ownership and dependencies

| Role | Work |
| --- | --- |
| 1 Tech Lead | Decision 0011; proposed/frozen schemas and examples; artifact contract, approval record, plan/prompts; integration and freeze publication; install/demo/architecture documentation and final slides/Q&A. No runtime implementation. |
| 2 Plugin Engineer | SessionStart pin-check, verified-version/model/pricing advisory; mechanically validated ledger injection; optional PreToolUse protected-file guard after compatibility evidence; repeated-failure escalation advice; artifact lifecycle, install/check/packaging, process hygiene and two non-evaluation smoke projects. |
| 3 Controller Engineer | Requirements-table and claim-audit prompts with independent calibration sets; pinned low-effort Luna client, two-call budget/deadlines/accounting; code-owned check derivation coordinated with Role 4. Never inspect v3 tasks/graders or reconstruct ledger from transcripts. |
| 4 Verifier Engineer | Per-requirement completion report, deterministic check runner and evidence, single-retry rule; request executor ledger writing via Stop continuation and mechanically validate identifiers/hashes. No judge delegation on the hook path. |
| 5 Evaluation Engineer | Frozen v3 task set (54 varied, individually structured tasks); plugin runner mode that runs codex exec with plugin installed and collects the artifact directory; A/H3 configs, pilot/cost estimates, freeze validation, access audit/pricing, paired metrics and human samples. Runner does not orchestrate control calls. |

Owners edit only their paths and role STATUS. Cross-role implementation changes
need a proposal; the prompts specify package tests. All five original role
ownership boundaries and shared working rules continue to apply.

## Evaluation and success criterion

| Configuration | Execution |
| --- | --- |
| A | `gpt-6.1-sol`, medium, alone; LocalHarnessMaker bypassed via copied child environment `HARNESS_NESTED=1`. |
| H3 | Same executor/effort/settings plus installed hooks; remove the nested guard from executor/resume child environments so real hooks run. Nested controller children still set it. Collect `.localharness/v3/` after exit; no runner-owned contract/verify loop. |
| C, optional | User-filled static template on an explicitly matched subset; no required v3 run. |

B is dropped for v3. Use identical tasks, seeds, Codex version and effective
Fast/priority tier for A/H3. Record native tier evidence. Pinned versioned
API-equivalent Standard rates remain the accounting convention, not a claim
about actual Fast billing. Include all attempted executor/control calls, failed
calls and retries once; unknown cost stays null. Subscription use is not free.

V3 tasks cover bug fix, feature plus test, constrained refactoring, dense
requirements, two sessions, and ambiguous requests with author-prepared answers.
H3's eligible hook questions receive visible prepared answers, never inferred
intent. Under the disclosed [clarification policy](../eval/tasks-v3/DESIGN.md),
A receives no alternate responder, even if it asks in final prose; H3 gets no
answer when its hook fails to ask. Report the nine `ambiguous_requirement`
tasks separately and also report results excluding them: this stratum measures
a hook-mediated information advantage. Reference/starter/mutation validation
is attributed in the freeze record; shared-line and per-run access rules remain
required. The full A run supplies calibration after the evaluator skipped the
separate pilot; do not tune the frozen population or hooks from its outcomes.
Do not give private tests to controller or executor. Grade after all spawned work exits, in a fresh trusted copy, with all
logs hashed/audited under STOP-E4. Invalidity stays disclosed.

Measure pass rate, task-level false done (valid-task-only, retained last-session
final message), cost per pass, handoff_success and attempts. Add human-sampled
requirements precision against private grading and report accuracy against
hidden outcomes; keep review evidence private and publish aggregates through
existing artifact references. Retain criterion false done and historical parity
fields without inventing measurements; local parity is not measured. Collect
user feedback on visible artifacts separately from quality/cost success.

Success requires all three: H3 matches A's pass rate within the paired interval,
task-level false-done rate at least halved, and cost per passing task at most
15 percent above A. Any quality loss fails the design. Report paired differences
and seeded 95 percent task-cluster bootstrap intervals (default 10,000, minimum
1,000); zero denominators and missing accounting are undefined, not success.
No numeric equivalence margin is supplied. An interval including zero alone
does not prove equivalence or excuse observed quality loss.

## Open decisions

- [0011](decisions/0011-pinned-luna-hook-direction.md): resolved, accepted by the user on 2026-10-25; pinned Luna direction and success criterion, B dropped, C optional, 0010 record-only.
- [0010](decisions/0010-reservations-r2-grader.md): record-only after 0011; its historical remedy options do not authorize grader, digest or population changes.
- Version 3 schema set: resolved, approved by the user 2026-10-25 at 01:55 KST from commit d82b87a and frozen; implementation may start.

## Assumptions

- Approval, task freeze, digest and measured findings are supplied user/Claude host evidence; this offline session does not rerun them or access live Notion/private storage. Evaluator-owned draft files in this checkout predate the host freeze and are not synchronized by this documentation change.
- The 10/25–10/27 A window is the updated planning target, not execution evidence. About two hours per full configuration is the proposal's estimate, not an approved cost or measured runtime. Role 5 must report call/cost estimates before large paid batches; use A measurements to refresh H3 estimates.
- Artifact layout, audit-before-repair/stale-audit handling and separate ledger bookkeeping continuation are approved interfaces. Pending questions with an unchanged workspace allow termination without audit or ledger; no new hook wire fields.
- The user's interval criterion gives no numeric equivalence margin. Undefined/inconclusive evidence cannot be presented as achieved success.
