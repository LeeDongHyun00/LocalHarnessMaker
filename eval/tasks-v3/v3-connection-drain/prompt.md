Finish the thread-safe drainable pool in connections.py. Keep Pool(resources,close),
acquire(timeout=None), release(resource), lease(timeout=None) as a context manager,
drain(timeout=None)->dict, and diagnostics()->dict. Resources are distinct objects;
close(resource) is injected, does not reenter the pool, and may raise Exception.

CD1. Initially open; acquire returns idle resources FIFO by identity. When empty, wait until a resource, drain or timeout. timeout is nonnegative seconds or None for unbounded; timeout=0 never waits; negative raises ValueError('timeout') before effects. Exhaustion raises TimeoutError('pool'). Never lease one resource concurrently twice.
CD2. release returns an active resource to the idle tail while open, waking waiters. Reject foreign or double release with ValueError('lease'). lease must release even when its body raises. Never close an active resource before release.
CD3. drain changes open to draining before waking every blocked acquirer; every acquire after that transition raises RuntimeError('draining'), even if idle resources existed. Close idle resources immediately and close each active resource once on release. State becomes closed when no active resources remain. Repeated drain is safe; no resource closes twice.
CD4. drain waits at most timeout for active leases; expiry returns a draining snapshot without forcibly reclaiming them. A later release or drain may finish closure. Count each close attempt even when close raises; capture str(exc) in close-attempt order and continue retiring other resources.
CD5. diagnostics returns a detached dict with exactly state, idle, leased, waiters, closed, errors; integer counts describe current ownership and closed counts close attempts. All waiters are counted only while blocked. Drain returns the same snapshot shape. No stale counts after wakeup or timeout.
CD6. Add usage.py runnable as `python usage.py`. Demonstrate a lease body raising and recovering, then drain the pool, assert the pool is closed and every resource closed once, and print exactly 'drain example ok' plus newline, exit 0, empty stderr. Use only in-memory resources.

Use Python 3.11+ and only the standard library. Preserve the stated APIs.
Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
