# Verifier fixes — 2026-10-22

## Leader exit before inherited pipe EOF

A command could exit successfully while a background descendant retained stdout
or stderr. Waiting for communicate to reach EOF delayed cleanup until the full
criterion timeout and incorrectly produced an unverifiable timeout verdict.
The user reproduced this with real sandbox-exec after commit e927b73.

The shared command/judge runner now uses communicate in at most 50 ms slices,
which drain both pipes through Python's POSIX selector implementation, and polls
the direct child between slices. Once the child exits, its return code is saved,
its group is killed immediately, and remaining pipe output is drained for at
most 200 ms. If EOF still does not arrive, already captured output is retained
and the saved child exit code determines the result. Text output keeps Popen's
encoding/error policy and newline translation. Active children retain the
original absolute deadline, TERM/grace/KILL timeout handling, EPERM/ESRCH
fallback and final cleanup before verdict publication.

Four real Python process-tree cases exercise command-rule and judge transport
with direct exits 0 and 7 and grandchildren that inherit both pipes and sleep
for two seconds. With a one-second criterion deadline they finish within three
seconds, preserve exact output, pass for expected exit 0, preserve exit 7 as
failure, and confirm the known grandchild PID no longer exists. These run
without sandbox-exec, network, controller or model calls. Two real capture tests
check complete UTF-8 output on both pipes, and four injected cases check bounded
post-KILL drain without EOF in binary and text modes. Existing injected clocks
now account for each communication slice; deadline and shutdown regressions
remain covered. Real macOS sandbox-exec reproduction remains pending on host.

## macOS cleanup EPERM/ESRCH follow-up

The host process-tree check found intermittent killpg EPERM during timeout
cleanup. It replaced the original timeout with "cannot launch command", left
the group registered, and could raise again from the final shutdown scope after
the CLI had already printed its success path. The user reported no survivors,
but the exit code/stdout pair violated the CLI contract.

Group signaling now tolerates EPERM and ESRCH and falls back to Popen's
exit-checked direct-child signaling. A live known child still receives TERM,
the shared grace period and KILL, followed by bounded reaping. Already-exited
children are reaped without signaling their PID. Signal/exit races in the direct
fallback and OS errors while polling, reaping or closing pipes do not replace
the original timeout or shutdown. Unexpected group OS errors are diagnosed on
stderr and use the same fallback. A bounded reaping retry allows at most two
0.1-second direct-child waits.

Only an OSError from Popen construction is wrapped as LaunchError and reported
as "cannot launch command". Later communication errors are reported as
"command execution failed". Verdict serialization finishes inside the shutdown
scope, and writing the verdict and printing its path happen only after that
scope has finished cleanup successfully. Unexpected scope-exit failures return
2 with empty stdout and preserve any previous verdict file. Timeout/budget
verdicts still return 0 with exactly the path and newline. TERM/HUP/INT shutdown
still returns 2 with empty stdout.

Injected EPERM/ESRCH cases cover group TERM, probing and KILL, both 6- and
60-second budgets, TERM/HUP/INT shutdown, direct-child exit races, an already
exited child, judge timeout reasons, and publication after scope cleanup. Fake
trees retain a live direct child when group lookup fails; their descendants
model the host's already-exiting group. Tests use simulated time and no live
sandbox or model execution.

## Shutdown and verification budget

`verifier check` handles SIGTERM, SIGHUP and SIGINT across input processing,
verification and process cleanup. A shared owner tracks detached judge and
sandbox-command process groups. Shutdown and criterion timeouts send SIGTERM,
wait up to two seconds across all owned groups, then SIGKILL survivors and
perform bounded child reaping. Successful children receive immediate group
cleanup for leftover descendants. Shutdown exits 2 with a diagnostic on stderr
and no success path on stdout. Signal handlers are restored after the call.

Signals arriving during Popen are deferred until its PID is registered; signals
are not blocked across fork, so children retain their normal signal mask.
Repeated shutdown signals cannot interrupt teardown. No cleanup path uses an
unbounded wait or communicate. The sandbox command filter, environment and
Seatbelt isolation profile are unchanged.

HARNESS_VERIFY_BUDGET_SECONDS defaults to 450 and must be finite and positive
before any criterion runs. A monotonic deadline limits each command/judge timeout
to its existing timeout or the remaining budget minus a two-second cleanup
reserve, whichever is smaller. Criteria that cannot start receive unverifiable
items naming the budget. The schema-valid verdict still exits 0, and H3 retains
non-null feedback before retry exhaustion.

