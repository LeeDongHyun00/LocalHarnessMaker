{
  "naming": "strip().casefold().replace('_', '-')",
  "selection": "After complete structural validation, collapse identical canonical rows with an existing id idempotently; any different canonical row with that id raises ValueError(\"calendar-windows: duplicate id\"). Keep the first occurrence position.",
  "domain_rules": "Value is an integer start hour in 0..23 inclusive, target a room, and each selected booking lasts one hour. Reject out-of-range hours with ValueError(\"calendar-windows: invalid hour\") before checking clashes. Two bookings in the same room with the same start raise ValueError(\"calendar-windows: overlap\"); adjacent hours do not clash. Return {\"rooms\": {target: [[start,end,id],...]}} with room names sorted and bookings sorted by start.",
  "error_prefix": "calendar-windows",
  "verification": {
    "command": [
      "python",
      "verify.py"
    ],
    "failed_tests": 0,
    "passed_tests": 9
  },
  "naming_scope": "Apply to both id and target through every public single-input entry point. Preserve every other character, including internal spaces, slash separators and Unicode.",
  "error_order": [
    "rows container type",
    "all row structural validation",
    "duplicate id selection",
    "all selected hour ranges",
    "overlap"
  ],
  "shared_path": "project.run and project.render resolve engine.compute at call time and invoke it exactly once. Batch extensions must use this same path.",
  "day_2": "run_many(batches) and render_many(batches) retain their annotated signatures and NotImplementedError bodies. Regression coverage currently asserts that deferred behavior; replace it when implementing batch composition and cross-member output independence.",
  "protected_sha256": {
    "project/compat.py": "bef387eee4b7a3e2b9a9df698ebd2e74157766c85e746adad16971085a87030b",
    "test_public.py": "40637f121d03705b3082b2eb3eed3a0c758d372ced53c12fb367b585b3b28fdd",
    "verify.py": "4dfdf99e793b0da8eef7a849ad80e237cf393e35870c42fdeac69d167a032b8a",
    "README.md": "3940c95abb93b87227532b41e980cb9d3510a9269b9fd3e218180e94fb6cf43a"
  }
}
