import argparse
from dpll import DPLLSolver
from graph import Graph, Node
from circuit import CountBitsCircuit, ZERO_BIT, MAX_RESERVED_VARIABLE
from cnf import CNF, Clause, Variable
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


def independent_set_cnf(graph: Graph, k: int) -> bool:
    # map the nodes to variables (1 is reserved for ZERO_BIT)
    to_variable = {node: variable for variable, node in enumerate(graph.nodes, start=MAX_RESERVED_VARIABLE + 1)}
    # encode the edges in the cnf
    edge_clauses: list[Clause] = [[-to_variable[from_node], -to_variable[to_node]] for from_node, to_node in graph.get_edges()]

    # encode that the number of picked nodes is k
    # extract node variables
    node_variables = list(to_variable.values())
    # encode k as bits (lowest bit at k_bits[0])
    k_bits = [int(bit) for bit in reversed(bin(k)[2:])]

    # make a circuit that calculates the number of true variables
    counter = CountBitsCircuit(node_variables, len(k_bits), start_at=max(node_variables) + 1)
    # simulate the gates with clauses
    counter_clauses = counter.sat_equivalent_cnf().clauses
    # the sum bits should equal the k bits, encode that
    correct_sum_bit_clauses: list[Clause] = [[sum_bit_variable * (1 if k_bit == 1 else -1)] for sum_bit_variable, k_bit in zip(counter.sum_bits, k_bits)]

    # make sure the ZERO_BIT is set to 0
    zero_bit_clauses = [[-ZERO_BIT]]

    # build the cnf
    # variables are: nodes, gates, ZERO_BIT
    n_variables = len(graph.nodes) + counter.size + 1
    # clauses: "don't pick nodes that are connected with an edge", "counter gates", "variable count is k", "ZERO_BITS"
    all_clauses = edge_clauses + counter_clauses + correct_sum_bit_clauses + zero_bit_clauses
    n_clauses = len(all_clauses)
    cnf = CNF(n_variables, n_clauses, all_clauses)
    solver = DPLLSolver()
    satisfiable = solver.solve(cnf)
    return satisfiable


################################################################
# TESTS
################################################################


def test_independent_set():
    # max independent set of graph_0 is 3
    max_set = 3
    max_checked = 10
    graph_0 = Graph.from_file("graphs/graph_0.txt")
    for k in range(max_set + 1):
        assert independent_set(graph_0, k)[0]
        assert independent_set_cnf(graph_0, k)
    for k in range(max_set + 1, max_checked + 1):
        assert not independent_set(graph_0, k)[0]
        assert not independent_set_cnf(graph_0, k)

    # max independent set of graph_nikolaus is 2
    max_set = 2
    max_checked = 10
    graph_nikolaustxt = Graph.from_file("graphs/graph_nikolaus.txt")
    for k in range(max_set + 1):
        assert independent_set(graph_nikolaustxt, k)[0]
        assert independent_set_cnf(graph_nikolaustxt, k)
    for k in range(max_set + 1, max_checked + 1):
        assert not independent_set(graph_nikolaustxt, k)[0]
        assert not independent_set_cnf(graph_nikolaustxt, k)

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
