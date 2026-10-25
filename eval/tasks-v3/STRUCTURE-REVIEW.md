# Version 3 structure comparison — construction checkpoint

Original bug-fix author comparison: 36 pairs checked on
architecture, data flow and failure mechanism. Each numeric result is the number
of differing axes (maximum 3). The detailed rationale remains in trusted storage.
This author comparison is not the independent reviewer required by DESIGN.md;
Claude's host review and comparison across all 54 tasks remain pending. No
calibration, freeze or outcome-based task selection is claimed.

| Task | Task | Axes checked | Differing axes |
| --- | --- | ---: | ---: |
| v3-cancelled-deadline | v3-cycle-witness | 3 | 3 |
| v3-cancelled-deadline | v3-framed-stream | 3 | 3 |
| v3-cancelled-deadline | v3-histogram-merge | 3 | 3 |
| v3-cancelled-deadline | v3-incremental-fanout | 3 | 3 |
| v3-cancelled-deadline | v3-origin-shadow | 3 | 3 |
| v3-cancelled-deadline | v3-quoted-record | 3 | 3 |
| v3-cancelled-deadline | v3-savepoint-unwind | 3 | 3 |
| v3-cancelled-deadline | v3-wide-column | 3 | 3 |
| v3-cycle-witness | v3-framed-stream | 3 | 3 |
| v3-cycle-witness | v3-histogram-merge | 3 | 3 |
| v3-cycle-witness | v3-incremental-fanout | 3 | 3 |
| v3-cycle-witness | v3-origin-shadow | 3 | 3 |
| v3-cycle-witness | v3-quoted-record | 3 | 3 |
| v3-cycle-witness | v3-savepoint-unwind | 3 | 3 |
| v3-cycle-witness | v3-wide-column | 3 | 3 |
| v3-framed-stream | v3-histogram-merge | 3 | 3 |
| v3-framed-stream | v3-incremental-fanout | 3 | 3 |
| v3-framed-stream | v3-origin-shadow | 3 | 3 |
| v3-framed-stream | v3-quoted-record | 3 | 3 |
| v3-framed-stream | v3-savepoint-unwind | 3 | 3 |
| v3-framed-stream | v3-wide-column | 3 | 3 |
| v3-histogram-merge | v3-incremental-fanout | 3 | 3 |
| v3-histogram-merge | v3-origin-shadow | 3 | 3 |
| v3-histogram-merge | v3-quoted-record | 3 | 3 |
| v3-histogram-merge | v3-savepoint-unwind | 3 | 3 |
| v3-histogram-merge | v3-wide-column | 3 | 3 |
| v3-incremental-fanout | v3-origin-shadow | 3 | 3 |
| v3-incremental-fanout | v3-quoted-record | 3 | 3 |
| v3-incremental-fanout | v3-savepoint-unwind | 3 | 3 |
| v3-incremental-fanout | v3-wide-column | 3 | 3 |
| v3-origin-shadow | v3-quoted-record | 3 | 3 |
| v3-origin-shadow | v3-savepoint-unwind | 3 | 3 |
| v3-origin-shadow | v3-wide-column | 3 | 3 |
| v3-quoted-record | v3-savepoint-unwind | 3 | 3 |
| v3-quoted-record | v3-wide-column | 3 | 3 |
| v3-savepoint-unwind | v3-wide-column | 3 | 3 |

## Cross-shape author review — 2026-10-25

The 24 pairs below cover all six shapes, deliberately including tasks in the
same domain. Review uses public prompts, APIs and starter structures; no private
oracle or omitted policy is disclosed. Each cell compares A to B on one DESIGN
axis. Shared mechanics are stated explicitly; this is author review, not Claude
host acceptance. The remaining all-population independent review is pending.

