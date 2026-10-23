Fixed `strip_prefix` using `str.removeprefix`, preserving its signature and type hints.

Added a regression test covering repeated prefixes, character stripping, nonmatching and empty prefixes, and empty text.

`python -m unittest discover -v` passes.