# Heredoc regression in literal-loop audit — 2026-10-23

Restrict loop discovery to shell syntax. Heredoc payloads/delimiters and comments
are excluded from discovery; quoted arguments already retain their raw word
boundaries. Original text still receives the same operand, expansion, private
marker, canonical-path and output checks as before literal-loop resolution.
This restores Python scripts passed through quoted heredocs without hiding
protected-path evidence or clearing previously unresolved expansions. Mixed
actual shell loops and heredoc/comment spans remain outside bounded unrolling.

Both supplied shapes are synthetic regressions: py_compile followed by nested
Python loops, and PYTHONDONTWRITEBYTECODE=1 with a case list and tuple-unpacking
loop. Tests compare complete audits against the pre-loop-resolution behavior,
cover item.started/completed pairs and native command/function/code-mode records,
and retain the literal parent-directory loop fixes. Additional data cases cover
tab-stripped/multiple/escaped heredocs, quoted arguments and here strings.

Claude's host comparison across 104 finished tasks is user-provided evidence:
three literal-loop tasks became clean, while Python heredoc scripts regressed.
Rechecking all 104 for clean audits with no private matches remains host work;
this session cannot inspect those logs or the real private root. Retained
reports and frozen tasks are unchanged; no model calls, staging or commits.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 943 passed in 83.58s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks eval/reports` both exited 0.

## Assumptions

- The retained host logs are unavailable here. Pre-change behavior is compared
  by disabling only loop transformation while retaining all legacy audit checks
  and identical synthetic log bytes; no host outcome is inferred from tests.

# Literal for-loop access audit — 2026-10-23

Resolve one bounded literal-list `for` loop without executing shell code. Each
`$name`/`${name}` filesystem word is expanded for every literal value and passed
through the existing canonical/private-root, symlink, traversal and recursive
access checks. Conditional operands are inspected even when absent. Executor
JSON, native command items, function calls and custom JavaScript wrappers share
the same parser.

Regression coverage includes the exact smoke command reading parent
`AGENTS.md` files, synthetic private-root traversal and symlink access (including
a later list value), and recursive access through an ancestor alias. Dynamic or
glob lists, command substitution, arithmetic, nested/while loops, mutations
before/inside/after the loop and directory-changing bodies remain inconclusive.
Unsupported embedded options, redirections and executable code also retain
uncertainty. No shell command from a captured record is executed by this audit.

Host re-audit of the retained second harness smoke and pilot B is pending.
No retained report, frozen task, shared interface or CLI flag changed. This
session uses only this worktree's `.venv`, synthetic private locations and
mocked model calls; the main-checkout baseline A remains separate.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 875 passed in 78.68s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks eval/reports` both exited 0.

## Assumptions

- The supplied smoke/pilot failures describe unavailable host evidence. These
  regressions establish parser behavior, not the retained runs' audit outcomes.

# Smoke accounting and publication fixes — 2026-10-23

Control accounting accepts symlinked ancestors above the runtime (macOS `/var`),
while rejecting links at/below the runtime and absolute/traversing manifest
entries. Hash-pinned control envelopes retain observed models and priced costs.

Published grading logs now allow only unittest identifiers/status and summary
lines. Full stdout/stderr and the combined grading log stay in the external
runtime. Synthetic failing/error/skipped graders verify that assertion source,
assertion/error messages and skip reasons appear nowhere in either the initial
published report directory or its regraded copy.

Generated JSON, log copies and artifact references use repository-relative
checkout paths. Validation resolves references from the repository root and
accepts historical absolute references. Regrading normalizes copied historical
review logs without changing the retained source; comparison source references
use the same path convention. External runtime references remain absolute.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 686 passed in 79.93s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks eval/reports` both exited 0.
Frozen tasks and retained reports remain unchanged. No model calls, real private
grader lookup, staging or commits. Host smoke verification remains pending.

## Assumptions

- The host smoke result is user-provided evidence; its external report is not
  available or inspected here. All new grader/executor coverage is synthetic.
- Relative published references use the repository root, while external runtime
  references retain their absolute locations for evidence verification.

# Capacity recovery and timeout continuation — 2026-10-23

Recognize only case-insensitive `at capacity` in structured `error` and
`turn.failed` events, including controller and forwarded judge stderr envelopes.
Retain executor segments and resume the same session after 60/120/300/600-second
waits, independent of attempt/retry/reinstruction limits. Control operations
archive interrupted evidence before rerunning. Exhausted recovery halts with no
task outcome and resumes from the same `--out`; capacity never becomes a failed
criterion, reinstruction or control CLI error. Checkpoints and run diagnostics
mark infrastructure recovery and waits; control recovery evidence is hash-pinned.

Zero tokens apply only to capacity refusals before any item event. Partial work
with missing usage remains unknown. Native cumulative token-count deltas retain
executor work across resumes; output already includes reasoning. Each control
envelope affects its own call, including interrupted envelope-only evidence with
measured operation latency. Final executor timeouts continue the task loop;
unclassified nonzero exits keep STOP-E1 and usage limits still halt immediately.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 678 passed in 79.26s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks eval/reports` both exited 0.
Mocked recovery tests cover both exact error events, one-wait success, exhausted
recovery and later resume, contract/verifier/handoff/day-2 operations, zero versus
unknown usage, native deltas, timeout continuation and unchanged usage limits.
No model calls, live private-root lookup, retained report edits, staging or commits.

## Assumptions

- The user's two observed capacity events define the entire capacity vocabulary;
  no other service-error wording or retry classification is added.
- This worktree is r5/harness-smoke at f844d27, with its own `.venv`; main's
  concurrent smoke and historical full-a-attempt1 evidence are untouched.
- Live validation and full-run measurements remain host work. Report schema and
  CLI flags remain unchanged; recovery classification is retained in artifacts.

# Harness accounting, configurations and run provenance — 2026-10-23

