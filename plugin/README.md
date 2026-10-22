# LocalHarnessMaker plugin

The three hooks generate a contract before approval, verify approved work at
Stop, continue unmet work up to `HARNESS_MAX_ATTEMPTS` (default 3), and generate
and validate a handoff after a passing verdict or retry exhaustion. SessionStart validates and injects
`.harness/handoff.json`. Normal sessions require explicit `approve`; edits
regenerate the contract. The state keeps the five shared fields, with approval
and session identity in a private sidecar. Resume preserves approval; a new
session resets attempts.

Real mode uses `HARNESS_BACKEND=codex_cli` by default and never falls back to
stubs. Only explicit `HARNESS_STUB=1` selects synthetic fixtures. The controller
owns any permitted backend transport fallback. All hook child environments are
copies with `HARNESS_NESTED=1`; hooks with that exact flag exit before imports,
stdin, files or logging, with empty stdout/stderr. Other values run normally.

A failing verdict before the limit blocks with its exact `reinstruct_message`.
A null message at that point is an error, logged on stderr. Exhaustion permits
completion and shows unmet criteria with evidence. Any hook exception produces
empty stdout, a warning on stderr and exit 0, retaining the skill workflow.
Missing transcripts and handoff failures also fail open. Handoffs are published
only after controller generation, CLI validation and local schema validation;
a failed generation renames the previous handoff to `handoff.stale.UUID.json`
without deleting it. SessionStart never injects stale names. On exhaustion the
handoff carries remaining work and the completion message still lists unmet
criteria, even if handoff generation fails. Completion without a new handoff
is not proof of successful handoff generation.

The installer writes `.local-harness-maker` into the selected project root.
After the exact nested guard, each hook reads the payload and checks the
canonical cwd and its ancestors for this marker before loading runtime state
or logging. Unmarked projects exit 0 with empty stdout/stderr and no writes;
subdirectories inherit opt-in, siblings and symlink escapes do not. Demos and
probes create markers only in their temporary workspaces. State JSON is written
through temporary files and atomically replaced. Malformed session metadata is
renamed to `session.bad.UUID.json`, warned about, and reset as a new session.

## Install from a fresh clone

On the host, install Python 3.11+ and the exact Codex version in
[CODEX_VERSION](CODEX_VERSION). From the fresh repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install .
export HARNESS_PYTHON="$PWD/.venv/bin/python"
trial_root="$(mktemp -d)"
mkdir -p "$trial_root/home" "$trial_root/project"
HOME="$trial_root/home" CODEX_HOME="$trial_root/codex-home" \
  bash plugin/install.sh --codex-home "$trial_root/codex-home" \
  --project "$trial_root/project"
HOME="$trial_root/home" CODEX_HOME="$trial_root/codex-home" \
  bash plugin/install.sh --check --codex-home "$trial_root/codex-home" \
  --project "$trial_root/project"
