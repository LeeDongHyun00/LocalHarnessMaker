Repair parse_pairs. Also add its public specification as a docstring, add regression tests in test_solution.py, and preserve input values and collection order as specified.

Work only in the supplied task workspace. Edit solution.py and public tests; use Python 3.11+ and the standard library. Do not access parent repositories or external services.

Public behavior:
Parse nonempty newline-separated key=value records, splitting on the first equals sign and stripping both sides. Ignore blank lines; last repeated key wins. Raise ValueError on missing equals or empty key. Empty values are allowed.

Maintain type hints. Do not mutate input collections. No algorithmic complexity constraint is imposed. Verify with python -m unittest discover -v.

Submission requirements: test_solution.py must contain at least 3 passing unittest test methods exercising the public API. Retain all behavior and compatibility requirements above.