Price each hash-pinned controller/verifier `control_call` stderr record with the
eval price snapshot, including retries and codex_cli-to-cheap_api fallback.
Retain actual model/backend/status/latency and ignore controller USD. Delegation
completeness/count checks and missing model/tokens propagate unknown control
and total costs. Invalid tasks retain costs. Mechanical verification and
validate-handoff add no calls. Single observed control model fills metadata;
none or multiple models produces a warning and null. Operation sidecars retain
exit/deadline evidence and survive usage-limit and interrupt recovery.

Add smoke/full harness configurations with two reinstructions (three attempts
per day), reduce full B to 100 single-session tasks, and publish planning
estimates. The estimate guard accepts exact bundled NAME configurations with
NAME-estimate.md while retaining historical pilot/full mappings. Headline
harness cost comparison remains pending live measurement. Decision 0007 drops
local Gemma/QLoRA and parity measurement, assigns C a user-filled stratified
20-task subset, and compares handoff with A. No frozen tasks changed.

New checkpoints capture starting git commit and pricing snapshot ID. Reports
use the recorded commit, warn with both values on HEAD/snapshot drift, and
preserve build-time behavior for older checkpoints. Prices in report metadata
still identify the snapshot actually used to price the retained calls.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 621 passed in 57.81s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks eval/reports/pilot-a eval/reports/pilot-b`
both exited 0. Tests use mocked models and synthetic local graders only.

## Assumptions

- Role 4 will supply the exact judge forwarding/delegation records described by
  the user. This worktree does not include or modify that implementation.
- Mocked tests establish accounting/orchestration, not live compatibility;
  Claude runs the host smoke next. No model/network/private-root lookup occurs.
- Luna planning uses 5,000 uncached input and 1,000 output tokens per generation;
  executor planning uses pilot A's session average. Full B also shows its
  historical max-effort pilot alternative. Planning estimates are not measurements.
- Only eval-owned paths change in r5/harness-smoke at b9ac131. Main's running
  full-A process and worktree are untouched. No staging or commits.

# 0.163 audit compatibility and usage-limit recovery — 2026-10-23

Support the host smoke's line-9 `event_msg.thread_settings_applied` as non-tool
metadata. Validate its thread/settings envelope and nested permissions and
collaboration fields; scan the complete record for private markers, including
extra keys, aliases and canonical traversal. Other unknown kinds and malformed
settings remain inconclusive. Telemetry combines its applied model/effort with
turn_context, rejects conflicts and publishes both evidence sources. A synthetic
34-record fixture preserves the supplied native structure without user paths.

Usage-limit error/turn.failed events now halt the entire run as resumable
STOP-E1 infrastructure failures, with the original message/reset time on stderr
and no interrupted-task outcome or report. Detection also reads control CLI
stderr's nested control_cli_events, without changing controller/verifier code.
The runner makes no further call after observing the limit. Same-output recovery
resumes the active executor or pending control step and preserves completed days.
Interrupted control streams/partial outputs are archived, hash-pinned, redacted
and referenced by the eventual report; missing accounting remains null.

Regressions cover both native versions, full-record private-marker injections,
malformed settings, conflicting telemetry, the exact supplied usage-limit event
pair, CLI stderr/reset time, no-thread recovery, loop-wide halt, all six
two-session control stages, repeated limits and verifier reinstruction recovery.
Validation: `.venv/bin/python -m pytest tests/eval -q` — 596 passed in 56.24s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks eval/reports/pilot-a eval/reports/pilot-b`
both exited 0. Only synthetic graders/local grading subprocesses were used.

## Assumptions

- b04f9b0 contains the completed two-session work. Claude's uncommitted smoke
  report is retained unchanged and excluded from this commit plan.
- The supplied host smoke was invalid/inconclusive before day 2; mock regression
  success does not establish host compatibility. Claude reruns a fresh smoke.
- Control CLIs retain bounded execution and may perform their existing internal
  retry/fallback before returning. Eval detects their structured limit evidence
  on return; no frozen interface or other-role implementation is changed.
- Reset text is relayed verbatim; no timezone or missing usage is inferred.
  No model calls, private-root lookup, staging or commits occurred here.

# r5-full-001 and r5-full-002 — 2026-10-23

The combined uncommitted change runs frozen two-session tasks as two fresh
sessions in one public workspace. Day 2 receives exact day2.md bytes; harness
contracts arrive separately through developer_instructions. Runner-owned
handoff generation and validation use the frozen CLIs. Both days retain native
and event audits, settings, distinct identities, delivered-prompt hashes and
exit hashes before one trusted grade. Attempts and executor costs sum once.

Evidence publishing uses the runner's hash manifest, excludes workspace files
and refuses symlinks. Preexisting control outputs invalidate the task with
runner_control_file_preexisting; modified pinned files remain control errors.
Only manifest-pinned, numerically named verdicts can feed handoff generation.
Forged verdict-99.json and verdict-final.json cannot replace verdict-1.json.

Hard-crash recovery resumes the active session without repeating completed days.
An audit-clean day-1 timeout/error can continue to day 2. Regrade preserves final
executor timeout/error outcomes, retains invalid pre-day-2 tasks and grades the
remaining eligible tasks without executor calls. Missing handoff observations
invalidate rather than disappearing from quality denominators.

Decision [0006](../docs/decisions/0006-codex-version-policy.md) governs version
provenance. Full A/B and the two-session smoke select codex-cli
0.163.0-alpha.11.1; historical 0.162 pilots are diagnostic planning inputs only.
Every native session must supply matching cli_version evidence. Missing or
mismatched evidence invalidates that task and retains costs while report.json
still records every task. A pre-session version change still halts the run.
The comparison helper refuses mixed codex_version reports. New versions require
a hook probe and one-task audit smoke before a large run; the supplied 0.163
host hook probe passed, while audit smoke/production verification remain pending.

