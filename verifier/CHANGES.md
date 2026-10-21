# Verifier progress — 2026-10-21

The checker reads the last assistant final report using the Codex response-item
structure captured in both exec and TUI evidence linked by
`docs/hooks-contract.md`. Completion terms are mapped only to explicit criterion
IDs. Earlier reports, user messages, tools and commentary do not supply claims.
A failed mechanical check with a completion claim keeps its failing status and
evidence and receives reason `claimed_without_evidence`. Pass and unverifiable
outcomes retain their original reasons. Synthetic report fixtures now use the
measured record structure; a regression injects broken health-check outcomes.

`reinstruct.py` includes only verdict items whose status is `fail`, their
criterion positions, descriptions and one line of failure evidence. Messages
are bounded to 300 characters. Long descriptions/evidence are shortened; up to
three failed items are detailed, with a count of further failed items.
`HARNESS_MAX_ATTEMPTS` uses the hook's existing default of 3. At or beyond that
limit, or with no failed items, the message is null. Unverifiable items still
prevent overall pass and remain visible in the verdict; they do not generate
failed-item feedback.

Mixed contracts delegate only llm_judge criteria through
`python -m controller judge --criterion FILE --artifact WORKSPACE --backend BACKEND --out FILE`.
The subprocess uses the current interpreter, shell=False, piped input, a
120-second deadline, and a copied environment with HARNESS_NESTED=1. Backend
selection uses the hook's existing HARNESS_BACKEND default of codex_cli.
Offline schema-reference resolution validates the complete approved criterion
and judgment. Returned IDs, llm_judge evidence markers and accounting
relationships are checked. Valid status/reason/evidence are preserved exactly;
transport errors or malformed results become explicit unverifiable items.
All-judge contracts retain the required quality warning without model calls.
The verifier never imports controller.

Only the six tests that actually execute macOS Seatbelt skip when
CODEX_SANDBOX is set. This session exposes CODEX_SANDBOX=seatbelt. Mocked tests
and command rejection/profile tests still run; verifier/sandbox.py is unchanged.

## Verification

`.venv/bin/python -m pytest tests/verifier -q`: 125 passed, 6 skipped in 0.97s.
Coverage includes both captured transcript excerpts, explicit/negated/grouped
claims, claimed-without-evidence, CLI verdict output, bounded/exhausted
re-instruction, all judge statuses, exact reason/evidence preservation, full
criterion serialization, backend choice, copied nested guard, deadline,
malformed judgments, ID/marker/accounting rejection, transport errors, and
controller import independence. Judge subprocesses and command outcomes are
mocked. No network, nested Codex, live model, or sandbox-exec call ran.
`git diff --check -- verifier tests/verifier state/STATUS-verifier.md`: exit 0,
no output.

## Pending

Host verification remains required for real macOS isolation, FastAPI fixture
outcomes, controller judge integration, production hook continuation and
latency. The smoke helper now invokes live judge delegation for the unchanged
shared contract and must only run on an authorized host. validate-handoff,
review sampling, broader command support, bounded capture, complete sandbox
auditing and measured D-4 rules remain unfinished. No merge, staging or commit
was performed; the full suite is reserved for the pre-merge host check.

## Assumptions

- The user's three ordered priorities define this session's implementation scope; future dated deliverables remain on the STATUS list.
- Only explicit criterion IDs and completion terms in the last measured final report count; generic completion prose and semantic paraphrases are not inferred.
- "Failed items only" means status=fail. Unverifiable results remain overall failures but generate no failed-item re-instruction by themselves.
- The existing hook environment settings are reused; no shared CLI, schema, or hook changes are needed.
- The workspace is the artifact directory supplied to the judge. Missing before/after evidence must remain unverifiable according to the rubric.
- The captured format establishes current exec/TUI parsing only; resume/compaction variants and installed-wheel schema packaging remain unverified.
- No PR was requested. This summary and STATUS provide Assumptions for a later PR description.
