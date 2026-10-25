Add Collector.tail_export(cutoff). Continue the retained collector's sampling,
ancestry and duplicate policies.

TS4. Return newly eligible, previously unsent spans whose end <= cutoff, in the
same order as export. Each accepted span is sent at most once by tail_export;
ordinary export remains a full, non-consuming view. A child may be sent before
its root's end time when its full ancestry is observed. If an orphan was
previously withheld, later parent arrival makes it eligible on the next call,
even when its end predates an earlier cutoff. Do not discard unready spans.
TS5. Tail cutoff values must be nondecreasing; a smaller cutoff raises
ValueError('cutoff') without changing sent state or the last cutoff. Equal
cutoffs are allowed. Late duplicates do not resend or change sampled choices.
Separate traces and unsampled roots must retain the original selection policy
through partial arrival. Retain prior APIs, add tests and run the same command.
