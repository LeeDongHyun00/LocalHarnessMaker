Fixed `strip_prefix` to remove exactly one literal prefix using `str.removeprefix`, preserving type hints. Added its public specification as a docstring and five regression tests covering edge cases, input preservation, and collection order.

Verified with `python -m unittest discover -v`: all 5 tests pass.