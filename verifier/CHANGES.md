# Real evaluation sampler correction — 2026-10-23

The sampler now accepts version-1 reports using the exact schema preserved in
decision 0003, alongside current version-2 reports. Repository-relative retained
paths under eval/reports/DIR_NAME are rebased into the supplied report directory.
Listed standalone verdict files remain supported, including day-1/day-2 names;
when absent for a task, its listed result.json supplies inline verdicts. Every
source is hash-checked and every verdict schema-validated. Standalone sources
have precedence to avoid counting both copies. Inline source indexes retain
separate sessions with identical attempt numbers. Final grading context always
comes from report.json and criterion items remain unchanged.

The explicitly requested optional --out writes the review outside a read-only
report directory. Its default remains DIR/verifier-sample.json, with unchanged
path-only stdout and exit-code conventions. README.md documents source paths,
version handling and inline source indexes.

## Verification

`.venv/bin/python -m pytest tests/verifier -q`: 566 passed, 8 host-only Seatbelt
skips in 6.79s. Synthetic retained-layout fixtures cover version 1, repository
paths, inline/standalone/coexisting verdicts, restarted session attempt numbers,
report grading provenance, deterministic rounds, unchanged inputs, hash/JSON/
schema/identity failures, and the module entry point with --out. Existing tests
retain version-2 reports, default output and containment/error coverage.

`.venv/bin/python -m verifier sample --reports
eval/reports/full-harness
--n 20 --out /tmp/lhm-verifier-review-78912e5238cc4e51a2bb6bfb13723f71.json`
returned exit 0, path-only stdout and
`verifier sample selected=20 available=142 seed=42` on stderr. All four report
task types are represented. Read-only SHA-256 comparisons confirmed report.json
and all 120 task result files were unchanged. The snapshot has 142 inline
verdicts and no standalone verdict files; the user-reported count was 147.

## Assumptions

- The user's explicit --out request authorizes this additive sampler flag; shared schemas, hooks and other CLI interfaces remain unchanged.
- Listed standalone verdicts take precedence per task; inline verdict_path/verdict_sha256 identify result.json and verdict_index identifies the zero-based entry. No unlisted verdicts are discovered.
- Final task grading is context for each sampled verdict, not evidence of per-attempt hidden grading. Its report value overrides any duplicated result.json grading.
- Version-1 schema loading reads the existing decision record without modifying shared files or synthesizing a metric. The source report is read-only; the review artifact is in /tmp.
- Only this worktree and its .venv were used. Eight host-only checks and the full-suite pre-merge run remain pending; no model/network calls, nested Codex, sandbox-exec, staging or commits ran.

---

# Complete claim observations — 2026-10-23

Every successful verifier check now writes VERDICT.claims.json beside the
unchanged verdict. Each real criterion has its claimed flag, first exact source
clause (whole table row), and final verdict status. Summary counts partition
claimed pass/fail/unverifiable and unclaimed items, supplying the denominator
missing from negative-only claimed_without_evidence reasons. One extraction
result drives both artifacts; no schema, CLI argument, stdout or exit-code
meaning changes. Sidecar writes occur before verdict writes, after cleanup;
failed invocations must not be consumed as a valid artifact pair.

The extractor now recognizes status tables/checklists, explicit collective
success statements, inclusive numeric ranges and distinctive description words.
Scoped negatives, exceptions, fenced/quoted text filtering and last-final-report
selection remain. Description matching is deterministic lexical overlap with
an ambiguity guard, not semantic inference. README.md and RULES.md document the
format, counts, matching and failure semantics for evaluation integration.

## Verification

`.venv/bin/python -m pytest tests/verifier -q`: 556 passed, 8 skipped in 5.78s.
The terminal summary reports 56 labeled synthetic final reports,
precision=1.000000, recall=1.000000, TP=75, FP=0, FN=0. Regressions cover all
claim/status combinations, quality/budget outcomes, no final report, judge
reason preservation, exact clauses, deterministic sidecars, standalone module
execution, output failures and cleanup before publication. All eight skips are
host-only Seatbelt checks. The first run exposed a test double that did not
forward the new internal observation keyword; it now forwards injected kwargs.

## Pending

