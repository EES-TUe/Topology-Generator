
from Topology_Generator.LvNetworkPlotter import LvNetworkPlotter
from Topology_Generator.LvNetworkBuilder import LvNetworkBuilder
import geopandas

def main():
    # Full network
    x_bottom_left = 233256
    y_bottom_left = 583730
    x_top_right = 233701
    y_top_right = 583956
    bbox = (x_bottom_left, y_bottom_left, x_top_right, y_top_right)

    lv_lines_shape_file = "C://Users//20180029//repos//Topology-Generator//ENEXIS_Elektra_shape//Enexis_e_ls_verbinding//nbnl_e_ls_verbinding.shp"
    lv_mv_lines_shape_file = "C://Users//20180029//repos//Topology-Generator//ENEXIS_Elektra_shape//Enexis_e_ms_ls_station//nbnl_e_ms_ls_station.shp"

    geo_df_lv_lines : geopandas.GeoDataFrame = geopandas.read_file(lv_lines_shape_file, bbox=bbox)
    print(geo_df_lv_lines)
    geo_df_mv_lv_stations : geopandas.GeoDataFrame = geopandas.read_file(lv_mv_lines_shape_file, bbox=bbox)

    network_builder = LvNetworkBuilder(geo_df_lv_lines, geo_df_mv_lv_stations)
    starting_points = network_builder.extract_lv_lines_connected_to_mv_lv_station()
    lv_network = network_builder.build_lv_network(starting_points[0].starting_lines[0])
    lv_network2 = network_builder.build_lv_network(starting_points[1].starting_lines[0])

    lv_network_topology = network_builder.compute_lv_network_topology_from_lv_mv_station(starting_points[0].starting_lines[0])
    lv_network_topology2 = network_builder.compute_lv_network_topology_from_lv_mv_station(starting_points[1].starting_lines[0])

    network_plotter = LvNetworkPlotter(2,2)
    network_plotter.plot_lv_network(lv_network, starting_points[0].lv_mv_station)
    network_plotter.plot_lv_network(lv_network2, starting_points[1].lv_mv_station)
    network_plotter.plot_network_topology(lv_network_topology)
    network_plotter.plot_network_topology(lv_network_topology2)
    network_plotter.show_plot()

if __name__ == "__main__":
    exit(main())
