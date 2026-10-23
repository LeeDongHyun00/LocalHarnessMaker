# Verifier rules

A verdict passes only when every item passes. Fail and unverifiable remain
separate statuses, and both keep overall=fail. Re-instruction is an independent
decision: stopping retries does not turn missing verification into a pass.

## Completion claims

Only the latest measured assistant `final_answer` message supplies claims.
Earlier reports, user/tool messages, commentary, block quotes and fenced code
are excluded. The transcript parser remains pinned to the published Codex
`response_item` format. Extraction is deterministic and makes no model calls.

A completion predicate and criterion reference must share a clause. Completion
words include done, complete/completed, implemented, pass/passed/passing/passes,
met, satisfied, fulfilled, verified, succeeded and successful. References are:

- Exact, case-sensitive criterion IDs, including comma/and lists.
- Inclusive same-prefix numeric ranges such as `SC-1 through SC-4`, `SC-1 to SC-4`, `SC-1–SC-4` and `SC-1 - SC-4`. Both endpoints must exist and be ascending; only existing contract IDs are selected.
- Explicit collective statements such as `all success criteria are met`, `all criteria passed` or `every success criterion is satisfied`. Generic `all done` or `all tasks done` remains unmapped.
- Description words, matched case-insensitively as whole words. Remove common function/contract words, numbers and completion words; require at least two remaining words (one for a one-word vocabulary), including at least one word unique among contract descriptions. Identical descriptions and shared words alone are ambiguous. There is no stemming, synonym or semantic paraphrase matching.

Markdown tables use a `Status` or `Result` column and `ID`, `Criterion`,
`Criterion ID`, `Description` or `Requirement` reference columns. Without a
recognized reference header, use the first non-status column. Without a table
header, infer a standalone positive status cell and use the first other column.
Status words above and standalone OK, Success, ✓, ✔ or ✅ count as positive.
Evidence columns supply neither completion predicates nor criterion references;
a pending status with "previously passed" evidence stays unclaimed. Ordinary
checklist rows such as `- SC-1: Passed` and checked `[x]`/`[X]` rows also count.
Unchecked `[ ]` rows stay unclaimed even if their text says done.

Retain scoped negatives: not/no/never, incomplete, unfinished, unverifiable,
fail/failed/failing/fails, pending, remaining, blocked, todo, will/would/should/
could/if, cannot/unable and negative contractions suppress the affected
predicate. A leading negative suppresses the whole clause. Comma/and lists
share a predicate, while an individual negative clears only its pending IDs.
Exception/contrast words (`except`, `but`, `other than`, `apart from`, `besides`,
`excluding`) stop positive extraction for the rest of the clause; named IDs or
descriptions in that tail are excluded from any collective/range claim. An
all-criteria statement with an unmapped exception is conservatively unclaimed.
Any affirmative observation counts; repeated claims retain the first supporting
clause rather than attempting to reconcile contradictory later statements.

The observation contains the exact source clause, or entire table row,
and final verdict status for every real criterion, plus claimed/unclaimed and
claimed-by-status counts in `VERDICT.claims.json` (see [README.md](README.md)).
Unclaimed clauses are empty. Only a mechanically failed claimed criterion gets
reason `claimed_without_evidence`; passes, unverifiable results and valid judge
reasons keep their existing semantics. Sidecar counts include judge statuses
without rewriting their reasons. Claimed-and-unverifiable is uncertainty,
separate from confirmed failed claims. The verdict schema remains unchanged.

## Commands

Only direct Python invocations are accepted. Commands run with the existing
macOS Seatbelt profile: networking denied, writes limited to the canonical
workspace, sanitized environment and bounded process-group lifetime. Unsupported
platforms and sandbox setup failures never fall back to unsandboxed execution.
The profile does not establish read isolation or general destructive-operation
prevention. Shell operators are rejected, including adjacent operators. The
existing Python `-c` AST checks remain in effect.

