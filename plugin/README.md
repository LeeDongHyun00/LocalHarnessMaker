# LocalHarnessMaker plugin

The D-2 fixture loop is implemented: request, full contract injection, approval,
one Stop re-instruction, and a synthetic pass. All lifecycle entry points,
including the original compatibility probe, exit 0 with zero bytes on stdout
and stderr when `HARNESS_NESTED` is exactly `1`. This check precedes runtime
imports, stdin, configuration/state access, subprocess calls, and timing logs.

The installed version is pinned in [CODEX_VERSION](CODEX_VERSION). Role 1 has
published [the hook contract](../docs/hooks-contract.md). D-2 evidence is in
[2026-10-21-d2-pass](evidence/2026-10-21-d2-pass/approval-summary.json).
The original startup probes remain under `evidence/2026-10-21-exec/` and
`evidence/2026-10-21-tui/`.

Verify saved evidence without using the model:

```sh
.venv/bin/python -m pytest tests/plugin -q
.venv/bin/python -m plugin.check_demo_evidence plugin/evidence/2026-10-21-d2-pass
.venv/bin/python -m plugin.check_probe_evidence \
  plugin/evidence/2026-10-21-exec plugin/evidence/2026-10-21-tui
```

Run a new fixture demo from the repository root using the existing Codex login:

```sh
HARNESS_STUB=1 bash plugin/demo.sh --out plugin/evidence/NEW-demo
```

The demo prints the contract summary and waits for typed `approve`. It uses one
initial `codex exec`, then `codex exec resume` for approval; Stop continues the
second turn once. To automate the demo user, explicitly add `--scripted-approval`.
That option applies only to this isolated synthetic fixture simulation, sends
approval after the summary is saved, and is clearly identified in the log.
`--approval-only` stops after the first process; `--continue EVIDENCE_DIR` resumes
an approval that has not yet been attempted. Existing evidence is preserved.

The optional live SC-2 test starts exactly one Codex process, checks the full
contract in the model transcript, and leaves approval pending:

```sh
HARNESS_CODEX_LIVE=1 .venv/bin/python -m pytest tests/plugin/test_codex_integration.py -q
```

Live tests and demos consume account usage. Their stdout/stderr, replies,
complete transcripts, hook input/output/timing logs, and before/after state
snapshots are retained. Temporary Codex homes register the reviewed hook scripts
and reference the existing CLI login outside the repository without reading or
copying credential content. The demo trust bypass is local to each invocation;
persisted hook trust and normal configuration are not changed. Cleanup is not
performed under the repository's deletion stop rule.

## Behavior and scope

The hook configuration is [hooks/hooks.json](hooks/hooks.json). Set `PLUGIN_ROOT`
to this checkout's plugin directory and `HARNESS_PYTHON` to a Python interpreter
with the repository dependencies. SessionStart initializes `.harness/state.json`;
resuming or compacting the same session preserves its contract/approval state.
UserPromptSubmit delegates contract generation to the controller CLI and injects
the [executor skill](skills/harness/SKILL.md). `approve` acknowledges only the
unchanged displayed contract; edits regenerate it. Stop delegates all criterion
verification to the verifier CLI. Pending approval skips verification entirely.

`HARNESS_STUB=1` selects `_stub.py`, which copies shared example JSON unchanged.
The first check returns verdict_fail.json; the second returns verdict_pass.json.
The demo has no FastAPI app and deliberately uses no tools: it proves routing,
approval, and continuation. All real task criteria remain not done. Fixture cost
zeros and evidence are synthetic, and no task-success or real cost claim follows
from a fixture pass.

Without stub mode, the hooks delegate to the shared CLIs using explicit
`HARNESS_BACKEND` (default `codex_cli`) and optional `HARNESS_CASES`. This route
is not live-verified for D-3. Controller contract calls have a five-second
deadline; verifier calls have a thirty-second deadline. Every child gets a copied
environment with `HARNESS_NESTED=1`. Normal hook exceptions return empty output,
warn on stderr, and let Codex continue. `HARNESS_MAX_ATTEMPTS` defaults to 3;
retry exhaustion or a null re-instruction ends with the unmet items in
`systemMessage`. The five required state fields remain unchanged; the private
session.json sidecar stores phase and reviewed-contract hash.

SessionStart can validate/inject an existing `.harness/handoff.json`, but handoff
generation, real integration, installation, packaging, and install.sh --check
remain future deliverables. No SessionEnd hook is registered.

The first D-2 run's approval process timed out after 180 seconds, following an
assistant commentary with no later tool/Stop event. Its partial output and state
are preserved in [failure.json](evidence/2026-10-21-d2/failure.json). The fresh
routing-only run completed; actual task execution and shell-tool reliability are
outside this stub proof.

## Change summary

Added exact silent nested guards to all four hook entry points, three thin
lifecycle handlers, approval state, bounded Stop routing, byte-preserving fixture
CLIs, executor skill, reproducible demo, and offline evidence audits. Tests cover
guard precedence, open/unreadable stdin, poisoned imports/state/config I/O and
subprocesses, normal guard values, mocked CLI protocols, exceptions, approval,
retry exhaustion, resume, fixture immutability, and demo boundaries. Measured
successful hook overhead was at most 0.193 seconds, excluding stub CLI time.

## Assumptions

- The user authorized D-2 executor runs and a scripted user for the isolated approval demonstration; normal sessions still wait for actual user approval.
- A repeated SessionStart with the same session_id is a resume/compact, not a new session reset; a new session_id resets attempts and phase while retaining the handoff location.
- A routing-only stub pass establishes no real application result, controller latency, paid cost estimate, or D-3/D-4 installation result.
