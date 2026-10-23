Refactored `words` and `words_legacy` to delegate to one private `_count_words` helper, preserving signatures, type hints, return types, and error behavior.

Added five public tests covering token counting, empty input, immutability, errors, and API compatibility.

Compilation passed, and `python -m unittest discover -v` passed all five tests.