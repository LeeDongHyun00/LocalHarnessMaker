{
  "naming": "strip().casefold().replace('_', '-')",
  "selection": "After complete structural validation, collapse identical canonical rows with an existing id idempotently; any different canonical row with that id raises ValueError(\"workflow-state: duplicate id\"). Keep the first occurrence position.",
  "domain_rules": "Value is a state code: 0=open, 1=running, 2=closed. Reject other codes with ValueError(\"workflow-state: invalid state\") before transitions. For each target workflow the first event must be 0, then only 0->1 and 1->2 are allowed. An unchanged code is idempotent even with a new event id; reopening is forbidden. Invalid transitions raise ValueError(\"workflow-state: invalid transition\"). Return {\"states\": {workflow: code}} with keys sorted.",
  "error_prefix": "workflow-state",
  "verification": {
    "command": [
      "python",
      "verify.py"
    ],
    "failed_tests": 0,
    "passed_tests": 9
  },
  "naming_scope": "Apply the recipe to both id and target. Preserve all other characters, including internal spaces, slash separators and Unicode.",
  "ordering": "Validate all rows structurally before duplicate selection. Resolve duplicate conflicts before domain checks. Check all selected state codes before processing transitions. Preserve first occurrence order for selected ids; sort final workflow keys.",
  "shared_path": "run and render each resolve engine.compute at call time and invoke it exactly once. Batch extensions must use this same domain-policy path.",
  "day_2_remaining": "run_many(batches) and render_many(batches) retain their original type hints and signatures and raise NotImplementedError(\"Implement batch composition\"). Implement batch composition and extend the regression coverage for batch semantics tomorrow."
}
