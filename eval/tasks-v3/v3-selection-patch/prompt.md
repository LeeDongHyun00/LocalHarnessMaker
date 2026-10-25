Complete the multi-cursor editor in patching.py and its JSON CLI. Coordinates are
Python string indices, not bytes. Keep Document(text, selections), text,
selections, apply(edits), undo(), and `python patching.py`.

SP1. Selections and edits are half-open (start,end) pairs with 0 <= start <= end <= len(text). apply receives (start,end,replacement) triples in original-document coordinates, accepts unsorted edits, and applies them simultaneously. Reject bad ranges with ValueError('range').
SP2. Reject intersecting nonempty replacement ranges, an insertion strictly inside a replacement range, or two edits with the same start with ValueError('overlap'); adjacency is legal. Validate the entire batch before changing text, selections or undo history. An empty batch changes nothing.
SP3. Rebase each selection endpoint independently: before an edit it is unchanged except preceding shifts; inside an edit or exactly at either boundary it moves to the end of that replacement. An insertion therefore attaches endpoints on its coordinate to the inserted text's end. At adjacent edit boundaries, the first edit in sorted order owns the endpoint. Preserve selection order and caller-owned lists.
SP4. Each successful nonempty apply is one undo step restoring both text and selections. undo returns True on restoration, False when empty; rejected and empty batches add no step.
SP5. CLI reads one JSON object with text, selections and edits from stdin. On success emit exactly one JSON line with text and selections (lists of pairs), exit 0, empty stderr. For invalid JSON, missing keys, wrong shapes or invalid patches: exit 2, empty stdout, stderr exactly 'invalid patch' plus newline. Include demo.json with a valid two-edit request and DEMO.md containing `python patching.py < demo.json`; executing it must agree with Document.

Use Python 3.11+ and only the standard library. Preserve the stated APIs.
Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
