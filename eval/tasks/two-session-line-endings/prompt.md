Day 1: implement normalize, add unittest regression coverage, and record design decisions plus a verification command in HANDOFF.md for the next session.

Work only in the supplied task workspace. Edit solution.py and public tests; use Python 3.11+ and the standard library. Do not access parent repositories or external services.

Public behavior:
Replace CRLF and lone CR with LF. Preserve existing LF, all other characters, and the number of line breaks. Do not strip trailing newlines.

Maintain type hints. Do not mutate input collections. No algorithmic complexity constraint is imposed. Verify with python -m unittest discover -v.
