Add opaque pagination to postings.py's in-memory postings index. Inputs have
string queries, nonempty string doc IDs and integer scores. Preserve replace.

IC1. Index(records) owns a snapshot. For each exact query deduplicate doc IDs
using their maximum score, then sort descending score and ascending doc ID.
search(query, limit, cursor=None) returns frozen Page(items: list[Posting],
next_cursor: str | None). Unknown query returns an empty page. Require positive
integer limit (bool is invalid), otherwise ValueError.
IC2. A returned cursor continues after the last returned item, without skipping
or duplicating tied scores. It is opaque to callers and deterministic for the
same index revision/query/position; limit can change between pages. next_cursor
is None exactly when no rows remain. Returned item lists are independent.
IC3. Bind every cursor to the exact query and the whole index revision. Any
replace, even an unrelated query or unchanged data, invalidates old cursors.
Invalid/malformed/mismatched cursors raise ValueError before changing state.
Use URL-safe base64 of UTF-8 JSON with exactly v=1, query, revision (integer),
offset (non-bool integer between 0 and the current result length inclusive);
reject wrong fields, types, version, query, revision or position. Cursor is
opaque but not authenticated. Add a regression test detecting tied-score rows
skipped when a continuation is based only on score instead of full position.

IC4. Keep test_public.py byte-for-byte unchanged and keep its tests
passing. Supply executable regression tests as described above.

Use Python 3.11+ and the standard library. Keep the public signatures and existing
behavior except for the specified feature. Add meaningful unittest tests to
regression_tests.py (not test_*.py); they must pass with the implementation and
fail for the regression named above, even when that defective implementation
still exposes the complete API. Do not change test_public.py. Run both
`python -m unittest discover -s . -p "test_*.py" -v` and
`python -m unittest regression_tests -v` from workspace/.
