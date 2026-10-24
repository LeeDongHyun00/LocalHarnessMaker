# Version 3 task design — 2026-10-25

Construction checkpoint: nine `bug_fix` candidates are authored and remain
unfrozen; the other 45 tasks are pending. See [validation](VALIDATION.md) and
[structure comparison](STRUCTURE-REVIEW.md). The 54-task design below is retained.
The user approved interface v3 on 2026-10-25 and separately authorized candidate
authoring; task freeze still requires host validation. The user-approved
[v3 direction](../../docs/handoff/2026-10-25-v3-direction.md), especially sections
3 and 5, supersedes the old Role 5 A/B/contract-harness plan for this work.
The [host findings](../../docs/weekly/2026-10-21-host-verification.md) dated
2026-10-24 and 2026-10-25 are historical evidence, not v3 measurements.

## Population and comparisons

Plan 54 independent tasks: nine of each shape below, in 18 domains with exactly
three tasks per domain. There are 45 single-session tasks and nine two-session
tasks, hence 63 required executor sessions per configuration. Domain labels are
strata, not template families. A is gpt-6.1-sol medium alone; H3 is the same
executor plus the actual plugin hooks and pinned gpt-6-luna low. B is dropped;
C is optional and requires separately authored user templates, a paired subset
and a separate estimate. It is outside these full-run templates.

| Shape | Tasks | Sessions | Main observation |
| --- | ---: | ---: | --- |
| bug_fix | 9 | 9 | Diagnose an interacting edge case in existing behavior |
| feature_plus_test | 9 | 9 | Add behavior and a meaningful regression test |
| constrained_refactoring | 9 | 9 | Change an internal mechanism while preserving explicit invariants |
| multiple_requirements | 9 | 9 | Finish heterogeneous, interacting deliverables |
| two_session | 9 | 18 | Preserve day-1 decisions when extending work on day 2 |
| ambiguous_requirement | 9 | 9 | Ask about one deliberately missing policy choice |
| Total | 54 | 63 | 45 single-session tasks |

Each row below is an authoring brief, not an executable task or a public prompt.
IDs are provisional inventory labels, not a task selection for the runner.
Each task gets an independently written starter, prompt, reference, requirement
map and grader. No generated common package, fixed module count, R1–R16 list,
facade trio, common error namespace or domain-substitution recipe. Do not port
v1/v2 inputs, solutions or reservations expectations. Shared harness utilities
and test frameworks are allowed; shared task implementations/oracles are not.
An independent reviewer compares architecture, data flow and failure mechanisms
across all 54 rows before authoring acceptance. If two rows reduce to the same
task with renamed entities, redesign one before calibration.

## Task inventory

The structures and evidence below define distinct authoring targets. Concrete
fixtures and oracle values belong to the task inputs or trusted storage and are
kept out of this inventory.

### bug_fix

| ID | Domain | Own structure and required behavior | Hidden evidence focus |
| --- | --- | --- | --- |
| v3-framed-stream | text_protocol | Incremental byte decoder with a cursor and callback; fix a delimiter split across feeds without consuming the next frame | Partitioned feeds, recovery after malformed input, callback sequence |
| v3-savepoint-unwind | storage | SQLite unit-of-work context managers; fix inner rollback corrupting outer transaction ownership | Nested exception traces, persisted rows, connection reuse |
| v3-cancelled-deadline | scheduling | Heap-backed timer service with cancellation handles; fix a cancelled head hiding an equally due timer | Fake-clock trace, tie order, repeated cancellation |
| v3-wide-column | rendering | Terminal table layout with measured glyph widths and wrapping; fix combining characters shifting the final column | Display-width invariants and explicit line-break rules |
| v3-quoted-record | data_exchange | Stateful CSV reader retaining source positions; fix quoted newline/CRLF interaction and error offsets | Independently generated records, offsets and recovery boundaries |
| v3-cycle-witness | graph | Iterative DFS producing a cycle witness; fix disconnected traversal returning an edge that is not in the cycle | Witness validity, isolated nodes, stable traversal order |
| v3-origin-shadow | configuration | Layered settings resolver returning value plus provenance; fix explicit empty values falling through to defaults | Value/provenance pairs, environment parsing, source immutability |
| v3-incremental-fanout | build_tooling | Timestamp/digest incremental build planner; fix removed dependencies leaving a stale transitive target | Rebuild sets over edits/removals, untouched output hashes |
| v3-histogram-merge | observability | Mergeable bucket counters with a separate overflow bin; fix boundary samples being counted twice on merge | Conservation of counts, associativity, original counter preservation |

