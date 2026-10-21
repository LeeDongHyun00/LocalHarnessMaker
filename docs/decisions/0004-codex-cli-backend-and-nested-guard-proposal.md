# Proposal: codex_cli backend and nested-hook guard

Date: 2026-10-21 (Asia/Seoul).
Status: approved by the user on 2026-10-21

Approved record; shared schemas and interface documentation are published in
schemas/VERSION 1. Runtime implementation remains assigned to each owning role.

## Approved decision and affected roles

The user selected gpt-6-luna through the existing logged-in Codex CLI as primary,
the same exact model through HTTP API as fallback, and local Gemma as the second
stage. Do not substitute another model, make local a hidden fallback, or require
an API key for CLI authentication. Role 3 must replace the current configurable
gpt-4.1-mini assumption after interface approval.

| Role | Change after approval |
| --- | --- |
| 1 Tech Lead | Update shared CLI/environment documentation and version the approved bundle |
| 2 Plugin | Put the exact nested guard before every hook's input/import/state/config work |
| 3 Controller | Add injectable CLI subprocess backend and configured fallback/model order |
| 4 Verifier | Pass configured codex_cli routing through the judge subprocess boundary |
| 5 Evaluation | Support codex_cli config, guard runner-owned exec/resume, audit logs and API-equivalent accounting |

## Exact proposed interface text

```text
All controller --backend arguments accept exactly: codex_cli, cheap_api, local.
--backend remains required. Primary workflow/config selects codex_cli explicitly.

python -m controller contract --prompt FILE --handoff FILE_OR_none --cases DIR --backend codex_cli_OR_cheap_api_OR_local --out contract.json
python -m controller handoff --transcript PATH --contract contract.json --verdict verdict.json --backend codex_cli_OR_cheap_api_OR_local --out handoff.json
python -m controller judge --criterion JSON_FILE --artifact PATH --backend codex_cli_OR_cheap_api_OR_local --out judgment.json

codex_cli invokes codex exec using the existing login and model gpt-6-luna.
cheap_api invokes HTTP Responses API with model gpt-6-luna; API keys come only
from OPENAI_API_KEY or the existing configured environment-key name.
local uses the configured second-stage Gemma backend. If unavailable, return
an explicit error rather than silently making a cloud call. Models, executable
paths, endpoints, deadlines and fallback policy live in controller configuration.

HARNESS_NESTED=1 is a process-local bypass for every LocalHarnessMaker hook.
The hook's first action is an exact comparison to the string "1". If equal,
exit 0 immediately with ZERO bytes on stdout AND stderr. Do not read stdin,
load state/config, import controller/verifier, create directories, log timing,
invoke subprocesses/models or mutate files. Check before normal processing
and whole-script exception handling. Empty output is not {} or a newline.
Unset, empty, "0", "true" and "01" preserve normal behavior.

Set HARNESS_NESTED=1 in a copied child environment for every controller-owned
Codex subprocess, including retry/resume/repair calls and any wrapper that
can launch Codex. Role 5 also sets it for runner-owned executor and resume
subprocesses: that runner independently owns injection/verification and must
not duplicate it through hooks. Normal direct-user Codex sessions leave it
unset. Never mutate the parent's environment or persist a global setting.

Reuse CLI login; do not read/copy auth.json, synthesize HTTP credentials from
it, or change persistent login/configuration/trust. HTTP fallback needs its
own configured environment key. No service configuration is changed.

Consume codex exec --json events as logs/accounting, not controller stdout.
Read final JSON from --output-last-message, validate locally, and overwrite
code-owned metadata. Use --output-schema with the strict wire-schema adapter
supported by the installed CLI; local validation is still mandatory. Only
the final --out path reaches successful controller stdout. Logs go to stderr;
existing input/internal error codes 1/2 and success code 0 remain unchanged.

For --backend codex_cli, CLI unavailability, failed transport or deadline
expiry may transition once to cheap_api using the same gpt-6-luna if its key
and remaining call budget exist. Do not fall back for a judgment whose status
is fail/unverifiable. Explicit --backend cheap_api bypasses CLI entirely.
Do not silently use local or another model. Log the actual backend/model and
fallback reason for every call, preserving partial/unknown accounting.

Use one budget of at most three model generation calls (initial plus two
retries), shared across CLI calls, HTTP fallback and validation regenerations.
Fallback consumes a slot; it does not reset the budget. Allow one CLI-to-HTTP
transition per command and keep remaining retries HTTP after the transition.
Without fallback credentials/budget, fail explicitly with exit 2. Input
validation errors exit 1 before any call. Unknown usage/cost is null, not zero.
Every call's cost is API-equivalent USD, including CLI, local and failed calls.
```

