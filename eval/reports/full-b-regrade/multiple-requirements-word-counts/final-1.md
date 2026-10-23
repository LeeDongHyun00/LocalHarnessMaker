Repaired `words`, added its public specification as a docstring, and added six regression tests covering casefolding, whitespace, punctuation, empty input, input preservation, and collection order.

Verified with `python -m unittest discover -v`: all 6 tests passed.