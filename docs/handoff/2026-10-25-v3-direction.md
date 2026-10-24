# Proposal: a hook system that compensates gpt-6.1-sol, with gpt-6-luna pinned (2026-10-25)

Written by Claude for the user's approval after the user stopped the version 2 harness recovery. Role 1 turns the approved parts into a decision record (0011) and the plan; Roles 2 to 5 implement. Nothing here changes the frozen task sets or the retained reports.

## 1. What the measurements established

| Finding | Evidence |
|---|---|
| Sol medium alone saturates ordinary tasks | v1: A passes 100 of 100 single-session tasks; v2: 95 of 100 (the 5 failures are one grader-ambiguous family) |
| Sol max adds cost, not quality | v2: B 0.949 pass at 1.2x the cost of A at 0.95 |
| The cheap-control contract harness lowers quality and raises cost | v1: +32 percent cost, no quality gain; v2 as run: 0.805 pass (n 77) against 0.95, 2.17 attempts per task against 1.2 |
| Its failure modes are specific | wrong mechanical checks written by Luna (regex typo '- ', nonexistent paths), judge-heavy criteria (19 to 58 percent), re-instruction on non-executable evidence, handoffs extracted from transcripts (v2 handoff 11 of 15 against A's 18 of 19) |
| Sol's own weaknesses are visible | task-level false-done 5 percent on dense specs (v2 A); compliance with wrong instructions over spec fidelity; day-2 context loss 5 to 15 percent; assumes through ambiguity instead of asking (reservations R2, every effort level) |

The original claim (cheap control model + contract + verify beats A and B on cost per pass) is answered: no. The new goal is different: a hook layer that removes Sol's visible weaknesses with deterministic code plus a few cheap, pinned Luna calls, measured by the same evaluation infrastructure on a held-out task set.

## 2. Design principles (from the evidence)

1. Executable oracles, not LLM judgments. Every check the hooks enforce is deterministic: the project's own test command, protected-file hashes, existence of files named in the request, public API signature snapshots, input-immutability probes. Luna never writes regexes or commands.
2. The context owner writes the memory. The day-1 session (Sol) writes its decision ledger; the hook only validates it mechanically and injects it next time. Luna does not reconstruct handoffs from transcripts.
3. Evidence-based, single retry. Re-instruct at most once, only when an executable check fails. Never on judge opinions or unverifiable items.
4. Ask before assuming. Ambiguity in the request is surfaced to the user as questions before work starts, by Luna, as text the user confirms; the hook does not resolve ambiguity itself.
5. Pinned control model. gpt-6-luna is fixed in configuration, verified at session start against the installed Codex model list, priced from a pinned snapshot; a missing or renamed model fails closed with a visible advisory, never a silent substitution.
6. Value the user can see. Every hook produces an artifact the user reads: the requirements table with open questions, the completion report with per-requirement evidence, the decision ledger. Satisfaction is measured as well as pass rate.

## 3. The hooks

| Hook (Codex event) | Component | Owner | What it does | Luna call |
|---|---|---|---|---|
| SessionStart | pin-check | Role 2 | Verifies installed Codex version, that gpt-6-luna is listed, and that the pricing snapshot covers it; injects the decision ledger from the previous session after mechanical validation; writes an advisory and disables Luna hooks if the pin fails | none |
| UserPromptSubmit (first prompt) | requirements table | Role 3 | Luna restates the request as a numbered table of checkable requirements and lists ambiguities as questions; the table is shown to the user; mechanical checks are derived from the table by code (named files, named commands, named protected files), not by Luna | 1 (low effort) |
| PreToolUse on destructive edits (optional) | protected-file guard | Role 2 | Blocks edits to files the table marks protected; deterministic | none |
| Stop | completion report | Roles 4 and 3 | Runs the deterministic checks and the project's tests; Luna audits the executor's final message against the table (claim present, evidence cited) and writes a per-requirement report; one re-instruction only if an executable check failed | 1 (low effort) |
| Stop (after the report) | decision ledger | Role 4 | Asks the executor session, through the Stop-hook continuation, to write the ledger (decisions, rationale, open items) in a fixed schema; validates the schema and the named identifiers against the workspace | none |
| Stop (on repeated failure) | escalation advice | Role 2 | If the executable check still fails after the single retry, the report recommends a higher reasoning effort or a human review; the hook never changes effort itself | none |

Budget: two Luna calls per session (requirements table, completion report) at low effort, each under 10 seconds measured; control cost well under 2 percent of executor cost at Fast prices. Everything else is code.

## 4. What is kept from the current repository

- Plugin hooks runtime, process tree hygiene, version policy, install and check tooling (Role 2).
- Verifier's deterministic check runner, claims extraction, unittest and pytest support, sandboxed execution (Role 4). The llm_judge check type is retired from the hook path.
- Controller's Luna client, accounting lines, deadline handling, pinned pricing (Role 3). The contract prompt is replaced by the requirements-table prompt; the judge prompt by the claim-audit prompt.
- The whole evaluation runner, audit, pricing, recovery and comparison tooling (Role 5).

## 5. Evaluation of the new system

- Task set version 3 (Role 5): 50 to 60 tasks across varied shapes (bug fix, feature plus test, refactoring under constraints, multi-requirement, two-session, and a new shape: ambiguous requirement that the task author resolves one way, so that asking pays), built with the same grader validation (references pass, starters fail, mutation score, shared-line rules). Not a template family; each task has its own structure. Frozen before any run.
- Configurations: A (Sol medium alone) and H3 (Sol medium plus the hooks). B is dropped: v2 already shows max effort adds cost without quality. C stays the user's optional baseline.
- Metrics: pass rate, cost per pass, task-level false-done rate (the hooks' main target), handoff_success, attempts, and two user-facing measures: requirements-table precision (checked against hidden tests by a human sample) and report accuracy (the completion report's per-requirement verdicts against hidden grading).
- Freeze rule (decision 0008) is honored: the new design is informed by v1 and v2 results, so it is evaluated only on version 3; v2 is not reused for H3.
- Success criterion: H3 matches A's pass rate within the interval, lowers task-level false-done rate by at least half, and costs at most 15 percent more per passing task. Any quality loss fails the design.

## 6. Schedule (development ends 2026-11-13, presentation 2026-11-16)

| Dates | Work |
|---|---|
| 10/25 to 10/27 | User approval; Role 1 decision 0011 and plan; Role 3 requirements-table and claim-audit prompts with calibration sets; Role 5 version 3 task design |
| 10/28 to 11/03 | Role 2 pin-check and ledger injection; Role 4 completion report and single-retry rule; Role 5 builds and freezes version 3; live smoke of the hooks on two non-evaluation projects |
| 11/04 to 11/08 | Full runs: A and H3 on version 3 (about 2 hours each at Fast tier), human review sample of the reports |
| 11/09 to 11/13 | Recovery, paired comparison, final evaluation document covering v1, v2 and v3 with the negative result stated plainly |

## 7. Decisions requested from the user

1. Approve the direction and the success criterion in section 5.
2. Confirm gpt-6-luna as the pinned control model (alternative: pin to a dated snapshot name if Codex exposes one).
3. Confirm dropping baseline B for version 3 and keeping C optional.
4. Decide whether the reservations grader question (decision 0010) still needs an answer; with the v2 harness comparison abandoned it affects only the record of A and B on v2.
