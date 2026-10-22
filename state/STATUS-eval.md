## Done

- Replaced code-mode source allowlisting with lexical extraction of every direct tools call; synthetic Promise/allSettled, arrays, loops, display spreads and local helper glue pass, while nonliteral operands, unknown tools, aliases, eval/Function and unresolved callables stay inconclusive (.venv/bin/python -m pytest tests/eval -q: 487 passed).
- Covered the supplied nested-quoting rg wrapper and exec file_change list shape, including workspace/protected targets; canonical path checks and private-root redaction recognize /var and /private/var (.venv/bin/python -m pytest tests/eval -q: 487 passed).
- Added runner-recorded configuration and workspace content manifests immediately after executor exit, plus all-task eval.runner.regrade using retained logs, hash-checked workspaces and the existing fresh-copy grade() path; schema-valid synthetic regrades match current runner outcomes without executor calls or source/runtime writes (.venv/bin/python -m pytest tests/eval -q: 487 passed).
- Added refusal tests for missing/mismatched exit hashes and source/nested output destinations, all-task recovery from old inconclusive audits, fresh grading copies and CLI success/refusal output; retained every earlier detection regression (.venv/bin/python -m pytest tests/eval -q: 487 passed).
- Updated eval/README.md and eval/CHANGES.md with the regrade command, provenance, hash semantics and historical-run restrictions; frozen tasks and both pilot directories are unchanged (git diff --check -- eval tests/eval state/STATUS-eval.md: exit 0; git diff --exit-code -- eval/tasks eval/reports/pilot-a eval/reports/pilot-b: exit 0).

## Remaining

- Claude re-audits both retained host pilots with the matching private root: .venv/bin/python -m eval.runner.reaudit --private-root "$LHM_PRIVATE_GRADERS" --out eval/reports/pilot-a/ and the corresponding pilot-b directory. Review every error kind and access match before interpreting quality. This session cannot establish real-log cleanliness.
- Claude reruns pilot B once on the host in a fresh output directory with the new exit hashes. Historical runs lacking hashes cannot be regraded; never reconstruct hashes from current workspaces. Inspect the new full capture and hash evidence.
- On a hash-bearing finished run, use .venv/bin/python -m eval.runner.regrade --private-root "$LHM_PRIVATE_GRADERS" --from SOURCE --out NEWDIR as needed; review its complete report and run-diagnostics provenance. Keep SOURCE immutable.
- Manually re-check five valid pilot-A samples, then compare A/B selected-task hashes, seed, CLI, executor settings and costs; obtain explicit approval before full measurement.
- Host-verify executor/controller/verifier/resume compatibility, nested guards, retries, termination and production sandbox behavior. Missing true before/after plan observations remain null.
- Review structural helper extraction and submitted regression quality manually; behavioral graders do not certify those properties.
- Implement and host-verify two-session handoff execution before including those tasks; complete control accounting, the done-claim denominator and hash-pinned paired local-minus-cheap_api parity. D-3 through D-5 remain pending.
- Run the full repository suite once before a future merge. This session runs only tests/eval and does not stage or commit.

## Decisions

- Extract direct tools calls independently of JavaScript control flow: parallel Promise calls use literal operands even when the surrounding glue is complex.
- Preserve fail-closed indirect/unresolved callable handling and command-object spreads: static evidence cannot resolve a tool alias or an operand that may be overridden.
- Preserve the existing shlex wrapper decoding and list-form target extraction, with exact host-shape regressions: the observed shape must be proven without interpreting glue or authored content as shell.
- Canonicalize both path sides and redact macOS aliases: /var and /private/var identify the same temporary paths on the host.
- Hash every retained relative entry, type, mode, file content and symlink target at executor exit, including caches: regrading must reject any changed retained workspace and must not invent historical integrity.
- Save hash/config fields only in runner checkpoints and segment diagnostics: no shared report schema or frozen eval run interface changes are needed.
- Regrade the complete task set through grade() in fresh copies, with separate grading-output runtimes: no executor/controller/judge call or source run/runtime write is necessary.
- Preserve source executor/control calls, costs, metadata provenance and observations; regenerate audits, grades and quality metrics: offline regrading adds no executor measurement.
- Record source report SHA-256, audit implementation file hashes and all workspace checks in run-diagnostics.json: current uncommitted parser code must be identifiable independently of the source executor commit.

## Verify commands

- .venv/bin/python -m pytest tests/eval -q
- git diff --check -- eval tests/eval state/STATUS-eval.md
- git diff --exit-code -- eval/tasks eval/reports/pilot-a eval/reports/pilot-b
- Host only: .venv/bin/python -m eval.runner.reaudit --private-root "$LHM_PRIVATE_GRADERS" --out eval/reports/pilot-a/
- Host only: .venv/bin/python -m eval.runner.reaudit --private-root "$LHM_PRIVATE_GRADERS" --out eval/reports/pilot-b/
- Host only, hash-bearing source and fresh destination: .venv/bin/python -m eval.runner.regrade --private-root "$LHM_PRIVATE_GRADERS" --from SOURCE --out NEWDIR
- Before a future merge only: full repository suite once.

## Do not touch

- Frozen eval/tasks/, existing reports including eval/reports/pilot-a/ and pilot-b/, docs/eval-freeze.md, controller/, verifier/, plugin/, shared schemas/configuration and other roles' tests/STATUS files. Never share tasks with Role 3.
- .git: no staging, commits, history rewrites or file deletion in this session. Commit only eval/CHANGES.md, eval/README.md, eval/runner/audit.py, eval/runner/core.py, eval/runner/javascript.py, eval/runner/regrade.py, tests/eval/test_access_audit.py, tests/eval/test_runner.py and state/STATUS-eval.md.
- No executor, controller, judge, nested Codex, live model/API, network, macOS sandbox-exec or private-root lookup in this session.
- Never publish private graders/locations or reference/mutation rationales. Tests use synthetic graders under pytest temporary storage only.
- Never backfill exit hashes, write into a source regrade run, launch Codex in a grading copy or expose a grading copy to later executor turns.

## Assumptions

- The supplied host results at commit 96583d3 are authoritative user evidence: pilot A has 10/10 valid/clean, pass_rate 1.0 and cost_per_pass USD 0.029; pilot B has 9/10 invalid/inconclusive with unresolved_custom_input 11 and unresolved_operand 4. These are not measurements made in this session.
- Claude owns host re-audit and the new pilot-B run. Synthetic offline test success does not establish pilot-B cleanliness, host isolation or a new quality result.
- Retained checkpoints/reports are trusted runner output; exact exit hashes, matching task inputs and log/grader manifests are required for regrading. Runs without hashes remain diagnostic-only until a fresh host run.
- Immediate task graders and public inputs are immutable during one invocation; the existing invocation-scoped fingerprint cache remains unchanged.
- Earlier pinned pricing and task-freeze provenance remain authoritative: openai-standard-short-2026-10-22-v1, freeze commit 7cdaf3b and full-set digest b78913b04280f6696d419d2afdc96b152675973d82f05199ddef848986285d1f.