Claude's host run on a live harness report and Role 5 ingestion remain pending;
the synthetic fixture does not measure live precision/recall or establish an
aggregate false_done_rate. Existing sandbox, controller/plugin integration and
full-suite pre-merge checks remain pending on the host. No network, nested Codex,
model calls, sandbox-exec, staging or commits ran. Only owned paths changed;
concurrent Role 3 files and the main checkout were left untouched.

## Assumptions

- The explicitly requested sidecar uses items with id/claimed/clause/status and a summary with the five requested counts; a .json suffix is replaced with .claims.json. No new shared schema is introduced.
- Successful computations, including fail/unverifiable verdicts, publish observations. Invalid inputs/internal computation errors publish nothing; partial/older files from failed artifact writes are not valid outputs.
- Only actual criteria count. Empty criteria produce zero counts; no final report means zero claims. Judged fail/unverifiable statuses are observed without rewriting their reasons.
- Description matching requires two content words (one for a one-word vocabulary) and a word unique among criterion descriptions. An affirmative statement supplies a claim even if a later statement contradicts it; retain the first supporting clause.
- The requested extractor work supersedes the previous IDs-only scope. Numeric ranges require known ascending same-prefix endpoints; explicit all-criteria statements with named exceptions exclude those criteria, while unmapped exceptions remain conservative.

---

# Verifier futile-retry fixes — 2026-10-23

Judged items now receive re-instruction only for status=fail. An unverifiable
judge response keeps its exact status, reason and evidence, leaves overall=fail,
and consumes no feedback slot or overflow count, even with a workspace cause.
This supersedes the judge-uncertainty retry policy in the earlier live-smoke
change below. Mechanical workspace-caused uncertainty remains actionable.

File/regex criteria reject prose, separators, absolute/drive-qualified paths,
parent traversal and globs before filesystem resolution. Rejected paths are
contract-caused unverifiable items with no retry. Plausible missing paths remain
workspace-caused and actionable; file_exists retains fail and regex retains
unverifiable. Shared schemas, CLIs and hook interfaces are unchanged.

## Verification

`.venv/bin/python -m pytest tests/verifier -q`: 476 passed, 8 skipped in 11.54s.
Regressions cover all three judge statuses at attempts 1–3, exact uncertainty
reason/evidence preservation, mixed feedback numbering/counts, invalid path
classification before filesystem access, and plausible missing path retries.

## Pending

Host verification must rerun the live proposed-system smoke with the real
controller/plugin/evaluation runner and all eight Seatbelt cases. Network,
nested Codex, live model calls and sandbox-exec were not run. Full-suite
verification remains pending before merge; no staging or commits were attempted.

## Assumptions

- Use a conservative single-token literal criterion path policy: filenames with whitespace, prose/operand separators or glob/expansion characters are rejected even if a filesystem could store them. Windows drive/root spellings are rejected as non-relative workspace paths.
- The user's measured futile-retry corrections supersede the earlier workspace-judge retry rule and role-prompt rule 6. Existing mechanical workspace retry behavior remains in place.
- This session uses only this worktree and its .venv. Other roles' paths and the main checkout remain outside the authorized edit scope.

---

# Verifier live-smoke fixes — 2026-10-23 (judge uncertainty policy superseded above)

Unittest discovery and local module/dotted/file targets now run through the same
Seatbelt dispatch as pytest. Discovery accepts -s/-p/-t and -v/-q/-b/-f/-k;
pytest additionally accepts -x, -k EXPR, -rA, --tb=short and -p no:cacheprovider.
Option operands are parsed by meaning, path containment includes symlinks,
shell operators remain rejected and the existing -c AST checks are unchanged.
The Seatbelt profile and environment are unchanged.

Re-instruction now selects status=fail and explicitly workspace-caused
unverifiable items. Internal cause categories distinguish workspace, contract,
verifier, transport and budget without changing verdict fields. Missing local
command input and valid judge uncertainty remain actionable; contract quality,
unsupported commands, exhausted budgets and failed/timed-out judge delegation
end retry feedback when no actionable items remain. Reasons retain specific
causes; valid judge reasons/evidence remain unchanged. RULES.md documents command
support, categories, conservative timeout handling and the existing feedback cap.
This supersedes the earlier blanket H3 non-pass retry policy below.

## Verification

