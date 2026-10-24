# Version 3 host-only capture

After Roles 3/4 land, run `.venv/bin/python -m plugin.host_checks v3-prepare
--out /tmp/lhm-v3-host-capture`. Follow the printed first-session command,
review the numbered table and question pause, answer using the actual question
ID in JSON, and wait for the report and separate ledger continuation before
exiting. Run the printed second-session command and verify HARNESS_LEDGER is
visible without restating the label. Then run `.venv/bin/python -m
plugin.host_checks v3-check --out /tmp/lhm-v3-host-capture`.

Preparation performs help-only integration checks and isolated installation;
it never starts an executor automatically. Both interactive scripts retain
hook trust/terminal evidence and use v3 with HARNESS_NESTED unset. Review the
terminal captures as well as the offline artifact audit. No v3 host run was
performed in the network-disabled workspace-write implementation session.
The procedures below retain the explicitly selected historical v1/v2 path.

# Host installation checks

These procedures require a host with the logged-in Codex CLI and macOS `/usr/bin/script`. Run from the repository root with `.venv` available. They are prepared procedures, not recorded live successes. Do not run them during an evaluation batch. Each trust/silence procedure uses two executor sessions at `gpt-6.1-sol`, low effort; control calls use stub fixtures. No task approval or real controller call is needed.

Use a fresh evidence directory for each capture. Preparation creates a separate temporary HOME, CODEX_HOME and project; it links the existing login without reading or copying its contents. It never edits the real Codex configuration. Keep the temporary files until review; these commands do not delete them. A failed stage must be investigated in its retained logs; use a new directory to repeat the procedure.

## Persisted hook trust

```sh
.venv/bin/python -m plugin.host_checks prepare --scenario trust --out /tmp/lhm-trust-2026-10-23
bash /tmp/lhm-trust-2026-10-23/first-session.sh
```

In the first interactive session, accept the hook trust request for the three displayed diagnostic wrappers. The wrappers invoke the installed production hooks and retain their exact streams. Let the supplied prompt complete and the harness contract appear. Do not approve the contract. Enter `/exit` after the reply finishes. The terminal recorder must have exited before continuing. If trust is denied, do not edit configuration to manufacture approval; start a fresh capture and accept it normally.

```sh
.venv/bin/python -m plugin.host_checks second --out /tmp/lhm-trust-2026-10-23
.venv/bin/python -m plugin.host_checks check --out /tmp/lhm-trust-2026-10-23
```

The second command launches a new `exec` session in the same project with the same isolated CODEX_HOME and unchanged hook commands. Neither launch uses `--dangerously-bypass-hook-trust`; preparation seeds project trust only. Pass requires all three lifecycle hooks in both sessions, distinct session IDs, contract injection, an unchanged config during the second session, a complete executor event stream and an unchanged CLI version. This measures persisted trust for the installed hooks through the retained wrappers; the old demo bypass does not establish it.

## Bundled binary with no Codex on PATH

```sh
.venv/bin/python -m plugin.host_checks prepare --scenario bundle --out /tmp/lhm-bundle-2026-10-23
.venv/bin/python -m plugin.host_checks check --out /tmp/lhm-bundle-2026-10-23
```

Preparation invokes the real installer with `PATH=''` and `HARNESS_CODEX` absent, using an absolute Python executable. It separately records the installer's discovery result in that same environment. Pass requires the ChatGPT bundle path, a successful installation, registered lifecycle events, the install manifest, marker and skill. No executor session is launched. This checks the actual bundle at `/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex`; a missing bundle is a failed host prerequisite, not permission to substitute a fake.

## Unrelated project silence

```sh
.venv/bin/python -m plugin.host_checks prepare --scenario silence --out /tmp/lhm-silence-2026-10-23
bash /tmp/lhm-silence-2026-10-23/first-session.sh
```

Accept hook trust in this isolated first session, let `HOST_CHECK_OK` finish, then enter `/exit`. No contract should appear: this fresh sibling project has no marker. Trust acceptance must be completed before continuing, so skipped untrusted hooks cannot masquerade as silence.

```sh
.venv/bin/python -m plugin.host_checks second --out /tmp/lhm-silence-2026-10-23
.venv/bin/python -m plugin.host_checks check --out /tmp/lhm-silence-2026-10-23
```

Pass requires all three hooks actually invoked in both fresh sessions, exit 0 and exactly empty stdout AND stderr for every invocation. Before/after inventories must show no marker in the project's ancestry and no `.harness` anywhere in the project. The recorder writes outside that project. Inventories establish observed states, not absence of transient writes; this is not a macOS sandbox isolation check.

## Evidence layout and offline review

| Files under each `--out` directory | Meaning |
|---|---|
| `experiment.json` | Scenario, exact executable, isolated home/project and interpreter paths |
| `version-before.{json,stdout,stderr}`, `install.{json,stdout,stderr}` | Command/exit/environment summary and exact streams |
| `discovery.{json,stdout,stderr}`, `installed.json` (bundle) | Empty-PATH discovery and installation inventory |
| `first-session.sh`, `first-command.json`, `first-session.terminal` (trust/silence) | Exact first launch and recorded interactive trust/session |
| `hooks.json`, `hooks-after-second.json`, `wrappers/*.py`, `wrapper-hashes.json`, `hooks/*.json` (trust/silence) | Registered commands and production hook inputs, exit status, exact stdout/stderr |
| `first-records.json` (trust/silence) | SHA-256 hashes separating first-session records from later invocations |
| `second.{json,stdout,stderr}`, `config-after-{first,second}.toml` (trust/silence) | Fresh second launch, full CLI JSON stream, persisted settings |
| `before.json`, `after.json`, `version-after.{json,stdout,stderr}` (trust/silence) | Project inventories and version-drift evidence |
| `audit.json` | Offline verdict; failures overwrite an earlier verdict with overall=fail |

The checker never runs Codex or reads the original temporary workspace. Copy the complete evidence directory to a fresh review destination and rerun the same `check --out DESTINATION` command there. Review the terminal trust interaction alongside the machine verdict. Captures are diagnostic observations, not tamper-proof attestations. No credential file belongs in the evidence directory.
