Implement Merge(streams, checkpoint=None) in merge.py. streams is an insertion-
ordered mapping from unique nonempty stream names to finite iterables of
(timestamp, payload). Each stream is nondecreasing by integer timestamp; payloads
are arbitrary objects and must not be compared. Stream names and inputs do not
change during a merge. Inputs are restartable by supplying fresh iterables when
resuming, not by reusing exhausted generators.

EV1. take(n) returns up to n (stream_name, timestamp, payload) triples in ascending
timestamp order. Keep each individual stream's original order, emit every event
once, and return [] after exhaustion. n is an exact nonnegative int, otherwise
ValueError('count') with no consumption. take(0) does not fetch input.
EV2. Equal timestamps across different streams need deterministic precedence.
The product has not chosen stream-name order versus mapping insertion order.
Apply the same choice across batched take calls and checkpoint replay.
EV3. checkpoint() returns a new dict with an emitted-event count for EVERY stream,
including zero-count streams. Prefetched events are not counted as emitted.
Resuming skips exactly those counts in fresh streams, then emits the unconsumed
suffix in the same order as uninterrupted execution. A supplied checkpoint must
have exactly the stream keys and exact nonnegative int counts, else raise
ValueError('checkpoint') before fetching input. Counts beyond stream lengths raise
ValueError('checkpoint') when the merge is first read; do not silently truncate.
EV4. Stay streaming: before first positive take, do not fetch events. Thereafter
keep at most one unconsumed lookahead event per nonempty stream. No materializing
entire iterables, no input mutation; take(n) may fetch the replacement lookahead
for each emitted item. Mutating a returned checkpoint cannot alter merge state.

Use Python 3.11+ and the standard library. Preserve the stated API. Change application
code and add regression tests as needed. Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
