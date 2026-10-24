{
  "naming": "strip().casefold().replace('_', '-')",
  "selection": "After complete structural validation, collapse identical canonical rows with an existing id idempotently; any different canonical row with that id raises ValueError(\"event-replay: duplicate id\"). Keep the first occurrence position.",
  "domain_rules": "Replay selected rows in encounter order; target is a stream, value a signed delta and each stream starts at zero. Any negative intermediate balance raises ValueError(\"event-replay: negative prefix\"), even if later rows repair it. Return {\"balances\": {target: final_balance}, \"history\": [balance_after_each_row]} with balances inserted in sorted target order, retaining zeros.",
  "error_prefix": "event-replay",
  "verification": {
    "command": [
      "python",
      "verify.py"
    ],
    "failed_tests": 0,
    "passed_tests": 7
  },
  "day_2": "run_many(batches) and render_many(batches) retain their original typed signatures and NotImplementedError bodies. Replace the day-1 stub regression with batch behavior coverage when implementing them. Use the same engine.compute module attribute at call time for each single-input computation.",
  "ordering": "Validate every row structurally before duplicate selection; finish duplicate selection before replaying domain rules. Validation returns fresh canonical rows in encounter order, including duplicates. Preserve history order and sort balance dictionary targets.",
  "shared_path": "project.run and project.render each call engine.compute exactly once through the engine module attribute; render serializes the computed result using ensure_ascii=False, sort_keys=True, separators=(comma, colon), followed by exactly one newline."
}
