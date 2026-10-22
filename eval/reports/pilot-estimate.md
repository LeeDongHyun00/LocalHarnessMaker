# Baseline A/B pilot estimate — 2026-10-22

Prepared for Claude to run on the host after pilot approval; no executor or model
call was made in preparation. D-2 pilot preparation is complete; SC-5 measured
results and approval are pending. Task set v1 is frozen at `7cdaf3b`, full-set
digest `b78913b04280f6696d419d2afdc96b152675973d82f05199ddef848986285d1f`
([freeze record](../../docs/eval-freeze.md)).

The pinned snapshot is `openai-standard-short-2026-10-22-v1` in
[prices.yaml](../prices.yaml): [OpenAI pricing](https://developers.openai.com/api/docs/pricing),
Claude's host fetch supplied by the user, checked 2026-10-22. Standard tier,
short context up to 272K input tokens; USD per million tokens. The page provides
no price-list date or version; the snapshot identifier is locally assigned.
Sol input/cached/output = $2/$0.10/$10; Luna = $0.10/$0.01/$0.50.
Reasoning is included in output once. These are API-equivalent costs, not a
ChatGPT subscription invoice.

## Selection and configuration

Deterministic rule: visit task types in order bug_fix (3), feature_plus_test (3),
multiple_requirements (2), constrained_refactoring (2). For each type, sort
single-session tasks by `(family, id)` and take its quota, excluding families
already selected. The legacy bug-chunk-tail metadata has no family; use its ID
as the family key. This yields ten distinct families, without examining results.
Both configs retain this exact ordered list; seed 0 shuffles execution identically.

| Type | Tasks |
| --- | --- |
| bug_fix | bug-fix-adjacent-runs; bug-fix-balanced-brackets; bug-chunk-tail |
| feature_plus_test | feature-plus-test-clamp-values; feature-plus-test-common-prefix; feature-plus-test-flatten-once |
| multiple_requirements | multiple-requirements-inclusive-range; multiple-requirements-interleave |
| constrained_refactoring | constrained-refactoring-interval-union; constrained-refactoring-invert-groups |

Both configs use gpt-6.1-sol, harness off, no control calls, seed 0,
`codex-cli 0.162.0-alpha.17.2`, retry_limit=0, reinstruction_limit=0,
600 seconds per executor process and 20 seconds per trusted grading process.
A requests medium effort; B requests max. Ten initial calls plus zero retries
means at most ten executor calls per configuration, twenty combined. Recovery
of an interrupted process can add a segment; such a continuation needs a revised
budget before invocation. Two-session tasks are excluded until supported.

## Token and cost estimate

Recorded [baseline-a-first-task](baseline-a-first-task/README.md) usage for one
medium task: 58,248 input including 54,656 cached, 524 output. Uncached input is
3,592. Cache tokens are a subset, not an additional input charge.

`(3592 * 2 + 54656 * 0.10 + 524 * 10) / 1000000 = $0.0178896` per A task.

| Scenario | Calls including retries | Input tokens | Cached subset | Output tokens | API-equivalent USD |
| --- | ---: | ---: | ---: | ---: | ---: |
| A per task | 1 | 58,248 | 54,656 | 524 | 0.0178896 |
| A ten tasks | 10 | 582,480 | 546,560 | 5,240 | 0.178896 |
| B per task, illustrative 2x output | 1 | 58,248 | 54,656 | 1,048 | 0.0231296 |
| B ten tasks, illustrative 2x output | 10 | 582,480 | 546,560 | 10,480 | 0.231296 |
| A+B, illustrative | 20 | 1,164,960 | 1,093,120 | 15,720 | 0.410192 |

For B with output multiplier k, per-task cost is `$0.0126496 + $0.00524*k`;
k=5 gives $0.388496 for ten B tasks and $0.567392 combined. These scenarios
are estimates, not upper bounds. More turns or reduced cache reuse increase cost.
At unchanged tokens but no cache reuse, A is $1.21736 for ten tasks; B at 2x
output is $1.26976, $2.48712 combined.

Plan used_percent cannot be predicted from tokens and is measured by the pilot.
Diagnostics retain native account snapshots alongside tokens for each executor
attempt. A true pre-run snapshot may be absent; before stays null and the first
in-run observation is labeled separately. Last in-run observation is labeled
after, with its timestamp; it is not a post-exit sample or exact task charge.
Concurrent account activity and rounding prevent exact task attribution.

## Host execution

After approval and host prerequisites, use fresh output directories:

```sh
.venv/bin/python -m eval run --config eval/configs/pilot-a.yaml --out eval/reports/pilot-a/
.venv/bin/python -m eval run --config eval/configs/pilot-b.yaml --out eval/reports/pilot-b/
```

The runner prints the reported estimate to stderr for these exact bundled
configs; other batches of ten or more remain blocked. This exception is not
user approval. Retain run diagnostics, native evidence, logs and hashes; review
all invalid/access-audit results and manually re-check five A samples. Do not
start a full run without explicit approval. The runner's task_set_sha256 hashes
the selected public/private inputs; the full frozen-set digest above identifies
the source population, while both pilots must have identical selected-set hashes.

## Assumptions

- The user-supplied host pricing fetch is authoritative for this offline session.
- CLI baseline calls use Standard short context unless evidence says otherwise;
  explicitly unknown tiers/models or long-context turns remain unpriced/null.
- One historical medium task is a planning proxy, not a representative sample.
- Max effort uses more output; 2x and 5x are illustrative assumptions, with input
  and cache reuse held fixed, not measured predictions or a spending cap.
- Retry limits of zero bound the pilot's initial batch and isolate effort.