### feature_plus_test

| ID | Domain | Own structure and required behavior | Hidden evidence focus |
| --- | --- | --- | --- |
| v3-undo-group | editor | Command stack with redo branches; add atomic undo groups and public regression tests | Partial failure unwinds, nested grouping, redo invalidation |
| v3-link-preview | filesystem | Directory walker yielding typed entries; add a dry-run symbolic-link plan and tests | Relative targets, cycles, no filesystem writes during preview |
| v3-scope-explanation | access_control | Rule evaluator over a role DAG; add explain output tracing allow/deny precedence | Result/explanation consistency, inherited rules, counterexample test |
| v3-workflow-checkpoint | workflow | Generator-driven job with serializable checkpoints; add resume from a checkpoint and tests | No repeated side effects, checkpoint validation, failure boundary |
| v3-pool-lease | resource_pooling | Context-managed bounded pool; add expiring lease renewal and tests | Fake time, double release, fairness and cleanup |
| v3-event-watermark | event_processing | Window accumulator with late-data channel; add watermark advancement and tests | Exact close boundary, out-of-order arrival, no lost late events |
| v3-plural-catalog | localization | Message catalog compiler; add plural-form validation and tests with diagnostic spans | Missing forms, literal escapes, original source locations |
| v3-index-cursor | search | Sorted postings index; add opaque pagination cursors and tests | Stable continuation, changed query rejection, duplicate-score ties |
| v3-cache-negative | caching | Memoizer wrapping a fallible loader; add separately timed negative entries and tests | Exception classification, TTL distinction, concurrent loader calls |

### constrained_refactoring

| ID | Domain | Own structure and explicit constraint | Hidden evidence focus |
| --- | --- | --- | --- |
| v3-token-scanner | text_protocol | Replace chained string slicing with a token iterator while preserving token spans and public API | Differential token traces, bounded scans, protected API snapshot |
| v3-journal-codec | storage | Separate a binary journal codec from file I/O without changing wire bytes or replay behavior | Byte fixtures, truncated tail handling, injected I/O failures |
| v3-ready-queue | scheduling | Replace repeated full sorting with an indexed ready queue; preserve priorities and cancellation semantics | Operation-count bound and observable dispatch order |
| v3-html-events | rendering | Convert recursive HTML emission to an explicit event stack; preserve escaping and output bytes | Deep nesting without recursion, byte equality, no input mutation |
| v3-fixedwidth-plan | data_exchange | Compile fixed-width field descriptors once rather than per row; preserve validation order and diagnostics | Instrumented compilation count, invalid descriptors, alignment |
| v3-path-reconstruction | graph | Replace copied path prefixes with predecessor links in a route search; preserve chosen path/ties | Public API, allocation bound, unreachable endpoints |
| v3-config-dispatch | configuration | Replace condition-heavy directive parsing with registered handlers; retain unknown-directive diagnostics | Extension registration, source order, protected entry points |
| v3-build-manifest | build_tooling | Split manifest discovery from subprocess command construction using an injected launcher | Exact argv, no shell launch, ordering and discovery failures |
| v3-log-sink | observability | Separate log formatting from batched transport while preserving flush/error semantics | Backpressure trace, byte formatting, failed batch ownership |

### multiple_requirements

