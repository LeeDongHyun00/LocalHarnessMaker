# Evaluation runner

The initial runner supports standalone baselines without plugin hooks. The
single-task config is valid YAML written in its JSON subset so the runner needs
no new root dependency. Harness baselines and the shared report interface are
not implemented; `report.schema.json` validates a provisional baseline artifact
only. No schema under `schemas/` is changed.

Set `LHM_PRIVATE_GRADERS` in the trusted parent shell to an external storage root
that is separate from this repository. Do not put its value in repository files.
Each task has an external subdirectory named by its public task ID, containing
regular `test_*.py` grader files. Optional external `audit-names.json` contains
`historical_names`, an array of previous grader basenames. This preserves audit
coverage when relocating or renaming a grader. The initial grader has already
been moved and its historical basename retained externally.

```sh
.venv/bin/python -m pytest tests/eval -q
.venv/bin/python -m eval run --config eval/configs/pilot.yaml --out eval/reports/baseline-a-first-task
```

The CLI prints one report path and writes diagnostics to stderr. Exit codes are
0 for a written report (including recorded invalid tasks), 1 for input errors,
and 2 for internal errors. Reusing the same config/output directory recovers its
checkpoint. Completed tasks do not invoke Codex again. Interrupted executor turns
resume their explicit session ID; interrupted grading repeats grading without
resuming an executor. Config/task fingerprint mismatches reject recovery.

The trusted parent supplies grader storage; that setting and all other inherited
private-location values are absent from the executor environment. Each task uses
a fresh temporary workspace and Codex home with an external auth symlink to the
existing ChatGPT login. Hooks and plugins are disabled for standalone baselines.
No API key is forwarded and no global Codex configuration is edited. The exact
command includes `--sandbox workspace-write`, never-approval policy,
`model_reasoning_effort`, and `--json`; retained session evidence confirms the
applied model and effort instead of inferring them from requested flags.

All executor JSONL streams, including resumed segments, are scanned for private
root spellings and current/historical grader basenames, across raw JSON, decoded
strings and URL encodings. Matches invalidate a run. Empty, malformed or
incomplete event evidence is inconclusive and invalidates the result. Full raw
logs stay in external runtime storage; repository review copies redact private
markers. Results retain original log hashes, line numbers and redacted evidence.

Only after the executor exits and the audit/settings checks pass are private
graders copied into a fresh grading copy. The loader selects only the private
grader files, so executor-authored public tests cannot inflate the grader count.
A grading copy is never used for an executor continuation. Raw runtime and
grading evidence are retained for review rather than deleted.

The user approved observed-access auditing instead of access denial. This method
does not establish filesystem isolation or capture unlogged activity. Earlier
grader contents remain in Git history; no history rewrite was requested.
Historical filenames are included in the audit. Standard unittest grading also
assumes cooperative task code; it is not an adversarial code-execution sandbox.

Per-task usage contains observed token totals and native session rate-limit
snapshots when exposed. These snapshots describe shared account usage and can
be rounded or affected by concurrent sessions. Exact task subscription
consumption and billed dollars remain null; tokens are not converted into an
API invoice. API-equivalent cost metrics require a separately agreed basis.

The installed CLI and
[official configuration reference](https://developers.openai.com/codex/config-reference/)
establish `model_reasoning_effort`. The
[official non-interactive documentation](https://developers.openai.com/codex/noninteractive/)
describes JSONL executor events and usage. On the installed version, applied
effort and account snapshots come from native session JSONL, not exec stdout.

## Assumptions

- The user's access-audit decision authorizes relocating the original grader and
  running one subscription-backed executor call, superseding the previous
  deny-read prerequisite.
- A single-task pilot validates runner mechanics; it cannot establish the
  project's A/B quality or cost hypothesis.
- The shared evaluation-report proposal remains unapproved. This local artifact
  is provisional and does not implement that proposed interface.
