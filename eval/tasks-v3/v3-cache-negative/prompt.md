Extend memo.py's Memoizer(loader, ttl, negative_ttl, clock). All durations are
positive finite numbers and clock is nondecreasing/injected. Keys are strings.
Loader never recursively calls the same memoizer. Add separately timed negative
entries and support concurrent callers.

CN1. Cache successful values, including None and false values, for ttl measured
from loader completion. A hit returns the same value object. Expire at now >=
deadline. Cache keys independently; no loader call for a live hit.
CN2. Only NotFound (including subclasses) is a negative result. Cache its args
for negative_ttl from completion and raise NotFound with those same args on a
negative hit. Every other exception propagates unchanged and is never cached.
Negative expiration permits a later success; positive expiration permits a
later negative result. Never use positive ttl for a negative entry.
CN3. At most one loader invocation per key may be in flight. Same-key callers
wait then recheck the entry; unrelated keys may load while a loader is blocked.
Release waiters after success or any exception. Loader executes outside the
global cache lock. Add a fake-clock regression test detecting a negative result
incorrectly surviving its shorter negative TTL because positive TTL was used.

CN4. Keep test_public.py byte-for-byte unchanged and keep its tests
passing. Supply executable regression tests as described above.

Use Python 3.11+ and the standard library. Keep the public signatures and existing
behavior except for the specified feature. Add meaningful unittest tests to
regression_tests.py (not test_*.py); they must pass with the implementation and
fail for the regression named above, even when that defective implementation
still exposes the complete API. Do not change test_public.py. Run both
`python -m unittest discover -s . -p "test_*.py" -v` and
`python -m unittest regression_tests -v` from workspace/.
