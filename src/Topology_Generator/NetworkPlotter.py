
from typing import List
from shapely import LineString, Polygon
import matplotlib.pyplot as plt
import networkx as nx
import string

from Topology_Generator.GeometryHelperFunctions import GeometryHelperFunctions


class NetworkPlotter:

    def __init__(self, n_rows, n_cols, label_subplots = True):
        self.subplot_rows = n_rows
        self.subplot_columns = n_cols
        self.subplot_index = 1
        self.label_subplots = label_subplots

    def _annotation_near(self, annotations : List[tuple], new_annotation : tuple):
        return any(GeometryHelperFunctions.points_are_close(annotation, new_annotation) for annotation in annotations)

    def _add_annotation(self, annotations : List[tuple], new_annotation : tuple):
        near = self._annotation_near(annotations, new_annotation)
        while near:
            MARGIN_BETWEEN_ANNOTATIONS = 1.25
            new_annotation = (new_annotation[0], new_annotation[1] + MARGIN_BETWEEN_ANNOTATIONS )
            near = self._annotation_near(annotations, new_annotation)
        annotations.append(new_annotation)
        return new_annotation
    
    def _add_subplot(self):
        axs = plt.subplot(self.subplot_rows, self.subplot_columns, self.subplot_index)
        if self.label_subplots:
            axs.annotate(
                f"{string.ascii_lowercase[self.subplot_index - 1]})",
                xy=(0, 1), xycoords='axes fraction',
                xytext=(+0.5, -0.5), textcoords='offset fontsize',
                fontsize='large', verticalalignment='top', fontfamily='serif',
                bbox=dict(facecolor='1.0', edgecolor='none', pad=3.0))
        self.subplot_index += 1

    def plot_lines(self, color, lines, with_line_numbers, without_axis_numbers=False):
        annotations = []
        for i, line in enumerate(lines):
            plt.plot(*line.xy, color=color)
            if with_line_numbers:
                plt.annotate(str(i), self._add_annotation(annotations, line.coords[0]))
                plt.annotate(str(i), self._add_annotation(annotations, line.coords[-1]))
            if without_axis_numbers:
                plt.xticks([])
                plt.yticks([])

    def plot_shapes(self, color, shapes):
        for shape in shapes:
            plt.plot(*shape.xy, color=color)

    def plot_mv_network_with_lv_network(self, mv_network_lines : List[LineString], lv_network_lines : List[LineString], mv_network_color : str = "blue", lv_network_color : str = "red"):
        self._add_subplot()
        self.plot_lines(mv_network_color, mv_network_lines, False, True)
        self.plot_lines(lv_network_color, lv_network_lines, False, True)

    def plot_network(self, lv_network_lines : List[LineString], mv_lv_station : Polygon = None, with_line_numbers = False, without_axis_numbers = False, network_color : str = 'blue'):
        self._add_subplot()
        self.plot_lines(network_color, lv_network_lines, with_line_numbers, without_axis_numbers)
        if mv_lv_station != None:
            self.plot_shapes('green', [mv_lv_station])

    def plot_network_topology(self, topology : nx.Graph):
        self._add_subplot()
        nx.draw_networkx(topology, with_labels=True)

    def show_plot(self):
        plt.show()