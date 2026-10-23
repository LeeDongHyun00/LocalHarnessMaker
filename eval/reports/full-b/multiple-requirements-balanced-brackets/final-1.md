Repaired `balanced` to check all three bracket types and nesting order, ignore other characters, and preserve inputs. Added its public specification docstring and six regression tests in `test_solution.py`.

Verified with `python -m unittest discover -v`: all 6 tests pass.