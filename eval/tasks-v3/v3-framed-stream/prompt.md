Repair the incremental message decoder in framing.py. A consumer reports that
splitting a network read changes which messages arrive; subsequent valid frames
can disappear after a malformed one. Keep Decoder(on_frame, on_error), feed(bytes)
and finish(). Callbacks receive bytes and an error string respectively.

FR1. The terminator is the exact byte sequence CR LF dot CR LF. Remove it from each
payload. Deliver every frame, including empty frames, once and in order, regardless
of feed partitioning. Bytes after one terminator belong to the next frame.
FR2. A payload containing NUL is malformed: call on_error('nul') once instead of
on_frame, then continue at the next frame. Other payload bytes are unrestricted.
FR3. feed(b'') is harmless. finish() returns None for an empty pending buffer and
raises ValueError('truncated') otherwise, preserving pending bytes so a later feed
can complete them. Never invent a frame at EOF.
FR4. Retire a completed frame before calling either callback. Propagate callback
exceptions; a later feed resumes with the remaining frames, without redelivery.

Use Python 3.11+ and the standard library. Preserve the documented public API.
Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
Change application code and add regression tests as needed.
