Day 1: implement strip_prefix, add unittest regression coverage, and record design decisions plus a verification command in HANDOFF.md for the next session.

Work only in the supplied task workspace. Edit solution.py and public tests; use Python 3.11+ and the standard library. Do not access parent repositories or external services.

Public behavior:
Remove exactly one matching prefix. A nonmatching or empty prefix leaves text unchanged. Do not strip individual characters or repeated prefixes.

Maintain type hints. Do not mutate input collections. No algorithmic complexity constraint is imposed. Verify with python -m unittest discover -v.
