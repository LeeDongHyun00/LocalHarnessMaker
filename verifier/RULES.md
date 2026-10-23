# Verifier rules

A verdict passes only when every item passes. Fail and unverifiable remain
separate statuses, and both keep overall=fail. Re-instruction is an independent
decision: stopping retries does not turn missing verification into a pass.

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
