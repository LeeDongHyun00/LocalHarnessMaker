Implemented `select` with type hints, preserving row and column order, omitting missing keys, deduplicating columns, and returning fresh dictionaries without mutating inputs.

Added five unittest methods covering ordinary, boundary, and empty inputs. Compilation and `python -m unittest discover -v` both passed.