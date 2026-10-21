## Done

- Built the initial unfrozen bug-fix fixture and validated that its three private cases reject the original implementation and pass a correction; the private source has now been relocated outside the repository under the user's access-audit decision (.venv/bin/python -m pytest tests/eval -q: 26 passed in 1.54s, including both fixture checks; eval/reports/baseline-a-first-task/tests.log).
- Implemented the hook-independent standalone baseline CLI, JSON-subset YAML config, provisional local report schema, pass_rate, timeout cleanup, transport retry and durable interruption/completed-run recovery (.venv/bin/python -m pytest tests/eval -q: 26 passed, including timeout, retry, same-session continuation, completed-checkpoint reuse and grading-crash recovery).
- Implemented per-task observed-access auditing across executor segments and native JSONL, with invalidation on current/historical grader filenames, private root matches or incomplete/malformed evidence; filtered the executor environment and preserved external originals plus redacted repository evidence (.venv/bin/python -m pytest tests/eval -q: 26 passed, including escaped/URL paths, basenames, historical names, invalidation and environment filtering).
- Ran exactly one subscription-backed baseline A executor on bug-chunk-tail; the CLI wrote the report, the executor exited successfully, the access audit was clean with zero matches/errors, and a fresh grading copy created after exit passed 3/3 private tests (.venv/bin/python -m eval run --config eval/configs/pilot.yaml --out eval/reports/baseline-a-first-task: exit 0, one report path; report.json and bug-chunk-tail/grading.log).
- Confirmed actual gpt-6.1-sol at medium effort from native session JSONL; the exec stdout JSONL does not expose effort (bug-chunk-tail/session-evidence.jsonl: turn_context model=gpt-6.1-sol, effort=medium; report.json settings_evidence.verified=true).
- Recorded per-task observed tokens and exposed ChatGPT account plan snapshots without inventing API billing or exact subscription consumption (bug-chunk-tail/exec-1.jsonl: turn.completed usage input_tokens=58248, cached_input_tokens=54656, output_tokens=524; session-evidence.jsonl: four prolite snapshots, 10080-minute primary window, used_percent=2.0; billed_usd and exact_task_consumption are null).
- Verified completed-run recovery without another model call and validated the provisional report and repository privacy check (.venv/bin/python -m eval run --config eval/configs/pilot.yaml --out eval/reports/baseline-a-first-task: exit 0, retained one executor segment; trusted-parent .venv/bin/python - schema/privacy audit: local report schema valid, private-location occurrences=0).
- Wrote the change summary, runner instructions, limitations and assumptions; retained the earlier preflight as historical evidence superseded by the user's audit choice (eval/README.md and eval/reports/baseline-a-first-task/README.md: present; git diff --check -- eval tests/eval state/STATUS-eval.md: exit 0).

## Remaining

- D-1: complete harness-mode contract/verifier/reinstruction orchestration and broader failure isolation using the frozen role CLIs; the present runner intentionally accepts standalone baseline configurations only.
- Coordinate the shared evaluation report schema with Role 1, including the user's subscription accounting choice. The current eval/report.schema.json is a provisional baseline artifact, not the proposed schemas/evaluation-report.schema.json. Do not change shared interfaces independently.
- D-2: expand the unfrozen task set to 100 single-session tasks plus 20 two-session tasks. Move private graders directly into external storage, retain historical filename audit aliases when needed, and record task-set hashes before future execution. The first-run digest is explicitly labeled after_execution.
- Prepare the 10-task baseline A/B pilot, report expected subscription usage or clearly labeled accounting assumptions, and obtain full-run approval. Respect STOP-3 before a batch of 10 or more paid calls; this session used one executor call only.
- Freeze the approved task set and provide its hash to Role 1 for docs/eval-freeze.md; manually re-check five baseline A samples. No freeze, five-sample human review or full-run approval is claimed.
- Continue D-3 through D-5 after the pilot: static-template and harness runs, cheap_api/local comparisons as approved, two-session handoff results, human review table, and final task-type metrics with confidence intervals. No A/B quality or cost conclusion follows from one task.

