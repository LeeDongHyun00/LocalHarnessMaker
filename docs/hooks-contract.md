# Installed Codex hook contract

Date: 2026-10-21 (Asia/Seoul). Pin: `codex-cli 0.162.0-alpha.17.2`.
Status: published by Role 1 on 2026-10-21 with user approval.
This installed-version evidence is the source of truth under AGENTS.md section 3.3.

Official reference: [Codex hooks](https://learn.chatgpt.com/docs/hooks), fetched on 2026-10-21.
All JSON samples below are captured runtime values, not fixtures.

## Observed behavior

| Check | Interactive CLI | codex exec |
|---|---|---|
| SessionStart fires | Yes, source=startup | Yes, source=startup |
| UserPromptSubmit fires | Yes | Yes |
| Both additionalContext values visible | Both markers in developer context and first assistant reply | Both markers in developer context and first assistant reply |
| Stop forces continuation | Yes, SECOND_REPLY | Yes, SECOND_REPLY |
| Second Stop lets the turn finish | Yes, empty JSON object | Yes, empty JSON object |
| Process exits normally | Exit 0 after /quit | Exit 0 |

Config uses `hooks.json` next to the isolated user `config.toml`. Each event has
an array of groups with a `hooks` array of command handlers. Context replies use
`hookSpecificOutput.hookEventName` and `hookSpecificOutput.additionalContext`.
The captured transcripts show this text arriving as developer messages.

The first Stop returns exactly:

```json
{"decision": "block", "reason": "test: print one more line"}
```

Codex continues within the same turn, delivers the reason inside a user
`<hook_prompt ...>` message, and calls Stop again with `stop_hook_active: true`.
The second response is `{}`, allowing completion. UserPromptSubmit fires once,
not again for this automatic Stop continuation. A production hook must therefore
preserve the current contract across Stop continuation. The probe has an
additional one-shot file guard to avoid an unbounded loop if the active flag
is missing. This guard is experiment machinery, not the production attempt limit.

## Evidence

| Mode | Captured files | Offline check |
|---|---|---|
| exec | [events](../plugin/evidence/2026-10-21-exec/events.jsonl), [stderr](../plugin/evidence/2026-10-21-exec/stderr.log), [transcript excerpt](../plugin/evidence/2026-10-21-exec/transcript-excerpt.jsonl), [result](../plugin/evidence/2026-10-21-exec/result.json) | context_visible=true, continued_once=true, exit_code=0 |
| interactive | [terminal recording](../plugin/evidence/2026-10-21-tui/terminal.log), [transcript excerpt](../plugin/evidence/2026-10-21-tui/transcript-excerpt.jsonl), [result](../plugin/evidence/2026-10-21-tui/result.json) | context_visible=true, continued_once=true, exit_code=0 |

Each directory contains the exact registered `hooks.json`, an experiment manifest,
and four captured input/output pairs under `hooks/`. `transcript-source.json`
records the source path, SHA-256, and excerpt selection. Excerpts preserve complete
selected JSONL records. Terminal recording includes ANSI control codes.

## Complete input and output samples

### exec

SessionStart — [1792557065790951000-SessionStart-e5b0ce22fc644b27b2d5803690a3ae7d.json](../plugin/evidence/2026-10-21-exec/hooks/1792557065790951000-SessionStart-e5b0ce22fc644b27b2d5803690a3ae7d.json)

```json
{
  "input": {
    "session_id": "01a15cba-0f64-7070-a1e4-f3a94a8fc456",
    "transcript_path": "/private/var/folders/1s/swm_fg0j7dv02dm24jfkw8vc0000gn/T/harness-hook-probe-spmnaxsq/codex-home/sessions/2026/10/21/rollout-2026-10-21T13-31-01-01a15cba-0f64-7070-a1e4-f3a94a8fc456.jsonl",
    "cwd": "/var/folders/1s/swm_fg0j7dv02dm24jfkw8vc0000gn/T/harness-hook-probe-spmnaxsq/workspace",
    "hook_event_name": "SessionStart",
    "model": "gpt-6.1-sol",
    "permission_mode": "bypassPermissions",
    "source": "startup"
  },
  "output": {
    "hookSpecificOutput": {
      "hookEventName": "SessionStart",
      "additionalContext": "When first replying, include this exact marker: HARNESS_SESSION_CONTEXT_4D91"
    }
  }
}
```

UserPromptSubmit — [1792557065873536000-UserPromptSubmit-ecf82de8c0504be8a4366db1cb1df0e5.json](../plugin/evidence/2026-10-21-exec/hooks/1792557065873536000-UserPromptSubmit-ecf82de8c0504be8a4366db1cb1df0e5.json)

```json
{
  "input": {
    "session_id": "01a15cba-0f64-7070-a1e4-f3a94a8fc456",
    "turn_id": "01a15cba-15c6-78d0-9c94-76ee8b4b4c10",
    "transcript_path": "/private/var/folders/1s/swm_fg0j7dv02dm24jfkw8vc0000gn/T/harness-hook-probe-spmnaxsq/codex-home/sessions/2026/10/21/rollout-2026-10-21T13-31-01-01a15cba-0f64-7070-a1e4-f3a94a8fc456.jsonl",
    "cwd": "/var/folders/1s/swm_fg0j7dv02dm24jfkw8vc0000gn/T/harness-hook-probe-spmnaxsq/workspace",
    "hook_event_name": "UserPromptSubmit",
    "model": "gpt-6.1-sol",
    "permission_mode": "bypassPermissions",
    "prompt": "This is a hook compatibility experiment. Reply with the two exact markers supplied in extra context, then FIRST_REPLY. Do not use tools or change files. If later asked to print one more line, reply only SECOND_REPLY."
  },
  "output": {
    "hookSpecificOutput": {
      "hookEventName": "UserPromptSubmit",
      "additionalContext": "When first replying, include this exact marker: HARNESS_CONTRACT_CONTEXT_8B62"
    }
  }
}
```

Stop — [1792557068108829000-Stop-6c10e7aa307d49feb48a7fef4b88839a.json](../plugin/evidence/2026-10-21-exec/hooks/1792557068108829000-Stop-6c10e7aa307d49feb48a7fef4b88839a.json)

```json
{
  "input": {
    "session_id": "01a15cba-0f64-7070-a1e4-f3a94a8fc456",
    "turn_id": "01a15cba-15c6-78d0-9c94-76ee8b4b4c10",
    "transcript_path": "/private/var/folders/1s/swm_fg0j7dv02dm24jfkw8vc0000gn/T/harness-hook-probe-spmnaxsq/codex-home/sessions/2026/10/21/rollout-2026-10-21T13-31-01-01a15cba-0f64-7070-a1e4-f3a94a8fc456.jsonl",
    "cwd": "/var/folders/1s/swm_fg0j7dv02dm24jfkw8vc0000gn/T/harness-hook-probe-spmnaxsq/workspace",
    "hook_event_name": "Stop",
    "model": "gpt-6.1-sol",
    "permission_mode": "bypassPermissions",
    "stop_hook_active": false,
    "last_assistant_message": "HARNESS_SESSION_CONTEXT_4D91\nHARNESS_CONTRACT_CONTEXT_8B62\nFIRST_REPLY"
  },
  "output": {
    "decision": "block",
    "reason": "test: print one more line"
  }
}
```

Stop — [1792557070565202000-Stop-8e2c69a4bf21400795949132d5f77952.json](../plugin/evidence/2026-10-21-exec/hooks/1792557070565202000-Stop-8e2c69a4bf21400795949132d5f77952.json)

```json
{
  "input": {
    "session_id": "01a15cba-0f64-7070-a1e4-f3a94a8fc456",
    "turn_id": "01a15cba-15c6-78d0-9c94-76ee8b4b4c10",
    "transcript_path": "/private/var/folders/1s/swm_fg0j7dv02dm24jfkw8vc0000gn/T/harness-hook-probe-spmnaxsq/codex-home/sessions/2026/10/21/rollout-2026-10-21T13-31-01-01a15cba-0f64-7070-a1e4-f3a94a8fc456.jsonl",
    "cwd": "/var/folders/1s/swm_fg0j7dv02dm24jfkw8vc0000gn/T/harness-hook-probe-spmnaxsq/workspace",
    "hook_event_name": "Stop",
    "model": "gpt-6.1-sol",
    "permission_mode": "bypassPermissions",
    "stop_hook_active": true,
    "last_assistant_message": "SECOND_REPLY"
  },
  "output": {}
}
```

### tui

SessionStart — [1792557098317985000-SessionStart-bd4655ed3a19441182da58750a626111.json](../plugin/evidence/2026-10-21-tui/hooks/1792557098317985000-SessionStart-bd4655ed3a19441182da58750a626111.json)

```json
{
  "input": {
    "session_id": "01a15cba-9509-7011-a03f-83227aad185e",
    "transcript_path": "/private/var/folders/1s/swm_fg0j7dv02dm24jfkw8vc0000gn/T/harness-hook-probe-g0kb1wng/codex-home/sessions/2026/10/21/rollout-2026-10-21T13-31-34-01a15cba-9509-7011-a03f-83227aad185e.jsonl",
    "cwd": "/var/folders/1s/swm_fg0j7dv02dm24jfkw8vc0000gn/T/harness-hook-probe-g0kb1wng/workspace",
    "hook_event_name": "SessionStart",
    "model": "gpt-6.1-sol",
    "permission_mode": "bypassPermissions",
    "source": "startup"
  },
  "output": {
    "hookSpecificOutput": {
      "hookEventName": "SessionStart",
      "additionalContext": "When first replying, include this exact marker: HARNESS_SESSION_CONTEXT_4D91"
    }
  }
}
```

UserPromptSubmit — [1792557098409845000-UserPromptSubmit-74a9b34413a54fe4858eb78a842f1c3c.json](../plugin/evidence/2026-10-21-tui/hooks/1792557098409845000-UserPromptSubmit-74a9b34413a54fe4858eb78a842f1c3c.json)

```json
{
  "input": {
    "session_id": "01a15cba-9509-7011-a03f-83227aad185e",
    "turn_id": "01a15cba-954e-78d2-ba65-34bf906b5f82",
    "transcript_path": "/private/var/folders/1s/swm_fg0j7dv02dm24jfkw8vc0000gn/T/harness-hook-probe-g0kb1wng/codex-home/sessions/2026/10/21/rollout-2026-10-21T13-31-34-01a15cba-9509-7011-a03f-83227aad185e.jsonl",
    "cwd": "/var/folders/1s/swm_fg0j7dv02dm24jfkw8vc0000gn/T/harness-hook-probe-g0kb1wng/workspace",
    "hook_event_name": "UserPromptSubmit",
    "model": "gpt-6.1-sol",
    "permission_mode": "bypassPermissions",
    "prompt": "This is a hook compatibility experiment. Reply with the two exact markers supplied in extra context, then FIRST_REPLY. Do not use tools or change files. If later asked to print one more line, reply only SECOND_REPLY."
  },
  "output": {
    "hookSpecificOutput": {
      "hookEventName": "UserPromptSubmit",
      "additionalContext": "When first replying, include this exact marker: HARNESS_CONTRACT_CONTEXT_8B62"
    }
  }
}
```

Stop — [1792557100750693000-Stop-67445e39d3b24901850101197f458c7b.json](../plugin/evidence/2026-10-21-tui/hooks/1792557100750693000-Stop-67445e39d3b24901850101197f458c7b.json)

```json
{
  "input": {
    "session_id": "01a15cba-9509-7011-a03f-83227aad185e",
    "turn_id": "01a15cba-954e-78d2-ba65-34bf906b5f82",
    "transcript_path": "/private/var/folders/1s/swm_fg0j7dv02dm24jfkw8vc0000gn/T/harness-hook-probe-g0kb1wng/codex-home/sessions/2026/10/21/rollout-2026-10-21T13-31-34-01a15cba-9509-7011-a03f-83227aad185e.jsonl",
    "cwd": "/var/folders/1s/swm_fg0j7dv02dm24jfkw8vc0000gn/T/harness-hook-probe-g0kb1wng/workspace",
    "hook_event_name": "Stop",
    "model": "gpt-6.1-sol",
    "permission_mode": "bypassPermissions",
    "stop_hook_active": false,
    "last_assistant_message": "HARNESS_SESSION_CONTEXT_4D91\nHARNESS_CONTRACT_CONTEXT_8B62\nFIRST_REPLY"
  },
  "output": {
    "decision": "block",
    "reason": "test: print one more line"
  }
}
```

Stop — [1792557102980157000-Stop-fa118d85555f494bb8f3cd7ce08d81fb.json](../plugin/evidence/2026-10-21-tui/hooks/1792557102980157000-Stop-fa118d85555f494bb8f3cd7ce08d81fb.json)

```json
{
  "input": {
    "session_id": "01a15cba-9509-7011-a03f-83227aad185e",
    "turn_id": "01a15cba-954e-78d2-ba65-34bf906b5f82",
    "transcript_path": "/private/var/folders/1s/swm_fg0j7dv02dm24jfkw8vc0000gn/T/harness-hook-probe-g0kb1wng/codex-home/sessions/2026/10/21/rollout-2026-10-21T13-31-34-01a15cba-9509-7011-a03f-83227aad185e.jsonl",
    "cwd": "/var/folders/1s/swm_fg0j7dv02dm24jfkw8vc0000gn/T/harness-hook-probe-g0kb1wng/workspace",
    "hook_event_name": "Stop",
    "model": "gpt-6.1-sol",
    "permission_mode": "bypassPermissions",
    "stop_hook_active": true,
    "last_assistant_message": "SECOND_REPLY"
  },
  "output": {}
}
```

## Limits and follow-up decisions

Only startup was exercised. Resume, fork, clear, compaction, handoff save/injection,
controller/verifier integration, contract approval, and the production attempt
limit remain unverified. Non-null transcript paths were observed; consumers
must still accept null as documented. The context marker is not a generated
contract, so this experiment does not establish SC-2 or D-2.

Both runs explicitly used `--dangerously-bypass-hook-trust` on newly authored,
reviewed probe commands. Persisted hook trust and plugin installation were not
tested. Normal installation must document the official trust review; it must
not silently use the bypass. The isolated configuration requested read-only
sandboxing and never approval, but payloads reported `bypassPermissions`.
No model tools or file changes were requested or observed. This experiment
makes no claim about the effective sandbox policy.

The interactive terminal had TERM=dumb, displayed a warning, and was continued
with y. The turn completed; /quit then exited the CLI normally. An unstable
skip_host_skill_discovery feature warning also appeared. These warnings are
retained in the evidence rather than treated as hook failures.

Probe stderr includes an elapsed_seconds line for every invocation; unit tests
check this and fail-open behavior. Codex did not expose these lines in its
captured exec stderr, so measured production-hook latency below one second is
not claimed. No controller call ran, so STOP-P3 latency is not evaluated.

## Assumptions

- First-task authorization includes two executor experiments, each with one bounded continuation, using the existing local login. No control API calls ran.
- A fresh temporary CODEX_HOME and workspace provide isolated hook registration without changing the user's regular configuration. Existing auth.json is linked only outside the repository; no credential content is copied into evidence.
- The default assigned executor is gpt-6.1-sol. The experiment selects low reasoning effort for a marker-only response; this is not the controller's effort selection logic.
- Role 1 published this document from plugin/hooks-contract.draft.md with user approval and adjusted evidence links for docs/. The source draft and captured evidence remain unchanged. Publication does not implement later schema or hook-interface proposals.
