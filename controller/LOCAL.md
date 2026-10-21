# Local constrained-decoding adapter

The stage-two adapter targets an already-running llama.cpp or vLLM server
with an OpenAI-compatible chat-completions endpoint. It sends strict
`response_format.json_schema` output constraints and validates returned JSON
locally. It does not install software, download weights, start services, or
fall back to cloud. The exact server build, Gemma 4 12B model artifact/alias,
and that build's schema support must be verified on the host before enabling.
No serving invocation has been verified in this network-disabled session.

In controller/config.yaml, set local.enabled only after that verification.
Configure model to match the server's reported model identity, endpoint to a
loopback chat-completions URL, and timeout_seconds/max_output_tokens to bounded
limits. No credentials or CLI login are used by this adapter. Requests,
responses, model mismatch, unavailable service and regeneration limits have
mock-only coverage. Unsupported constrained output is an explicit error.

No hardware capacity has been measured. Pure weight storage for 12 billion
parameters is approximately 24 GB at 16 bits or 6 GB at 4 bits (decimal GB);
these arithmetic lower bounds exclude quantization metadata, KV cache,
activations, runtime buffers and operating-system memory. They are not serving
memory requirements. Measure actual peak memory and latency for the selected
server, quantization and context before claiming D-3 or the 30-second target.
If capacity is insufficient, STOP-C4 requires reporting a quantization proposal
and expected quality impact before proceeding.

There is no approved API-equivalent local price snapshot in prices.yaml.
Missing prices and missing usage remain null. Judge and handoff support this;
contract.schema.json requires numerical cost metadata, so contract generation
fails explicitly until reliable usage and a configured versioned price snapshot
are available. Never label local inference free or substitute fabricated zero.