`.venv/bin/python -m pytest tests/verifier -q`: 369 passed, 8 skipped in 4.74s.
New tests cover accepted options/targets, rejected operands/operators, symlink
escapes, identical sandbox dispatch, cause categories, mixed verdicts and
unverifiable-only retry decisions. Existing timeout/budget cleanup assertions
now require null feedback while retaining all lifecycle/output checks.

## Pending

Claude must run all eight Seatbelt cases on the host: the six existing checks
plus passing/failing unittest discover. Historical host evidence predates these
changes. Live evaluation/controller/plugin integration and full-suite pre-merge
verification remain pending. This session ran only verifier tests, with no
sandbox-exec, network, nested Codex, model calls, staging or commits.

## Assumptions

- Short option operands may be attached or separate; positional unittest discovery arguments use the same containment checks as -s/-p/-t. Discovery patterns are filename globs, not directory paths.
- A valid judge response is workspace review and keeps its reason/evidence unchanged. A command timeout alone cannot establish a workspace cause and does not retry; unknown causes also stop feedback.
- The user's actionable retry refinement supersedes role-prompt rule 6 and earlier H3 history. Shared schema, CLI and hook interfaces remain unchanged.

---

# Verifier changes — 2026-10-23

Judge delegation now forwards only child stderr records starting with
`control_call ` or `control_cli_events `, unchanged and in order. One flushed,
compact, sorted-key `judge_delegation` JSON line follows each attempted delegation.
Launch, natural exit and stderr completeness are tracked separately: nonzero
exits can retain complete accounting, while timeout, killed children, truncated
capture and missing control-call records cannot. Verdicts, stdout, existing CLI
flags, exit codes and judgment semantics are preserved. `verifier/README.md`
documents the exact protocol for Role 5.

D-3 `python -m verifier sample --reports DIR --n 20` validates report.json and
hash-pinned listed verdicts, then selects verdict attempts with seed 42 in rounds
across task types. The output records each item's exact status/evidence/reason,
task identity/type, attempt, verdict overall result and final report grading and
outcome. Missing grading remains null. Only the report and named verdicts are
read; grader sources, grading copies and logs are unnecessary. Successful stdout
contains only the generated verifier-sample.json path and a newline.

Claude's user-reported host results complete the earlier pending six Seatbelt
checks, macOS EPERM/pipe-holding grandchild cleanup (10/10, e927b73 and 7de2f99)
and live validate-handoff acceptance in plugin/evidence/2026-10-22-real. These
results were not rerun here. STATUS removes those checks from Remaining.

## Verification

`.venv/bin/python -m pytest tests/verifier -q`: 292 passed, 6 skipped in 3.94s.
The six skips are the existing host-only Seatbelt tests. Accounting tests use
mocked children for success, nonzero exit with two calls, partial timeout stderr,
no call records, launch failure, truncation, unreadable pipes, killed children,
shutdown flushing and interleaving with elapsed_seconds/budget cutoffs. Sampling
tests use synthetic schema-valid reports, including a real module-entry call,
without controller, grader or model calls.

## Pending

Host integration must verify the accounting records with the real controller and
Role 5 parser, sample a completed proposed-system report, and check real
controller/Codex descendants and hook deadlines. Full-suite verification remains
a host pre-merge task. No live calls, nested Codex, sandbox-exec, staging or
commits ran here; eval/, controller/ and plugin/ were not edited.

## Assumptions

- The user explicitly requested the D-3 command already named in the role prompt; existing shared schemas, check/validate-handoff flags and hook interfaces remain frozen.
- The unspecified sample destination/seed/format are DIR/verifier-sample.json, fixed seed 42 and documented review JSON. Up to n verdict attempts are selected, and an empty candidate pool produces an explicit empty sample.
- Listed verdict names use the existing runner's verdict-N.json and prefixed/archived forms; plain verdict.json is accepted. Paths must resolve inside the report directory; missing, duplicated, changed or invalid verdicts are input errors.
- A sample compares a verdict attempt with final task grading from report.json, without inferring a hidden-test result for that attempt. Invalid/timeout/error tasks may have null grading.
- Signaled child exits conservatively have incomplete accounting. Unterminated forwarded records receive a separator before the summary; their content is not parsed or rewritten.
- Exact host commands for Claude's latest results were not supplied; STATUS labels them as user-reported host evidence, not checks executed in this session.

---

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
