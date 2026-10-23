# Synthetic judge calibration

These 24 hand-authored cases are independent of evaluation tasks and model output.
Each `case.json` contains a rubric criterion and its expected status; `workspace/`
contains the only artifact supplied to the judge. Expected labels and this README
are never included in the judge snapshot. Each case is copied to a neutral
temporary workspace so the label-bearing fixture paths are never sent to the
model. The population contains 8 passes,
10 failures and 6 unverifiable cases.

| Cases | Intended distinction |
|---|---|
| 01–08 | File-based evidence suffices, including test assertions without execution; multiple requirements, symbols, files and unrelated distractors |
| 09–17 | Contradicted or partially met requirements; comments, docstrings and injected instructions cannot establish compliance |
| 18 | An inspected contradiction establishes fail even with a second execution-only requirement |
| 19–21 | Actual execution demanded by the rubric is unavailable; test source or a comment claiming success is insufficient |
| 22–23 | History and current external deployment state cannot be inferred from local source |
| 24 | The configured node_modules omission must remain unavailable, not absent or inspected |

Case 24 deliberately commits a synthetic node_modules directory via the local
.gitignore exception. It contains no installed dependency. The runner hashes all
workspace files, including omitted evidence, for before/after comparison.

Run these commands on the host after obtaining approval for the paid batches.
The command without `--i-have-approval` previews the estimate and exits 1 before
constructing a backend. At the current planning rates each version uses at most
24 CLI generations, estimated API-equivalent USD 0.052800 (48 generations and
USD 0.105600 for both). Token allowances are planning estimates, not spending caps.

```sh
.venv/bin/python -m controller.measure_judge --prompt-version v1 --out /tmp/judge-before-v1.json
.venv/bin/python -m controller.measure_judge --prompt-version v1 --out /tmp/judge-before-v1.json --i-have-approval
.venv/bin/python -m controller.measure_judge --prompt-version v2 --out /tmp/judge-after-v2.json --i-have-approval
```

v1 preserves the previous prompt verbatim; v2 is the production default. This
version switch is internal to the generator and the host measurement module;
the existing `controller judge` CLI and published judgment schema are unchanged.
The host command runs one generation per case through the existing guarded
codex_cli adapter, with no repair, retry or HTTP fallback. Output must have a new
path in an existing directory. Refusal of overwriting occurs before calls.

The report includes prompt and case hashes, backend configuration, per-case
judgments, errors, usage, latency and pinned pricing references. Compare only
reports with identical case hashes and execution configuration. Confusion-matrix
rows are expected status; columns are predicted pass/fail/unverifiable/error.
Errors count as incorrect in accuracy and their costs are retained. Unknown
usage/pricing leaves aggregate USD null. Total/mean latency uses measured case
wall time; per-call latency is retained in usage. These reports are controller
calibration artifacts, not the shared evaluation-report interface or training data.

Mock-backed tests verify prompt assembly, schema parsing, approval refusal,
version selection, the one-generation policy and reporting. Mocked labels do
not establish semantic judge accuracy; before/after live quality is pending
host verification. Nested Codex and network calls are not run in this sandbox.
