import argparse
from graph import Graph, Node
from test import TestAction


################################################################
# FUNCTIONALITY
################################################################


def independent_set(graph: Graph, k: int) -> tuple[bool, list[Node]]:
    """Returns True and a list of k independent nodes if it exists, False and None otherwise."""

    # we can always find an empty set of independent nodes
    if k == 0:
        return True, []

    for node in graph.nodes:
        # remove the node and its neighbours from the graph
        removed_nodes = set([node] + graph.neighbours[node])
        remaining_nodes = graph.nodes - removed_nodes
        subgraph = graph.subgraph(remaining_nodes)
        # see if we can make an independent set with this subgraph and the remaining nodes
        subgraph_possible, node_list = independent_set(subgraph, k - 1)
        # if we could make an independent set, we can expand this set by n for a bigger independent set
        if subgraph_possible:
            return True, node_list + [node]
    return False, None


################################################################
# TESTS
################################################################


def test_independent_set():
    graph = Graph.from_file("graphs/graph_0.txt")
    for k in range(4):
        assert independent_set(graph, k)[0]
    for k in range(4, 10):
        assert not independent_set(graph, k)[0]

    print("independent_set test: all tests passed.")


################################################################
# MAIN
################################################################


def main():
    parser = argparse.ArgumentParser(description="Determines if there is an independent set of k nodes.")
    parser.add_argument("filename",
                        help="File with the encoded graph.")
    parser.add_argument("k",
                        type=int,
                        help="Number of independent nodes.")
    parser.add_argument("--test",
                        action=TestAction.build(test_independent_set),
                        help="Tests the implementation (no other arguments needed).")
    args = parser.parse_args()

    graph = Graph.from_file(args.filename)
    possible, node_list = independent_set(graph, args.k)
    if possible:
        print(f"There exists and independent node set with size {args.k}: {node_list}")
    else:
        print(f"There does not exist and independent node et with size {args.k}.")


if __name__ == "__main__":
    main()
