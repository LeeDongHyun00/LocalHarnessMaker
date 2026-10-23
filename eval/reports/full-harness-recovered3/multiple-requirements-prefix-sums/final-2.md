Updated only `prefix`’s specification docstring, explicitly covering inclusive sums, length, order, empty input, negatives, and non-mutation.

Python’s AST confirms the docstring exists. All 5 tests pass.

The supplied regex still requires two signature colons and incorrectly rejects a normal Python function docstring; that check needs correction.