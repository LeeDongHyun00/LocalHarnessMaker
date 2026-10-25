Refactor scanner.py from repeated suffix slicing to a lazy token iterator.
The existing Token type is the API contract; preserve token_api.py byte-for-byte.
TS1. Keep scan(text: str) -> list[Token], and expose iter_tokens(text) as an iterator yielding the same ordered Token(kind, value, start, end) values. Offsets are zero-based Unicode code-point indexes with exclusive ends. Whitespace uses str.isspace and is skipped; words start with ASCII letter or underscore and continue with ASCII alphanumeric or underscore; numbers are runs of ASCII decimal digits; every other non-quote character is one punct token.
TS2. Double-quoted strings form a string token whose span includes both quotes. A backslash removes itself and quotes the next character, including a newline or backslash. Other characters are literal. A missing closing quote or dangling escape raises ValueError('unterminated at N'), where N is the opening quote offset. No partial string token is emitted.
TS3. iter_tokens is lazy: constructing it reads no characters and requesting one token does not scan subsequent tokens. scan consumes iter_tokens. Across a full scan, the sum of characters read by indexing and copied by slicing the original input must be at most 16*len(text)+16; do not copy successive remaining suffixes or coerce the whole input to a new string to bypass this bound. str subclasses may instrument these operations.
TS4. Preserve token_api.py bytes and the scan parameter name/signature. Do not mutate the input. Token traces must be partitioned solely by this grammar, including empty input, adjacent tokens and non-ASCII punctuation.

Use Python 3.11+ and the standard library. Add regression tests as needed.
Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
