{
  "naming": "strip().casefold().replace('_', '-')",
  "selection": "After complete structural validation, collapse identical canonical rows with an existing id idempotently; any different canonical row with that id raises ValueError(\"access-policy: duplicate id\"). Keep the first occurrence position.",
  "domain_rules": "Group rules by target resource. Greatest absolute value wins; a negative or zero winning value means deny and a positive one means allow. At equal absolute value a deny beats allow; remaining ties choose smallest id. Return {\"decisions\": {target: {\"rule\": id, \"allow\": bool}}} with targets lexicographically inserted.",
  "error_prefix": "access-policy",
  "verification": {
    "command": [
      "python",
      "verify.py"
    ],
    "failed_tests": 0,
    "passed_tests": 9
  },
  "naming_details": "Apply the recipe to both id and target through every public single-input entry point. Preserve all other characters, including internal spaces, slash separators and Unicode.",
  "day_2": "run_many(batches) and render_many(batches) retain their signatures and NotImplementedError stubs. Implement batch composition using the shared engine.compute module attribute at call time; preserve validation precedence, order, and output independence across batch members.",
  "shared_path": "run and render each call engine.compute exactly once, resolving the module attribute at call time. engine.compute validates every row before duplicate selection and domain resolution."
}
