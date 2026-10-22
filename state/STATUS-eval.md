## Done

- Restricted fingerprint enumeration to immediate non-dot task graders, excluded symlink/dot/root-level/nested copies, deduplicated sources by SHA-256 and shared one invocation-scoped analysis across runner/re-audit tasks, retries and streams (.venv/bin/python -m pytest tests/eval -q: 463 passed in 34.19s).
- Bounded corpus and native-payload work: regressions require identical fingerprints with 120 task graders plus 5,000 dot-directory copies, one parse per unique content and under-five-second analysis; 200 KB code-mode and 1 MB FileChange cases, including malformed input and 3,000 calls, also pass under-five-second bounds (.venv/bin/python -m pytest tests/eval -q: 463 passed in 34.19s).
- Removed repeated decoder source copying, bounded slash-free path scanning and avoided repeated full-source literal extraction; retained the uncommitted code-mode fix and updated README/CHANGES (git diff --check -- eval tests/eval state/STATUS-eval.md: exit 0; git diff --exit-code -- eval/tasks eval/reports/pilot-a: exit 0).
- Restricted shell operand rules to decoded commands/directories; every literal code-mode exec command is audited, while dynamic commands/workdirs and unknown tools remain inconclusive (.venv/bin/python -m pytest tests/eval -q: 454 passed in 47.54s).
- Restricted FileChange/apply_patch inputs to target/move paths and skipped quoted fake tool calls inside patch content; 29 synthetic cases preserve the real line-23/25 shapes and cover unittest, protected reads/targets, concatenation, special-character content, symlinks and moves (.venv/bin/python -m pytest tests/eval -q: 454 passed in 47.54s).
- Updated eval/README.md and eval/CHANGES.md for the operand fix and supplied d73b41f host result; frozen tasks and pilot artifacts remain unchanged (git diff --check -- eval tests/eval state/STATUS-eval.md: exit 0; git diff --exit-code -- eval/tasks eval/reports/pilot-a: exit 0; git status --short: pilot-a remains untracked).
- Preserved the uncommitted native-record fix: world_state/token_usage_record validation and path checks, custom exec decoding, native event tool operands, complete persisted access-audit.json diagnostics and the synthetic 33-record native fixture (.venv/bin/python -m pytest tests/eval -q: 425 passed in 33.24s).
- Restricted fingerprints to command aggregated_output and function/custom tool outputs; executor-authored patches, changes, arguments and metadata are excluded while input path/operand checks remain (.venv/bin/python -m pytest tests/eval -q: 425 passed in 33.24s).
- Selected only hidden lines with distinctive literals absent from the entire public task corpus, excluding public normalized lines and boilerplate; decoded string/numeric equivalents are covered (.venv/bin/python -m pytest tests/eval -q: 425 passed in 33.24s).
- Added read-only eval.runner.reaudit for finished checkpoint runtimes with real per-task audit settings, retained log/grader manifest checks and sanitized per-task summaries; tests prove no subprocess invocation or artifact writes and preserve matches alongside errors (.venv/bin/python -m pytest tests/eval -q: 425 passed in 33.24s).
- Added synthetic honest unittest/pytest-output fixtures, all public-file categories, cross-task public literals, authored-input exclusions and hidden-line cat/sed/grep/Python output detection (.venv/bin/python -m pytest tests/eval -q: 425 passed in 33.24s).
- Updated eval/README.md and eval/CHANGES.md with host re-audit instructions and evidence; frozen public tasks are unchanged (git diff --check -- eval tests/eval state/STATUS-eval.md: exit 0; git diff --exit-code -- eval/tasks: exit 0).

## Remaining

- Claude accepts the combined corpus/cache/performance and shell/file-change operand fixes on the host by running .venv/bin/python -m eval.runner.reaudit --private-root "$LHM_PRIVATE_GRADERS" --out eval/reports/pilot-a/ with the matching private graders and retained external runtimes. Prior d73b41f acceptance reached 9/10 clean; the uncommitted code-mode fix passed 454 host tests but its re-audit hung over nine minutes. New target: under one minute with 10/10 clean unless actual protected access is detected; review each status/error kind/match label. This session cannot establish the host result.
- Claude then reruns pilot A on the host in a fresh output directory, retaining native/event streams, audits and costs. Re-audit never updates the old checkpoint/report; preserve the untracked eval/reports/pilot-a/. The user reports ten originally invalid/ungraded tasks and about one percentage point of weekly plan use.
- Inspect the rerun for any remaining unsupported/dynamic event forms or observed access before interpreting quality; manually re-check five valid A samples. No pilot quality result is established by these offline tests.
- Run pilot B on the host under the existing approval/budget workflow and compare identical selected-task hashes, seed, CLI and executor settings; obtain explicit approval before full measurement.
- Verify installed CLI executor/controller/verifier/resume compatibility, actual nested guard, retries, full capture, process termination and sandbox behavior on the host. Missing true before/after plan samples remain null.
- Preserve the prepared A/B configs and pinned Standard short-context price snapshot. The runner hashes selected public/private inputs; docs/eval-freeze.md records the full frozen population. Resolve any future shared provenance change with Role 1 before headline publication.
- Review structural helper extraction and submitted regression quality manually; behavioral graders do not certify those properties.
- Implement and host-verify two-session handoff execution/observations before including those tasks.
- Complete control-call accounting, the done-claim denominator and hash-pinned paired local-minus-cheap_api parity. Missing observations remain undefined; D-3 through D-5 remain pending.
- Run the full repository suite once before a future merge; this session ran only tests/eval and did not stage or commit.

## Decisions

