from typing import List

import numpy as np
from shapely import Polygon, LineString, MultiLineString, Point, overlaps, STRtree, covers
from dataclasses import dataclass
import geopandas
import networkx as nx
from Topology_Generator.GeometryHelperFunctions import GeometryHelperFunctions, OVERLAP_SQUARE_SIZE


@dataclass
class LineStringEndPair:
    line_string : LineString
    first_point_end : bool
    index : int

@dataclass
class LvMvStationStartingLinesPair:
    lv_mv_station : Polygon
    starting_lines : List[LineStringEndPair]

class LvNetworkBuilder:
    def __init__(self, lv_lines_df : geopandas.GeoDataFrame, lv_mv_station_df : geopandas.GeoDataFrame):
        self.lv_lines_df = lv_lines_df
        self.lv_mv_station_df = lv_mv_station_df
        all_lv_lines = self._extract_lv_lines_from_dataframe(self.lv_lines_df)
        self.str_tree_lines = STRtree(all_lv_lines)
    
    def _line_string_connected_to_point(self, point : Point, line_2 : LineString, index : int) -> LineStringEndPair:
        endpoint_1 = Point(line_2.coords[0])
        endpoint_2 = Point(line_2.coords[-1])
        point_first_end = False
        if covers(endpoint_1, point):
            point_first_end = False
        elif covers(endpoint_2, point):
            point_first_end = True
        else:
            return None
        return LineStringEndPair(line_2, point_first_end, index)
    
    def _get_next_lines(self, line_string_end_pair : LineStringEndPair) -> List[LineStringEndPair]:
        point_to_connect_to = Point(line_string_end_pair.line_string.coords[0]) if line_string_end_pair.first_point_end else Point(line_string_end_pair.line_string.coords[-1])
        intersecting_indices = self.str_tree_lines.query(point_to_connect_to, 'touches')
        intersecting_indices = np.setdiff1d(intersecting_indices, np.array([line_string_end_pair.index]))
    
        ret_val = []
        for index in intersecting_indices:
            next_line = self.str_tree_lines.geometries.take(index)
            next_line_string_end_pair = self._line_string_connected_to_point(point_to_connect_to, next_line, index)
            if next_line_string_end_pair != None:
                ret_val.append(next_line_string_end_pair)
        return ret_val
    
    def _add_node_and_edge(self, network_graph : nx.Graph, from_node : int, last_added_node : int, edge_length : float) -> int:
        last_added_node += 1
        network_graph.add_node(last_added_node)
        network_graph.add_edge(from_node, last_added_node, length=edge_length)
    
        return last_added_node
    
    def _extract_common_point(self, next_line_string_end_pairs) -> tuple:
        common_point = np.array(list(zip(*next_line_string_end_pairs[0].line_string.xy)))
        for next_line_string_end_pair in next_line_string_end_pairs[1:]:
            common_point = np.intersect1d(common_point, list(zip(*next_line_string_end_pair.line_string.xy)))
        return (common_point[0], common_point[1])
    
    def _build_lv_network_recursive(self, network_graph : nx.Graph, line_string_end_pair : LineStringEndPair, last_added_node : int, from_node : int, visited_lines = [], loops_mapping = {}) -> int:

        if line_string_end_pair.index not in visited_lines:
            visited_lines.append(line_string_end_pair.index)
            edge_length = line_string_end_pair.line_string.length
            next_line_string_end_pairs = self._get_next_lines(line_string_end_pair)
            cleared = False
    
            while len(next_line_string_end_pairs) > 0:
                if len(next_line_string_end_pairs) > 1:
                    # Case the line ending has multiple branches
                    common_point = self._extract_common_point(next_line_string_end_pairs)
                    if common_point in loops_mapping:
                        # Case alogrithm has looped back to a point it has been before
                        network_graph.add_edge(from_node, loops_mapping[common_point], length=edge_length)
                    elif all(next_line_string_end_pair.index not in visited_lines for next_line_string_end_pair in next_line_string_end_pairs):
                        # Case alogrithm has found a new intersection of lines
                        last_added_node = self._add_node_and_edge(network_graph, from_node, last_added_node, edge_length)
                        from_node = last_added_node
                        loops_mapping[common_point] = from_node
    
                    for next_line_string_end_pair in next_line_string_end_pairs:
                        last_added_node = self._build_lv_network_recursive(network_graph, next_line_string_end_pair, last_added_node, from_node, visited_lines, loops_mapping)
    
                    next_line_string_end_pairs.clear()
                    cleared = True
                elif len(next_line_string_end_pairs) == 1:
                    # The line has no brances
                    next_line_string_end_pair = next_line_string_end_pairs[0]
                    visited_lines.append(next_line_string_end_pair.index)
                    edge_length += next_line_string_end_pair.line_string.length
                    next_line_string_end_pairs = self._get_next_lines(next_line_string_end_pair)
    
            if len(next_line_string_end_pairs) == 0 and not cleared:
                # Case we have reached a dead end
                last_added_node = self._add_node_and_edge(network_graph, from_node, last_added_node, edge_length)
    
        return last_added_node
    
    def build_lv_network(self, starting_line : LineStringEndPair) -> List[LineStringEndPair]:
        visited_indices = []
        next_line_string_end_pairs = self._get_next_lines(starting_line)
        ret_val = []
        while len(next_line_string_end_pairs) > 0:
            new_pairs = []
            for next_line_string_end_pair in next_line_string_end_pairs:
                if next_line_string_end_pair.index not in visited_indices:
                    ret_val.append(next_line_string_end_pair.line_string)
                    new_line_string_pairs = self._get_next_lines(next_line_string_end_pair)
                    new_pairs.extend(new_line_string_pairs)
                visited_indices.append(next_line_string_end_pair.index)
            next_line_string_end_pairs = new_pairs
        ret_val.append(starting_line.line_string)
        return ret_val
    
    def _add_line(self, lines : List[LineString], new_line : LineString):
        line_with_similar_start_end_coords = any((GeometryHelperFunctions.points_are_close(line.coords[0], new_line.coords[0]) and GeometryHelperFunctions.points_are_close(line.coords[-1], new_line.coords[-1])) or (GeometryHelperFunctions.points_are_close(line.coords[0], new_line.coords[-1]) and GeometryHelperFunctions.points_are_close(line.coords[-1], new_line.coords[0])) for line in lines)
        if not line_with_similar_start_end_coords:
            lines.append(new_line)

    def extract_lv_lines_connected_to_mv_lv_station(self) -> List[LvMvStationStartingLinesPair]:
        ret_val = []
        for station in self.lv_mv_station_df.geometry:
            lines_intersecting_with_station = []
            station_polygon = GeometryHelperFunctions.points_to_polygon(station.coords)
            lv_lines_indices = self.str_tree_lines.query(station_polygon, 'dwithin', OVERLAP_SQUARE_SIZE)
            for index in lv_lines_indices:
                lv_line = self.str_tree_lines.geometries.take(index)
                point_touches_mv_station = GeometryHelperFunctions.polygon_touches_point(Point(lv_line.coords[0]), station_polygon) 
                lines_intersecting_with_station.append(LineStringEndPair(lv_line, not point_touches_mv_station, index))
            ret_val.append(LvMvStationStartingLinesPair(station, lines_intersecting_with_station))
        return ret_val
    
    def _extract_lv_lines_from_dataframe(self, lv_lines : geopandas.GeoDataFrame):
        lv_lines = lv_lines.drop_duplicates()
        all_lv_lines = []
        for line in lv_lines.geometry:
            if isinstance(line, LineString):
                self._add_line(all_lv_lines, line)
            if isinstance(line, MultiLineString):
                for line_instance in line.geoms:
                    self._add_line(all_lv_lines, line_instance)
        return all_lv_lines
    
    def compute_lv_network_topology_from_lv_mv_station(self, starting_line : LineString) -> nx.Graph:
        network_graph = nx.Graph()
        start_node = 0
        network_graph.add_node(start_node)
        self._build_lv_network_recursive(network_graph, starting_line, start_node, start_node, [])
        return network_graph