from esdl import EnergySystem, esdl
from Topology_Generator.EsdlHelperFunctions import EsdlHelperFunctions
from Topology_Generator.EsdlNetworkParser import EsdlNetworkParser
from Topology_Generator.LvNetworkBuilder import LvNetworkBuilder
from Topology_Generator.NeighbourhoodArchetypeHandler import NeighbourhoodArchetypeHandler
from Topology_Generator.MvNetworkBuilder import MvNetworkBuilder
from Topology_Generator.NetworkPlotter import NetworkPlotter
from Topology_Generator.dataclasses import EnergySystemOutput, EsdlNetworkTopology, LineToHomeInput, NavigationLineString, NetworkTopologyInfo
from typing import List
from shapely import Point, LineString, distance, Polygon, intersection, intersects
from Topology_Generator.Logging import LOGGER
from Topology_Generator.TopologyAnalyzer import TopologyAnalyzer

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
        closest_line_index = 0
        line_connected_to_end_feeder : LineString = None
        shortest_line_connected_to_end_feeder : LineString = LineString([Point(0,0), Point(1000000000,0)])

        while closest_line_index < len(closest_line.line_string.coords) - 1:
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
            closest_line_index += 1

        return shortest_line_connected_to_end_feeder


    def add_lines_connected_to_homes(self, network_topology_info : NetworkTopologyInfo) -> List[LineToHomeInput]:
        LOGGER.info(f"Adding lines to homes for network with connections: {network_topology_info.amount_of_connections}")
        for edge in network_topology_info.network_topology.edges.items():
            buildings_bordering_edge = edge[1]["houses"] 
            associated_lines = edge[1]["line_strings"] 
            lines_to_homes = []
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
                    esdl_building = esdl.Building(name="building")
                    # generate the three phase networks as well as the in and out ports
                    esdl_building.geometry = esdl.Point(lat=new_linestring_to_home.coords[-1][0], lon=new_linestring_to_home.coords[-1][1])
                    new_line_input = LineToHomeInput(new_linestring_to_home, esdl.Building(name="building"), esdl.ElectricityCable(name="cable"))
                    lines_to_homes.append(new_line_input)
                    LOGGER.info(f"Added line to home with length: {lines_to_homes[-1].length}")

        test_plotter = NetworkPlotter(1,1)
        test_plotter.plot_network_with_buildings(network_topology_info.network_lines + lines_to_homes, buildings_bordering_edge, True)
        test_plotter.show_plot()
        return lines_to_homes


    def generate_lv_esdl(self, network_topology_info : NetworkTopologyInfo, network_with_min_distance : EsdlNetworkTopology) -> esdl.EnergySystem:
        new_lines_to_homes = self.add_lines_connected_to_homes(network_topology_info)

        for line_string in network_topology_info.network_lines:
            line_that_intersects = next((line for line in new_lines_to_homes if intersects(line, line_string)), None)
            while line_that_intersects != None:
                # Create building
                # Create cable
                # Create joints
                # Connect cable to building and joints



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
                    for network_topology_info in network_topology_infos:
                        lv_lines_to_vizualize.extend(network_topology_info.network_lines)
                        network_distance, network_with_min_distance = topology_analyzer.find_best_matching_network(network_topology_info)



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
                            self.add_lines_connected_to_homes(network_topology_info)
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
