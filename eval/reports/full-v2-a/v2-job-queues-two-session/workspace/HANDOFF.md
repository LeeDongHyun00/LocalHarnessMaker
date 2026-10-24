{
  "naming": "strip().casefold().replace('_', '-')",
  "naming_details": "Normalize both id and target using the naming recipe. Preserve all other characters, including internal spaces, slash separators and Unicode.",
  "selection": "After complete structural validation, collapse identical canonical rows with an existing id idempotently; any different canonical row with that id raises ValueError(\"job-queues: duplicate id\"). Keep the first occurrence position.",
  "domain_rules": "Each target is a queue, value its signed priority. Return {\"queues\": {target: [id,...]}} with queue names lexicographically inserted. Within a queue, order higher priority first; equal priorities retain selected-row encounter order. Never use id to break priority ties.",
  "error_prefix": "job-queues",
  "verification": {
    "command": [
      "python",
      "verify.py"
    ],
    "failed_tests": 0,
    "passed_tests": 8
  },
  "validation_order": "validation.validate creates fresh canonical rows for every structurally valid row in encounter order. Complete structural validation precedes duplicate selection and domain resolution; a malformed later row takes precedence over an earlier conflicting duplicate.",
  "shared_path": "run and render each resolve engine.compute at call time and invoke it exactly once. Keep this path for day-2 batch composition.",
  "deferred": "run_many(batches) and render_many(batches) preserve their signatures and type hints but raise NotImplementedError. Implement batch bodies on day 2; replace the regression that currently checks these intentional stubs with behavioral batch coverage, including independence between batch members."
}
