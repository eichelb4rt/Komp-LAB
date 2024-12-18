import argparse
from io import TextIOWrapper
from typing import Self
from pathlib import Path

from test import TestAction


################################################################
# FUNCTIONALITY
################################################################


def skip_comments(f: TextIOWrapper) -> str:
    while line := f.readline():
        if line[0] != '#':
            return line
    return ""


Node = int
Edge = tuple[Node, Node]
AdjacencyList = dict[Node, list[Node]]


def reverse_edge(edge: Edge) -> Edge:
    return (edge[1], edge[0])


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

    def get_edges(self) -> list[Edge]:
        edges: list[Edge] = []
        for node in self.nodes:
            for neighbour in self.neighbours[node]:
                # if the edge was not collected yet, collect it
                if (node, neighbour) not in edges and (neighbour, node) not in edges:
                    edges.append((node, neighbour))
        return edges

    def __eq__(self, other):
        if isinstance(other, Graph):
            return (self.nodes, self.neighbours) == (other.nodes, other.neighbours)
        return False

    @classmethod
    def from_file(cls, filename) -> Self:
        with open(filename, 'r') as f:
            # read promises
            firstline = skip_comments(f)
            n_nodes, n_edges = [int(c) for c in firstline.split(" ")]
            # read nodes
            secondline = skip_comments(f)
            nodes = {int(node) for node in secondline.split(",")}
            assert len(nodes) == n_nodes, f"Nodes do not have promised count. (Promised: {n_nodes}, Observed: {len(nodes)})"
            # read edges
            edges: list[Edge] = []
            while line := skip_comments(f):
                from_node, to_node = cls.parse_edge(line)
                assert (from_node, to_node) not in edges and (to_node, from_node) not in edges, f"Edges should be unique, {(from_node, to_node)} appeared twice."
                edges.append((from_node, to_node))
            assert len(edges) == n_edges, f"Edges do not have promised count. (Promised: {n_edges}, Observed: {len(edges)})"
        return cls.from_edges(nodes, edges)

    @classmethod
    def parse_edge(cls, edge_str: str) -> Edge:
        from_node, to_node = edge_str.split("--")
        return (int(from_node), int(to_node))

    @classmethod
    def from_edges(cls, nodes: set[Node], edges: list[Edge]) -> Self:
        """Assumes all edges are unique."""

        # check if all edges contain correct nodes
        observed_nodes = {node for edge in edges for node in edge}
        assert observed_nodes.issubset(nodes)
        # build adjacency list
        neighbours: dict[Node, list[Node]] = {node: [] for node in nodes}
        for edge in edges:
            # edge is undirected
            neighbours[edge[0]].append(edge[1])
            neighbours[edge[1]].append(edge[0])
        return cls(nodes, neighbours)

    def write(self, filename: str):
        edges = self.get_edges()
        out_str = f"{len(self.nodes)} {len(edges)}\n"
        out_str += ", ".join(map(str, self.nodes)) + "\n"
        for from_node, to_node in edges:
            out_str += f"{from_node} -- {to_node}\n"
        with open(filename, 'w') as f:
            f.write(out_str)

    def dot_encode(self) -> str:
        dot_str = "strict graph {\n"
        # add all nodes
        for node in self.nodes:
            dot_str += f"\t{node}\n"
        # add all edges
        for from_node, to_node in self.get_edges():
            dot_str += f"\t{from_node} -- {to_node}\n"
        # close encoding
        dot_str += "}"
        return dot_str


################################################################
# TESTS
################################################################


def test_graphs():
    nodes_0 = {1, 3, 5, 7, 9}
    edges_0 = [
        (1, 3),
        (1, 5),
        (1, 7),
        (7, 9)
    ]
    graph_0 = Graph.from_edges(nodes_0, edges_0)

    nodes_1 = {1, 3, 5}
    edges_1 = [
        (1, 3),
        (1, 5)
    ]
    graph_1 = Graph.from_edges(nodes_1, edges_1)

    nodes_2 = {1, 3, 4}
    edges_2 = [
        (1, 3),
        (1, 4)
    ]
    graph_2 = Graph.from_edges(nodes_2, edges_2)

    edges_3 = [
        (1, 3)
    ]
    graph_3 = Graph.from_edges(nodes_1, edges_3)

    # neighbours of 1 are 3, 5 and 7
    assert graph_0.adjacent_nodes({1}) == {3, 5, 7}

    # the empty subgraph should be empty
    empty_set = set()
    assert graph_0.subgraph(empty_set).is_empty()

    # graph 1 is a subgraph of graph 0
    assert graph_0.subgraph(nodes_1) == graph_1

    # even though they are isomorph, they are not the exact same graph
    assert graph_1 != graph_2

    # same nodes, but not the same edges
    assert graph_1 != graph_3

    # try reading graph_0 from file and make sure it's the same as here
    graph_0_from_file = Graph.from_file("inputs/graph_0.txt")
    assert graph_0_from_file == graph_0

    print("Graph test: all tests passed.")


################################################################
# MAIN
################################################################


def main():
    parser = argparse.ArgumentParser(description="Reads a graph from a file and saves it as a dot encoding.")
    parser.add_argument("filename",
                        help="File with the encoded graph.")
    parser.add_argument("--test",
                        action=TestAction.build(test_graphs),
                        help="Tests the implementation (no other arguments needed).")
    args = parser.parse_args()

    graph = Graph.from_file(args.filename)
    out_file = f"dot_encodings/{Path(args.filename).stem}.dot"
    with open(out_file, 'w') as f:
        f.write(graph.dot_encode())
    print("Graph successfully converted to DOT encoding.")


if __name__ == "__main__":
    main()
