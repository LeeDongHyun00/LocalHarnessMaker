---
name: harness
description: Follow LocalHarnessMaker requirements, visible questions, deterministic completion evidence, one focused repair and an executor-written decision ledger. Retains historical contract instructions for v1/v2 demos.
---

When `HARNESS_REQUIREMENTS` appears, display the numbered table before work.
Ask every unanswered question and end that turn before changing any file.
Never assume an answer. The hook accepts explicit user JSON of the form
`{"answers":{"Q-1":"the user's answer"}}`; request that format when needed.
There is no generated-contract approval gate on this v3 path.

Follow exact named/protected files and configured checks. Report each row with
command/output or path/hash evidence. Missing oracles remain unverifiable.
Only an executed deterministic failure authorizes the single application
repair continuation; audit opinions and unverifiable rows do not.

In the separate verifier ledger continuation, write the requested schema-shaped
ledger with `validation=null`, decisions/rationale, fixed identifiers/paths and
open items. Do not edit application code in that continuation. Preserve the
application completion summary and evidence in the retained final response.
`HARNESS_LEDGER` is prior context validated against the current workspace.
Leave `.localharness/v3/` phase/accounting/validation files to their producers.

If a pin disables Luna, show the advisory and continue ordinary work without
claiming H3 validation, substituting another model or changing effort/settings.

The remaining instructions apply only to explicit historical v1/v2 demos
(`HARNESS_INTERFACE_VERSION=2` or routing-only `HARNESS_STUB=1`).

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
