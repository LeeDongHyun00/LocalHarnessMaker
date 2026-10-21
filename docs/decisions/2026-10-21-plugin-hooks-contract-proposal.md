# Proposal: publish the measured hook contract

Date: 2026-10-21 (Asia/Seoul). Author: Role 2 Plugin Engineer.
Status: pending Role 1 review; STOP-2 reached.

AGENTS.md section 2 says: "If you need a change outside your paths, write a
proposal file in docs/decisions/ and stop." The role prompt assigns the hook
contract evidence to Role 2 and says Role 1 merges that file. Role 2 has prepared
the complete document within its owned paths and stops before publishing into
the lead-owned docs/ tree.

Requested action: review [the draft](../../plugin/hooks-contract.draft.md), then
publish it as docs/hooks-contract.md and adjust the evidence links to point into
plugin/evidence/. Its creation changes the repository's source of truth from
the official docs to the measured installed-version contract, so a placeholder
was not created. No schema, CLI, or hook input/output revision is requested.

The installed version is pinned at codex-cli 0.162.0-alpha.17.2. Both the
interactive CLI and codex exec fired SessionStart, UserPromptSubmit, and two
Stop calls. Both additionalContext markers appeared as developer messages and
in the assistant reply. Returning decision=block with reason="test: print one
more line" triggered SECOND_REPLY. The next Stop received stop_hook_active=true
and returned {}, allowing normal completion. There was no second
UserPromptSubmit for automatic continuation.

Verification: `.venv/bin/python -m pytest tests/plugin -q` returned 10 passed in
0.42s. `.venv/bin/python -m plugin.check_probe_evidence
plugin/evidence/2026-10-21-exec plugin/evidence/2026-10-21-tui` reported
context_visible=true, continued_once=true, two assistant messages, and exit 0
for both runs. Full captured payloads, launch manifests, stdout/stderr or terminal
recordings, transcript excerpts, and source hashes are retained in those paths.

This verifies the First task's compatibility experiment. D-1 awaits canonical
publication; D-2 through D-5 and production SC-1 through SC-6 remain pending.
See [the plugin STATUS file](../../state/STATUS-plugin.md) for the ordered work.

## Assumptions

- The explicit First task authorizes isolated compatibility runs using the existing login; normal user configuration and external service configuration were not changed.
- Canonical publication belongs to Role 1, consistent with shared ownership rules and the instruction that Role 1 merges the hook contract.
- Startup experiments do not prove handoff, approval, production retry limits, persisted trust, control-call latency, or nullable transcript handling.
