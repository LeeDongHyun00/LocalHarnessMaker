# Command-stream regression corpus

`synthetic.jsonl` is a labeled offline seed, not exported real-run evidence.
Host export adds report-named JSONL files, discovered automatically by
`tests/eval/test_corpus_regression.py`.

Run from the repository root on the trusted host:

```sh
.venv/bin/python -m eval.runner.corpus_export \
  --private-root "$LHM_PRIVATE_GRADERS" \
  --private-marker "$LHM_PRIVATE_MARKER"
```

Supply every historical private-root alias and sentinel through repeated flags.
The tool does not open graders. It follows each report's checkpoint into executor
segments and native rollouts. Missing reports/runtimes fail the export; use
repeated `--report NAME` to explicitly export an available subset. No unavailable
run becomes an empty fixture. The defaults include the six requested full reports
and every pilot directory.

Each record holds the command sequence from one source stream, preserving code
stores and paired displays. Private-bearing physical JSONL lines are dropped;
known host locations become placeholders and output values are capped at 2000
characters. Unknown remaining locations become synthetic paths. Short structured
displays retain their envelopes; oversized ones become truncated strings.

Private directory basenames come from `LHM_PRIVATE_GRADERS`, optional
`LHM_PRIVATE_V3`, and supplied roots at runtime; no host directory name is
hard-coded. The generic `<private_root>` placeholder is always rejected.

Hashed marker guards let CI reject host-supplied sentinels and locations without
storing those values in fixtures.

`content_sha256` covers the canonical record excluding itself and `expected`.
`expected` records the current auditor's status, error kinds and match markers
for the **sanitized replay**, using synthetic framing and directory topology.
It does not reproduce original-run private fingerprints, filesystem aliases,
missing completion events or full outputs, and does not certify an original run.

To accept a reviewed parser change, re-run the same host export with
`--rebaseline RECORD_ID` for each affected record. Existing changed records are
refused without that flag; accepted additions/changes print sanitized before/after
records for review. Removal of a record requires manual review. Keep the export
output with the change review; never silently regenerate expected results in CI.