| ID | Domain | Own structure and interacting deliverables | Hidden evidence focus |
| --- | --- | --- | --- |
| v3-selection-patch | editor | Multi-cursor document patching, selection rebasing, undo and a CLI demonstration | Overlap atomicity, coordinate shifts, CLI/document consistency |
| v3-archive-extract | filesystem | Streaming archive extraction with traversal rejection, quotas, atomic destination publication and dry-run summary | Path aliases, quota failure cleanup, manifest/output agreement |
| v3-policy-migration | access_control | Policy format migration, backward-compatible reader, least-privilege default and operator migration notes | Old/new round trips, denied unknowns, documented invocation |
| v3-job-compensation | workflow | Durable multi-step job runner with idempotency keys, compensation and status export | Failure at each boundary, replay safety, exported state consistency |
| v3-connection-drain | resource_pooling | Drainable connection pool with bounded wait, shutdown diagnostics and public usage example | Waiter wakeups, no new leases after drain, example behavior |
| v3-replay-dedup | event_processing | Append/replay log with deduplication, tombstones, compaction and corrupt-record diagnostics | Replay before/after compaction, deterministic rejection, old-file safety |
| v3-catalog-extract | localization | Extract messages from source spans, merge translator comments, emit stable catalog and CLI errors | Comment ownership, repeat extraction, exit/stdout/stderr contract |
| v3-query-explain | search | Query AST parser, filter pushdown, explain tree and compatibility adapter | Logical equivalence, spans, explain/actual execution agreement |
| v3-cache-invalidation | caching | Dependency-tag invalidation, namespace isolation, stats and maintenance CLI | Selective eviction, overlapping tags, consistent counters/output |

### two_session

Day 1 specifies all policy values unambiguously; day 2 never repeats them.
Each task retains the ordinary code/workspace in both configurations. H3 also
retains its plugin-written ledger. A receives no synthesized memory. A fresh
day-2 session gets only the new public request; it can inspect retained files.
No day-1 prompt, transcript, private test outcome or runner summary is injected.

| ID | Domain | Day 1: distinct implementation and decisions | Day 2: dependent extension / grading |
| --- | --- | --- | --- |
| v3-stream-negotiation | text_protocol | Version-negotiated request/response codec; fix capability intersection and unknown-extension policy | Add multiplexing while preserving negotiated capability and rejection behavior |
| v3-page-recovery | storage | Slotted-page store; implement a specified torn-write recovery and page-version policy | Add vacuum/reopen without changing recovered records or page compatibility |
| v3-shift-calendar | scheduling | Shift recurrence compiler; implement explicit holiday precedence and boundary convention | Add range export preserving both decisions on overlapping shifts |
| v3-document-theme | rendering | Document stylesheet cascade; implement inheritance, explicit reset and stable resource naming | Add print rendering with the same cascade and resource identities |
| v3-import-reconcile | data_exchange | Reconciliation import pipeline; implement a stated conflict order and row-rejection atomicity | Add resumable chunk ingestion preserving conflict results and rejection boundaries |
| v3-component-order | graph | Strong-component condensation; implement explicit representative and topological tie policies | Add incremental edge updates preserving identities and deterministic output |
| v3-secret-redaction | configuration | Config inspection tool; implement named secret-field propagation and masking policy | Add diff/export without revealing secrets through changed/nested values |
| v3-package-lock | build_tooling | Package lock resolver; implement a stated prerelease and source-precedence policy | Add offline verification preserving resolution and reproducible lock bytes |
| v3-trace-sampling | observability | Trace collector; implement specified root sampling and child inheritance | Add tail export retaining the same sampling decisions after partial arrival |

### ambiguous_requirement

Each public prompt deliberately omits exactly one policy axis below. All other
requirements, constraints and test commands are explicit. A frozen author note
chooses one policy before any run; the hidden grader applies that choice in
both configurations. The choice and note text are not published in this design,
public task files, hook input or initial executor prompt. Authors construct
cases that discriminate the two plausible choices and document why the prompt
alone cannot resolve them. The hidden choice is an intentional experimental
oracle, not an ordinary derivable public requirement; report it as such.

