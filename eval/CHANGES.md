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