## Decisions

- Use the user-approved access-audit method: it supersedes the earlier STOP-E4 deny-read prerequisite and authorizes relocating the original grader before one baseline A call.
- Keep private grader locations only in trusted-parent memory/environment: actual locations are absent from repository artifacts and stripped from the environment passed to codex exec.
- Copy graders only after executor exit, into a fresh separate grading copy: no executor continuation is permitted once grading has begun; grading recovery never invokes Codex again.
- Audit all observed executor segments and native session JSONL, including historical grader basenames: matches invalidate the run and retain evidence, while absence of matches does not prove isolation.
- Use a fresh temporary Codex home and existing external ChatGPT auth symlink, with hooks/plugins disabled and HARNESS_NESTED=1: Role 2 confirmed hooks fire under exec, and baseline A must remain independent of the harness.
- Keep tokens and account rate-limit snapshots separate from billing: ChatGPT subscription snapshots are shared and rounded, so exact task consumption and billed USD remain unknown/null.
- Keep the local result schema provisional: the shared evaluation report proposal is not approved and its API-equivalent accounting does not yet represent the user's subscription requirement.
- Record the first task-set digest after execution and label its timing: runner finalization occurred after the live call; it is not evidence of a pre-run freeze.
- Retain external raw logs and grading copies: no history rewrite or cleanup deletion was requested; historical grader contents remain in Git history and their former filename is audited.

## Verify commands

- With LHM_PRIVATE_GRADERS set only in the trusted parent shell: .venv/bin/python -m pytest tests/eval -q
- With the same trusted-parent setup: .venv/bin/python -m eval run --config eval/configs/pilot.yaml --out eval/reports/baseline-a-first-task
- codex --version
- codex login status
- Read eval/reports/baseline-a-first-task/report.json, bug-chunk-tail/result.json, exec-1.jsonl, session-evidence.jsonl and grading.log.
- Validate report.json against eval/report.schema.json with jsonschema.Draft202012Validator; verify private root spellings are absent from tracked/untracked nonignored repository files.
- git diff --check -- eval tests/eval state/STATUS-eval.md

## Do not touch

- controller/, controller/case_library/, verifier/, plugin/, other role tests and other role STATUS files; never share task-set contents with Role 3.
- Shared schemas, CLIs and hook interfaces; only Role 1 may change them through the required decision/version process.
- Existing user edits, legacy harness/, experiments/ and root configuration.
- Never write the private grader root into repository files, executor prompts, configs, argv or forwarded environment; never copy grading files into an executor workspace.
- Never use git add -A. Any future commit must stage only explicit eval/, tests/eval/ and state/STATUS-eval.md paths, and must exclude other roles' staged changes.
- Do not delete unrelated files, rewrite Git history or change external service configuration. Relocating the original grader was explicitly authorized; no broader deletion permission was inferred.

## Assumptions

- The user approved access auditing instead of proving read denial and requested one subscription-backed baseline A task; no future full experiment was authorized.
- Relocating the original grader includes removing its public working-tree copy. Its prior Git history is preserved; observed references to its old basename are included in the audit.
- Native Codex JSONL turn_context and token_count records are valid runtime evidence when exec stdout omits applied effort or plan snapshots; both sources are identified explicitly in the result.
- Four account snapshots at 2% usage do not establish zero task cost or exact task percentage consumption; the first snapshot can follow model usage and other sessions share the account.
- Standard-library unittest grading assumes cooperative task code and observed-access audit coverage. Neither establishes an adversarial sandbox or visibility into unlogged activity.
- The config uses the JSON subset of YAML to avoid modifying Role 1's dependency configuration. Full YAML syntax and harness configurations remain unsupported.
- One passing task validates the first-task mechanics only; confidence intervals, parity, full task-set quality and cost-per-pass comparisons remain unfinished.
