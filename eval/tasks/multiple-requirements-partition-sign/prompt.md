Repair partition. Also add its public specification as a docstring, add regression tests in test_solution.py, and preserve input values and collection order as specified.

Work only in the supplied task workspace. Edit solution.py and public tests; use Python 3.11+ and the standard library. Do not access parent repositories or external services.

Public behavior:
Return negatives, zeros, positives as three lists in that order. Preserve relative order and duplicates in each partition.

Maintain type hints. Do not mutate input collections. No algorithmic complexity constraint is imposed. Verify with python -m unittest discover -v.
