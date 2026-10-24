# Version 3 structure comparison — construction checkpoint

Author comparison of the nine constructed bug-fix tasks: 36 pairs checked on
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
