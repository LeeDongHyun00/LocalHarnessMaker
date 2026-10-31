# LocalHarnessMaker

LocalHarnessMaker is a Codex plugin that turns a request into an approved task
contract, verifies completion, continues executor-actionable unfinished work,
and carries progress into a new session. It contains three lifecycle hooks and
one skill. GPT-6.1 Sol executes the work; the controller uses `gpt-6-luna` through
`codex_cli`, with a same-model `cheap_api` transport fallback. Local Gemma and
QLoRA were dropped by [decision 0007](docs/decisions/0007-scope-cuts.md).

## Prerequisites

- Python 3.11 or newer, Git, and pip dependencies from `pyproject.toml`.
- A macOS host for real verifier command checks under Seatbelt (`sandbox-exec`).
  Unsupported platforms do not run these checks without isolation.
- A working Codex CLI and its existing login for live demonstrations. The
  executable is resolved from `HARNESS_CODEX`, `codex` on PATH, then the ChatGPT
  macOS bundled binary. `OPENAI_API_KEY` is optional for controller HTTP fallback;
  credentials are never copied from the CLI login or stored in the repository.

[plugin/VERIFIED_VERSIONS.json](plugin/VERIFIED_VERSIONS.json) currently records
`codex-cli 0.162.0-alpha.17.2` (exec and interactive startup probes) and
`codex-cli 0.163.0-alpha.11.1` (exec probe). These are evidence-backed versions,
not installation pins. A changed version requires a new hook probe and a
one-task access-audit smoke before a large evaluation; see
[decision 0006](docs/decisions/0006-codex-version-policy.md).

## Install and check

From a clone, create a persistent environment. Replace `/absolute/path/to/project`
with the project you want to opt in. Installation changes the explicitly selected
Codex home and project, so use a disposable target for initial inspection.

```sh
git clone https://github.com/LeeDongHyun00/LocalHarnessMaker.git
cd LocalHarnessMaker
python3 -m venv .venv
.venv/bin/python -m pip install '.[dev]'
export HARNESS_PYTHON="$PWD/.venv/bin/python"
export HARNESS_BACKEND=codex_cli
bash plugin/install.sh --codex-home "${CODEX_HOME:-$HOME/.codex}" --project /absolute/path/to/project
bash plugin/install.sh --check --codex-home "${CODEX_HOME:-$HOME/.codex}" --project /absolute/path/to/project
```

Installation copies the runtime and skill, registers SessionStart,
UserPromptSubmit and Stop, enables hooks, and appends project instructions while
preserving existing instructions and unrelated hook registrations. Keep the
Python environment at the installed path. Rerunning the installer repairs its
files and registrations. Review the installed commands in the CLI's host trust UI.

The project marker `.local-harness-maker` enables hooks in that project and its
canonical subdirectories. Unmarked projects, siblings and symlink escapes do not
activate them. `--check` makes no model call; success prints
`LocalHarnessMaker installation OK`. Missing CLI, unverified version, missing
hooks/skill or invalid installation settings produce diagnostics and exit 1.
An unverified well-formed version may install with a warning.

## Use and run the demo

Open Codex in the marked project and submit a request. Before implementation,
the harness skill displays the goal, criteria, assumptions, reasoning effort and
cost estimate. Review them and answer `approve`, or provide edits to regenerate
the contract. Approval applies to that contract; handoff context never grants
approval. At completion, the verifier checks evidence and Stop continues only
with supplied actionable feedback, up to the attempt limit (default 3).

The isolated real demo creates a temporary home and workspace and uses the host
login through a symlink, without copying credentials. Run it after the current
host evaluation finishes, using a fresh output directory:

```sh
bash plugin/demo.sh --real --out /tmp/lhm-new-real
```

Review the displayed contract and type `approve`. The task creates `result.txt`
containing exactly `ok` and a newline, verifies it, and saves a validated handoff.
Then audit the capture offline:

```sh
.venv/bin/python -m plugin.check_demo_evidence /tmp/lhm-new-real
```

For an immediate offline demonstration using committed host evidence:

```sh
.venv/bin/python -m plugin.check_demo_evidence plugin/evidence/2026-10-22-real
.venv/bin/python -m plugin.two_session_demo check --out plugin/evidence/2026-10-23-two-session
```

Both must report `overall=pass`. The first also reports `approval_gate=true`,
`real_task_verified=true` and `synthetic=false`; the second reports
`session_start_injected=true` and `user_restatement_needed=false`.
[docs/demo.md](docs/demo.md) gives all five recorded scenarios, exact checker
commands, expected fields, and the fresh-clone checklist.

## Verified scope

Committed host captures demonstrate the approval gate, real verification and
handoff, a new session receiving prior context without user restatement,
remaining work after exhaustion, and rejection of stale context after injected
handoff generation/validation failures. Their offline checkers pass in this
sandbox. Workspace snapshots show no task entries at the saved pre-approval
boundaries; they cannot exclude a transient write later removed.

These captures do not establish persisted hook trust, natural provider-failure
recovery, exclusive model reliance on injected context, or complete nested-process
cleanup after terminal closure. This session cannot run nested Codex, live models
or macOS Seatbelt. Fresh-clone installation and the full test suite remain
pending Claude's host checklist. The running full evaluation is separate; no
quality or cost improvement is claimed here.

See [architecture](docs/architecture.md), [CLI interfaces](docs/interfaces.md)
and the [hook contract](docs/hooks-contract.md) for implementation boundaries.
