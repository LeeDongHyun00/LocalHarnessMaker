Repair Reader in records.py: quoted CRLF text currently changes row boundaries.
Reader(text).read() returns Record(fields: list[str], start: int, end: int) or None.
Offsets are zero-based Python string indices, not encoded byte offsets.

CSV1. Comma separates fields; LF or CRLF terminates a record only outside quotes.
A field may start with a double quote; doubled quotes inside it decode to one quote.
All characters inside quotes, including CR and LF, are retained verbatim. Bare CR
outside quotes is ordinary field data. A trailing comma creates an empty last field.
CSV2. Record.start is the first character of the record; Record.end is the exclusive
end before its terminator. EOF closes an unquoted or closed-quote record; empty input
and the position just after a final terminator produce None, not an extra record.
An empty physical line is one empty field. Repeated read() after EOF returns None.
CSV3. A quote inside a nonempty unquoted field, or a nonseparator character after
a closing quote, raises ParseError with offset at that offending character. An
unterminated quoted field raises ParseError at len(text). Its message is 'csv'.
For a non-EOF error, consume through the next physical LF (including an optional
preceding CR) before raising; the next read starts after it. EOF error exhausts
input. Prior returned records remain unchanged. Do not normalize input newlines. Other characters, including NUL and tab, are ordinary data.
CSV4. Across reading the whole input, inspect individual characters via indexing at
most 4 * len(text) + 10 times. Substring search/slicing is allowed; do not repeatedly
rescan a record prefix. This deterministic budget replaces a timing requirement.

Use Python 3.11+ and the standard library. Preserve the documented public API.
Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
Change application code and add regression tests as needed.
