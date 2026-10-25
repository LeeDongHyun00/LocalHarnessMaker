# LocalHarnessMaker plugin

The default hook path is interface v3, authorized by the user's 2026-10-25
schema freeze. SessionStart pins exactly `gpt-6-luna`, then revalidates the
most recent prior ledger. The first native-session prompt produces a visible
requirements table. Unanswered questions pause the turn before file changes;
explicit user answers use `{"answers":{"Q-1":"answer"}}`. Later prompts never
regenerate requirements or spend another requirements call.

Stop delegates checks to verifier, audits the first retained final message
once, and permits one application repair only for executed failures. The next
Stop checks round 2 without Luna. Repeated failure writes/surfaces
`escalation_advice` recommending human review or higher effort, without changing
settings. A separate verifier-authored ledger continuation happens at most
once. Invalid or missing ledgers get an advisory; they never create a loop.
The report retains the original audit and marks it stale if repair or ledger
bookkeeping changes the final message. Completion evidence is printed on
stderr and retained in `completion-report.json`.

All state lives in
`<workspace>/.localharness/v3/sessions/<sha256(UTF-8 native session_id)>/`.
JSON replacements are atomic, evidence snapshots immutable, and controller
owns append-only `luna-calls.jsonl`; hooks verify the retained prefix, call
count/identity and pricing reference. `hook-state.json` and `hook.lock` are
private orchestration files in that directory. A nonblocking per-session lock
and persisted reservations prevent duplicate calls/repairs after replay or
interruption. Interrupted phases fail open with an advisory and cannot count
as valid H3 completion. Paths reject absolute/traversal/symlink escapes.

`latest-ledger.json` must exactly match the ledger of the most recent prior
session selected by `pin-check.checked_at`, excluding the current session.
Missing artifacts, timestamp ties or identity conflicts never fall back to an
older ledger. `verifier ledger-validate` remeasures before injection, and the
hook checks identifier/file coverage and current hashes before publication.

Every hook retains the exact, immediate `HARNESS_NESTED=1` zero-byte bypass.
Controller/verifier children receive that value in a copied environment.
Direct host demos remove it. No v3 hook calls contract, handoff, judge,
`llm_judge`, fallback, regeneration, or an automatic effort change.

## Pin preflight and installation

```sh
.venv/bin/python -m plugin.pin_check --session-id ID \
  --artifacts /WORKSPACE/.localharness/v3/sessions/SHA256_OF_ID --codex /PATH/TO/codex
.venv/bin/python -m plugin.install --codex-home /ISOLATED/CODEX_HOME --project /PROJECT --check
```

Pin-check exits 0 enabled, 1 disabled with a readable stdout advisory, or 2 for
an internal/artifact error. It verifies the installed version against
`VERIFIED_VERSIONS.json`, tries an advertised `models --json` command first,
then a non-generating stdio app-server `initialize` / `initialized` /
`model/list` probe. Each subprocess has a one-second limit within a five-second
total budget. Pin-check starts no thread and invokes no model. An answered
listing records `model_evidence.source=listing`; display names, prefixes and
newer model identities never satisfy the exact pin.

When neither listing facility answers completely, pin-check may use the exact
installed version's `luna_observation` in the registry. A well-formed observation
of `gpt-6-luna` enables the pin with `source=probe_observation` and
`checks.model_listed=true`. It retains a hashed observation snapshot in
`model_list` and copies the observation's timestamp, thread, tier and original
evidence hash into `model_evidence`. A different version, mismatched model or
missing/malformed observation leaves the pin disabled. An answered listing that
omits Luna also disables it. Enabled results have empty `reason_codes`.
The versioned `controller/prices.yaml` snapshot and pricing reference are still
required. The controller's per-call provider identity check enforces the exact
model on every invocation; registry evidence does not guarantee future calls.

For a new CLI version, first retain and audit its hook compatibility probe,
then run the minimal pinned Luna probe in [HOST-CHECKS.md](HOST-CHECKS.md).
Record `luna_observation` with the actual model/tier, RFC 3339 timestamp, thread
ID and SHA-256 of the verbatim evidence before allowing H3. The registered
`0.163.0-alpha.11.1` observation was captured on 2026-10-25 KST, thread
`01a16ee8-a276-7c23-bd00-0fbe69a816a3`, model `gpt-6-luna`, tier `priority`,
evidence SHA-256 `da10b7331103114c67ff3d26e21e95f54e51aca7faaed888b12cc4e434bf11c2`.
This supplied observation establishes pin eligibility; v3 integration and host
smokes remain separate acceptance checks. Deployment requires Role 1's approved
`model_evidence` schema amendment (decision 0012); tests use a local amended copy
while that shared schema is pending.

`install.sh --check` delegates the same checks and separately reports missing
registration/skill, unverified CLI, unavailable/missing exact model and missing
installed pricing. Its temporary preflight artifacts stay outside the project;
it does not change external configuration. Installation snapshots include the
v3 modules, schemas and pinned prices. Pin-disabled sessions skip all later
Luna calls and cannot be reported as H3. Ordinary work and safe deterministic
verification/ledger handling remain available.

