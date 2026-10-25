# Evaluation task set version 3 freeze (D-3)

Frozen on 2026-10-25 after Claude's independent host review. The
[host record](weekly/2026-10-21-host-verification.md) records review at
06:40 KST and freeze at 07:40 KST: Role 5 set `frozen=true` on all 54 task
`meta.json` files, changing only that field. This documentation session did
not rerun evaluation or private grading.

Task-set SHA-256:

```text
7645e003ed4ef52c43d58555f494c7554ee468c5e628b5d95e22c37a30b5b01d
```

Claude computed the digest on the host with `eval.freeze_v3` over public
inputs plus the complete version 3 private snapshot: graders, coverage,
references, author notes and question matchers. Private locations and contents
are not published here.

## Scope and inventory

Version 3 contains 54 tasks in `eval/tasks-v3/`: nine per shape across 18
domains, three tasks per domain. There are 45 single-session and nine
two-session tasks, requiring 63 executor sessions per full configuration.
The two-session row is part of the 54-task total, not an additional population.
Domains are strata rather than shared-template families; see the
[design and inventory](../eval/tasks-v3/DESIGN.md).

| Shape | Tasks | Two-session tasks included |
|---|---:|---:|
| `bug_fix` | 9 | 0 |
| `feature_plus_test` | 9 | 0 |
| `constrained_refactoring` | 9 | 0 |
| `multiple_requirements` | 9 | 0 |
| `two_session` | 9 | 9 |
| `ambiguous_requirement` | 9 | 0 |
| Total | 54 | 9 |

## Host verification evidence

The 2026-10-25 host review and freeze record supply the findings below.
Author validation is recorded separately in
[VALIDATION.md](../eval/tasks-v3/VALIDATION.md). No complete host command
invocation was supplied beyond the digest module name; none is inferred here.

| Check | Result |
|---|---|
| Recorded author reference/starter validation | All 54 references pass; all 54 untouched starters fail |
| Recorded author coverage and mutations | 225 requirements covered; 325 reference checks; 3,168 mutants, 2,980 killed, 188 equivalent, zero survivors/errors |
| Claude independent host validation, up to 60 mutants per task | All 54 graders; 2,355 killed, 139 recorded equivalents, zero survivors/errors; smallest killed population 9 |
| Host public-input inspection | No private references; prompt length 194–393 words, median 266 |
| Host prompt spot review | Three prompts across bug fix, ambiguity and two sessions; distinct structures, numbered requirements and an explicitly unresolved ambiguity axis |
| Freeze implementation package checks | Host record reports `tests/eval`: 2,157 passed |

These are attributed findings from finite checks, not proof that every possible
mutation or implementation was checked. Public-input inspection does not
replace shared-line validation or each run's private-grader access audit.

### Calibration and known limitation

Claude, as evaluator, skipped the separate ten-task calibration pilot at the
06:40 KST review; the [weekly record](weekly/2026-10-21-host-verification.md)
documents this departure from the earlier design. The full A run doubles as
the calibration measurement. The 60–85 percent A pass-rate target on the 45
single-session tasks remains a target; if A misses it, disclose the miss in
the final evaluation without replacing, selecting or changing tasks.
`pilot-v3-a` remains an optional cost check, not a completed pilot. Controller
prompt calibration is separate evidence and does not calibrate this task set.

The nine `ambiguous_requirement` tasks have a disclosed clarification
asymmetry in [DESIGN.md](../eval/tasks-v3/DESIGN.md): H3 receives prepared
answers only when its hook raises an eligible question; A has no hook table
and receives no alternate responder, even if its final prose asks a question.
H3 receives no answer when its hook fails to ask. This stratum measures a
hook-mediated information advantage. Report it separately, alongside results
excluding those nine tasks; do not describe it as equal-information reasoning.

## Freeze and reporting rules

Version 3 never changes. Any task-set revision requires a separately identified
held-out version and a new freeze record. A and H3 select the digest above in
`metadata.task_set_sha256`; Claude's host record states that both full-run
configurations were filled with it. H3 remains **not approved** until the
runner's actual plugin mode exists and the host smoke passes. A digest does
not establish hook compatibility, execution approval or successful H3 results.

After this freeze, no hook, controller or verifier change may use version 3
results: the anti-contamination rule in
[decision 0008](decisions/0008-task-set-v2.md) applies to the new design.
Outcome-informed changes require a new held-out population. Versions
[1](eval-freeze.md) and [2](eval-freeze-v2.md), which informed this design,
remain historical and unchanged; H3 is evaluated only on version 3.

Run full A first, complete live hook smoke and runner plugin mode, then run
H3 and the paired comparison on the frozen population under the
[dated plan](plan.md). Retain native Fast/priority tier, model/effort and
Codex-version evidence, pinned Standard-rate API-equivalent accounting,
post-exit trusted grading and STOP-E4 access audits. Report paired uncertainty
and invalidity. This record changes no schema, CLI or hook interface.

## Assumptions

- Freeze, digest and host validation are supplied Claude findings dated
  2026-10-25; this offline session does not access the private snapshot or
  independently recompute its digest. No freeze commit identity is inferred.
- Evaluator files in this checkout retain pre-freeze draft wording/configs.
  The later user-supplied host freeze record governs this publication; no
  evaluator-owned file is changed or certified as synchronized here.
