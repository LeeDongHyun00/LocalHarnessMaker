Extend commands.py's command history with atomic grouping. Commands implement
do() and undo(); a failing do() is guaranteed not to change the document. No
undo() fails. History.execute(command), undo(), redo() retain their signatures;
undo()/redo() return False when unavailable, True otherwise.

UG1. Add History.group() as a context manager. Successful commands inside it
become one undo/redo entry in execution order; undo reverses that order. Nested
successful groups join the parent. An empty group adds no entry.
UG2. An exception leaving a group undoes only that group's completed commands
in reverse order, propagates the same exception, and leaves history/redo intact.
A caught inner exception permits the outer group to continue. A successful
outermost nonempty group clears redo; aborted and empty groups do not.
UG3. Outside groups execute clears redo only after do succeeds. Undo and redo
inside any open group raise RuntimeError before changing anything. Redo runs
the same commands in order. Add a regression test that detects a group undo
incorrectly reverting only its final command.

UG4. Keep test_public.py byte-for-byte unchanged and keep its tests
passing. Supply executable regression tests as described above.

Use Python 3.11+ and the standard library. Keep the public signatures and existing
behavior except for the specified feature. Add meaningful unittest tests to
regression_tests.py (not test_*.py); they must pass with the implementation and
fail for the regression named above, even when that defective implementation
still exposes the complete API. Do not change test_public.py. Run both
`python -m unittest discover -s . -p "test_*.py" -v` and
`python -m unittest regression_tests -v` from workspace/.
