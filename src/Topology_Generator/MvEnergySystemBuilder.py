import uuid
from esdl import EnergySystem, esdl
from Topology_Generator.GeometryHelperFunctions import GeometryHelperFunctions
from Topology_Generator.EsdlHelperFunctions import EsdlHelperFunctions
from Topology_Generator.EsdlNetworkParser import EsdlNetworkParser
from Topology_Generator.LvNetworkBuilder import LvNetworkBuilder
from Topology_Generator.NeighbourhoodArchetypeHandler import NeighbourhoodArchetypeHandler
from Topology_Generator.MvNetworkBuilder import MvNetworkBuilder
from Topology_Generator.NetworkPlotter import NetworkPlotter
from Topology_Generator.dataclasses import EnergySystemOutput, EsdlNetworkTopology, LineToHomeInput, NavigationLineString, NetworkTopologyInfo
from typing import List
from shapely import Point, LineString, distance, Polygon, intersection, intersects, STRtree
from Topology_Generator.Logging import LOGGER
from Topology_Generator.TopologyAnalyzer import TopologyAnalyzer
from esdl.esdl_handler import EnergySystemHandler

class MvEnergySystemBuilder:
    def __init__(self, lv_network_builder : LvNetworkBuilder ,archetypes_esdls_paths : dict, archetype_handler : NeighbourhoodArchetypeHandler):
        self.archetype_network_mapping : dict[int : List[List[EsdlNetworkTopology]]] = self.init_archetype_networks(archetypes_esdls_paths)
        self.archetype_handler = archetype_handler
        self.lv_network_builder = lv_network_builder

    def init_archetype_networks(self, archetypes_esdls_paths : dict) -> dict[int : List[List[EsdlNetworkTopology]]]:
        ret_val = {}
        for archetype, esdl_paths in archetypes_esdls_paths.items():
            ret_val[archetype] = []
            for esdl_path in esdl_paths:
                LOGGER.debug(f"Parsing esdl file: {esdl_path}")
                esdl_parser = EsdlNetworkParser(esdl_path=esdl_path)
                esdl_network_builder = LvNetworkBuilder(esdl_parser)
                networks_to_match_against = esdl_network_builder.extract_network_and_topologies()
                networks_to_match_against_with_esdl = [EsdlNetworkTopology(network_to_match_against.network_lines, 
                                                                           network_to_match_against.network_topology, 
                                                                           network_to_match_against.starting_line, 
                                                                           esdl_parser.get_esdl_connected_assets_from_line_string(network_to_match_against.network_lines), 
                                                                           esdl_parser.get_transformer_connected_to_line_string(network_to_match_against.starting_line),
                                                                           esdl_parser.get_esdl_cable_from_line_string(network_to_match_against.starting_line.line_string)) for network_to_match_against in networks_to_match_against]
                ret_val[archetype].append(networks_to_match_against_with_esdl)
                LOGGER.debug(f"Finished parsing esdl file: {esdl_path}")
        return ret_val

    def remove_joints_connected_to_transformer(self, best_match : List[esdl.ConnectableAsset]):
        new_joints = EsdlHelperFunctions.get_all_esdl_objects_from_type(best_match.network_assets, esdl.Joint)
        to_remove = []
        for joint in new_joints:
            for port in joint.port:
                if isinstance(port, esdl.InPort):
                    for out_port in port.connectedTo:
                        if isinstance(out_port.eContainer(), esdl.Transformer):
                            LOGGER.debug(f"Removing {joint.name}")
                            to_remove.append(joint)
        for value in to_remove:
            best_match.network_assets.remove(value)


    def compute_line_to_closest_line(self, building : Polygon, point : Point, closest_line : NavigationLineString) -> LineString:
        line_connected_to_end_feeder : LineString = None
        shortest_line_connected_to_end_feeder : LineString = LineString([Point(0,0), Point(1000000000,0)])

        for closest_line_index in range(0, len(closest_line.line_string.coords) - 1):
            point_a = closest_line.line_string.coords[closest_line_index]
            point_b = closest_line.line_string.coords[closest_line_index+1]
            if point_a[0] > point_b[0]:
                point_a = closest_line.line_string.coords[closest_line_index+1]
                point_b = closest_line.line_string.coords[closest_line_index]
            slope = (point_b[1] - point_a[1]) / (point_b[0] - point_a[0])
            slope_perpidicular = -1 * (1 / slope)
            b = point.y - slope_perpidicular * point.x

            TOUCH_MARGIN = 15
            line_segment_perpidicular_to_building = LineString([(point.x - TOUCH_MARGIN, slope_perpidicular * (point.x - TOUCH_MARGIN) + b), (point.x, point.y)])
            line_segment_perpidicular_from_building = LineString([(point.x, point.y), (point.x + TOUCH_MARGIN, slope_perpidicular * (point.x + TOUCH_MARGIN) + b)])
            positive_intersection_building = line_segment_perpidicular_to_building.intersection(building)
            negative_intersection_building = line_segment_perpidicular_from_building.intersection(building)
            positive_intersection_line = intersection(line_segment_perpidicular_to_building, LineString([point_a, point_b]))
            negative_intersection_line = intersection(line_segment_perpidicular_from_building, LineString([point_a, point_b]))
            if not positive_intersection_line.is_empty and positive_intersection_building.geom_type == "Point":
                return LineString([positive_intersection_line, point])
            elif not negative_intersection_line.is_empty and negative_intersection_building.geom_type == "Point":
                return LineString([negative_intersection_line, point])

            line_connected_to_end_feeder = LineString([Point(point_a), point ])
            if distance(point, Point(point_a)) > distance(point, Point(point_b)):
                line_connected_to_end_feeder = LineString([Point(point_b), point])
            if line_connected_to_end_feeder.length < shortest_line_connected_to_end_feeder.length:
                shortest_line_connected_to_end_feeder = line_connected_to_end_feeder
        return shortest_line_connected_to_end_feeder


    def generate_esdl_home(self, coords : tuple[float, float]) -> esdl.Building:
        building_point = esdl.Point(lat=coords[0], lon=coords[1])
        building = esdl.Building(name="home")
        building.geometry = building_point
        e_connection = esdl.EConnection(name="home")
        e_connection.geometry = building_point
        e_connection.port.append(esdl.InPort(id=str(uuid.uuid4()), name="In"))
        for i in range(0, 3):
            e_connection.port.append(esdl.OutPort(id=str(uuid.uuid4()), name=f"OutPh{i+1}"))
            electricity_network = esdl.ElectricityNetwork(name=f"ph{i+1}")
            electricity_network.port.append(esdl.InPort(id=str(uuid.uuid4()), name="In"))
            electricity_network.port.append(esdl.OutPort(id=str(uuid.uuid4()), name="Out"))
            electricity_network.port.append(esdl.OutPort(id=str(uuid.uuid4()), name="In"))
            building.asset.append(electricity_network)
        building.asset.append(e_connection)
        return building


    def generate_lines_connected_to_homes(self, network_topology_info : NetworkTopologyInfo) -> List[LineToHomeInput]:
        LOGGER.info(f"Adding lines to homes for network with connections: {network_topology_info.amount_of_connections}")
        for edge in network_topology_info.network_topology.edges.items():
            buildings_bordering_edge = edge[1]["houses"] 
            associated_lines = edge[1]["line_strings"] 
            ret_val : List[LineToHomeInput] = []
            for building in buildings_bordering_edge:
                
                coord_index = 0
                potential_lines_to_home = []
                while coord_index < len(building.boundary.coords):
                    coord = building.boundary.coords[coord_index]
                    point = Point(coord)
                    closest_line = min(associated_lines, key=lambda line, point = point: distance(line.line_string, point))
                    line_to_closest_line = self.compute_line_to_closest_line(building, point, closest_line)
                    potential_lines_to_home.append(line_to_closest_line)
                    coord_index += 1

                if len(potential_lines_to_home) > 0:
                    new_linestring_to_home = min(potential_lines_to_home, key=lambda line: line.length)
                    esdl_building = self.generate_esdl_home(new_linestring_to_home.coords[-1])

                    cable_to_home = esdl.ElectricityCable(name="cabletohome")
                    cable_to_home.port.append(esdl.InPort(id=str(uuid.uuid4()), name="In"))
                    cable_to_home.port.append(esdl.OutPort(id=str(uuid.uuid4()), name="Out"))
                    cable_to_home.geometry = esdl.Line()
                    cable_to_home.geometry.point.append(esdl.Point(lat=new_linestring_to_home.coords[-1][0], lon=new_linestring_to_home.coords[-1][1], CRS="WGS84"))
                    cable_to_home.geometry.point.append(esdl.Point(lat=new_linestring_to_home.coords[0][0], lon=new_linestring_to_home.coords[0][1], CRS="WGS84"))
                    esdl_building.asset[-1].port[0].connectedTo.append(cable_to_home.port[1])
                    cable_to_home.port[1].connectedTo.append(esdl_building.asset[-1].port[0])

                    new_line_input = LineToHomeInput(new_linestring_to_home, esdl_building, cable_to_home)
                    ret_val.append(new_line_input)
                    LOGGER.info(f"Added line to home with length: {ret_val[-1].line.length}")

        test_plotter = NetworkPlotter(1,1)
        line_string_to_homes = [line_to_home_input.line for line_to_home_input in ret_val]
        test_plotter.plot_network_with_buildings(network_topology_info.network_lines + line_string_to_homes, buildings_bordering_edge, True)
        test_plotter.show_plot()
        return ret_val
    

    def list_of_points_to_linestring(self, points) -> LineString:
        return LineString([(point.lat, point.lon) for point in points])


    def plot_intermediate_result(self, assets_to_plot : List[esdl.ConnectableAsset]):
        line_strings = [self.list_of_points_to_linestring(cable.geometry.point) for cable in EsdlHelperFunctions.get_all_esdl_objects_from_type(assets_to_plot, esdl.ElectricityCable)]
        test_plotter = NetworkPlotter(1,1)
        test_plotter.plot_network(line_strings)
        test_plotter.show_plot()


    def generate_lv_esdl(self, network_topology_info : NetworkTopologyInfo, network_with_min_distance : EsdlNetworkTopology, start_joint : esdl.Joint) -> esdl.EnergySystem:
        lines_to_home_inputs = self.generate_lines_connected_to_homes(network_topology_info)
        lv_assets = []
        last_joint = start_joint
        point_last_added_joint = (start_joint.geometry.lat, start_joint.geometry.lon)
        r_tree_lines = STRtree(network_topology_info.network_lines)
        starting_line_new_r_tree = network_topology_info.starting_line
        start_point = GeometryHelperFunctions.get_connected_coords(starting_line_new_r_tree)
        start_line_index = r_tree_lines.query(Point(start_point), 'touches')
        starting_line_new_r_tree.index = start_line_index[0]
        next_lines = [starting_line_new_r_tree]
        while next_lines != []:
            last_nav_line_string = None
            for nav_line_string in next_lines:
                last_nav_line_string = nav_line_string
                points_for_cable = []
                added_lines_to_home = False
                reversed_iteration = -1 if nav_line_string.first_point_end else 1
                for i in range(0, len(nav_line_string.line_string.coords) - 1):
                    i_start = i
                    i_end = i + 1
                    if reversed_iteration == -1:
                        i_start = reversed_iteration * (i + 1)
                        i_end = reversed_iteration * (i + 2)
                    point_a = point_last_added_joint if added_lines_to_home else nav_line_string.line_string.coords[i_start]
                    added_lines_to_home = False
                    points_for_cable.append(point_a)
                    point_b = nav_line_string.line_string.coords[i_end]
                    line_string = LineString([Point(point_a), Point(point_b)])
                    line_to_home_input_intersects = next((line_to_home_input for line_to_home_input in lines_to_home_inputs if intersects(line_to_home_input.line, line_string)), None)
                    while line_to_home_input_intersects != None:
                        lines_to_home_inputs.remove(line_to_home_input_intersects)
                        point_for_joint = line_to_home_input_intersects.line.coords[0]
                        intersection_point = intersection(line_string, line_to_home_input_intersects.line)
                        if point_for_joint != (last_joint.geometry.lat, last_joint.geometry.lon):
                            last_joint = self.generate_cable_and_joint(points_for_cable, (intersection_point.x, intersection_point.y), last_joint, lv_assets)
                            point_last_added_joint = (intersection_point.x, intersection_point.y)
                            added_lines_to_home = True
                        line_to_home_input_intersects.cable_to_home.port[0].connectedTo.append(last_joint.port[1])
                        last_joint.port[1].connectedTo.append(line_to_home_input_intersects.cable_to_home.port[0])
                        points_for_cable.clear()
                        lv_assets.append(line_to_home_input_intersects.cable_to_home)
                        lv_assets.append(line_to_home_input_intersects.house)
                        line_to_home_input_intersects = next((line_to_home_input for line_to_home_input in lines_to_home_inputs if intersects(line_to_home_input.line, line_string)), None)
                        self.plot_intermediate_result(lv_assets)

                    if i == len(nav_line_string.line_string.coords) - 2 and point_last_added_joint != point_b:
                        last_joint = self.generate_cable_and_joint(points_for_cable, point_b, last_joint, lv_assets)
                        self.plot_intermediate_result(lv_assets)

            next_lines = GeometryHelperFunctions.get_next_lines(r_tree_lines, last_nav_line_string)
        return lv_assets


    def generate_cable_and_joint(self, points_for_cable : List[tuple[float, float]], intersection_point : tuple[float, float], last_joint : esdl.Joint, lv_assets : List[esdl.ConnectableAsset]) -> tuple[esdl.ElectricityCable, esdl.Joint]:
        part_cable = esdl.ElectricityCable(name="cable")
        part_cable.geometry = esdl.Line()
        for point in points_for_cable:
            part_cable.geometry.point.append(esdl.Point(lat=point[0], lon=point[1], CRS="WGS84"))
        part_cable.geometry.point.append(esdl.Point(lat=intersection_point[0], lon=intersection_point[1], CRS="WGS84"))
        new_joint = esdl.Joint(id=str(uuid.uuid4()), name="joint")
        new_joint.port.append(esdl.InPort(id=str(uuid.uuid4()), name="In"))
        new_joint.port.append(esdl.OutPort(id=str(uuid.uuid4()), name="Out"))
        new_joint.geometry = esdl.Point(lat=points_for_cable[-1][0], lon=points_for_cable[-1][1], CRS="WGS84")
        part_cable.port.append(esdl.InPort(id=str(uuid.uuid4()), name="In"))
        part_cable.port.append(esdl.OutPort(id=str(uuid.uuid4()), name="Out"))
        part_cable.port[1].connectedTo.append(new_joint.port[0])
        new_joint.port[0].connectedTo.append(part_cable.port[1])
        part_cable.port[0].connectedTo.append(last_joint.port[1])
        last_joint.port[1].connectedTo.append(part_cable.port[0])
        lv_assets.append(part_cable)
        lv_assets.append(new_joint)
        return new_joint


    def build_mv_energy_system(self, mv_network : EnergySystem) -> EnergySystemOutput:
        assets = mv_network.instance[0].area.asset
        transfomers : List[esdl.Transformer] = EsdlHelperFunctions.get_all_esdl_objects_from_type(assets, esdl.Transformer)

        lv_lines_to_vizualize = []
        for transfomer in transfomers:
            LOGGER.debug(f"Next transformer at point: {(transfomer.geometry.lat, transfomer.geometry.lon)}")
            transfomer_point = Point(transfomer.geometry.lat, transfomer.geometry.lon)
            network_topology_infos = self.lv_network_builder.extract_lv_networks_and_topologies_at_point(transfomer_point)
            if len(network_topology_infos) > 0:
                archetype = self.archetype_handler.archetype_at_point(transfomer_point)
                LOGGER.info(f"LV grid archetype: {archetype}")
                network_collections = self.archetype_network_mapping[archetype]
                for i, network_collection in enumerate(network_collections):
                    topology_analyzer = TopologyAnalyzer(network_collection)
                    for network_topology_info in network_topology_infos[1:2]:
                        lv_lines_to_vizualize.extend(network_topology_info.network_lines)
                        network_distance, network_with_min_distance = topology_analyzer.find_best_matching_network(network_topology_info)
                        lv_assets = self.generate_lv_esdl(network_topology_info, network_with_min_distance, transfomer.port[1].connectedTo[0].eContainer())
                        esh = EnergySystemHandler()
                        es = esh.create_empty_energy_system(name="test", es_description="Autogenerated based on gis data ",
                                            inst_title="Instance name", area_title="Area name")
                        energy_system_information = esdl.EnergySystemInformation(id=str(uuid.uuid4()))
                        es.energySystemInformation = energy_system_information
                        EsdlHelperFunctions.add_new_assets_to_energy_system(es, lv_assets)
                        esdl_parser_lv_network = EsdlNetworkParser(energy_system=es)
                        network_plotter = NetworkPlotter(1,1, False)
                        network_plotter.plot_network(esdl_parser_lv_network.all_lv_lines)
                        network_plotter.show_plot()



    def build_mv_energy_system2(self, mv_network : EnergySystem) -> EnergySystemOutput:
        if len(mv_network.instance) == 1:
            assets = mv_network.instance[0].area.asset
            transfomers : List[esdl.Transformer] = EsdlHelperFunctions.get_all_esdl_objects_from_type(assets, esdl.Transformer)
            length_correlation = []
            amount_of_connections_correlation = []
            lv_lines_to_vizualize = []
            for transfomer in transfomers:
                LOGGER.debug(f"Next transformer at point: {(transfomer.geometry.lat, transfomer.geometry.lon)}")
                transfomer_point = Point(transfomer.geometry.lat, transfomer.geometry.lon)
                network_topology_infos = self.lv_network_builder.extract_lv_networks_and_topologies_at_point(transfomer_point)
                if len(network_topology_infos) > 0:
                    archetype = self.archetype_handler.archetype_at_point(transfomer_point)
                    LOGGER.info(f"LV grid archetype: {archetype}")
                    network_collections = self.archetype_network_mapping[archetype]
                    min_total_distance = 5000000
                    best_matches : List[EsdlNetworkTopology] = []
                    archetype_transformer = None
                    total_amount_of_connections_best_match = 0
                    total_amount_of_length_best_match = 0
                    total_amount_of_connections_lv_networks = sum([network_topology_pair.amount_of_connections for network_topology_pair in network_topology_infos])
                    total_amount_of_length_lv_networks = sum([network_topology_pair.total_length for network_topology_pair in network_topology_infos])
                    for i, network_collection in enumerate(network_collections):
                        total_disatance = 0
                        new_matches = []
                        topology_analyzer = TopologyAnalyzer(network_collection)
                        for network_topology_info in network_topology_infos:
                            self.generate_lines_connected_to_homes(network_topology_info)
                            network_plotter = NetworkPlotter(1,2)
                            network_plotter.plot_network_with_buildings(network_topology_info.network_lines, network_topology_info.buildings, without_axis_numbers=True)
                            network_plotter.plot_network_topology(network_topology_info.network_topology)
                            network_plotter.show_plot()
                        # for network_topology_info in network_topology_infos:
                        #     lv_lines_to_vizualize.extend(network_topology_info.network_lines)
                        #     network_distance, network_with_min_distance = topology_analyzer.find_best_matching_network(network_topology_info)
                        #     total_disatance += network_distance
                        #     new_matches.append(network_with_min_distance)
                        if total_disatance <= min_total_distance:
                            LOGGER.info(f"New min total distance: {total_disatance} using collection {i}")
                            archetype_transformer = network_collection[0].starting_transformer
                            best_matches = new_matches
                            total_amount_of_connections_best_match = sum([best_match.amount_of_connections for best_match in best_matches])
                            total_amount_of_length_best_match = sum([best_match.total_length for best_match in best_matches])
                    new_transformer_connection_point = EsdlHelperFunctions.generate_esdl_joint(transfomer.geometry.lat, transfomer.geometry.lon, transfomer.name + "lvvoltageconnection")
                    transfomer.port[1].connectedTo.append(new_transformer_connection_point.port[0])
                    LOGGER.info(f"Total amount of connections in found lv network: {total_amount_of_connections_lv_networks} total amount of connections in the best matches: {total_amount_of_connections_best_match}")
                    LOGGER.info(f"Total length in found lv network: {total_amount_of_length_lv_networks} total amount of length in the best matches: {total_amount_of_length_best_match}")
                    amount_of_connections_correlation.append((total_amount_of_connections_lv_networks, total_amount_of_connections_best_match))
                    length_correlation.append((total_amount_of_length_lv_networks, total_amount_of_length_best_match))
                    for best_match in best_matches:
                        best_match.esdl_starting_cable.port[0].connectedTo.clear()
                        best_match.esdl_starting_cable.port[0].connectedTo.append(new_transformer_connection_point.port[1])
                        new_transformer_connection_point.port[1].connectedTo.append(best_match.esdl_starting_cable.port[0])
                        self.remove_joints_connected_to_transformer(best_match)

                    transfomer.assetType = archetype_transformer.assetType
                    transfomer.voltagePrimary = archetype_transformer.voltagePrimary
                    transfomer.voltageSecundary = archetype_transformer.voltageSecundary
                    # EsdlHelperFunctions.add_new_assets_to_energy_system(mv_network, [transfomer])
            esdl_parser_mv_network = EsdlNetworkParser(energy_system=mv_network)
            network_plotter = NetworkPlotter(1,1, False)
            network_plotter.plot_mv_network_with_lv_network(esdl_parser_mv_network.all_lv_lines, lv_lines_to_vizualize, mv_network_color="darkmagenta", lv_network_color="coral")
            network_plotter.show_plot()
        return EnergySystemOutput(mv_network, length_correlation, amount_of_connections_correlation)
