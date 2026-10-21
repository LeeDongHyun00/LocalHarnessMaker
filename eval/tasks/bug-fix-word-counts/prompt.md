Fix the incorrect behavior of words without changing its signature. Add a small regression test in test_solution.py.

Work only in the supplied task workspace. Edit solution.py and public tests; use Python 3.11+ and the standard library. Do not access parent repositories or external services.

Public behavior:
Split on arbitrary whitespace, casefold each token, and count it. Punctuation remains part of the token. Empty or whitespace-only text returns {}.

Maintain type hints. Do not mutate input collections. No algorithmic complexity constraint is imposed. Verify with python -m unittest discover -v.
