# Verifier fixes — 2026-10-22

H3: re-instruction includes every non-pass item, including unverifiable checks
and contract-quality warnings. It is null only for a passing verdict or at/above
the attempt limit. The existing 300-character format details up to three items
and counts the rest. The golden failure test compares the named criteria with
schemas/examples/verdict_fail.json. An exhaustive test covers all 243 status
mixes for five items at both remaining attempts and at exhaustion.

M3/M4: comma-separated criterion lists share their completion predicate.
Exception phrases (except, but, other than, apart from, besides, excluding)
stop claim extraction for the rest of that clause. Explicit per-item negatives
remain scoped, including “SC-1 completed, SC-2 not done”. Unmapped prose still
supplies no claim. An integration regression checks that an unclaimed failing
criterion retains its mechanical reason while a claimed failure receives
claimed_without_evidence.

M5: controller judge runs with shell=False, piped input/output, a copied
HARNESS_NESTED=1 environment and start_new_session=True. The verifier sends
SIGKILL to the entire process group and reaps the child after timeout, other
communication errors, and successful completion with possible lingering
children. A timeout remains unverifiable with its deadline in the reason.
HARNESS_JUDGE_TIMEOUT_SECONDS configures the finite positive deadline; the
existing default stays 120 seconds. Validation precedes any check/model call,
and the verifier never imports controller. Injected process runners, clocks
and group signals test cleanup without real sleeps or model calls.

The test environment now unsets HARNESS_MAX_ATTEMPTS and HARNESS_BACKEND.
Explicit regressions check their defaults of 3 and codex_cli with both unset,
the 120-second judge default, a configured deadline, and invalid deadlines.

## Verification

.venv/bin/python -m pytest tests/verifier -q: 151 passed, 6 skipped.
All six skips are real macOS Seatbelt tests blocked by nested sandboxing.
The earlier host run reported by Claude on 2026-10-21 passed all 131 verifier
tests and all 25 tests in tests/verifier/test_sandbox.py; another host run is
required after these changes. git diff --check -- verifier tests/verifier
state/STATUS-verifier.md: exit 0, no output.

## Pending

Host checks: Seatbelt rerun, real controller/Codex grandchild timeout cleanup,
FastAPI fixtures, live judge integration and plugin continuation/latency.
A cross-role decision must align the Stop hook's 40-second timeout, this
verifier's 120-second default, and controller codex_cli's 180 seconds per call
with up to three generation calls per command. Other roles' files are unchanged
by this session. Full-suite verification remains a host pre-merge task.

Broader command support, bounded capture, complete sandbox auditing,
validate-handoff, human review sampling and measured D-4 rules remain unfinished.
No network, nested Codex, live model, sandbox-exec, staging or commit ran.

## Assumptions

- The user's host-review priorities define this session's scope; later deliverables remain pending.
- Only explicit criterion IDs with completion terms in the last measured final report count; exception tails are conservatively unclaimed.
- Failed items in rule 6 include every status other than pass, as explicitly directed by the user. The three-detail/count-rest overflow stays unchanged.
- HARNESS_JUDGE_TIMEOUT_SECONDS is verifier-local configuration; deadline coordination requires a later cross-role decision. No shared CLI, schema or hook interface changes are made.
- Process-group cleanup covers descendants remaining in the judge's POSIX group; real controller/Codex behavior still needs host verification. Forced termination by the shorter outer hook remains part of deadline coordination.
- No PR was requested; this file and STATUS provide the change summary and Assumptions for a future PR.
