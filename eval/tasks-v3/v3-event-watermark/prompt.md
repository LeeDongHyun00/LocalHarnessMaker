Extend windows.py's integer event-time accumulator with advance(mark). Width is
a positive integer; timestamps, values and watermarks are integers, including
negative timestamps/values. There is initially no watermark.

EW1. Windows are [k*width,(k+1)*width) for every integer k, including negative k.
add(timestamp,value) returns None and sums values in the appropriate pending
window, preserving zero-sum windows as present. Arrival order is unrestricted.
EW2. advance(mark) -> list[(start,end,sum)] atomically sets the watermark and
removes/returns all present windows whose end <= mark, sorted by start. Emit no
empty windows and never emit a closed window again. Equal marks are allowed;
decreasing marks raise ValueError before changing any state.
EW3. After advancement, add with timestamp < current watermark goes to a late
channel, even if that event's window is still open. Timestamp == watermark is
on time. late() drains and returns late (timestamp,value) pairs in arrival order.
Draining does not alter pending sums. Add a regression test detecting advance
failing to close a present window whose end equals the watermark exactly.

EW4. Keep test_public.py byte-for-byte unchanged and keep its tests
passing. Supply executable regression tests as described above.

Use Python 3.11+ and the standard library. Keep the public signatures and existing
behavior except for the specified feature. Add meaningful unittest tests to
regression_tests.py (not test_*.py); they must pass with the implementation and
fail for the regression named above, even when that defective implementation
still exposes the complete API. Do not change test_public.py. Run both
`python -m unittest discover -s . -p "test_*.py" -v` and
`python -m unittest regression_tests -v` from workspace/.
