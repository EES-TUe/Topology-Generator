from typing import List
from Topology_Generator.GeoDataNetworkParser import GeoDataNetworkParser
from Topology_Generator.GeometryHelperFunctions import OVERLAP_SQUARE_SIZE, GeometryHelperFunctions
from shapely import Point, dwithin

from Topology_Generator.NetworkParser import StationStartingLinesContainer
from Topology_Generator.dataclasses import NavigationLineString

class EnexisGeoDataNetworkParser(GeoDataNetworkParser):

    def extract_lines_connected_to_2d_entity(self, str_tree_lines, touch_margin, station) -> List[NavigationLineString]:
        ret_val = []
        line_indices = str_tree_lines.query(station, 'dwithin', touch_margin)
        for index in line_indices:
            line = str_tree_lines.geometries.take(index)
            first_point_touches_station = GeometryHelperFunctions.polygon_touches_point(Point(line.coords[0]), station, touch_margin) 
            last_point_touches_station = GeometryHelperFunctions.polygon_touches_point(Point(line.coords[-1]), station, touch_margin) 
            if first_point_touches_station or last_point_touches_station:
                ret_val.append(NavigationLineString(line, not first_point_touches_station, index))
        return ret_val
    
    def extract_lv_lines_connected_to_mv_lv_station_at_point(self, point : Point) -> List[NavigationLineString]:
        for i, station in enumerate(self.geo_df_lv_mv_station.geometry):
            touch_margin = 0.1
            if dwithin(station, point, touch_margin):
                return self.extract_lines_connected_to_2d_entity(self.str_tree_lv_lines, touch_margin, station)
        return []