# Shared interfaces

Status: initial draft, 2026-10-21 (Asia/Seoul). `schemas/VERSION` is `0`.
This implements the initial Role 1 assignment; it does not declare the
2026-10-24 freeze. AGENTS.md and the role prompts define the scope.

## Repository setup

Use Python 3.11 or newer. From the repository root:

```sh
make skeleton
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
make validate-schemas PYTHON=.venv/bin/python
make test PYTHON=.venv/bin/python
```

`make skeleton` recreates empty role directories after checkout. Git does not
track empty directories. Role 1 adds no implementation files in other roles'
packages. Setuptools discovers the namespace roots `controller`, `verifier`,
`eval`, and `plugin`; their owners will add executable modules. The pre-existing
`harness` package remains included. The six commands below are contracts, not
implemented commands at this stage.

Pytest's default collection covers `tests/lead`, `tests/plugin`,
`tests/controller`, `tests/verifier`, and `tests/eval`. For a package change use
`make test TEST_PATH=tests/ROLE`. The pre-existing experiments, `harness/`, and
top-level legacy tests are preserved. They retain their existing setup and
opt-in Docker/Chromium integration requirements; this role suite does not claim
to validate them. Run the full relevant suites once before merge.

## CLI baseline

Run commands from the repository root or an environment with the project
installed. All six commands share exit codes: `0` successful operation, `1`
input error, `2` internal error. On success, stdout is exactly one output path
followed by a newline; logs go to stderr. A verification verdict of `fail` is a
successful verification operation, not a CLI input/internal error. On an error,
do not print a success path. Consumers validate JSON before using it.

| CLI | Arguments | Output artifact / successful stdout | Exit codes |
| --- | --- | --- | --- |
| `python -m controller contract` | `--prompt FILE --handoff FILE_OR_none --cases DIR --backend cheap_api_OR_local --out contract.json` | `contract.json`, validated with `schemas/contract.schema.json`; stdout: `--out` path | 0 / 1 / 2 |
| `python -m controller handoff` | `--transcript PATH --contract contract.json --verdict verdict.json --backend cheap_api_OR_local --out handoff.json` | `handoff.json`, validated with `schemas/handoff.schema.json`; stdout: `--out` path | 0 / 1 / 2 |
| `python -m controller judge` | `--criterion JSON_FILE --artifact PATH --backend cheap_api_OR_local --out judgment.json` | `judgment.json`; stdout: `--out` path; judgment schema remains unresolved before freeze | 0 / 1 / 2 |
| `python -m verifier check` | `--contract contract.json --workspace DIR --transcript PATH --attempt N --out verdict.json` | `verdict.json`, validated with `schemas/verdict.schema.json`; stdout: `--out` path | 0 / 1 / 2 |
| `python -m verifier validate-handoff` | `--handoff handoff.json` | Validates the existing handoff without rewriting it; stdout: supplied handoff path (draft assumption) | 0 / 1 / 2 |
| `python -m eval run` | `--config YAML --out eval/reports/NAME/` | Report directory; stdout: supplied directory path; report filenames/schema remain owned by Role 5 | 0 / 1 / 2 |

`FILE_OR_none` means a file path or the literal `none`; `cheap_api_OR_local`
means either `cheap_api` or `local`. Verification commands run in the selected
workspace. For `validate-handoff`, invalid input is exit `1`. No new flags or
commands are introduced here.

## Schemas and samples

All three schemas use JSON Schema draft 2020-12, require all fields listed in
AGENTS.md, and reject unknown object fields. The four check variants are
exclusive: `command`, `file_exists`, `regex`, `llm_judge`. Each variant requires
only its own specified fields. Criteria IDs must be unique within a contract;
the runtime must enforce uniqueness and correspondence with verdict/handoff
IDs because JSON Schema alone does not check those relationships.

| Artifact | Schema | Draft detail |
| --- | --- | --- |
| Contract | `schemas/contract.schema.json` | `reasoning_effort` and `cost_estimate` must be overwritten by code in `controller/analyze.py`; schema validation alone cannot prove their origin |
| Verdict | `schemas/verdict.schema.json` | `attempt` starts at 1; item `evidence` and `reason` are strings; a passing overall verdict requires all items to pass and a null re-instruction |
| Handoff | `schemas/handoff.schema.json` | `artifact`, `state`, `what`, `why` are strings; arrays may be empty |

Command `expected` is an object with required integer `exit_code` (0–255) and
optional string `stdout`. If stdout is present, compare it exactly, including
newlines. If absent, check only the exit code. This supports stable pytest
checks without comparing elapsed time. Capture evidence even when stdout is
not compared. Command timeouts, workspace isolation, and network restrictions
are the verifier's responsibility, as defined in Role 4's prompt.

Empty `success_criteria` and all-judge contracts remain representable so the
verifier can issue its required quality warning and an unverifiable verdict.
`unverifiable` never contributes to an overall pass. A failing verdict may have
a null re-instruction when the retry cap has been reached; the 300-character
limit is enforced by the schema. Retry cap configuration is not a verdict
field, so the producer must enforce it.

