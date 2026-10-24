A cancelled timer sometimes delays unrelated work until a later poll. Repair
Timers(clock) in timers.py without changing call_at(deadline, callback), cancel(handle)
or run_due(). The injected clock returns numeric time; deadlines are numeric.

TM1. call_at returns an integer handle unique for this service's lifetime. Timers
fire in ascending (deadline, insertion order). At each run_due, read the clock
exactly once and execute every active timer whose deadline is <= that reading.
This includes newly scheduled due timers created by a callback in the same poll.
TM2. cancel returns True only when it changes a pending active timer to cancelled;
unknown, already cancelled or fired handles return False. Cancelled heap heads
must not prevent equally due or later-due active timers from firing.
TM3. Remove a timer from pending state before invoking its callback; propagate a
callback exception immediately and leave the rest runnable by a later poll.
run_due returns the number of callbacks executed when it returns normally.
TM4. Cancelling another due callback from a callback takes effect immediately;
future timers survive early polls. Independent Timers objects share no state.

Use Python 3.11+ and the standard library. Preserve the documented public API.
Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
Change application code and add regression tests as needed.
