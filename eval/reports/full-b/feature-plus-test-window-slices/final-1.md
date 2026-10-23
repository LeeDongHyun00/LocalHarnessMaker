Implemented `windows` with positive-size validation and no input mutation.

Added 5 unittest methods covering ordinary, boundary, empty, invalid-size, and input-preservation cases.

Verified with `python -m unittest discover -v`: all 5 tests passed.