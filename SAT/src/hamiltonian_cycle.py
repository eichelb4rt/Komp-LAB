import argparse
from pathlib import Path
from graph import Graph, Node
from cnf import CNF, Variable, Literal, Clause
from dpll import DPLLSolver
from test import TestAction


def hamiltonian_cycle_cnf(graph: Graph) -> CNF:
    """There is a hamiltonian cycle of length k if there is a hamiltonian path of length k and the last node has an edge to the first node."""

    # n is the number of nodes
    n = len(graph.nodes)
    # node index i -> node v_i
    nodes: dict[int, Node] = {i: node for i, node in enumerate(graph.nodes)}
    # there's n^2 variable for: v_ij = is_on_pos[i][j] <=> node v_i is on position j in the path
    is_on_pos: list[list[int]] = [[i * len(nodes) + j for j in range(1, n + 1)] for i in range(n)]
    # every node i has a defined position j
    # (each node appears at least once in the path)
    clauses: list[Clause] = [[is_on_pos[i][j] for j in range(n)] for i in range(n)]
    # no node j appears twice on the path
    # node k is not on position i and j at the same time if they are different
    clauses += [[-is_on_pos[k][i], -is_on_pos[k][j]] for k in range(n) for i in range(n) for j in range(n) if i != j]
    # each position on the path is occupied
    clauses += [[is_on_pos[i][j] for i in range(n)] for j in range(n)]
    # no position is occupied by 2 nodes
    # position k is not occupied by positions i and j at the same time if they are different
    clauses += [[-is_on_pos[i][k], -is_on_pos[j][k]] for k in range(n) for i in range(n) for j in range(n) if i != j]
    # non-adjacent nodes can not be adjacent in the path
    edges = graph.get_edges()
    # i and j are node indices. have_edge(i,j) <=> {v_i, v_j} in E
    have_edge = lambda i, j: (nodes[i], nodes[j]) in edges or (nodes[j], nodes[i]) in edges
    # node i on position k and node j on position (k + 1) % n do not have an edge between them => one of them is not on the right position
    clauses += [[-is_on_pos[i][k], -is_on_pos[j][(k + 1) % n]] for k in range(n) for i in range(n) for j in range(n) if i != j and not have_edge(i, j)]
    # build cnf
    n_vars = n**2
    n_clauses = len(clauses)
    return CNF(n_vars, n_clauses, clauses)


def test_cnf():
    graph_0 = Graph.from_file("inputs/graph_0.txt")
    cnf_graph_0 = hamiltonian_cycle_cnf(graph_0)
    graph_nikolaus = Graph.from_file("inputs/graph_nikolaus.txt")
    cnf_graph_nikolaus = hamiltonian_cycle_cnf(graph_nikolaus)
    solver = DPLLSolver()
    assert solver.solve(cnf_graph_0) is False
    assert solver.solve(cnf_graph_nikolaus) is True
    print("Hamiltonian Cycle Test: all tests passed.")


def main():
    # TODO: proper interface
    parser = argparse.ArgumentParser(description="Reads a graph from a file and saves it as a dot encoding.")
    parser.add_argument("filename",
                        help="File with the encoded graph.")
    parser.add_argument("--cnf",
                        action='store_true',
                        help="Saves the cnf instead of trying to solve it with my dpll solver.")
    parser.add_argument("--test",
                        action=TestAction.build(test_cnf),
                        help="Tests the implementation (no other arguments needed).")
    args = parser.parse_args()

    graph = Graph.from_file(args.filename)
    cnf = hamiltonian_cycle_cnf(graph)

    if args.cnf:
        out_file = f"inputs/cnf_hamiltonian_cycle_{Path(args.filename).stem}.txt"
        cnf.write(out_file)
        print(f"Output written to: {out_file}")
        return

    # we want to solve it ourselfs
    solver = DPLLSolver()
    solvable = solver.solve(cnf)
    if solvable:
        print(f"There is a hamiltonian cycle in {args.filename}.")
    else:
        print(f"There is not a hamiltonian cycle in {args.filename}.")


if __name__ == "__main__":
    main()
