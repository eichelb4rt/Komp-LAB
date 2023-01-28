import numpy as np

from graph import Graph, Edge, reverse_edge
import itertools


def can_jump(pos_x: np.ndarray, pos_y: np.ndarray) -> bool:
    """Returns if a knight can jump from position x to position y."""

    diff = np.abs(pos_x - pos_y)
    n_dims = diff.shape[0]
    n_2s = np.count_nonzero(diff == 2)
    n_1s = np.count_nonzero(diff == 1)
    n_0s = np.count_nonzero(diff == 0)
    # a knight can jump 2 in 1 direction, 1 in 1 direction, and 0 in all others
    return n_2s == 1 and n_1s == 1 and n_0s == n_dims - 2


def knight_graph(n_dims: int, width: int, skip_positions: list[tuple[int]] = []) -> Graph:
    # build nodes
    coords_to_node: dict[tuple[int], int] = {position: node for node, position in enumerate(itertools.product(range(width), repeat=n_dims), start=1) if position not in skip_positions}
    nodes = set(coords_to_node.values())

    # build edges
    edges: list[Edge] = []
    # 2 n-dimensional coordinates
    for positions_xy in itertools.product(range(width), repeat=2 * n_dims):
        # first n_dims entries are x positions
        pos_x = np.array(positions_xy[:n_dims])
        # next n_dims entries are y positions
        pos_y = np.array(positions_xy[n_dims:])
        # we don't need to look at the same edge
        if np.all(pos_x == pos_y):
            continue
        # we don't want any of the skipped nodes
        if tuple(pos_x) in skip_positions or tuple(pos_y) in skip_positions:
            continue
        if can_jump(pos_x, pos_y):
            new_edge = (coords_to_node[tuple(pos_x)], coords_to_node[tuple(pos_y)])
            # edges are undirected
            if new_edge not in edges and reverse_edge(new_edge) not in edges:
                edges.append(new_edge)

    # build graph
    return Graph.from_edges(nodes, edges)


def main():
    n_dims = 3
    width = 3
    skip_nodes = [
        (0, 1, 1),
        (1, 1, 1),
        (2, 1, 1)
    ]
    graph = knight_graph(n_dims, width, skip_nodes)
    out_file = f"inputs/graph_knight_{n_dims}d_{width}w.txt"
    graph.write(out_file)
    print(f"Output written to: {out_file}")


if __name__ == "__main__":
    main()
