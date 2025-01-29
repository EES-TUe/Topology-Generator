import unittest
import geopandas

from shapely import LineString, Polygon
from Topology_Generator.EnexisGeoDataNetworkParser import EnexisGeoDataNetworkParser
from Topology_Generator.LvNetworkBuilder import LvNetworkBuilder
import networkx as nx

from Topology_Generator.dataclasses import NavigationLineString

class TestLvNetworkBuilder(unittest.TestCase):

    def setUp(self):
        lv_mv_station = LineString([(0, 0),(2,0),(2,2),(0,2), (0,0)])
        self.lv_mv_geo_df = geopandas.GeoDataFrame(
            {
                "id": [1],
                "geometry": [lv_mv_station]
            }
        )

    def test_starting_lines_are_extracted_correctly(self):
        # Arrange
        line_1 = LineString([(2,1), (3,1)])
        line_2 = LineString([(1,2), (1,3)])
        line_3 = LineString([(4,1), (5,1)])
        lv_lines_geo_df = geopandas.GeoDataFrame(
            {
                "id": [1, 2, 3],
                "geometry": [line_1, line_2, line_3]
            }
        )

        # Execute
        network_parser = EnexisGeoDataNetworkParser(lv_lines_geo_df, self.lv_mv_geo_df)
        starting_points = network_parser.extract_lv_lines_connected_to_mv_lv_station()

        # Assert
        self.assertEqual(len(starting_points), 1)
        self.assertEqual(len(starting_points[0].starting_lines), 2)
        self.assertListEqual(starting_points[0].starting_lines, [NavigationLineString(line_1, False, 0), NavigationLineString(line_2, False, 1)])

    def test_straigt_line_topology_is_correctly_computed(self):
        # Arrange
        line_1 = LineString([(2,1), (3,1)])
        line_2 = LineString([(3,1), (4,1)])
        lv_lines_geo_df = geopandas.GeoDataFrame(
            {
                "id": [1, 2],
                "geometry": [line_1, line_2]
            }
        )

        network_parser = EnexisGeoDataNetworkParser(lv_lines_geo_df, self.lv_mv_geo_df)
        network_builder = LvNetworkBuilder(network_parser)

        # Execute
        lv_network_topology = network_builder.extract_network_and_topologies()[0].network_topology
        edge_list = [(u,v,d) for u,v,d in lv_network_topology.edges.data()]
        node_list = [n for n in lv_network_topology.nodes]

        # Assert
        self.assertEqual(len(node_list), 2)
        self.assertEqual(len(edge_list), 1)
        self.assertEqual(edge_list[0], (0, 1, {"amount_of_connections" : 0, "length" : 2}))

    def test_branch_line_topology_is_correctly_computed(self):
        # Arrange
        line_1 = LineString([(2,1), (3,1)])
        line_2 = LineString([(3,1), (5,1)])
        line_3 = LineString([(3,1), (3,0)])
        lv_lines_geo_df = geopandas.GeoDataFrame(
            {
                "id": [1, 2, 3],
                "geometry": [line_1, line_2, line_3]
            }
        )

        network_parser = EnexisGeoDataNetworkParser(lv_lines_geo_df, self.lv_mv_geo_df)
        network_builder = LvNetworkBuilder(network_parser)

        # Execute
        lv_network_topology = network_builder.extract_network_and_topologies()[0].network_topology
        edge_list = [(u,v,d) for u,v,d in lv_network_topology.edges.data()]

        # Assert
        self.assertEqual(len(lv_network_topology.nodes), 4)
        self.assertEqual(len(edge_list), 3)
        self.assertListEqual(edge_list, [(0, 1, {"amount_of_connections" : 0, "length" : 1}), (1, 2, {"amount_of_connections" : 0, "length" : 2}), (1, 3, {"amount_of_connections" : 0, "length" : 1})])

    def test_loop_line_topology_is_correctly_computed(self):
        # Arrange
        line_1 = LineString([(2,1), (3,1)])
        line_2 = LineString([(3,1), (5,1), (5,2)])
        line_3 = LineString([(5,2), (6,2)])
        line_4 = LineString([(5,2), (3,2)])
        line_5 = LineString([(3,1), (3,2)])
        line_6 = LineString([(3,2), (3,3)])
        lv_lines_geo_df = geopandas.GeoDataFrame(
            {
                "id": [1, 2, 3, 4, 5, 6],
                "geometry": [line_1, line_2, line_3, line_4, line_5, line_6]
            }
        )

        network_parser = EnexisGeoDataNetworkParser(lv_lines_geo_df, self.lv_mv_geo_df)
        network_builder = LvNetworkBuilder(network_parser)

        # Execute
        lv_network_topology = network_builder.extract_network_and_topologies()[0].network_topology
        edge_list = [(u,v,d) for u,v,d in lv_network_topology.edges.data()]

        # Assert
        self.assertEqual(len(lv_network_topology.nodes), 6)
        self.assertEqual(len(edge_list), 6)
        self.assertListEqual(edge_list, [(0, 1, {"amount_of_connections" : 0, "length" : 1}), (1, 2, {"amount_of_connections" : 0, "length" : 3}), (1, 4, {"amount_of_connections" : 0, "length" : 1}), (2, 3, {"amount_of_connections" : 0, "length" : 1}), (2, 4, {"amount_of_connections" : 0, "length" : 2}), (4, 5, {"amount_of_connections" : 0, "length" : 1}) ])

    def test_houses_are_counted_as_connections(self):
         # Arrange
        line_1 = LineString([(2,1), (3,1)])
        line_2 = LineString([(3,1), (5,1)])
        line_3 = LineString([(3,1), (3,0)])
        lv_lines_geo_df = geopandas.GeoDataFrame(
            {
                "id": [1, 2, 3],
                "geometry": [line_1, line_2, line_3]
            }
        )
        house = Polygon([(2.1, 1.1), (2.9, 1.1), (2.9, 2.1), (2.1, 2.1)])
        bag_data_geo_df = geopandas.GeoDataFrame(
            {
                "id": [1],
                "geometry": [house],
                "gebruiksdoel" : ["woonfunctie"]
            }
        )

        network_parser = EnexisGeoDataNetworkParser(lv_lines_geo_df, self.lv_mv_geo_df, bag_data_geo_df)
        network_builder = LvNetworkBuilder(network_parser)

        # Execute
        lv_network_topology = network_builder.extract_network_and_topologies()[0].network_topology
        edge_list = [(u,v,d) for u,v,d in lv_network_topology.edges.data()]

        # Assert
        self.assertEqual(len(lv_network_topology.nodes), 4)
        self.assertEqual(len(edge_list), 3)
        self.assertListEqual(edge_list, [(0, 1, {"amount_of_connections" : 1, "length" : 1}), (1, 2, {"amount_of_connections" : 0, "length" : 2}), (1, 3, {"amount_of_connections" : 0, "length" : 1})])

    def test_houses_are_only_counted_once_among_different_lv_lines(self):
         # Arrange
        line_1 = LineString([(2,1), (3,1)])
        line_2 = LineString([(3,1), (5,1)])
        line_3 = LineString([(3,1), (3,0)])
        line_4 = LineString([(2,2), (2,4)])
        lv_lines_geo_df = geopandas.GeoDataFrame(
            {
                "id": [1, 2, 3, 4],
                "geometry": [line_1, line_2, line_3, line_4]
            }
        )
        house = Polygon([(2.1, 1.1), (2.9, 1.1), (2.9, 2.1), (2.1, 2.1)])
        bag_data_geo_df = geopandas.GeoDataFrame(
            {
                "id": [1],
                "geometry": [house],
                "gebruiksdoel" : ["woonfunctie"]
            }
        )

        network_parser = EnexisGeoDataNetworkParser(lv_lines_geo_df, self.lv_mv_geo_df, bag_data_geo_df)
        network_builder = LvNetworkBuilder(network_parser)

        # Execute
        lv_network_topologies = network_builder.extract_network_and_topologies()
        edge_list = []
        for lv_network_topology in lv_network_topologies:
            edge_list.extend([(u,v,d) for u,v,d in lv_network_topology.network_topology.edges.data()])

        # Assert
        self.assertEqual(len(lv_network_topologies), 2)
        self.assertEqual(len(edge_list), 4)
        self.assertEqual(1, sum([d["amount_of_connections"] for u, v, d in edge_list]))

    def test_when_lv_network_loops_back_it_stops(self):

        test_examples = [ 
            [LineString([(2,1), (3,1)]), LineString([(3,1), (5,1)]), LineString([(3,1), (3,0)]), LineString([(3,0), (2,0)]), LineString([(3,0), (4,0)])],
            [LineString([(2,1), (3,2)]), LineString([(3,2), (5,2)]), LineString([(3,2), (3,1)]), LineString([(3,1), (2,1)]), LineString([(3,1), (4,1)])]
        ]

        for i in range(0, len(test_examples)):
            with self.subTest(i=i):
                param = test_examples[i]

                # Arrange
                lv_lines_geo_df = geopandas.GeoDataFrame(
                    {
                        "id": [i for i in range(0, len(param))],
                        "geometry": param
                    }
                )
        
                network_parser = EnexisGeoDataNetworkParser(lv_lines_geo_df, self.lv_mv_geo_df)
                network_builder = LvNetworkBuilder(network_parser)

                # Execute
                lv_network_topologies = network_builder.extract_network_and_topologies()
                lv_network_topologiy = lv_network_topologies[0]
                edge_list = [(u,v,d) for u,v,d in lv_network_topologiy.network_topology.edges.data()]

                # Assert
                self.assertEqual(len(lv_network_topologies), 1)
                self.assertEqual(len(edge_list), 5)
                self.assertGreater(len(nx.find_cycle(lv_network_topologiy.network_topology)), 0)

if __name__ == '__main__':
    unittest.main()