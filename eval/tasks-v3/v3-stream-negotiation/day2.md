Extend negotiation.py with Mux(codec). Preserve the existing codec and negotiation
contracts. The workspace from the preceding session is available for inspection.

SN4. Mux.send(channel, body) returns a codec packet with a mux extension
{'channel': channel, 'sequence': N}; channel is a nonempty string and N is a
per-channel counter beginning at zero. Mux.receive(packet) returns (channel,
body); it accepts only the next expected sequence for that channel. Outgoing and
incoming counters are independent. Require the extension's exact two keys,
nonempty string channel and integer (not bool) sequence. Missing/malformed mux,
out-of-order sequence or bad channel raises ValueError('mux'). Do not advance any
counter on rejection. The codec's capability and version rules still apply.
SN5. Interleave at least two channels and resume after rejected packets without
renumbering either stream. A codec without the relevant negotiated capability
must reject send/receive as ValueError('extension'); no fallback framing. Keep
all prior policies, including wire representation and unknown-extension handling.
Run the existing test command and add regression tests as needed.