| ID | Domain | Own structure | Single under-specified axis / grader coverage |
| --- | --- | --- | --- |
| v3-editor-anchor | editor | Collaborative edit transform with anchor positions | Attachment side of an insertion at an existing cursor; compare successive transforms |
| v3-copy-collision | filesystem | Recursive copy planner with an atomic commit step | Treatment of an already present destination; exercise dry-run and commit |
| v3-token-expiry | access_control | Signed-token verifier with injectable clock | Inclusivity of the exact expiry instant; check validation and refresh |
| v3-approval-quorum | workflow | Approval state machine collecting role votes | Whether the requester contributes to quorum; check transitions and audit output |
| v3-pool-resize | resource_pooling | Resizable worker pool with pending leases | Disposition of active leases when shrinking below occupancy; check wakeup behavior |
| v3-event-tie | event_processing | Merge of independent event streams with equal timestamps | Tie precedence between streams; check streaming and checkpoint replay |
| v3-locale-fallback | localization | Catalog fallback resolver returning source locale | Precedence of regional versus configured fallback; check lookup and provenance |
| v3-search-empty | search | Query evaluator composing match sets with filters | Meaning of an empty query; check pagination and filtered counts |
| v3-cache-refresh | caching | Refreshing cache exposing stale values and loader errors | Whether stale data may be returned on refresh failure; check expiry/error interaction |

## Clarification protocol and disclosed asymmetry

H3's first-prompt hook writes the requirements table and open questions under
the plugin artifact contract in [AGENTS.md](../../AGENTS.md). Exact paths,
schemas, atomic publication and session identity are defined there, not here.
Before authoring, freeze a runner-only question matcher for each ambiguity:
the missing subject and choice axis, a bounded list of normalized phrase pairs,
and the single fixed reply. Normalize Unicode/case/whitespace; require a
nonempty interrogative open-question entry matching both subject and axis.
For example, a question about an expiry boundary is eligible; a generic request
to clarify the task or an executor assertion of an assumed policy is not.
Freeze positive paraphrase and unrelated-question fixtures before model runs;
no runtime LLM judge or outcome-based manual matching. The matcher and note
are trusted responder data, separate from graders and their paths.

The proposed runner observes only schema-valid, newly published hook tables
bound to the current task/session and plugin invocation. An executor-created
lookalike file, quoted question in a final message, stale artifact, arbitrary
tool output or generic question does not trigger a reply. Retain table hash,
question locator/text, matcher version/result, reply hash and delivery time.
Never inspect grader source to generate a reply. If several eligible questions
refer to the same omission, send the one note once. Unrelated questions receive
no invented information and are logged. No note is delivered without an
eligible hook question, even if the executor independently guessed correctly.

For noninteractive `codex exec`, the plugin must support a question-only pause
before implementation: publish the table, surface the question and finish the
process without a work-completion audit or ledger-generation turn. After exit,
the runner validates the artifact, then delivers the frozen note verbatim as a
user message through `codex exec resume` of the same session. This is a
clarification turn, not a new session, quality retry or runner-written contract.
The hook reuses its requirements table, binds the answer, and eventually emits
one completion report at the actual work-completion boundary. It must not
spend a third Luna call on the answer or a deterministic retry. If no eligible
question occurs, no clarification resume occurs. Budget at most one such
resume per ambiguous task. The plugin's pause/resume lifecycle and artifact
provenance need Role 1/2 confirmation and a compatibility probe before runner
implementation; this document does not add hook JSON fields or CLI flags.

