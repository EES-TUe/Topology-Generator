from Topology_Generator.EsdlNetworkParser import EsdlNetworkParser
from Topology_Generator.NetworkPlotter import NetworkPlotter
import os

base_path = "C:/Users/20180029/repos/Topology-Generator/src/to_plot/"
for file in os.listdir(base_path):
    print(f"Plotting {file}")
    file_path = os.path.join(base_path, file)
    esdl_parser = EsdlNetworkParser(esdl_path=file_path)
    full_network_plotter = NetworkPlotter(1,1)
    lines_to_exclude = [ "MV_Cable197"]
    line_strings_to_exclude = [esdl_parser.mv_line_string_meta_data[line] for line in lines_to_exclude if line in esdl_parser.mv_line_string_meta_data]
    mv_lines_to_plot = [line for line in esdl_parser.all_mv_lines if line not in line_strings_to_exclude]
    full_network_plotter.plot_mv_network_with_lv_network(mv_lines_to_plot, esdl_parser.all_lv_lines + esdl_parser.lines_to_homes_line_strings)
    full_network_plotter.show_plot()