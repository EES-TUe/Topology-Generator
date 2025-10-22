from Topology_Generator.EsdlNetworkParser import EsdlNetworkParser
from Topology_Generator.NetworkPlotter import NetworkPlotter
import os

base_path = "C:/Users/20180029/repos/Topology-Generator/src/to_plot/"
for file in os.listdir(base_path):
    print(f"Plotting {file}")
    file_path = os.path.join(base_path, file)
    esdl_parser = EsdlNetworkParser(esdl_path=file_path)
    full_network_plotter = NetworkPlotter(1,1)
    full_network_plotter.plot_mv_network_with_lv_network(esdl_parser.all_mv_lines, esdl_parser.all_lv_lines + esdl_parser.lines_to_homes_line_strings)
    full_network_plotter.show_plot()