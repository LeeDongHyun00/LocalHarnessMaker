Implemented `flatten` with preserved type hints, order, and a new result list without mutating inputs.

Added four unittest methods covering ordinary, empty, single-element, and shared-inner-list inputs.

Verified: `python -m unittest discover -v` — all 4 tests pass.