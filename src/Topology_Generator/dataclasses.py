from dataclasses import dataclass, field
from typing import List
import esdl
from networkx import Graph
from shapely import LineString, Polygon, Point

from Topology_Generator.EsdlHelperFunctions import EsdlHelperFunctions

class NavigationLineString:

    def __init__(self, line_string : LineString, first_point_end : bool, index : int):
        self.line_string : LineString = line_string
        self.first_point_end : bool = first_point_end
        self.index : int = index
        self.end_point : tuple[float, float] = line_string.coords[0] if first_point_end else line_string.coords[-1]
        self.connected_point : tuple[float, float] = line_string.coords[-1] if first_point_end else line_string.coords[0]

class NetworkTopologyInfo:
    def __init__(self, network_topology : Graph, starting_line : NavigationLineString):
        self.network_lines : List[NavigationLineString] = EsdlHelperFunctions.flatten_list_of_lists([edge[1]["line_strings"] for edge in network_topology.edges.items()])
        self.network_topology : Graph = network_topology
        self.starting_line : NavigationLineString = starting_line
        self.amount_of_connections : int = sum([edge[1]["amount_of_connections"] for edge in network_topology.edges.items()])
        self.total_length : int = sum([edge[1]["length"] for edge in network_topology.edges.items()])
        self.buildings : List[Polygon] = EsdlHelperFunctions.flatten_list_of_lists([edge[1]["houses"] for edge in network_topology.edges.items()])

class EsdlNetworkTopology(NetworkTopologyInfo):
    def __init__(self, network_lines: List[LineString], network_topology: Graph, starting_line: NavigationLineString, network_assets : List[esdl.ConnectableAsset], starting_transformer : esdl.Transformer, esdl_starting_cable : esdl.ElectricityCable):
        super().__init__(network_lines, network_topology, starting_line)
        self.network_assets : List[esdl.ConnectableAsset] = network_assets
        self.starting_transformer : esdl.Transformer = starting_transformer
        self.esdl_starting_cable : esdl.ElectricityCable = esdl_starting_cable

@dataclass
class EdgeLabel:
    length : float
    amount_of_connections : int
    total_voltage_drop : float = 0.0
    meets_voltage_drop_requirements : bool = False
    houses_bordering_line : List[Polygon] = field(default_factory=list)
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