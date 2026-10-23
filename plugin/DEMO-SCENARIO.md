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

Claude completed the pass-path host run on 2026-10-23 at de38626; retained
evidence is plugin/evidence/2026-10-23-two-session/ (commit 4fa9ec2). Its offline
checker passes all flags above.

The evidence establishes receipt of the handoff and successful follow-up without
user restatement. It does not prove that the model relied exclusively on that
context: day-1 files still exist in the shared workspace, and tool access is not
isolated by this demo. Exhaustion, stale-handoff rejection, persisted trust and
macOS sandbox isolation remain separate host checks.

## Remaining handoff checks for Claude (host only)

These scripts are prepared, not live-verified. Wait until the host evaluation is
finished before using model capacity. Use raw captures outside the checkout and
fresh directories for every scenario; never overwrite a failed capture. All
commands below run from the repository. The same compatibility/login/isolation
prerequisites as the pass demonstration apply. The scripts check the CLI identity
between stages. No production hook, controller or verifier interface is changed.

Run each numbered command separately, reviewing its output before the next.
`--scripted-approval` is optional for unattended Claude runs and sends only
`approve` after displaying the captured contract.

### Exhaustion

1. `.venv/bin/python -m plugin.handoff_failure_demo day1 --scenario exhaustion --out /tmp/lhm-DATE-exhaustion --scripted-approval`
2. Show day1/request-state/contract.json: exactly one command criterion,
   `python -c 'raise SystemExit(1)'`, expected exit 0. The script refuses approval
   if the real controller changes it. After approval the executor must honestly
   leave this intentionally impossible check unmet. HARNESS_MAX_ATTEMPTS=1 is set
   only in the child environment. Show the real fail verdict at attempt 1,
   session phase `exhausted`, Stop systemMessage listing unmet IDs, and validated
   handoff.remaining containing those same IDs. There are zero re-instructions.
3. `.venv/bin/python -m plugin.handoff_failure_demo day2 --scenario exhaustion --out /tmp/lhm-DATE-exhaustion`
4. Show distinct session IDs, unchanged project/home, and exact saved-handoff
   context in SessionStart and the developer transcript. Day 2 stops at approval;
   no second approval or completion is needed to establish receipt.
5. `.venv/bin/python -m plugin.handoff_failure_demo check --scenario exhaustion --out /tmp/lhm-DATE-exhaustion`
   Require overall=pass, remaining_injected=true, new_session=true,
   approval_gates=true and stale_injected=false.

### Stale context after generation or validation failure

Run this sequence twice, replacing MODE with `generation` and then `validation`,
using a separate raw directory for each. Do not combine them into a paid batch.

1. `.venv/bin/python -m plugin.handoff_failure_demo day1 --scenario MODE --out /tmp/lhm-DATE-MODE --scripted-approval`
2. Show previous-handoff.json: a valid demo seed containing
   `obsolete-release-context`. This is explicitly seeded old context, not a
   claimed previous live outcome. The real task creates result.txt and passes
   the real verifier. A temporary interpreter wrapper delegates all calls to
   the real Python except the selected boundary: generation returns exit 2 from
   `controller handoff` without a model call; validation lets generation finish,
   then returns exit 2 only for `verifier validate-handoff` on handoff.pending.*.
   Current-handoff validation at SessionStart is never intercepted. Show
   faults.jsonl, the Stop error, unchanged handoff.stale.*.json bytes, absent
   handoff.json, and (validation case) retained generated pending handoff.
   This demonstrates real lifecycle handling of an injected CLI failure; it
   does not claim a natural provider outage or invalid model response occurred.
3. `.venv/bin/python -m plugin.handoff_failure_demo day2 --scenario MODE --out /tmp/lhm-DATE-MODE`
   Day 2 launches a new session with the real interpreter and no injected fault.
   Show SessionStart output=null, no HARNESS_HANDOFF in the developer transcript,
   archived previous bytes still present and no current handoff. Stop at approval.
4. `.venv/bin/python -m plugin.handoff_failure_demo check --scenario MODE --out /tmp/lhm-DATE-MODE`
   Require overall=pass, new_session=true, approval_gates=true,
   remaining_injected=false and stale_injected=false.

A no-retry scenario uses three executor launches and two contract generations;
exhaustion/validation add one handoff generation, generation failure adds none.
Mechanical verification and handoff validation make no model calls. Regeneration,
fallback or unexpected judge criteria can add calls. Inspect contracts before
approval, keep each stage separate, and report a cost estimate before any batch
of ten or more paid calls (STOP-3). No measured dollar cost is claimed here.

## Portable evidence for future demonstrations

Keep raw captures and temporary homes on the host, outside the checkout. Before
committing any future evidence, export a fresh portable copy (including future
pass-path two-session demos):

```
.venv/bin/python -m plugin.export_demo_evidence --source /tmp/lhm-DATE-exhaustion --out plugin/evidence/DATE-exhaustion
.venv/bin/python -m plugin.handoff_failure_demo check --scenario exhaustion --out plugin/evidence/DATE-exhaustion
```

Use the matching checker/scenario for the other demonstrations; for a pass demo
use `plugin.two_session_demo check`. The exporter replaces checkout, user home,
temporary home, workspace and evidence prefixes with `${REPO}`, `${HOME}`,
`${DEMO}`, `${CODEX_HOME}`, `${WORKSPACE}` and `${EVIDENCE}` consistently in
metadata, commands, logs and embedded contexts, including canonical path aliases.
It records the transformation and recomputes the saved-handoff validation hash
for exported bytes. Keep the unmodified raw capture for original-byte provenance;
the portable copy is an explicitly transformed artifact. Review exports for any
additional host-specific paths before committing. Do not resume an exported
capture: operational metadata is in the raw host capture. Existing committed
evidence, including 2026-10-23-two-session, stays unchanged.
