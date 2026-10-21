# Verified case library

Store full schema-valid contracts as one JSON object per line in `*.jsonl`
files, including subdirectories. Only add contracts that passed verification;
retain their provenance outside prompt data. Schema validity alone does not
prove they passed. This reader does not collect, generate or write cases.
Do not populate this library from executor or paid-model output without the
terms-of-service review required by STOP-C3.

Retrieval uses BM25 (k1=1.5, b=0.75) over task summaries, constraints and
criterion descriptions, returning at most three positive-score matches.
Unicode word tokens are case folded; file order then line order breaks ties.
Duplicates are suppressed. Empty libraries and no matches yield no examples;
malformed records fail before any model call. The seed directory stays empty.
