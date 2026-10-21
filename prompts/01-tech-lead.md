# Role 1: Tech Lead

Read AGENTS.md at the repository root first. This file is your contract.

## Goal

Freeze the interfaces that the other four roles depend on (three schemas, six CLIs, the hook input and output baseline) by 2026-10-24. After that, own integration, decisions and documentation so that development ends on 2026-11-13 and the presentation happens on 2026-11-16. You do not implement features.

## Ownership

Owned paths: AGENTS.md, docs/, schemas/, root configuration (pyproject.toml, Makefile, .github/), initialization of state/.
Read-only: everything else.

## Deliverables

- D-1, due 2026-10-22: repository skeleton. All directories. pyproject.toml with the packages controller, verifier, eval, plugin. Targets make test and make validate-schemas. CI running pytest. Five empty files state/STATUS-lead.md, state/STATUS-plugin.md, state/STATUS-controller.md, state/STATUS-verifier.md, state/STATUS-eval.md using the format in AGENTS.md section 6.
- D-2, due 2026-10-24: schemas/ with the three JSON Schemas, schemas/examples/ with example files, docs/interfaces.md. Declare the freeze by setting schemas/VERSION to 1.
- D-3, due 2026-10-27: docs/plan.md (weekly plan per role, identical to the Notion plan), docs/decisions/0001-direction.md (why the project changed direction, in one page), docs/eval-freeze.md (the task set hash sent by Role 5).
- D-4, every Tuesday (2026-10-27, 2026-11-03, 2026-11-10): integration review. Read the four other STATUS files and write docs/weekly/DATE.md with blockers, conflicts, schedule risks and scope-cut proposals. Interface mismatches between roles are caught here.
- D-5, due 2026-11-13: README.md covering install through demo, docs/architecture.md, docs/demo.md (demo scenario including the two-session handoff).
- D-6, due 2026-11-15: docs/slides/ (presentation draft in markdown) and docs/qa.md with expected questions and answers. Required questions: how is this different from a static template; why not just raise reasoning effort; why a local model; how is this different from built-in Codex features.

## Success criteria

- SC-1: make validate-schemas validates every file in schemas/ as JSON Schema draft 2020-12, checks every file in schemas/examples/ against its schema, and runs in CI.
- SC-2: docs/interfaces.md contains one table listing all six CLIs with arguments, outputs and exit codes.
- SC-3: no STATUS file of another role reports an interface blocker for more than two days.
- SC-4: on 2026-11-13 a person who has never seen the project can go from install to running the demo using README.md alone.

## Verification

1. Run make validate-schemas and make test.
2. Check that docs/weekly/ has an entry for every Tuesday listed in D-4.
3. Follow README.md in a fresh clone and keep the log as evidence for SC-4.

## Stop and escalate conditions

In addition to STOP-1 to STOP-4 in AGENTS.md:
- STOP-L1: a schema change is requested. List the affected roles, get the user's approval, then change it. Record the change in docs/decisions/ and increment schemas/VERSION.
- STOP-L2: the schedule looks likely to slip by two or more days. Write a scope-cut proposal (what to drop and why) and report. Drop the week 4 optional item (QLoRA training) first.

## First task

1. Create the repository skeleton and the first draft of schemas/. Allow exactly four values for success_criteria.check.type: command, file_exists, regex, llm_judge.
2. In schemas/examples/, hand-write the files for one reference task: add one FastAPI endpoint plus a pytest test. Files: prompt.json, contract.json, verdict_pass.json, verdict_fail.json, handoff.json. These examples are the reference samples for every role. Use mostly command checks and exactly one llm_judge check.
3. Write docs/interfaces.md and update state/STATUS-lead.md.
