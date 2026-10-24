{
  "naming": "strip().casefold().replace('_', '-')",
  "selection": "After complete structural validation, collapse identical canonical rows with an existing id idempotently; any different canonical row with that id raises ValueError(\"cache-invalidation: duplicate id\"). Keep the first occurrence position.",
  "domain_rules": "Id is a cache key, target its dependency, value its nonnegative generation. A self target is a root. Reject negative generations first with ValueError(\"cache-invalidation: negative generation\"), then absent dependencies with ValueError(\"cache-invalidation: missing dependency\"), then non-root cycles with ValueError(\"cache-invalidation: cycle\"). A key is dirty when its own generation is zero or its dependency is transitively dirty. Return {\"dirty\": [ids], \"clean\": [ids]} with both lists lexicographically sorted.",
  "error_prefix": "cache-invalidation",
  "verification": {
    "command": [
      "python",
      "verify.py"
    ],
    "failed_tests": 0,
    "passed_tests": 11
  },
  "naming_scope": "Apply the naming recipe to both id and target. Preserve every other character, including internal spaces, slash separators and Unicode.",
  "validation_order": "Validate all rows structurally and canonicalize before duplicate selection. validation.validate returns fresh canonical rows in encounter order without duplicate selection or domain checks. Duplicate errors precede negative generation, missing dependency and cycle errors.",
  "shared_policy_path": "project.run and project.render resolve engine.compute at call time and invoke it exactly once per call. Batch implementations must use the same path.",
  "day_2_remaining": "run_many(batches) and render_many(batches) retain their original signatures and NotImplementedError bodies. Their current regression checks the deferred behavior; replace it with batch composition coverage on day 2. Batch result independence remains to be implemented and verified.",
  "implementation": "Domain traversal is iterative and supports dependency chains beyond Python recursion limits. Output dictionary insertion order is dirty then clean; both lists are lexicographically sorted. Rendering uses recursively sorted object keys, Unicode JSON, compact separators and one trailing newline."
}
