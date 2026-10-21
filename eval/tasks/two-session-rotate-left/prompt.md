Day 1: implement rotate, add unittest regression coverage, and record design decisions plus a verification command in HANDOFF.md for the next session.

Work only in the supplied task workspace. Edit solution.py and public tests; use Python 3.11+ and the standard library. Do not access parent repositories or external services.

Public behavior:
Rotate left by steps modulo length. Negative steps rotate right. Empty input returns []. Example: [1,2,3], 4 gives [2,3,1].

Maintain type hints. Do not mutate input collections. No algorithmic complexity constraint is imposed. Verify with python -m unittest discover -v.
