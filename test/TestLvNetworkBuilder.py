import unittest
import geopandas

from shapely import LineString, Polygon, Point
from Topology_Generator.AllianderGeoDataNetworkParser import AllianderGeoDataNetworkParser
from Topology_Generator.LvNetworkBuilder import LvNetworkBuilder
import networkx as nx

from Topology_Generator.dataclasses import NavigationLineString

class TestLvNetworkBuilder(unittest.TestCase):

    def setUp(self):
        lv_mv_station = Point(0,0)
        self.lv_mv_geo_df = geopandas.GeoDataFrame(
            {
                "id": [1],
                "geometry": [lv_mv_station]
            }
        )

        self.lv_stations_geo_df = geopandas.GeoDataFrame(
            {
                "id": [1],
                "geometry": [Point(100,2)]
            }
        )

        lv_line_strings = [
            LineString([(1,0), (50,1)]),
            LineString([(50,1), (50,52)]),
            LineString([(50,52), (53,55)]),
            LineString([(50,1), (100,2)]),
        ]



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
        network_parser = AllianderGeoDataNetworkParser(lv_lines_geo_df, self.lv_mv_geo_df)
        starting_points = network_parser.extract_lv_lines_connected_to_mv_lv_station_at_point(Point(0,0))

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

        network_parser = AllianderGeoDataNetworkParser(lv_lines_geo_df, self.lv_mv_geo_df)
        network_builder = LvNetworkBuilder(network_parser)

        # Execute
        lv_network_topology = network_builder.extract_lv_networks_and_topologies_at_point(Point(0,0))[0].network_topology
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

        network_parser = AllianderGeoDataNetworkParser(lv_lines_geo_df, self.lv_mv_geo_df)
        network_builder = LvNetworkBuilder(network_parser)

        # Execute
        lv_network_topology = network_builder.extract_lv_networks_and_topologies_at_point(Point(0,0))[0].network_topology
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

        network_parser = AllianderGeoDataNetworkParser(lv_lines_geo_df, self.lv_mv_geo_df)
        network_builder = LvNetworkBuilder(network_parser)

        # Execute
        lv_network_topology = network_builder.extract_lv_networks_and_topologies_at_point(Point(0,0))[0].network_topology
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

        network_parser = AllianderGeoDataNetworkParser(lv_lines_geo_df, self.lv_mv_geo_df, bag_data_geo_df)
        network_builder = LvNetworkBuilder(network_parser)

        # Execute
        lv_network_topology = network_builder.extract_lv_networks_and_topologies_at_point(Point(0,0))[0].network_topology
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

        network_parser = AllianderGeoDataNetworkParser(lv_lines_geo_df, self.lv_mv_geo_df, bag_data_geo_df)
        network_builder = LvNetworkBuilder(network_parser)

        # Execute
        lv_network_topologies = network_builder.extract_lv_networks_and_topologies_at_point(Point(0,0))
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
        
                network_parser = AllianderGeoDataNetworkParser(lv_lines_geo_df, self.lv_mv_geo_df)
                network_builder = LvNetworkBuilder(network_parser)

                # Execute
                lv_network_topologies = network_builder.extract_lv_networks_and_topologies_at_point(Point(0,0))
                lv_network_topologiy = lv_network_topologies[0]
                edge_list = [(u,v,d) for u,v,d in lv_network_topologiy.network_topology.edges.data()]

                # Assert
                self.assertEqual(len(lv_network_topologies), 1)
                self.assertEqual(len(edge_list), 5)
                self.assertGreater(len(nx.find_cycle(lv_network_topologiy.network_topology)), 0)

    def test_lv_cables_are_added_according_to_design_rules(self):
        station = Point(0,4)
        line_1 = LineString([(0,4), (8,4)])
        line_2 = LineString([(8,4), (8,8)])
        line_3 = LineString([(8,4), (8,0)])
        houses = []
        houses.append(Polygon([(1,5), (1,6), (2,6), (2,5)])) # Hoekwoning
        houses.append(Polygon([(2,5), (2,6), (3,6), (3,5)])) # Rijtjeshuis
        houses.append(Polygon([(3,5), (3,6), (4,6), (4,5)])) # Hoekwoning
        houses.append(Polygon([(6,3), (7,3), (7,2), (6,2)])) # Hoekwoning
        houses.append(Polygon([(6,2), (6,1), (7,1), (7,2)])) # Rijtjeshuis
        houses.append(Polygon([(5,2), (6,2), (6,1), (5,1)])) # Hoekwoning
        houses.append(Polygon([(6,1), (6,0), (7,0), (7,1)])) # Hoekwoning
        houses.append(Polygon([(9,2), (10,2), (10,1), (9,1)])) # Vrijstaand
        houses.append(Polygon([(9,5), (9,6), (10,6), (10,5)])) # 2 onder 1 kap
        houses.append(Polygon([(9,6), (9,7), (10,7), (10,6)])) # 2 onder 1 kap
        houses.append(Polygon([(6,6), (6,7), (7,7), (7,6)])) # Massionette
        houses.append(Polygon([(6,7), (6,8), (7,8), (7,7)])) # Appartement

        lv_mv_geo_df = geopandas.GeoDataFrame(
            {
                "id": [1],
                "geometry": [station]
            }
        )

        lv_lines_geo_df = geopandas.GeoDataFrame(
            {
                "id": list(range(3)),
                "geometry": [line_1, line_2, line_3]
            }
        )
        amount_of_dwellings = [1 for i in range(len(houses))]
        amount_of_dwellings[10] = 3
        amount_of_dwellings[11] = 15
        bag_data_geo_df = geopandas.GeoDataFrame(
            {
                "id": list(range(len(houses))),
                "geometry": [houses],
                "gebruiksdoel" : ["woonfunctie" for i in range(len(houses))],
                "bouwjaar" : ["1980" for i in range(len(houses))],
                "aantal_verblijfsobjecten" : amount_of_dwellings
            }
        )
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()