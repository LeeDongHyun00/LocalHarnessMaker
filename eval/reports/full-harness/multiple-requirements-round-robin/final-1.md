Repaired `round_robin` to interleave groups round by round, preserving values and order without mutating inputs. Added its public specification docstring and five regression tests in `test_solution.py`.

Verified successfully with `python -m py_compile solution.py` and `python -m unittest discover -v`. All five tests pass.