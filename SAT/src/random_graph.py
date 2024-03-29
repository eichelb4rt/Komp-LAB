import argparse
import random
from graph import Graph, Node, Edge, reverse_edge


def gen_edge(n_nodes: int) -> Edge:
    node_from = random.randint(1, n_nodes)
    # generate different second node
    node_to = random.randint(1, n_nodes)
    while node_to == node_from:
        node_to = random.randint(1, n_nodes)
    return (node_from, node_to)


def gen_graph(n_nodes: int, n_edges: int) -> Graph:
    assert n_edges <= n_nodes * (n_nodes - 1) // 2, "A graph cannot have more than n_nodes*(n_nodes)/2 edges."
    # build some edges
    edges: set[Node] = set()
    for _ in range(n_edges):
        # generate an edge that is not in the graph yet
        new_edge = gen_edge(n_nodes)
        while new_edge in edges or reverse_edge(new_edge) in edges:
            new_edge = gen_edge(n_nodes)
        edges.add(new_edge)
    # build the graph
    nodes = set(range(1, n_nodes + 1))
    return Graph.from_edges(nodes, list(edges))


def gen_graph_connected(n_nodes: int, n_edges: int) -> Graph:
    assert n_edges >= n_nodes - 1, "n_edges has to be at least n_nodes in a connected graph."
    assert n_edges <= n_nodes * (n_nodes - 1) // 2, "A graph cannot have more than n_nodes*(n_nodes)/2 edges."

    # have some nodes that are already connected, and some that are missing
    unconnected_nodes = list(range(1, n_nodes + 1))
    connected_nodes: list[int] = []
    # start by choosing a node
    first_node = random.choice(unconnected_nodes)
    unconnected_nodes.remove(first_node)
    connected_nodes.append(first_node)
    # add random edges from the connected nodes to the unconnected nodes
    edges: set[Node] = set()
    for _ in range(n_nodes - 1):
        node_from = random.choice(connected_nodes)
        node_to = random.choice(unconnected_nodes)
        edges.add((node_from, node_to))
        unconnected_nodes.remove(node_to)
        connected_nodes.append(node_to)
    # now add random edges
    for _ in range(n_edges - n_nodes + 1):
        # generate an edge that is not in the graph yet
        new_edge = gen_edge(n_nodes)
        while new_edge in edges or reverse_edge(new_edge) in edges:
            new_edge = gen_edge(n_nodes)
        edges.add(new_edge)
    return Graph.from_edges(connected_nodes, list(edges))


def main():
    parser = argparse.ArgumentParser(description="Generates random graphs.")
    parser.add_argument("n_graphs",
                        type=int,
                        help="Number of graphs generated.")
    parser.add_argument("n_nodes",
                        type=int,
                        help="Number of nodes in the generated graph.")
    parser.add_argument("n_edges",
                        type=int,
                        help="Number of edges in the generated graph.")
    parser.add_argument("-c", "--connected",
                        action='store_true',
                        help="Only generate connected graphs.")
    args = parser.parse_args()

    for i in range(args.n_graphs):
        if args.connected:
            random_graph = gen_graph_connected(args.n_nodes, args.n_edges)
        else:
            random_graph = gen_graph(args.n_nodes, args.n_edges)
        out_file = f"inputs/graph_{i}.random.txt"
        random_graph.write(out_file)


if __name__ == "__main__":
    main()