Full configurations select all 120 frozen tasks, seed 0 and pilot retry limits;
two-session processes get 1200 seconds, others 600, grading 20. The published
estimate budgets 140 sessions each, USD 4.0960136/6.0263112 and approximately
56/84 plan percentage points. STOP-3 also budgets controller retries/fallbacks
and judge criteria: one no-retry two-session harness task already bounds 11
paid calls. The failing guard test now clears an obsolete task timeout when it
changes task selection; loader validation is unchanged. No full run is approved.
A bounded per-event audit cache preserves exhaustive detection while avoiding
repeated identical protected-path resolution in large-call events.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 537 passed in
46.12 seconds. `git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks eval/reports/pilot-a eval/reports/pilot-b`
both exited 0.
All calls are mocked except local synthetic grading subprocesses. No network,
model calls, private-root lookup, staging or commits occurred. Host measurements
and five manual pilot-A reviews remain pending.

## Assumptions

- Frozen task content and historical pilot artifacts remain unchanged.
- Pilot session token/cost averages and supplied plan deltas are estimates for
  both days; they are neither new quality evidence nor spending caps.
- Host compatibility of contract delivery, real native capture and production
  recovery remains unverified here. The supplied probe result is host evidence.
- Complete control-call accounting, done-claim denominator and paired parity
  remain unknown; absent accounting is never inferred as zero.

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


## 2026-10-22 host-review remediation

H2: retained grading copies now live outside executor runtimes. All sibling
runtimes, including prior runs, and the retained grading location are audited.
Four mocked cross-task/cross-run tests cover glob and absolute copy reads.
H1: shell parsing tracks directories, resolves concrete globs/quotes, handles
event workdir/cwd, compares paths without case, and rejects unresolved operands.
Recursive ancestor searches are detected. Hashed normalized grader lines detect
tool-output disclosure independently of command construction. Ordinary workspace
commands remain clean. Dynamic unlogged execution still requires host review.
M1: checkpoint results use the same redaction as public result files; audit
matches retain labels instead of raw candidate paths. An integration test scans
every file under --out for both source-root spellings.
Low items: transport retries reset for each reinstruction segment; post-call
report/usage ValueErrors become internal ReportError; unresolved guards have
direct cases; bootstrap tests require seed-sensitive intervals; the shim test
resolves the actual unchanged relative reference from the shim file's URI.

| H1 command case | Before | After |
|---|---|---|
| cd /, root without leading slash | clean | access_detected |
| cd .. twice | clean | access_detected |
| cd ../.. | clean | access_detected |
| glob hiding root suffix | clean | access_detected |
| quoted path splitting | clean | access_detected |
| ~user path | clean | inconclusive |
| find ancestor -exec cat | clean | access_detected |
| grep -rh ancestor | clean | access_detected |
| uppercase home/.CODEX | clean | access_detected |
| cd ~, relative .codex | clean | access_detected |

Evidence: `PYTHONPATH=. .venv/bin/python /tmp/lhm_compare.py` compared the
HEAD audit module with the working module, using synthetic roots only; all ten
before results were clean. Permanent parameterized tests retain every case.
`.venv/bin/python -m pytest tests/eval -q`: 88 passed, 2 skipped, 1 xfailed.

STOP-1 / M2 proposal for Role 1: allow aggregate validity=invalid with an
explicit halt/count reason when the reported task IDs differ from the configured
task set, even if all attempted tasks are valid. Keep audit-clean failures valid
quality samples and preserve their costs. The frozen schema's allOf currently
requires status=valid in this case. No schema field is needed, but revising this
frozen invariant requires user approval, a decision record and schemas/VERSION
increment. No shared or other-role path was changed. The strict xfail reproduces
STOP-E1 after 1 of 2 tasks; M2 is not fixed.

## Assumptions

- Keep grading copies in one retained temporary location instead of deleting
  files under STOP-4; all tasks audit that location and other temporary runtimes.
- A concrete wildcard expansion can establish access; unknown expansion stays
  inconclusive. Named-user tilde expansion is deliberately unresolved.
- Resolve the compatibility shim relative to its actual URI using an offline
  registry; its existing relative $ref needs no shared-schema modification.
- This session supplies no live model, isolation or production measurement.

## 2026-10-22 wrapped-command regression

Unwrapped literal executor shell displays with shlex before examining the
inner command. Quote provenance now belongs to each inner argument, so a
wrapper closing quote or another argument's quotes cannot invalidate a path.
Workspace-bounded globs are resolved even without matches; concrete symlink
matches still undergo protected-path checks. Glob/filter option values are
excluded from filesystem operand analysis. Recursive start paths, including
implicit current directories, remain audited. make variable values retain
their own quote provenance for the observed TEST_PATH corpus case.

The fixture contains 42 distinct non-heredoc commands selected from the
59-entry host corpus. It records source indices and the source SHA-256.
The external design-note path was rewritten as fixtures/notion-design.md;
all referenced paths are synthesized inside a temporary workspace. Commands
are replayed as JSON log records and are never executed. No absolute user,
home or private-root path was copied into the fixture.

| Fixture audit status | Before (5faf49d) | After |
|---|---:|---:|
| clean | 4 | 42 |
| inconclusive | 38 | 0 |
| access_detected | 0 | 0 |

The table below uses the existing prompt-file read for each shell wrapper.

| Wrapper | Before | After |
|---|---|---|
| /bin/zsh -lc single quotes | inconclusive | clean |
| /bin/zsh -lc double quotes | inconclusive | clean |
| /bin/bash -lc single quotes | inconclusive | clean |
| /bin/bash -lc double quotes | inconclusive | clean |
| sh -c single quotes | inconclusive | clean |
| sh -c double quotes | inconclusive | clean |

Per-case results use C=clean, I=inconclusive and D=access_detected.
Wrapped columns use the executor's `/bin/zsh -lc` display. Workspace
files exist for the requested glob examples; unmatched glob cases are
included separately. Therefore some unwrapped glob cases already audit
clean before this patch, while their wrapped forms are inconclusive.

