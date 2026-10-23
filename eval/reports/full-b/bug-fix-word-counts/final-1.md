Fixed `words` to casefold and count whitespace-separated tokens while preserving punctuation, its signature, and type hints.

Added regression tests for Unicode casefolding, whitespace, punctuation, and empty input.

`python -m unittest discover -v`: **2 tests passed**.