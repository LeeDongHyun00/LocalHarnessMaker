Repaired `balanced` to validate nesting of `()`, `[]`, and `{}`, ignore other characters, and handle empty text correctly.

Added the public specification docstring and five regression tests, including input value and order preservation.

Verification passed: compilation and `python -m unittest discover -v` (5 tests).