from dataclasses import dataclass
from typing import List
from esdl import esdl
from esdl.esdl_handler import EnergySystemHandler
from shapely import LineString, Point, dwithin

from Topology_Generator.EsdlHelperFunctions import EsdlHelperFunctions
from Topology_Generator.GeometryHelperFunctions import GeometryHelperFunctions
from Topology_Generator.NetworkParser import NetworkParser, StationStartingLinesContainer
from Topology_Generator.dataclasses import NavigationLineString

@dataclass
class MetaDataESDLCable:
    cable : esdl.ElectricityCable
    amount_of_connections : int
    attached_assets : List[esdl.ConnectableAsset]

class EsdlNetworkParser(NetworkParser):
    def __init__(self, esdl_path : str = "", energy_system : esdl.EnergySystem = None):
        if esdl_path != "":
            esh = EnergySystemHandler()
            esh.load_file(esdl_path)
            self.energy_system = esh.get_energy_system()
        elif energy_system != None:
            self.energy_system = energy_system
        self.line_string_meta_data : dict[LineString, MetaDataESDLCable]= {}
        self.lines_connected_to_transformer_mapping : dict[esdl.Transformer, StationStartingLinesContainer] = {}
        self.lines_to_homes : List[esdl.ElectricityCable] = []
        self.cables : List[esdl.ElectricityCable] = []
        self.transformers : List[esdl.Transformer] = []
        self.transformer_touch_margin = 0.00000001
        super().__init__()
        self._init_transformer_mapping()

    def _init_generic_collections(self) -> dict[esdl.ElectricityCable, MetaDataESDLCable]:
        esdl_obj_meta_data : dict[esdl.ElectricityCable, MetaDataESDLCable] = {}
        if len(self.energy_system.instance) == 1:
            assets = self.energy_system.instance[0].area.asset
            buildings = EsdlHelperFunctions.get_all_esdl_objects_from_type(assets, esdl.Building)
            homes = EsdlHelperFunctions.flatten_list_of_lists([EsdlHelperFunctions.get_all_esdl_objects_from_type(building.asset, esdl.EConnection) for building in buildings])
            self.homes_count = 0
            for home in homes:
                for port in EsdlHelperFunctions.get_all_in_ports_from_esdl_obj(home):
                    for esdl_out_port in port.connectedTo:
                        cable = esdl_out_port.eContainer()
                        # self.lines_to_homes.append(cable)
                        self.update_esdl_cable_metadata(cable, home.eContainer(), esdl_obj_meta_data)

            self.cables = EsdlHelperFunctions.get_all_esdl_objects_from_type(assets, esdl.ElectricityCable)
            self.transformers = EsdlHelperFunctions.get_all_esdl_objects_from_type(assets, esdl.Transformer)
            amount_of_connections = sum([esdl_obj_meta_data.amount_of_connections for esdl_obj_meta_data in esdl_obj_meta_data.values()])
            assert len(homes) == amount_of_connections
        return esdl_obj_meta_data

    def get_line_length_from_metadata(self, line_string : LineString) -> float:
        return self.line_string_meta_data[line_string].cable.length
    
    def get_amount_of_connections_bordering_line(self, line_string : LineString) -> int:
        return self.line_string_meta_data[line_string].amount_of_connections
    
    def get_transformer_connected_to_line_string(self, navigation_line_string : NavigationLineString) -> esdl.Transformer:
        coords = navigation_line_string.line_string.coords[-1] if navigation_line_string.first_point_end else navigation_line_string.line_string.coords[0]
        return next(transformer for transformer in self.transformers if dwithin(Point(transformer.geometry.lat, transformer.geometry.lon), Point(coords), self.transformer_touch_margin))
    
    def get_esdl_connected_assets_from_line_string(self, line_strings : List[LineString]) -> List[esdl.ConnectableAsset]:
        ret_val = []
        for line_string in line_strings:
            ret_val.append(self.line_string_meta_data[line_string].cable)
            ret_val.extend(self.line_string_meta_data[line_string].attached_assets)
        return ret_val
    
    def get_esdl_cable_from_line_string(self, line_string : LineString):
        return self.line_string_meta_data[line_string].cable

    def update_esdl_cable_metadata(self, electricity_cable : esdl.ElectricityCable, home : esdl.Building, esdl_obj_meta_data : dict[esdl.ElectricityCable, MetaDataESDLCable]):
        esdl_obj_to_follow = electricity_cable
        for port in EsdlHelperFunctions.get_all_in_ports_from_esdl_obj(esdl_obj_to_follow):
            for esdl_out_port in port.connectedTo:
                connection_joint = esdl_out_port.eContainer()
                in_ports_connection_joint = EsdlHelperFunctions.get_all_in_ports_from_esdl_obj(connection_joint)
                if len(in_ports_connection_joint) > 0 and len(in_ports_connection_joint[0].connectedTo) > 0 and isinstance(in_ports_connection_joint[0].connectedTo[0].eContainer(), esdl.ElectricityCable):
                    esdl_container = in_ports_connection_joint[0].connectedTo[0].eContainer()
                    if esdl_container not in esdl_obj_meta_data.keys():
                        esdl_obj_meta_data[esdl_container] = MetaDataESDLCable(esdl_container, 1, [home, electricity_cable, connection_joint])
                        self.homes_count += 1
                    else:
                        self.homes_count += 1
                        esdl_obj_meta_data[esdl_container].amount_of_connections += 1
                        esdl_obj_meta_data[esdl_container].attached_assets.append(home)
                        esdl_obj_meta_data[esdl_container].attached_assets.append(electricity_cable)
                else:
                    for port in EsdlHelperFunctions.get_all_out_ports_from_esdl_obj(connection_joint):
                        for in_port in port.connectedTo:
                            esdl_container = in_port.eContainer()
                            if isinstance(esdl_container, esdl.ElectricityCable) and "Home" not in esdl_container.name:
                                if esdl_container not in esdl_obj_meta_data.keys():
                                    esdl_obj_meta_data[esdl_container] = MetaDataESDLCable(esdl_container, 1, [home, electricity_cable, connection_joint])
                                    self.homes_count += 1
                                else:
                                    self.homes_count += 1
                                    esdl_obj_meta_data[esdl_container].amount_of_connections += 1
                                    esdl_obj_meta_data[esdl_container].attached_assets.append(home)
                                    esdl_obj_meta_data[esdl_container].attached_assets.append(electricity_cable)
                                break

    def extract_lv_lines_connected_to_mv_lv_station(self) -> List[StationStartingLinesContainer]:
        return [value for value in self.lines_connected_to_transformer_mapping.values()]

    def _init_transformer_mapping(self) -> List[StationStartingLinesContainer]:
        for transformer in self.transformers:
            transformer_location = Point(transformer.geometry.lat, transformer.geometry.lon)
            lv_lines_indices = self.str_tree_lv_lines.query(transformer_location, 'touches')
            lines_intersecting_with_station = []
            for index in lv_lines_indices:
                lv_line = self.str_tree_lv_lines.geometries.take(index)
                point_touches_mv_station = GeometryHelperFunctions.points_are_close(lv_line.coords[0], (transformer.geometry.lat, transformer.geometry.lon)) 
                lines_intersecting_with_station.append(NavigationLineString(lv_line, not point_touches_mv_station, index))
            self.lines_connected_to_transformer_mapping[transformer] = StationStartingLinesContainer(lines_intersecting_with_station, 1)
    
    def extract_lv_lines_connected_to_mv_lv_station_at_point(self, point : Point) -> List[NavigationLineString]:
        for transformer in self.transformers:
            transformer_location = Point(transformer.geometry.lat, transformer.geometry.lon)
            if dwithin(transformer_location, point, self.transformer_touch_margin):
                return self.lines_connected_to_transformer_mapping[transformer].starting_lines
        return []

    def _extract_lv_network_lines(self) -> List[LineString]:
        esdl_obj_meta_data = self._init_generic_collections()
        ret_val = []

        for cable in self.cables:
            points = []
            if cable not in self.lines_to_homes:
                for geo_property in cable.geometry.eAllContents():
                    if isinstance(geo_property, esdl.Point):
                        new_point = (geo_property.lat, geo_property.lon)
                        points.append(new_point)
                new_line_string = LineString(points)
                if new_line_string not in ret_val:
                    ret_val.append(new_line_string)
                    self.line_string_meta_data[new_line_string] = esdl_obj_meta_data[cable] if cable in esdl_obj_meta_data.keys() else MetaDataESDLCable(cable, 0, [cable.port[0].connectedTo[0].eContainer(), cable.port[1].connectedTo[0].eContainer()])
        return ret_val