- Enumerate only ROOT/<non-dot-task>/test_*.py and deduplicate contents before AST analysis: validation/mutation/reference copies are not grader fingerprint inputs, while whole-root path protection remains unchanged.
- Share immutable fingerprint/public-corpus analysis once per runner/re-audit invocation: all task and retry audits need the same corpus; a new invocation must refresh it, and per-task manifest hashing remains live.
- Match code-mode calls at source offsets and require a boundary before generic paths: repeated slicing and slash-free regex retries would otherwise scale quadratically on large native payloads.
- Apply shell expansion/quoting rules only to actual decoded shell commands and directories: JavaScript glue and authored file contents caused the two remaining false inconclusive errors.
- Check only target/move paths for FileChange and apply_patch: model-written content, including private-looking strings, is not access evidence; canonical path/symlink checks still apply.
- Keep dynamic and unknown code-mode calls inconclusive: static literal extraction must not certify unresolved execution as clean.
- Match fingerprints only against tool outputs: executor-authored content is not observed read evidence; path and operand checks still cover inputs.
- Compare hidden literals with every public task's prompt/day2/expected/meta/workspace files: shared specification examples and boilerplate cannot establish private access.
- Retain the 16-character minimum and fingerprints across all immediate non-dot task graders: distinctive hidden output can still reveal cross-task reads with concealed paths; quarantine/reference copies never contribute.
- Treat --out in the explicitly requested re-audit diagnostic as the existing source run: the command reads finished evidence and prints labels without creating a destination or changing frozen eval run semantics.
- Treat world_state and token_usage_record as non-tool metadata: their full contents can disclose private locations even though ordinary session settings are not shell commands; fingerprints do not apply.
- Inspect native custom input and nested event items: recognizing a record type alone did not establish operand coverage.
- Accept only statically decoded literal custom exec shell/patch calls: unsupported expressions and dynamic code cannot establish a clean audit.
- Persist a separate complete access-audit.json per task: all errors must remain reviewable even when a match takes precedence over inconclusive status.
- Keep shared schemas, the frozen eval run CLI and token accounting unchanged: the user explicitly requested the separate offline re-audit module.
- Preserve all pilot reports: the supplied host result is historical evidence, and Claude owns rerun/report-retention decisions.
- Preserve prior pricing and selected-task hashing decisions: the offline audit fix supplies no new measurement or authority to alter provenance semantics.

## Verify commands

- .venv/bin/python -m pytest tests/eval -q
- git diff --check -- eval tests/eval state/STATUS-eval.md
- git diff --exit-code -- eval/tasks eval/reports/pilot-a
- Host acceptance only: .venv/bin/python -m eval.runner.reaudit --private-root "$LHM_PRIVATE_GRADERS" --out eval/reports/pilot-a/
- Host only, with a fresh output directory selected by Claude: .venv/bin/python -m eval run --config eval/configs/pilot-a.yaml --out eval/reports/NEW-NAME/
- Host only, after approval: .venv/bin/python -m eval run --config eval/configs/pilot-b.yaml --out eval/reports/pilot-b/
- Before a future merge only: full repository test suite once.

## Do not touch

- Frozen eval/tasks/, existing reports including eval/reports/pilot-a/, docs/eval-freeze.md, controller/, verifier/, plugin/, shared schemas/configuration, other roles' tests/STATUS files and concurrent changes; never share task contents with Role 3.
- .git: no staging, commits, history rewrites or file deletion in this session.
- No executor, controller, judge, nested Codex, live API/model, network, macOS sandbox-exec or private-root lookup in this session.
- Never publish private locations, graders, references, mutants or equivalence rationales. Regression tests use synthetic roots under pytest temporary storage only.

## Assumptions

- Immediate task graders and public inputs remain immutable during one invocation. The cache is in-memory only and recreated for every run/re-audit; file manifests continue to use live hashes.
- The supplied host inventory (14,669 test files, 120 task graders, 847 unique contents), 454 passing tests and nine-minute hang are authoritative user evidence. The private root was unavailable and was not located or inspected; 463 passing offline tests do not establish under-one-minute host acceptance or 10/10 clean tasks.
- Claude's commit d73b41f and pilot A 9/10 clean result (previously all inconclusive) are user-supplied host evidence. Only the two authorized retained records were read to derive regression shapes; tests replace their task content and paths with synthetic values.
- Claude owns the matching-private-root host acceptance run. The 454 passing eval tests establish regression behavior, not 10/10 real-log cleanliness or a pilot quality result.
- The supplied retained host session is structural evidence for codex-cli 0.162.0-alpha.17.2; unseen formats remain fail-closed. The fixture preserves categorical discriminators while replacing all task/user content and numeric observations.
- The user's description of pilot A at d38a5da and its approximate weekly plan use is authoritative host evidence, not a measurement made here.
- Metadata usage validation is independent of accounting; accepting token_usage_record does not add or double-count tokens.
- Claude will rerun on the host and decide report retention; offline regression success does not establish pilot quality, observed host cleanliness or sandbox isolation.
- The user's supplied Claude verification (385 passed) and pilot A fingerprint false positive are host evidence; they were not reproduced with real graders in this session.
- Re-audit assumes the original external runtimes and matching private graders remain available; missing/changed evidence is inconclusive unless access is detected. --out denotes the existing finished run, as documented.
- Earlier supplied pricing/freeze evidence remains authoritative: snapshot openai-standard-short-2026-10-22-v1, Standard short context absent conflicting evidence, freeze commit 7cdaf3b and full-set digest b78913b04280f6696d419d2afdc96b152675973d82f05199ddef848986285d1f.
