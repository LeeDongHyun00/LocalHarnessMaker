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
6. Record a separate host two-session check of handoff injection and persisted
   hook trust. These are pending; neither the real-demo preparation nor the
   unit tests establish them.

This sandbox session prepared the scenario and real mode without running Codex.
