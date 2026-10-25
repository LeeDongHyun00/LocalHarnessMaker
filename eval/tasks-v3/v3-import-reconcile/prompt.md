Finish Importer in reconcile.py for reconciling external rows. A row is exactly
{'id': nonempty string, 'updated': integer (not bool), 'source': nonempty string,
'fields': dict of string keys to string values}. Invalid rows must not partially
change state. rank is a supplied list of source names, highest priority first;
unknown nonempty sources are valid but rank after all known sources.
Use Python 3.11+ and the standard library.

IR1. Importer(rank).ingest(rows) returns one status per row: 'inserted',
'replaced', 'ignored', or 'rejected'. Conflicts use the greater updated value,
then the earlier source in rank. Equal updated/rank keeps the EXISTING row,
including ties between two unknown sources. A winning row replaces the entire
fields mapping; never field-merge. Rejected rows do not affect later rows.
IR2. snapshot() returns rows sorted lexicographically by id, with all four keys.
Inputs, rank and returned snapshots must not alias internal state. Empty fields
is valid. Reject unexpected/missing keys, bool timestamps, empty id/source and
nonstring field entries as 'rejected' without throwing. ingest accepts any
iterable of rows and processes in order, validating before conflict resolution.
IR3. save(path) writes canonical UTF-8 JSON {'rank':rank,'rows':snapshot}, with
sorted keys, compact separators and ensure_ascii=True, no terminal newline.
Importer.load(path) restores exactly that state and policy. Persist only when
explicitly saved; no network or global state. Keep these APIs; add tests and run
python -m unittest discover -s . -p 'test_*.py' -v in workspace/.
