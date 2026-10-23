# Demonstrations and fresh-clone verification

The captures below are committed host evidence. Their checkers read retained
files without launching Codex, models or `sandbox-exec`. All five checkers passed
in this documentation session. Live reruns, fresh-clone installation and the full
test suite were not run here. Wait until the current host evaluation finishes
before starting any live demonstration.

## Single session: approval, verification and handoff

Evidence: [plugin/evidence/2026-10-22-real](../plugin/evidence/2026-10-22-real),
recorded with `codex-cli 0.162.0-alpha.17.2`, real controller/verifier and
GPT-6.1 Sol executor. The capture entry point and offline checker are:

```sh
bash plugin/demo.sh --real --out plugin/evidence/2026-10-22-real --scripted-approval
.venv/bin/python -m plugin.check_demo_evidence plugin/evidence/2026-10-22-real
```

The capture command is historical: the existing directory must never be reused.
For a new typed-approval run, use `bash plugin/demo.sh --real --out /tmp/lhm-new-real`.
`--scripted-approval` sends only `approve` after displaying the contract; it is
for isolated unattended demos. Omit it to review and type approval yourself.
The demo references the existing login by an external symlink, without reading
or copying credentials, and uses a temporary HOME/CODEX_HOME/workspace. Its
per-invocation trust bypass does not establish persisted hook trust.

Inspect `experiment.json`, `request-result.json`, `approval-result.json` for the
exact executor argv, version and exit status; `hooks.jsonl` and the two saved
transcripts for context/approval boundaries; `request-state/session.json` for
`awaiting_approval` and attempt 0; and `approval-state/` for the unchanged contract,
passing real verdict and schema-valid handoff. `result.txt` is exactly `ok\n`.
The three workspace snapshots are empty at their saved pre-approval boundaries;
they do not exclude a transient write later removed.

The checker must report:

| Field | Recorded value |
|---|---|
| `overall` | `pass` |
| `contract_visible`, `approval_gate`, `real_task_verified` | `true` |
| `synthetic` | `false` |
| `attempts`, `reinstructions` | `1`, `0` |
| `max_hook_overhead_seconds` | `0.18847` from retained timings |

A new real run may legitimately need more attempts. The committed single-session
capture demonstrates first-attempt success, not a re-instruction.

## Two sessions: no user restatement

Evidence: [plugin/evidence/2026-10-23-two-session](../plugin/evidence/2026-10-23-two-session),
recorded with `codex-cli 0.163.0-alpha.11.1`. The stage commands are separate;
review day 1 before launching day 2:

```sh
.venv/bin/python -m plugin.two_session_demo day1 --out plugin/evidence/2026-10-23-two-session --scripted-approval
.venv/bin/python -m plugin.two_session_demo day2 --out plugin/evidence/2026-10-23-two-session --scripted-approval
.venv/bin/python -m plugin.two_session_demo check --out plugin/evidence/2026-10-23-two-session
```

The first two commands describe the recorded capture; use a fresh raw directory
outside the checkout for a new run. Day 1 writes `result.txt` and records a random
release label as a decision in its handoff. Day 2 starts a new thread in the same
workspace/home and asks for `followup.txt` using yesterday's label, without
including the label or a clarification turn. Approval resumes each day's own
thread; day 2 is not a resume of day 1.

Inspect `handoff-validation.json` for the successful validation command, output
and saved-handoff hash; `day1/approval-state/handoff.json` for the decision;
`day2/incoming-handoff.json`, the first event in `day2/hooks.jsonl`, and developer
text in `day2/request-transcript.jsonl` for exact handoff injection. Both days
have approval snapshots and passing verdicts; day 2 retains the exact follow-up
bytes and unchanged `result.txt`.

The checker must report `overall=pass`, `saved_handoff_validated=true`,
`session_start_injected=true`, `context_visible=true`, `new_session=true`,
`approval_gates=true`, and `user_restatement_needed=false`. Receipt and successful
follow-up are demonstrated. Exclusive reliance on handoff context is not proven:
day-1 files remain available in the shared workspace.

