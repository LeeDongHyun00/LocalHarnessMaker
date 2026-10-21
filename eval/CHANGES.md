# Evaluation changes — 2026-10-21 offline session

New runner reports validate against the approved shared evaluation report
schema, including formats and runtime ID/count/cost/order/hash checks. The
provisional local schema is a compatibility reference only. Historical baseline
artifacts remain unchanged; legacy checkpoints require an explicit migration.
The eval CLI now prints the supplied output directory as frozen in version 1.

The tool-event access audit invalidates protected Codex-home, sibling-bridge,
repository-outside-workspace and private-grader accesses. Incomplete, missing,
unsupported and unresolved evidence is inconclusive and prevents grading.
Assistant-only path prose is not an access. Raw external streams and hashes
remain available; public review evidence is redacted.

Harness mode calls the frozen contract and verifier CLIs through injectable
bounded subprocesses, injects the validated contract, and resumes only on a
non-null bounded verifier re-instruction. Contract/verdict failures and observed
access stop the task before private grading. Tests mock model/control calls.

Public inventory now contains 100 single-session and 20 two-session unfrozen
drafts; the 119 new candidates need external graders and diversity/specification
review. No hidden task graders or live executor calls were created. The pending
list is `eval/GRADERS-PENDING.md`.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 55 passed, 2 skipped
(external grader configuration absent). Host-only checks remain pending.

## Assumptions

- Version 1 is approved and supersedes the previous STATUS's provisional-schema
  description; shared interfaces were not edited.
- Public draft preparation is authorized without private graders. Related family
  variants need review before the task set can be frozen.
- Unobserved pricing, control-call accounting and full claim denominators remain
  undefined. No quality/cost result follows from mock tests.