| A | B | Architecture | Data flow | Failure mechanism |
| --- | --- | --- | --- | --- |
| v3-framed-stream | v3-token-scanner | Persistent callback decoder versus lazy token iterator | Chunked bytes to retired frames versus text to spanned tokens | Split delimiter/recovery versus quadratic suffix copying |
| v3-framed-stream | v3-stream-negotiation | Callback decoder versus negotiated packet codec | Partitioned byte feeds versus agreement snapshot and whole JSON packets | Lost frames versus capability/version rejection and snapshot drift |
| v3-token-scanner | v3-stream-negotiation | Lazy lexical iterator versus negotiation plus codec | Character cursor to token spans versus offers to agreement to packets | Eager/quadratic scanning versus protocol-policy carryover on day 2 |
| v3-savepoint-unwind | v3-journal-codec | Recursive context ownership versus pure codec and I/O adapters | SQL nesting to savepoint stack versus bytes to records and tail | Parent rollback versus short-write/checksum separation |
| v3-savepoint-unwind | v3-page-recovery | SQLite context manager versus slotted snapshot store | Ordered statements and unwind versus append-only pages and reopen | Inner rollback ownership versus torn suffix and slot reuse across reopen |
| v3-journal-codec | v3-page-recovery | Record codec/adapters versus fixed-page state store | Variable-length records to tail versus versioned snapshots to slot map | Checksum offset/short writes versus page recovery/version carryover |
| v3-cancelled-deadline | v3-ready-queue | Timer heap with callbacks versus indexed ready queue | Clock cutoff and newly due work versus priorities to payload dispatch | Cancelled head starvation versus comparison bound/key reuse; cancellation mechanics shared |
| v3-cancelled-deadline | v3-shift-calendar | Timer service versus recurrence compiler | Clock-driven mutable pending work versus dates to resolved intervals | Callback retirement versus holiday/overnight policy carryover |
| v3-ready-queue | v3-shift-calendar | Indexed mutable queue versus calendar compiler | Push/cancel/pop versus recurrence expansion and overlap sweep | Tie stability and bounded comparisons versus date precedence and interval coalescing |
| v3-wide-column | v3-html-events | Width-based table pipeline versus explicit traversal stack | Glyphs to wrapped/padded cells versus nodes to escaped markup | Combining-mark alignment versus recursion depth and byte preservation |
| v3-wide-column | v3-document-theme | Terminal layout functions versus stylesheet cascade | Text widths to columns versus inherited style to resource/render output | Soft-wrap placement versus reset/inheritance policy carryover |
| v3-html-events | v3-document-theme | Event-stack serializer versus cascade engine | Node traversal to bytes versus ancestry to resolved styles/resources | Recursion/escaping versus inherited reset and stable resource identities; tree mechanics shared |
| v3-origin-shadow | v3-config-dispatch | Layered value resolver versus directive-handler registry | Source layers to value/provenance versus ordered source lines to handler results | Explicit empty shadowing versus diagnostic/order preservation during dispatch refactor |
| v3-origin-shadow | v3-secret-redaction | Settings resolver versus secret-aware inspector | Layer selection to provenance versus nested config to masked projections | Empty fallback versus secrecy propagation into day-2 diff/export |
| v3-config-dispatch | v3-secret-redaction | Handler dispatcher versus redaction propagation | Directive stream to registered handlers versus nested values to masked paths | Extension routing/diagnostics versus secret-policy carryover |
| v3-undo-group | v3-selection-patch | Command history/context groups versus document batch patcher and CLI | Command do/undo stream versus original coordinates to text/selections | Nested abort/redo invalidation versus overlap atomicity and coordinate rebasing |
| v3-undo-group | v3-editor-anchor | Grouped command history versus cursor transform functions | Reversible side effects versus edit iterable to cursor positions | Partial group rollback versus omitted insertion attachment policy |
| v3-selection-patch | v3-editor-anchor | Mutable document/undo plus CLI versus document-free transforms | Simultaneous original-coordinate edits versus sequential current-coordinate edits | Batch validation/rebasing versus boundary policy and iterable consumption |
| v3-link-preview | v3-archive-extract | Read-only filesystem walker versus streaming extractor | Link chains to classified plans versus tar stream to staged directory/summary | Relative-link base and cycles versus traversal/alias/quota cleanup |
| v3-link-preview | v3-copy-collision | Link classifier versus snapshot/commit copy plan | Filesystem links to statuses versus source bytes to deferred publication | Target resolution versus collision policy/source drift; planning mechanics shared |
| v3-archive-extract | v3-copy-collision | Streaming archive publication versus reusable snapshot plan | Nonseekable entries to temporary tree versus captured source to later commit | Quota/normalized alias rejection versus destination policy and source revalidation; atomic staging shared |
| v3-pool-lease | v3-connection-drain | Nonblocking clocked ticket pool versus thread-safe drainable resource pool | FIFO tickets to timed leases versus waiters/resources to close diagnostics | Renewal expiry/double release versus drain wakeups and close-once ownership |
| v3-pool-lease | v3-pool-resize | Expiring lease objects versus callback-based slot allocator | Clock and TTL to deadlines versus capacity changes to queued grants | Old deadline reclamation versus omitted shrink policy/callback retirement |
| v3-connection-drain | v3-pool-resize | Blocking resource pool versus synchronous slot allocator | Resource identity and waits to close attempts versus ticket queue to numeric IDs | Shutdown wakeup/close errors versus shrink policy and callback exceptions; ownership accounting shared |
