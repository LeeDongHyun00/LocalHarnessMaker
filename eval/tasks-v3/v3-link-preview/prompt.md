Add a read-only symbolic-link plan to walkplan.py. Preserve walk(root), which
yields Entry(path, kind) descendants sorted by relative POSIX path, with kinds
file, directory, link. Do not descend into directory links or include root.

LP1. Add preview_links(root) -> list[LinkPlan], one frozen LinkPlan(path, target,
status) per link in walk order. path is relative POSIX and target is the exact
unmodified readlink text. Include directory and dangling links.
LP2. Resolve relative targets from the link's parent, following chains. status
is file or directory for existing targets inside the resolved root, missing for
absent internal targets, cycle for link loops, outside for final resolved paths
outside root, even missing ones. Check path components, not string prefixes.
Root is an existing directory; there are no concurrent filesystem changes.
LP3. Neither walker nor preview may create, modify or delete filesystem entries.
Repeated preview preserves bytes and link targets. Add a regression test that
detects resolving a nested relative link against root instead of its parent.

LP4. Keep test_public.py byte-for-byte unchanged and keep its tests
passing. Supply executable regression tests as described above.

Use Python 3.11+ and the standard library. Keep the public signatures and existing
behavior except for the specified feature. Add meaningful unittest tests to
regression_tests.py (not test_*.py); they must pass with the implementation and
fail for the regression named above, even when that defective implementation
still exposes the complete API. Do not change test_public.py. Run both
`python -m unittest discover -s . -p "test_*.py" -v` and
`python -m unittest regression_tests -v` from workspace/.
