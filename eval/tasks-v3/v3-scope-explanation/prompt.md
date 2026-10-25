Add Policy.explain(roles, resource) to access.py. Rule(role, resource, effect) is
frozen; effect is allow or deny. parents maps role names to parent role lists.
Keep Policy(parents, rules) and allows(roles, resource) -> bool.

SE1. Reachable roles include supplied roles and all transitive parents; unknown
roles are leaves. Any matching deny wins over every allow regardless of
distance. Match a rule's role and its exact resource or '*'. Default is deny.
allows and explain must use exactly the same policy.
SE2. explain returns exactly {'allowed': bool, 'roles': sorted unique reachable
names, 'matched': matching rule indices in original source order, 'winner':
index or None}. Winner is first matching deny, otherwise first matching allow,
otherwise None. Irrelevant rules must not appear.
SE3. At construction reject cycles anywhere in the parent graph with ValueError,
including unreachable cycles. Copy input collections so later mutations do not
alter policy. Do not mutate actor roles. Add a regression test detecting an
inherited deny incorrectly losing to a direct allow.

SE4. Keep test_public.py byte-for-byte unchanged and keep its tests
passing. Supply executable regression tests as described above.

Use Python 3.11+ and the standard library. Keep the public signatures and existing
behavior except for the specified feature. Add meaningful unittest tests to
regression_tests.py (not test_*.py); they must pass with the implementation and
fail for the regression named above, even when that defective implementation
still exposes the complete API. Do not change test_public.py. Run both
`python -m unittest discover -s . -p "test_*.py" -v` and
`python -m unittest regression_tests -v` from workspace/.
