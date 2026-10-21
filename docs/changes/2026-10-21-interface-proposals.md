# Role 1 hook publication and interface proposals, 2026-10-21

Published [the measured hook contract](../hooks-contract.md) from Role 2's draft
with user approval and adjusted its evidence links to ../plugin/evidence/.
Recorded the approved gpt-6-luna CLI/API model order and the STOP-E4 access-audit
choice in the interface documentation and lead STATUS.

Created three separate proposals using the next free sequential numbers:
[0002 judgment](../decisions/0002-judgment-schema-proposal.md),
[0003 evaluation report](../decisions/0003-evaluation-report-schema-proposal.md),
[0004 backend and nested guard](../decisions/0004-codex-cli-backend-and-nested-guard-proposal.md).
Each includes the draft schema or exact interface, an example, affected roles,
and the tests each owner will add after approval. Added lead-owned tests for
the embedded drafts/examples, synthetic cost arithmetic, required report
metrics/audits and published evidence links. These do not implement the proposed
features or prove their future runtime behavior.

| Check | Observed result |
| --- | --- |
| `.venv/bin/python -m plugin.check_probe_evidence plugin/evidence/2026-10-21-exec plugin/evidence/2026-10-21-tui` | Both: context_visible=true, continued_once=true, exit_code=0 |
| `codex exec --help` | Installed CLI lists --model, --json, --output-schema and --output-last-message; no model call |
| `make test PYTHON=.venv/bin/python TEST_PATH=tests/lead` | 69 passed |
| `make validate-schemas PYTHON=.venv/bin/python` | Validated 3 draft 2020-12 schemas and 5 examples |
| Schema-tree hash comparison below | Unchanged, 10 files; schemas/VERSION=0 |
| `git diff --check` | Exit 0, no output |

The schema tree was fingerprinted before any edits in this session; the
snapshot is local temporary evidence, not a committed interface file. Verify it
with this command in the same environment:

```sh
.venv/bin/python - <<'PY'
from pathlib import Path
import hashlib
import json

before = json.loads(Path('/tmp/localharness-lead-schema-before.json').read_text())
after = {p.as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
         for p in sorted(Path('schemas').rglob('*')) if p.is_file()}
assert before == after
assert Path('schemas/VERSION').read_text().strip() == '0'
print(f'Schema tree unchanged: {len(after)} files; schemas/VERSION=0')
PY
```

No schema/version, runtime implementation, other role STATUS, private grader,
credential or external configuration was changed. No model call, commit,
push, or cross-chat message was performed. Work stops pending approval of the
three proposals as explicitly requested and required by STOP-L1. The full suite
was not run because this change affects only lead-owned documentation/tests.

## Assumptions

- User approval already covers the selected model/transport order, access-audit method and hook publication; it does not yet cover the proposed exact schemas or interface details.
- JSON samples, costs, prices, CIs, hashes and paths are synthetic, with unknown production accounting represented as null rather than zero.
- Role 5 retains the original local-minus-cheap_api parity definition; proposed confidence-interval and fallback-budget policies remain reviewable decisions.
- Later commits must stage only lead-owned paths, tests/lead/ and state/STATUS-lead.md; never git add -A.
