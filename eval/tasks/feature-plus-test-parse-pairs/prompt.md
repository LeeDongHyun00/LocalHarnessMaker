Implement parse_pairs and add standard-library unittest tests in test_solution.py covering ordinary, boundary and empty inputs (or invalid numeric inputs when no collection is accepted).

Work only in the supplied task workspace. Edit solution.py and public tests; use Python 3.11+ and the standard library. Do not access parent repositories or external services.

Public behavior:
Parse nonempty newline-separated key=value records, splitting on the first equals sign and stripping both sides. Ignore blank lines; last repeated key wins. Raise ValueError on missing equals or empty key. Empty values are allowed.

Maintain type hints. Do not mutate input collections. No algorithmic complexity constraint is imposed. Verify with python -m unittest discover -v.
