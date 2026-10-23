Both functions now delegate to one private helper, preserving signatures, return types, error behavior, imports, and input immutability.

Added 5 public unittest methods. All pass with `python -m unittest discover -v` on Python 3.13.5.