# 0007: Scope cuts and completion schedule

Status: approved by the user on 2026-10-23

## Context

[Integration review 1](../weekly/2026-10-27.md), written by Claude on
2026-10-23 ahead of its scheduled review date, proposed five scope decisions.
The user approved all five on 2026-10-23 and also stated that usage limits are
no longer a concern. Work continues to completion up to, but not including,
the local LLM stage. The review's usage-cap estimates are historical context,
not a reason to stop the remaining approved work.

## Decision

1. Drop local Gemma 4 12B (Role 3 D-3) and QLoRA (Role 3 D-5). Do not run
   local-control comparisons; report parity as **not measured**.
2. Run baseline C on a stratified 20-task subset: five tasks per task type,
   drawn from 20 different families. The user fills the 20 static templates
   once. Claude does not fill them, preserving evaluator independence.
   Compare the harness with C on those same 20 tasks, paired.
3. Run baseline B on the 100 single-session tasks only. Compare
   `handoff_success` between the harness and baseline A.
4. Use this execution schedule, superseding conflicting original plan dates:

   | Window | Work |
   |---|---|
   | W1, through 2026-10-30 | Harness-mode smoke and full A |
   | W2, through 2026-11-06 | Full harness and C on the approved subset |
   | W3, through 2026-11-13 | B on single-session tasks and final analysis |

5. An `OPENAI_API_KEY` for executor `codex exec` is only a fallback if the
   subscription cap blocks a run. This does not replace the controller's
   existing same-model HTTP transport fallback policy. Keys remain in the
   environment and are never written into the repository.

## Scope and verification

This decision changes scope and documentation only. Version 1 schemas, CLI
selectors (including `local`), hook inputs/outputs and `schemas/VERSION` remain
unchanged. Retain the parity field and its local-minus-cheap_api definition;
use the existing undefined-metric representation with null value/bounds and
an explanation that local measurement was dropped by this decision.
The harness-versus-C paired comparison does not redefine parity.

Owning roles apply the approved scope to their implementations and run plans.
This record does not claim any new evaluation result, live model call or host
verification. The full evaluation already running on the host is untouched.

## Assumptions

- Approval and the usage-limit clarification are user-supplied facts dated
  2026-10-23; no new budget, run result or backend availability is inferred.
