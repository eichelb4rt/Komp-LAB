from typing import Self


Node = int
Edge = tuple[Node, Node]
AdjacencyList = dict[Node, list[Node]]


class Graph:
    def __init__(self, nodes: set[Node], neighbours: AdjacencyList):
        self.nodes = nodes
        self.neighbours = neighbours

    def is_empty(self) -> bool:
        return len(self.nodes) == 0

    def adjacent_nodes(self, nodes: set[Node]) -> set[Node]:
        """Returns all the adjacent nodes of a set of nodes."""

        # first gather all neighbours
        all_neighbours = {neighbour for node in nodes for neighbour in self.neighbours[node]}
        # neighbours could contain the nodes themselves; remove them.
        return all_neighbours - nodes

    def subgraph(self, nodes: set[Node]) -> Self:
        """Returns a subgraph with the given nodes."""

        # only allow specified nodes in the edges
        neighbours = {node: [neighbour for neighbour in self.neighbours[node] if neighbour in nodes] for node in nodes}
        return Graph(nodes, neighbours)

    @classmethod
    def from_edges(cls, nodes: set[Node], edges: list[Edge]) -> Self:
        # check if all edges contain correct nodes
        observed_nodes = {node for edge in edges for node in edge}
        assert observed_nodes.issubset(nodes)
        # build adjacency list
        neighbours: dict[Node, list[Node]] = {node: [] for node in nodes}
        for edge in edges:
            # edge is undirected
            neighbours[edge[0]].append(edge[1])
            neighbours[edge[1]].append(edge[0])
        return Graph(observed_nodes, neighbours)

    def __eq__(self, other):
        if isinstance(other, Graph):
            return (self.nodes, self.neighbours) == (other.nodes, other.neighbours)
        return False
