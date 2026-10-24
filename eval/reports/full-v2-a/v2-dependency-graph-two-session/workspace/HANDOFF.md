{
  "naming": "strip().casefold().replace('_', '-')",
  "selection": "After complete structural validation, collapse identical canonical rows with an existing id idempotently; any different canonical row with that id raises ValueError(\"dependency-graph: duplicate id\"). Keep the first occurrence position.",
  "domain_rules": "Each id is a node with one prerequisite named target. A self target marks a root, not a cycle. All other targets must name selected ids; otherwise ValueError(\"dependency-graph: missing dependency\"). Reject non-root cycles with ValueError(\"dependency-graph: cycle\"). Return {\"order\": [...]} using Kahn waves: in each round append all currently ready ids sorted lexicographically; a node cannot become ready until the next round. Values are metadata, not ordering weights.",
  "error_prefix": "dependency-graph",
  "verification": {
    "command": [
      "python",
      "verify.py"
    ],
    "failed_tests": 0,
    "passed_tests": 11
  },
  "naming_scope": "Apply the naming recipe to both id and target. Preserve all other characters, including internal spaces, slash separators and Unicode.",
  "validation_order": "Validate every row structurally before duplicate selection, then check missing dependencies before cycles. validation.validate returns fresh canonical rows in encounter order without selection or domain checks.",
  "shared_path": "run and render each call engine.compute exactly once through the engine module attribute at call time. Use this same path for day-2 batch composition.",
  "deferred": "run_many(batches) and render_many(batches) retain their original signatures and NotImplementedError stubs. Implement batch composition on day 2; replace the regression that asserts these temporary stubs with batch behavior coverage.",
  "protected_files": "project/compat.py, test_public.py, verify.py and README.md are unchanged byte for byte; SHA-256 hashes were checked after verification."
}
