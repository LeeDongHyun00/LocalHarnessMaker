# 0005: Direction change to a GPT operating harness

Status: approved by the user on 2026-10-21

Source: the 2026-10-21 callouts and project overview in the supplied read-only Notion export, “AI Project: GPT Operating Harness” (last edited 2026-10-21; exported by Claude Code). Approval and implementation choices match [the handoff, section 3](../handoff/2026-10-21-claude-code-handoff.md#3-decisions-already-made-by-the-user). This records the decision; it does not change version 1 interfaces or certify implementation.

The old direction was a local LLM that raises a cheap model's quality. The new direction is a cheap control layer that makes a capable executor, GPT-6.1 Sol, finish tasks, follow user intent and hand off work between sessions. The rationale is that a prompt cannot raise a weak model's capability ceiling, while a harness can correct a strong model's behavior through explicit contracts, independent verification and continuity.

The design identifies two weaknesses. The evidence below is reported by the supplied design, not independently reproduced in this session.

| Weakness | Evidence recorded in the design |
|---|---|
| Stops after the minimum and skips tests/verification | An independent comparison described minimal completion and six missed bugs out of 36 planted bugs. An effort experiment scored low 3.0 and max 8.7, attributing the difference to thoroughness and verification; higher effort did not monotonically improve quality. |
| Fills unspecified gaps, fails to execute procedures and loses continuity between sessions | The design cites prompting guidance recommending contract-style prompts and `AGENTS.md`, plus system-card figures of 23.5% ignored prohibitions and 44.8% compliance with reasoning-process instructions. These motivate explicit constraints and handoffs; they do not themselves measure handoff success. |

Delivery is a **Codex plugin: three hooks plus a skill, with no web UI**. `UserPromptSubmit` supplies the contract, the skill presents it for correction/approval, `Stop` verifies and re-instructs unmet criteria within a retry limit and saves the handoff on completion, and `SessionStart` injects the validated handoff. `SessionEnd` is observe-only. The design chose this form because the target workflow is coding-agent work and Sol availability was described as Codex/ChatGPT Work. Prior UI sketches are information references only.

Stage one uses **`gpt-6-luna` through the user's Codex login**, with the same model over HTTP API as fallback. Stage two substitutes **local Gemma 4 12B** with retrieved examples and constrained decoding. Optional QLoRA is subordinate to the delivery schedule. Subscription calls are accounted for at API-equivalent cost, not treated as free. Facts such as effort, token counts and cost belong in code; the control model structures requests, judges ambiguous criteria and summarizes handoffs.

Evaluation uses **access-audit isolation instead of read denial**, superseding decision 0001's deny-read prerequisite. Private graders stay outside the repository/public workspaces and enter fresh trusted grading copies only after executor and spawned work exit. All executor/retry/resume event streams are retained and audited; observed access invalidates the task/report, while incomplete evidence is inconclusive and invalid. A clean audit means no access was observed, not that filesystem reads were blocked.

**Defensive-wording suppression is excluded.** The design says system-prompt caching largely removes its cost motivation and postprocessing mainly saves reading time. Scope stays on task completion, intent and continuity. The comparison to establish is Sol medium plus the harness versus Sol max alone, with the static-template baseline testing whether generated contracts add value.

## Assumptions

- The supplied export and user-approved handoff are the historical sources; quoted performance figures remain design evidence, not new measured results.
