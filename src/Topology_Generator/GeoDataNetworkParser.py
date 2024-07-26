from typing import List
from shapely import LineString, MultiLineString, Point
import geopandas
import numpy as np

from Topology_Generator.GeometryHelperFunctions import GeometryHelperFunctions
from Topology_Generator.NetworkParser import NetworkParser, StationStartingLinesContainer
from enum import Enum

class GeneratorCableCase(Enum):
    THIN = 2
    AVG = 1
    THICK = 3

class BuildingYearCategory(Enum):
    OLD = 1
    AVG = 2
    NEW = 3

class GeoDataNetworkParser(NetworkParser):
    def __init__(self, geo_df_lv_lines : geopandas.GeoDataFrame, lv_mv_station_df : geopandas.GeoDataFrame, geo_df_bag_data : geopandas.GeoDataFrame = geopandas.GeoDataFrame(), geo_df_mv_lines : geopandas.GeoDataFrame = geopandas.GeoDataFrame(), geo_df_hv_stations : geopandas.GeoDataFrame = geopandas.GeoDataFrame(), generator_cable_case : GeneratorCableCase = GeneratorCableCase.AVG):
        self.geo_df_lv_lines = geo_df_lv_lines
        self.geo_df_lv_mv_station = lv_mv_station_df
        self.geo_df_bag_data = geo_df_bag_data
        self.geo_df_mv_lines = geo_df_mv_lines
        self.geo_df_hv_stations = geo_df_hv_stations
        self.counted_connections_indices = np.array([])
        self.generator_cable_case : GeneratorCableCase = generator_cable_case
        super().__init__()

    def _add_line(self, lines : List[LineString], new_line : LineString):
        line_with_similar_start_end_coords = any((GeometryHelperFunctions.points_are_close(line.coords[0], new_line.coords[0]) and GeometryHelperFunctions.points_are_close(line.coords[-1], new_line.coords[-1])) or (GeometryHelperFunctions.points_are_close(line.coords[0], new_line.coords[-1]) and GeometryHelperFunctions.points_are_close(line.coords[-1], new_line.coords[0])) for line in lines)
        if not line_with_similar_start_end_coords:
            lines.append(new_line)
            
    def extract_lv_lines_connected_to_mv_lv_station(self) -> List[StationStartingLinesContainer]:
        # Method should be overriden by derrived classes
        pass

    def extract_mv_lines_connected_to_hv_mv_station(self) -> List[StationStartingLinesContainer]:
        # Method should be overriden by derrived classes
        pass

    def get_amount_of_connections_bordering_line(self, line_string : LineString) -> int:
        MAX_DISTANCE_TO_LINE = 20.0
        ret_val = 0.0
        if not self.geo_df_bag_data.empty:
            indices = self.geo_df_bag_data.sindex.query(line_string, predicate="dwithin", distance=MAX_DISTANCE_TO_LINE)
            new_connections = np.setdiff1d(indices, self.counted_connections_indices)
            new_connections = np.array([index for index in new_connections if self.geo_df_bag_data.take([index]).iloc[0]["gebruiksdoel"] != None and "woonfunctie" in self.geo_df_bag_data.take([index]).iloc[0]["gebruiksdoel"]])
            self.counted_connections_indices = np.insert(self.counted_connections_indices, 0, new_connections)
            ret_val = new_connections.size
        return ret_val

    def is_there_industry_at_point(self, point : Point) -> bool:
        MAX_DISTANCE_TO_POINT = 12.0
        indices = self.geo_df_bag_data.sindex.query(point, predicate="dwithin", distance=MAX_DISTANCE_TO_POINT)
        return any("industriefunctie" in self.geo_df_bag_data.take(index)["gebruiksdoel"] for index in indices)

    def get_building_year_of_building_at_point(self, point : Point)  -> int:
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