```

Both targets are explicit. Installation copies controller, verifier, schemas,
hooks, skill and project instructions into the targets, so runtime imports and
data do not require the checkout. Keep the selected Python environment at its
installed path. No credential is copied. Inputs, configuration, bounded integer
timeouts, source files and destination paths are validated before any target
write. File updates use temporary files and atomic replacement. An interrupted
installation can be repaired by rerunning the same command. Reruns replace our
registrations without duplicates, preserve unrelated hooks, enable
`features.hooks`, and append the project instructions only if absent. Existing
project instructions are retained. Repair does not delete prior files.

The executable is resolved from `HARNESS_CODEX`, then `codex` on PATH, then the
macOS bundled binary:
`/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex`.
The five-second version probe uses the same shutdown protocol as other child
calls. `--check` independently reports `Codex CLI not found`, `Codex version
mismatch`, `Hooks not registered`, and `Skill missing`, returning 1 if any fail.
A failed/timed-out probe has its own diagnostic. No executor or model is run.

Checks compare event/script registrations semantically and validate JSON integer
timeouts against `local-harness-maker/install.json`, including the embedded
runtime budget. They accept a different checking interpreter and do not require
the install-time environment overrides. Float, string, boolean, out-of-range or
changed JSON timeouts report a timeout type or value mismatch. The current
source defaults do not override an installed manifest during `--check`.

Review and approve the installed hook commands using the pinned CLI's normal
trust UI on the host. Registration checks do not prove persisted trust. This
session tested only temporary HOME/CODEX_HOME targets and did not modify the
user's real Codex configuration.

## Deadlines

Each child starts with `start_new_session=True`. On SIGTERM, SIGHUP, SIGINT,
a deadline or any other exception, the owner sends SIGTERM to all groups it
owns, waits up to two seconds, then sends SIGKILL to surviving groups and reaps
the direct children with a bounded wait. Normal child completion uses the same
cleanup to terminate leftover descendants. The runner checks leader exit every
50 ms while reading/writing pipes, independently of pipe EOF. When the leader
exits, cleanup starts immediately even if a grandchild holds stdout/stderr; after
group termination it drains the pipes for at most 250 ms and returns the leader
status and captured output. The drain also fits inside the cleanup reserve.
Signals during spawn are deferred
until the child is registered; repeated signals cannot interrupt cleanup. The
hook reserves four seconds for cleanup and overhead and caps later calls to the
remaining cumulative budget. All child calls use `shell=False` and copied
environments. The installer, demo and compatibility probe use this runner too.

SIGKILL cannot be caught by this protocol. Abruptly killing an owner with
SIGKILL requires external process supervision to guarantee cleanup. Separately
owned nested sessions rely on the same protocol in their owning verifier and
controller; Role 4 owns judge and sandbox-command shutdown. Actual terminal
closure and nested process cleanup remain host verification checks.

| Operation | Environment variable | Default seconds |
|---|---|---:|
| Contract | HARNESS_CONTRACT_TIMEOUT | 30 |
| Verifier check | HARNESS_VERIFY_TIMEOUT | 480 |
| Handoff generation | HARNESS_HANDOFF_TIMEOUT | 120 |
| Handoff validation | HARNESS_VALIDATE_TIMEOUT | 5 |
| SessionStart hook | HARNESS_SESSIONSTART_TIMEOUT | 10 |
| UserPromptSubmit hook | HARNESS_USERPROMPTSUBMIT_TIMEOUT | 40 |
| Stop hook | HARNESS_STOP_TIMEOUT | 660 |

Outer timeouts are resolved into hooks.json as JSON integers at installation or
demo preparation; commands pin the matching runtime budget. Set overrides before
installation. All deadline overrides require decimal integer seconds, bounded
at 86400; outer hooks require at least 5 seconds and child calls at least 1.
Fractional values (including `10.0`), non-finite values and invalid retry limits
are rejected before installation/demo files are written. Child deadlines can be
changed at invocation and remain capped by the outer budget.

Tests tie Runtime's default outer budgets directly to hooks.json. Stop defaults
leave room for 480 + 120 + 5 seconds of CLI work plus cleanup. The verifier owns
its 450-second internal budget (`HARNESS_VERIFY_BUDGET_SECONDS`); its plugin
caller allows 480 seconds. The contract path is a user-approved exception to
"callers outlast callees": the controller's per-call Codex deadline is now
35 seconds (commit `0d57e36`), but the plugin cuts the contract call off at
30 seconds inside the 40-second hook. The controller cannot reach its 35-second
deadline and perform deadline-triggered fallback on that path. Other callers
outlast their callee budgets. Contract calls log latency; hooks log elapsed and
CLI time. Real latency and nested shutdown require host verification.

## Host demos and evidence

Run only on the host with its existing CLI login. The demos create temporary
HOME, CODEX_HOME and workspace, reference the existing login with an external
symlink without reading/copying it, and register only the three reviewed hooks.
The demo process deadline is at least 2400 seconds and expands with configured
Stop timeouts and retry limits, so it outlasts the hook cycles. The outer
executor is a direct-user session with the nested flag unset so hooks
can fire; hook-launched children set the guard. The per-invocation demo trust
bypass does not establish persisted trust. No cleanup deletes files.

```sh
HARNESS_STUB=1 bash plugin/demo.sh --out plugin/evidence/NEW-stub --scripted-approval
bash plugin/demo.sh --real --out plugin/evidence/2026-10-22-real --scripted-approval
.venv/bin/python -m plugin.check_demo_evidence plugin/evidence/2026-10-22-real
```

Omitting `--out` in real mode uses `plugin/evidence/DATE-real/`. Existing output
is rejected. Omit `--scripted-approval` for typed approval; `--approval-only`
stops before approval and `--continue EVIDENCE_DIR` resumes an unattempted
approval. Scripted approval applies only to the isolated demo and is sent after
the saved summary is displayed.

Real mode requests one file, `result.txt`, containing exactly `ok\n`, with real
controller/verifier CLIs and `HARNESS_BACKEND=codex_cli`. Stub mode retains the
routing-only FastAPI fixtures and expects exactly one re-instruction followed
by synthetic pass. Real mode accepts a first-attempt pass or subsequent bounded
re-instructions. Both retain commands, exit status, transcripts, hook logs,
contract injection, approval gate, state snapshots and verdict evidence. Real
mode additionally validates the handoff and checks/copies the exact artifact.
It saves `initial-workspace.json`, `request-workspace.json`, and
`before-approval-workspace.json`, listing task files/directories/symlinks and
file hashes. Harness metadata and the opt-in marker are excluded. Both collection
and the offline real-mode audit reject any task entry present before approval;
`approval_gate=true` requires those checks. Snapshots establish the observed
workspace state, not the absence of a transient write later removed. Older real
evidence lacking these snapshots must be captured again.
The offline audit verifies those saved boundaries and re-instruction visibility.
Real mode was prepared but was not executed in this sandbox. Two-session real
handoff injection remains a separate host check.

```sh
.venv/bin/python -m pytest tests/plugin -q
.venv/bin/python -m plugin.check_demo_evidence plugin/evidence/2026-10-21-d2-pass
bash -n plugin/install.sh plugin/demo.sh
```

Prior startup evidence is in `evidence/2026-10-21-exec/` and
`evidence/2026-10-21-tui/`; the canonical interface is
[docs/hooks-contract.md](../docs/hooks-contract.md). Existing D-2 evidence is
synthetic and does not establish real application success, usage or latency.
The opt-in live SC-2 test remains disabled by default.

## Change summary

Addressed R2 shutdown/deadline findings with owned-group signal cleanup and
budget tests; integer timeout and installer findings with preflight, repair and
semantic checks; hook findings with project scoping, exhaustion handoffs and
atomic session recovery; demo findings with pre-approval workspace evidence.
Offline tests cover these cases with fake trees/signals and temporary homes.

## Assumptions

- The latest user-approved review decisions supersede Stop 600 seconds, handoff 90 seconds, and preservation of an old handoff after generation failure. The 30-second contract cutoff remains approved despite the controller's 35-second per-call deadline.
- A real demonstration may pass on its first check; a synthetic forced failure is not appropriate in real mode.
- No PR was requested. Use this change summary and these assumptions in a future PR description.
- Live model execution, macOS isolation, persisted trust, real latency and two-session handoff behavior require host verification. Only plugin tests were run here; the full suite remains a pre-merge check for the coordinating role.