In A, plugin hooks are disabled and the same observer finds no hook table:
there is no eligible question and no note delivery. Do not scan A's prose or
provide it an alternate responder. If A asks in its final output, retain that
evidence and score its artifact under the unchanged oracle, with no reply.
H3 also receives no note when its hook fails to ask. Guessing the wrong policy
fails the relevant hidden requirement; guessing correctly can pass. Thus this
stratum measures a hook-mediated information advantage, not equal-information
reasoning ability. Disclose this in every comparison and report the nine
ambiguous tasks separately, alongside results excluding them. Both initial
prompts and all non-clarification runtime settings are paired.

## Difficulty, calibration and freeze

Target A pass rate 60–85% on the 45 single-session tasks, with ordinary and
ambiguous single-session results also separated. This is a target, not a
forecast. Difficulty comes from diagnosis, state transitions, constrained
resource use, atomicity, provenance, public test quality and interacting
deliverables, rather than longer copies of one requirements list. Constraints
must be explicit and executable; use operation counts/injected clocks rather
than noisy wall-time limits. Public tests are useful but incomplete.

Before building the held-out population, author ten separate single-session
calibration tasks (two per single-session shape), excluded permanently from
the 54 and with different implementations/fixtures. Run A only after a pilot
estimate is approved; inspect five pilot-A outputs manually. A result of 6–8
passes out of ten is compatible with the target but has wide uncertainty.
Review per-shape difficulty and independently review the complete candidate,
since v2's pilot did not predict its full-population ceiling. Do not claim the
held-out rate has been calibrated. If calibration misses the target, revise
the authoring specification before construction, retain candidate identities,
and use fresh calibration material; never select held-out tasks by outcomes.

Freeze public inputs, private graders/references, author notes/matchers, review
sampling seed, scoring rubric, plugin revision/config, model/effort, Codex
version and pricing snapshot before paired A/H3 runs. Role 1 publishes the
population identity after host validation. Do not tune hooks or tasks on frozen
v3 outcomes; any revision needs a separately identified future population.
If full A misses 60–85%, disclose the miss without replacing easy tasks.

## Grader acceptance rules

Offline construction and validation are authorized for the current candidates;
independent host review and freeze remain separate work. For every task require: reference passes all checks; untouched
starter fails at least one substantive requirement; every requirement has
executed hidden coverage, including tests, constraints and day-1/day-2 carryover.
Feature-test deliverables must run and expose a relevant regression: merely
creating a test file is insufficient. Protected bytes, signatures, absence of
side effects and complexity bounds each need their own executable oracle where
specified. Except for the one declared ambiguity axis, every hidden expectation
must be derivable from public requirements. Reference authors document the
derivation, and independent review resolves ambiguity before freezing.

Mutation validation exhausts the declared generated population per task and
adds targeted requirement-breaking mutants for interactions not reached by AST
operators. Require zero surviving non-equivalent mutants, zero validation
errors and private hash-bound reviews for every claimed equivalent. Record
generated, killed, equivalent, survivor and executed counts; the tool's generic
90% threshold is insufficient. Unexecuted or timed-out mutants are unresolved,
not killed. Independent spot mutations supplement the generated population.

No private grader assertion line may be shared with any public input, including
prompt, starter, public tests and expected/metadata files. Independently author
oracle input/expected pairs; relabeling a public assertion is insufficient.
Retain public-input overlap checks, private marker scans and corpus checks.
Executor-corpus overlaps are warnings requiring review and counts of files
examined; they never waive assertion overlap, access evidence or missing
coverage. Publish counts and task IDs only, never grader lines or notes.

Apply STOP-E4 to executor and hook/control evidence. Grade only audit-clean
artifacts in fresh trusted copies after all executor and spawned processes exit.
Never expose graders to either configuration or run Codex in grading copies.
Invalid tasks invalidate the headline report; their spending remains included.

## Human review of 20 tasks

Before outcomes, choose a deterministic stratified sample using seed 0 and
sorted frozen task IDs: four ambiguous, four multiple-requirements and three
each of bug-fix, feature-plus-test, refactoring and two-session tasks (20 total).
Use seeded selection within each shape; retain selected IDs and sampling code
hash. Review both sessions for selected two-session tasks. Do not replace
missing, malformed or invalid artifacts with nicer examples. Reviewers receive
hash-pinned H3 tables/reports, source prompts, author notes and trusted hidden
per-requirement results only after execution; none is sent back to models.

