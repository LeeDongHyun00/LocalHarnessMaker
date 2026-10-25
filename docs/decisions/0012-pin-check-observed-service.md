# 0012: Pin-check verification by observed service

Date: 2026-10-25

Status: accepted by the user on 2026-10-25 at 05:55 KST.

## Context

The user reports that installed `codex-cli 0.163.0-alpha.11.1` has no
`models` subcommand. Its stdio app-server answers `initialize` but never
`model/list`. Listing-only verification therefore disables Luna with
`model_list_unavailable`, preventing H3 even when the pinned model is served.

The supplied host report records a minimal pinned probe serving `gpt-6-luna`
at service tier `priority` in six seconds, with a native
`thread_settings_applied` identity record. The evidence is outside this
repository at `codex-bridge/report-copies/luna-pin-probe-2026-10-25.txt`;
the user identifies Role 2's `state/STATUS-plugin.md` history as its SHA-256
record. This offline publication does not independently verify that file or
assert a digest, thread ID or observation timestamp not supplied here.

## Decision

When no listing facility answers, pin-check may verify the pinned model using
observed service evidence recorded by the host operator from a minimal pinned
probe for the exact installed CLI version. A version without a recorded
observation stays disabled. An answering listing that lacks the pinned model
is not grounds for substituting probe evidence.

The operator records the observation as `luna_observation` in that version's
entry in `plugin/VERIFIED_VERSIONS.json` before enabling H3. On every CLI version
change, run a new minimal pinned probe and record its observation; do not carry
an older version's observation forward. Existing hook compatibility and pricing
verification remain required.

Pin-check adds the closed `model_evidence` object with required `source`
(`listing` or `probe_observation`), `observed_model`, nullable `service_tier`,
RFC 3339 `observed_at`, nullable `thread_id` and nullable `evidence_sha256`
(64 lowercase hex characters when present). Enabled results require this
object and retain empty `reason_codes`. Listing verification records
`source=listing`. No other pin-check schema constraint changes.

The controller's per-call identity check remains the enforcement: requested
model must equal observed model; otherwise record `pin_mismatch` and exit 2.
Recorded service availability does not permit identity substitution or replace
the per-call check. No automatic probe call is added to SessionStart.

## Consequence

The frozen interface set stays at version 3 with this explicitly approved
amendment to [0011](0011-pinned-luna-hook-direction.md). This is the authorized
exception to the normal version-increment rule; subsequent interface changes
still require a new decision, explicit approval and a version increment.
Historical schemas, CLIs and all other hook interfaces remain unchanged.

Roles 2 and 3 own registry/pin-check integration and controller enforcement;
Role 5 must retain valid pin and accounting evidence before presenting H3 as
successful. Publishing the schema and synthetic examples establishes no runtime
compatibility, live H3 result, or measured latency/cost target. Existing
`checks` and `model_list` enabled-result constraints are preserved by this
additive amendment; runtime integration must reconcile those legacy fields
without fabricating listing evidence or relaxing the schema silently.
