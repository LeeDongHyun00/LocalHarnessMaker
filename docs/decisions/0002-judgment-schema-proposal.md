# Proposal: judgment schema and criterion input

Date: 2026-10-21 (Asia/Seoul).
Status: approved by the user on 2026-10-21

Approved record; shared schemas and interface documentation are published in
schemas/VERSION 1. Runtime implementation remains assigned to each owning role.

## Change and affected roles

Add schemas/judgment.schema.json. --criterion accepts exactly one complete
success_criteria item (id, description, check), without a contract wrapper or
array. The command is reserved for llm_judge; a mechanical criterion is an
input error before any model call. The existing four contract check types stay
unchanged. The output has exactly the six requested fields.

| Role | Change after approval |
| --- | --- |
| 1 Tech Lead | Publish the schema/example, extend shared validation, update docs and version the approved bundle |
| 3 Controller | Validate input/output and compute identity/usage outside model content |
| 4 Verifier | Serialize the full criterion; invoke the CLI through subprocess; map criterion_id to verdict item id and retain status/reason/evidence |
| 2 Plugin and 5 Evaluation | Consume verdicts unchanged and account for judge calls as control costs |

## Draft input JSON Schema

The relative reference resolves to the existing contract schema in schemas/;
no duplicated success-criterion definition is introduced.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Proposed judge criterion input",
  "allOf": [
    {"$ref": "contract.schema.json#/properties/success_criteria/items"},
    {"properties": {"check": {"properties": {"type": {"const": "llm_judge"}}}}}
  ]
}
```

## Draft output JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Proposed judgment",
  "type": "object",
  "additionalProperties": false,
  "required": ["criterion_id", "status", "reason", "evidence", "model", "usage"],
  "properties": {
    "criterion_id": {"type": "string", "minLength": 1},
    "status": {"enum": ["pass", "fail", "unverifiable"]},
    "reason": {"type": "string", "minLength": 1},
    "evidence": {"type": "string", "minLength": 1},
    "model": {"type": "string", "minLength": 1},
    "usage": {"$ref": "#/$defs/usage"}
  },
  "$defs": {
    "usage": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "usd",
        "latency_seconds",
        "cost_basis",
        "pricing_ref"
      ],
      "properties": {
        "input_tokens": {"type": ["integer", "null"], "minimum": 0},
        "cached_input_tokens": {"type": ["integer", "null"], "minimum": 0},
        "output_tokens": {"type": ["integer", "null"], "minimum": 0},
        "usd": {"type": ["number", "null"], "minimum": 0},
        "latency_seconds": {"type": "number", "minimum": 0},
        "cost_basis": {"const": "api_equivalent_usd"},
        "pricing_ref": {"type": ["string", "null"], "minLength": 1}
      }
    }
  }
}
```

Runtime checks require criterion_id to equal input id and evidence to contain
llm_judge. Model content supplies status/reason/evidence only; code supplies
criterion_id, model and usage. model identifies the selected final judgment
model; a conflicting provider-reported identity fails the operation instead of
being relabeled. Preserve fail and unverifiable; neither is an overall pass.

usage sums every generation/regeneration/fallback call used for this judgment.
Per-call private logs retain actual backend/model and price snapshot so mixed
models can be costed correctly. latency_seconds measures total wall time.
Cache tokens are a subset of input_tokens; output token counts already include
any billed reasoning tokens. Unknown counts/cost stay null, never zero.

All usd values are API-equivalent USD, including logged-in CLI and local calls.
Use pinned per-model input/cached/output rates. If usage or applicable pricing
is unavailable, usd is null; pricing_ref is null when no snapshot exists.
Do not infer zero cost from a subscription login or unavailable local price.

## Example

Input and output are synthetic. fixture-rates-v1 uses 1 / 0.5 / 2 USD per
million input/cached/output tokens, not actual model prices. Thus
(1000 + 100 + 240) / 1000000 = 0.00134 USD.

### Criterion input example

```json
{
  "id": "SC-4",
  "description": "Preserve existing routes.",
  "check": {
    "type": "llm_judge",
    "rubric": "Review the supplied before/after diff. Pass only if existing routes are preserved. Missing comparison evidence is unverifiable."
  }
}
```

### Judgment output example

```json
{
  "criterion_id": "SC-4",
  "status": "unverifiable",
  "reason": "The before/after comparison is missing.",
  "evidence": "SYNTHETIC llm_judge: review/diff.txt is absent.",
  "model": "gpt-6-luna",
  "usage": {
    "input_tokens": 1200,
    "cached_input_tokens": 200,
    "output_tokens": 120,
    "usd": 0.00134,
    "latency_seconds": 0.8,
    "cost_basis": "api_equivalent_usd",
    "pricing_ref": "fixture-rates-v1"
  }
}
```

Illustrative command: python -m controller judge --criterion criterion.json
--artifact review/ --backend codex_cli --out judgment.json. The backend addition
is proposed separately in 0004. Success prints the --out path and exits 0 even
for fail/unverifiable; malformed input exits 1; backend failure or exhausted
output-validation retries exits 2. Logs go to stderr. Missing comparison
material can yield unverifiable; unreadable input paths are CLI input errors.

## Tests to add after approval

- Role 1 tests/lead: validate referenced input and output example; reject arrays/wrappers, missing/extra fields, mechanical checks, unknown statuses, negative usage and invalid token types. Extend shared schema/example inventory without losing existing coverage.
- Role 3 tests/controller: mocked backends for all statuses, criterion-ID equality, code-owned model/usage, llm_judge marker, null unknown accounting, cache bounds, model mismatch and summed retry/fallback usage. Check exit codes and one-path stdout separately from missing-artifact judgments.
- Role 4 tests/verifier: subprocess fixtures for pass/fail/unverifiable, invalid/wrong-ID judgment rejection, unchanged reason/evidence and no controller imports.
- Role 5 tests/eval: count every judge call once as control cost at API-equivalent rates, including unsuccessful/fallback calls.

Version 1 publishes the input/output schemas and examples and implements the
lead-owned validation tests. Runtime/integration tests remain assigned to their
owning roles; publication does not claim those implementations are complete.

## Assumptions

- Only llm_judge items execute this command, consistent with its existing purpose; the input is still a full contract criterion object.
- Nullable usage preserves missing accounting. Per-call logs support mixed models without unspecified judgment top-level fields.
- Approval of the three proposals precedes shared interface publication and a version increment; this record alone is not approval.
