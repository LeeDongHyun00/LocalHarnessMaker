# Day 2 handoff

Added `normalize_many(cases: list[tuple]) -> list` in `solution.py`.
Each tuple is unpacked as positional arguments to `normalize`, with results
returned in case order. An empty batch returns `[]`. Exceptions propagate
unchanged, and processing stops at the first exception. The wrapper does not
mutate the cases list, its tuples, or their arguments.

The day-1 `normalize(text: str) -> str` implementation and its seven regression
tests remain unchanged. Five new unittest methods cover batch ordering, empty
batches, positional unpacking, input preservation, exception identity and early
termination, and errors from invalid arguments.

## Day 2 verification evidence

Executed in the runner-provided workspace:

```sh
python -m unittest discover -v
```

Observed result (exit code 0):

```text
Ran 12 tests in 0.002s

OK
```

## Day 1 implementation notes

Implemented `normalize(text: str) -> str` in `solution.py` using Python 3.11+
and only the standard library.

## Design decisions

- Replace CRLF with LF first, then replace remaining CR with LF. This treats
  CRLF as one line break and each lone CR as one line break.
- Leave existing LF and every other character unchanged, including whitespace,
  Unicode separators, and trailing newlines. Do not strip or split lines.
- Keep the typed string API. String replacement does not mutate the input;
  there are no input collections to mutate.
- Public regression tests cover individual and mixed line endings, consecutive
  and trailing breaks, empty input, other characters, input preservation, and
  idempotence.

## Verification

Run from the supplied task workspace with Python 3.11+:

```sh
python -m unittest discover -v
```
