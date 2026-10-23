# Host recording sequence

1. Show plugin/VERIFIED_VERSIONS.json, the actual version saved in the demo
   experiment.json, and the three registered hooks in the temporary demo
   home's hooks.json. Explain the 30/480/120-second child deadlines and
   40/660-second UserPromptSubmit/Stop deadlines.
2. Run `bash plugin/demo.sh --real --out plugin/evidence/DATE-real` from the
   checkout. Show the saved contract summary: goal, criteria, assumptions,
   effort and cost. Show the empty request-workspace.json before approval. Pause at the approval prompt for review.
3. Type `approve`. Show result.txt creation and verification. If the real
   verifier re-instructs, show only the unmet criteria being addressed. A
   first-attempt pass is also valid; do not manufacture a failure.
4. Show approval-summary.json, approval-state/verdict.json and
   approval-state/handoff.json. Run the offline evidence audit documented in
   README.md and show its output. Identify any missing evidence as pending.
5. For an intentionally synthetic continuation example, show the preserved
   2026-10-21-d2-pass evidence or run a fresh stub demo in another directory.
   Label it routing-only and synthetic throughout.
6. Follow the real two-session sequence below for handoff injection. Persisted
   hook trust remains a separate check; offline tests do not establish live success.

This sandbox session prepared the scenario and real mode without running Codex.

## Real two-session handoff demonstration (D-4/D-5)

Prepared for Claude on the host; not executed in the workspace sandbox. Use a
fresh `plugin/evidence/DATE-two-session/` directory (replace DATE below). Keep
the temporary workspace and home between days. Do not resume day 1 to simulate
day 2: the script deliberately launches a new thread for day 2.

Prerequisites: activated repository environment, real controller/verifier,
working CLI login, and a host CLI with passing compatibility evidence in
VERIFIED_VERSIONS.json. The script checks identity before/after stages and
stops on changes. It uses temporary HOME/CODEX_HOME/workspace, references the
existing login with a temporary symlink without copying credentials, and sets
HARNESS_BACKEND=codex_cli with stub mode disabled. Executor hooks run normally;
controller children retain the nested guard. The real home is unchanged.
Hook trust is bypassed for this isolated demonstration; persisted trust is a
separate host check. Do not use this demonstration during a host evaluation if
sharing host model capacity would disrupt it.

1. Run `.venv/bin/python -m plugin.two_session_demo day1 --out plugin/evidence/DATE-two-session`.
   Show the day-1 contract and type `approve` after reviewing it. The task writes
   exactly `ok\n` to result.txt and verifies it. A fresh random release label is
   given only on day 1; the executor reports it as a decision for the next day,
   without writing it in a task file. Stop must produce a passing real verdict
   and a handoff retaining that decision. The script validates the saved handoff
   with the real `verifier validate-handoff` CLI and saves its command/result.
   Show day1/approval-state/{verdict,handoff}.json and handoff-validation.json.
   If the controller loses the decision, retain the failed evidence and start
   a fresh directory; do not repair the handoff by hand.
2. Run `.venv/bin/python -m plugin.two_session_demo day2 --out plugin/evidence/DATE-two-session`.
   This is a separate invocation so day 1 is reviewable before more live calls.
   Show the new session ID, same workspace/home, and first SessionStart event
   in day2/hooks.jsonl. Its additionalContext must equal the saved handoff, and
   that exact context must occur as developer text in request-transcript.jsonl.
   The only task request is the constant FOLLOWUP in plugin/two_session_demo.py:
   use yesterday's release label for followup.txt. It never states the label.
3. Review the day-2 contract and type `approve`. Show followup.txt, its exact-byte
   verification, and the passing day-2 verdict. No user clarification turn is
   sent. Both days support `--scripted-approval` for Claude's unattended host
   run; this sends only `approve` after printing the summary and is demo-only.
4. Offline, run `.venv/bin/python -m plugin.two_session_demo check --out plugin/evidence/DATE-two-session`.
   Require saved_handoff_validated, session_start_injected, context_visible,
   new_session and approval_gates=true; user_restatement_needed=false; overall=pass.
   Capture the output alongside the automatic audit.json. The checker reads
   retained evidence only, including passing schema-validated verdicts, distinct
   session IDs, unchanged approved contracts, workspace snapshots, successful
   executor stages and exact final bytes. Changed/missing evidence fails closed.

Each successful no-retry day uses two executor launches, one contract call and
one handoff call (at least four paid calls); judge criteria, retries and fallback
can add calls. Before a batch of ten or more paid calls, report its host cost
estimate under STOP-3. No cost or live success is claimed by this preparation.
Do not overwrite an attempted day or delete its temporary files; retain failures.

The evidence establishes receipt of the handoff and successful follow-up without
user restatement. It does not prove that the model relied exclusively on that
context: day-1 files still exist in the shared workspace, and tool access is not
isolated by this demo. Exhaustion, stale-handoff rejection, persisted trust and
macOS sandbox isolation remain separate host checks.
