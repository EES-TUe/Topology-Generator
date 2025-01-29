import unittest
import geopandas

from shapely import LineString, Point
from Topology_Generator.AllianderGeoDataNetworkParser import AllianderGeoDataNetworkParser
from Topology_Generator.EnexisGeoDataNetworkParser import EnexisGeoDataNetworkParser
from Topology_Generator.dataclasses import NavigationLineString

class TestGeoDataNetworkParser(unittest.TestCase):

    def test_enexis_starting_lines_are_extracted_correctly(self):
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
        lv_mv_station = LineString([(0, 0),(2,0),(2,2),(0,2), (0,0)])
        lv_mv_geo_df = geopandas.GeoDataFrame(
            {
                "id": [1],
                "geometry": [lv_mv_station]
            }
        )

        # Execute
        network_parser = EnexisGeoDataNetworkParser(lv_lines_geo_df, lv_mv_geo_df)
        starting_points = network_parser.extract_lv_lines_connected_to_mv_lv_station()

        # Assert
        self.assertEqual(len(starting_points), 1)
        self.assertEqual(len(starting_points[0].starting_lines), 2)
        self.assertListEqual(starting_points[0].starting_lines, [NavigationLineString(line_1, False, 0), NavigationLineString(line_2, False, 1)])

    def test_alliander_starting_lines_are_extracted_correctly(self):
        # Arrange
        line_1 = LineString([(2,1), (3,1)])
        line_2 = LineString([(1,2), (1,3)])
        line_3 = LineString([(4,1), (5,1)])
        lv_mv_geo_df = geopandas.GeoDataFrame(
            {
                "id": [1],
                "geometry": Point(0,1)
            }
        )
        lv_lines_geo_df = geopandas.GeoDataFrame(
            {
                "id": [1, 2, 3],
                "geometry": [line_1, line_2, line_3]
            }
        )

        # Execute
        network_parser = AllianderGeoDataNetworkParser(lv_lines_geo_df, lv_mv_geo_df)
        starting_points = network_parser.extract_lv_lines_connected_to_mv_lv_station()

        # Assert
        self.assertEqual(len(starting_points), 1)
        self.assertEqual(len(starting_points[0].starting_lines), 2)
        self.assertListEqual(starting_points[0].starting_lines, [NavigationLineString(line_1, False, 0), NavigationLineString(line_2, False, 1)])

if __name__ == '__main__':
    unittest.main()