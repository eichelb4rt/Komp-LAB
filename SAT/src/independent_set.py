import argparse
from pathlib import Path
from bit_util import to_bits

from dpll import DPLLSolver
from graph import Graph, Node
from circuit import MAX_RESERVED_VARIABLE, ZERO_BIT, CountBitsCircuit
from cnf import CNF, Clause

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


def independent_set_cnf(graph: Graph, k: int) -> CNF:
    # map the nodes to variables (1 is reserved for ZERO_BIT)
    to_variable = {node: variable for variable, node in enumerate(graph.nodes, start=MAX_RESERVED_VARIABLE + 1)}
    # encode the edges in the cnf
    clauses: list[Clause] = [[-to_variable[from_node], -to_variable[to_node]] for from_node, to_node in graph.get_edges()]

    # encode that the number of picked nodes is k
    # extract node variables
    node_variables = list(to_variable.values())
    # encode k as bits (lowest bit at k_bits[0])
    k_bits = to_bits(k)

    # make a circuit that calculates the number of true variables
    counter = CountBitsCircuit(node_variables, len(k_bits), start_at=max(node_variables) + 1)
    # simulate the gates with clauses
    clauses += counter.tseitin().clauses
    # the sum bits should equal the k bits, encode that
    clauses += [[sum_bit_variable * (1 if k_bit else -1)] for sum_bit_variable, k_bit in zip(counter.sum_bits, k_bits)]

    # make sure the ZERO_BIT is set to 0
    clauses += [[-ZERO_BIT]]

    # build the cnf
    # variables are: nodes, gates, ZERO_BIT
    n_variables = len(graph.nodes) + counter.size + 1
    n_clauses = len(clauses)
    return CNF(n_variables, n_clauses, clauses)


################################################################
# TESTS
################################################################


def test_independent_set():
    # file, max independent set, max checked k
    test_graphs = [
        ("graphs/graph_0.txt", 3, 10),
        ("graphs/graph_nikolaus.txt", 2, 10)
    ]

    print("Testing recursive function.")
    # test recursive independent set function
    for graph_file, max_set, max_checked in test_graphs:
        graph = Graph.from_file(graph_file)
        for k in range(max_set + 1):
            exists, nodes = independent_set(graph, k)
            assert exists
        for k in range(max_set + 1, max_checked + 1):
            exists, nodes = independent_set(graph, k)
            assert not exists

    # build cnfs
    print("Building cnfs.")
    cnfs: list[list[CNF]] = [[] for _ in test_graphs]
    for test_index, (graph_file, max_set, max_checked) in enumerate(test_graphs):
        graph = Graph.from_file(graph_file)
        for k in range(max_checked + 1):
            cnf = independent_set_cnf(graph, k)
            cnfs[test_index].append(cnf)

    # solve cnfs and see if they work
    print("Solving cnfs.")
    solver = DPLLSolver()
    for test_index in range(len(test_graphs)):
        _, max_set, max_checked = test_graphs[test_index]
        for k in range(max_set + 1):
            exists = solver.solve(cnfs[test_index][k])
            assert exists
        for k in range(max_set + 1, max_checked + 1):
            exists = solver.solve(cnfs[test_index][k])
            assert not exists

    print("Independent set test: all tests passed.")


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
    parser.add_argument("--cnf",
                        action='store_true',
                        help="Builds and saves a cnf for the problem instead of solving it recursively.")
    parser.add_argument("--test",
                        action=TestAction.build(test_independent_set),
                        help="Tests the implementation (no other arguments needed).")
    args = parser.parse_args()

    graph = Graph.from_file(args.filename)
    if args.cnf:
        cnf = independent_set_cnf(graph, args.k)
        cnf_file = f"inputs/cnf_independent_set_k_{args.k}_{Path(args.filename).stem}.txt"
        cnf.write(cnf_file)
        print(f"CNF written to: {cnf_file}")
    else:
        possible, node_list = independent_set(graph, args.k)
        if possible:
            print(f"There exists and independent node set with size {args.k}: {node_list}")
        else:
            print(f"There does not exist and independent node et with size {args.k}.")


if __name__ == "__main__":
    main()