| Ordinary command | Before unwrapped | Before wrapped | After unwrapped | After wrapped |
|---|---|---|---|---|
| `cat prompts/01-tech-lead.md` | C | I | C | C |
| `ls *.py` | C | I | C | C |
| `cat src/*.py` | C | I | C | C |
| `pytest -q tests/test_*.py` | C | I | C | C |
| `find . -name '*.py'` | C | I | C | C |
| `rg -n def -g '*.py' .` | C | I | C | C |
| `rg --files -g '*.py'` | C | I | C | C |
| `rg --glob '*.py' def .` | C | I | C | C |
| `rg --glob='*.py' def .` | C | I | C | C |
| `find . -iname '*.PY'` | I | I | C | C |
| `find . -path './src/*.py'` | C | I | C | C |
| `grep -r --include='*.py' def .` | C | I | C | C |
| `grep -r --include '*.py' def .` | C | I | C | C |
| `ls unmatched*.py` | I | I | C | C |
| `cat src/missing*.py` | I | I | C | C |
| `ls missing*/file` | I | I | C | C |
| `cd src && cat *.py` | C | I | C | C |

| Protected or unresolved case | Before unwrapped | Before wrapped | After unwrapped | After wrapped |
|---|---|---|---|---|
| cd / | D | D | D | D |
| cd .. twice | D | D | D | D |
| cd ../.. | D | D | D | D |
| root-name glob | D | I | D | D |
| quote-split path | D | I | D | D |
| ~user | I | I | I | I |
| find -exec | D | I | D | D |
| grep -rh | D | I | D | D |
| uppercase home/.CODEX | D | D | D | D |
| cd ~ | D | I | D | D |
| absolute private path | D | D | D | D |
| ../ traversal | D | D | D | D |
| cross-task/run absolute retained copy | D | D | D | D |
| cross-task/run retained-copy glob | D | D | D | D |
| external retained glob | D | D | D | D |
| external runtime glob | D | I | D | D |
| decode-and-execute | I | I | I | I |
| internal split path unresolved | I | I | I | I |
| ancestor find | D | I | D | D |
| ancestor rg --files | D | I | D | D |
| ancestor grep -rh PATTERN | D | I | D | D |
| ancestor ls -R | D | I | D | D |
| ancestor du | D | I | D | D |
| ancestor tar -cf archive.tar | D | I | D | D |
| ancestor rsync -a | D | I | D | D |
| ancestor cp -r | D | I | D | D |
| private-line fingerprint | D | D | D | D |

The external retained/runtime glob rows correspond to
`cat ../../lhm-retained-grading/grading-*/test_*.py` and
`cat ../../lhm-eval-*/workspace/solution.py`. Cross-task and cross-run
integration tests also cover absolute and glob reads, both wrapped and
unwrapped, requiring an invalid task, no grading, and aggregate invalidity.

Evidence: `PYTHONPATH=. .venv/bin/python /tmp/lhm_compare_wrappers.py`
compared the 5faf49d audit snapshot with this patch using synthetic roots;
42 fixture results changed from 4 C / 38 I to 42 C / 0 I. Additional
replay checked all three wrappers with both quote styles: I to C in all
six cases. The baseline snapshot was byte-compared with git show 5faf49d.
`.venv/bin/python -m pytest tests/eval -q`: 306 passed, 2 skipped, 1 xfailed.
The M2 strict-xfail function, including its decorator, was AST-compared
with 5faf49d and is unchanged. M2 STOP-1 remains open.

Pending host verification: replay full installed-version event streams
and confirm real executor/resume, process termination, nested guards and
sandbox behavior. No nested Codex, live model/API, network or macOS
sandbox-exec call was made. Dynamic execution retains the documented
caveat; unknown variable expansion and decode-and-execute stay unresolved.

### Assumptions

- The 42 distinct non-heredoc corpus commands provide a representative
  regression fixture; replaying all 59 live captures remains a host check.
- A bounded glob with no matches is resolved for auditing even if the
  actual shell command would fail; audit cleanliness does not imply
  command success.
- Optional HOME expansion was left unchanged; only literal shell
  unwrapping, operand quoting and workspace glob/pattern handling changed.


## 2026-10-22 approved recovery and grader validation

M2 now halts before report construction, exits 2 through the existing CLI, and
prints STOP-E1 with attempted/configured counts on stderr. Checkpoint and run
diagnostics survive; the same output directory resumes and publishes only the
complete configured task set. The strict xfail was replaced with halt/recovery
and CLI stream/exit tests. The earlier schema-change proposal below is superseded
by the approved no-report decision; no shared schema or CLI changed.

The task-set digest reads only `git ls-files` public inputs and private grader
content hashes. Ignored caches and untracked generated files cannot enter it;
tracked edits still change the digest. Missing/symlinked tracked inputs fail
validation. Public workspace files were inspected as text only; every grading
execution used independent copies.

The standalone `python -m eval.runner.validate_graders --private-root
"$PRIVATE_ROOT" --tasks all` validates through the runner's `grade()` function.
References are private overlays, never included in grader sources or executor
workspaces. Output contains task IDs, counts and hashes only. All 120 tasks
failed on untouched copies and passed with references applied: 598 test methods,
155 passed/443 failed on original copies, 598 passed/0 failed on reference copies.
The existing bug-chunk-tail grader passed revalidation unchanged (0/3 original,
3/0 reference). Per-task counts and every grader SHA-256 are published in
`eval/GRADERS-PENDING.md` without locations or test contents.

Public task review retained the 25 related families, 100 single-session tasks
and 20 two-session tasks. It clarified observable submission requirements:
bug fixes require at least one public unittest method; feature and constrained
refactoring variants require at least two; multiple-requirement and two-session
variants require at least three. This makes regression-test delivery explicit,
including for refactoring originals whose behavior already passes. Graders check
both refactoring entry points and input preservation, without prescribing the
helper implementation. Multiple-requirement variants also check the requested
public docstring. Two-session graders check both APIs, batch order, empty batch,
input preservation, exception identity and handoff verification evidence.
Structural helper extraction and regression coverage quality remain human review
items; behavioral validation alone does not certify them. Family correlations
remain relevant to later metric interpretation.

