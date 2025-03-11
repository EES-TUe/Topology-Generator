import unittest
import uuid
import esdl
import geopandas
from shapely import LineString, Polygon, Point

from Topology_Generator.EsdlHelperFunctions import EsdlHelperFunctions
from Topology_Generator.LvNetworkBuilder import LvNetworkBuilder
from Topology_Generator.AllianderGeoDataNetworkParser import AllianderGeoDataNetworkParser
from Topology_Generator.MvEnergySystemBuilder import MvEnergySystemBuilder

class TestMvEnergySystemBuilder(unittest.TestCase):

    def setUp(self):
        lines = [LineString([(2,1), (3,1)]),
                 LineString([(3,1), (3,2.6)]),
                 LineString([(3,2.6), (3,4.0)])]
        lv_lines_geo_df = geopandas.GeoDataFrame(
            {
                "id": [i for i in range(0, len(lines))],
                "geometry": lines
            }
        )
        houses = [Polygon([(2.1, 1.1), (2.9, 1.1), (2.9, 2.1), (2.1, 2.1)]),
                  Polygon([(2.1, 2.2), (2.9, 2.2), (2.9, 3.0), (2.1, 3.0)]),
                  Polygon([(3.1, 3.1), (3.9, 3.1), (3.9, 3.9), (3.1, 3.9)]),
                  Polygon([(2.5, 4.1), (3.5, 4.1), (3.5, 4.5), (2.5, 4.5)])]
        bag_data_geo_df = geopandas.GeoDataFrame(
            {
                "id": [i for i in range(len(houses))],
                "geometry": houses,
                "gebruiksdoel" : ["woonfunctie" for i in range(len(houses))]
            }
        )

        lv_mv_geo_df = geopandas.GeoDataFrame(
            {
                "id": [1],
                "geometry": [Point((2,1))]
            }
        )

        network_parser = AllianderGeoDataNetworkParser(lv_lines_geo_df, lv_mv_geo_df, bag_data_geo_df)
        network_builder = LvNetworkBuilder(network_parser)
        
        self.lv_network_topology_infos = network_builder.extract_network_and_topologies()
        self.mv_system_builder = MvEnergySystemBuilder(network_builder, {}, None)

    def esdl_lines_equal(self, esdl_line1, esdl_line2):
        if len(esdl_line1.point) != len(esdl_line2.point):
            return False
        return all(esdl_line1.point[i].lat == esdl_line2.point[i].lat and esdl_line1.point[i].lon == esdl_line2.point[i].lon for i in range(len(esdl_line1.point)))

    def test_lines_to_homes_are_connected_correctly(self):
        # Arrange
        lv_network_topology = self.lv_network_topology_infos[0]
        esdl_line1 = esdl.Line()
        esdl_line1.point.append(esdl.Point(lat=2.9, lon=1.1))
        esdl_line1.point.append(esdl.Point(lat=3.0, lon=1.1))
        esdl_line2 = esdl.Line()
        esdl_line2.point.append(esdl.Point(lat=2.9, lon=2.2))
        esdl_line2.point.append(esdl.Point(lat=3.0, lon=2.2))
        esdl_line3 = esdl.Line()
        esdl_line3.point.append(esdl.Point(lat=3.1, lon=3.1))
        esdl_line3.point.append(esdl.Point(lat=3.0, lon=3.1))
        esdl_line4 = esdl.Line()
        esdl_line4.point.append(esdl.Point(lat=2.5, lon=4.1))
        esdl_line4.point.append(esdl.Point(lat=3.0, lon=4.0))
        
        # Execute
        new_lines_to_homes = self.mv_system_builder.generate_lines_connected_to_homes(lv_network_topology)
        
        # Assert
        self.assertEqual(len(new_lines_to_homes), 4)
        esdl_lines = [line_to_home.cable_to_home.geometry for line_to_home in new_lines_to_homes]
        self.assertTrue(any(self.esdl_lines_equal(esdl_line1, esdl_line) for esdl_line in esdl_lines))
        self.assertTrue(any(self.esdl_lines_equal(esdl_line2, esdl_line) for esdl_line in esdl_lines))
        self.assertTrue(any(self.esdl_lines_equal(esdl_line3, esdl_line) for esdl_line in esdl_lines))
        self.assertTrue(any(self.esdl_lines_equal(esdl_line4, esdl_line) for esdl_line in esdl_lines))

    def test_lv_assets_are_correctly_generated(self):
        # Arrange
        lv_network_topology = self.lv_network_topology_infos[0]
        esdl_line1 = esdl.Line()
        esdl_line1.point.append(esdl.Point(lat=2.9, lon=1.1))
        esdl_line1.point.append(esdl.Point(lat=3.0, lon=1.1))
        esdl_line2 = esdl.Line()
        esdl_line2.point.append(esdl.Point(lat=2.9, lon=2.2))
        esdl_line2.point.append(esdl.Point(lat=3.0, lon=2.2))
        esdl_line3 = esdl.Line()
        esdl_line3.point.append(esdl.Point(lat=3.1, lon=3.1))
        esdl_line3.point.append(esdl.Point(lat=3.0, lon=3.1))
        esdl_line4 = esdl.Line()
        esdl_line4.point.append(esdl.Point(lat=2.5, lon=4.1))
        esdl_line4.point.append(esdl.Point(lat=3.0, lon=4.0))
        esdl_line5 = esdl.Line()
        esdl_line5.point.append(esdl.Point(lat=2.0, lon=1.0))
        esdl_line5.point.append(esdl.Point(lat=3.0, lon=1.0))
        esdl_line6 = esdl.Line()
        esdl_line6.point.append(esdl.Point(lat=3.0, lon=1.0))
        esdl_line6.point.append(esdl.Point(lat=3.0, lon=1.1))
        esdl_line7 = esdl.Line()
        esdl_line7.point.append(esdl.Point(lat=3.0, lon=1.1))
        esdl_line7.point.append(esdl.Point(lat=3.0, lon=2.2))
        esdl_line8 = esdl.Line()
        esdl_line8.point.append(esdl.Point(lat=3.0, lon=2.2))
        esdl_line8.point.append(esdl.Point(lat=3.0, lon=2.6))
        esdl_line9 = esdl.Line()
        esdl_line9.point.append(esdl.Point(lat=3.0, lon=2.6))
        esdl_line9.point.append(esdl.Point(lat=3.0, lon=3.1))
        esdl_line10 = esdl.Line()
        esdl_line10.point.append(esdl.Point(lat=3.0, lon=3.1))
        esdl_line10.point.append(esdl.Point(lat=3.0, lon=4.0))
        

        start_joint = esdl.Joint()
        start_joint.geometry = esdl.Point(lat=2.0, lon=1.0)
        start_joint.port.append(esdl.InPort(id=str(uuid.uuid4()), name="In"))
        start_joint.port.append(esdl.OutPort(id=str(uuid.uuid4()), name="Out"))
        
        # Execute
        lv_assets = self.mv_system_builder.generate_lv_esdl(lv_network_topology, start_joint)
        
        # Assert
        esdl_cables = EsdlHelperFunctions.get_all_esdl_objects_from_type(lv_assets, esdl.ElectricityCable)
        joints = EsdlHelperFunctions.get_all_esdl_objects_from_type(lv_assets, esdl.Joint)
        e_connections = EsdlHelperFunctions.get_all_esdl_objects_from_type(lv_assets, esdl.Building)
        self.assertEqual(len(joints), 6)
        self.assertEqual(len(esdl_cables), 10)
        self.assertEqual(len(e_connections), 4)
        self.assertNotIn(start_joint, joints)
        self.assertTrue(all(len(joint.port[0].connectedTo) > 0 for joint in joints))
        self.assertTrue(all(len(joint.port[1].connectedTo) > 0 for joint in joints))
        self.assertTrue(any(self.esdl_lines_equal(esdl_line1, esdl_line.geometry) for esdl_line in esdl_cables))
        self.assertTrue(any(self.esdl_lines_equal(esdl_line2, esdl_line.geometry) for esdl_line in esdl_cables))
        self.assertTrue(any(self.esdl_lines_equal(esdl_line3, esdl_line.geometry) for esdl_line in esdl_cables))
        self.assertTrue(any(self.esdl_lines_equal(esdl_line4, esdl_line.geometry) for esdl_line in esdl_cables))
        self.assertTrue(any(self.esdl_lines_equal(esdl_line5, esdl_line.geometry) for esdl_line in esdl_cables))
        self.assertTrue(any(self.esdl_lines_equal(esdl_line6, esdl_line.geometry) for esdl_line in esdl_cables))
        self.assertTrue(any(self.esdl_lines_equal(esdl_line7, esdl_line.geometry) for esdl_line in esdl_cables))
        self.assertTrue(any(self.esdl_lines_equal(esdl_line8, esdl_line.geometry) for esdl_line in esdl_cables))
        self.assertTrue(any(self.esdl_lines_equal(esdl_line9, esdl_line.geometry) for esdl_line in esdl_cables))
        self.assertTrue(any(self.esdl_lines_equal(esdl_line10, esdl_line.geometry) for esdl_line in esdl_cables))

if __name__ == '__main__':
    unittest.main()