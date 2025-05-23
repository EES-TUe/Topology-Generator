from typing import List
from Topology_Generator.GeoDataNetworkParser import GeneratorCableCase, BuildingYearCategory
from Topology_Generator.GeoDataNetworkParser import GeoDataNetworkParser
from Topology_Generator.GeometryHelperFunctions import GeometryHelperFunctions
from shapely import STRtree, dwithin, Point, distance, touches
import geopandas
import numpy as np

from Topology_Generator.Logging import LOGGER
from Topology_Generator.NetworkParser import StationStartingLinesContainer
from Topology_Generator.dataclasses import NavigationLineString

class AllianderGeoDataNetworkParser(GeoDataNetworkParser):

    def remove_duplicate_and_non_connected_lines(self, station : Point, ret_val : List[NavigationLineString]):
        to_clean = []
        for i, navigation_line_string in enumerate(ret_val):
            for j in range(i, len(ret_val)):
                navigation_line_string_a = ret_val[i]
                navigation_line_string_b = ret_val[j]
                coord_a_connected_point = GeometryHelperFunctions.get_connected_coords(navigation_line_string_a)
                coord_b_end_point = GeometryHelperFunctions.get_end_coords(navigation_line_string_b)
                coord_a_end_point = GeometryHelperFunctions.get_end_coords(navigation_line_string_a)
                coord_b_connected_point = GeometryHelperFunctions.get_connected_coords(navigation_line_string_b)

                if touches(Point(coord_a_connected_point), Point(coord_b_end_point)) or touches(Point(coord_a_end_point), Point(coord_b_connected_point)):
                    if distance(Point(coord_a_connected_point), station) < distance(Point(coord_b_connected_point), station):
                        to_clean.append(navigation_line_string_b)
                    else:
                        to_clean.append(navigation_line_string_a)

        for navigation_line_string in to_clean:
            if navigation_line_string in ret_val:
                ret_val.remove(navigation_line_string)

    def extract_lines_connected_to_2d_entity2(self, str_tree_lines : STRtree, touch_margin : float, station : Point) -> List[NavigationLineString]:
        ret_val = []
        line_indices = str_tree_lines.query(station, 'dwithin', touch_margin)
        for index in line_indices:
            line = str_tree_lines.geometries.take(index)

            first_point_touches_station = GeometryHelperFunctions.points_are_close(line.coords[0], (station.x, station.y), touch_margin) 
            last_point_touches_station = GeometryHelperFunctions.points_are_close(line.coords[-1], (station.x, station.y), touch_margin) 
            if first_point_touches_station and last_point_touches_station:
                dis_station_first_coord = distance(Point(line.coords[0]), station)
                dis_station_last_coord = distance(Point(line.coords[-1]), station)
                ret_val.append(NavigationLineString(line, dis_station_first_coord > dis_station_last_coord, index))
            elif first_point_touches_station or last_point_touches_station:
                ret_val.append(NavigationLineString(line, not first_point_touches_station, index))

        self.remove_duplicate_and_non_connected_lines(station, ret_val)
        return ret_val
    
    def extract_lines_connected_to_2d_entity_one_side_connected(self, str_tree_lines : STRtree, touch_margin : float, station : Point) -> List[NavigationLineString]:
        ret_val = []
        line_indices = str_tree_lines.query(station, 'dwithin', touch_margin)
        for index in line_indices:
            line = str_tree_lines.geometries.take(index)
            amount_of_lines_connecting_first_point = str_tree_lines.query(Point(line.coords[0]), 'touches').size
            amount_of_lines_connecting_last_point = str_tree_lines.query(Point(line.coords[-1]), 'touches').size
            if not (amount_of_lines_connecting_first_point > 1 and amount_of_lines_connecting_last_point > 1):
                
                first_point_touches_station = amount_of_lines_connecting_first_point == 1
                last_point_touches_station = amount_of_lines_connecting_last_point == 1
                if not (first_point_touches_station and last_point_touches_station):
                    ret_val.append(NavigationLineString(line, not first_point_touches_station, index))

        return ret_val

    def extract_lines_connected_to_2d_entity_include_both_sides_disconnected(self, str_tree_lines : STRtree, touch_margin : float, station : Point) -> List[NavigationLineString]:
        ret_val = []
        line_indices = str_tree_lines.query(station, 'dwithin', touch_margin)
        for index in line_indices:
            line = str_tree_lines.geometries.take(index)
            amount_of_lines_connecting_first_point = str_tree_lines.query(Point(line.coords[0]), 'touches').size
            amount_of_lines_connecting_last_point = str_tree_lines.query(Point(line.coords[-1]), 'touches').size
            if not (amount_of_lines_connecting_first_point > 1 and amount_of_lines_connecting_last_point > 1):
                
                first_point_touches_station = GeometryHelperFunctions.points_are_close(line.coords[0], (station.x, station.y), touch_margin) 
                last_point_touches_station = GeometryHelperFunctions.points_are_close(line.coords[-1], (station.x, station.y), touch_margin) 
                if first_point_touches_station and last_point_touches_station:
                    dis_station_first_coord = distance(Point(line.coords[0]), station)
                    dis_station_last_coord = distance(Point(line.coords[-1]), station)
                    ret_val.append(NavigationLineString(line, dis_station_first_coord > dis_station_last_coord, index))
                elif first_point_touches_station or last_point_touches_station:
                    ret_val.append(NavigationLineString(line, not first_point_touches_station, index))

        return ret_val

    def extract_lines_connected_to_stations_include_both_sides_disconnected(self, station_geo_df : geopandas.GeoDataFrame, str_tree_lines : STRtree, touch_margin : float) -> List[StationStartingLinesContainer]:
        ret_val = []
        for station in station_geo_df.geometry:
            lines_intersecting_with_station = self.extract_lines_connected_to_2d_entity_include_both_sides_disconnected(str_tree_lines, touch_margin, station)
            building_year = self.get_building_year_of_building_at_point(station)
            ret_val.append(StationStartingLinesContainer(lines_intersecting_with_station, building_year))
        return ret_val
    
    def extract_lines_connected_to_stations_include_one_side_connected(self, station_geo_df : geopandas.GeoDataFrame, str_tree_lines : STRtree, touch_margin : float) -> List[StationStartingLinesContainer]:
        ret_val = []
        for station in station_geo_df.geometry:
            lines_intersecting_with_station = []

            i = 0
            while lines_intersecting_with_station == [] and i < 5:
                touch_margin_to_check = touch_margin + i * 50.0
                LOGGER.debug(f"Trying to find lines connected to station {station} with touch margin {touch_margin_to_check}")
                lines_intersecting_with_station = self.extract_lines_connected_to_2d_entity_one_side_connected(str_tree_lines, touch_margin_to_check, station)
                i += 1

            building_year = self.get_building_year_of_building_at_point(station)
            ret_val.append(StationStartingLinesContainer(lines_intersecting_with_station, building_year))
        return ret_val
    
    def extract_mv_lines_connected_to_mv_lv_station_at_point(self, point : Point) -> List[NavigationLineString]:
        for station in self.geo_df_lv_mv_station.geometry:
            if dwithin(station, point, 3.0):
                return self.extract_lines_connected_to_2d_entity_one_side_connected(self.str_tree_mv_lines, 3.0, station)
        return []
    
    def extract_lv_lines_connected_to_mv_lv_station_at_point(self, point : Point) -> List[NavigationLineString]:
        for station in self.geo_df_lv_mv_station.geometry:
            if dwithin(station, point, 10.0):
                return self.extract_lines_connected_to_2d_entity_include_both_sides_disconnected(self.str_tree_lv_lines, 10.0, station)
        return []

    def extract_mv_lines_that_are_connected_at_point(self, point : Point):
        ret_val = self.extract_lines_connected_to_2d_entity_include_both_sides_disconnected(self.str_tree_mv_lines, 3.0, point)
        return ret_val

    def extract_lv_lines_connected_to_mv_lv_station(self) -> List[StationStartingLinesContainer]:
        return self.extract_lines_connected_to_stations_include_both_sides_disconnected(self.geo_df_lv_mv_station, self.str_tree_lv_lines, 3.0)

    def extract_lv_lines_connected_at_point(self, point : Point):
        return self.extract_lines_connected_to_2d_entity_include_both_sides_disconnected(self.str_tree_mv_lines, 3.0, point)
    
    def extract_mv_lines_connected_to_hv_mv_station_at_point(self, point : Point) -> List[NavigationLineString]:
        indices = self.geo_df_hv_stations.sindex.query(point, predicate="dwithin", distance=20.0)
        ret_val = []
        if len(indices) > 0:
            station_point = self.geo_df_hv_stations.take([indices[0]]).geometry
            ret_val = self.extract_lines_connected_to_2d_entity_one_side_connected(self.str_tree_mv_lines, 20.0, Point(station_point.x, station_point.y))
        return ret_val
    
    def remove_navigation_line_strings_not_connected_to_building(self, input : List[NavigationLineString]):
        items_to_remove = [navigation_line_string for navigation_line_string in input if self.get_building_year_of_building_at_point(Point(navigation_line_string.line_string.coords[0])) == 1 and self.get_building_year_of_building_at_point(Point(navigation_line_string.line_string.coords[-1])) == 1]
        for navigation_line in items_to_remove:
            input.remove(navigation_line)

    def remove_navigation_line_strings_connected_to_mv_station(self, input : List[NavigationLineString] ):
        to_remove = []
        for navigation_line_string in input:
            point_a = GeometryHelperFunctions.get_connected_coords(navigation_line_string)
            point_b = GeometryHelperFunctions.get_end_coords(navigation_line_string)
            if len(self.extract_mv_lines_connected_to_mv_lv_station_at_point(Point(point_a))) > 0 or len(self.extract_mv_lines_connected_to_mv_lv_station_at_point(Point(point_b))):
                to_remove.append(navigation_line_string)

        for item in to_remove:
            input.remove(item)

    def extract_mv_lines_connected_to_hv_mv_station(self) -> List[StationStartingLinesContainer]:
        ret_vals = self.extract_lines_connected_to_stations_include_one_side_connected(self.geo_df_hv_stations, self.str_tree_mv_lines, 50.0)
        for ret_val in ret_vals:
            self.remove_navigation_line_strings_not_connected_to_building(ret_val.starting_lines)
            self.remove_navigation_line_strings_connected_to_mv_station(ret_val.starting_lines)
        return ret_vals

    def define_cable_type_based_on_year(self, building_year):
        building_year_category = self.builidng_year_to_building_year_category(building_year)
        cable_mapping = {
            (GeneratorCableCase.THIN,  BuildingYearCategory.OLD) : "GPLK-Cu-35",
            (GeneratorCableCase.AVG,   BuildingYearCategory.OLD) : "GPLK-Cu-70",
            (GeneratorCableCase.THICK, BuildingYearCategory.OLD) : "GPLK-Cu-95",
            (GeneratorCableCase.THIN,  BuildingYearCategory.AVG) : "GPLK-Al-50",
            (GeneratorCableCase.AVG,   BuildingYearCategory.AVG) : "GPLK-Al-150",
            (GeneratorCableCase.THICK, BuildingYearCategory.AVG) : "GPLK-Al-240",
            (GeneratorCableCase.THIN,  BuildingYearCategory.NEW) : "XLPE-Al-95",
            (GeneratorCableCase.AVG,   BuildingYearCategory.NEW) : "XLPE-Al-150",
            (GeneratorCableCase.THICK, BuildingYearCategory.NEW) : "XLPE-Al-240",
        }
        return cable_mapping[(self.generator_cable_case, building_year_category)]


