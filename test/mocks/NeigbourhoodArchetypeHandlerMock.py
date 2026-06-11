from unittest.mock import MagicMock
from shapely import Point
from Topology_Generator.NeighbourhoodArchetypeHandler import NeighbourhoodArchetypeHandler

class NeigbourhoodArchetypeHandlerMock(NeighbourhoodArchetypeHandler):

    def __init__(self):
        self.init_neighbourhood_data = MagicMock()
        self.convert_gis_coordinates_to_archetype_coordinates = MagicMock(return_value=Point(2,1))
        self.archetype_at_point = MagicMock(return_value=2)