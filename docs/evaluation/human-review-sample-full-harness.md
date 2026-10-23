# Human review sample: full harness v2 verdicts (report c1207c9)

Drawn with `python -m verifier sample --reports eval/reports/full-harness --n 20` (seed 42, 142 verdicts available). Reviewer: the user. For each row, read the verdict items in the task's result.json, compare them with the hidden-test outcome and the workspace, and record agree, disagree or unsure with a note. Verdict items that the hidden tests contradict are the interesting ones.

| # | Task | Type | Attempt | Verdict | Items pass/total | Task outcome | Where | Your verdict | Note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | two-session-common-prefix | feature_plus_test | 1 | pass | 5/5 | pass | eval/reports/full-harness/two-session-common-prefix/ |  |  |
| 2 | constrained-refactoring-common-prefix | constrained_refactoring | 1 | pass | 5/5 | pass | eval/reports/full-harness/constrained-refactoring-common-prefix/ |  |  |
| 3 | multiple-requirements-select-columns | multiple_requirements | 1 | pass | 5/5 | pass | eval/reports/full-harness/multiple-requirements-select-columns/ |  |  |
| 4 | bug-fix-round-robin | bug_fix | 1 | pass | 4/4 | pass | eval/reports/full-harness/bug-fix-round-robin/ |  |  |
| 5 | two-session-balanced-brackets | feature_plus_test | 1 | pass | 6/6 | pass | eval/reports/full-harness/two-session-balanced-brackets/ |  |  |
| 6 | constrained-refactoring-ordinal-labels | constrained_refactoring | 1 | pass | 4/4 | pass | eval/reports/full-harness/constrained-refactoring-ordinal-labels/ |  |  |
| 7 | multiple-requirements-line-endings | multiple_requirements | 1 | pass | 6/6 | pass | eval/reports/full-harness/multiple-requirements-line-endings/ |  |  |
| 8 | bug-fix-merge-counts | bug_fix | 1 | pass | 4/4 | pass | eval/reports/full-harness/bug-fix-merge-counts/ |  |  |
| 9 | feature-plus-test-invert-groups | feature_plus_test | 1 | pass | 7/7 | pass | eval/reports/full-harness/feature-plus-test-invert-groups/ |  |  |
| 10 | constrained-refactoring-invert-groups | constrained_refactoring | 1 | pass | 4/4 | pass | eval/reports/full-harness/constrained-refactoring-invert-groups/ |  |  |
| 11 | multiple-requirements-balanced-brackets | multiple_requirements | 1 | pass | 6/6 | pass | eval/reports/full-harness/multiple-requirements-balanced-brackets/ |  |  |
| 12 | bug-fix-line-endings | bug_fix | 1 | pass | 4/4 | pass | eval/reports/full-harness/bug-fix-line-endings/ |  |  |
| 13 | two-session-merge-counts | feature_plus_test | 1 | pass | 4/4 | pass | eval/reports/full-harness/two-session-merge-counts/ |  |  |
| 14 | constrained-refactoring-pairwise-edges | constrained_refactoring | 2 | pass | 7/7 | pass | eval/reports/full-harness/constrained-refactoring-pairwise-edges/ |  |  |
| 15 | multiple-requirements-interval-union | multiple_requirements | 1 | pass | 6/6 | pass | eval/reports/full-harness/multiple-requirements-interval-union/ |  |  |
| 16 | bug-fix-interleave | bug_fix | 1 | pass | 6/6 | pass | eval/reports/full-harness/bug-fix-interleave/ |  |  |
| 17 | feature-plus-test-interleave | feature_plus_test | 1 | pass | 5/5 | pass | eval/reports/full-harness/feature-plus-test-interleave/ |  |  |
| 18 | constrained-refactoring-select-columns | constrained_refactoring | 1 | fail | 3/4 | pass | eval/reports/full-harness/constrained-refactoring-select-columns/ |  |  |
| 19 | multiple-requirements-unique-permutations | multiple_requirements | 1 | pass | 6/6 | pass | eval/reports/full-harness/multiple-requirements-unique-permutations/ |  |  |
| 20 | bug-fix-common-prefix | bug_fix | 1 | pass | 3/3 | pass | eval/reports/full-harness/bug-fix-common-prefix/ |  |  |

Sample size: 20. Verdict content is in each task's result.json under verdicts; contracts and control streams are republished once r5-publish-001 lands.