## Concurrent-role adapter and host verification

`plugin/v3_adapter.py` contains all v3 argument spelling. It uses the four
user-authorized operation shapes, with stdout parsing confined to the expected
path or verifier JSON summary. The controller/verifier in this checkout still
implement historical operations, so cross-package execution remains pending
Roles 3/4 integration. Repair wording uses verifier's retained `reinstruct`
formatter with only executed failing rows and an explicit one-repair budget.
The ledger formatter seam is `verifier.ledger.ledger_request(ledger=Path,
requirements=Path, session_id=str)`; adjust this adapter to Role 4's actual
in-package formatter when it lands. Missing wording fails open visibly; there
is no plugin-authored substitute or repeated bookkeeping block.

Run the two-session demonstration only on the host, after those packages land:

```sh
.venv/bin/python -m plugin.host_checks v3-prepare --out /tmp/lhm-v3-host-capture
# Follow the printed session1.sh / explicit-answer / session2.sh commands.
.venv/bin/python -m plugin.host_checks v3-check --out /tmp/lhm-v3-host-capture
```

Preparation creates an isolated installation and two interactive launch
scripts, preserving actual hook trust prompts and terminal captures. It never
launches either paid executor automatically. The first session asks for an
unspecified release label, pauses, accepts the user's explicit JSON answer,
then shows the report and writes the ledger. Exit before launching session 2;
it should inject the ledger and write the same label to `followup.txt` without
restatement. The offline checker rejects missing artifacts, disabled pins,
missing calls, absent question/injection context and mismatched output bytes.
Review terminal captures for actual user-visible questions/answers and retained
application completion evidence. Structural audits do not establish live
latency, cost, isolation or model-context acceptance.

Optional PreToolUse protection is deferred: the retained installed-version
compatibility evidence covers SessionStart/UserPromptSubmit/Stop only, and
exposes no measured pre-tool event contract. Deterministic protected-file hash
checks stay verifier-owned. No new hook event or wire field was invented.
`docs/hooks-contract.md` is Role 1 owned. Role 1 needs to record this active
v3 sequencing, question-answer JSON convention, adapter seam, optional guard
deferral and pending live compatibility measurement there.

Historical demos explicitly select `HARNESS_INTERFACE_VERSION=2` (stub mode
also remains historical). Their evidence and implementation below are retained.
New sessions use v3 unless that legacy setting is explicitly supplied.

## Verification and assumptions

Run `.venv/bin/python -m pytest tests/plugin -q`. These tests mock controller,
verifier and CLI model discovery; no live model or nested Codex run is implied.
The coordinating role runs the full repository suite once before merge.

- The user's schema freeze and CLI shapes supersede still-proposed wording in
  the checked-in shared documentation; this role does not change shared files.
- Explicit question-ID/answer JSON records answers without inferring a mapping
  from ambiguous natural language. Unstructured answers keep the pause active.
- Role 4's pending ledger formatter name is an adapter seam, not an asserted
  implemented/public CLI. Host integration must resolve it before H3 runs.
- Live pin/model-list protocol, fresh-session hooks/trust, ledger validation,
  one repair, timing/cost and two non-evaluation smoke projects remain host work.

## Historical v1/v2 implementation and evidence

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

On the host, install Python 3.11+ and use the available Codex CLI. The app may
update it automatically; installation accepts unverified versions. From the
fresh repository root:

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
unverified`, `Hooks not registered`, and `Skill missing`, returning 1 if any fail.
The unverified-version message replaces the old SC-6 single-pin mismatch and
includes instructions to run the probe and add passing evidence to the list.
An unverified version warns during installation but does not prevent it.
A failed/timed-out probe has its own diagnostic. No executor or model is run.

Checks compare event/script registrations semantically and validate JSON integer
timeouts against `local-harness-maker/install.json`, including the embedded
runtime budget. They accept a different checking interpreter and do not require
the install-time environment overrides. Float, string, boolean, out-of-range or
changed JSON timeouts report a timeout type or value mismatch. The current
source defaults do not override an installed manifest during `--check`.

Review and approve the installed hook commands using the installed CLI's normal
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
Every group signal and liveness check tolerates EPERM/ESRCH: cleanup reaps the
leader and retries briefly, then lists live members with a bounded, shell-free
`ps -A -o pid=,pgid=,stat=` call and signals their PIDs after rechecking group
membership. It reaps the leader and checks for live survivors after SIGKILL;
zombies do not count as live work. ESRCH group errors after leader exit are
quiet; retries and survivor inspection remain active. Unexpected signal errors,
reap/listing errors and unresolved survivors go to stderr and
preserve the original result, timeout or shutdown. If process inspection or
signalling is denied, stderr reports that cleanup could not be verified.
The real inherited-pipe regression runs twenty times per pytest session and
measures cleanup from the leader's exit announcement to allow startup under load.
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

## Verified Codex versions

[VERIFIED_VERSIONS.json](VERIFIED_VERSIONS.json) is the ordered history of verified
versions, each with evidence directories relative to `plugin/`. Its first entry
is `codex-cli 0.162.0-alpha.17.2`, with passing exec and interactive startup
probes. [CODEX_VERSION](CODEX_VERSION) retains the first historical version for
older references; it is no longer an installation or execution pin.

Probe and demo preparation accept any well-formed installed version and save
its exact identity in `experiment.json`. Probe audits validate that identity,
include it in their result, and optionally require an exact expected version.
They can audit an unlisted version before it is added to the registry. Preparation
prints a launch command; execute it on the host and retain hook records,
transcript excerpt and result.json as in the original evidence directories.
Use fresh evidence directories and never overwrite earlier captures.

```sh
.venv/bin/python -m plugin.probe --mode exec --out plugin/evidence/NEW-exec
# Run the printed command on the host and capture the evidence.
.venv/bin/python -m plugin.check_probe_evidence \
  --expected-version "codex-cli 0.163.0-alpha.11.1" plugin/evidence/NEW-exec
