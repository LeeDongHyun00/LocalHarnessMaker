from collections import deque
from collections.abc import Hashable, Iterable, Mapping

def route(graph: Mapping[Hashable, Iterable[Hashable]], source: Hashable, target: Hashable) -> list[Hashable] | None:
    queue = deque([(source,[source])])
    visited = {source}
    while queue:
        node,path = queue.popleft()
        if node == target:
            return path
        for neighbor in graph.get(node,()):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor,path+[neighbor]))
    return None
