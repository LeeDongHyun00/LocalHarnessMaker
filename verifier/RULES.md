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

## Actionable re-instruction

Every status=fail item is actionable, including claimed_without_evidence.
Unverifiable items retry only when explicitly classified as workspace-caused.
`verifier/causes.py` defines the internal categories; Result/Execution carry
these to verdict assembly, which passes them to reinstruct without adding
schema fields. Selection never guesses a cause from model-generated reason text.

| Unverifiable cause | Examples | Re-instruct |
| --- | --- | --- |
| workspace | Missing local command input, missing dependency/path or denied resource reported by executed workspace code, unreadable/missing regex input, valid judge result unable to confirm the workspace criterion | Yes |
| contract | No mechanical criteria/empty criteria, rejected or unsupported commands/options, external paths, invalid regex | No |
| verifier | Sandbox unavailable/setup failure, command launch/capture failure, no exit code, command deadline or signal termination | No |
| transport | Judge launch failure, nonzero exit, malformed/invalid output, delegation timeout | No |
| budget | Verification budget exhausted before dispatch | No |

A command timeout alone does not establish a repairable workspace cause; it may
reflect the verifier deadline or a cap from the remaining budget. It is therefore
conservatively non-actionable. Unknown causes are also non-actionable.

A successfully delegated, schema-valid judge response keeps its status, reason
and evidence unchanged, including an unverifiable response. Such a response is
classified as workspace review, unlike transport or validation failures. Other
unverifiable reasons identify the specific rejection, missing input, verifier
failure, timeout or budget cutoff. Contract quality warnings skip delegation.

Feedback includes only actionable items, retains original item numbering,
details at most three items and counts only remaining actionable items. It is
at most 300 characters. When no actionable item remains, or the attempt limit
is reached, reinstruct_message is null. The verdict and overall failure are
preserved so the caller can end the loop without spending futile attempts.