Injected runner, clock, signal and fake-tree tests cover both launch sites,
TERM/HUP/INT, timeout escalation, cooperative exit, normal-exit leftovers,
multiple groups sharing the grace period, launch-time accounting, signal delivery
during launch, exact CLI shutdown output, and timeout cleanup consuming the
budget before subsequent criteria. These injected lifecycle tests use simulated time.

## D-3 validate-handoff

Implemented the approved `python -m verifier validate-handoff --handoff HANDOFF`
command. It reads the input without writing, validates against the shared
handoff schema offline, and rejects criterion IDs present in both done and
remaining. Success prints the supplied path exactly, including relative path
spelling, followed by one newline. No --out flag is accepted.

Missing/unreadable files, invalid UTF-8/JSON, schema violations and contradictory
states exit 1. Validator infrastructure failures exit 2. Errors print only to
stderr. No contract, controller import or model call is needed.

## Earlier review fixes

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

Earlier M5 behavior (superseded by the shutdown protocol above): controller judge runs with shell=False, piped input/output, a copied
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

.venv/bin/python -m pytest tests/verifier -q: 254 passed, 6 skipped in 2.88s.
All six skips are the real macOS Seatbelt tests blocked by nested sandboxing.
The new plain-Python process-tree and pipe-draining tests ran here; no live
controller, model call or nested Codex ran.

The user reported Claude verified and committed the preceding EPERM fix as
e927b73: 250 passed on host including all six Seatbelt tests, zero processes
after SIGTERM, and valid exit-0 verdicts in five of five 6-second budget runs.
Those results predate this change. The new host repro found a background child
holding stdout still alive after 40 seconds; Claude must rerun it after this fix.
git diff --check -- verifier tests/verifier state/STATUS-verifier.md: exit 0,
no output.

## Pending

Host checks: real macOS leader-exit/inherited-pipe repro, timeout cleanup and CLI output/exit rerun,
Seatbelt rerun after this fix, real controller/Codex grandchild timeout cleanup,
FastAPI fixtures, live judge integration and plugin continuation/latency.
The user selected a 480-second outer plugin deadline and 450-second verifier
budget; Role 2 owns the concurrent plugin implementation. Host verification must
confirm actual Stop-hook timing and process-tree cleanup on macOS, including
controller/Codex descendants. Other roles' files are unchanged by this session.
Full-suite verification remains a host pre-merge task.

Broader command support, bounded capture, complete sandbox auditing,
human review sampling (`python -m verifier sample`) and measured D-4 rules remain unfinished.
The live controller handoff and Stop/SessionStart hook loop need host verification;
this session validates the checked-in reference, synthetic cases and controlled
plain-Python transport processes.
No network, nested Codex, live model, sandbox-exec, staging or commit ran.

## Assumptions

- The user's leader-exit/inherited-pipe priority supersedes Remaining order; human-review sampling remains pending.
- The bounded post-exit drain is 200 ms. Output retained after that bound may be incomplete if a descendant escapes the owned group or is unsignalable; the completed command's own exit code is preserved as requested.
- Each existing command timeout is 120 seconds; judge timeout remains configurable with a 120-second default. The new budget only reduces these deadlines.
- The two-second reserve covers graceful termination; post-KILL child waits are bounded to two 0.1-second attempts per direct child. Verdict validation/writing and scheduling have the remaining margin before the plugin's 480-second deadline.
- Contract-free runtime validation rejects done/remaining overlap. Contract membership, criterion coverage and artifact existence cannot be inferred from a handoff alone and are not checked. Same-state entries may describe multiple artifacts or remaining steps; no additional uniqueness constraint is imposed.
- Only explicit criterion IDs with completion terms in the last measured final report count; exception tails are conservatively unclaimed.
- Failed items in rule 6 include every status other than pass, as explicitly directed by the user. The three-detail/count-rest overflow stays unchanged.
- HARNESS_JUDGE_TIMEOUT_SECONDS and HARNESS_VERIFY_BUDGET_SECONDS are verifier-local configuration. No shared CLI, schema or hook interface changes are made.
- Cleanup reaches signalable owned POSIX groups. EPERM/ESRCH marks a group gone or unsignalable as instructed; only the known direct child can then be signaled safely. Host verification must confirm real descendants have exited. Descendants creating separate sessions need host verification; SIGKILL delivered directly to the verifier cannot run Python shutdown handlers.
- No PR was requested; this file and STATUS provide the change summary and Assumptions for a future PR.
