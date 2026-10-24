{
  "naming": "strip().casefold().replace('_', '-')",
  "selection": "After complete structural validation, collapse identical canonical rows with an existing id idempotently; any different canonical row with that id raises ValueError(\"filesystem-manifests: duplicate id\"). Keep the first occurrence position.",
  "domain_rules": "Id is a canonical relative file name (slash separators); reject absolute paths, empty slash segments, dot or dot-dot segments with ValueError(\"filesystem-manifests: invalid path\"). Then reject negative sizes with ValueError(\"filesystem-manifests: negative size\"). Target is a digest label, value a byte size. Return {\"files\": {id: {\"digest\": target, \"size\": value}}, \"bytes\": total} with file keys sorted lexicographically. Backslashes are literal filename characters, not separators.",
  "error_prefix": "filesystem-manifests",
  "verification": {
    "command": [
      "python",
      "verify.py"
    ],
    "failed_tests": 0,
    "passed_tests": 9
  },
  "normalization_scope": "Apply the naming recipe to both id and target. Preserve internal spaces, slash separators, Unicode and all other characters except the transformations in that recipe.",
  "ordering": "Validate all rows structurally first, select duplicate ids second, validate every selected path third, and check negative sizes fourth. Invalid paths anywhere outrank negative sizes. Validation retains encounter order; selection retains the first occurrence position. Domain files are inserted lexicographically, with digest before size; the result inserts files before bytes. Rendering recursively sorts object keys.",
  "shared_path": "project.api.run and project.api.render each resolve engine.compute at call time and invoke it exactly once. Keep this same domain-policy path for day-2 extensions.",
  "day_two": "run_many(batches) and render_many(batches) retain existing signatures and type hints but still raise NotImplementedError. Their regression currently checks those stubs and unchanged inputs; replace it with batch behavior coverage when implementing composition. Batch behavior, including independence between batch members, is deferred."
}
