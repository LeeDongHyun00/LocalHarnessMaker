Fixed [solution.py](/var/folders/1s/swm_fg0j7dv02dm24jfkw8vc0000gn/T/lhm-eval-r2ob3y0u/workspace/solution.py) to remove exactly one matching prefix, with a public specification docstring and preserved type hints.

Added six regression tests covering edge cases and input/order preservation in [test_solution.py](/var/folders/1s/swm_fg0j7dv02dm24jfkw8vc0000gn/T/lhm-eval-r2ob3y0u/workspace/test_solution.py).

Verified: `python -m unittest discover -v` — all 6 tests pass.