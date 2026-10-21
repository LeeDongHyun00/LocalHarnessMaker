Fix the incorrect behavior of permutations without changing its signature. Add a small regression test in test_solution.py.

Work only in the supplied task workspace. Edit solution.py and public tests; use Python 3.11+ and the standard library. Do not access parent repositories or external services.

Public behavior:
Return all distinct permutations of characters in sorted lexicographic order. The empty string has one permutation: the empty string. Inputs are at most seven characters.

Maintain type hints. Do not mutate input collections. No algorithmic complexity constraint is imposed. Verify with python -m unittest discover -v.
