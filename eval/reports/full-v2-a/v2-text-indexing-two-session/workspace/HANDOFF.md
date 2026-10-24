{
  "naming": "strip().casefold().replace('_', '-')",
  "selection": "After complete structural validation, collapse identical canonical rows with an existing id idempotently; any different canonical row with that id raises ValueError(\"text-indexing: duplicate id\"). Keep the first occurrence position.",
  "domain_rules": "Target is a token and value its occurrence count. Reject any negative count with ValueError(\"text-indexing: negative count\"). Return {\"index\": {token: {\"count\": total, \"documents\": [ids]}}}. Token names are sorted; document ids retain selected-row encounter order even for zero counts. Counts sum all selected rows.",
  "error_prefix": "text-indexing",
  "verification": {
    "command": [
      "python",
      "verify.py"
    ],
    "failed_tests": 0,
    "passed_tests": 9
  },
  "naming_scope": "Normalize both id and target. Preserve all other characters, including internal spaces, slash separators and Unicode.",
  "ordering": "Complete structural validation precedes duplicate selection; duplicate conflicts precede negative-count checks. validation.validate returns fresh canonical rows in encounter order without selection or domain checks.",
  "shared_path": "run and render each resolve engine.compute at call time and invoke it exactly once. Batch extensions must use this same path.",
  "day_2": "run_many(batches) and render_many(batches) retain their signatures and NotImplementedError stubs. Implement batch composition tomorrow and replace the regression that explicitly checks deferred bodies with batch behavior coverage."
}
