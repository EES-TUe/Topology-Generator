from typing import List
import unittest
import esdl
import geopandas
from shapely import LineString, Polygon, Point

from Topology_Generator.AllianderGeoDataNetworkParser import AllianderGeoDataNetworkParser
from Topology_Generator.EsdlHelperFunctions import EsdlHelperFunctions
from Topology_Generator.GeoDataNetworkParser import GeneratorCableCase
from Topology_Generator.MvNetworkBuilder import MvNetworkBuilder

class TestLvNetworkBuilder(unittest.TestCase):

    def setUp(self):
        self.df_hv_mv_station = geopandas.GeoDataFrame(
            {
                "id": [1],
                "geometry": [Point((1,1))]
            }
        )

        self.df_bag_data = geopandas.GeoDataFrame(
            {
                "id": [1,2],
                "geometry": [Polygon([(0, 0), (2, 0), (2, 2), (2, 0)]), Polygon([(38, 29), (40, 29), (40, 31), (38, 31)])],
                "bouwjaar" : [2003, 1984],
                "gebruiksdoel" : ["woonfunctie", "woonfunctie"]
            }
        )
        self.df_bag_data.set_geometry('geometry')

        self.mv_lines = [LineString([(2, 1), (220, 1)]),
                LineString([(220, 1), (500, 1)]),
                LineString([(500, 1.1), (400, 1.1)]),
                LineString([(400, 1.1), (400, 300)]),
                LineString([(390, 300), (200, 200)]),
                LineString([(200, 200), (1, 2)])]

        self.mv_lines_geo_df = geopandas.GeoDataFrame(
            {
                "id": [i for i in range(0, len(self.mv_lines))],
                "geometry": self.mv_lines
            }
        )

        self.lv_mv_geo_df = geopandas.GeoDataFrame(
            {
                "id": [1],
                "geometry": [Point((395,300))]
            }
        )

    def esdl_cable_geometry_equal(self, cable_a : esdl.Line, cable_b : esdl.Line):
        for point_a in cable_a.point:
            not_present = True
            for point_b in cable_b.point:
                if point_a.lat == point_b.lat and point_a.lon == point_b.lon:
                    not_present = False
            if not_present:
                return False
        return True
    
    def esdl_cable_in_collection(self, cable_a : esdl.Line, collection : List[esdl.Line]):
        ret_val = any(self.esdl_cable_geometry_equal(cable, cable_a) for cable in collection)
        return ret_val

    def test_mv_network_is_build_correctly(self):
        # Arrange
        parser = AllianderGeoDataNetworkParser(geopandas.GeoDataFrame(), self.lv_mv_geo_df, self.df_bag_data, self.mv_lines_geo_df, self.df_hv_mv_station, GeneratorCableCase.AVG)
        network_builder = MvNetworkBuilder(parser, 0, 0, 520, 520)

        # Execute
        mv_network = network_builder.generate_a_mv_network("unittest")

        # Assert
        assets = mv_network.instance[0].area.asset
        electricity_cables = EsdlHelperFunctions.get_all_esdl_objects_from_type(assets, esdl.ElectricityCable)
        transformers = EsdlHelperFunctions.get_all_esdl_objects_from_type(assets, esdl.Transformer)

        self.assertEqual(len(electricity_cables), 6)
        self.assertEqual(len(transformers), 3)

        expected_cable_types = ["GPLK_Cu_70", "GPLK_Al_150", "XLPE_Al_150"]
        self.assertTrue(all(cable.assetType in expected_cable_types for cable in electricity_cables))
        self.assertTrue(len([cable.assetType == "GPLK_Al_150" for cable in electricity_cables]), 3)
        self.assertTrue(len([cable.assetType == "XLPE_Al_150" for cable in electricity_cables]), 3)

        expected_esdl_lines = []
        for line in self.mv_lines:
            esdl_line = esdl.Line()
            for p in line.coords:
                esdl_line.point.append(esdl.Point(lat=p[0], lon=p[1], CRS="WGS84"))
            expected_esdl_lines.append(esdl_line)

        self.assertTrue(all(self.esdl_cable_in_collection(cable.geometry, expected_esdl_lines) for cable in electricity_cables))

    def test_when_no_mv_network_within_bouds_exception_is_thrown(self):
        # Arrange
        parser = AllianderGeoDataNetworkParser(geopandas.GeoDataFrame(), self.lv_mv_geo_df, self.df_bag_data, self.mv_lines_geo_df, self.df_hv_mv_station, GeneratorCableCase.AVG)
        network_builder = MvNetworkBuilder(parser, 0, 0, 5, 5)

        # Execute
        with self.assertRaises(ValueError):
            mv_network = network_builder.generate_a_mv_network("unittest")

    def test_given_mv_cables_not_connected_when_cables_are_close_then_new_trafo_is_added(self):
        # Arrange
        mv_lines = [LineString([(2, 1), (220, 1)]),
                 LineString([(220, 1), (500, 1)]),
                 LineString([(500, 1.1), (400, 1.1)]),
                 LineString([(400, 1.1), (1, 1.1)])]
        
        df_mv_lines = geopandas.GeoDataFrame(
            {
                "id": [i for i in range(0, len(mv_lines))],
                "geometry": mv_lines
            }
        )

        parser = AllianderGeoDataNetworkParser(geopandas.GeoDataFrame(), self.lv_mv_geo_df, self.df_bag_data, df_mv_lines, self.df_hv_mv_station, GeneratorCableCase.AVG)
        network_builder = MvNetworkBuilder(parser, 0, 0, 550, 550)

        # Execute
        mv_network = network_builder.generate_a_mv_network("unittest")

         # Assert
        assets = mv_network.instance[0].area.asset
        electricity_cables = EsdlHelperFunctions.get_all_esdl_objects_from_type(assets, esdl.ElectricityCable)
        transformers = EsdlHelperFunctions.get_all_esdl_objects_from_type(assets, esdl.Transformer)

        self.assertEqual(len(electricity_cables), 4)
        self.assertEqual(len(transformers), 2)

    def test_given_mv_cables_not_connected_when_mv_station_is_present_then_new_trafo_is_added(self):
        # Arrange
        mv_lines = [LineString([(2, 1), (220, 1)]),
                 LineString([(220, 1), (500, 1)]),
                 LineString([(500, 1.1), (400, 1.1)]),
                 LineString([(400, 1.1), (1, 1.1)])]

        df_mv_lines = geopandas.GeoDataFrame(
            {
                "id": [i for i in range(0, len(mv_lines))],
                "geometry": mv_lines
            }
        )

        df_bag_data = geopandas.GeoDataFrame(
            {
                "id": [1,2],
                "geometry": [Polygon([(0, 0), (2, 0), (2, 2), (2, 0)]), Polygon([(500, 0), (510, 0), (510, 2), (490, 2)])],
                "bouwjaar" : [2003, 1984]
            }
        )

        lv_mv_geo_df = geopandas.GeoDataFrame(
            {
                "id": [1],
                "geometry": [Point((500,1))]
            }
        )

        parser = AllianderGeoDataNetworkParser(geopandas.GeoDataFrame(), lv_mv_geo_df, df_bag_data, df_mv_lines, self.df_hv_mv_station, GeneratorCableCase.AVG)
        network_builder = MvNetworkBuilder(parser, 0, 0, 520, 520)

        # Execute
        mv_network = network_builder.generate_a_mv_network("unittest")

         # Assert
        assets = mv_network.instance[0].area.asset
        electricity_cables = EsdlHelperFunctions.get_all_esdl_objects_from_type(assets, esdl.ElectricityCable)
        transformers = EsdlHelperFunctions.get_all_esdl_objects_from_type(assets, esdl.Transformer)

        self.assertEqual(len(electricity_cables), 4)
        self.assertEqual(len(transformers), 2)
        self.assertEqual(transformers[0].commissioningDate.year, 1984)
        self.assertEqual(transformers[1].commissioningDate.year, 2003)

if __name__ == '__main__':
    unittest.main()