
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

def main():

    x_bottom_left = 157384
    y_bottom_left = 432937
    x_top_right = 159319
    y_top_right = 434915


    bbox = (x_bottom_left, y_bottom_left, x_top_right, y_top_right)

    # Bag data
    bag_data_gpkg = "<<path_to_your_gpkg>>/bag-data.gpkg"
    geo_df_bag_data : geopandas.GeoDataFrame = geopandas.read_file(bag_data_gpkg, layer='pand', bbox=bbox)

    # Alliander
    lv_lines_gpkg = "<<path_to_your_gpkg>>/alliander-lv-lines.gpkg"
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

if __name__ == "__main__":
    exit(main())
