Repair the incremental build planner in buildplan.py. A removed source dependency
can leave a transitive output stale. plan(previous, current, sources, outputs)
returns target names in dependency-first order; it performs no file writes.

BP1. current maps target names to ordered dependency-name lists; a dependency absent
from current is a source. Sources maps source name to Stamp(digest, mtime).
Outputs maps target name to Stamp; absent output requires rebuilding. A Previous
record stores dependencies, input_digests and built_at for one old target. Missing
previous records require rebuilding. Content digest equality outranks timestamps:
a source timestamp change alone is clean; a digest change is dirty even if older.
BP2. A target is dirty if its ordered dependency list changed (including removals or
reordering), any source input digest differs from its old snapshot, or any target
dependency is dirty. Missing required sources raise ValueError('missing:NAME').
Targets removed from current are not output. An empty unchanged target with an
existing output and previous record is clean. Repeated dependencies are allowed.
BP3. Traverse target roots in sorted-name order and dependencies in listed order;
append each dirty target once after dependencies. A target cycle raises
ValueError('cycle:NAME') at the first active target revisited by that traversal.
Validate the entire current graph, even clean targets. Never mutate the inputs,
outputs or old snapshots. The function's result must be repeatable.

Use Python 3.11+ and the standard library. Preserve the documented public API.
Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
Change application code and add regression tests as needed.
