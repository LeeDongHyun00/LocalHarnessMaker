## Done

- Replaced provisional report emission with the approved shared report schema, format validation, runtime ID/count/cost/order/hash checks, directory-only CLI stdout and an offline compatibility reference in eval/report.schema.json; historical provisional artifacts are preserved and cannot silently resume as version 1 (.venv/bin/python -m pytest tests/eval -q: 55 passed, 2 skipped; schema, runtime-invariant, legacy-checkpoint and CLI tests passed).
- Expanded observed tool-access auditing to ~/.codex, the sibling codex-bridge folder, repository paths outside the task workspace and private grader/grading roots; assistant prose is excluded, while denied/encoded/traversed/symlink accesses and incomplete/unsupported evidence invalidate tasks before grading (.venv/bin/python -m pytest tests/eval -q: 55 passed, 2 skipped; protected-access, native-tool, missing-capture and unfinished-event tests passed).
- Added hook-independent contract/verifier/re-instruction orchestration through frozen CLIs with injectable subprocesses, copied nested-guard environments, contract/verdict validation, same-session resume, null/exhausted feedback termination, retained evidence and failure recovery (.venv/bin/python -m pytest tests/eval -q: 55 passed, 2 skipped; mocked harness, failure, resume-access and completed-checkpoint tests passed).
- Added seeded task-cluster bootstrap metrics and per-segment executor accounting without fabricated zero prices; unknown costs/model identity stay null, and full done-claim/parity measurements remain explicitly undefined (.venv/bin/python -m pytest tests/eval -q: 55 passed, 2 skipped; deterministic bootstrap, zero-denominator, cached-token and unknown-cost tests passed).
- Prepared 119 new public drafts for a total of 100 single-session and 20 two-session tasks, with prompt.md, workspace, meta.json and expected.json, plus day2.md where applicable; listed every new task needing graders in eval/GRADERS-PENDING.md (.venv/bin/python eval/tools/prepare_tasks.py: Prepared 119 public candidates; no graders generated.; .venv/bin/python -m pytest tests/eval -q: inventory, Python syntax and pending-list checks passed).
- Wrote eval/README.md and eval/CHANGES.md describing changes, limitations and assumptions; this session made no executor/model/network/sandbox-exec calls and did not stage or commit (.venv/bin/python -m pytest tests/eval -q: all model/control subprocesses mocked; git diff --check -- eval tests/eval state/STATUS-eval.md: exit 0).
- Preserved the prior session's one-task baseline artifacts as historical provisional evidence, without rerunning or claiming current-schema validity (eval/reports/baseline-a-first-task/report.json: retained unchanged; no current live result claimed).

## Remaining

- Pending host verification: installed CLI contract/verifier/executor/resume compatibility, actual nested guard and production retry behavior, model/effort evidence, process termination and macOS sandbox-exec. Nested Codex, live models, network and sandbox-exec were unavailable and were not attempted in this workspace-write session.
- Obtain verified versioned model rates for eval/prices.yaml; its empty rates are explicitly an unpriced offline placeholder. Integrate actual per-call controller/judge/fallback transport/model/usage evidence exposed by the frozen CLIs; control costs and control_model remain null rather than inferred.
- Complete full done-claim denominator extraction and hash-pinned paired local-minus-cheap_api parity. Current emitted false_done_rate/parity are undefined with reasons; mock metrics are not measured quality evidence.
- Review the 119 draft candidates named in eval/GRADERS-PENDING.md, diversify related families, and write/validate external graders in a separately authorized session. No hidden task graders were written here. Revalidate the existing bug-chunk-tail external grader on the host; its two fixture tests skipped because LHM_PRIVATE_GRADERS was unset.
- Implement two-session runner handoff generation, injection and day-2 observation before executing those candidates. Current runner rejects two-session tasks before model calls; public day-2 prompts do not constitute orchestration evidence.
- Decide whether historical provisional baseline artifacts need explicit offline migration; otherwise use fresh output directories. No historical report was relabeled or rerun.
- Prepare the 10-task A/B pilot estimate and required approval before any 10-or-more paid-call batch or full run. Do not infer full-run authorization from this offline session.
- Freeze only after grader/specification/diversity review, then supply the task-set hash to Role 1 for docs/eval-freeze.md; re-check five A samples manually. SC-2, SC-5 and SC-6 remain unfinished.
- Run the full suite once before a future merge, then continue D-3 through D-5: static-template/harness measurements, local comparison, human review, task-type breakdowns and final report. No merge or headline cost/quality comparison occurred here.

## Decisions

- Use the approved shared report schema directly: the prior provisional status was superseded by version-1 approval and this user's first priority.
- Retire the local schema with a reference-only shim: no file deletion or shared-interface change is required.
- Preserve historical provisional reports and reject silent checkpoint migration: old evidence must not acquire unobserved pricing, provenance or audit guarantees.
- Audit supported tool access rather than assistant prose: the approved STOP-E4 requires observed operations, including denied attempts, and treats uncertainty as invalid.
- Keep raw logs externally and hash-pin both executor/native evidence: public redaction must not replace the original audit trail.
- Treat benchmark prompt execution as runner authorization to apply the generated contract: no interactive approval is possible in an automated evaluation; this does not change direct-user plugin behavior.
- Keep private grading outside the contract/verifier loop: neither private test contents nor private feedback reaches later executor turns.
- Keep absent rates/accounting and full claim denominators undefined: the frozen CLI output is insufficient to assert actual mixed-model/fallback accounting or false-done measurements.
- Mark new tasks as unfrozen drafts with graders pending: 120 public directories do not establish 120 reviewed, independently graded benchmark tasks.

## Verify commands

- .venv/bin/python -m pytest tests/eval -q
- git diff --check -- eval tests/eval state/STATUS-eval.md
- Read eval/GRADERS-PENDING.md for all 119 pending external graders.
- Host only, after prerequisites/authorization: verify live CLI, model/effort evidence, nested guard, process cleanup, external graders and sandbox behavior; do not run these in this session.
- Before a future merge only: run the full repository test suite once.

## Do not touch

- controller/, controller/case_library/, verifier/, plugin/, shared schemas/configuration, other roles' tests or STATUS files; never share the task set with Role 3.
- Existing concurrent edits and historical baseline artifacts; interface changes require Role 1 approval/versioning.
- Private grader storage or task graders in this session; no private contents/paths may enter executor/controller context or public artifacts.
- .git is read-only: do not stage, commit, rewrite history or delete files. Future commits must list only eval/, tests/eval/ and state/STATUS-eval.md paths explicitly.
- No executor models, nested codex exec, live model/API calls, network or macOS sandbox-exec in this environment. No full-run approval is implied.

## Assumptions

- The user's current priority order replaces the old STATUS ordering and provisional-schema claim; shared version 1 remains unchanged.
- A reference-only local schema counts as retirement while avoiding deletion under STOP-4.
- Public task preparation may include related family variants as drafts; diversity and grader review are required before freeze or measurement.
- expected_test_count=3 on new drafts is a planned grader-group count, not evidence that any grader exists or has run.
- The non-interactive benchmark runner may inject its generated contract as an authorized evaluation input; direct-user plugin approvals remain outside this session.
- Unobserved controller/judge accounting and actual fallback identity cannot be inferred from aggregate cost estimates or requested backend settings.
- Complete native/executor tool-event capture is required for a clean observed-access audit; clean logs do not establish isolation or visibility into unlogged activity.
- External grader configuration is absent in this test environment; the two skipped legacy fixture checks require trusted host verification.
