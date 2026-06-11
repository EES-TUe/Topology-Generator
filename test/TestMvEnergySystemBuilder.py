import unittest
import uuid
import esdl
import geopandas
from shapely import LineString, Polygon, Point, STRtree

from Topology_Generator.EsdlHelperFunctions import EsdlHelperFunctions
from Topology_Generator.LvNetworkBuilder import LvNetworkBuilder
from Topology_Generator.AllianderGeoDataNetworkParser import AllianderGeoDataNetworkParser
from Topology_Generator.MvEnergySystemBuilder import MvEnergySystemBuilder
from mocks.NeigbourhoodArchetypeHandlerMock import NeigbourhoodArchetypeHandlerMock

class TestMvEnergySystemBuilder(unittest.TestCase):

    def setUp(self):
        lines = [LineString([(2,1), (30,10)]),
                 LineString([(30,10), (30, 26)]),
                 LineString([(30,26), (30,40)])]
        lv_lines_geo_df = geopandas.GeoDataFrame(
            {
                "id": [i for i in range(0, len(lines))],
                "geometry": lines
            }
        )
        houses = [Polygon([(21, 11), (29, 11), (29, 21), (21, 21)]),
                  Polygon([(21, 22), (29, 22), (29, 30), (21, 30)]),
                  Polygon([(31, 31), (39, 31), (39, 39), (31, 39)]),
                  Polygon([(25, 41), (35, 41), (35, 45), (25, 45)])]
        bag_data_geo_df = geopandas.GeoDataFrame(
            {
                "id": [i for i in range(len(houses))],
                "geometry": houses,
                "gebruiksdoel" : ["woonfunctie" for i in range(len(houses))],
                "bouwjaar" : ["1980" for i in range(len(houses))],
                "aantal_verblijfsobjecten" : [1 for i in range(len(houses))]
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
        
        self.lv_network_topology_infos = network_builder.extract_lv_networks_and_topologies_at_point(Point((2,1)))
        self.mv_system_builder = MvEnergySystemBuilder(network_builder, NeigbourhoodArchetypeHandlerMock())

    def esdl_lines_equal(self, esdl_line1, esdl_line2):
        if len(esdl_line1.point) != len(esdl_line2.point):
            return False
        return all(esdl_line1.point[i].lat == esdl_line2.point[i].lat and esdl_line1.point[i].lon == esdl_line2.point[i].lon for i in range(len(esdl_line1.point)))

    def test_lines_to_homes_are_connected_correctly(self):
        # Arrange
        lv_network_topology = self.lv_network_topology_infos[0]
        esdl_line1 = esdl.Line()
        esdl_line1.point.append(esdl.Point(lat=float(29), lon=float(11)))
        esdl_line1.point.append(esdl.Point(lat=float(30), lon=float(11)))
        esdl_line2 = esdl.Line()
        esdl_line2.point.append(esdl.Point(lat=float(29), lon=float(22)))
        esdl_line2.point.append(esdl.Point(lat=float(30), lon=float(22)))
        esdl_line3 = esdl.Line()
        esdl_line3.point.append(esdl.Point(lat=float(31), lon=float(31)))
        esdl_line3.point.append(esdl.Point(lat=float(30), lon=float(31)))
        esdl_line4 = esdl.Line()
        esdl_line4.point.append(esdl.Point(lat=float(30), lon=float(41)))
        esdl_line4.point.append(esdl.Point(lat=float(30), lon=float(40)))
        
        # Execute
        r_tree_lines = STRtree([navigation_line_string.line_string for navigation_line_string in lv_network_topology.network_lines])
        new_lines_to_homes = self.mv_system_builder.generate_lines_connected_to_homes("trafo", r_tree_lines, lv_network_topology)
        
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
        esdl_line1.point.append(esdl.Point(lat=29.0, lon=11.0))
        esdl_line1.point.append(esdl.Point(lat=30.0, lon=11.0))
        esdl_line2 = esdl.Line()
        esdl_line2.point.append(esdl.Point(lat=29.0, lon=22.0))
        esdl_line2.point.append(esdl.Point(lat=30.0, lon=22.0))
        esdl_line3 = esdl.Line()
        esdl_line3.point.append(esdl.Point(lat=31.0, lon=31.0))
        esdl_line3.point.append(esdl.Point(lat=30.0, lon=31.0))
        esdl_line4 = esdl.Line()
        esdl_line4.point.append(esdl.Point(lat=25.0, lon=41.0))
        esdl_line4.point.append(esdl.Point(lat=30.0, lon=40.0))
        esdl_line5 = esdl.Line()
        esdl_line5.point.append(esdl.Point(lat=20.0, lon=10.0))
        esdl_line5.point.append(esdl.Point(lat=30.0, lon=10.0))
        esdl_line6 = esdl.Line()
        esdl_line6.point.append(esdl.Point(lat=30.0, lon=10.0))
        esdl_line6.point.append(esdl.Point(lat=30.0, lon=11.0))
        esdl_line7 = esdl.Line()
        esdl_line7.point.append(esdl.Point(lat=30.0, lon=11.0))
        esdl_line7.point.append(esdl.Point(lat=30.0, lon=22.0))
        esdl_line8 = esdl.Line()
        esdl_line8.point.append(esdl.Point(lat=30.0, lon=22.0))
        esdl_line8.point.append(esdl.Point(lat=30.0, lon=26.0))
        esdl_line9 = esdl.Line()
        esdl_line9.point.append(esdl.Point(lat=30.0, lon=26.0))
        esdl_line9.point.append(esdl.Point(lat=30.0, lon=31.0))
        esdl_line10 = esdl.Line()
        esdl_line10.point.append(esdl.Point(lat=30.0, lon=31.0))
        esdl_line10.point.append(esdl.Point(lat=30.0, lon=40.0))
        

        start_joint = esdl.Joint()
        start_joint.geometry = esdl.Point(lat=20.0, lon=10.0)
        start_joint.port.append(esdl.InPort(id=str(uuid.uuid4()), name="In"))
        start_joint.port.append(esdl.OutPort(id=str(uuid.uuid4()), name="Out"))
        
        # Execute
        lv_assets = self.mv_system_builder.generate_lv_esdl(lv_network_topology, start_joint, "trafo")
        
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


    def test_houses_are_assigned_correct_assettype(self):
        station = Point(0, 40)
        line_1 = LineString([(0, 40), (80, 40)])
        line_2 = LineString([(80, 40), (80, 80)])
        line_3 = LineString([(80, 40), (80, 0)])
    
        houses = []
        houses.append(Polygon([(10,50), (10,60), (20,60), (20,50)])) # Hoekwoning
        houses.append(Polygon([(20,50), (20,60), (30,60), (30,50)])) # Rijtjeshuis
        houses.append(Polygon([(30,50), (30,60), (40,60), (40,50)])) # Hoekwoning
        houses.append(Polygon([(60,30), (70,30), (70,20), (60,20)])) # Hoekwoning
        houses.append(Polygon([(60,20), (60,10), (70,10), (70,20)])) # Rijtjeshuis
        houses.append(Polygon([(50,20), (60,20), (60,10), (50,10)])) # Hoekwoning
        houses.append(Polygon([(60,10), (60,0), (70,0), (70,10)])) # Hoekwoning
        houses.append(Polygon([(90,20), (100,20), (100,10), (90,10)])) # Vrijstaand
        houses.append(Polygon([(90,50), (90,60), (100,60), (100,50)])) # 2 onder 1 kap
        houses.append(Polygon([(90,60), (90,70), (100,70), (100,60)])) # 2 onder 1 kap
        houses.append(Polygon([(60,60), (60,70), (70,70), (70,60)])) # Massionette
        houses.append(Polygon([(60,70), (60,80), (70,80), (70,70)])) # Appartement

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
                "geometry": houses,
                "gebruiksdoel" : ["woonfunctie" for i in range(len(houses))],
                "bouwjaar" : ["1980" for i in range(len(houses))],
                "aantal_verblijfsobjecten" : amount_of_dwellings
            }
        )

        network_parser = AllianderGeoDataNetworkParser(lv_lines_geo_df, lv_mv_geo_df, bag_data_geo_df)
        network_builder = LvNetworkBuilder(network_parser)

        # Execute
        start_joint = esdl.Joint()
        start_joint.geometry = esdl.Point(lat=0.0, lon=4.0)
        start_joint.port.append(esdl.InPort(id=str(uuid.uuid4()), name="In"))
        start_joint.port.append(esdl.OutPort(id=str(uuid.uuid4()), name="Out"))
        lv_network_topologies = network_builder.extract_lv_networks_and_topologies_at_point(Point(0,40))
        lv_system = self.mv_system_builder.generate_lv_esdl(lv_network_topologies[0], start_joint, "trafo")

        building_types = [asset.assetType for asset in lv_system if isinstance(asset, esdl.Building)]
        self.assertEqual(5, sum([1 for assetType in building_types if assetType == "hoekwoning"]))
        self.assertEqual(2, sum([1 for assetType in building_types if assetType == "rijtjeshuis"]))
        self.assertEqual(1, sum([1 for assetType in building_types if assetType == "vrijstaand"]))
        self.assertEqual(2, sum([1 for assetType in building_types if assetType == "2-onder-1-kap"]))
        self.assertEqual(3, sum([1 for assetType in building_types if assetType == "massionette"]))
        self.assertEqual(15, sum([1 for assetType in building_types if assetType == "appartement"]))

if __name__ == '__main__':
    unittest.main()