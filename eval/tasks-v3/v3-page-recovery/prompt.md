Implement Store(path) in pages.py as a slotted snapshot store. append(text)
returns a never-reused integer slot, starting at zero; get(slot) returns text
or raises KeyError; delete(slot) removes a live slot or raises KeyError. commit()
persists the current state; constructing another Store reopens committed state.
Only strings are values. Use Python 3.11+ and the standard library.

PG1. Each committed page is exactly 512 bytes: magic b'SLOT', one unsigned
version byte, two big-endian unsigned payload-length bytes, four big-endian
CRC32 bytes of the payload, the UTF-8 payload, then zero padding. The payload
is JSON {'next': next_slot, 'slots': {'decimal_slot': text, ...}}, serialized
with sorted keys, compact separators and ensure_ascii=True. A page with payload
longer than 501 bytes raises ValueError('capacity') before changing the file.
The log is a concatenation of full snapshot pages; the last valid full page wins.
PG2. Reopen reads versions 1 and 2; all new pages use version 2. A full page
with bad magic, CRC, payload length or unsupported version raises
ValueError('page'), even if later pages are valid. A trailing fragment shorter
than a page is a torn write: ignore it on reopen. Opening never changes bytes;
the next commit removes only the torn suffix before appending its full page.
Empty files represent an empty store. No implicit commit on append/delete.
PG3. Reopening preserves slot identities and the next-slot watermark. Deletion
never allows reuse, including after deleting every slot. Missing get/delete does
not change the store. Values must be independent of later instances. Keep all
signatures above; the supplied encode_page(state, version=2) helper may be used
for fixtures. No external dependencies. Add tests as needed and run
python -m unittest discover -s . -p 'test_*.py' -v in workspace/.