Every changed public task file is enumerated below. For each task, `prompt.md`
adds the submission requirements; `expected.json` replaces pending three-group
metadata with five external groups and their pass condition; `meta.json` records
specification review/external validation while retaining `frozen=false`.
The listed `day2.md` files additionally clarify final regression coverage and
handoff verification evidence. No public workspace source or existing task ID
was changed. Bug-chunk-tail public files are unchanged.

| Task directory under eval/tasks/ | Changed files |
| --- | --- |
| bug-fix-adjacent-runs | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-balanced-brackets | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-clamp-values | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-common-prefix | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-flatten-once | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-inclusive-range | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-interleave | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-interval-union | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-invert-groups | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-last-index | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-line-endings | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-merge-counts | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-pairwise-edges | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-parse-pairs | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-partition-sign | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-prefix-sums | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-rotate-left | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-round-robin | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-select-columns | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-stable-unique | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-strip-prefix | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-unique-permutations | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-window-slices | `prompt.md`, `expected.json`, `meta.json` |
| bug-fix-word-counts | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-adjacent-runs | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-balanced-brackets | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-clamp-values | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-common-prefix | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-flatten-once | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-inclusive-range | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-interleave | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-interval-union | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-invert-groups | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-last-index | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-line-endings | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-merge-counts | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-ordinal-labels | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-pairwise-edges | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-parse-pairs | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-partition-sign | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-prefix-sums | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-rotate-left | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-round-robin | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-select-columns | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-stable-unique | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-strip-prefix | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-unique-permutations | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-window-slices | `prompt.md`, `expected.json`, `meta.json` |
| constrained-refactoring-word-counts | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-adjacent-runs | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-balanced-brackets | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-clamp-values | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-common-prefix | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-flatten-once | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-inclusive-range | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-interleave | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-interval-union | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-invert-groups | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-last-index | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-line-endings | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-merge-counts | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-ordinal-labels | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-pairwise-edges | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-parse-pairs | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-partition-sign | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-prefix-sums | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-rotate-left | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-round-robin | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-select-columns | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-stable-unique | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-strip-prefix | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-unique-permutations | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-window-slices | `prompt.md`, `expected.json`, `meta.json` |
| feature-plus-test-word-counts | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-adjacent-runs | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-balanced-brackets | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-clamp-values | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-common-prefix | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-flatten-once | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-inclusive-range | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-interleave | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-interval-union | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-invert-groups | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-last-index | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-line-endings | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-merge-counts | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-ordinal-labels | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-pairwise-edges | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-parse-pairs | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-partition-sign | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-prefix-sums | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-rotate-left | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-round-robin | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-select-columns | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-stable-unique | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-strip-prefix | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-unique-permutations | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-window-slices | `prompt.md`, `expected.json`, `meta.json` |
| multiple-requirements-word-counts | `prompt.md`, `expected.json`, `meta.json` |
| two-session-adjacent-runs | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-balanced-brackets | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-clamp-values | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-common-prefix | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-flatten-once | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-inclusive-range | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-interleave | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-interval-union | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-invert-groups | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-last-index | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-line-endings | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-merge-counts | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-pairwise-edges | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-partition-sign | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-prefix-sums | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-rotate-left | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-stable-unique | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-strip-prefix | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-window-slices | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |
| two-session-word-counts | `prompt.md`, `expected.json`, `meta.json`, `day2.md` |

## 2026-10-22 mutation and validation hygiene

Strengthened 23 external graders after reviewing all survivors from a deterministic
1,985-mutant offline pass. Tests remain limited to public prompt/expected behavior;
public tasks, workspaces and expected test-group counts are unchanged. The initial
pass killed 1,891 mutants. Review identified 23 behavioral gaps and 71 equivalent
mutants; equivalence rationales and generated source remain private.

Added `--mutants N` to the standalone grader validator, covering all requested AST
operator families, both application/regression overlays, exact runner grading,
passing reference controls, bounded deadlines, private review records and a 90%
per-task non-equivalent kill threshold. Reference/specification changes invalidate
recorded equivalences. Mutation stdout contains task IDs and counts only.

Validation/mutation runtimes and grading copies now stay under the explicitly
supplied private root and are cleaned on exit. Evaluation retention is unchanged.
Synthetic runner tests use pytest temporary storage. Claude transcript storage is
protected alongside Codex storage, with alias, case-insensitive, symlink, denied
access and recursive ancestor coverage.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 332 passed. All 120 untouched
and reference task pairs validate: originals 155 passed/443 failed, references
598 passed/0 failed. `GRADERS-PENDING.md` changes only 23 rows' grader hashes;
method/group counts remain unchanged. Publication checks found no private path or
task-specific grader line in 550 public evaluation/test/status files. No executor
or model calls were made; no freeze document was written.

Assumptions: the user's earlier sampled rates describe a different, smaller mutant
population. Report them as the supplied before values; the new deterministic pass
covers every generated mutant, including submitted-test overlays. Passing test-only
mutations are equivalent only when the specified application behavior and submitted
test requirements remain satisfied. Behavioral grading still leaves structural
helper extraction and regression quality for human review.

The final mutation command exited 0 for all 120 tasks: 1,914 killed, 71 recorded
equivalent, zero survived/errors. Every task kills 100% of its non-equivalent
mutants (raw aggregate 1,914/1,985). The expanded initial/final candidate populations
are identical; this session's raw count improved from 1,891 to 1,914 killed.

