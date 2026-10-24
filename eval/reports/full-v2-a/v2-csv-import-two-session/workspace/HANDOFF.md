{
  "naming": "strip().casefold().replace('_', '-')",
  "selection": "After complete structural validation, collapse identical canonical rows with an existing id idempotently; any different canonical row with that id raises ValueError(\"csv-import: duplicate id\"). Keep the first occurrence position.",
  "domain_rules": "Each target is a column and each selected row contributes an integer cell. Return {\"columns\": [sorted target names], \"data\": [[cells for column],...], \"ids\": [[ids for column],...]}. Each inner list retains selected-row encounter order for that column. Do not pad unequal columns and retain zero/negative cells.",
  "error_prefix": "csv-import",
  "verification": {
    "command": [
      "python",
      "verify.py"
    ],
    "failed_tests": 0,
    "passed_tests": 10
  },
  "day_2": "run_many(batches) and render_many(batches) retain their original typed signatures and raise NotImplementedError(\"Implement batch composition\"). Batch composition and independence between batch members remain deferred. Route future extensions through engine.compute resolved on the module at call time.",
  "architecture": "validation.validate returns fresh canonical rows in encounter order and completes all structural validation before engine.compute selects duplicates. project.run and project.render each invoke engine.compute exactly once. domain.resolve sorts columns and preserves encounter order within each column. Result dictionary insertion order is columns, data, ids. render serializes with ensure_ascii=False, sort_keys=True, separators=(comma, colon), and one trailing newline.",
  "protected_files": "SHA-256 checks confirmed project/compat.py, test_public.py, verify.py and README.md remain byte for byte unchanged."
}
