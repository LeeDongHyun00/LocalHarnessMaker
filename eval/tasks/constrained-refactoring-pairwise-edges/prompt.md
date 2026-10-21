Refactor pairs and pairs_legacy to delegate their shared algorithm to one private helper. Preserve both signatures, return types, error behavior and input immutability. Keep imports and public names compatible.

Work only in the supplied task workspace. Edit solution.py and public tests; use Python 3.11+ and the standard library. Do not access parent repositories or external services.

Public behavior:
Return overlapping adjacent pairs in input order. Inputs with fewer than two items return []. Example [1,2,3] gives [(1,2),(2,3)].

Maintain type hints. Do not mutate input collections. No algorithmic complexity constraint is imposed. Verify with python -m unittest discover -v.
