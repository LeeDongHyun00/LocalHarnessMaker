# Probe run results

Raw results of the gpt-6.1-sol weakness probes described in docs/handoff/2026-10-26-sol-probe-baseline.md. Each batch folder holds, per run, `run.json` (every turn: the developer message, Sol's final message, commands, edited files, token usage, and the check result at run time) and `recheck.json` (the check re-run with the final checks; prefer it), plus `summary.json` for the batch.

| Folder | Where | Probes | Runs |
|---|---|---|---|
| mac-b1 | Mac, codex-cli 0.164.0-alpha.11.1, workspace-write | P01 to P14 | 42 |
| mac-b2 | Mac, same | P15 to P18 | 12 |
| mac-r3smoke | Mac, same | P19 to P22, one run each | 4 |
| c1, c2 | Claude cloud (added by the cloud session) | P01 to P18, P19 to P22 | 54, 12 |

Not here on purpose: the probe sources and hidden checks (kept outside the repository), the final workspaces and the Codex session records. Local paths are redacted: the home directory is written as `~` and temporary directories as `<tmp>`.