```

Only after this audit passes, append the version and evidence paths to the JSON
list, rerun plugin tests and rerun installation `--check`. The tests audit every
listed directory against its recorded version and events. The new
`0.163.0-alpha.11.1` entry has retained hook evidence and the supplied
2026-10-25 KST Luna observation. A passing hook
probe does not replace the one-task audit compatibility smoke required before
large evaluation runs, or establish compatibility for other CLI versions.

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

Demo audits compare recorded POSIX paths lexically, treating `/private/var`,
`/private/tmp` and `/private/etc` as `/var`, `/tmp` and `/etc`. Placeholder paths
remain exact strings; arbitrary host symlinks are never followed. Portable export
uses the same aliases. Committed evidence remains unchanged, and regression tests
force identity path resolution to reproduce Linux behavior on macOS.

Replaced single-version gating with an evidence-backed version history, retained
version recording in probes/demos, and silenced expected post-exit ESRCH logs.
Addressed R2 shutdown/deadline findings with owned-group signal cleanup and
budget tests; integer timeout and installer findings with preflight, repair and
semantic checks; hook findings with project scoping, exhaustion handoffs and
atomic session recovery; demo findings with pre-approval workspace evidence.
Offline tests cover these cases with fake trees/signals and temporary homes.

## Assumptions

- The 2026-10-22 user decision supersedes the role prompt single-pin and STOP-P2 policy. Unlisted versions may install and run probes/demos; verification status remains explicit until passing host evidence is added. Existing evidence is immutable.

- The latest user-approved review decisions supersede Stop 600 seconds, handoff 90 seconds, and preservation of an old handoff after generation failure. The 30-second contract cutoff remains approved despite the controller's 35-second per-call deadline.
- A real demonstration may pass on its first check; a synthetic forced failure is not appropriate in real mode.
- No PR was requested. Use this change summary and these assumptions in a future PR description.
- Live model execution, macOS isolation, persisted trust, real latency and two-session handoff behavior require host verification. Only plugin tests were run here; the full suite remains a pre-merge check for the coordinating role.

### Two-session host capture

[DEMO-SCENARIO.md](DEMO-SCENARIO.md#real-two-session-handoff-demonstration-d-4d-5)
provides separate `plugin.two_session_demo day1`, `day2` and offline `check`
commands. This preparation adds a real pass-path handoff scenario with a random
day-1 decision and a follow-up that omits it. The checker requires validated
saved context, SessionStart injection visible in the new session, approval gates,
passing real verdicts and exact follow-up bytes. Offline synthetic tests do not
establish live two-session success. Assumption: Claude runs both days on the host
with the same retained temporary workspace/home and a working CLI login.

### Scripted host installation checks

See [HOST-CHECKS.md](HOST-CHECKS.md) for exact host commands, trust UI steps, evidence layouts and offline checkers for persisted hook trust, bundled binary discovery with an empty PATH, and unrelated-project silence. These remain host checks until their captures pass; this implementation session ran only offline fixtures.

SessionStart probes the CLI selected through `HARNESS_CODEX`, PATH, then the ChatGPT bundle, with a one-second maximum within its existing deadline. It records `cli_version` in plugin-owned session metadata. An unlisted version adds one line to injected context once per session, naming `python -m plugin.probe --mode exec --out plugin/evidence/NEW-exec`. Resume checks can detect a newly replaced binary; listed versions inject no advisory. Probe/registry failures log a warning and continue; an advisory also survives unavailable handoff context. Use `HARNESS_CODEX` for a launch outside the normal discovery paths. This advisory does not certify the compatibility of a new version; decision 0006's probe and audit smoke remain prerequisites for large evaluation runs.

Assumptions for this change: Claude's supplied 2026-10-23 host demo and Ubuntu CI results are accepted as reported evidence. The new host procedures use macOS's terminal recorder, interactive hook-trust acceptance and the existing login symlink in isolated homes; their live outcomes remain unmeasured. A version probe reports the currently selected executable on disk; it cannot recover the old in-memory version of an already-running executable replaced by the app.
