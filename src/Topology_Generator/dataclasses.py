from dataclasses import dataclass, field
from typing import List
import esdl
from networkx import Graph
import pandas as pd
import geopandas as gpd
from shapely import LineString, Polygon, Point, STRtree
import numpy as np

from Topology_Generator.EsdlHelperFunctions import EsdlHelperFunctions

class NavigationLineString:

    def __init__(self, line_string : LineString, first_point_end : bool, index : int):
        self.line_string : LineString = line_string
        self.first_point_end : bool = first_point_end
        self.index : int = index
        self.end_point : tuple[float, float] = line_string.coords[0] if first_point_end else line_string.coords[-1]
        self.connected_point : tuple[float, float] = line_string.coords[-1] if first_point_end else line_string.coords[0]

class NetworkTopologyInfo:
    def generate_component_graph_of_neighborhood(self, buildings : List[BuildingInformation]) -> Graph:

        def get_index_of_polygon(buildings : List[BuildingInformation], polygon : Polygon):
            for i, building in enumerate(buildings):
                if building.building_polygon.equals(polygon):
                    return i
            raise ValueError("Polygon not found in building list")

        houses_graph = Graph()
        for i, building in enumerate(buildings):
            houses_graph.add_node(i)

        tree_building_polygons = STRtree([building.building_polygon for building in buildings])
        for i, building in enumerate(buildings):
            house_polygon = building.building_polygon
            neigbouring_indices = np.concatenate((tree_building_polygons.query(house_polygon, 'intersects'), tree_building_polygons.query(house_polygon, 'touches')), axis=0)
            
            # if 158139 < p_middle[0] < 158157 and 433787 < p_middle[1] < 433796:
            #     bla = 0
            for neighbour_index in neigbouring_indices:
                neigbouring_geometry_index = get_index_of_polygon(buildings, tree_building_polygons.geometries.take(neighbour_index))
                if neigbouring_geometry_index != i:
                    houses_graph.add_edge(i, neigbouring_geometry_index)
        return houses_graph

    def __init__(self, network_topology : Graph, starting_line : NavigationLineString):
        self.network_lines : List[NavigationLineString] = EsdlHelperFunctions.flatten_list_of_lists([edge[1]["line_strings"] for edge in network_topology.edges.items()])
        self.network_topology : Graph = network_topology
        self.starting_line : NavigationLineString = starting_line
        self.amount_of_connections : int = sum([edge[1]["amount_of_connections"] for edge in network_topology.edges.items()])
        self.total_length : int = sum([edge[1]["length"] for edge in network_topology.edges.items()])
        self.buildings : List[BuildingInformation] = EsdlHelperFunctions.flatten_list_of_lists([edge[1]["houses"] for edge in network_topology.edges.items()])

        self.buildings_graph = self.generate_component_graph_of_neighborhood(self.buildings)


class EsdlNetworkTopology(NetworkTopologyInfo):
    def __init__(self, network_lines: List[LineString], network_topology: Graph, starting_line: NavigationLineString, network_assets : List[esdl.ConnectableAsset], starting_transformer : esdl.Transformer, esdl_starting_cable : esdl.ElectricityCable):
        super().__init__(network_lines, network_topology, starting_line)
        self.network_assets : List[esdl.ConnectableAsset] = network_assets
        self.starting_transformer : esdl.Transformer = starting_transformer
        self.esdl_starting_cable : esdl.ElectricityCable = esdl_starting_cable

@dataclass
class BuildingInformation:
    building_polygon : Polygon
    year_of_construction : int
    purpose : str
    amount_of_dwellings : int

@dataclass
class EdgeLabel:
    length : float
    amount_of_connections : int
    houses_bordering_line : List[BuildingInformation] = field(default_factory=list)
    line_strings : List[NavigationLineString] = field(default_factory=list)

@dataclass
class EnergySystemOutput:
    energy_system : esdl.EnergySystem
    length_correlation : List[tuple[float, float]]
    amount_of_connections_correlation : List[tuple[int, int]]

@dataclass
class LineToHomeInput:
    line : LineString
    house : esdl.Building
    cable_to_home : esdl.ElectricityCable

@dataclass
class PerpendicularLineSegments:
    line_to_building : LineString
    line_from_building : LineString