| Task ID | Supplied sampled before | Expanded after, excluding equivalents | Killed / equivalent |
| --- | --- | --- | --- |
| multiple-requirements-clamp-values | 0.55 | 1.00 | 12 / 6 |
| two-session-clamp-values | 0.55 | 1.00 | 13 / 6 |
| bug-fix-clamp-values | 0.67 | 1.00 | 8 / 2 |
| feature-plus-test-clamp-values | 0.71 | 1.00 | 10 / 4 |
| feature-plus-test-ordinal-labels | 0.73 | 1.00 | 24 / 3 |
| multiple-requirements-ordinal-labels | 0.73 | 1.00 | 25 / 3 |
| constrained-refactoring-clamp-values | 0.75 | 1.00 | 12 / 4 |
| constrained-refactoring-ordinal-labels | 0.82 | 1.00 | 26 / 3 |
| bug-fix-last-index | 0.83 | 1.00 | 11 / 0 |
| feature-plus-test-last-index | 0.83 | 1.00 | 12 / 0 |
| multiple-requirements-last-index | 0.83 | 1.00 | 12 / 0 |
| bug-fix-inclusive-range | 0.86 | 1.00 | 14 / 1 |

Reproduction commands (PRIVATE_ROOT is supplied explicitly by the trusted caller):

```sh
.venv/bin/python -m eval.runner.validate_graders --private-root "$PRIVATE_ROOT" --tasks all --mutants 10000 > "$PRIVATE_ROOT/mutation-after-full.jsonl"
.venv/bin/python -m eval.runner.validate_graders --private-root "$PRIVATE_ROOT" --tasks all > "$PRIVATE_ROOT/validation-mutation-final.jsonl"
```

The second command exited 0 with 120 valid/0 invalid and task-set SHA-256
`ea8e9a6df55b22a01fc87a66298262f3cd7e738f8af8ca0853d3f877f5b9f12f`.
Host review and Role 1 freeze recording remain pending. No staging or commit was
attempted; the full repository suite remains a future pre-merge check.

## Version 1 task-set freeze preparation — 2026-10-22

Set `frozen=true` in all 120 `eval/tasks/*/meta.json` files, retaining
`version=1`. A comparison against HEAD verified that only the freeze flag
changed in each metadata file and no other public task file changed. No grader,
reference, inventory hash or task specification was changed. The user authorized
this freeze after Claude's host verification in `80205d3` and `ad7d7be` and
independent mutation testing with no behavior-changing survivor.

The runner now rejects any selected task without an exact boolean true freeze
flag before version probing, private-grader loading, output creation or model
execution. This also applies to checkpoint recovery. No CLI, schema or hook
interface changed. Inventory tests require all 120 tasks to remain at version 1
and frozen; synthetic runner tests cover mixed frozen/unfrozen task sets,
missing flags and non-boolean flags without invoking external processes.

The prior task-set digest predates this metadata change and is not the final
freeze digest. Claude must run `python -m eval.runner.validate_graders` with the
private root on the host, then pass the final digest to Role 1 for
`docs/eval-freeze.md` (SC-2 remains pending that record). The pilot cost estimate,
approval and 10-task A/B pilot remain pending. No executor, controller, judge,
nested Codex or network call was made; no staging or commit was attempted.

Assumptions: the user's report of independent host verification is the basis for
freezing; private validation cannot be repeated in this sandbox. Historical task
review fields remain unchanged under the metadata-only instruction.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 336 passed in 33.41s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` — exit 0.

## 2026-10-22 ten-task pilot preparation

Replaced the offline price placeholder with snapshot
`openai-standard-short-2026-10-22-v1`, using the user's supplied Claude host fetch
of OpenAI pricing. The existing schema-compatible source string records the URL,
Standard tier, 272K context boundary and absence of a provider version/date;
checked_on is 2026-10-22. Sol input/cache/output rates are 2/0.10/10 USD per
million, Luna 0.10/0.01/0.50. Existing per-call accounting feeds totals and metrics
from this snapshot, bills cached and reasoning tokens once, and preserves null
for unknown models/tiers, long context or incomplete usage. Explicit native tier
evidence overrides the documented Standard default assumption.

Added pilot-a/pilot-b configs with ten identical single-session tasks from ten
families, deterministic 3/3/2/2 type quotas, seed 0, pinned CLI, zero retries,
600-second executor deadlines and harness off. Only effort differs (medium/max).
The exact bundled configs with their published estimate pass the existing paid
batch preflight and print the estimate to stderr; other large batches still
fail. This is preparation, not pilot approval. The estimate reports ten calls
per config, $0.178896 for A and illustrative $0.231296 for B at 2x output, plus
cache/output sensitivities. No maximum cost or plan-percent prediction is claimed.

Existing telemetry kept native token_count snapshots but aggregated attempts.
Added per-attempt tokens and timestamped primary used_percent before/after
observations to task results and run-diagnostics, without changing the frozen
report schema. Missing before/after observations remain null; first observed
inside the process is separately labeled, and after means last in-run sample.
Account rounding/concurrency still prevents an exact per-task consumption claim.

The user supplied final freeze commit 7cdaf3b and full-set digest
b78913b04280f6696d419d2afdc96b152675973d82f05199ddef848986285d1f,
now recorded by Role 1 in docs/eval-freeze.md. This supersedes pending-freeze
notes above. No public task, historical report, shared interface or other role's
path changed. Existing selected-task hash semantics are documented in the
estimate; the full frozen population hash is retained separately there.

Assumptions: trust the supplied host price fetch in this offline session;
Standard short context is the CLI baseline absent conflicting evidence; one
historical task is only a planning proxy; max uses more output and 2x/5x are
illustrative; zero retries bounds the initial batch. Claude must run approved
pilots on the host, retain evidence, review five A samples and obtain approval
before full measurement. No executor/controller/judge/model call, private-root
lookup, network call, staging or commit occurred here.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 342 passed in 19.41s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks` — exit 0. The old placeholder-cost assertion
was updated to verify the snapshot's computed executor/accounting/metric value.

## 2026-10-22 native-session pilot audit remediation

