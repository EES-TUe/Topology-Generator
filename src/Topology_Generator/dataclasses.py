from dataclasses import dataclass
from typing import List
import esdl
from networkx import Graph
from shapely import LineString

@dataclass
class NavigationLineString:
    line_string : LineString
    first_point_end : bool
    index : int

class NetworkTopologyInfo:
    def __init__(self, network_lines : List[LineString], network_topology : Graph, starting_line : NavigationLineString):
        self.network_lines : List[LineString] = network_lines
        self.network_topology : Graph = network_topology
        self.starting_line : NavigationLineString = starting_line
        self.amount_of_connections : int = sum([edge[1]["amount_of_connections"] for edge in network_topology.edges.items()])
        self.total_length : int = sum([edge[1]["length"] for edge in network_topology.edges.items()])

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

@dataclass
class EnergySystemOutput:
    energy_system : esdl.EnergySystem
    length_correlation : List[tuple[float, float]]
    amount_of_connections_correlation : List[tuple[int, int]]