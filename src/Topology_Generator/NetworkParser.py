from dataclasses import dataclass
from typing import List
from shapely import STRtree, LineString, Point, Polygon

from Topology_Generator.dataclasses import BuildingInformation, NavigationLineString

@dataclass
class StationStartingLinesContainer:
    starting_lines : List[NavigationLineString]
    building_year : int

class NetworkParser:
    def __init__(self):
        self.all_lv_lines = self._extract_lv_network_lines()
        self.str_tree_lv_lines = STRtree(self.all_lv_lines)
        self.all_mv_lines = self._extract_mv_network_lines()
        self.str_tree_mv_lines = STRtree(self.all_mv_lines)

    def _extract_lv_network_lines(self) -> List[LineString]:
        return []

    def _extract_mv_network_lines(self) -> List[LineString]:
        return []

    def extract_mv_lines_connected_to_mv_lv_station_at_point(self, point : Point) -> List[NavigationLineString]:
        return []
    
    def extract_lv_lines_connected_to_mv_lv_station_at_point(self, point : Point) -> List[NavigationLineString]:
        return []
    
    def get_id_of_mv_lv_transformer_at_point(self, point : Point) -> int:
        return -1
    
    def extract_lv_lines_connected_to_lv_station_at_point(self, point : Point) -> List[NavigationLineString]:
        return []
    
    def is_there_industry_at_point(self, point : Point) -> bool:
        return False
    
    def get_building_year_of_transformer_house_at_point(self, point : Point) -> int:
        return -1
    
    def get_building_year_of_building_at_point(self, point : Point) -> int:
        return -1
    
    def extract_mv_lines_that_are_connected_at_point(self, point : Point):
        return []
    
    def extract_mv_lines_connected_to_hv_mv_station_at_point(self, point : Point) -> List[NavigationLineString]:
        return []
    
    def is_line_connected_to_mv_station(self, line_string : LineString) -> bool:
        return False
    
    def is_line_connected_to_mv_station_at_point(self, line_string : LineString, point : Point) -> bool:
        return False

    def extract_mv_lines_connected_to_hv_mv_station(self) -> List[StationStartingLinesContainer]:
        return []

    def get_amount_of_connections_bordering_line(self, line_string : LineString) -> int:
        return 0
    
    def get_houses_bordering_line(self, line_string : LineString) -> List[BuildingInformation]:
        return []

    def get_line_length_from_metadata(self, line_string : LineString) -> float:
        return 0.0
    
    def define_mv_cable_type_based_on_year(self, building_year):
        return f"{building_year}-type"
