Complete WorkerPool(limit, on_ready) in workers.py. This is a synchronous worker-slot
allocator, not a thread launcher. Limits are exact nonnegative ints. acquire(ticket)
returns a unique positive integer lease immediately when a slot is available, or
None and queues the ticket when full. Tickets are unique strings across calls.
release(lease) returns True once for a live lease and False for unknown/already
released IDs. resize(limit) changes capacity; active is a frozenset of live IDs
and pending is a tuple of queued tickets. Keep this API.

WP1. Use monotonically increasing lease IDs, starting at 1, never reused. Queued
tickets receive available slots FIFO. Only queued grants call on_ready(ticket,
lease); immediate acquire grants do not. release and resize must drain all slots
that become available and remove granted tickets before notifying callbacks.
WP2. Shrinking below active occupancy needs a policy for the active leases; the
product has not chosen whether to revoke them or let them finish. Apply that
choice consistently to active, later releases and pending wakeups. A revocation
policy would revoke newest IDs first with no callback. A retained-lease policy
must wait until occupancy drops below the new limit before granting queued work.
WP3. Zero capacity is allowed. Negative/non-int limits raise ValueError('limit')
with no state changes. Callback exceptions propagate, but a notified lease remains
active and its ticket is already removed; a later release/resize can drain the
remaining queue without redelivery. Callbacks do not reenter the pool. Read-only
active/pending snapshots cannot mutate pool state. No clock or background thread.

Use Python 3.11+ and the standard library. Preserve the stated API. Change application
code and add regression tests as needed. Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
