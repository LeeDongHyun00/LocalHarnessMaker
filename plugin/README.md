# Plugin compatibility experiment

The current implementation covers Role 2's First task. Production hooks,
installation, contract approval, CLI integration, and handoff are pending.

The installed version is pinned in [CODEX_VERSION](CODEX_VERSION). Findings,
full runtime payloads, limitations, and official references are in
[hooks-contract.draft.md](hooks-contract.draft.md). Raw evidence is under
`evidence/2026-10-21-exec/` and `evidence/2026-10-21-tui/`.

Verify saved evidence without using the model:

```sh
.venv/bin/python -m pytest tests/plugin -q
.venv/bin/python -m plugin.check_probe_evidence \
  plugin/evidence/2026-10-21-exec plugin/evidence/2026-10-21-tui
```

Prepare a fresh experiment from the repository root:

```sh
.venv/bin/python -m plugin.probe --mode exec --out plugin/evidence/NEW-exec
.venv/bin/python -m plugin.probe --mode tui --out plugin/evidence/NEW-tui
```

Each command prints a quoted launch command. Review and run that command; the
exec form prints JSONL, and the TUI form requires an interactive terminal. Save
stdout/stderr or a terminal recording in the newly created evidence directory.
Two marker messages and FIRST_REPLY should be followed by SECOND_REPLY without
another user prompt. Quit the TUI after the second Stop finishes. The manifests
locate each original transcript; current evidence includes selected unmodified
transcript records and their source hashes. The preparer itself does not launch
Codex or call a model. New model runs consume account usage.

The experiment registers hooks in a fresh temporary Codex home and never
installs them into the user's normal configuration. The trust bypass applies
only to these reviewed experiment hooks. No cleanup command is provided because
repository rules prohibit deletion without escalation. Temporary paths and
authentication symlinks are not portable; rerun preparation on another machine.

## Change summary

Added an isolated hook-registration preparer, a fail-open input/output capture
probe, offline evidence checking, a version pin, and tests. Both the interactive
CLI and codex exec fired SessionStart, UserPromptSubmit, and two Stop calls.
Both context markers reached the model; the documented Stop response caused
exactly one continuation. The package suite passed 10 tests. This establishes
the feasibility of the hook loop on the pinned version; later deliverables
remain listed in state/STATUS-plugin.md.

## Assumptions

- The role's First task authorizes isolated executor compatibility experiments.
- Role 1 will review and publish the hook contract draft under docs/.
- No production success criteria are inferred from experiment-only tests.
