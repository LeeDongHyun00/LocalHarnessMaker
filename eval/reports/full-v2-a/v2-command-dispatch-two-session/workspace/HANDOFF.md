{
  "naming": "strip().casefold().replace('_', '-')",
  "selection": "After complete structural validation, collapse identical canonical rows with an existing id idempotently; any different canonical row with that id raises ValueError(\"command-dispatch: duplicate id\"). Keep the first occurrence position.",
  "domain_rules": "Target is a command name, value a signed handler priority. For each command choose the highest priority; ties choose lexicographically greatest id (unlike settings). Return {\"dispatch\": {command: id}, \"shadowed\": [all_unselected_ids]}. Command keys and shadowed ids are lexicographically sorted. A shadowed handler remains a valid input, even at negative priority.",
  "error_prefix": "command-dispatch",
  "verification": {
    "command": [
      "python",
      "verify.py"
    ],
    "failed_tests": 0,
    "passed_tests": 9
  },
  "validation_order": "Validate every row structurally before duplicate selection and domain resolution. validation.validate returns fresh canonical rows in encounter order, retaining duplicates and applying no domain checks. Invalid later rows outrank earlier duplicate errors.",
  "text_scope": "Apply naming to both id and target; preserve all other characters, including internal spaces, slash separators and Unicode.",
  "shared_path": "project.run and project.render each resolve engine.compute at call time and invoke it exactly once. compute validates, selects duplicate ids, then calls domain.resolve. Batch extensions must use this same path.",
  "errors": {
    "rows_type": "command-dispatch: rows must be a list",
    "invalid_row": "command-dispatch: invalid row",
    "duplicate_id": "command-dispatch: duplicate id"
  },
  "deferred": "run_many(batches) and render_many(batches) retain signatures and NotImplementedError bodies for day 2. Regression coverage currently asserts these deferred stubs; replace that expectation when implementing batch behavior.",
  "ordering_and_freshness": "Domain dictionary insertion order is dispatch then shadowed. Dispatch command keys and shadowed ids are sorted. Every output container is fresh. No integer magnitude bound applies."
}
