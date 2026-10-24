{
  "naming": "strip().casefold().replace('_', '-')",
  "selection": "After complete structural validation, collapse identical canonical rows with an existing id idempotently; any different canonical row with that id raises ValueError(\"search-facets: duplicate id\"). Keep the first occurrence position.",
  "domain_rules": "Target is a facet label, value a signed score, id a document. Return {\"facets\": [{\"name\": target, \"count\": number_of_documents, \"score\": sum, \"ids\": [ids]},...]}. Facets sort by decreasing count, then decreasing score, then name; ids within a facet are lexicographically sorted. Include negative and zero totals.",
  "error_prefix": "search-facets",
  "verification": {
    "command": [
      "python",
      "verify.py"
    ],
    "failed_tests": 0,
    "passed_tests": 10
  },
  "validation_order": "Validate all rows structurally and canonicalize both id and target before duplicate selection or domain aggregation. validation.validate returns fresh rows in encounter order, including duplicates. Structural errors outrank duplicate errors.",
  "text_preservation": "Apply naming to both text fields; preserve every other character, including internal spaces, slash separators and Unicode.",
  "container_order": "The result has a facets key. Each facet inserts name, count, score, ids in that order. Empty input returns {\"facets\": []}.",
  "shared_policy_path": "run and render each call engine.compute exactly once through the module attribute at call time. Future batch composition must use this same path.",
  "day_2": "run_many(batches) and render_many(batches) keep their annotated signatures and raise NotImplementedError. Complete batch composition and replace the deferred-stub regression with batch behavior coverage, including independent containers across members.",
  "errors": {
    "outer": "TypeError(\"search-facets: rows must be a list\")",
    "row": "ValueError(\"search-facets: invalid row\")",
    "duplicate": "ValueError(\"search-facets: duplicate id\")"
  }
}
