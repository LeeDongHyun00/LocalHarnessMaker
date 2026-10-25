Complete Collector(rate) in traces.py. rate is an integer in [0,100]. accept(span)
records a span dict with exactly trace, id, parent, start, end: trace and id are
nonempty strings, parent is None or a different nonempty span-id string; start
and end are integer timestamps (not bool) with start <= end. Parent relationships
within each trace are acyclic; parents may arrive later. A span's parent is in
the same trace. Use Python 3.11+ and the standard library.

TS1. A root has parent=None. Its trace is sampled iff the unsigned big-endian
integer represented by SHA256(trace.encode('utf-8')).digest() modulo 100 is less
than rate. No random state, duration, span-id hash or arrival position affects
sampling. rate 0 keeps none; rate 100 keeps every rooted trace.
TS2. Children inherit that root's decision, at any depth, even if received
before ancestors. export() returns only spans connected to an observed sampled
root. Withhold orphans until their ancestors arrive; never infer a root from an
unknown parent. Unsampled traces export nothing. Sort by (trace,start,id).
TS3. Duplicate (trace,id) uses first-write-wins, including a later different
VALID payload; return None. Distinct traces can reuse IDs. A second distinct
root in one trace, or any malformed span, raises ValueError('span') without
changing state. accept returns None; export returns independent dicts. Snapshot
caller input. rate is fixed on construction. Preserve these APIs; add tests
and run python -m unittest discover -s . -p 'test_*.py' -v in workspace/.
