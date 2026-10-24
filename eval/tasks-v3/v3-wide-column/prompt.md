The final separator in a terminal table drifts when text contains combining
characters. Repair columns.py's display_width(text), wrap(text, width) and
render(rows, widths). Inputs are Unicode strings without tabs/control characters
other than LF, and each row has exactly as many strings as widths.

WD1. A combining code point (unicodedata.combining != 0) occupies zero columns;
East Asian W or F occupies two; everything else occupies one. display_width returns
the sum, including zero for empty input. LF is a structural break only in wrap.
WD2. wrap returns a list of strings. Preserve every character and each explicit LF
as a new output line (LF itself is omitted), including empty and trailing lines.
Greedily fit characters by display width, never detach combining marks from the
preceding character at a soft wrap; leading combining marks stay on the first line.
A glyph wider than width raises ValueError('glyph'); width < 1 raises ValueError('width').
WD3. render wraps each cell, pads missing continuation lines with empty strings,
right-pads each fragment to its column's display width, joins columns with ' | ',
and joins output lines with LF and no final LF. No trimming, truncation or headers.
No rows, or any number of zero-column rows, produce ''. Do not mutate rows or widths. Reject row arity mismatch
with ValueError('arity') and any width < 1 with ValueError('width').

Use Python 3.11+ and the standard library. Preserve the documented public API.
Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
Change application code and add regression tests as needed.
