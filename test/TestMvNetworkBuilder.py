from typing import List
import threading
import unittest
import esdl
import geopandas
from shapely import LineString, Polygon, Point

from Topology_Generator.AllianderGeoDataNetworkParser import AllianderGeoDataNetworkParser
from Topology_Generator.EsdlHelperFunctions import EsdlHelperFunctions
from Topology_Generator.GeoDataNetworkParser import GeneratorCableCase
from Topology_Generator.GeometryHelperFunctions import GeometryHelperFunctions
from Topology_Generator.MvNetworkBuilder import MvNetworkBuilder

class TestMvNetworkBuilder(unittest.TestCase):

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
                "geometry": [Polygon([(0, 0), (2, 0), (2, 2), (2, 0)]), Polygon([(380, 290), (400, 290), (400, 310), (380, 310)])],
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

    def generate_mv_network_within_time_limit(self, network_builder : MvNetworkBuilder, time_limit_s : float = 10.0) -> esdl.EnergySystem:
        result = {}
        def generate():
            try:
                result["network"] = network_builder.generate_a_mv_network("unittest")
            except Exception as e:
                result["error"] = e
        thread = threading.Thread(target=generate, daemon=True)
        thread.start()
        thread.join(time_limit_s)
        self.assertFalse(thread.is_alive(), "MV network generation did not finish within the time limit")
        if "error" in result:
            raise result["error"]
        return result["network"]

    def create_parser_with_extra_mv_lines(self, extra_mv_lines : List[LineString]) -> AllianderGeoDataNetworkParser:
        mv_lines = self.mv_lines + extra_mv_lines
        df_mv_lines = geopandas.GeoDataFrame(
            {
                "id": [i for i in range(0, len(mv_lines))],
                "geometry": mv_lines
            }
        )
        return AllianderGeoDataNetworkParser(geopandas.GeoDataFrame(), self.lv_mv_geo_df, self.df_bag_data, df_mv_lines, self.df_hv_mv_station, GeneratorCableCase.AVG)

    def assert_no_connections_outside_network(self, assets : List[esdl.Asset]):
        connected_assets = [connected_port.energyasset for asset in assets for port in asset.port for connected_port in port.connectedTo]
        self.assertTrue(all(connected_asset in assets for connected_asset in connected_assets))

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
        self.assertEqual(sum(cable.assetType == "GPLK_Al_150" for cable in electricity_cables), 2)
        self.assertEqual(sum(cable.assetType == "XLPE_Al_150" for cable in electricity_cables), 4)

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
        self.assertTrue(all(cable.assetType != None for cable in electricity_cables))

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

    def test_given_dead_end_at_cable_junction_then_dead_end_is_left_out(self):
        # A cable branches off the ring at (220, 1), where there is no station, and ends without reaching anything
        # Arrange
        parser = self.create_parser_with_extra_mv_lines([LineString([(220, 1), (220, 100)])])
        network_builder = MvNetworkBuilder(parser, 0, 0, 520, 520)

        # Execute
        mv_network = self.generate_mv_network_within_time_limit(network_builder)

        # Assert
        assets = list(mv_network.instance[0].area.asset)
        electricity_cables = EsdlHelperFunctions.get_all_esdl_objects_from_type(assets, esdl.ElectricityCable)
        transformers = EsdlHelperFunctions.get_all_esdl_objects_from_type(assets, esdl.Transformer)

        self.assertEqual(len(electricity_cables), 6)
        self.assertEqual(len(transformers), 3)
        self.assertTrue(all(cable.assetType != None and cable.commissioningDate != None for cable in electricity_cables))
        self.assert_no_connections_outside_network(assets)

    def test_given_second_ring_through_cable_junctions_then_both_rings_are_built(self):
        # Two cables connect the ring at (220, 1) to the ring at (200, 200), both points without a station, forming a second ring
        # Arrange
        parser = self.create_parser_with_extra_mv_lines([LineString([(220, 1), (220, 100)]), LineString([(220, 100), (200, 200)])])
        network_builder = MvNetworkBuilder(parser, 0, 0, 520, 520)

        # Execute
        mv_network = self.generate_mv_network_within_time_limit(network_builder)

        # Assert
        assets = list(mv_network.instance[0].area.asset)
        electricity_cables = EsdlHelperFunctions.get_all_esdl_objects_from_type(assets, esdl.ElectricityCable)
        transformers = EsdlHelperFunctions.get_all_esdl_objects_from_type(assets, esdl.Transformer)
        joints = EsdlHelperFunctions.get_all_esdl_objects_from_type(assets, esdl.Joint)

        self.assertEqual(len(electricity_cables), 8)
        self.assertEqual(len(transformers), 3)
        self.assertTrue(all(cable.assetType != None and cable.commissioningDate != None for cable in electricity_cables))
        self.assert_no_connections_outside_network(assets)

        for junction in [(220, 1), (200, 200)]:
            junction_joints = [joint for joint in joints if GeometryHelperFunctions.points_are_close((joint.geometry.lat, joint.geometry.lon), junction)]
            self.assertEqual(len(junction_joints), 1)
            self.assertEqual(sum(len(port.connectedTo) for port in junction_joints[0].port), 3)

if __name__ == '__main__':
    unittest.main()