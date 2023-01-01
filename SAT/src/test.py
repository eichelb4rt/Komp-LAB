import argparse
from collections.abc import Callable

import graph


class TestAction(argparse.Action):
    """This class is for the test flag."""

    def __init__(self, option_strings, dest, test_function: Callable[[], None], **kwargs):
        self._test_function = test_function
        super().__init__(option_strings, dest, nargs=0, default=argparse.SUPPRESS, **kwargs)

    def __call__(self, parser, namespace, values, option_string, **kwargs):
        # if testing flag was set, ignore everything else and just test
        self._test_function()
        parser.exit()

    @classmethod
    def build(cls, test_function: Callable[[], None]):
        """Returns test action that can be used as an actual argparse action. Basically returns partial function."""

        return lambda option_strings, dest, **kwargs: TestAction(option_strings, dest, test_function, **kwargs)


def test_graphs():
    nodes_0 = {1, 3, 5, 7, 9}
    edges_0 = [
        (1, 3),
        (1, 5),
        (1, 7),
        (7, 9)
    ]
    graph_0 = graph.Graph.from_edges(nodes_0, edges_0)

    nodes_1 = {1, 3, 5}
    edges_1 = [
        (1, 3),
        (1, 5)
    ]
    graph_1 = graph.Graph.from_edges(nodes_1, edges_1)

    nodes_2 = {1, 3, 4}
    edges_2 = [
        (1, 3),
        (1, 4)
    ]
    graph_2 = graph.Graph.from_edges(nodes_2, edges_2)

    edges_3 = [
        (1, 3)
    ]
    graph_3 = graph.Graph.from_edges(nodes_1, edges_3)

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

    print("Graph test: all tests passed.")


if __name__ == "__main__":
    test_graphs()
