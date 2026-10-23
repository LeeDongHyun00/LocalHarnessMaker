Repaired `words` to split on arbitrary whitespace, casefold and count tokens, retain punctuation, and preserve first-occurrence order. Added the public API docstring and five regression tests, retaining type hints and leaving input unchanged.

Verified: compilation succeeds and `python -m unittest discover -v` passes all five tests.