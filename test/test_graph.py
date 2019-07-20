import pytest
import unittest

from pelita.graph import (Graph, NoPathException, diff_pos, iter_adjacencies,
                          manhattan_dist, move_pos)
from pelita.layout import parse_layout


# some directions that are used in the tests
north = (0, -1)
south = (0, 1)
west  = (-1, 0)
east  = (1, 0)
stop  = (0, 0)


class TestStaticmethods:

    def test_new_pos(self):
        assert move_pos((1, 1), north) == (1, 0)
        assert move_pos((1, 1), south) == (1, 2)
        assert move_pos((1, 1), east) == (2, 1)
        assert move_pos((1, 1), west) == (0, 1)
        assert move_pos((1, 1), stop) == (1, 1)
        assert move_pos((0, 0), (1, 1)) == (1, 1)

    def test_diff_pos(self):
        assert north == diff_pos((1, 1), (1, 0))
        assert south == diff_pos((1, 1), (1, 2))
        assert east == diff_pos((1, 1), (2, 1))
        assert west == diff_pos((1, 1), (0, 1))
        assert stop == diff_pos((1, 1), (1, 1))

    def test_diff_pos_arbitrary(self):
        vectors = [(0, 0), (0, 1), (-1, 1), (-2, 3)]
        orig = (1, 1)
        for vec in vectors:
            new = move_pos(orig, vec)
            assert vec == diff_pos(orig, new)

    def test_manhattan_dist(self):
        assert 0 == manhattan_dist((0, 0), (0, 0))
        assert 0 == manhattan_dist((1, 1), (1, 1))
        assert 0 == manhattan_dist((20, 20), (20, 20))

        assert 1 == manhattan_dist((0, 0), (1, 0))
        assert 1 == manhattan_dist((0, 0), (0, 1))
        assert 1 == manhattan_dist((1, 0), (0, 0))
        assert 1 == manhattan_dist((0, 1), (0, 0))

        assert 2 == manhattan_dist((0, 0), (1, 1))
        assert 2 == manhattan_dist((1, 1), (0, 0))
        assert 2 == manhattan_dist((1, 0), (0, 1))
        assert 2 == manhattan_dist((0, 1), (1, 0))
        assert 2 == manhattan_dist((0, 0), (2, 0))
        assert 2 == manhattan_dist((0, 0), (0, 2))
        assert 2 == manhattan_dist((2, 0), (0, 0))
        assert 2 == manhattan_dist((0, 2), (0, 0))

        assert 4 == manhattan_dist((1, 2), (3, 4))

    def test_iter_adjacencies(self):
        def onedim_lattice(n, max_size):
            return [neighbour for neighbour in [n - 1, n + 1] if abs(neighbour) <= max_size]

        # starting at 0, we’ll get all 21 points:
        adjs0 = list(iter_adjacencies([0], lambda n: onedim_lattice(n, 10)))
        assert 21 == len(adjs0)
        unittest.TestCase().assertCountEqual(range(-10, 11), dict(adjs0).keys())

        # starting at 11, we’ll get 22 points
        adjs1 = list(iter_adjacencies([11], lambda n: onedim_lattice(n, 10)))
        assert 22 == len(adjs1)
        unittest.TestCase().assertCountEqual(range(-10, 12), dict(adjs1).keys())

        # starting at 12, we’ll get 1 point
        adjs2 = list(iter_adjacencies([12], lambda n: onedim_lattice(n, 10)))
        assert 1 == len(adjs2)
        assert [(12, [])] == list(adjs2)

        # starting at [0, 12], we’ll get adjs0 | adjs2
        adjs3 = list(iter_adjacencies([0, 12], lambda n: onedim_lattice(n, 10)))
        assert 22 == len(adjs3)
        unittest.TestCase().assertCountEqual(adjs0 + adjs2, adjs3)

