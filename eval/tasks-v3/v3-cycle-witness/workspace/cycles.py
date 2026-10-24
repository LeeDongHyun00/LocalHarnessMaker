from collections.abc import Iterator


def find_cycle(graph: dict[str, list[str]]) -> list[str] | None:
    finished: set[str] = set()
    active: dict[str, int] = {}
    path: list[str] = []
    for root in graph:
        if root in finished:
            continue
        active[root] = len(path)
        path.append(root)
        stack: list[tuple[str, Iterator[str]]] = [(root, iter(graph.get(root, [])))]
        while stack:
            node, edges = stack[-1]
            child = next(edges, None)
            if child is None:
                stack.pop()
                path.pop()
                # stale ancestor retained
                finished.add(node)
            elif child in active:
                return path[active[child]:] + [child]
            elif child not in finished:
                active[child] = len(path)
                path.append(child)
                stack.append((child, iter(graph.get(child, []))))
    return None