The user reports that Claude's host pilot A at d38a5da produced ten invalid,
ungraded tasks, each reporting unsupported `world_state` at native line 7.
The supplied retained session was read only to inspect its record structure.
This session did not rerun, rewrite or grade `eval/reports/pilot-a/`.

The audit now accepts and checks the basic shape of native `world_state` and
`token_usage_record`. Full record text, including nested keys, is scanned for
private markers and canonical aliases. A disclosure explicitly reports that
the private location reached executor context. Unknown top-level/native item
kinds and unresolved operands remain inconclusive.

Native custom calls were already recognized, but their `input` was not parsed
for shell operands, and tools nested in `event_msg.item_completed` were skipped.
The audit now inspects both, decodes literal shell/patch calls in native `exec`
JavaScript without execution, resolves patch/change paths and command arrays,
and fingerprints tool inputs as well as outputs. Unsupported dynamic custom
code stays inconclusive. Assistant prose remains excluded from access checks.

Each task writes a redacted `access-audit.json` with all errors/matches, including
errors after unknown records and errors accompanying detected access. Results
retain the same audit; the shared report references the artifact and gives an
explicit metadata disclosure reason without a schema or CLI change.

Added a synthetic 33-record JSONL fixture preserving the supplied session's
record order, containers and categorical discriminators. Task text, identities,
paths, timestamps and numeric content are synthetic. Regressions cover a clean
fixture; private paths in both metadata kinds, custom arguments and outputs;
keys/encodings/traversal/symlink/grading-copy aliases; argument/output fingerprints;
shell, patch and file-change operands; malformed metadata; unknown kinds; and
complete persisted diagnostics preventing grading.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 385 passed in 23.65s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks` — exit 0. No model/executor/controller/judge
call, network call, private-root lookup, staging or commit occurred.

Assumptions: the supplied host session is structural evidence for the pinned
CLI only; arbitrary new formats remain unsupported. Usage metadata acceptance
does not change token accounting. Claude will rerun pilot A on the host and
decide how to retain the old report; a passing offline suite is not a measured
pilot result. The user reports the previous plan cost as about one percentage
point of the weekly window; no new plan consumption was measured here.

## 2026-10-22 fingerprint false-positive remediation and offline re-audit

The user reports Claude's host verification of the native-record fix (385 tests
passed), followed by a false-positive pilot A re-audit: an executor-authored
`file_change` matched shared grader boilerplate. This supersedes the preceding
section's argument-fingerprint behavior. Fingerprints now inspect only command
`aggregated_output` and function/custom tool outputs. Path and operand checks
continue inspecting inputs, patches, file changes and native metadata.

Hidden line selection now requires a number/string literal absent from all
public task prompts, day-2 prompts, expected/meta JSON and workspace files. It
also excludes publicly present normalized lines, docstrings, module entry guards
and unittest launchers. Decoded string/numeric equivalents and conservative
substring checks exclude shared examples. The existing 16-character normalized
minimum remains. Fingerprints still cover graders across the private root, but
only hashes and labels enter audit artifacts.

Added `python -m eval.runner.reaudit --private-root PATH --out EXISTING_RUN_DIR`.
This read-only diagnostic uses finished checkpoint runtimes, every retained
executor/native log, the task's own PrivateGraders and the runner's workspace,
repository and grading/cross-runtime settings. It checks retained log and grader
manifests, keeps access matches when evidence errors coexist, and prints only
task IDs, statuses, error kinds and match labels. It makes no executor/control
call and never rewrites reports, checkpoints or audit artifacts.

Synthetic regressions cover honest unittest submissions and pytest output with
shared examples/boilerplate, every public-file category and cross-task examples,
equivalent literal spellings, authored arguments/patches/file changes/metadata,
and hidden-line reads via cat/sed/grep/Python output with no private path.
Re-audit cases cover real audit roots, multiple tasks, sanitation, missing/changed
retained evidence, incomplete runs and byte-for-byte artifact immutability.

Assumptions: `--out` names the finished source run, not a destination; Claude has
the matching private root and original external runtimes on the host. Public
files stay frozen. This offline change adds no pilot quality result; Claude must
re-audit pilot A on the host before rerunning it. No model call, private-root
lookup, pilot artifact change, staging or commit occurred here.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 425 passed in 33.24s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks` — exit 0. The full repository suite is
deferred to a future merge; only the owned eval tests ran here.

## 2026-10-22 shell and file-change operand separation

The user reports Claude committed the fingerprint fix as `d73b41f` and re-audited
pilot A on the host: 9/10 tasks clean, versus 10/10 inconclusive before the fixes.
Read the two indicated records in the authorized retained interval-union runtime.
Line 23 combines a literal apply_patch with a literal unittest command; line 25
is a FileChange map. Their authored assertion contains `$`, which triggered a
whole-record unresolved-operand check.

Shell expansion/quoting rules now apply to decoded shell commands and their
directories only. Every supported literal `tools.exec_command` call is checked,
including its workdir. JavaScript glue is not a shell command. Concatenated or
otherwise dynamic commands/directories and unknown tools stay inconclusive.
The literal decoder skips quoted patch contents that resemble nested tool calls.
FileChange and apply_patch inputs supply only target/move paths to access checks;
content/diff text cannot trigger shell errors, path matches or fingerprints.
Canonical protected paths, symlinks and traversal checks remain in force.

