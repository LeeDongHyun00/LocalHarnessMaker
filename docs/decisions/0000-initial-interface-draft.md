# Initial interface draft

Date: 2026-10-21 (Asia/Seoul). Status: initial draft, not frozen.

The Role 1 First task explicitly requests repository initialization and the
first three schemas. No schemas or role STATUS files existed at session start.
Create this initial definition with `schemas/VERSION = 0`; reserve version 1
for the reviewed 2026-10-24 freeze. This is initial creation authorized by the
role assignment, not a revision to an existing interface.

Use closed objects and exclusive check variants to catch malformed controller
output. Represent `expected` as a required exit code with optional exact
stdout. Preserve the verifier's ability to warn about empty/all-judge contracts.
Reject overall passes containing failed or unverifiable items.

Use a contract-local string definition for the prompt fixture, keeping three
top-level artifact schemas. Reference verdict evidence and handoff contents
are synthetic. Controller code must compute actual effort, tokens, and cost.

Preserve existing experiments and the legacy `harness` implementation. Use a
root Makefile to recreate empty engineer-owned directories without writing
their implementation files. Initial pytest/CI scope is the five role suites.

Before freeze, resolve the missing judgment/report schema contracts, confirm
the validation-only CLI stdout convention, and review Role 2's installed-hook
evidence. Affected roles and remaining questions are listed in
[interfaces.md](../interfaces.md#freeze-prerequisites). No judgment or report
schema, CLI flag, or hook behavior is invented to close these gaps.

Future schema revisions require STOP-L1 approval and a version increment. The
Notion-aligned weekly plan and direction-change decision remain D-3 work; this
record does not replace `0001-direction.md` or claim a verified Notion plan.
