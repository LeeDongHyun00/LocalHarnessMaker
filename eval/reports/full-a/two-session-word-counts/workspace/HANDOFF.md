# Day 1 handoff

Implemented `words(text: str) -> dict[str, int]` in `solution.py` with standard-library-only Python compatible with Python 3.11+.

## Design decisions

- Use `str.split()` without a separator to split arbitrary whitespace, including Unicode whitespace, and ignore leading/trailing whitespace.
- Apply `str.casefold()` to each token before counting so Unicode case equivalents share a count.
- Preserve punctuation as part of each token; perform no additional normalization.
- Build a fresh dictionary on every call. The input string is unchanged and results share no mutable state.
- Empty and whitespace-only inputs naturally produce an empty dictionary.
- Keep type hints on the public function and test methods.

## Verification

Run from the task workspace with Python 3.11+:

```sh
python -m unittest discover -v
```

`test_solution.py` contains six regression tests covering repeated tokens, arbitrary whitespace, Unicode casefolding, punctuation, empty input, and independent results.

## Day 2 extension

Added `words_many(cases: list[tuple]) -> list` to the public API. Each tuple is unpacked as positional arguments to `words`, and results retain case order. Empty cases return `[]`. The first exception propagates as the same exception object and stops processing further cases. The wrapper does not mutate the cases list, tuples, or arguments. The day-1 `words` implementation and its six regression tests remain unchanged.

Added six batch test methods covering ordered results and unchanged inputs, empty batches, positional unpacking and mutable argument preservation, exception identity and stopping, invalid call errors, and independent result dictionaries.

Verification command run from the runner-provided workspace:

```sh
python -m unittest discover -v
```

Observed result: exit code 0; `Ran 12 tests in 0.002s`, followed by `OK`. All six day-1 tests and all six batch tests passed.
