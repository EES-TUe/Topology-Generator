
from typing import List
from shapely import Polygon, Point, intersects, LineString, STRtree, covers

import numpy as np

from Topology_Generator.dataclasses import NavigationLineString

OVERLAP_SQUARE_SIZE = 0.05
OVERLAP_SQUARE_CENTROID_DISTANCE = OVERLAP_SQUARE_SIZE / 2
CLOSE_MARGIN = 0.02

class GeometryHelperFunctions:
    
    @staticmethod
    def points_are_close(point_a, point_b, margin = CLOSE_MARGIN ): 
        return point_a[0] - margin <= point_b[0] <= point_a[0] + margin and point_a[1] - margin <= point_b[1] <= point_a[1] + margin

    @staticmethod
    def points_to_polygon(points) -> Polygon:
        return Polygon(points)

    @staticmethod
    def _create_point_box(point : Point, margin : float = OVERLAP_SQUARE_CENTROID_DISTANCE) -> Polygon:
        point_box = Polygon([(point.x - margin, point.y - margin), 
                        (point.x - margin, point.y + margin), 
                        (point.x + margin, point.y + margin), 
                        (point.x + margin, point.y - margin)])
        return point_box

    @staticmethod
    def polygon_touches_point(point : Point, polygon : Polygon, margin = OVERLAP_SQUARE_CENTROID_DISTANCE) -> bool:
        point_box = GeometryHelperFunctions._create_point_box(point, margin)
        return intersects(polygon, point_box)
    
    @staticmethod
    def line_string_connected_to_point(point : Point, line_2 : LineString, index : int) -> NavigationLineString:
        endpoint_1 = Point(line_2.coords[0])
        endpoint_2 = Point(line_2.coords[-1])

        point_first_end = False
        if covers(endpoint_1, point):
            point_first_end = False
        elif covers(endpoint_2, point):
            point_first_end = True
        else:
            return None
        return NavigationLineString(line_2, point_first_end, index)

    @staticmethod
    def get_next_lines(str_tree_lines : STRtree, navigation_line_string : NavigationLineString) -> List[NavigationLineString]:
        point_to_connect_to = Point(navigation_line_string.line_string.coords[0]) if navigation_line_string.first_point_end else Point(navigation_line_string.line_string.coords[-1])
        intersecting_indices = str_tree_lines.query(point_to_connect_to, 'touches')
        intersecting_indices = np.setdiff1d(intersecting_indices, np.array([navigation_line_string.index]))

        ret_val = []
        for index in intersecting_indices:
            next_line = str_tree_lines.geometries.take(index)
            next_line_string_end_pair = GeometryHelperFunctions.line_string_connected_to_point(point_to_connect_to, next_line, index)
            if next_line_string_end_pair != None:
                ret_val.append(next_line_string_end_pair)
        return ret_val
    
    @staticmethod
    def get_end_coords(navigation_line_string : NavigationLineString):
        return navigation_line_string.line_string.coords[0] if navigation_line_string.first_point_end else navigation_line_string.line_string.coords[-1]
    
    @staticmethod
    def get_connected_coords(navigation_line_string : NavigationLineString):
        return navigation_line_string.line_string.coords[-1] if navigation_line_string.first_point_end else navigation_line_string.line_string.coords[0]