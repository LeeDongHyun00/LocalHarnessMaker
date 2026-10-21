# Role 2: Plugin Engineer (hooks and skill)

Read AGENTS.md at the repository root first. This file is your contract.

## Goal

Build the Codex plugin that runs this loop inside Codex: user request, then contract injection, then approval, then execution, then verification and re-instruction at the Stop event, then handoff save and injection. Keep the hooks thin. Hooks only call the controller and verifier CLIs; they never implement control or verification logic themselves.

## Ownership

Owned paths: plugin/ including the hook configuration (hooks.json or the hooks section of config.toml, whichever the installed Codex version uses), plugin/hooks/ (Python scripts), plugin/skills/harness/SKILL.md, plugin/templates/AGENTS.md (the file installed into user projects), plugin/install.sh, plugin/demo.sh, plugin/CODEX_VERSION. Tests in tests/plugin/.
Read-only: everything else.

## Interfaces

1. CLIs you call: python -m controller contract, python -m controller handoff, python -m verifier check, python -m verifier validate-handoff. See AGENTS.md section 3.2. If a CLI does not exist yet, use plugin/hooks/_stub.py, which returns the files in schemas/examples/ unchanged. Stub mode is enabled by the environment variable HARNESS_STUB=1.
2. Hook input and output: the documentation at https://learn.chatgpt.com/docs/hooks. Confirm the real input and output of the three hooks on the installed Codex version and record them in docs/hooks-contract.md. Role 1 merges that file.
3. State file: .harness/state.json in the user's project with the fields attempt, contract_path, verdict_path, handoff_path, started_at. Reset at the start of every session.

## Deliverables

- D-1, due 2026-10-24: docs/hooks-contract.md. It must answer: do the three hooks fire; the full input JSON sample for each; how output fields behave (is additionalContext visible to the model; does the Stop hook force continuation and which fields do that); do the hooks fire under codex exec. Attach evidence logs. Pin the installed Codex version in plugin/CODEX_VERSION.
- D-2, due 2026-10-27: end-to-end run in stub mode. A request is entered, the contract appears in the model context, the Stop hook re-instructs once, then the run passes. Reproducible with plugin/demo.sh.
- D-3, due 2026-11-03: real controller and verifier CLIs connected. Re-instruction limit N (default 3, configurable) and the state file.
- D-4, due 2026-11-10: SessionStart injection of the handoff document. install.sh that registers hooks, copies the skill, checks the Codex version, and supports a --check mode. Fallback on hook failure: any exception produces empty output plus a warning on stderr, and the session continues. Plugin packaging.
- D-5, due 2026-11-13: demo recording scenario (plugin/demo.sh plus a document with the screen order).

## What the skill (SKILL.md) must instruct the executor model to do

1. If a contract is present in the context, show a summary before doing anything: goal, checklist, assumptions, reasoning effort, estimated cost. Then wait for the user to answer approve or edit. Do not change any file before approval.
2. During the work, actually run the commands listed under verification in the contract.
3. At the end, report every success criterion in a table with its evidence: the command and its output, or the file path. Mark items without evidence as not done.
4. If the Stop hook re-instructs, handle only the unmet items and finish again.
5. If no contract is present, behave normally. The plugin must not interfere with the user's other work.

## Success criteria

- SC-1: each of the three hooks has a unit test of the form stdin JSON in, stdout JSON out, with the CLIs mocked.
- SC-2: an integration test in stub mode runs codex exec once and the contract text appears in the transcript.
- SC-3: the Stop hook forces continuation with reinstruct_message when verdict.overall is fail, and when attempt is greater than or equal to N it lets the session end and shows the list of unmet items to the user.
- SC-4: an exception in any hook script never breaks the Codex session: whole-script try and except, exit code 0, log on stderr.
- SC-5: a log line records the hook execution time; the target is under 1 second excluding the control model call.
- SC-6: install.sh --check reports Codex version mismatch, hooks not registered, and skill missing as three distinct messages.

## Verification

1. pytest tests/plugin
2. bash plugin/install.sh --check
3. bash plugin/demo.sh once in stub mode and once in real mode; keep both logs.

## Stop and escalate conditions

In addition to STOP-1 to STOP-4 in AGENTS.md:
- STOP-P1: the hooks behave differently from the documentation in a way that makes the design impossible, especially if the Stop hook cannot force continuation. Write a draft of the alternative in docs/decisions/ and report. The alternative: the skill instructs the executor to run python -m verifier check before finishing and to continue on its own based on the verdict.
- STOP-P2: a Codex version upgrade is required. Report it; the version is pinned.
- STOP-P3: the control model call inside UserPromptSubmit takes more than 5 seconds. Write down an asynchronous or cached design and report.

## First task

1. Record the installed Codex version. Register a script for each of the three hooks that only dumps stdin to a file. Collect the real input JSON and paste it into docs/hooks-contract.md.
2. In the Stop hook, return the continuation format from the official documentation with the message "test: print one more line". Check whether the session actually continues and record the result including the exact field names.
3. Repeat the same experiment under codex exec and record whether the hooks fire. Write the result in your STATUS file so that Role 5 can read it.
4. Update state/STATUS-plugin.md.
