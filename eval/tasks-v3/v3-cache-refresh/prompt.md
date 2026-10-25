Implement Cache(loader, clock, ttl, stale_for) in refresh.py. loader(key) returns
any Python value or raises an exception. clock() returns monotonic numeric seconds;
ttl > 0 and stale_for >= 0 are supplied. No threads/concurrency/reentrant loader.
get(key) returns (value, status), with status 'loaded', 'fresh' or 'stale'.
invalidate(key) removes that key and returns whether it was present.

RF1. Missing entries load synchronously. On success store (value, sampled_time),
return status 'loaded'. A cached entry is fresh only while now < sampled_time+ttl;
then get returns 'fresh' without invoking loader. At equality it needs refresh.
Read clock exactly once per get, before loading, and use that sampled value for
a successful load timestamp even if loading advances time. None/False/0 are values.
RF2. A successful refresh replaces the cached value and resets the freshness
window. Loader exceptions never create entries or extend any stored timestamps.
If no cached value exists, propagate the original exception object unchanged.
An existing stale entry must remain stored after an unsuccessful refresh.
RF3. Returning stale data after a refresh failure is a product policy not yet
chosen. If permitted, stale data is eligible only while now < sampled_time+ttl+
stale_for; at or after that hard boundary propagate the original exception.
If forbidden, propagate regardless of stale eligibility. Use status 'stale' only
when an error is suppressed; never return stale data without first trying refresh.
RF4. Keys are independent. invalidate returns True exactly once for a stored
entry (including an expired one), then False. Invalidated entries cannot supply
stale data; the next get must load again. No background work or exception caching.

Use Python 3.11+ and the standard library. Preserve the stated API. Change application
code and add regression tests as needed. Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
