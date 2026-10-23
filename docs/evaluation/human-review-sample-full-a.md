# Human review sample: full baseline A (report a21eda2)

Drawn by Claude on 2026-10-23 with seed 42: 5 valid tasks per type plus every failed task. Reviewer: the user. For each task, open the public prompt and the executor's final workspace, and judge whether the hidden-test outcome looks right. Record your verdict in the last column (agree, disagree, unsure) and a note.

| # | Task | Type | Outcome | Attempts | Workspace | Prompt | Your verdict | Note |
|---|---|---|---|---|---|---|---|---|
| 1 | bug-chunk-tail | bug_fix | pass | 1 | eval/reports/full-a/bug-chunk-tail/workspace/ | eval/tasks/bug-chunk-tail/prompt.md |  |  |
| 2 | bug-fix-stable-unique | bug_fix | pass | 1 | eval/reports/full-a/bug-fix-stable-unique/workspace/ | eval/tasks/bug-fix-stable-unique/prompt.md |  |  |
| 3 | bug-fix-strip-prefix | bug_fix | pass | 1 | eval/reports/full-a/bug-fix-strip-prefix/workspace/ | eval/tasks/bug-fix-strip-prefix/prompt.md |  |  |
| 4 | bug-fix-interleave | bug_fix | pass | 1 | eval/reports/full-a/bug-fix-interleave/workspace/ | eval/tasks/bug-fix-interleave/prompt.md |  |  |
| 5 | bug-fix-adjacent-runs | bug_fix | pass | 1 | eval/reports/full-a/bug-fix-adjacent-runs/workspace/ | eval/tasks/bug-fix-adjacent-runs/prompt.md |  |  |
| 6 | constrained-refactoring-unique-permutations | constrained_refactoring | pass | 1 | eval/reports/full-a/constrained-refactoring-unique-permutations/workspace/ | eval/tasks/constrained-refactoring-unique-permutations/prompt.md |  |  |
| 7 | constrained-refactoring-prefix-sums | constrained_refactoring | pass | 1 | eval/reports/full-a/constrained-refactoring-prefix-sums/workspace/ | eval/tasks/constrained-refactoring-prefix-sums/prompt.md |  |  |
| 8 | constrained-refactoring-last-index | constrained_refactoring | pass | 1 | eval/reports/full-a/constrained-refactoring-last-index/workspace/ | eval/tasks/constrained-refactoring-last-index/prompt.md |  |  |
| 9 | constrained-refactoring-ordinal-labels | constrained_refactoring | pass | 1 | eval/reports/full-a/constrained-refactoring-ordinal-labels/workspace/ | eval/tasks/constrained-refactoring-ordinal-labels/prompt.md |  |  |
| 10 | constrained-refactoring-word-counts | constrained_refactoring | pass | 1 | eval/reports/full-a/constrained-refactoring-word-counts/workspace/ | eval/tasks/constrained-refactoring-word-counts/prompt.md |  |  |
| 11 | two-session-flatten-once | feature_plus_test | pass | 2 | eval/reports/full-a/two-session-flatten-once/workspace/ | eval/tasks/two-session-flatten-once/prompt.md |  |  |
| 12 | feature-plus-test-clamp-values | feature_plus_test | pass | 1 | eval/reports/full-a/feature-plus-test-clamp-values/workspace/ | eval/tasks/feature-plus-test-clamp-values/prompt.md |  |  |
| 13 | two-session-word-counts | feature_plus_test | pass | 2 | eval/reports/full-a/two-session-word-counts/workspace/ | eval/tasks/two-session-word-counts/prompt.md |  |  |
| 14 | two-session-common-prefix | feature_plus_test | fail | 2 | eval/reports/full-a/two-session-common-prefix/workspace/ | eval/tasks/two-session-common-prefix/prompt.md |  |  |
| 15 | feature-plus-test-interval-union | feature_plus_test | pass | 1 | eval/reports/full-a/feature-plus-test-interval-union/workspace/ | eval/tasks/feature-plus-test-interval-union/prompt.md |  |  |
| 16 | multiple-requirements-round-robin | multiple_requirements | pass | 1 | eval/reports/full-a/multiple-requirements-round-robin/workspace/ | eval/tasks/multiple-requirements-round-robin/prompt.md |  |  |
| 17 | multiple-requirements-window-slices | multiple_requirements | pass | 1 | eval/reports/full-a/multiple-requirements-window-slices/workspace/ | eval/tasks/multiple-requirements-window-slices/prompt.md |  |  |
| 18 | multiple-requirements-word-counts | multiple_requirements | pass | 1 | eval/reports/full-a/multiple-requirements-word-counts/workspace/ | eval/tasks/multiple-requirements-word-counts/prompt.md |  |  |
| 19 | multiple-requirements-adjacent-runs | multiple_requirements | pass | 1 | eval/reports/full-a/multiple-requirements-adjacent-runs/workspace/ | eval/tasks/multiple-requirements-adjacent-runs/prompt.md |  |  |
| 20 | multiple-requirements-rotate-left | multiple_requirements | pass | 1 | eval/reports/full-a/multiple-requirements-rotate-left/workspace/ | eval/tasks/multiple-requirements-rotate-left/prompt.md |  |  |
| 21 | two-session-line-endings | feature_plus_test | fail | 2 | eval/reports/full-a/two-session-line-endings/workspace/ | eval/tasks/two-session-line-endings/prompt.md |  |  |
| 22 | two-session-adjacent-runs | feature_plus_test | fail | 2 | eval/reports/full-a/two-session-adjacent-runs/workspace/ | eval/tasks/two-session-adjacent-runs/prompt.md |  |  |

Rules: do not open the private graders. The grading log in each task directory lists test names and results only.

Sample size: 22 (2 failures included).
