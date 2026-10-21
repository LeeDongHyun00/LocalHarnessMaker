# LocalHarnessMaker - Shared Working Rules

This file lives at the repository root. Every Codex session reads it automatically. Role-specific instructions live in the prompts/ directory. Identifiers used across all prompts: Role 1 to Role 5 for roles, D-n for deliverables, SC-n for success criteria, STOP-n for stop conditions.

## 1. Project summary

LocalHarnessMaker is a Codex plugin (three hooks plus one skill) that makes GPT-6.1 Sol finish tasks completely, follow the user's intent, and continue work across sessions.

How it works:
1. A cheap control model (a low-cost API model, or a local Gemma 4 12B) turns the user's request into a contract: goal, constraints, success criteria, verification commands, stop conditions, explicit assumptions.
2. The executor model (GPT-6.1 Sol inside Codex) shows the contract, waits for approval, then does the work.
3. A verifier checks the result against the contract's success criteria and re-instructs the executor on unmet items only, up to a fixed number of attempts.
4. At the end of a session a handoff document is generated and injected into the next session.

Dates: development ends 2026-11-13. Final presentation 2026-11-16. The design document is the Notion page "AI Project: GPT Operating Harness".

## 2. Repository layout and ownership

| Path | Owner | Contents |
|---|---|---|
| AGENTS.md, docs/, schemas/, root configuration | Role 1 Tech Lead | shared rules, design and decision records (docs/decisions/), schemas, pyproject.toml, Makefile, CI |
| plugin/ | Role 2 Plugin Engineer | hook configuration, hook scripts, skill, AGENTS.md template for user projects, install script |
| controller/ | Role 3 Controller Engineer | contract generator, handoff generator, backends (cheap_api, local), case library, prompt templates for the control model |
| verifier/ | Role 4 Verifier Engineer | rule checks, checklist matching, done-claim verification, re-instruction messages |
| eval/ | Role 5 Evaluation Engineer | task set, runner, baselines, metrics, reports |
| state/STATUS-ROLE.md | each role | per-role status file used as the handoff between sessions |
| tests/ROLE/ | each role | unit and integration tests |

Rules:
1. Edit only the paths you own. Read everything else.
2. If you need a change outside your paths, write a proposal file in docs/decisions/ and stop.
3. Do not spawn sub-agents. One session per role.

## 3. Interfaces between roles

Frozen on 2026-10-24. Only Role 1 may change them. Every change requires a record in docs/decisions/ and an increment of schemas/VERSION.

### 3.1 Schemas (directory schemas/, JSON Schema draft 2020-12)

File contract.schema.json, the contract:
- task_summary: string
- constraints: array of string
- success_criteria: array of objects with fields id, description, check
  - check.type is one of: command, file_exists, regex, llm_judge
  - check fields by type: command uses command and expected; file_exists uses path; regex uses path and pattern; llm_judge uses rubric
- verification: array of objects with fields command, expected
- stop_conditions: array of string
- assumptions: array of string. Things the request did not state and the control model assumed. The user corrects them before approval.
- reasoning_effort: object with fields value, rationale. value is one of: low, medium, high, xhigh, max. Computed by code in controller/analyze.py, never by the model.
- cost_estimate: object with fields input_tokens, output_tokens, usd. Computed by code.

File verdict.schema.json, the verdict:
- items: array of objects with fields id, status, evidence, reason. status is one of: pass, fail, unverifiable.
- overall: pass or fail
- reinstruct_message: string or null
- attempt: integer

File handoff.schema.json, the handoff document:
- done: array of objects with fields criterion_id, artifact
- remaining: array of objects with fields criterion_id, state
- decisions: array of objects with fields what, why
- verify_commands: array of string
- do_not_touch: array of string

### 3.2 Command line interfaces

Each role provides these commands. Hooks and the evaluation runner call them.

1. python -m controller contract --prompt FILE --handoff FILE_OR_none --cases DIR --backend cheap_api_OR_local --out contract.json
2. python -m controller handoff --transcript PATH --contract contract.json --verdict verdict.json --backend cheap_api_OR_local --out handoff.json
3. python -m controller judge --criterion JSON_FILE --artifact PATH --backend cheap_api_OR_local --out judgment.json (used only for llm_judge criteria)
4. python -m verifier check --contract contract.json --workspace DIR --transcript PATH --attempt N --out verdict.json
5. python -m verifier validate-handoff --handoff handoff.json
6. python -m eval run --config YAML --out eval/reports/NAME/

Conventions for every command:
- Exit code 0 means success, 1 means input error, 2 means internal error.
- stdout contains exactly one line: the path of the output file. All logs go to stderr.
- Every output JSON must validate against its schema.

### 3.3 Hook input and output

Source of truth: the Codex hooks documentation at https://learn.chatgpt.com/docs/hooks until the file docs/hooks-contract.md exists. Once Role 2 writes docs/hooks-contract.md from the installed Codex version, that file is the source of truth.

- Input on stdin as JSON: session_id, transcript_path, cwd, hook_event_name, model, and for the UserPromptSubmit event also prompt.
- UserPromptSubmit output: the contract text in the field hookSpecificOutput.additionalContext.
- Stop output: if the verdict is fail, force continuation and pass the re-instruction message as the next prompt; if the verdict is pass, return empty output.
- SessionStart output: the handoff text in the field hookSpecificOutput.additionalContext.
- SessionEnd is observe-only. Do not use it.

## 4. Working rules

1. Start of session: read state/STATUS-ROLE.md for your role. Continue from the first item under the heading Remaining. If the file is empty, do the First task section of your role prompt.
2. Assumptions: never guess. List anything the request does not specify under a heading named Assumptions, both in the PR description and in the STATUS file.
3. Bias to action: do not stop to ask questions. Produce a reviewable result, then report it together with your assumptions. Stop only for the conditions in section 5.
4. Definition of done: tests pass, STATUS file updated, change summary written. Every claim of done must carry evidence, meaning the command you ran and its output. Items without evidence are reported as not done.
5. End of session: update state/STATUS-ROLE.md using the format in section 6.
6. Tests: run only the tests of the package you changed. Run the full suite once before merge. Do not run the full suite after every small edit.
7. Code: Python 3.11 or newer, type hints everywhere. Comments, docstrings and commit messages in English. Conventional Commits with prefixes feat, fix, test, docs. pytest for tests. Every external call (HTTP API, model server, codex exec) must be mockable.
8. Scope: no unrequested refactoring or features. Do not change schemas, CLIs or hook interfaces. Only Role 1 may.
9. Secrets: API keys come from environment variables only. Never write them into the repository.
10. Reports: short paragraphs and tables. No decorative formatting, no repetition, no closing summaries.

## 5. Stop and escalate conditions

Stop and report to the user when any of these holds:
- STOP-1: progress requires changing an interface (schema, CLI, hook input or output).
- STOP-2: progress requires editing a path owned by another role.
- STOP-3: you are about to run 10 or more paid calls (executor model or control API) in one batch. Report the cost estimate first.
- STOP-4: the action deletes files, rewrites git history, or changes an external service configuration.

## 6. STATUS file format

File: state/STATUS-ROLE.md. Use exactly these headings, in this order, as markdown level-2 headings:

1. Done. One bullet per item, each ending with the evidence in parentheses: the command and its result.
2. Remaining. One bullet per item, in the order they should be done.
3. Decisions. One bullet per decision in the form: what was decided, then a colon, then why.
4. Verify commands. One bullet per command that shows the current state is correct.
5. Do not touch. One bullet per path or rule the next session must not change.
6. Assumptions. One bullet per assumption made during the session.
