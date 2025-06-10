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

    def extract_lv_lines_connected_to_mv_lv_station(self) -> List[StationStartingLinesContainer]:
        ret_val = []
        for station in self.geo_df_lv_mv_station.geometry:
            lines_intersecting_with_station = []
            station_polygon = GeometryHelperFunctions.points_to_polygon(station.coords)
            lv_lines_indices = self.str_tree_lv_lines.query(station_polygon, 'dwithin', OVERLAP_SQUARE_SIZE)
            for index in lv_lines_indices:
                lv_line = self.str_tree_lv_lines.geometries.take(index)
                point_touches_mv_station = GeometryHelperFunctions.polygon_touches_point(Point(lv_line.coords[0]), station_polygon) 
                lines_intersecting_with_station.append(NavigationLineString(lv_line, not point_touches_mv_station, index))
            building_year = self.get_building_year_of_building_at_point(station)
            ret_val.append(StationStartingLinesContainer(lines_intersecting_with_station, building_year))
        return ret_val
    
    def extract_lv_lines_connected_to_mv_lv_station_at_point(self, point : Point) -> List[NavigationLineString]:
        for station in self.geo_df_lv_mv_station.geometry:
            touch_margin = 0.1
            if dwithin(station, point, touch_margin):
                return self.extract_lines_connected_to_2d_entity(self.str_tree_lv_lines, touch_margin, station)
        return []