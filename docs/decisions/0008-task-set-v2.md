# 0008: Harder evaluation task set version 2 and Fast tier

Status: approved by the user on 2026-10-23

## Context

The user supplied the full baseline A result on frozen version 1:
`eval/reports/full-a`, commit `a21eda2`, codex-cli `0.163.0-alpha.11.1`,
115 of 120 tasks passed, including all 100 single-session tasks. On that
single-session pass rate the proposed system can at best tie A while adding
control cost; version 1 cannot test the intended project claim adequately.
Version 1 remains frozen and its results remain part of the final report.
These are attributed host results, not measurements rerun in this session.

The user approved a harder version 2 and the Codex “Fast” service tier,
`service_tier = "priority"`, described by the CLI as about 2x speed with
increased usage. The user reaffirmed that usage is not a constraint and that
completeness of the results is the goal.

## Decision

1. Build a separate set at `eval/tasks-v2/`, with task IDs prefixed `v2-`,
   its own external private graders, and its own freeze record and digest.
   Do not modify version 1 tasks, graders, digest or historical results.
2. Make version 2 harder by design: multi-file packages, more explicit
   requirements and constraints, and two-session tasks whose day-2 work
   depends on day-1 decisions the user does not restate. Every hidden test
   must follow from the public prompt; difficulty must not depend on hidden
   requirements.
3. Calibrate with a baseline A-only pilot, targeting roughly 30–70 percent
   pass rate. Adjust difficulty at the design level. Never select or drop
   individual tasks because of their pilot outcomes. Freeze the set before
   any full run; run A, B and the harness fresh on the frozen set. Pilot
   results are calibration evidence and do not substitute for full runs.
4. Use `service_tier = "priority"` for Codex development jobs and every
   version 2 evaluation configuration. Record and verify the effective tier
   from native session settings, rather than treating a requested setting
   as proof. Reports state the tier so comparisons between configurations
   remain like for like. API-equivalent costs continue to use the pinned
   Standard rates; this convention does not claim actual priority billing
   equals Standard billing.
5. After the version 2 freeze, no harness change may use version 2 results.
   The final evaluation must disclose which version 1 runs informed the
   harness fixes of 2026-10-23, distinguishing development evidence from
   the frozen version 2 evaluation.

## Schedule and ownership

Use the approved execution windows from decision 0007: W2 through
2026-11-06 and W3 through 2026-11-13. Build, validate and calibrate version 2
in W2, then freeze it before full runs. Run fresh full A, B and harness
measurements across W2 and W3; finish final analysis by 2026-11-13.
[The plan](../plan.md) records this update, which supersedes conflicting
measurement timing for version 2. Decision 0007's remaining scope cuts and
comparison scopes continue to apply; this decision sets no new task count.

Role 5 owns task construction, private validation, calibration, run
configuration and retained tier evidence. Role 1 publishes the separate
version 2 freeze record after receiving its inventory, digest and evidence.
Existing private-grader access auditing and post-exit grading rules apply.

## Scope and verification

This record publishes the approved policy only. It does not build or freeze
version 2, configure a service tier, run a model, or verify native settings.
It changes no schema, CLI, hook interface or `schemas/VERSION`; tier reporting
must use existing compatible evidence artifacts, not an unapproved schema
field. Any required interface revision follows the existing approval process.
The host evaluation runs are untouched.

## Assumptions

- Approval, the baseline result and the CLI's Fast description are supplied
  by the user; no independent host or network verification is claimed.
- Version 2 task count, exact freeze date and digest await owning-role
  evidence. The calibration target is approximate, not a measured result.
