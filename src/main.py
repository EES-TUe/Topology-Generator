
import pandas as pd
import esdl
from Topology_Generator.NetworkPlotter import NetworkPlotter
from Topology_Generator.EsdlHelperFunctions import EsdlHelperFunctions
from Topology_Generator.EsdlNetworkParser import EsdlNetworkParser
from Topology_Generator.LvNetworkBuilder import LvNetworkBuilder
from Topology_Generator.MvEnergySystemBuilder import MvEnergySystemBuilder
from Topology_Generator.NeighbourhoodArchetypeHandler import NeighbourhoodArchetypeHandler
from Topology_Generator.AllianderGeoDataNetworkParser import AllianderGeoDataNetworkParser
from Topology_Generator.GeoDataNetworkParser import GeneratorCableCase
from Topology_Generator.MvNetworkBuilder import MvNetworkBuilder
from esdl.esdl_handler import EnergySystemHandler
import geopandas

def normalize(arr, t_min, t_max):
    norm_arr = []
    diff = t_max - t_min
    diff_arr = max(arr) - min(arr)    
    for i in arr:
        temp = (((i - min(arr))*diff)/diff_arr) + t_min
        norm_arr.append(temp)
    return norm_arr


def main():

    x_bottom_left = 157384
    y_bottom_left = 432937
    x_top_right = 159319
    y_top_right = 434915
    # x_bottom_left = 184874
    # y_bottom_left = 551369
    # x_top_right = 189478
    # y_top_right = 556048

    # Full network
    # for file in os.listdir("C:/Users/20180029/repos/Topology-Generator/Archetypes/Cleaned"):
    #     filename = os.fsdecode(file)
    #     if filename.startswith("Enexis"): 
    #         esdl_parser = EsdlNetworkParser(esdl_path=f"C:/Users/20180029/repos/Topology-Generator/Archetypes/Cleaned/{filename}")
    #         # topology_analyzer = TopologyAnalyzer(networks_to_match_against)
    #         full_network_plotter = NetworkPlotter(1,1)
    #         full_network_plotter.plot_network(esdl_parser.all_lv_lines)
    #         full_network_plotter.show_plot()
    #         esdl_network_builder = LvNetworkBuilder(esdl_parser)
    #         networks_to_match_against = esdl_network_builder.extract_network_and_topologies()
    #         for network_to_match_against in networks_to_match_against:
    #             # amount_of_connections_network_to_match = sum([edge[1]["amount_of_connections"] for edge in network_to_match_against.network_topology.edges.items()])
    #             # LOGGER.info(f"Amount of connections in nework: {amount_of_connections_network_to_match}")
    #             network_plotter = NetworkPlotter(2,1)
    #             network_plotter.plot_network(network_to_match_against.network_lines)
    #             network_plotter.plot_network_topology(network_to_match_against.network_topology)
    #             network_plotter.show_plot()


    bbox = (x_bottom_left, y_bottom_left, x_top_right, y_top_right)

    # Bag data
    bag_data_gpkg = "D:/datasets/bag-light.gpkg"
    geo_df_bag_data : geopandas.GeoDataFrame = geopandas.read_file(bag_data_gpkg, layer='pand', bbox=bbox)

    # Alliander
    lv_lines_gpkg = "D:/datasets/Topologie_archetype_data/alliander/liander_elektriciteitsnetten.gpkg"

    geo_df_lv_lines : geopandas.GeoDataFrame = geopandas.read_file(lv_lines_gpkg, layer='laagspanningskabels', bbox=bbox)
    geo_df_mv_lv_stations : geopandas.GeoDataFrame = geopandas.read_file(lv_lines_gpkg, layer='middenspanningsinstallaties', bbox=bbox)
    geo_df_mv_kabels : geopandas.GeoDataFrame = geopandas.read_file(lv_lines_gpkg, layer='middenspanningskabels', bbox=bbox)
    geo_df_hv_stations : geopandas.GeoDataFrame = geopandas.read_file(lv_lines_gpkg, layer='onderstations', bbox=bbox)
    geo_df_lv_stations : geopandas.GeoDataFrame = geopandas.read_file(lv_lines_gpkg, layer='laagspanningsverdeelkasten', bbox=bbox)
    generator_cable_case_mv_lines = GeneratorCableCase.THICK
    network_parser = AllianderGeoDataNetworkParser(geo_df_lv_lines, geo_df_mv_lv_stations, geo_df_bag_data, geo_df_mv_kabels, geo_df_hv_stations, geo_df_lv_stations, generator_cable_case_mv_lines)
    
    mv_network_builder = MvNetworkBuilder(network_parser, x_bottom_left, y_bottom_left, x_top_right, y_top_right)
    mv_network = mv_network_builder.generate_a_mv_network("Tiel")
    mv_network_builder.plot_mv_network(mv_network)

    esh = EnergySystemHandler(mv_network)
    esh.save("mv-energy-system.esdl")

if __name__ == "__main__":
    exit(main())
