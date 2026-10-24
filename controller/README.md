# Controller

The v3 hook entry points are `requirements` and `claim-audit`. They use exactly
`gpt-6-luna` at low effort through one isolated `codex_cli` invocation each,
without regeneration, fallback or inherited historical routing. The hook owns
the session's two-call budget. Controller phase allocations and a one-shot client
also refuse duplicate invocations, including after failure or interruption.

```sh
SESSION_KEY=$(printf %s "$SESSION_ID" | shasum -a 256 | cut -d ' ' -f 1)
ARTIFACTS=".localharness/v3/sessions/$SESSION_KEY"
.venv/bin/python -m controller requirements --prompt request.txt \
  --session-id "$SESSION_ID" --artifacts "$ARTIFACTS" --config project-checks.json
.venv/bin/python -m controller claim-audit --requirements "$ARTIFACTS/requirements.json" \
  --final-message final.txt --session-id "$SESSION_ID" --artifacts "$ARTIFACTS"
```

`--config` is optional. `--artifacts` is the exact session directory beneath the
workspace root, not its parent. Native session IDs are hashed as UTF-8. The hook
must first publish a schema-valid, enabled `pin-check.json` with matching session
ID, version/model/pricing checks and hash-pinned evidence. Model-list evidence
must name the exact model. The pricing snapshot must match `controller/prices.yaml`;
its pin-check pricing reference is retained. No network version/pricing discovery
is attempted by these operations. SessionStart owns that verification.

Exit 0 publishes a schema-valid `ready`/`pending_questions` requirements table
or `complete` audit and prints its path plus newline. Pin/call/output failures
publish `unavailable`, report diagnostics on stderr and exit 2 with no success
stdout. Invalid CLI inputs use exit 1. JSON replacements are atomic; immutable
evidence and one complete, schema-valid `luna-calls.jsonl` line per invocation
are retained. A crash can leave a consumed allocation without a result; it never
permits an automatic second invocation. Such incomplete accounting needs host
review and cannot establish successful H3.

The client verifies observed native model metadata, not a generated model name.
Missing/malformed or conflicting identity fails closed as `pin_mismatch` and
disables later Luna calls in the pin advisory. A timeout without observed model
identity remains `timeout`; it cannot establish a successful pin. Usage from
native completion records is retained for failed/timed-out calls. Unknown tokens
or cost stay null. Known tokens are priced from the pinned snapshot, including
cached-input discounts; separate reasoning-token fields are not added twice.
`HARNESS_CONTROL_TIMEOUT_SECONDS` is read at construction (finite positive;
default 35 seconds). Existing measured `control_call` and deadline diagnostics
are retained. The under-ten-second latency target is unmeasured here.

Requirements prompt v1 supplies only text, six-kind classification, verbatim
source excerpts and unanswered questions. Code checks source correspondence,
assigns IDs and derives every check from original request clauses or explicit
trusted configuration. A safe substring selected inside an unsafe original
command cannot authorize a shortened command. No model-written command, hash,
check or answer is accepted. Unsupported syntax, ambiguous files and missing
oracles yield an `unavailable` check with a reason, not a guessed oracle.

Project configuration is a JSON object with `checks`, a list of bindings. Each
binding names `kind`, exact original `source_excerpt` and `check`; it is internal
controller configuration, not a new shared artifact schema. Example:

```json
{"checks": [
  {"kind": "behavior", "source_excerpt": "Return healthy status.",
   "check": {"type": "command", "argv": ["python", "-m", "unittest"], "cwd": ".", "expected_exit_code": 0}},
  {"kind": "constraint", "source_excerpt": "Preserve the health signature.",
   "check": {"type": "signature_snapshot", "path": "app.py", "identifiers": ["health()"]}},
  {"kind": "constraint", "source_excerpt": "Preserve inputs.",
   "check": {"type": "input_immutability", "argv": ["python", "-m", "unittest"], "inputs": ["data/input.json"]}}
]}
```

Commands are argv for later `shell=False` execution by the verifier, never run by
this controller. The supported grammar is direct Python unittest/pytest,
py_compile/compileall, pytest, and relative Python scripts without arguments.
Absolute paths, parent traversal, shell operators/substitutions, unsupported
modules/options and symlink escapes are unavailable. Expected exit defaults to
the configured zero-success convention; an explicit request exit code is honored.
Behavior tests must be bound to the exact covered excerpt; arbitrary project
tests are not proof of every behavior. Named files derive existence checks;
protected files capture pre-edit byte hashes. Signature baselines use Python AST
arguments, returns and async status with qualified identifiers, excluding bodies,
as serialized by `v3_checks.signature_bytes`. Other languages are unavailable.
Immutability probes capture declared fixture byte hashes before edits. The hook
and verifier must use the same signature serialization when integrating.

Questions remain pending until visible user answers arrive. The internal
`record_answers` helper records supplied answers without another call; callers
must supply actual user responses. Silence never chooses an interpretation.

The audit retains the exact final-message bytes/hash. Luna identifies claimed
requirement IDs and verbatim claims/citations, with a support opinion. Code
verifies citations against final text, confines referenced evidence to the session,
computes hashes from retained bytes and rejects explicit mismatched hashes.
Missing/escaping/forged citations are unsupported; absent citations cannot be
supported. Verified evidence does not turn an opinion into a deterministic pass.
The hook remains responsible for report/check consistency and evidence provenance.
After a changed final message, the original audit is preserved as stale with no
new call. Claims never trigger repair. No verifier imports occur in controller.

Calibration sets and scoring instructions are in
[fixtures/v3-calibration](../tests/controller/fixtures/v3-calibration/README.md).
Each phase has 40 requests derived from permitted public v1/v2 prompt excerpts
and authored variants. Host measurement has not been run; dated evidence records
null live precision/recall. Scorer round-trip numbers are synthetic validation.

## Historical version 1/2 operations

`contract`, `judge` and `handoff`, their backend selectors, tests and previous
measurement scripts remain compatible for retained v1/v2 artifacts. Their
regeneration/fallback policies do not apply to hooks. They are historical entry
points and are not part of the v3 control path.

Verification: `.venv/bin/python -m pytest tests/controller -q`.

## Assumptions

- User approval on 2026-10-25 authorizes v3 and the two supplied CLI shapes even
  while Role 1 updates older proposed-status prose concurrently.
- Only public v1/v2 prompt text is permitted calibration input; no graders or
  frozen v3 material may be consulted.
- Explicit configuration bindings establish oracle coverage; unsupported cases
  remain unavailable. The hook supplies pin evidence and actual user answers.
- This implementation exposes the requested primary CLI transport; historical
  HTTP fallback is not inherited. Live timing, price/pin evidence compatibility,
  hook integration and quality targets require host verification.
