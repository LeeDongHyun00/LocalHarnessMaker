{
  "naming": "strip().casefold().replace('_', '-')",
  "selection": "After complete structural validation, collapse identical canonical rows with an existing id idempotently; any different canonical row with that id raises ValueError(\"document-patches: duplicate id\"). Keep the first occurrence position.",
  "domain_rules": "Target is a document and value a nonnegative original offset. Reject negative offsets with ValueError(\"document-patches: negative offset\") before collision checks. Different patches at the same document/offset raise ValueError(\"document-patches: collision\"). Return {\"patches\": {document: [ids]}, \"offsets\": {document: [offsets]}} with document keys sorted and each list in decreasing original offset order, so application cannot shift a later patch location.",
  "error_prefix": "document-patches",
  "verification": {
    "command": [
      "python",
      "verify.py"
    ],
    "failed_tests": 0,
    "passed_tests": 10
  },
  "naming_scope": "Apply the naming recipe to both id and target; preserve all other characters, including internal spaces, slash separators and Unicode.",
  "ordering": "Validate every row structurally, then select by canonical id, then reject any negative offset, then check collisions. validation.validate only returns fresh canonical rows in encounter order.",
  "shared_path": "project.run and project.render each resolve engine.compute at call time and invoke it exactly once. Batch implementations must use this same shared domain-policy path.",
  "day_2": "run_many(batches) and render_many(batches) retain their typed signatures and NotImplementedError bodies. Batch functionality and independence between batch members remain deferred; regression coverage currently checks both stubs and input preservation."
}
