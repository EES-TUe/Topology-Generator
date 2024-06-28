
from typing import List
from shapely import LineString, Polygon
import matplotlib.pyplot as plt
import networkx as nx

from Topology_Generator.GeometryHelperFunctions import GeometryHelperFunctions


class LvNetworkPlotter:

    def __init__(self, n_rows, n_cols):
        self.subplot_rows = n_rows
        self.subplot_columns = n_cols
        self.subplot_index = 1

    def _annotation_near(self, annotations : List[tuple], new_annotation : tuple):
        return any(GeometryHelperFunctions.points_are_close(annotation, new_annotation) for annotation in annotations)

    def _add_annotation(self, annotations : List[tuple], new_annotation : tuple) -> tuple:
        near = self._annotation_near(annotations, new_annotation)
        while near:
            new_annotation = (new_annotation[0], new_annotation[1] + 1.25 )
            near = self._annotation_near(annotations, new_annotation)
        annotations.append(new_annotation)
        return new_annotation
    
    def plot_lines(self, color, lines, with_line_numbers):
        annotations = []
        for i, line in enumerate(lines):
            plt.plot(*line.xy, color=color)
            if with_line_numbers:
                plt.annotate(str(i), self._add_annotation(annotations, line.coords[0]))
                plt.annotate(str(i), self._add_annotation(annotations, line.coords[-1]))

    def plot_shapes(self, color, shapes):
        for shape in shapes:
            plt.plot(*shape.xy, color=color)

    def plot_lv_network(self, lv_network_lines : List[LineString], mv_lv_station : Polygon, with_line_numbers = False):
        plt.subplot(self.subplot_rows, self.subplot_columns, self.subplot_index)
        self.subplot_index += 1
        self.plot_lines('blue', lv_network_lines, with_line_numbers)
        self.plot_shapes('green', [mv_lv_station])
    
    def plot_network_topology(self, topology : nx.Graph):
        plt.subplot(self.subplot_rows, self.subplot_columns, self.subplot_index)
        self.subplot_index += 1
        nx.draw_networkx(topology, with_labels=True)
    
    def show_plot(self):
        plt.show()
    