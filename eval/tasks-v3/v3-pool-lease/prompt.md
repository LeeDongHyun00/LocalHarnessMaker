Extend the bounded ticket pool in leases.py with expiring renewable leases.
Pool(capacity, clock) uses a positive capacity and injected nondecreasing clock;
times and TTLs are finite real numbers. This API is single-threaded/nonblocking.

PL1. request() issues an opaque FIFO ticket. acquire(ticket, ttl) returns a Lease
only if that same-pool ticket is the oldest pending ticket and capacity is free;
otherwise None without removing it. Acquired tickets are consumed permanently.
A foreign-pool ticket raises ValueError. Nonpositive TTL raises ValueError before
any state change. Successful acquire sets deadline to clock() + ttl.
PL2. Expire leases lazily before acquire, renew and release; a lease is inactive
at now >= deadline and frees one slot. Lease.renew(ttl) sets a live lease's
deadline to now + ttl (it may shorten it), returns None, and raises RuntimeError
if expired/released. Nonpositive renewal TTL raises ValueError without change.
Never resurrect an expired lease or release capacity twice.
PL3. Lease.release() returns True only on the first live release, False otherwise.
Lease is a context manager returning itself and releasing on normal/exceptional
exit without swallowing exceptions. FIFO is retained across expiry and renewal.
Add a fake-clock regression test that detects renewal leaving the old deadline
in effect, so a renewed live lease is incorrectly reclaimed at the old expiry.

PL4. Keep test_public.py byte-for-byte unchanged and keep its tests
passing. Supply executable regression tests as described above.

Use Python 3.11+ and the standard library. Keep the public signatures and existing
behavior except for the specified feature. Add meaningful unittest tests to
regression_tests.py (not test_*.py); they must pass with the implementation and
fail for the regression named above, even when that defective implementation
still exposes the complete API. Do not change test_public.py. Run both
`python -m unittest discover -s . -p "test_*.py" -v` and
`python -m unittest regression_tests -v` from workspace/.
