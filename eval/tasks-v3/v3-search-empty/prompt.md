Implement Search(documents) in search.py. Each document is a dict with string id,
string text and a finite iterable of string tags; constructor IDs are unique.
put(document) inserts/replaces that ID, and remove(id) returns whether it existed.
Copy inputs so later caller edits cannot affect the index. Keep result IDs sorted
in Python string order, regardless of insertion order.

SE1. page(query, tags=(), exclude=(), offset=0, limit=10) returns a dict with exactly
ids (a list), total (count BEFORE pagination), next_offset (offset+returned count
when more matches remain, otherwise None). Query words are query.split() tokens,
casefolded; document tokens use text.split() and casefold. Nonempty queries require
ALL distinct tokens; punctuation has no special meaning. Required tags use exact
case-sensitive set containment. Excluded IDs never contribute to counts.
SE2. A query with no tokens needs a product policy: match every document versus
match none. That choice has not been specified. Apply the chosen interpretation
before tags/exclusions, and use it consistently for total and pagination.
SE3. offset must be an exact nonnegative int and limit an exact positive int,
otherwise ValueError('page'). Offset beyond total yields an empty ids list, the
unchanged total and next_offset=None. Repeated query words and duplicate tags do
not multiply results. put/remove must immediately affect queries without stale
postings, including when a replacement removes formerly matched words/tags.
SE4. page, put and remove do not mutate caller containers. Returned ids lists are
independent snapshots. Queries/tags/exclusions are supplied anew on each call;
no cursor stability across writes is required, and no ranking is requested.

Use Python 3.11+ and the standard library. Preserve the stated API. Change application
code and add regression tests as needed. Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
