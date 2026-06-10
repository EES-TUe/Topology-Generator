from typing import List
from esdl import Polygon
from shapely import LineString, MultiLineString, Point
import geopandas
import numpy as np
from shapely.ops import nearest_points

from Topology_Generator.Constants import GeoDataMargins
from Topology_Generator.GeometryHelperFunctions import GeometryHelperFunctions
from Topology_Generator.NetworkParser import NetworkParser, StationStartingLinesContainer
from enum import Enum

from Topology_Generator.dataclasses import BuildingInformation, NavigationLineString

class GeneratorCableCase(Enum):
    THIN = 2
    AVG = 1
    THICK = 3

class BuildingYearCategory(Enum):
    OLD = 1
    AVG = 2
    NEW = 3

class GeoDataNetworkParser(NetworkParser):
    def __init__(self, geo_df_lv_lines : geopandas.GeoDataFrame, lv_mv_station_df : geopandas.GeoDataFrame, geo_df_bag_data : geopandas.GeoDataFrame = geopandas.GeoDataFrame(), geo_df_mv_lines : geopandas.GeoDataFrame = geopandas.GeoDataFrame(), geo_df_hv_stations : geopandas.GeoDataFrame = geopandas.GeoDataFrame(), geo_df_lv_stations = geopandas.GeoDataFrame(), mv_generator_cable_case : GeneratorCableCase = GeneratorCableCase.AVG, lv_generator_cable_case : GeneratorCableCase = GeneratorCableCase.AVG):
        self.geo_df_lv_lines = geo_df_lv_lines
        self.geo_df_lv_mv_station = lv_mv_station_df
        self.geo_df_bag_data = geo_df_bag_data
        self.geo_df_mv_lines = geo_df_mv_lines
        self.geo_df_hv_stations = geo_df_hv_stations
        self.geo_df_lv_stations = geo_df_lv_stations
        self.counted_connections_indices = np.array([])
        self.mv_generator_cable_case : GeneratorCableCase = mv_generator_cable_case
        self.lv_generator_cable_case : GeneratorCableCase = lv_generator_cable_case
        self.lv_line_buildings_mapping : dict[LineString, List[Polygon]] = self.init_line_building_mapping(geo_df_lv_lines, geo_df_bag_data)
        super().__init__()

    def init_line_building_mapping(self, geo_df_lv_lines : geopandas.GeoDataFrame, geo_df_bag_data : geopandas.GeoDataFrame):
        ret_val = {}
        for index, building in geo_df_bag_data.iterrows():
            if building["gebruiksdoel"] is not None and "woonfunctie" in str(building["gebruiksdoel"]).lower():
                nearest_index = geo_df_lv_lines.sindex.nearest(building.geometry, max_distance=GeoDataMargins.MAX_DISTANCE_BUILDING_TO_LV_CABLE)
                if nearest_index.size > 0:
                    line_string = geo_df_lv_lines.take(nearest_index[1]).geometry.iloc[0]
                    if line_string not in ret_val:
                        ret_val[line_string] = []
                    ret_val[line_string].append(index)
        return ret_val

    def _add_line(self, lines : List[LineString], new_line : LineString):
        line_with_similar_start_end_coords = any((GeometryHelperFunctions.points_are_close(line.coords[0], new_line.coords[0]) and GeometryHelperFunctions.points_are_close(line.coords[-1], new_line.coords[-1])) or (GeometryHelperFunctions.points_are_close(line.coords[0], new_line.coords[-1]) and GeometryHelperFunctions.points_are_close(line.coords[-1], new_line.coords[0])) for line in lines)
        if not line_with_similar_start_end_coords:
            lines.append(new_line)
            
    def extract_lv_lines_connected_to_mv_lv_station(self) -> List[StationStartingLinesContainer]:
        # Method should be overriden by derrived classes
        pass

    def extract_lv_lines_connected_to_lv_station_at_point(self, point : Point) -> List[NavigationLineString]:
        # Method should be overriden by derrived classes
        pass

    def extract_mv_lines_connected_to_hv_mv_station(self) -> List[StationStartingLinesContainer]:
        # Method should be overriden by derrived classes
        pass

    def is_line_connected_to_mv_station(self, navigation_line_string : NavigationLineString) -> bool:
        # Method should be overriden by derrived classes
        pass

    def _remove_connections_with_intersection_at_transformer(self, new_connections_indices : List[int], line_string : LineString):
        to_remove = []
        for index in new_connections_indices:
            building = self.geo_df_bag_data.take([index]).iloc[0].geometry
            point_on_building, point_on_line = nearest_points(building, line_string)
            nearest_lv_station = self.geo_df_lv_mv_station.sindex.query(point_on_line, predicate="dwithin", distance=GeoDataMargins.LV_CABLES_TO_MV_LV_STATION_MARGIN)
            if nearest_lv_station.size > 0:
                to_remove.append(index)
        return np.setdiff1d(new_connections_indices, to_remove)


    def get_houses_bordering_line(self, line_string : LineString) -> List[BuildingInformation]:
        ret_val = []
        if not self.geo_df_bag_data.empty:
            new_connections = self.lv_line_buildings_mapping[line_string] if line_string in self.lv_line_buildings_mapping else []
            new_connections = self._remove_connections_with_intersection_at_transformer(new_connections, line_string)

            for index in new_connections:
                building = self.geo_df_bag_data.take([index])
                ret_val.append(BuildingInformation(building.iloc[0].geometry, 
                                                   int(building.iloc[0]["bouwjaar"]), 
                                                   building.iloc[0]["gebruiksdoel"], 
                                                   int(building.iloc[0]["aantal_verblijfsobjecten"])))
        return ret_val


    def get_building_year_of_building_at_point(self, point : Point)  -> int:
        if not self.geo_df_bag_data.empty:
            indices = self.geo_df_bag_data.sindex.query(point)
            for index in indices:
                building = self.geo_df_bag_data.take([index])
                return int(building.iloc[0]["bouwjaar"])
        return 1

    def get_building_year_of_transformer_house_at_point(self, point : Point) -> int:
        mv_station_indices = self.geo_df_lv_mv_station.sindex.query(point, predicate="dwithin", distance=3.0)
        if len(mv_station_indices) > 0:
            mv_station_point = self.geo_df_lv_mv_station.take([mv_station_indices[0]]).geometry
            return self.get_building_year_of_building_at_point(Point(mv_station_point.x, mv_station_point.y))
        return 1

    def get_line_length_from_metadata(self, line_string : LineString) -> float:
        return line_string.length
    
    def _extract_network_lines(self, df_lines : geopandas.GeoDataFrame) -> List[LineString]:
        lines = df_lines.drop_duplicates()
        all_lines = []
        if not df_lines.empty:
            for line in lines.geometry:
                if isinstance(line, LineString):
                    self._add_line(all_lines, line)
                if isinstance(line, MultiLineString):
                    for line_instance in line.geoms:
                        self._add_line(all_lines, line_instance)
        return all_lines

    def _extract_lv_network_lines(self) -> List[LineString]:
        return self._extract_network_lines(self.geo_df_lv_lines)
    
    def _extract_mv_network_lines(self) -> List[LineString]:
        return self._extract_network_lines(self.geo_df_mv_lines)
    
    def builidng_year_to_building_year_category(self, building_year) -> BuildingYearCategory:
        if building_year <= 1970:
            return BuildingYearCategory.OLD
        elif 1970 < building_year <= 2000:
            return BuildingYearCategory.AVG
        elif 2000 < building_year:
            return BuildingYearCategory.NEW
