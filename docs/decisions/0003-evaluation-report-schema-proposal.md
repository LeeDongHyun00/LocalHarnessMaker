# Proposal: evaluation report, grader access audit and confidence intervals

Date: 2026-10-21 (Asia/Seoul).
Status: approved by the user on 2026-10-21

Approved record; shared schemas and interface documentation are published in
schemas/VERSION 1. Runtime implementation remains assigned to each owning role.

## Decision context and affected roles

The 2026-10-21 user decision selects access audit for STOP-E4 and supersedes the
deny-read prerequisite in 0001-eval-isolation-proposal.md. Private graders live
outside the repository and enter only a separate grading copy after codex exec
exits. Logged access to a private grader path invalidates the run. This audits
observed activity; it does not assert read denial or complete log visibility.

| Role | Change after approval |
| --- | --- |
| 1 Tech Lead | Publish schemas/evaluation-report.schema.json/example, extend validation and version the approved interface |
| 5 Evaluation | Write report.json, retain hash-pinned event logs, audit accesses and compute metrics; externalize private graders before runs |
| 3 Controller | Supply per-call code-computed model/usage/pricing records |
| 4 Verifier | Supply verdict/done-claim evidence without private graders during execution |
| 2 Plugin | Honor nested bypass and preserve the hooks-independent runner |

The existing eval CLI arguments/exit codes remain unchanged. On success it
prints the --out directory once; report.json is proposed as the canonical
JSON inside that directory. An invalid task is a recorded outcome, not an
input-error exit. Inability to write/validate the report is an internal error.
No task contents are included or shared with Role 3.

