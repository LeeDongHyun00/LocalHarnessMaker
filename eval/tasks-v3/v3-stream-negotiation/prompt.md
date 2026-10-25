Implement the negotiated JSON request/response transport in negotiation.py. The
existing API is a sketch; replace its shortcuts. An offer has versions (integers)
and capabilities (strings). Use Python 3.11+ and the standard library.

SN1. negotiate(local, remote) returns {'version': V, 'capabilities': C}, choosing
only the greatest common version and a sorted, duplicate-free capability
intersection. Raise ValueError('version') if no version is common. Do not mutate
either offer. Capability names are case sensitive; unknown names in offers are
ignored. The only known names are 'trace' and 'mux'.
SN2. Codec(agreement).encode(body, extensions=None) emits one UTF-8 JSON object
with exactly version, body and extensions followed by LF, sorted keys, compact
separators, ensure_ascii=True. body is a JSON value. decode(packet) returns
(body, extensions). It requires an integer (not bool) equal to the agreed version and exactly those three
keys. Malformed JSON, missing/extra keys or a version mismatch raise
ValueError('packet'). Both methods reject extension keys outside the negotiated
capabilities with ValueError('extension'), even if the value is null. Absent
extensions means {}. An unknown extension must never be silently dropped.
SN3. Treat agreement and input mappings as snapshots: changing the original
offer, agreement or extension mapping later cannot change the codec's decisions
or a previously returned decoded value. Empty payloads and Unicode survive a
round trip. A decode accepts exactly one JSON object and exactly one final LF;
embedded newlines inside JSON strings must be escaped on the wire.

Keep negotiate and Codec with the signatures shown. Add regression tests as
needed. Run python -m unittest discover -s . -p 'test_*.py' -v in workspace/.