class TestGraph:
    def test_pos_within(self):
        test_layout = (
        """ ##################
            #0#.  .  # .     #
            #2#####    #####1#
            #     . #  .  .#3#
            ################## """)
        layout = parse_layout(test_layout)
        graph = Graph(layout['bots'][0], layout['walls'])

        assert not ((0, 0) in graph)
        with pytest.raises(NoPathException):
            graph.pos_within((0, 0), 0)
        assert not ((6, 2) in graph)
        with pytest.raises(NoPathException):
            graph.pos_within((6, 2), 0)

        assert (1, 1) in graph
        unittest.TestCase().assertCountEqual([(1, 1)], graph.pos_within((1, 1), 0))
        target = [(1, 1), (1, 2), (1,3), (2, 3), (3, 3)]
        unittest.TestCase().assertCountEqual(target, graph.pos_within((1, 1), 5))
        # check that distance in a_star is working properly
        for pos in target:
            assert len(graph.a_star((1, 1), pos)) < 5
        for pos in set(graph).difference(target):
            assert len(graph.a_star((1, 1), pos)) >= 5

    def test_basic_adjacency_list(self):
        test_layout = (
        """ ######
            #    #
            ###### """)
        layout = parse_layout(test_layout)
        graph = Graph((1, 1), layout['walls'])
        target = { (4, 1): [(4, 1), (3, 1)],
                   (1, 1): [(2, 1), (1, 1)],
                   (2, 1): [(3, 1), (2, 1), (1, 1)],
                   (3, 1): [(4, 1), (3, 1), (2, 1)]}

        sorted_g = {k: sorted(v) for k, v in graph.items()}
        sorted_t = {k: sorted(v) for k, v in target.items()}
        assert sorted_g == sorted_t

    def test_extended_adjacency_list(self):
        test_layout = (
        """ ##################
            #0#.  .  # .     #
            # #####    ##### #
            #     . #  .  .#1#
            ################## """)
        layout = parse_layout(test_layout)
        graph = Graph((1, 1), layout['walls'])

        adjacency_target = {(7, 3): [(7, 2), (7, 3), (6, 3)],
         (1, 3): [(1, 2), (2, 3), (1, 3)],
         (12, 1): [(13, 1), (12, 1), (11, 1)],
         (16, 2): [(16, 3), (16, 1), (16, 2)],
         (15, 1): [(16, 1), (15, 1), (14, 1)],
         (5, 1): [(6, 1), (5, 1), (4, 1)],
         (10, 3): [(10, 2), (11, 3), (10, 3), (9, 3)],
         (7, 2): [(7, 3), (7, 1), (8, 2), (7, 2)],
         (1, 2): [(1, 3), (1, 1), (1, 2)],
         (3, 3): [(4, 3), (3, 3), (2, 3)],
         (13, 3): [(14, 3), (13, 3), (12, 3)],
         (8, 1): [(8, 2), (8, 1), (7, 1)],
         (16, 3): [(16, 2), (16, 3)],
         (6, 3): [(7, 3), (6, 3), (5, 3)],
         (14, 1): [(15, 1), (14, 1), (13, 1)],
         (11, 1): [(12, 1), (11, 1), (10, 1)],
         (4, 1): [(5, 1), (4, 1), (3, 1)],
         (1, 1): [(1, 2), (1, 1)],
         (12, 3): [(13, 3), (12, 3), (11, 3)],
         (8, 2): [(8, 1), (9, 2), (8, 2), (7, 2)],
         (7, 1): [(7, 2), (8, 1), (7, 1), (6, 1)],
         (9, 3): [(9, 2), (10, 3), (9, 3)],
         (2, 3): [(3, 3), (2, 3), (1, 3)],
         (10, 1): [(10, 2), (11, 1), (10, 1)],
         (5, 3): [(6, 3), (5, 3), (4, 3)],
         (13, 1): [(14, 1), (13, 1), (12, 1)],
         (9, 2): [(9, 3), (10, 2), (9, 2), (8, 2)],
         (6, 1): [(7, 1), (6, 1), (5, 1)],
         (3, 1): [(4, 1), (3, 1)],
         (11, 3): [(12, 3), (11, 3), (10, 3)],
         (16, 1): [(16, 2), (16, 1), (15, 1)],
         (4, 3): [(5, 3), (4, 3), (3, 3)],
         (14, 3): [(14, 3), (13, 3)],
         (10, 2): [(10, 3), (10, 1), (10, 2), (9, 2)]}

        sorted_g = {k: sorted(v) for k, v in graph.items()}
        sorted_t = {k: sorted(v) for k, v in adjacency_target.items()}

        assert sorted_t == sorted_g

    def test_bfs_to_self(self):
        test_layout = (
        """ ############
            #0.     #.1#
            ############ """)
        layout = parse_layout(test_layout)
        graph = Graph((1, 1), layout['walls'])
        assert [] == graph.bfs((1,1), [(1, 1), (2, 1)])

    def test_a_star(self):
        test_layout = (
        """ ##################
            #02.# .  # .  #  #
            #   ###    ####1 #
            # ### . #  .  ##3#
            #                #
            ################## """)
        layout = parse_layout(test_layout)
        graph = Graph((1, 1), layout['walls'])

        #Test distance to middle from both sides
        assert 11 == len(graph.a_star((1, 1), (7, 2)))
        assert 12 == len(graph.a_star((2, 1), (7, 2)))
        assert 14 == len(graph.a_star((16, 1), (7, 2)))
        assert 15 == len(graph.a_star((15, 1), (7, 2)))    

        # Test basic assertions
        assert 0 == len(graph.a_star((1, 1), (1, 1)))
        assert 1 == len(graph.a_star((1, 1), (2, 1)))
        assert 1 == len(graph.a_star((2, 1), (1, 1)))

        # Test distance to middle from both sides
        assert 11 == len(graph.a_star((1, 1), (7, 2)))
        assert 12 == len(graph.a_star((2, 1), (7, 2)))
        assert 14 == len(graph.a_star((16, 1), (7, 2)))
        assert 15 == len(graph.a_star((15, 1), (7, 2)))

    def test_a_star2(self):
        test_layout = (
            """ ########
                #1#    #
                # # #0 #
                #      #
                ######## """ )
        layout = parse_layout(test_layout)
        graph = Graph((1, 1), layout['walls'])
        #Test distance to middle from both sides
        assert 7 == len(graph.a_star(layout['bots'][0], layout['bots'][1]))
        assert 7 == len(graph.a_star(layout['bots'][1], layout['bots'][0]))

    def test_a_star3(self):
        test_layout = (
            """
            ################################################################
            #0#                #    #         #                     #   #  #
            # ######### ######           #              #           ###    #
            # #            #   ######## ## ## #  #      #           #   #  #
            #   ############   # # #  #  #         ## ###############      #
            # #            # ### # #     # ###  ##        #         #### ###
            # ####### #### #   #   #  #  #       #                         #
            # #   1      #     ###   ##### ##      ############# ###########
            # #   #      # #   #   #     # ##    #   #                     #
            #    ######################### ##    ## ######### ##############
            ################################################################"""
        )
        layout = parse_layout(test_layout)
        graph = Graph((1, 1), layout['walls'])
        #Test distance to middle from both sides
        assert 15 == len(graph.a_star(layout['bots'][0], layout['bots'][1]))
        assert 15 == len(graph.a_star(layout['bots'][1], layout['bots'][0]))

    def test_a_star_left_right(self):
        def len_of_shortest_path(layout):
            layout = parse_layout(layout)
            graph = Graph((1, 1), layout['walls'])
            path = graph.a_star(layout['bots'][0], layout['bots'][1])
            return len(path)

        l1 = """
        ##################
        #  1  #    #  0  #
        #     #    #     #
        # #####    ##### #
        #                #
        ##################
        """

        l2 = """
        ##################
        #  0  #    #  1  #
        #     #    #     #
        # #####    ##### #
        #                #
        ##################
        """
        assert len_of_shortest_path(l1) == len_of_shortest_path(l2)

    def test_path_to_same_position(self):
        test_layout = (
        """ ##################
            #0#.  .  # .     #
            #2#####    #####1#
            #     . #  .  .#3#
            ################## """)
        layout = parse_layout(test_layout)
        graph = Graph((1, 1), layout['walls'])
        assert [] == graph.a_star((1, 1), (1, 1))
        assert [] == graph.bfs((1, 1), [(1, 1)])

    def test_bfs_exceptions(self):
        test_layout = (
        """ ############
            #0.     #.1#
            ############ """)
        layout = parse_layout(test_layout)
        # TODO: We cannot set up an unconnected graph currently
        graph = Graph((1, 1), layout['walls'])
        with pytest.raises(NoPathException):
            graph.bfs((1, 1), [(10, 1)])
        with pytest.raises(NoPathException):
            graph.bfs((1, 1), [(10, 1), (9, 1)])
        with pytest.raises(NoPathException):
            graph.bfs((0, 1), [(10, 1)])
        with pytest.raises(NoPathException):
            graph.bfs((1, 1), [(11, 1)])

    def test_a_star_exceptions(self):
        test_layout = (
        """ ############
            #0.     #.1#
            ############ """)
        layout = parse_layout(test_layout)
        # TODO: We cannot set up an unconnected graph currently
        graph = Graph((1, 1), layout['walls'])
        with pytest.raises(NoPathException):
            graph.a_star((1, 1), (10, 1))
        with pytest.raises(NoPathException):
            graph.a_star((0, 1), (10, 1))
        with pytest.raises(NoPathException):
            graph.a_star((1, 1), (11, 1))