| Invocation | Accepted arguments |
| --- | --- |
| `python -m unittest` | No arguments (default discovery); local module names, dotted class/method names or test file paths; `-v`, `-q`, `-b`, `-f`, `-k PATTERN` |
| `python -m unittest discover` | `-s START`, `-p PATTERN`, `-t TOP`, the unittest flags above; positional START/PATTERN/TOP also supported |
| `python -m pytest` | Local paths/node IDs; `-q`, `-v`, `-s`, `--disable-warnings`, `-x`, `-k EXPR`, `-rA`, `--tb=short`, `-p no:cacheprovider` |
| `python -m py_compile` | Local file paths |

`python3` and the current interpreter spelling are also accepted, and dispatch
always uses the verifier's interpreter. Short options with operands accept both
separate and attached values. Option values are consumed according to their
meaning: `-k` is a selection expression, unittest `-p` is a filename glob and
pytest `-p` permits only disabling cacheprovider, never loading arbitrary plugins.

Path operands must exist inside the workspace; absolute paths, traversal outside
it and symlink escapes are rejected. Dotted unittest names must have a local
module/package prefix, checked without importing workspace code; class/method
suffixes remain names. Discovery patterns cannot contain directory separators.
Invalid options are contract defects. Missing local command input is a workspace
defect and can be repaired by the executor. Arbitrary project test code still
runs under Seatbelt; the command parser is defense in depth.

## File and regex paths

`file_exists` and `regex` require one relative literal workspace path. Validation
rejects whitespace/control characters, prose or operand separators (`;`, `,`,
`|`, `&`), glob/expansion characters (`*`, `?`, `[`, `]`, `{`, `}`), absolute or
drive/root-qualified paths (including Windows spellings), and any `..` component.
These are contract-caused unverifiable items, rejected before filesystem access.
Symlink escapes remain rejected. Whitespace-containing filenames are outside
this conservative single-token criterion path policy.

A plausible missing path such as `tests/test_app.py` remains workspace-caused:
`file_exists` reports fail and `regex` reports unverifiable, so the executor can
create the required file. A malformed path is never repaired by asking the
executor to create a file named after contract prose.

## Actionable re-instruction

Every status=fail item is actionable, including claimed_without_evidence.
An llm_judge item retries only with status=fail; status=unverifiable never
retries, even when the judge inspected the workspace. Mechanical unverifiable
items retry only when explicitly classified as workspace-caused.
`verifier/causes.py` defines the internal categories; Result/Execution carry
these to verdict assembly, which passes them to reinstruct without adding
schema fields. Selection never guesses a cause from model-generated reason text.

| Unverifiable cause | Examples | Re-instruct |
| --- | --- | --- |
| workspace (mechanical) | Missing local command input, missing dependency/path or denied resource reported by executed workspace code, unreadable/missing plausible regex input | Yes |
| workspace (judge review) | Schema-valid judge response unable to confirm the criterion, including requests for test execution evidence absent from the snapshot | No |
| contract | No mechanical criteria/empty criteria, rejected or unsupported commands/options, malformed/external/traversing/glob criterion paths, invalid regex | No |
| verifier | Sandbox unavailable/setup failure, command launch/capture failure, no exit code, command deadline or signal termination | No |
| transport | Judge launch failure, nonzero exit, malformed/invalid output, delegation timeout | No |
| budget | Verification budget exhausted before dispatch | No |

A command timeout alone does not establish a repairable workspace cause; it may
reflect the verifier deadline or a cap from the remaining budget. It is therefore
conservatively non-actionable. Unknown causes are also non-actionable.

A successfully delegated, schema-valid judge response keeps its status, reason
and evidence unchanged, including an unverifiable response. Such a response is
classified as workspace review, unlike transport or validation failures, but
uncertainty does not establish a repair the executor can make. The item retains
the judge's reason even when feedback is null. Other
unverifiable reasons identify the specific rejection, missing input, verifier
failure, timeout or budget cutoff. Contract quality warnings skip delegation.

Feedback includes only actionable items, retains original item numbering,
details at most three items and counts only remaining actionable items. It is
at most 300 characters. When no actionable item remains, or the attempt limit
is reached, reinstruct_message is null. The verdict and overall failure are
preserved so the caller can end the loop without spending futile attempts.
