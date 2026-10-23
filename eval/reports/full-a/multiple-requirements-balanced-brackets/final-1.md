Repaired `balanced` to validate nesting of `()`, `[]`, and `{}`, ignore other characters, and accept empty text.

Added the public specification docstring and five regression tests, including input preservation and collection order.

Verified with `python -m unittest discover -v`: all 5 tests pass.