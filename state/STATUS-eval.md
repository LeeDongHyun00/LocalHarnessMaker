## Done

- Fixed ordinary wrapped-command false inconclusive audits by unwrapping zsh/bash/sh displays before shlex operand analysis, keeping quote provenance per inner word, bounding workspace globs and separating filter options from paths (.venv/bin/python -m pytest tests/eval -q: 306 passed, 2 skipped, 1 xfailed).
- Added 42 distinct sanitized host-corpus commands with source indices/hash and synthetic referenced paths; before 4 clean/38 inconclusive, after 42 clean/0 inconclusive, with all six shell/quote variants clean (PYTHONPATH=. .venv/bin/python /tmp/lhm_compare_wrappers.py: fixture counts 4 C/38 I to 42 C/0 I; six wrapper quote replays I to C).
- Preserved wrapped and unwrapped H1, absolute/traversal/encoded/symlink controls, all eight recursive ancestor command families, private-line fingerprints, decode-and-execute uncertainty and cross-task/cross-run grading-copy invalidation; documented per-case before/after tables (.venv/bin/python -m pytest tests/eval -q: 306 passed, 2 skipped, 1 xfailed; M2 strict-xfail AST unchanged from 5faf49d).

- Fixed H2 by retaining grading copies outside executor runtimes and auditing retained copies, sibling runtimes and prior runs; four synthetic integration variants invalidate glob/absolute reads across tasks and runs (.venv/bin/python -m pytest tests/eval -q: 88 passed, 2 skipped, 1 xfailed).
- Fixed H1 with shlex directory tracking, cwd/workdir, concrete glob/quote resolution, case-insensitive canonical comparisons, recursive ancestor detection and normalized private-line fingerprints; all ten host cases now detect access or are inconclusive, while ordinary workspace commands stay clean (PYTHONPATH=. .venv/bin/python /tmp/lhm_compare.py: ten clean-before cases became nine access_detected and one inconclusive; .venv/bin/python -m pytest tests/eval -q: 88 passed, 2 skipped, 1 xfailed).
- Fixed M1 by using labels in audit matches and redacting checkpoint results; tests scan all --out files for raw/canonical synthetic grader roots (.venv/bin/python -m pytest tests/eval -q: publication scan passed; 88 passed, 2 skipped, 1 xfailed).
- Fixed transport retry counting per reinstruction segment, post-call report/usage error classification, unresolved-guard coverage, seed-sensitive bootstrap coverage and actual-location shim resolution coverage; replaced previous unsupported STATUS evidence claims (.venv/bin/python -m pytest tests/eval -q: 88 passed, 2 skipped, 1 xfailed).
- Documented retained-copy exposure accurately and recorded the H1 before/after table and M2 proposal in owned eval/CHANGES.md (.venv/bin/python -m pytest tests/eval -q: 88 passed, 2 skipped, 1 xfailed; no live model calls).

## Remaining

- STOP-1: M2 cannot be satisfied under the frozen schema: its allOf requires aggregate valid if no task is invalid, while audit-clean executor failures must remain valid samples. Role 1 needs user approval, a decision record and schemas/VERSION revision allowing aggregate-only halt invalidity. The strict xfail test reproduces the requested two-task STOP-E1 behavior. Current partial STOP-E1 reports must not be used as valid comparisons. Proposal is in eval/CHANGES.md; no other-role path was edited.
- After that interface decision, implement task-set ID/count mismatch validation, explicit halt/count reasons in report/stderr, and successful exit 0 for the recorded invalid report. Remove the strict xfail only when the behavior passes.
- Pending host verification: installed CLI executor/controller/verifier/resume compatibility, actual nested guard, retry behavior, complete event capture, case-insensitive aliases, process termination and sandbox behavior. Nested Codex, live models, network and macOS sandbox-exec are unavailable here and were not attempted.
- Revalidate external graders on the host; LHM_PRIVATE_GRADERS was unset and two legacy fixture tests skipped. All current tests use synthetic private roots and mocked model/control calls.
- Obtain verified versioned prices and actual per-call controller/judge/fallback accounting; complete done-claim denominator and hash-pinned paired local-minus-cheap_api parity. Current missing observations remain undefined.
- Review/diversify the 119 public drafts, provision external graders separately, implement two-session handoff execution and observations, then estimate/approve the 10-task pilot. Freeze only after review; supply the hash to Role 1 and manually re-check five baseline samples.
- Full repository tests remain pending before any future merge; this session ran only tests/eval and did not stage or commit. D-2 through D-5 measurements remain unfinished.

