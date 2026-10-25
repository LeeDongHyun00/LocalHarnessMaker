Complete jobs.py as a durable compensating job runner. Keep Runner(path, perform,
compensate), run(job_id, steps)->dict and export(job_id)->dict. path's parent exists;
steps is a list of distinct nonempty strings and job_id is nonempty, neither may
contain ':'. perform(step,key) returns a JSON value. compensate(step,key,value)
undoes a successful result. Callbacks are injected and idempotent by key; an
Exception from perform guarantees that invocation made no external effect.

JC1. Persist a job before callbacks and persist each callback boundary using atomic JSON-file replacement. Export exactly steps, state, done, pending, error, undone. Initially state='running', done=[], pending=None, error=None, undone=[]. done entries are {'step':str,'value':JSON}; preserve step order. Before each perform persist pending=step; on success append its result and clear pending.
JC2. perform keys are job_id + ':' + step. Reopening Runner resumes only unfinished steps, reusing the same key for a pending callback. A BaseException simulates process interruption: propagate it leaving the durable pending step for replay. Never repeat a committed successful callback. All steps succeeding (including an empty plan) sets state='succeeded'. A succeeded or failed job is terminal and another run makes no callbacks.
JC3. On an Exception from perform, store str(exc) as error, clear pending, enter 'compensating' and undo only completed steps in reverse order. Before undo persist pending=step; compensation keys append ':undo' to the perform key. After each successful undo append its step to undone and clear pending. Finish with state='failed'; retain done as history. A compensation exception propagates, leaving state/pending for replay with the identical undo key and without repeating committed undos or any performs.
JC4. Reject invalid identities with ValueError('identity') before creating state. A repeated job_id with a different ordered steps list raises ValueError('plan') without callbacks or durable changes. Distinct jobs share a file but never share progress or keys. run/export return deep copies; callback mutation of a compensation value must not mutate done history.
JC5. Add STATUS.md documenting all four state names and idempotent callback replay. Include the literal key formulas `job_id + ':' + step` and `job_id + ':' + step + ':undo'`, and an executable fenced `python` example using tempfile and injected callbacks. The example must call run on at least two steps, export the same job, assert equality of run/export and print exactly 'status example ok' plus newline.

Use Python 3.11+ and only the standard library. Preserve the stated APIs.
Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
