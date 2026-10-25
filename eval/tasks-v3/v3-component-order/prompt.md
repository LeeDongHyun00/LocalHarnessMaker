Implement Graph(nodes, edges) in components.py. Nodes are distinct strings;
edges are pairs of node names. Expose condensation() returning
{'components': [tuple_of_members,...], 'edges': [(representative,representative),...]}
using Python 3.11+ and the standard library.

CO1. Compute maximal strongly connected components, including isolated nodes
and self-loops. Sort members lexicographically; a component's representative
is its smallest member. Collapse intercomponent edges, remove self-edges and
deduplicate. Return condensation edges sorted lexicographically by the pair.
CO2. Return components in topological order from sources to sinks. Whenever
several components are ready, choose the lexicographically smallest
representative, recomputing the choice after each emitted component. This is
not a single initial sort of all components and not DFS finish order.
CO3. Construction snapshots nodes and edges; unknown edge endpoints raise
ValueError('node'). Duplicate edges are harmless. Empty input yields empty
lists. Repeated condensation calls and mutations of returned lists must not
change the graph; no recursion-depth limit on a chain of 1500 nodes. Each
condensation() call must execute at most 64*(N+E+1) Python line events in
components.py (including helpers there), where N is the node count and E is the
count of distinct original edges. This deterministic work budget applies to
that call only, not construction or update; heap operations in the standard
library do not count. Preserve
Graph and condensation signatures. Add tests and run
python -m unittest discover -s . -p 'test_*.py' -v in workspace/.
