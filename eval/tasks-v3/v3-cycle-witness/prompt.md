Fix find_cycle(graph) in cycles.py. It uses iterative depth-first search to return
a directed cycle witness, but disconnected components can leak stale path state.
The input is a dict mapping string vertices to lists of successor strings.

CW1. Return None for an acyclic graph; otherwise return a list beginning and ending
with the same vertex. Every adjacent pair must be an edge, and internal vertices
must be distinct. A self-loop returns [vertex, vertex]. Do not change the input.
CW2. Determinism is part of the API: visit roots in dictionary insertion order and
successors in list order; choose the first back edge to a currently active ancestor.
Include successor-only vertices as terminal vertices. Finished vertices and disconnected
components cannot remain on the active path. Repeated edges are permitted.
CW3. Use an explicit DFS stack. A path of 4000 vertices must work without changing
Python's recursion limit or recursing. Expand each vertex's successor list at most once per call. Calls must be independent and repeatable.

Use Python 3.11+ and the standard library. Preserve the documented public API.
Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
Change application code and add regression tests as needed.
