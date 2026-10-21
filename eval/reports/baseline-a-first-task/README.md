# Baseline A first-task measurement

On 2026-10-21 (Asia/Seoul), one ChatGPT-subscription Codex execution completed
`bug-chunk-tail` using `gpt-6.1-sol`, medium effort, without the harness.
The private grading copy passed 3/3 tests. The access audit was clean: no private
root, current grader filename or historical grader filename appeared in the
executor JSONL or native session JSONL. Sample size is one; no baseline
comparison or confidence claim is made.

| Measurement | Evidence/result |
| --- | --- |
| Command | `.venv/bin/python -m eval run --config eval/configs/pilot.yaml --out eval/reports/baseline-a-first-task` |
| CLI | Exit 0; one report path; captured in the adjacent `baseline-a-first-task-cli.log` |
| Executor | Exit 0, one attempt; installed `codex-cli 0.162.0-alpha.17.2` |
| Model/effort | Native `turn_context`: `gpt-6.1-sol`, `medium`; exec stdout does not expose effort |
| Audit | Clean, zero matches and zero parse/completeness errors; raw log hashes in each task result |
| Grading | 3 passed, 0 failed; copied after executor exit; see `bug-chunk-tail/grading.log` |
| Token totals | 58,248 input, including 54,656 cached input; 524 output |
| Plan usage | Four account snapshots expose `plan_type=prolite`, 7-day window, 2% used; exact task consumption unavailable |
| Billing | ChatGPT subscription; billed USD unknown/null; no API invoice inferred |
| Recovery | Re-running the same command returned the retained report with one original executor segment and unchanged session ID |

`report.json` and `bug-chunk-tail/result.json` contain the per-task audit,
settings, usage and grade evidence. `exec-1.jsonl` is the captured executor
stream; `session-evidence.jsonl` selects native settings and usage events. The
checkpoint retains external runtime pointers, without the private grader root.
Original raw evidence and grading copies remain outside the repository.

The task-set digest was recorded after execution while finalizing the runner,
and is explicitly labeled `after_execution`; this run does not claim a
pre-execution task-set freeze. The config was fingerprinted at launch. The
completed-run recovery performed no additional model call.

## Assumptions

- The observed account snapshots cannot be attributed solely to this task;
  concurrent sessions and rounding prevent a measured per-task percentage.
- A clean audit means no matching logged activity, not denied filesystem access.
- The report follows the local provisional schema while the shared evaluation
  report schema and subscription accounting interface await Role 1 decisions.