Two reviewers independently map atomic table entries to the frozen requirement
map, then adjudicate disagreements with a retained rationale. Requirements-table
precision is supported, correctly stated nonduplicate entries divided by all
asserted checkable entries. Invented constraints, incorrect restatements and
duplicates are false positives. A faithfully stated open question is not an
asserted requirement; score it separately as correctly/incorrectly raised.
Report coverage/recall alongside precision to expose omissions or empty tables.

Completion-report accuracy is correct per-requirement pass/fail assessments
divided by all required assessments, using hidden grading as the reference.
Missing, unverifiable or unmappable assessments are not correct; report their
counts, false-pass and false-fail counts separately. A report entry marked pass
without a cited, traceable observation is inaccurate even if the grader passes.
Compare a report with the exact workspace revision it evaluated: a report
preceding a retry is scored against a post-exit copy of that pinned revision,
and its staleness against final output is disclosed. A public-only revision
snapshot can be captured at Stop, but no graders are added or run until all
executor/spawned work exits. If that revision is unavailable, record missing
accuracy evidence rather than substituting final results. Include all versions
in review; never silently treat a pre-retry report as a final audit.

Publish task-macro values with task-cluster bootstrap intervals, denominators,
artifact availability, reviewer agreement and adjudications. Show entry-micro
counts as diagnostics and label the stratified sample (not a 54-task census).
Invalid tasks have no trusted grading and remain unscored for accuracy, with
exclusion counts; never grade them to fill the sample. Within valid sampled
tasks, absent required artifacts/assessments count as missing and incorrect,
so selective artifact emission cannot improve the score. No eligible trusted
observations means undefined accuracy, not zero hidden failures.
Use the existing task artifact path/hash references to retain eval-owned review
sidecars; do not add fields to the shared report metric object. A has no table
or completion report: user-facing artifact measures are not applicable to A,
not zero. Its hidden outcomes and retained final claims remain paired evidence.

## Analysis and success criteria

Preserve pass_rate, cost_per_pass, task_false_done_rate, false_done_rate,
avg_attempts and handoff_success with valid-task units and seeded 10,000
task-cluster bootstrap replicates. Pair A/H3 tasks, including both sessions in
one cluster; report shape splits, single-session results and ambiguous-excluded
results. The legacy local-minus-cheap_api parity field remains unmeasured,
not redefined as H3-minus-A. User-facing review metrics are separate artifacts.

Assess the approved goals: H3 matches A within the paired pass-rate interval,
halves task-level false-done, and has cost_per_pass at most 1.15 times A.
Operationalize the quality check as no lower observed pass rate and a paired
95% difference interval containing zero or wholly above zero; any observed
quality loss fails. An interval containing zero alone does not establish
equivalence; disclose uncertainty and small strata. Retain ratios/intervals for
false-done and cost; zero baseline false-done or missing accounting makes the
corresponding relative claim undefined, not achieved. Freeze this interpretation
with the analysis plan before runs; do not infer success from a nonsignificant
quality loss. No claim is measured in this session.

## Assumptions

- 54 tasks, balanced shapes and the 20-task sampling allocation are design
  choices within the approved range; only the nine bug-fix candidates have been
  constructed in this checkpoint. The complete population remains pending.
- The plugin contract in AGENTS.md will define exact artifact paths and schemas.
  Question-only pause/resume, hook provenance and report revision binding must
  be confirmed before implementation; no shared interface is changed here.
- Two Luna calls means one table and one claim audit per logical work session;
  clarification, ledger continuation and deterministic retry reuse session state.
- The existing Fast snapshot is an offline planning reference. Host probes,
  pinned tool/plugin identities and spending approval remain future work.
