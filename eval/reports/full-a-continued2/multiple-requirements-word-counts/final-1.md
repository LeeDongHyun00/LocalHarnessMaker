Repaired `words` to count casefolded whitespace-separated tokens while preserving punctuation, input text, and first-occurrence order. Added the public specification docstring and five regression tests in `test_solution.py`.

Verified with `python -m unittest discover -v`: all 5 tests pass.