## Exhaustion and handoff failures

All three committed captures use `codex-cli 0.163.0-alpha.11.1`. They are portable
exports with host-path placeholders; each `portable-export.json` states the
transformation and separately retained raw provenance. Do not resume exported
captures. The exact underlying executor argv remain in each day's
`request-result.json` and, for day 1, `approval-result.json`, with exported paths.

| Scenario | Evidence directory | Expected behavior |
|---|---|---|
| Exhaustion | [2026-10-23-exhaustion](../plugin/evidence/2026-10-23-exhaustion) | One deliberately impossible command criterion fails at attempt 1; Stop lists unmet work and the next new session receives it in the validated handoff. |
| Generation | [2026-10-23-generation](../plugin/evidence/2026-10-23-generation) | The task passes; an injected `controller handoff` exit 2 archives old context, and the new session receives no stale handoff. |
| Validation | [2026-10-23-validation](../plugin/evidence/2026-10-23-validation) | The task passes and handoff generation finishes; an injected `verifier validate-handoff` exit 2 retains pending output, archives old context, and prevents stale injection. |

Run these offline checkers on the committed exports:

```sh
.venv/bin/python -m plugin.handoff_failure_demo check --scenario exhaustion --out plugin/evidence/2026-10-23-exhaustion
.venv/bin/python -m plugin.handoff_failure_demo check --scenario generation --out plugin/evidence/2026-10-23-generation
.venv/bin/python -m plugin.handoff_failure_demo check --scenario validation --out plugin/evidence/2026-10-23-validation
```

Every result must have the matching `scenario`, `overall=pass`, `new_session=true`,
`approval_gates=true`, and `stale_injected=false`. `remaining_injected` must be
`true` for exhaustion and `false` for generation and validation.

Exhaustion uses `HARNESS_MAX_ATTEMPTS=1` only in child environments. Inspect its
sole contract criterion, `python -c 'raise SystemExit(1)'` with expected exit 0,
failed verdict, `phase=exhausted`, zero blocking re-instructions, Stop's unmet-item
message, `handoff.remaining`, and exact SessionStart/developer context on day 2.
Day 2 stops at approval; it does not claim remaining work was completed.

The other two scenarios seed valid old context containing
`obsolete-release-context`. Inspect `previous-handoff.json`, `faults.jsonl`, the
Stop error, the byte-preserving `handoff.stale.*.json` archive and absent current
`handoff.json`. Validation additionally retains `handoff.pending.*.json`. Day 2
uses the real interpreter without the fault, reports SessionStart output null,
and has no `HARNESS_HANDOFF` in developer context. These are controlled CLI
failure demonstrations; neither claims a naturally occurring provider outage
or invalid model output.

For new host captures, the exact supported stage/export sequence is below.
Run it separately for `scenario=exhaustion`, `scenario=generation`, and
`scenario=validation`, reviewing each stage. The raw directory must be fresh;
replace `NEW` in the export destination with a unique name.

```sh
scenario=exhaustion
raw_capture="$(mktemp -d)/$scenario"
.venv/bin/python -m plugin.handoff_failure_demo day1 --scenario "$scenario" --out "$raw_capture" --scripted-approval
.venv/bin/python -m plugin.handoff_failure_demo day2 --scenario "$scenario" --out "$raw_capture"
.venv/bin/python -m plugin.handoff_failure_demo check --scenario "$scenario" --out "$raw_capture"
.venv/bin/python -m plugin.export_demo_evidence --source "$raw_capture" --out "plugin/evidence/NEW-$scenario"
.venv/bin/python -m plugin.handoff_failure_demo check --scenario "$scenario" --out "plugin/evidence/NEW-$scenario"
```

Each scenario makes real executor/control calls except at the selected injected
boundary. Judge criteria, retries and fallback may add calls. Report a cost
estimate before a batch of ten or more paid calls (STOP-3). Keep existing evidence
and failed raw captures; never overwrite or delete them.

