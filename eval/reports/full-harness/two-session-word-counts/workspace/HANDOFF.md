# Day 2 handoff

Implemented the existing public API `words(text: str) -> dict[str, int]`.

Design decisions:
- Use `str.split()` without a separator to handle arbitrary whitespace and discard empty tokens.
- Apply `str.casefold()` to every token before counting, including Unicode case folding.
- Preserve punctuation as part of each token; no stripping or other normalization is applied.
- Build a fresh dictionary on each call. Input is unchanged, and empty or whitespace-only input returns `{}`.
- Use Python 3.11+ and the standard library only.

Public regression coverage includes repeated words, whitespace, Unicode case folding,
punctuation, empty input, and independent results.

Verification commands (run from the task workspace):

```sh
python -m py_compile solution.py
python -m unittest discover -v
```

Day 2 adds `words_many(cases: list[tuple]) -> list`, which calls
`words(*case)` sequentially and returns results in case order. Empty input
returns `[]`. Exceptions propagate unchanged and stop further calls. The wrapper
does not modify cases or their arguments. The Day 1 `words` API is unchanged.

Added four batch tests covering ordering, empty input, unchanged inputs,
positional argument forwarding, and propagation of the same exception object
without processing subsequent cases. All six Day 1 tests remain in place.

Day 2 verification observed in the runner workspace:
- `python -m py_compile solution.py` exited with code 0 (no output).
- `python -m unittest discover -v` exited with code 0: ran 10 tests in
  0.002s; result `OK` (all 10 passed).
