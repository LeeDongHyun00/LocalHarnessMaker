# Cross-role contracts and job status, 2026-10-25

Added Role 1 regressions in `tests/lead/test_cross_role_v3.py`. The real hook
adapter constructs argv; installed editable controller/verifier CLI entry points
run in process with only the Luna client mocked at the controller boundary.
An absent named file causes round 1 failure, one fixture repair passes round 2,
and ledger validation publishes an identical latest-ledger copy. Both unchanged
and changed audited final messages are covered. Every primary JSON artifact,
audit block and accounting line validates against the frozen local schemas.

The help regression parses all 11 signatures in AGENTS.md section 3.2, covering
10 unique command parsers, including historical operations and the pin CLI.
It checks exact flags, value arity and required/optional usage. Shared historical
and v3 `verifier check` modes use the union of their flags and intersection of
unconditionally required flags; the integration exercises the actual v3 mode.

| Verification | Result |
| --- | --- |
| `.venv/bin/python -m pytest tests/lead -q` | Exit 1: 151 passed, 2 failed in 40.18s; both failures expose the defect below |
| `make validate-schemas` | 11 schemas and 13 examples validated |
| `python3` inline STATUS archive/format and prompt audit | Five archives restore exactly to HEAD bytes; current blocks <=10 lines; six ordered job headings and all five prompt rules checked |
| `git diff --quiet -- controller verifier plugin schemas` | Exit 0: runtime packages and frozen schemas unchanged |

Role 4 defect: `verifier/v3_report.py:172` reads a supplied audit only when no
prior report exists. In the specified round-1 → audit → round-2 sequence, the
report silently retains `status=unavailable`, empty claims and no accounting
reference. The expected status is `complete` for the unchanged message or
`stale` with the original claims/hash/call for the changed message. Both tests
reach valid ledger publication before asserting this failure. Keep these as
ordinary CI failures; Role 4 must fix its merge without repeating the audit.
All 10 CLI-help cases pass; no argument drift was observed.

AGENTS.md now defines dated append-only job sections, a consolidator-owned current
state block and disjoint-path/worktree parallel jobs. All five STATUS files retain
legacy prose under History; migration dates do not date the historical work.
All five role prompts cap final reports at 40 lines and restrict README/CHANGES
edits to the change. Assumptions: this job consolidates the format migration;
the enabled pin is synthetic, and these offline checks establish no live hook,
installed-Codex, command-sandbox or provider compatibility.