## Draft report JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Proposed evaluation report",
  "type": "object",
  "additionalProperties": false,
  "required": ["metadata", "tasks", "metrics", "accounting", "validity"],
  "properties": {
    "metadata": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "run_id",
        "created_at",
        "config_name",
        "config_sha256",
        "task_set_sha256",
        "git_commit",
        "codex_version",
        "executor_model",
        "reasoning_effort",
        "control_backend",
        "control_model",
        "seed",
        "reinstruction_limit",
        "cost_basis",
        "pricing",
        "confidence",
        "parity_comparator"
      ],
      "properties": {
        "run_id": {"type": "string", "minLength": 1},
        "created_at": {"type": "string", "format": "date-time"},
        "config_name": {"type": "string", "minLength": 1},
        "config_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "task_set_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "git_commit": {"type": "string", "minLength": 1},
        "codex_version": {"type": "string", "minLength": 1},
        "executor_model": {"type": "string", "minLength": 1},
        "reasoning_effort": {"enum": ["low", "medium", "high", "xhigh", "max"]},
        "control_backend": {"enum": ["none", "codex_cli", "cheap_api", "local"]},
        "control_model": {"type": ["string", "null"], "minLength": 1},
        "seed": {"type": "integer"},
        "reinstruction_limit": {"type": "integer", "minimum": 0},
        "cost_basis": {"const": "api_equivalent_usd"},
        "pricing": {
          "type": "object",
          "additionalProperties": false,
          "required": ["snapshot_id", "source", "checked_on", "rates"],
          "properties": {
            "snapshot_id": {"type": "string", "minLength": 1},
            "source": {"type": "string", "minLength": 1},
            "checked_on": {"type": "string", "format": "date"},
            "rates": {
              "type": "array",
              "minItems": 0,
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": ["model", "input_per_million_usd", "cached_input_per_million_usd", "output_per_million_usd"],
                "properties": {
                  "model": {"type": "string", "minLength": 1},
                  "input_per_million_usd": {"type": "number", "minimum": 0},
                  "cached_input_per_million_usd": {"type": "number", "minimum": 0},
                  "output_per_million_usd": {"type": "number", "minimum": 0}
                }
              }
            }
          }
        },
        "confidence": {
          "type": "object",
          "additionalProperties": false,
          "required": ["level", "method", "resamples", "seed"],
          "properties": {
            "level": {"const": 0.95},
            "method": {"const": "task_cluster_percentile_bootstrap"},
            "resamples": {"type": "integer", "minimum": 1000},
            "seed": {"type": "integer"}
          }
        },
        "parity_comparator": {"anyOf": [{"$ref": "#/$defs/artifact"}, {"type": "null"}]}
      }
    },
    "tasks": {"type": "array", "minItems": 0, "items": {"$ref": "#/$defs/task"}},
    "metrics": {
      "type": "object",
      "additionalProperties": false,
      "required": ["pass_rate", "false_done_rate", "cost_per_pass", "avg_attempts", "handoff_success", "parity"],
      "properties": {
        "pass_rate": {
          "allOf": [
            {"$ref": "#/$defs/metric"},
            {
              "properties": {
                "sample_unit": {"const": "valid_task"},
                "value": {"type": ["number", "null"], "minimum": 0, "maximum": 1}
              }
            }
          ]
        },
        "false_done_rate": {
          "allOf": [
            {"$ref": "#/$defs/metric"},
            {
              "properties": {
                "sample_unit": {"const": "claimed_criterion"},
                "value": {"type": ["number", "null"], "minimum": 0, "maximum": 1}
              }
            }
          ]
        },
        "cost_per_pass": {
          "allOf": [
            {"$ref": "#/$defs/metric"},
            {
              "properties": {"sample_unit": {"const": "attempted_task"}, "value": {"type": ["number", "null"], "minimum": 0}}
            }
          ]
        },
        "avg_attempts": {
          "allOf": [
            {"$ref": "#/$defs/metric"},
            {
              "properties": {"sample_unit": {"const": "valid_task"}, "value": {"type": ["number", "null"], "minimum": 1}}
            }
          ]
        },
        "handoff_success": {
          "allOf": [
            {"$ref": "#/$defs/metric"},
            {
              "properties": {
                "sample_unit": {"const": "eligible_two_session_task"},
                "value": {"type": ["number", "null"], "minimum": 0, "maximum": 1}
              }
            }
          ]
        },
        "parity": {
          "allOf": [
            {"$ref": "#/$defs/metric"},
            {
              "properties": {
                "sample_unit": {"const": "matched_task"},
                "value": {"type": ["number", "null"], "minimum": -1, "maximum": 1}
              }
            }
          ]
        }
      }
    },
    "accounting": {
      "type": "object",
      "additionalProperties": false,
      "required": ["attempted_tasks", "valid_tasks", "invalid_tasks", "total_cost_usd"],
      "properties": {
        "attempted_tasks": {"type": "integer", "minimum": 0},
        "valid_tasks": {"type": "integer", "minimum": 0},
        "invalid_tasks": {"type": "integer", "minimum": 0},
        "total_cost_usd": {"type": ["number", "null"], "minimum": 0}
      }
    },
    "validity": {
      "type": "object",
      "additionalProperties": false,
      "required": ["status", "reasons"],
      "properties": {
        "status": {"enum": ["valid", "invalid"]},
        "reasons": {"type": "array", "items": {"type": "string", "minLength": 1}}
      }
    }
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
    },
    "artifact": {
      "type": "object",
      "additionalProperties": false,
      "required": ["path", "sha256"],
      "properties": {"path": {"type": "string", "minLength": 1}, "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}}
    },
    "segment": {
      "type": "object",
      "additionalProperties": false,
      "required": ["attempt", "session_id", "started_at", "exited_at", "exit_code", "events"],
      "properties": {
        "attempt": {"type": "integer", "minimum": 1},
        "session_id": {"type": "string", "minLength": 1},
        "started_at": {"type": "string", "format": "date-time"},
        "exited_at": {"type": "string", "format": "date-time"},
        "exit_code": {"type": "integer"},
        "events": {"$ref": "#/$defs/artifact"}
      }
    },
    "accessMatch": {
      "type": "object",
      "additionalProperties": false,
      "required": ["event_log", "line", "tool", "path", "operation", "evidence"],
      "properties": {
        "event_log": {"type": "string", "minLength": 1},
        "line": {"type": "integer", "minimum": 1},
        "tool": {"type": "string", "minLength": 1},
        "path": {"type": "string", "minLength": 1},
        "operation": {"enum": ["read", "list", "search", "execute", "write", "unknown"]},
        "evidence": {"type": "string", "minLength": 1}
      }
    },
    "audit": {
      "type": "object",
      "additionalProperties": false,
      "required": ["method", "status", "private_grader_roots", "matches", "reason"],
      "properties": {
        "method": {"const": "access_audit"},
        "status": {"enum": ["clean", "access_detected", "inconclusive"]},
        "private_grader_roots": {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1}},
        "matches": {"type": "array", "minItems": 0, "items": {"$ref": "#/$defs/accessMatch"}},
        "reason": {"type": ["string", "null"], "minLength": 1}
      },
      "allOf": [
        {
          "if": {"properties": {"status": {"const": "clean"}}},
          "then": {"properties": {"matches": {"maxItems": 0}, "reason": {"type": "null"}}}
        },
        {
          "if": {"properties": {"status": {"const": "access_detected"}}},
          "then": {"properties": {"matches": {"minItems": 1}, "reason": {"type": "string", "minLength": 1}}}
        },
        {
          "if": {"properties": {"status": {"const": "inconclusive"}}},
          "then": {"properties": {"reason": {"type": "string", "minLength": 1}}}
        }
      ]
    },
    "metric": {
      "type": "object",
      "additionalProperties": false,
      "required": ["value", "sample_size", "sample_unit", "ci95", "undefined_reason"],
      "properties": {
        "value": {"type": ["number", "null"]},
        "sample_size": {"type": "integer", "minimum": 0},
        "sample_unit": {"enum": ["valid_task", "claimed_criterion", "attempted_task", "eligible_two_session_task", "matched_task"]},
        "ci95": {
          "type": "object",
          "additionalProperties": false,
          "required": ["level", "lower", "upper", "method"],
          "properties": {
            "level": {"const": 0.95},
            "lower": {"type": ["number", "null"]},
            "upper": {"type": ["number", "null"]},
            "method": {"const": "task_cluster_percentile_bootstrap"}
          }
        },
        "undefined_reason": {"type": ["string", "null"], "minLength": 1}
      },
      "allOf": [
        {
          "if": {"properties": {"value": {"type": "null"}}},
          "then": {
            "properties": {
              "ci95": {"properties": {"lower": {"type": "null"}, "upper": {"type": "null"}}},
              "undefined_reason": {"type": "string", "minLength": 1}
            }
          },
          "else": {
            "properties": {
              "sample_size": {"minimum": 1},
              "ci95": {"properties": {"lower": {"type": "number"}, "upper": {"type": "number"}}},
              "undefined_reason": {"type": "null"}
            }
          }
        },
        {"if": {"properties": {"sample_size": {"const": 0}}}, "then": {"properties": {"value": {"type": "null"}}}}
      ]
    },
    "call": {
      "type": "object",
      "additionalProperties": false,
      "required": ["call_id", "purpose", "backend", "model", "status", "usage"],
      "properties": {
        "call_id": {"type": "string", "minLength": 1},
        "purpose": {"enum": ["executor", "contract", "handoff", "judge"]},
        "backend": {"enum": ["codex_cli", "cheap_api", "local"]},
        "model": {"type": "string", "minLength": 1},
        "status": {"enum": ["completed", "failed", "timeout"]},
        "usage": {"$ref": "#/$defs/usage"}
      }
    },
    "grading": {
      "type": "object",
      "additionalProperties": false,
      "required": ["copy_path", "copied_at", "grader_source_outside_repo", "result", "passed_tests", "failed_tests", "log"],
      "properties": {
        "copy_path": {"type": "string", "minLength": 1},
        "copied_at": {"type": "string", "format": "date-time"},
        "grader_source_outside_repo": {"const": true},
        "result": {"enum": ["pass", "fail", "error"]},
        "passed_tests": {"type": "integer", "minimum": 0},
        "failed_tests": {"type": "integer", "minimum": 0},
        "log": {"$ref": "#/$defs/artifact"}
      }
    },
    "task": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "task_id",
        "task_type",
        "two_session",
        "outcome",
        "invalid_reasons",
        "attempts",
        "executor_segments",
        "grader_access_audit",
        "grading",
        "done_claims",
        "calls",
        "costs",
        "artifacts",
        "handoff"
      ],
      "properties": {
        "task_id": {"type": "string", "minLength": 1},
        "task_type": {"type": "string", "minLength": 1},
        "two_session": {"type": "boolean"},
        "outcome": {"enum": ["pass", "fail", "timeout", "error", "invalid"]},
        "invalid_reasons": {"type": "array", "minItems": 0, "items": {"type": "string", "minLength": 1}},
        "attempts": {"type": "integer", "minimum": 1},
        "executor_segments": {"type": "array", "minItems": 0, "items": {"$ref": "#/$defs/segment"}},
        "grader_access_audit": {"$ref": "#/$defs/audit"},
        "grading": {"anyOf": [{"$ref": "#/$defs/grading"}, {"type": "null"}]},
        "done_claims": {
          "type": "object",
          "additionalProperties": false,
          "required": ["claimed_items", "claimed_without_evidence"],
          "properties": {
            "claimed_items": {"type": "integer", "minimum": 0},
            "claimed_without_evidence": {"type": "integer", "minimum": 0}
          }
        },
        "calls": {"type": "array", "minItems": 0, "items": {"$ref": "#/$defs/call"}},
        "costs": {
          "type": "object",
          "additionalProperties": false,
          "required": ["executor_usd", "control_usd", "total_usd"],
          "properties": {
            "executor_usd": {"type": ["number", "null"], "minimum": 0},
            "control_usd": {"type": ["number", "null"], "minimum": 0},
            "total_usd": {"type": ["number", "null"], "minimum": 0}
          }
        },
        "artifacts": {"type": "array", "minItems": 0, "items": {"$ref": "#/$defs/artifact"}},
        "handoff": {"anyOf": [{"$ref": "#/$defs/handoff"}, {"type": "null"}]}
      },
      "allOf": [
        {
          "if": {
            "properties": {"grader_access_audit": {"properties": {"status": {"enum": ["access_detected", "inconclusive"]}}}}
          },
          "then": {"properties": {"outcome": {"const": "invalid"}}}
        },
        {
          "if": {"properties": {"outcome": {"const": "invalid"}}},
          "then": {"properties": {"invalid_reasons": {"minItems": 1}, "grading": {"type": "null"}}},
          "else": {
            "properties": {
              "invalid_reasons": {"maxItems": 0},
              "executor_segments": {"minItems": 1},
              "grader_access_audit": {"properties": {"status": {"const": "clean"}}}
            }
          }
        },
        {
          "if": {"properties": {"outcome": {"enum": ["pass", "fail"]}}},
          "then": {"properties": {"grading": {"$ref": "#/$defs/grading"}}}
        },
        {
          "if": {"properties": {"two_session": {"const": true}, "outcome": {"not": {"const": "invalid"}}}},
          "then": {"properties": {"handoff": {"$ref": "#/$defs/handoff"}}}
        },
        {
          "if": {"properties": {"two_session": {"const": false}}},
          "then": {"properties": {"handoff": {"type": "null"}}}
        }
      ]
    },
    "handoff": {
      "type": "object",
      "additionalProperties": false,
      "required": ["day2_pass", "user_restated_day1_context", "evidence"],
      "properties": {
        "day2_pass": {"type": "boolean"},
        "user_restated_day1_context": {"type": "boolean"},
        "evidence": {"$ref": "#/$defs/artifact"}
      }
    }
  },
  "allOf": [
    {
      "if": {"properties": {"tasks": {"contains": {"properties": {"outcome": {"const": "invalid"}}}}}},
      "then": {"properties": {"validity": {"properties": {"status": {"const": "invalid"}, "reasons": {"minItems": 1}}}}},
      "else": {"properties": {"validity": {"properties": {"status": {"const": "valid"}, "reasons": {"maxItems": 0}}}}}
    }
  ]
}
```

## Runtime invariants and access audit

1. Resolve canonical private source and grading-copy paths, including symlink aliases. Sources must be outside the repository and every public executor workspace; grading copies must also be separate from those workspaces. Existing prototype graders are untouched here. Role 5 must externalize them before paid runs under its ownership and any required deletion approval.
2. Capture every execution/retry/resume --json stream completely, retain its SHA-256, and record process start/termination in executor_segments. Audit every segment, including nested tool/controller activity visible there. Do not expose grader/grading-copy paths or test contents through executor/controller prompts or context.
3. Inspect tool-access events and their arguments/results for canonical private source/copy paths, children, symlink aliases, listing/search/execution or attempted reads. Include denied/failed accesses. Record event log, 1-based line, tool, path, operation and evidence. Assistant prose mentioning a path alone is not an access event; raw substring matching of all prose is insufficient.
4. A match makes audit.status=access_detected and outcome=invalid. Missing/malformed/truncated/unsupported logs, incomplete capture or unresolved access operands/aliases make status=inconclusive and outcome=invalid. Store invalid_reasons and no grading result. clean means no access observed in complete supported logs, not proof of isolation.
5. Only after the executor and spawned work terminate, copy the public artifact to a fresh trusted grading copy and copy private graders there. copied_at must be strictly after the associated executor exited_at. Never run/resume Codex in any grading copy or return private test content to the public workspace. Grade a later public-workspace attempt in another fresh copy, after its exit; retain earlier grading artifacts with hashes.
6. Runtime checks enforce unique task/call IDs, complete segments, claimed_without_evidence <= claimed_items, grading counts/result versus outcome, observed executor model/effort versus config, costs and metric arithmetic. Configuration mismatches invalidate a task even with a clean access audit. Pass/fail requires trusted grading and a clean audit.
7. Any invalid task marks the aggregate report validity=invalid with reasons; it cannot be used as a valid headline comparison. Metrics on its audited valid subset are diagnostic only, and a fresh valid run is required for reported comparisons. Audit-clean failures/timeouts/executor errors count as valid quality samples. Invalid tasks count in attempted/invalid totals and never as valid passes. Keep every invalid/failed/retried/fallback call's cost in total accounting and cost-per-pass; invalidating a run cannot erase its cost.

For two-session tasks, handoff records day-2 pass, whether day-1 context was
restated, and a hash-pinned evidence artifact. One-session tasks use null.
Missing handoff evidence invalidates that two-session task rather than removing
a difficult case from the denominator. Where an invalid two-session run never
reaches day 2, the runner must record incomplete handoff observation as null;
the task schema permits that only for invalid outcomes.

## Six metrics and uncertainty

| Metric | Definition | sample_size / unit |
| --- | --- | --- |
| pass_rate | Passing valid tasks / all valid tasks | Valid tasks / valid_task |
| false_done_rate | Claimed items with reason claimed_without_evidence / claimed items, from valid tasks | Claimed criterion items / claimed_criterion |
| cost_per_pass | All attempted tasks' executor plus control API-equivalent USD / passing valid tasks | All attempted tasks, including invalid / attempted_task |
| avg_attempts | Mean executor attempts per valid task; controller regeneration is cost, not executor attempt | Valid tasks / valid_task |
| handoff_success | Eligible valid two-session tasks passing without restating day-1 context / eligible valid two-session tasks | Eligible two-session tasks / eligible_two_session_task |
| parity | Local-control pass_rate minus cheap_api-control pass_rate on matched valid task IDs | Matched tasks / matched_task |

Keep the existing local-minus-cheap_api parity definition. Selecting codex_cli
as primary does not silently redefine it. A report lacking the required pair
has undefined parity. Pin the comparator report/hash and require matching task
set, seed, executor model/effort and Codex version. The local report references
the cheap_api comparator when computing this metric.

Use a seeded task-cluster percentile bootstrap, default 10,000 resamples and
minimum 1,000. Resample task IDs, retaining each task's claims/attempts/sessions;
use paired task resampling for parity. For cost_per_pass resample all attempted
task clusters, preserving invalid costs and valid-pass indicators. Recompute
ratios for every replicate; CI endpoints are the 2.5th/97.5th percentiles.
If the original denominator or any bootstrap denominator is zero, emit null
value and CI bounds with a specific undefined_reason rather than silently
removing replicates. Thus a point estimate whose chosen finite interval cannot
be formed is withheld explicitly. Missing cost similarly yields null
cost_per_pass. ci95 always specifies 0.95 and the method. Runtime checks enforce
lower <= upper and metric-specific bounds. A one-task bootstrap may be
degenerate and does not establish generalization.

All money fields are API-equivalent USD. Compute each call with the pinned
per-model rates:
((input_tokens - cached_input_tokens) * input_rate + cached_input_tokens *
cached_rate + output_tokens * output_rate) / 1000000.
Include executor, contract, handoff, judge, retries and fallback calls once.
Unknown usage/price makes that cost and affected aggregates null, never zero.
Use no subscription discount assumption. For local Gemma use an explicitly
sourced equivalent API price for that model if available, otherwise null.

## Example report

Every value is synthetic. fixture-rates-v1 uses 1 / 0.5 / 2 USD per million
input/cached/output tokens for both models; these are not actual model prices.
Executor 0.00114 plus controller 0.00028 equals 0.00142 USD. Paths/hashes are
illustrative and do not assert existing artifacts. The one-task CIs are
intentionally degenerate; ineligible metrics have sample_size=0 and null bounds.

```json
{
  "metadata": {
    "run_id": "synthetic-proposal-example",
    "created_at": "2026-10-21T16:00:00+09:00",
    "config_name": "system-codex-cli",
    "config_sha256": "1111111111111111111111111111111111111111111111111111111111111111",
    "task_set_sha256": "2222222222222222222222222222222222222222222222222222222222222222",
    "git_commit": "synthetic-fixture",
    "codex_version": "codex-cli 0.162.0-alpha.17.2",
    "executor_model": "gpt-6.1-sol",
    "reasoning_effort": "medium",
    "control_backend": "codex_cli",
    "control_model": "gpt-6-luna",
    "seed": 42,
    "reinstruction_limit": 3,
    "cost_basis": "api_equivalent_usd",
    "pricing": {
      "snapshot_id": "fixture-rates-v1",
      "source": "Synthetic fixture rates, not live pricing.",
      "checked_on": "2026-10-21",
      "rates": [
        {
          "model": "gpt-6.1-sol",
          "input_per_million_usd": 1,
          "cached_input_per_million_usd": 0.5,
          "output_per_million_usd": 2
        },
        {
          "model": "gpt-6-luna",
          "input_per_million_usd": 1,
          "cached_input_per_million_usd": 0.5,
          "output_per_million_usd": 2
        }
      ]
    },
    "confidence": {"level": 0.95, "method": "task_cluster_percentile_bootstrap", "resamples": 10000, "seed": 42},
    "parity_comparator": null
  },
  "tasks": [
    {
      "task_id": "synthetic-feature-1",
      "task_type": "feature_plus_test",
      "two_session": false,
      "outcome": "pass",
      "invalid_reasons": [],
      "attempts": 1,
      "executor_segments": [
        {
          "attempt": 1,
          "session_id": "synthetic-session-1",
          "started_at": "2026-10-21T15:59:00+09:00",
          "exited_at": "2026-10-21T15:59:10+09:00",
          "exit_code": 0,
          "events": {
            "path": "events/synthetic-feature-1.jsonl",
            "sha256": "3333333333333333333333333333333333333333333333333333333333333333"
          }
        }
      ],
      "grader_access_audit": {
        "method": "access_audit",
        "status": "clean",
        "private_grader_roots": ["/private-eval-fixture/graders"],
        "matches": [],
        "reason": null
      },
      "grading": {
        "copy_path": "/private-eval-fixture/grading/synthetic-feature-1",
        "copied_at": "2026-10-21T15:59:11+09:00",
        "grader_source_outside_repo": true,
        "result": "pass",
        "passed_tests": 3,
        "failed_tests": 0,
        "log": {
          "path": "grading/synthetic-feature-1.log",
          "sha256": "4444444444444444444444444444444444444444444444444444444444444444"
        }
      },
      "done_claims": {"claimed_items": 1, "claimed_without_evidence": 0},
      "calls": [
        {
          "call_id": "synthetic-exec-1",
          "purpose": "executor",
          "backend": "codex_cli",
          "model": "gpt-6.1-sol",
          "status": "completed",
          "usage": {
            "input_tokens": 1000,
            "cached_input_tokens": 120,
            "output_tokens": 100,
            "usd": 0.00114,
            "latency_seconds": 10,
            "cost_basis": "api_equivalent_usd",
            "pricing_ref": "fixture-rates-v1"
          }
        },
        {
          "call_id": "synthetic-contract-1",
          "purpose": "contract",
          "backend": "codex_cli",
          "model": "gpt-6-luna",
          "status": "completed",
          "usage": {
            "input_tokens": 200,
            "cached_input_tokens": 0,
            "output_tokens": 40,
            "usd": 0.00028,
            "latency_seconds": 0.8,
            "cost_basis": "api_equivalent_usd",
            "pricing_ref": "fixture-rates-v1"
          }
        }
      ],
      "costs": {"executor_usd": 0.00114, "control_usd": 0.00028, "total_usd": 0.00142},
      "artifacts": [],
      "handoff": null
    }
  ],
  "metrics": {
    "pass_rate": {
      "value": 1,
      "sample_size": 1,
      "sample_unit": "valid_task",
      "ci95": {"level": 0.95, "lower": 1, "upper": 1, "method": "task_cluster_percentile_bootstrap"},
      "undefined_reason": null
    },
    "false_done_rate": {
      "value": 0,
      "sample_size": 1,
      "sample_unit": "claimed_criterion",
      "ci95": {"level": 0.95, "lower": 0, "upper": 0, "method": "task_cluster_percentile_bootstrap"},
      "undefined_reason": null
    },
    "cost_per_pass": {
      "value": 0.00142,
      "sample_size": 1,
      "sample_unit": "attempted_task",
      "ci95": {"level": 0.95, "lower": 0.00142, "upper": 0.00142, "method": "task_cluster_percentile_bootstrap"},
      "undefined_reason": null
    },
    "avg_attempts": {
      "value": 1,
      "sample_size": 1,
      "sample_unit": "valid_task",
      "ci95": {"level": 0.95, "lower": 1, "upper": 1, "method": "task_cluster_percentile_bootstrap"},
      "undefined_reason": null
    },
    "handoff_success": {
      "value": null,
      "sample_size": 0,
      "sample_unit": "eligible_two_session_task",
      "ci95": {"level": 0.95, "lower": null, "upper": null, "method": "task_cluster_percentile_bootstrap"},
      "undefined_reason": "No eligible two-session tasks."
    },
    "parity": {
      "value": null,
      "sample_size": 0,
      "sample_unit": "matched_task",
      "ci95": {"level": 0.95, "lower": null, "upper": null, "method": "task_cluster_percentile_bootstrap"},
      "undefined_reason": "No paired local/cheap_api comparator report."
    }
  },
  "accounting": {"attempted_tasks": 1, "valid_tasks": 1, "invalid_tasks": 0, "total_cost_usd": 0.00142},
  "validity": {"status": "valid", "reasons": []}
}
```

## Tests to add after approval

- Role 1 tests/lead: validate example/formats and require all six metrics, sample sizes, 95-percent CI metadata, costs and audit fields. Reject unknown fields, negative counts/costs, wrong metric units, non-95-percent intervals, pass with detected access, missing invalid reasons and grading on invalid tasks.
- Role 5 tests/eval audit: clean log, allowed/denied reads, listing/search, path traversal, aliases/symlinks, resumed-session and retry accesses, nested events, assistant-only path prose, missing/truncated/malformed/unsupported streams and unresolved operands. Assert graders copied strictly after exit and no grading copy exposed to any future executor turn.
- Role 5 tests/eval metrics: deterministic fixture bootstrap/quantiles, paired parity, interval ordering, task clustering, zero original/bootstrap denominators, null accounting, invalid exclusion from quality and inclusion in cost, metadata comparability, counts, unique IDs, invalid aggregate reports and evidence-backed handoff outcomes.
- Role 5 tests/eval accounting: cached input is an input subset; retries, fallback, judge and handoff are each billed once; no CLI/local free-cost assumption. Recompute 0.00142 USD from the example's synthetic snapshot.
- Roles 3/4 integration: transfer code-owned usage and done-claim evidence without private grader content in inputs; prove the runner operates with hooks bypassed.

No grader is moved/deleted/copied and no paid run is started by this proposal.
Lead-owned schema/example tests are implemented in version 1. Runtime and
integration tests remain assigned to each owning role after this approval.

## Assumptions

- The approved access audit replaces proof of read denial; incomplete observation invalidates rather than certifies a run.
- report.json is proposed within the existing --out directory, without a CLI flag change.
- Metrics state their own sample units while task IDs remain the bootstrap clusters.
- Null values explain missing/undefined measurements, including the proposed conservative zero-bootstrap-denominator policy.
- Original parity compares local and cheap_api; transport selection is a separate decision.