## Decisions

- Unwrap only literal supported shell invocations with shlex and keep inner raw-word provenance: wrapper quoting must not be confused with quoting inside an operand.
- Certify workspace globs by their static directory prefix and absence of later traversal: unmatched internal globs are resolved, while concrete symlink matches remain protected-path checks and external globs remain unresolved or detected.
- Treat rg/find/grep filter option values as patterns and retain recursive start-directory auditing: pattern syntax alone must not invalidate an ordinary workspace command.
- Retain conservative variable handling, including HOME: environment-aware expansion is optional and outside this small correction.

- Retain grading copies outside executor runtimes and audit all retained/other-runtime locations: avoids deletion under STOP-4 while making observed cross-task/cross-run access invalid.
- Classify recursive ancestor access as access_detected: find/recursive grep/list/copy/archive operations cover protected descendants.
- Hash normalized non-trivial grader lines across the private task family: catches tool-output disclosure independently of operand construction without recording plaintext in fingerprint evidence.
- Keep unresolved shell paths and decode-and-execute pipelines inconclusive: clean logs must not stand in for missing operand resolution.
- Stop on M2's frozen invariant conflict: inventing an invalid task would violate valid quality-sample accounting; changing the shared schema exceeds Role 5 ownership.
- Keep the existing relative-reference shim and resolve it from its actual URI: offline registry tests now exercise the real shim rather than substituting its target.

## Verify commands

- .venv/bin/python -m pytest tests/eval -q
- git diff --check -- eval tests/eval state/STATUS-eval.md
- Pending host only: complete live CLI/event/process/nested-guard/sandbox checks after the interface blocker is resolved.
- Before a future merge only: full repository test suite once.

## Do not touch

- controller/, verifier/, plugin/, shared schemas/configuration, other roles' tests or STATUS files, or concurrent changes; never share task contents with Role 3.
- Real private grader storage; this session uses only synthetic pytest/temp roots and no model calls.
- .git and historical baseline artifacts; do not stage, commit, delete files or rewrite history.
- No live evaluation until the open interface decision and host verification prerequisites are resolved.

## Assumptions

- The current user priority is the wrapped-command regression; the existing M2 STOP-1 record and strict xfail remain unchanged.
- The 42-command corpus fixture intentionally selects distinct non-heredoc commands; the full 59-command production replay remains pending host verification.
- All shell displays in tests are log data; even fixture commands naming other roles' tests are never executed. Only tests/eval was run.
- No match for a workspace-bounded glob does not create audit uncertainty; a command may fail normally while its observed access audit stays clean.

- The user's host-review priorities supersede the previous Remaining ordering; schemas and external CLIs remain frozen.
- Retained copies share the runner's temporary directory namespace; all lhm-eval-* siblings and lhm-retained-grading are audit roots on every task/run.
- Unknown named-user tildes remain unresolved; concrete globs and quote splitting can resolve to detected protected paths.
- Dynamic execution is not fully established by static command parsing or line fingerprints; full capture and host review remain required.
- The shim resolves relative to its own file URI through an offline registry; no frozen shared schema needs alteration for that test.
- No human can answer in this environment; STOP-1 is reported without requesting a response or modifying another role's paths.
