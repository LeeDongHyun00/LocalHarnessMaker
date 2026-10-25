Add Store.vacuum() in pages.py. Inspect the retained implementation for its
existing storage and recovery policies.

PG4. Vacuum atomically replaces the log with exactly one committed snapshot of
the current in-memory state, using the established writer format. Preserve all
live values, slot identities and allocation history, including pending edits.
Use a sibling temporary file and os.replace; if replacement raises, leave the
original file unchanged, clean up the temporary file and propagate the error.
PG5. Reopen a vacuumed store and continue appending/deleting/committing without
changing compatibility or torn-write handling. Vacuum must also work for an
empty or previously fully deleted store. Add regression tests and run the same
test command. Preserve every prior public API.