Added 29 synthetic cases using the real line-23/25 envelopes: unittest is clean,
protected reads and later commands are detected, dynamic/unknown calls are
inconclusive, and authored `$`, backticks, quotes and private-looking strings
stay clean at workspace targets. Native/list FileChanges and literal custom,
code-mode and function-call patches cover protected targets, symlinks and moves.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 454 passed in 47.54s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks` — exit 0.

## Assumptions

- The user's 9/10 result and commit identity are supplied host evidence. No real
  private graders are available here, and no host acceptance result is claimed.
- Claude will rerun the read-only re-audit with the matching private graders;
  the target is 10/10 clean unless actual protected access is detected. Reports,
  frozen tasks and CLI/schema interfaces remain unchanged. No model call,
  private-root lookup, staging or commit occurred in this session.

## 2026-10-22 bounded grader corpus and payload processing

Claude's supplied host check passed 454 eval tests, but re-audit exceeded nine
minutes with a stack inside ast.walk. The user reports 14,669 test files under
the private root, only 120 immediate task graders and 847 unique contents;
recursive enumeration included validation/mutation/reference storage.

Fingerprint inputs now come only from `ROOT/<non-dot-task>/test_*.py`, without
following symlink directories/files. Dot storage, root-level tests and deeper
descendants never feed fingerprints. PrivateGraders.load also requires an
immediate non-dot task directory. Whole-root path protection remains in force,
including every dot-directory and its copies.

SHA-256 content deduplication precedes AST parsing. One invocation-scoped cache
shares the public-corpus/distinctive-line/fingerprint analysis across all tasks,
streams and retries in both the runner and read-only re-audit. It is discarded
between invocations; task-specific manifest hashes still read current files.
AST nodes are collected once per unique grader, and literal source extraction
uses precomputed byte offsets instead of repeatedly splitting the entire file.

The code-mode decoder now matches at source offsets and builds its remainder in
one pass rather than copying the remaining source for each call. A boundary on
the generic path regex prevents quadratic retries across long slash-free words.
The previous command-only shell and path-only FileChange/patch fix is retained.

Nine new regressions cover 120 task graders plus 5,000 quarantined duplicate
copies, exact fingerprint equality, no dot-file reads, one parse per unique
content, cache lifetime and rejected non-task paths. Large-payload cases cover
200 KB patches, commands and malformed literals, 3,000 sequential tool calls,
and a 1 MB FileChange. Corpus analysis across 120 tasks and each large-payload
audit must finish within five seconds. Runner and multi-task re-audit tests
also assert one corpus computation per invocation and fresh analysis next time.

Validation: `.venv/bin/python -m pytest tests/eval -q` — 463 passed in 34.19s.
`git diff --check -- eval tests/eval state/STATUS-eval.md` and
`git diff --exit-code -- eval/tasks eval/reports/pilot-a` — exit 0. Frozen public
tasks and pilot artifacts are unchanged; no model call, private-root lookup,
staging or commit occurred.

## Assumptions

- Public inputs and immediate task graders are immutable within one invocation;
  the cache is in memory only and is never reused by a later invocation.
- The host counts, hang and 454-test result are user-supplied evidence. Claude
  must rerun with the matching private root; acceptance remains under one minute
  with 10/10 tasks clean unless a task actually accessed a protected path. These
  synthetic checks do not establish that host result or pilot quality.

## 2026-10-22 pilot-B shapes and offline regrading

Replaced code-mode whole-source allowlisting with lexical direct-call extraction.
Promise combinators, arrays, loops and display spreads no longer make literal
shell calls unresolved. Dynamic command/workdir operands, aliases, computed tool
access, unknown tools and eval/Function remain inconclusive. Synthetic regressions
cover the supplied parallel-call shape, the exact nested-quoting rg wrapper,
list-form exec file changes, protected targets and macOS temporary-path aliases.
Path comparisons and private-root redaction now cover both `/var` spellings.
Earlier protected-access regressions remain in the eval suite.

The runner records workspace content manifests at executor exit and saves the
configuration in its checkpoint. Added `python -m eval.runner.regrade
--private-root PATH --from DIR --out NEWDIR`: all-task re-audit and fresh-copy
`grade()` execution with unchanged executor accounting, regenerated metrics and
a schema-valid report. It refuses historical missing hashes and mismatches;
source reports/runtimes remain read-only. Separate diagnostics retain source
report and audit-code hashes plus every workspace check. No report schema,
frozen task, pilot artifact or shared interface was edited.

Tests use synthetic graders, mocked executors and local grading subprocesses.
They cover hash refusal before output, source/runtime immutability, fresh copies,
all-task recovery from historical inconclusive audits, parity with current runner
fixture outcomes, and CLI success/refusal output. Host pilot acceptance and the
new pilot-B executor run remain Claude's work.

### Assumptions

- The supplied host results at `96583d3` are historical user evidence: A has
  10/10 valid/clean, pass rate 1.0 and cost per pass USD 0.029; B has 9/10 invalid
  with unresolved_custom_input/unresolved_operand errors. This session did not
  reproduce these measurements or access real private graders.
- Retained checkpoint/report evidence is trusted runner output. Regrading
  requires matching public/private task inputs and exact retained workspaces;
  it cannot establish exit-time integrity for an older run without hashes.

## 2026-10-23 — C preparation, paired comparison and accounting review

Prepared the seed-0 metadata-only twenty-task C subset, twenty unfilled human
skeletons, fill-once rules, standalone config and planning estimate. Added static
template preflight, exact harness-wrapper injection, report artifact hashes and
checkpoint drift refusal. Optional full task populations let B/C reports verify
the same frozen digest as full A while checkpointing selected inputs separately.

Added `python -m eval.runner.compare LEFT RIGHT --out DIR`: schema/provenance
checks, matched valid tasks, diagnostic invalid handling, overall/per-type
metrics, paired 10,000-resample intervals, hash-pinned source reports and JSON /
Markdown output. Existing run CLI flags and shared schemas are unchanged.

Control markers now match only at line start. Zero-delegation accounting permits
all-judge quality-warning contracts and pinned budget-skipped judge items;
other missing judge evidence remains unknown. Standalone runs no longer warn
about an absent control model. Harness estimates now use 15,000 input and 1,000
output tokens per Luna generation ($0.002), based on supplied host observations.

No public task, retained measurement, private grader, other checkout or git index
was modified. Verification and remaining host work are recorded in STATUS-eval.

Verification: `.venv/bin/python -m pytest tests/eval -q` — 649 passed in
60.49s. Frozen task and pilot-report diffs are empty; no full repository suite
was run in this session.
