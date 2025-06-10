
from Topology_Generator.AllianderGeoDataNetworkParser import AllianderGeoDataNetworkParser
from Topology_Generator.GeoDataNetworkParser import GeneratorCableCase
from Topology_Generator.MvNetworkBuilder import MvNetworkBuilder
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
    generator_cable_case = GeneratorCableCase.THICK
    network_parser = AllianderGeoDataNetworkParser(geo_df_lv_lines, geo_df_mv_lv_stations, geo_df_bag_data, geo_df_mv_kabels, geo_df_hv_stations, generator_cable_case)
    
    mv_network_builder = MvNetworkBuilder(network_parser, x_bottom_left, y_bottom_left, x_top_right, y_top_right)


    mv_network = mv_network_builder.generate_a_mv_network("To-look-at")
    mv_network_builder.plot_mv_network(mv_network)

if __name__ == "__main__":
    exit(main())
