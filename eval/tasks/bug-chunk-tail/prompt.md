Fix `chunking.chunked` so it partitions a list into consecutive chunks of the
requested positive size, preserving every item and its order. The final chunk
may be shorter than the requested size. An empty input produces an empty list.
Preserve the existing function signature and do not modify the input list.
