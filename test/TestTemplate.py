import unittest
import geopandas

from shapely import LineString

from Topology_Generator.LvNetworkBuilder import LineStringEndPair, LvNetworkBuilder

class Test(unittest.TestCase):

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
        network_builder = LvNetworkBuilder(lv_lines_geo_df, self.lv_mv_geo_df)
        starting_points = network_builder.extract_lv_lines_connected_to_mv_lv_station()

        # Assert
        self.assertEqual(len(starting_points), 1)
        self.assertEqual(len(starting_points[0].starting_lines), 2)
        self.assertListEqual(starting_points[0].starting_lines, [LineStringEndPair(line_1, False, 0), LineStringEndPair(line_2, False, 1)])

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

        network_builder = LvNetworkBuilder(lv_lines_geo_df, self.lv_mv_geo_df)
        starting_points = network_builder.extract_lv_lines_connected_to_mv_lv_station()

        # Execute
        lv_network_topology = network_builder.compute_lv_network_topology_from_lv_mv_station(starting_points[0].starting_lines[0])
        edge_list = [(u,v,d) for u,v,d in lv_network_topology.edges.data()]
        node_list = [n for n in lv_network_topology.nodes]

        # Assert
        self.assertEqual(len(node_list), 2)
        self.assertEqual(len(edge_list), 1)
        self.assertEqual(edge_list[0], (0, 1, {"length" : 2}))

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

        network_builder = LvNetworkBuilder(lv_lines_geo_df, self.lv_mv_geo_df)
        starting_points = network_builder.extract_lv_lines_connected_to_mv_lv_station()

        # Execute
        lv_network_topology = network_builder.compute_lv_network_topology_from_lv_mv_station(starting_points[0].starting_lines[0])
        edge_list = [(u,v,d) for u,v,d in lv_network_topology.edges.data()]

        # Assert
        self.assertEqual(len(lv_network_topology.nodes), 4)
        self.assertEqual(len(edge_list), 3)
        self.assertListEqual(edge_list, [(0, 1, {"length" : 1}), (1, 2, {"length" : 2}), (1, 3, {"length" : 1})])

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

        network_builder = LvNetworkBuilder(lv_lines_geo_df, self.lv_mv_geo_df)
        starting_points = network_builder.extract_lv_lines_connected_to_mv_lv_station()

        # Execute
        lv_network_topology = network_builder.compute_lv_network_topology_from_lv_mv_station(starting_points[0].starting_lines[0])
        edge_list = [(u,v,d) for u,v,d in lv_network_topology.edges.data()]

        # Assert
        self.assertEqual(len(lv_network_topology.nodes), 6)
        self.assertEqual(len(edge_list), 6)
        self.assertListEqual(edge_list, [(0, 1, {"length" : 1}), (1, 2, {"length" : 3}), (1, 4, {"length" : 1}), (2, 3, {"length" : 1}), (2, 4, {"length" : 2}), (4, 5, {"length" : 1}) ])

if __name__ == '__main__':
    unittest.main()