---
name: harness
description: Execute a LocalHarnessMaker contract injected by lifecycle hooks, including approval, verification evidence and focused re-instruction. Without an injected contract, follow the user's ordinary request.
---

When `HARNESS_CONTRACT` appears in context, display the goal, success-criterion
checklist, assumptions, reasoning effort with rationale, and estimated tokens
and USD cost before doing any work. Wait for the user to answer `approve` or
provide edits. Do not run implementation tools or change any file before approval.
Previously displayed estimates and assumptions remain subject to user correction.

`HARNESS_APPROVED` means the user approved the displayed contract. Follow its
scope and stop conditions. Actually run its verification commands and retain
their real exit codes and output. Do not infer a command's result from code.

At completion, report every success criterion in a table with its status and
evidence: command plus output, or the relevant file path. Mark criteria without
evidence as not done. A synthetic fixture verdict is not evidence of task success;
label it synthetic and keep actual missing evidence visible.

When Stop supplies a re-instruction, address only its unmet items and finish
again with updated evidence. It is a continuation of the approved contract,
not a new task or approval request. Respect the same stop conditions and retry
limit; never start a recursive Codex session to escape them.

For an explicitly routing-only `HARNESS_STUB=1` demonstration with no application,
respect that demonstration's no-tools scope and the fixture's unavailable-app
stop condition. Do not run commands against a nonexistent app. Show real criteria
as not done and fixture verdicts as synthetic; this exception never supplies
approval or evidence for an actual implementation task.

If there is no injected contract, behave normally. Do not invent an approval gate
or add harness files for unrelated work. Hook-owned `.harness/` metadata records
orchestration state; leave it to the hooks.
