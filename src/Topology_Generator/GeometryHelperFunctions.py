
from shapely import Polygon, Point, overlaps

OVERLAP_SQUARE_SIZE = 0.05
OVERLAP_SQUARE_CENTROID_DISTANCE = OVERLAP_SQUARE_SIZE / 2
CLOSE_MARGIN = 0.12

class GeometryHelperFunctions:
    def points_are_close(point_a, point_b): 
        return point_a[0] - CLOSE_MARGIN <= point_b[0] <= point_a[0] + CLOSE_MARGIN and point_a[1] - CLOSE_MARGIN <= point_b[1] <= point_a[1] + CLOSE_MARGIN
    
    def points_to_polygon(points) -> Polygon:
        return Polygon(points)

    def _create_point_box(point : Point) -> Polygon:
        point_box = Polygon([(point.x - OVERLAP_SQUARE_CENTROID_DISTANCE, point.y - OVERLAP_SQUARE_CENTROID_DISTANCE), 
                        (point.x - OVERLAP_SQUARE_CENTROID_DISTANCE, point.y + OVERLAP_SQUARE_CENTROID_DISTANCE), 
                        (point.x + OVERLAP_SQUARE_CENTROID_DISTANCE, point.y + OVERLAP_SQUARE_CENTROID_DISTANCE), 
                        (point.x + OVERLAP_SQUARE_CENTROID_DISTANCE, point.y - OVERLAP_SQUARE_CENTROID_DISTANCE)])
        return point_box
        
    def polygon_touches_point(point : Point, polygon : Polygon) -> bool:
        point_box = GeometryHelperFunctions._create_point_box(point)
        return overlaps(polygon, point_box)