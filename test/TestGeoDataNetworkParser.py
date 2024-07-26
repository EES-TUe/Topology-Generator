import unittest
import geopandas

from shapely import LineString, Point
from Topology_Generator.AllianderGeoDataNetworkParser import AllianderGeoDataNetworkParser
from Topology_Generator.EnexisGeoDataNetworkParser import EnexisGeoDataNetworkParser
from Topology_Generator.dataclasses import NavigationLineString

class TestGeoDataNetworkParser(unittest.TestCase):

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
        nav_line_strings = network_parser.extract_lv_lines_connected_to_mv_lv_station_at_point(Point(0,1))

        # Assert
        self.assertEqual(len(nav_line_strings), 3)
        self.assertEqual(nav_line_strings[0].index, 0)
        self.assertEqual(nav_line_strings[0].line_string, line_1)
        self.assertFalse(nav_line_strings[0].first_point_end)

if __name__ == '__main__':
    unittest.main()