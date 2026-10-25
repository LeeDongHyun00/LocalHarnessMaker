jobs.py drives pure deterministic generators. A factory yields (unique nonempty
string key, JSON-compatible payload); sending a JSON-compatible effect result
computes the next step. Effects are injected and may raise before making any
external change. A generator terminates normally, and never raises otherwise.
Keep Job(name, factory, effect), step() -> bool, snapshot() -> dict; add restore.

WC1. A successful step invokes effect(key, payload) exactly once, saves its
result, and sends the result to the generator. Return True for each executed
step, False after exhaustion. Effect failure propagates, leaves the same step
pending, and does not alter the snapshot; a later step can retry it.
WC2. snapshot is JSON serializable and exactly {'version': 1, 'job': name,
'completed': [{'key': key, 'result': result}, ...]}. All returned and restored
data must be independent deep copies. Add restore(checkpoint) -> None: replay
the generator with recorded results without invoking any completed effects,
then continue at the first unfinished step. Completed jobs restore as exhausted.
WC3. Before altering current state or invoking effects reject malformed fields,
non-integer or wrong version, wrong job name, non-list completed, malformed
entry fields, key mismatch or a prefix longer than the job with ValueError.
Inputs described as JSON-compatible need no extra type validation. Add a
regression test detecting restore repeating an already completed side effect.

WC4. Keep test_public.py byte-for-byte unchanged and keep its tests
passing. Supply executable regression tests as described above.

Use Python 3.11+ and the standard library. Keep the public signatures and existing
behavior except for the specified feature. Add meaningful unittest tests to
regression_tests.py (not test_*.py); they must pass with the implementation and
fail for the regression named above, even when that defective implementation
still exposes the complete API. Do not change test_public.py. Run both
`python -m unittest discover -s . -p "test_*.py" -v` and
`python -m unittest regression_tests -v` from workspace/.
