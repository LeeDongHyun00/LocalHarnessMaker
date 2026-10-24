{
  "naming": "strip().casefold().replace('_', '-')",
  "selection": "After complete structural validation, collapse identical canonical rows with an existing id idempotently; any different canonical row with that id raises ValueError(\"layered-settings: duplicate id\"). Keep the first occurrence position.",
  "domain_rules": "Each target is a setting name and value is its integer layer priority. For each target select the row with greatest value; ties choose smallest id. Return {\"settings\": {target: selected_id}} with targets inserted lexicographically. Negative layers are valid; do not assume zero is a default candidate.",
  "error_prefix": "layered-settings",
  "verification": {
    "command": [
      "python",
      "verify.py"
    ],
    "failed_tests": 0,
    "passed_tests": 10
  },
  "validation_order": "Validate every row structurally before duplicate selection or domain rules. validation.validate returns fresh canonical rows in encounter order, including duplicates.",
  "normalization_scope": "Apply the naming recipe to both id and target; preserve all other characters, including internal spaces, slash separators and Unicode.",
  "errors": {
    "container": "TypeError(\"layered-settings: rows must be a list\")",
    "row": "ValueError(\"layered-settings: invalid row\")",
    "duplicate": "ValueError(\"layered-settings: duplicate id\")"
  },
  "day_two": "run_many(batches) and render_many(batches) retain their signatures and NotImplementedError bodies. Implement batch composition and independence using the same engine.compute module attribute at call time; batch regression currently checks the deferred stubs.",
  "shared_path": "run and render each call engine.compute exactly once; render serializes with ensure_ascii=False, sort_keys=True, separators=(comma, colon), and one trailing newline."
}
