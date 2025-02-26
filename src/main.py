
import pandas as pd
from Topology_Generator.EsdlNetworkParser import EsdlNetworkParser
from Topology_Generator.LvNetworkBuilder import LvNetworkBuilder
from Topology_Generator.MvEnergySystemBuilder import MvEnergySystemBuilder
from Topology_Generator.NeighbourhoodArchetypeHandler import NeighbourhoodArchetypeHandler
from Topology_Generator.AllianderGeoDataNetworkParser import AllianderGeoDataNetworkParser
from Topology_Generator.GeoDataNetworkParser import GeneratorCableCase
from Topology_Generator.MvNetworkBuilder import MvNetworkBuilder
import geopandas

from Topology_Generator.NetworkPlotter import NetworkPlotter
from Topology_Generator.dataclasses import NetworkTopologyInfo

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
    # x_bottom_left = 187180
    # y_bottom_left = 548389
    # x_top_right = 18536
    # y_top_right = 552992

    # Full network
    esdl_parser = EsdlNetworkParser(esdl_path="C:/Users/20180029/repos/Topology-Generator/Archetypes/Alliander_Arch2_Net1_BU03633702_2030.esdl", transformer_touch_margin=3.0)
    esdl_network_builder = LvNetworkBuilder(esdl_parser)
    networks_to_match_against = esdl_network_builder.extract_network_and_topologies()
    # topology_analyzer = TopologyAnalyzer(networks_to_match_against)
    full_network_plotter = NetworkPlotter(1,1)
    full_network_plotter.plot_network(esdl_parser.all_lv_lines)
    full_network_plotter.show_plot()
    for network_to_match_against in networks_to_match_against:
        # amount_of_connections_network_to_match = sum([edge[1]["amount_of_connections"] for edge in network_to_match_against.network_topology.edges.items()])
        # LOGGER.info(f"Amount of connections in nework: {amount_of_connections_network_to_match}")
        network_plotter = NetworkPlotter(2,1)
        network_plotter.plot_network(network_to_match_against.network_lines)
        network_plotter.plot_network_topology(network_to_match_against.network_topology)
        network_plotter.show_plot()


    bbox = (x_bottom_left, y_bottom_left, x_top_right, y_top_right)

    # Bag data
    bag_data_gpkg = "C:/Users/20180029/datasets/bag-light.gpkg"
    geo_df_bag_data : geopandas.GeoDataFrame = geopandas.read_file(bag_data_gpkg, layer='pand', bbox=bbox)

    # Alliander
    lv_lines_gpkg = "C:/Users/20180029/datasets/Topologie_archetype_data/alliander/liander_elektriciteitsnetten.gpkg"

    geo_df_lv_lines : geopandas.GeoDataFrame = geopandas.read_file(lv_lines_gpkg, layer='laagspanningskabels', bbox=bbox)
    geo_df_mv_lv_stations : geopandas.GeoDataFrame = geopandas.read_file(lv_lines_gpkg, layer='middenspanningsinstallaties', bbox=bbox)
    geo_df_mv_kabels : geopandas.GeoDataFrame = geopandas.read_file(lv_lines_gpkg, layer='middenspanningskabels', bbox=bbox)
    geo_df_hv_stations : geopandas.GeoDataFrame = geopandas.read_file(lv_lines_gpkg, layer='onderstations', bbox=bbox)
    generator_cable_case = GeneratorCableCase.THICK
    network_parser = AllianderGeoDataNetworkParser(geo_df_lv_lines, geo_df_mv_lv_stations, geo_df_bag_data, geo_df_mv_kabels, geo_df_hv_stations, generator_cable_case)


    lv_network_builder = LvNetworkBuilder(network_parser)
    # transfomer_point = Point(158228.036, 433707.268)
    # network_topology_infos = lv_network_builder.extract_lv_networks_and_topologies_at_point(transfomer_point)

    # Enexis
    # lv_lines_shp_path = "C:/Users/20180029/datasets/Topologie_archetype_data/ENEXIS_Elektra_shape/Enexis_e_ls_verbinding/nbnl_e_ls_verbinding.shp"
    # mv_lv_station_shp_path = "C:/Users/20180029/datasets/Topologie_archetype_data/ENEXIS_Elektra_shape/Enexis_e_ms_ls_station/nbnl_e_ms_ls_station.shp"

    # geo_df_lv_lines : geopandas.GeoDataFrame = geopandas.read_file(lv_lines_shp_path, bbox=bbox)
    # geo_df_mv_lv_stations : geopandas.GeoDataFrame = geopandas.read_file(mv_lv_station_shp_path, bbox=bbox)
    # network_parser = EnexisGeoDataNetworkParser(geo_df_lv_lines, geo_df_mv_lv_stations)
    
    mv_network_builder = MvNetworkBuilder(network_parser, x_bottom_left, y_bottom_left, x_top_right, y_top_right)
    archetype_dict = {
        1 : [
            "C:/Users/20180029/repos/Topology-Generator/Archetypes/Alliander_Arch1_Net1_BU02680203_2030.esdl",
            "C:/Users/20180029/repos/Topology-Generator/Archetypes/Alliander_Arch1_Net2_BU02680204_2030.esdl"
        ],
        2 : [
            "C:/Users/20180029/repos/Topology-Generator/Archetypes/Alliander_Arch2_Net1_BU03633702_2030.esdl",
            "C:/Users/20180029/repos/Topology-Generator/Archetypes/Alliander_Arch2_Net2_BU02680202_2030.esdl"
        ],
        3 : [
            "C:/Users/20180029/repos/Topology-Generator/Archetypes/Alliander_Arch3_Net1_BU03611003_2030.esdl",
            "C:/Users/20180029/repos/Topology-Generator/Archetypes/Alliander_Arch3_Net2_BU02810100_2030.esdl"
        ],
        4 : [
            "C:/Users/20180029/repos/Topology-Generator/Archetypes/Alliander_Arch4_Net1_BU04020505_2030.esdl",
            "C:/Users/20180029/repos/Topology-Generator/Archetypes/Alliander_Arch4_Net2_BU04791210_2030.esdl"
        ],
        5 : [
            "C:/Users/20180029/repos/Topology-Generator/Archetypes/Alliander_Arch5_Net1_BU02000506_2030.esdl",
            "C:/Users/20180029/repos/Topology-Generator/Archetypes/Alliander_Arch5_Net2_BU04530302_2030.esdl"
        ],
        6 : [
            "C:/Users/20180029/repos/Topology-Generator/Archetypes/Alliander_Arch6_Net1_BU19403001_2030.esdl",
            "C:/Users/20180029/repos/Topology-Generator/Archetypes/Alliander_Arch6_Net2_BU19403201_2030.esdl"
        ],
        7 : [
            "C:/Users/20180029/repos/Topology-Generator/Archetypes/Alliander_Arch7_Net1_BU04320101_2030.esdl",
            "C:/Users/20180029/repos/Topology-Generator/Archetypes/Alliander_Arch7_Net2_BU03940675_2030.esdl"
        ],
        8 : [
            "C:/Users/20180029/repos/Topology-Generator/Archetypes/Alliander_Arch8_Net1_BU02890802_2030.esdl"
        ]
    }
    # mv_network = None
    mv_network = mv_network_builder.generate_a_mv_network("To-look-at")
    mv_network_builder.plot_mv_network(mv_network)

    bla = MvEnergySystemBuilder(lv_network_builder, archetype_dict, NeighbourhoodArchetypeHandler(pd.read_csv("C:/Users/20180029/repos/Topology-Generator/Archetypes/buurten_archetypen.csv")))
    bla.build_mv_energy_system(mv_network)
    # for i in range(0,2):
    #     energy_system_output = bla.build_mv_energy_system(mv_network)
    #     esh = EnergySystemHandler(energy_system_output.energy_system)
    #     esh.save(f"mv-energy-system{i}.esdl")
    #     if len(energy_system_output.amount_of_connections_correlation) > 0 and len(energy_system_output.length_correlation) > 0:
    #         x1,y1 = zip(*energy_system_output.amount_of_connections_correlation)
    #         x2,y2 = zip(*energy_system_output.length_correlation)
    #         with open("out.txt", mode="a") as file:
    #             file.write(f"Output non normalized values of iteration {i}\n")
    #             file.write(f"x1 values: {x1}\n")
    #             file.write(f"y1 values: {y1}\n")
    #             file.write(f"x2 values: {x2}\n")
    #             file.write(f"y2 values: {y2}\n")
    #         if min(x1) != max(x1) and min(y1) != max(y1) and min(x2) != max(x2) and min(y2) != max(y2):
    #             x1y1_norm = normalize(x1 + y1, 0, 1)
    #             x1 = x1y1_norm[:len(x1)]
    #             y1 = x1y1_norm[len(x1):]
    #             x2y2_norm = normalize(x2 + y2, 0, 1)
    #             x2 = x2y2_norm[:len(x2)]
    #             y2 = x2y2_norm[len(x2):]
    #             with open("out.txt", mode="a") as file:
    #                 file.write(f"Output normalized values of iteration {i}\n")
    #                 file.write(f"x1 values: {x1}\n")
    #                 file.write(f"y1 values: {y1}\n")
    #                 file.write(f"x2 values: {x2}\n")
    #                 file.write(f"y2 values: {y2}\n")
    #             plt.subplot(1,2,1)
    #             plt.scatter(x1, y1, color='blue')
    #             plt.plot([0,1],[0,1])
    #             plt.xlabel("Amount of connections in found lv network")
    #             plt.ylabel("Amount of connections in matched lv network")
    #             plt.subplot(1,2,2)
    #             plt.scatter(x2,y2, color='orange')
    #             plt.plot([0,1],[0,1])
    #             plt.xlabel("Total length of cables in found lv network")
    #             plt.ylabel("Total length of cables in matched lv network")
    #             plt.show()
    # topology_analyzer = TopologyAnalyzer(networks_to_match_against)
    
    # add case for loops mapping on station level
    # add case for missing mv statino
    # for mv_network in mv_networks:
        # mv_esdl_parser = EsdlNetworkParser(energy_system=mv_network)
        
        # shp_lv_networks = geo_data_network_builder.extract_network_and_topologies()
    
        # network_to_test = shp_lv_networks[5]
    
        # print(f"Amount of shp networks: {len(shp_lv_networks)}")
    
        # network_with_min_distance = topology_analyzer.find_best_matching_network(network_to_test)
    
        # amount_of_connections_esdl_network = sum([esdl_parser.get_amount_of_connections_bordering_line(line_string) for line_string in network_with_min_distance.network_lines])
        # amount_of_connections_network_to_test = sum([edge[1]["amount_of_connections"] for edge in network_to_test.network_topology.edges.items()])
        # print(f"Amount of connections in matched esdl network: {amount_of_connections_esdl_network}")
        # print(f"Amount of connections in tested gis network: {amount_of_connections_network_to_test}")

        # network_plotter = NetworkPlotter(1,1)
        # network_plotter.plot_network_topology(networks_to_match_against[5].network_topology)
        # network_plotter.plot_network(mv_esdl_parser.all_mv_lines)
        # network_plotter.plot_lv_network(esdl_parser.all_lv_lines)
        # network_plotter.plot_lv_network(network_parser.all_lv_lines)
        # network_plotter.plot_network_topology(network_to_test.network_topology)
        # network_plotter.plot_network_topology(network_with_min_distance.network_topology)
        # network_plotter.plot_lv_network(esdl_lv_networks[1].network_lines)
    
        # print(f"Graph edit distance between two graphs {graph_edit_distance(lv_network_topology_esdl, lv_network_topology_shp, timeout=300)}")
        # network_plotter.show_plot()

if __name__ == "__main__":
    exit(main())
