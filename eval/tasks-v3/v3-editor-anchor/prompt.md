Implement collaborative cursor transforms in anchors.py. An edit is ('insert', at,
text) or ('delete', start, end); each edit uses the document coordinates AFTER all
preceding edits. Positions count Python Unicode code points, never encoded bytes.
The caller supplies edits within the current document; no document is supplied.

AN1. transform(cursor, edits) returns the cursor after every edit in order. Insertion
strictly before the cursor advances it by len(text); insertion strictly after it
leaves it alone. Deletion [start,end) maps cursors inside it to start and shifts
cursors at or after end left by end-start. Empty inserts/deletes do nothing.
AN2. Handle an insertion exactly at an existing cursor consistently in transform
and transform_many(cursors, edits), including successive transforms. This boundary
needs the product's attachment-side policy; it has not been specified here.
AN3. transform_many returns a new list in input order and consumes an edit iterable
only once. Neither function mutates caller lists or edit tuples. Empty edit streams
preserve positions. Keep both signatures, accepting arbitrary finite iterables.
AN4. Negative cursors/positions, reversed deletions, unknown edit kinds, wrong tuple
lengths and non-string insertion text raise ValueError before returning a result.
All positions must have exact type int. Invalid edits are rejected even when there
are no cursors. No clamping of invalid input.

Use Python 3.11+ and the standard library. Preserve the stated API. Change application
code and add regression tests as needed. Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
