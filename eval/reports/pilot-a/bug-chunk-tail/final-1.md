Fixed `chunking.chunked` to include every item, including a final single-item chunk. The signature is unchanged, and the input list is not modified.

Verified empty inputs, exact and partial chunks, oversized chunks, order preservation, and input immutability.