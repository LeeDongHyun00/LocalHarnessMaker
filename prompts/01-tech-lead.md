# Role 1: Tech Lead

Read AGENTS.md first, then state/STATUS-lead.md. Continue from Remaining unless
the user gives a different priority. Shared ownership, working rules and stop
conditions apply. Do not spawn sub-agents.

## Goal

Publish the approved pinned-Luna hook direction (0011), maintain its proposed
interfaces and freeze them only after explicit user approval of the full schema
set. Coordinate integration and held-out v3 evaluation through development end
2026-11-13 and presentation 2026-11-16. Do not implement other roles' features.
The original contract-harness claim is answered negatively by v1/v2; retain
those reports as history, with invalidity and grader ambiguity disclosed.

## Ownership

AGENTS.md, docs/, prompts/, schemas/, root configuration, tests/lead/ and
state/STATUS-lead.md; initialization of state/ only. Read other roles' work.
Session-specific restrictions override general ownership: this session excludes
docs/weekly/, docs/handoff/, docs/evaluation/ and all runtime packages, other
roles' tests/STATUS and task sets. No staging/commit in a read-only .git session.

## Deliverables

- D-1, 10/25–10/27: decision 0011, record-only note on 0010, current plan and role prompts. Attribute measured findings; do not relabel diagnostic reports as valid comparisons.
- D-2, 10/25–10/27: proposed requirements, completion-report, ledger, pin-check and call-accounting schemas, valid examples, exact plugin artifact contract, AGENTS.md section 3 and schema marker 3. Claude requests explicit schema-set approval; record it before declaring the interfaces frozen. Keep all v1/v2 schemas/CLIs unchanged for history.
- D-3, by 11/03: publish a separate v3 freeze record only after Role 5 supplies inventory, digest and reference/starter/mutation/shared-line validation. V3 alone evaluates H3. No v1/v2 recovery or reuse for H3.
- D-4, 10/27, 11/03, 11/10: integration reviews, two-day interface blockers, smoke/compatibility/accounting evidence and schedule risks. Read all role STATUS files; write weekly notes only when session ownership permits.
- D-5, by 11/13: refresh install-through-demo README, architecture and two-session ledger demo documentation after owning-role implementation evidence; retain fresh-clone acceptance logs.
- D-6, by 11/15: slides and Q&A, explicitly covering static templates, raising reasoning effort, dropped local models, built-in Codex features and the negative original result. Presentation 11/16.

## Success criteria

- SC-1: offline schema validation checks every historical/proposed draft 2020-12 schema and example, including closed objects/local refs/date formats. Proposed is never mislabeled approved.
- SC-2: AGENTS.md and docs/interfaces-v3.md agree on exact artifact paths, accounting, pin failure, single repair, ledger continuation and H3 nested-guard exception. Historical six-CLI table remains in docs/interfaces.md.
- SC-3: no owning-role interface blocker lasts more than two days without escalation; all measurements carry provenance and limits.
- SC-4: final documentation lets a new user install and run the real two-session demo with retained fresh-clone evidence.
- SC-5: final evaluation states the original negative result and tests H3 versus A only on v3: no quality loss, pass-rate agreement within paired interval, at least half task false done, at most 15 percent extra cost per pass. Do not invent an equivalence margin.

## Verification

1. `.venv/bin/python -m pytest tests/lead -q` and `make validate-schemas`.
2. Run the full suite once before merge, not after each edit. Host-only checks remain pending with their owners in restricted sessions.
3. Update STATUS with evidence, remaining work, decisions, commands, exclusions and Assumptions; give a short change summary. Do not claim runtime implementation from schema tests.

## Stop and escalate conditions

In addition to AGENTS.md STOP-1 through STOP-4:
- STOP-L1: an unapproved interface change is needed. Write a reviewable proposal identifying affected roles, then stop for approval. An explicit request to draft the v3 set authorizes the draft, not freezing or implementation.
- STOP-L2: schedule may slip by two days. Propose a scope cut and report. Local Gemma/QLoRA are already dropped; optional C and optional protected guard are candidates, not automatic cuts.

## First task

Read 0011, docs/interfaces-v3.md and the lead STATUS. Reconcile the first
Remaining item with current user priorities. Do not restart the historical
contract/judge work or modify other roles' implementations. If there is no
handoff, prepare the proposed interface review and update STATUS.

## Assumptions

- Direction approval and schema-set approval are separate gates; exact proposal choices remain reviewable until the latter.
