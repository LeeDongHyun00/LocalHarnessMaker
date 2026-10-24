{
  "naming": "strip().casefold().replace('_', '-')",
  "selection": "After complete structural validation, collapse identical canonical rows with an existing id idempotently; any different canonical row with that id raises ValueError(\"schema-migration: duplicate id\"). Keep the first occurrence position.",
  "domain_rules": "Id names a migration, target its predecessor; a self target is a root. Value is a positive version. Reject nonpositive versions first with ValueError(\"schema-migration: invalid version\"), then absent predecessors with ValueError(\"schema-migration: missing predecessor\"), then any non-root edge whose predecessor version is not strictly smaller with ValueError(\"schema-migration: version order\"). Return {\"migrations\": [ids]} ordered by increasing version then id.",
  "error_prefix": "schema-migration",
  "verification": {
    "command": [
      "python",
      "verify.py"
    ],
    "failed_tests": 0,
    "passed_tests": 9
  },
  "naming_details": "Normalize both text fields using strip().casefold().replace('_', '-'). Preserve all other characters, including internal spaces, slash separators and Unicode.",
  "ordering": "Complete structural validation precedes duplicate selection. Duplicate selection precedes domain checks, whose order is invalid version, missing predecessor, version order. validation.validate returns fresh canonical rows in encounter order without selection or domain checks.",
  "day_2": "run_many(batches) and render_many(batches) retain their original typed signatures and NotImplementedError bodies. Their regression currently verifies these deferred stubs; update this coverage when implementing batches. Batch composition must use the engine.compute module attribute at call time and preserve independent result containers.",
  "shared_path": "run and render each call engine.compute exactly once through the module attribute. render uses ensure_ascii=False, sort_keys=True, separators=(comma, colon), and exactly one trailing newline."
}
