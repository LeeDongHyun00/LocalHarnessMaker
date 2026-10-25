class Graph:
    def __init__(self, nodes: object, edges: object) -> None:
        self.nodes=set(nodes)
        self.edges=set(map(tuple,edges))
    def condensation(self) -> dict:
        return {'components':[(n,) for n in sorted(self.nodes)],'edges':sorted(self.edges)}
