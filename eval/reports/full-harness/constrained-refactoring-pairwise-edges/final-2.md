Both public functions delegate to `_adjacent_pairs`. Added a regression test explicitly verifying this, with signatures and behavior preserved.

Syntax compilation passed, and `python -m unittest discover -v` passed all 6 tests.