This new guard covers SessionStart, UserPromptSubmit, Stop and future hooks
supplied by this plugin; no SessionEnd hook is added. It does not govern other
plugins' hooks, which need separate runner verification. The current probe
has not tested this guard; the published hook evidence is not evidence of its
implementation. Normal hook failure/timing requirements apply when unguarded.

## Example

This illustrative argv/environment record is not an executed model call.
Use an injected subprocess runner, shell=False, piped stdin, separate event
and stderr capture, and a configured deadline. The private temporary control
workspace contains intended inputs/schema, never graders or a grading copy.

```json
{
  "controller_command": ["python", "-m", "controller", "contract", "--prompt", "request.txt", "--handoff", "none", "--cases", "controller/case_library/seed", "--backend", "codex_cli", "--out", "contract.json"],
  "child_env_overrides": {"HARNESS_NESTED": "1"},
  "child_argv": ["codex", "exec", "--model", "gpt-6-luna", "--sandbox", "read-only", "--skip-git-repo-check", "--json", "--color", "never", "--cd", "/tmp/harness-control-example", "--output-schema", "/tmp/harness-control-example/wire-schema.json", "--output-last-message", "/tmp/harness-control-example/response.json", "-"],
  "hook_result_with_guard": {"exit_code": 0, "stdout": "", "stderr": ""},
  "controller_success_stdout": "contract.json\n"
}
```

Control-model instructions request structured output without implementation
tools or approval interaction. Do not use the probe's trust bypass by default.
Flags were checked with installed codex exec --help on
codex-cli 0.162.0-alpha.17.2 and the
[official codex exec documentation](https://learn.chatgpt.com/docs/developer-commands#codex-exec),
read on 2026-10-21 with OpenAI Docs. No model invocation, model/account access
check, real price, login change or live backend success is claimed.

## Tests to add after approval

- Role 1 tests/lead: updated six-CLI table retains the other three commands, adds codex_cli to all controller backend enums, documents the exact guard and the approved version.
- Role 2 tests/plugin: parameterize every hook with guard=1, malformed/blocked/unreadable stdin and failing state/config/import/subprocess mocks; assert immediate exit 0, zero bytes on both streams, and no I/O/calls. Test unset/0/true/01 normal behavior and precedence over HARNESS_STUB=1.
- Role 3 tests/controller: subprocess mocks for exact argv/model, shell=False, stdin, deadline, copied child env and guard on initial/retry/resume; no parent-env mutation; separate event/final-file parsing; metadata overwrite and schema validation. Test timeout/nonzero/missing login/key, one HTTP transition with same model, at most three total calls, no fallback for fail/unverifiable, no hidden local fallback, and summed/null API-equivalent cost.
- Role 4 tests/verifier: pass the configured backend to judge, validate output and prove nested hooks cannot recursively invoke verifier/controller.
- Role 5 tests/eval: config enum, guarded executor/resume children, hooks-independent loop, complete audit logs and correct fallback costs. Use mocks now and a separately authorized single smoke call for later live verification.

## Assumptions

- The enum is additive; cheap_api/local remain explicit and codex_cli is selected by primary workflow config, not a new optional CLI argument.
- One fallback transition inside the existing three-call total budget is part of this approved interface policy, distinct from the earlier model-order decision.
- The exact-string guard is entirely silent, including timing logs, and propagates only into child environments.
- No availability/pricing result is inferred; missing usage or rates remains null API-equivalent accounting.
- Each role implements its own paths after approval; only Role 1 applies shared interface/version edits.
