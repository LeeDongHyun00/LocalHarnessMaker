# Retained FILE-manifest inputs

The supplied excerpt contains two JavaScript records, both from one rate
budgets task. It contains neither an earlier `original_sources` store nor a
third record. Surrounding host task/session metadata is omitted. JavaScript is
preserved with one final newline; no absolute host paths occur in these inputs.
The tests supply synthetic manifests, identities, paths and paired outputs.

| Fixture | Original native line | Characters excluding final newline | Classification |
| --- | --- | --- | --- |
| derived-record-1.js | 65 | 1484 | derived_from_audited_outputs with a confirmed earlier store; otherwise unresolved |
| derived-record-2.js | 75 | 1718 | derived_from_audited_outputs with a confirmed earlier store; otherwise unresolved |

The regression test pins the complete fixture bytes with SHA-256:

- derived-record-1.js: a804a466d4840c4995cb21d8372b92984817db5a617c1aa5a1e3e7cfe0377e7f
- derived-record-2.js: 6b6d08cbd92cc81394f0eee8c6c33182df81dbbae89c03e44178767245beba15

`test_derived_inputs.py` supplies the private-output and unknown-source variants,
using only temporary synthetic private roots. It also tests same-script stores,
paired raw tool results, concatenated private paths, missing/altered displays,
overwritten keys and unsupported operations. A clean synthetic session is not
a claim about the unavailable complete baseline-B sessions.
