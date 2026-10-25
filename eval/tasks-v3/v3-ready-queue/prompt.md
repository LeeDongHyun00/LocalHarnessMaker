Replace ReadyQueue's repeated full sorting with an indexed priority queue. Keep the ReadyQueue constructor, push(key, priority, payload), cancel(key), pop(), and len(queue).
RQ1. pop returns (key, payload) for the lowest priority; equal priorities dispatch in push order. Keys are strings; priorities support total ordering; payloads may be unorderable. A live duplicate key raises ValueError('duplicate key') without replacing it. pop on no live entries raises IndexError('empty'). Separate instances are independent.
RQ2. cancel returns True exactly when it removes a live key, otherwise False. Cancelled entries never dispatch. Reusing a cancelled or popped key is a new insertion with a new tie position. len counts live entries only. Do not compare payloads.
RQ3. Maintain a key index and priority structure rather than repeatedly sorting or linearly scanning all live entries on pop/cancel. Lazy deletion of cancelled entries is permitted. For any 256-entry workload of pushes followed by cancellations and complete drain, make at most 40*256 priority comparisons (equality plus ordering together); this is an operation bound, not a time limit. Tests may use instrumented priorities and opaque payloads.
RQ4. Preserve the API signatures, state after duplicate/empty errors, and payload identity. Add regression coverage for tie order, cancellation and key reuse.

Use Python 3.11+ and the standard library. Add regression tests as needed.
Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
