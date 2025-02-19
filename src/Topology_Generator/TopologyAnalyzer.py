from typing import List, Tuple
from networkx import Graph, graph_edit_distance

from Topology_Generator.NetworkPlotter import NetworkPlotter
from Topology_Generator.dataclasses import EsdlNetworkTopology, NetworkTopologyInfo
from Topology_Generator.Logging import LOGGER

class TopologyAnalyzer:

    def __init__(self, networks_to_match_against : List[EsdlNetworkTopology]):
        self.networks_to_match_against = networks_to_match_against
        self.max_cable_length = self._get_max_length_of_network_cables(self.networks_to_match_against)
        self.max_amount_of_connections = self._get_max_amount_of_connections(self.networks_to_match_against)
        LOGGER.info(f"Max cable length: {self.max_cable_length}")
        LOGGER.info(f"Max amount of connections: {self.max_amount_of_connections}")

    def _get_max_length_of_network_topology(self, network_topology : Graph):
        return max([edge[2]["length"] for edge in network_topology.edges.data()])
    
    def _get_max_amount_of_connections_of_network_topology(self, network_topology : Graph):
        return max([edge[2]["amount_of_connections"] for edge in network_topology.edges.data()])

    def _get_max_length_of_network_cables(self, networks : List[NetworkTopologyInfo]):
        max_cable_length = 0
        for network_to_match_against in networks:
            new_max_cable_length = self._get_max_length_of_network_topology(network_to_match_against.network_topology)
            if max_cable_length < new_max_cable_length:
                max_cable_length = new_max_cable_length
        return  max_cable_length
    
    def _get_max_amount_of_connections(self, networks : List[NetworkTopologyInfo]):
        max_amount_of_connections = 0
        for network_to_match_against in networks:
            new_max_amount_of_connections_length = self._get_max_amount_of_connections_of_network_topology(network_to_match_against.network_topology)
            if max_amount_of_connections < new_max_amount_of_connections_length:
                max_amount_of_connections = new_max_amount_of_connections_length
        return max_amount_of_connections


    def find_best_matching_network(self, network_to_test : NetworkTopologyInfo, vizualize_result = False) -> Tuple[float, EsdlNetworkTopology]:
        # See if we can combine this with the amount of connections and data from cbs
        network_with_min_distance = self.networks_to_match_against[0]
        min_distance = 500000000
        amount_of_connections_network_to_test = network_to_test.amount_of_connections
        amount_of_connections_network_min_distance = 0
        for network_to_match_against in self.networks_to_match_against:
            LOGGER.info(f"Starting to match network with {len(network_to_test.network_topology.edges)} edges and {len(network_to_test.network_topology.nodes)} nodes")
            LOGGER.info(f"Against to network with {len(network_to_match_against.network_topology.edges)} edges and {len(network_to_match_against.network_topology.nodes)} nodes")
            if len(network_to_match_against.network_topology.edges) < 20:
                distance = graph_edit_distance(network_to_match_against.network_topology,
                                               network_to_test.network_topology,
                                               timeout=300,
                                               node_del_cost=self.node_del_cost,
                                               node_ins_cost=self.node_ins_cost,
                                               edge_del_cost=self.edge_del_cost,
                                               edge_ins_cost=self.edge_ins_cost,
                                               edge_subst_cost=self.edge_subst_cost)
                amount_of_connections_network_to_match = network_to_match_against.amount_of_connections
    
                distance_amount_of_connections = abs(amount_of_connections_network_to_match - amount_of_connections_network_to_test)
                if amount_of_connections_network_to_test > 0 and amount_of_connections_network_to_match > 0:
                    distance_amount_of_connections = (amount_of_connections_network_to_test - amount_of_connections_network_to_match) / amount_of_connections_network_to_match if amount_of_connections_network_to_match <= amount_of_connections_network_to_test else (amount_of_connections_network_to_match - amount_of_connections_network_to_test) / amount_of_connections_network_to_test
    
                distance += distance_amount_of_connections
    
                if distance <= min_distance:
                    min_distance = distance
                    network_with_min_distance = network_to_match_against
                    amount_of_connections_network_min_distance = amount_of_connections_network_to_match
        LOGGER.info(f"Distance to network with minimal distance: {min_distance}")
        LOGGER.info(f"Amount of connections in network to test: {amount_of_connections_network_to_test}")
        LOGGER.info(f"Amount of connections in network with minimal distance: {amount_of_connections_network_min_distance}")
        if vizualize_result:
            network_plotter = NetworkPlotter(2,2)
            network_plotter.plot_network_topology(network_to_test.network_topology)
            network_plotter.plot_network(network_to_test.network_lines)
            network_plotter.plot_network_topology(network_with_min_distance.network_topology)
            network_plotter.plot_network(network_with_min_distance.network_lines)
            network_plotter.show_plot()
        return min_distance, network_with_min_distance

    def node_del_cost(self, node):
        return 0
    
    def node_ins_cost(self, node):
        return 0
    
    def edge_del_cost(self, edge):
        return edge['length'] / self.max_cable_length  + edge['amount_of_connections'] / self.max_amount_of_connections
    
    def edge_ins_cost(self, edge):
        return edge['length'] / self.max_cable_length + edge['amount_of_connections'] / self.max_amount_of_connections
    
    def edge_subst_cost(self, edge_1, edge_2):
        length_e_1 = edge_1['length']
        length_e_2 = edge_2['length']
        amount_of_connections_e_1 = edge_1['amount_of_connections']
        amount_of_connections_e_2 = edge_2['amount_of_connections']
        min_amount_of_connections = min(amount_of_connections_e_1, amount_of_connections_e_2)
        score = abs(length_e_2 - length_e_1) / min(length_e_1, length_e_2) 
        return score + 1 if min_amount_of_connections == 0 else score + abs(amount_of_connections_e_1 - amount_of_connections_e_2) / min_amount_of_connections
