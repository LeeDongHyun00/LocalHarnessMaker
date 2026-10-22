# 0006: Codex version policy

Status: approved by the user on 2026-10-22

## Context

At about 03:57 UTC on 2026-10-22, the ChatGPT app updated its bundled Codex CLI
from `0.162.0-alpha.17.2` to `0.163.0-alpha.11.1` on its own. No other Codex
binary exists on the Mac. All pilot runs (30 executor sessions) and all
development jobs up to 03:50 UTC used `0.162.0-alpha.17.2`.

These are the user-supplied host facts, already recorded in [CLAUDE.md section
2](../../CLAUDE.md#2-how-to-run-codex) (commit `d3cb0c6`) and [host verification,
decision 11](../weekly/2026-10-21-host-verification.md#codex-version-change-and-policy-2026-10-22).
This record makes the approved policy a shared rule; it does not claim a new
host probe or runtime implementation.

## Decision

- The installed version may keep changing. Do not hold or roll back versions.
- Every run records the installed version in evaluation report metadata
  `codex_version` and the per-session `cli_version`.
- Only reports produced with the same Codex version are compared for evaluation
  SC-3. A mixed-version comparison is diagnostic only.
- A version change requires a new hook compatibility probe and a one-task audit
  compatibility smoke before any large run.
- A run stops if the Codex version changes in the middle of it.
- The plugin keeps a list of verified versions with their probe evidence instead
  of a single pin. Publish the version history and evidence in `plugin/` and
  [the hook contract](../hooks-contract.md#verified-versions).

## Scope and verification

The published hook evidence starts with `0.162.0-alpha.17.2`.
`0.163.0-alpha.11.1` remains pending until Claude's host compatibility probe;
a one-task audit compatibility smoke is also required before a large run.
Startup evidence does not establish production guard, handoff, trust or retry
behavior. Implementation and host verification remain with their owning roles.

This decision changes policy wording only. It changes no schema, CLI, hook input
or output, or `schemas/VERSION`.

## Assumptions

- Version history and pilot/development provenance are supplied host evidence;
  this offline session does not independently rerun the host measurements.