## Fresh-clone host checklist — pending Claude

Run after the active evaluation finishes. Retain command outputs, exit codes,
clone commit and `codex --version` (or the resolved executable's version) in an
external host log. This is a procedure awaiting execution, not fresh-clone proof.

1. Clone and create the environment on the host with dependency access:

   ```sh
   git clone https://github.com/LeeDongHyun00/LocalHarnessMaker.git LocalHarnessMaker-fresh
   cd LocalHarnessMaker-fresh
   git rev-parse HEAD
   python3 -m venv .venv
   .venv/bin/python -m pip install '.[dev]'
   export HARNESS_PYTHON="$PWD/.venv/bin/python"
   ```

   Verify that the clone includes this documentation change and all five committed
   evidence directories. Use the host's existing CLI login for later live work;
   the install/check below requires only the CLI version probe.

2. Install into disposable explicit targets and check them:

   ```sh
   trial_root="$(mktemp -d)"
   mkdir -p "$trial_root/home" "$trial_root/project"
   HOME="$trial_root/home" CODEX_HOME="$trial_root/codex-home" bash plugin/install.sh --codex-home "$trial_root/codex-home" --project "$trial_root/project"
   HOME="$trial_root/home" CODEX_HOME="$trial_root/codex-home" bash plugin/install.sh --check --codex-home "$trial_root/codex-home" --project "$trial_root/project"
   ```

   Require both exits 0 and `LocalHarnessMaker installation OK` from `--check`.
   Inspect the project marker/instructions, copied skill/runtime, registered three
   hooks and enabled hooks feature. This does not exercise persisted host trust.
   For an unlisted CLI, retain the warning and follow decision 0006's probe/smoke
   procedure before large runs; do not relabel the version as verified.

3. Audit committed version probes and all five demo captures offline:

   ```sh
   .venv/bin/python -m plugin.check_probe_evidence --expected-version 'codex-cli 0.162.0-alpha.17.2' plugin/evidence/2026-10-21-exec plugin/evidence/2026-10-21-tui
   .venv/bin/python -m plugin.check_probe_evidence --expected-version 'codex-cli 0.163.0-alpha.11.1' plugin/evidence/2026-10-22-exec-0.163
   .venv/bin/python -m plugin.check_demo_evidence plugin/evidence/2026-10-22-real
   .venv/bin/python -m plugin.two_session_demo check --out plugin/evidence/2026-10-23-two-session
   .venv/bin/python -m plugin.handoff_failure_demo check --scenario exhaustion --out plugin/evidence/2026-10-23-exhaustion
   .venv/bin/python -m plugin.handoff_failure_demo check --scenario generation --out plugin/evidence/2026-10-23-generation
   .venv/bin/python -m plugin.handoff_failure_demo check --scenario validation --out plugin/evidence/2026-10-23-validation
   ```

   Require exit 0 for every checker, probe context/continuation success with the
   expected version, and the exact demo fields documented above. These commands
   examine saved evidence, not the newly installed runtime's live behavior.

4. Validate schemas and run the test suite once on the fresh host clone:

   ```sh
   make validate-schemas PYTHON=.venv/bin/python
   .venv/bin/python -m pytest tests/lead tests/plugin tests/controller tests/verifier tests/eval -q
   ```

   Retain the summary including every skip/xfail and its reason. A skipped live or
   private-grader test is pending evidence, not a pass. Provide external private
   fixtures only through the owning role's trusted setup; never copy graders into
   this checkout. This documentation session ran only `tests/lead`.

5. To finish install-through-live-demo acceptance, follow the fresh real demo
   command in [README.md](../README.md#use-and-run-the-demo), review/type approval,
   and run its checker. Retain the new raw capture separately. Record any missing
   host trust, Seatbelt, shutdown or live integration evidence explicitly. Update
   lead STATUS only after Claude supplies the host log and result.
