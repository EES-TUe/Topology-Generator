from typing import List, Tuple

from shapely import STRtree, Point
import networkx as nx
from Topology_Generator.EsdlNetworkParser import EsdlNetworkParser
from Topology_Generator.GeometryHelperFunctions import GeometryHelperFunctions, NavigationLineString
from Topology_Generator.NetworkParser import NetworkParser
from Topology_Generator.Logging import LOGGER

from Topology_Generator.dataclasses import EdgeLabel, NetworkTopologyInfo


class LvNetworkBuilder:
    def __init__(self, parser : NetworkParser):
        self.str_tree_lines : STRtree = parser.str_tree_lv_lines
        self.filter_lv_lines_connected_to_mv_lines = isinstance(parser, EsdlNetworkParser)
        self.parser = parser

    def _add_node_and_edge(self, network_graph : nx.Graph, from_node : int, last_added_node : int, edge_label : EdgeLabel) -> int:
        last_added_node += 1
        network_graph.add_node(last_added_node)
        network_graph.add_edge(from_node, last_added_node, length=edge_label.length, amount_of_connections=edge_label.amount_of_connections, houses=edge_label.houses_bordering_line, line_strings=edge_label.line_strings)

        return last_added_node

    def _extract_common_points(self, next_line_string_end_pairs : List[NavigationLineString]) -> set[Tuple[float, float]]:
        ret_val = set()
        for next_line_string_end_pair in next_line_string_end_pairs:
            common_point = next_line_string_end_pair.line_string.coords[-1] if next_line_string_end_pair.first_point_end else next_line_string_end_pair.line_string.coords[0]
            ret_val.add(common_point)
        return ret_val
    
    def get_next_lines_lv_network(self, next_line_string_end_pair : NavigationLineString) -> List[NavigationLineString]:
        new_lines = GeometryHelperFunctions.get_next_lines(self.str_tree_lines, next_line_string_end_pair)
        point_of_potential_station = next_line_string_end_pair.end_point
        ret_val = new_lines
        if self.filter_lv_lines_connected_to_mv_lines:
            lines_connected_to_transformer = self.parser.extract_lv_lines_connected_to_mv_lv_station_at_point(Point(point_of_potential_station))
            ret_val = [new_line for new_line in new_lines if new_line not in lines_connected_to_transformer]
        if ret_val == []:
            ret_val = self.parser.extract_lv_lines_connected_to_lv_station_at_point(Point(point_of_potential_station))
            ret_val = [value for value in ret_val if value.index != next_line_string_end_pair.index]

        return ret_val

    def _build_lv_network_recursive(self, network_graph : nx.Graph, navigation_line_string : NavigationLineString, last_added_node : int, from_node : int, visited_lines : List[NavigationLineString], loops_mapping : dict[Tuple[float, float], int]) -> int:
        if not any(visited_line.index == navigation_line_string.index for visited_line in visited_lines):
            visited_lines.append(navigation_line_string)
            edge_label = EdgeLabel(0, 0)
            self._update_line_labels(navigation_line_string, edge_label)
            next_navigation_line_strings = self.get_next_lines_lv_network(navigation_line_string)

            cleared = False

            while len(next_navigation_line_strings) > 0:
                if len(next_navigation_line_strings) > 1:
                    # Case the line ending has multiple branches
                    common_points = self._extract_common_points(next_navigation_line_strings)
                    common_point = next((common_point for common_point in common_points if common_point in loops_mapping ), None)
                    if common_point != None:
                        # Case alogrithm has looped back to a point it has been before
                        network_graph.add_edge(from_node, loops_mapping[common_point], length=edge_label.length, amount_of_connections=edge_label.amount_of_connections, houses=edge_label.houses_bordering_line, line_strings=edge_label.line_strings)
                        if visited_lines[0].index in [next_navigation_line_string.index for next_navigation_line_string in next_navigation_line_strings]:
                            # Case alogrithm looped back to the starting point
                            next_navigation_line_strings.clear()
                    elif all(next_line_string_end_pair.line_string not in visited_lines for next_line_string_end_pair in next_navigation_line_strings):
                        # Case alogrithm has found a new intersection of lines
                        last_added_node = self._add_node_and_edge(network_graph, from_node, last_added_node, edge_label)
                        from_node = last_added_node
                        for common_point in common_points:
                            loops_mapping[common_point] = from_node

                    found_mv_station_connection = False
                    last_added_node_new = last_added_node
                    for navigation_line_string in next_navigation_line_strings:
                        prev_last_added_node = last_added_node
                        last_added_node_new = self._build_lv_network_recursive(network_graph, navigation_line_string, last_added_node, from_node, visited_lines, loops_mapping)
                        if prev_last_added_node == last_added_node_new:
                            # Algorithm has found a branch that connects to a mv station
                            found_mv_station_connection = True
                    last_added_node = last_added_node if found_mv_station_connection else last_added_node_new

                    next_navigation_line_strings.clear()
                    cleared = True
                elif len(next_navigation_line_strings) == 1:
                    # The line has no brances
                    navigation_line_string = next_navigation_line_strings[0]
                    visited_lines.append(navigation_line_string)
                    self._update_line_labels(navigation_line_string, edge_label)
                    next_navigation_line_strings = self.get_next_lines_lv_network(navigation_line_string)

            if len(next_navigation_line_strings) == 0 and not cleared and navigation_line_string.end_point not in loops_mapping.keys() and not self.parser.is_line_connected_to_mv_station(navigation_line_string):
                # Case we have reached a dead end
                connection_point = navigation_line_string.end_point
                if connection_point in loops_mapping:
                    network_graph.add_edge(from_node, loops_mapping[connection_point], length=edge_label.length, amount_of_connections=edge_label.amount_of_connections, houses=edge_label.houses_bordering_line, line_strings=edge_label.line_strings)
                else:
                    last_added_node = self._add_node_and_edge(network_graph, from_node, last_added_node, edge_label)

        return last_added_node

    def _update_line_labels(self, navigation_line_string : NavigationLineString, edge_label : EdgeLabel) -> EdgeLabel:
        edge_label.length += self.parser.get_line_length_from_metadata(navigation_line_string.line_string)
        houses = self.parser.get_houses_bordering_line(navigation_line_string.line_string)
        edge_label.amount_of_connections += len(houses) if len(houses) > 0 else self.parser.get_amount_of_connections_bordering_line(navigation_line_string.line_string)
        edge_label.houses_bordering_line.extend(houses)
        edge_label.line_strings.append(navigation_line_string)

    def compute_lv_network_topology_from_lv_mv_station(self, starting_line : NavigationLineString, loops_mapping : dict[Tuple[float, float], int] ) -> Tuple[NetworkTopologyInfo, List[int]]:
        network_graph = nx.Graph()
        start_node = 0
        network_graph.add_node(start_node)
        visited_lines : List[NavigationLineString] = []
        self._build_lv_network_recursive(network_graph, starting_line, start_node, start_node, visited_lines, loops_mapping)
        # Visited lines are being used instead of lines in labels, todo check labels
        return NetworkTopologyInfo(network_graph, starting_line), [visited_line.index for visited_line in visited_lines]
    
    def _define_initial_loops_mapping(self, starting_lines) -> dict[Tuple[float, float], int]:
        return {starting_line.line_string.coords[-1] if starting_line.first_point_end else starting_line.line_string.coords[0] : 0 for starting_line in starting_lines}

    def extract_lv_networks_and_topologies_at_point(self, point : Point) -> List[NetworkTopologyInfo]:
        starting_lines = self.parser.extract_lv_lines_connected_to_mv_lv_station_at_point(point)
        lv_networks = []
        all_visited_indices = []
        loops_mapping = self._define_initial_loops_mapping(starting_lines)
        for starting_line in starting_lines:
            if starting_line.index not in all_visited_indices:
                lv_network_topology_pair, visited_indices = self.compute_lv_network_topology_from_lv_mv_station(starting_line, loops_mapping)
                lv_networks.append(lv_network_topology_pair)
                all_visited_indices.extend(visited_indices)
        return lv_networks