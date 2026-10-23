Fixed `permutations` in [solution.py](/var/folders/1s/swm_fg0j7dv02dm24jfkw8vc0000gn/T/lhm-eval-2rcp7d8w/workspace/solution.py) to return all distinct permutations in lexicographic order, preserving its signature and type hints.

Added two regression tests covering duplicates, ordering, and empty input.

Verified: `python -m unittest discover -v` — both tests pass.