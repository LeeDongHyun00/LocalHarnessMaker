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
