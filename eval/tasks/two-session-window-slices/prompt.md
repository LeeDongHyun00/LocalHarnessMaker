Day 1: implement windows, add unittest regression coverage, and record design decisions plus a verification command in HANDOFF.md for the next session.

Work only in the supplied task workspace. Edit solution.py and public tests; use Python 3.11+ and the standard library. Do not access parent repositories or external services.

Public behavior:
Return all contiguous windows of exactly size, advancing by one. Raise ValueError for size <= 0. A size exceeding length returns [].

Maintain type hints. Do not mutate input collections. No algorithmic complexity constraint is imposed. Verify with python -m unittest discover -v.