| Reference file | Validation schema | Meaning |
| --- | --- | --- |
| `schemas/examples/prompt.json` | `contract.schema.json#/$defs/referencePrompt` | A JSON string containing the user request; fixture format only, not a new CLI envelope |
| `schemas/examples/contract.json` | `contract.schema.json` | One FastAPI endpoint plus a pytest test; three command checks and exactly one llm_judge check |
| `schemas/examples/verdict_fail.json` | `verdict.schema.json` | Synthetic attempt 1: endpoint works, requested test is missing, SC-3 is unverifiable and SC-4 fails |
| `schemas/examples/verdict_pass.json` | `verdict.schema.json` | Synthetic attempt 2: all four criteria pass |
| `schemas/examples/handoff.json` | `handoff.schema.json` | Resume from the failing attempt with SC-3 and SC-4 remaining |

These samples are hand-written specifications. No FastAPI task, model call, or
judge was run to produce their evidence. The zero token/cost fields are fixture
placeholders, not pricing or usage estimates. Consumers may read `--prompt`
as UTF-8 request text; JSON decoding is needed only when extracting this JSON
fixture's string for display. The reference app and test are intentionally not
implemented in this repository by Role 1.

`make validate-schemas` checks every JSON schema outside `schemas/examples/`
and every file inside it, using an explicit schema mapping. Missing required
files or unmapped examples fail validation. It does not execute commands or
make network/model calls. CI runs this target and pytest on Python 3.11 and
3.14; a local pass does not establish a remote CI pass.

## Hook baseline

Until Role 2 supplies an installed-version evidence document at
`docs/hooks-contract.md`, use the [official Codex hooks documentation](https://learn.chatgpt.com/docs/hooks)
(read on 2026-10-21). This section records documented behavior, not an
installed-version test. Do not create a placeholder `docs/hooks-contract.md`,
because its existence would replace the documentation as the source of truth.

Common stdin fields are `session_id`, `transcript_path` (string or null), `cwd`,
`hook_event_name`, and `model`. Event-specific fields may also be present.
`UserPromptSubmit` adds `prompt`. Do not assume the transcript wire format is
stable. See [common input fields](https://learn.chatgpt.com/docs/hooks#common-input-fields).

| Event | Documented output used by the project | Project responsibility |
| --- | --- | --- |
| `UserPromptSubmit` | `{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"CONTRACT"}}` | Inject the contract; the skill shows it and waits for approval before execution |
| `Stop` | Fail: `{"decision":"block","reason":"REINSTRUCTION"}`; pass: no output | A block creates a continuation user prompt; cap retries and generate/save the handoff before allowing completion |
| `SessionStart` | `{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"HANDOFF"}}` | Validate the saved handoff and inject it for the next session |

The output shapes above are documented under
[UserPromptSubmit](https://learn.chatgpt.com/docs/hooks#userpromptsubmit),
[Stop](https://learn.chatgpt.com/docs/hooks#stop), and
[SessionStart](https://learn.chatgpt.com/docs/hooks#sessionstart).
`SessionEnd` is observe-only and must not be used. Role 2 must still establish
the actual installed version, exact event payloads, trust requirements,
continuation behavior, and whether hooks fire under `codex exec`. Role 5's
runner performs the loop itself and must not depend on hook support.

## Freeze prerequisites

| Unresolved item | Affected roles | Required follow-up |
| --- | --- | --- |
| `controller judge` output schema and the representation of its criterion input | 1, 3, 4 | Propose the schema, obtain user approval under STOP-L1, record the decision, and version the interface before implementation |
| Evaluation result JSON schema and report artifact layout | 1, 5 | Role 5 proposes the outputs so JSON-producing commands have an explicit validation schema |
| `validate-handoff` success stdout without an `--out` flag | 1, 2, 4 | Confirm the documented draft assumption with consumers before freeze |
| Installed hook evidence, version pin, transcript handling, and handoff-save point | 1, 2, 3, 4, 5 | Review Role 2's evidence rather than treating current web documentation as an installed-version result |

Any subsequent schema change requires user approval, a decision record, and a
version increment. Declare the freeze with `schemas/VERSION = 1` only after
the initial review resolves the above issues.

## Assumptions

- This session implements the explicitly assigned first draft, without declaring the later freeze or completing future deliverables.
- Empty directories are recreated with `make skeleton`; implementation files remain owned by the four engineers.
- Unspecified draft types are strings for textual evidence/state, structured `expected` for command checks, and positive one-based attempts. These are review points before freeze.
- `validate-handoff` prints its input path on success because the baseline has no output-file flag.
- The role-specific pytest collection is separate from the preserved legacy experiment tests.
- The FastAPI fixture assumes an existing exported app, installed dependencies, and access to a before/after diff; real controller metadata is computed, not copied from fixtures.
