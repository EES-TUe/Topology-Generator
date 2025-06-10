from dataclasses import dataclass
from typing import List
import uuid

import esdl
from shapely import STRtree, Point
from Topology_Generator.EsdlHelperFunctions import EsdlHelperFunctions
from Topology_Generator.EsdlNetworkParser import EsdlNetworkParser
from Topology_Generator.GeometryHelperFunctions import GeometryHelperFunctions
from Topology_Generator.NetworkParser import NetworkParser, StationStartingLinesContainer
from datetime import datetime
from esdl.esdl_handler import EnergySystemHandler
from Topology_Generator.Logging import LOGGER

from Topology_Generator.NetworkPlotter import NetworkPlotter
from Topology_Generator.dataclasses import NavigationLineString

@dataclass
class EsdlAssetWithMetaData:
    esdl_obj : esdl.Asset
    number : int

class MvNetworkBuilder:
    def __init__(self, parser : NetworkParser, x_bottom_left : float, y_bottom_left : float, x_top_right : float, y_top_right : float):
        self.str_tree_lv_lines : STRtree = parser.str_tree_lv_lines
        self.str_tree_mv_lines : STRtree = parser.str_tree_mv_lines
        self.parser = parser
        self.high_voltage_trafo_name = "HighVoltageTrafo"
        self.x_bottom_left = x_bottom_left
        self.y_bottom_left = y_bottom_left
        self.x_top_right = x_top_right
        self.y_top_right = y_top_right
        self.all_visited_lines = []
        self.starting_lines_containers : List[StationStartingLinesContainer] = []
        self.starting_lines_container_index = 0
        self.starting_line_index = 0

    def plot_mv_network(self, mv_network : esdl.EnergySystem):
        esdl_parser = EsdlNetworkParser(energy_system=mv_network)
        plotter = NetworkPlotter(1,1, False)
        plotter.plot_network(esdl_parser.all_lv_lines, without_axis_numbers=True)
        plotter.show_plot()

    def _get_lines_connected_to_mv_station_at(self, navigation_line : NavigationLineString):
        connection_point = Point(self._get_end_coords_from_navigation_line_string(navigation_line))
        next_navigation_line_strings = self.parser.extract_mv_lines_connected_to_mv_lv_station_at_point(connection_point)
        return next_navigation_line_strings

    def _navigations_line_string_is_in_list(self, navigation_line, next_navigation_line_strings):
        existing_line = next((new_navigation_line for new_navigation_line in next_navigation_line_strings if new_navigation_line.index == navigation_line.index), None)
        return existing_line
    
    def _generate_new_transformer(self, lat : float, long : float, name : str, commissioning_date : datetime = datetime.min):
        transformer = esdl.Transformer(id=str(uuid.uuid4()), name=name, assetType="testtrafotype", voltagePrimary=50.0, voltageSecundary=10.0, commissioningDate=commissioning_date)
        transformer.geometry = esdl.Point(lat=lat, lon=long, CRS="WGS84")
        transformer.port.append(esdl.InPort(id=str(uuid.uuid4()), name="In"))
        transformer.port.append(esdl.OutPort(id=str(uuid.uuid4()), name="Out"))
        return transformer
    
    def _generate_esdl_cable(self, navigation_line_string : NavigationLineString) -> esdl.ElectricityCable:
        cable = esdl.ElectricityCable(id=str(uuid.uuid4()), length=navigation_line_string.line_string.length, name=f"Cable{navigation_line_string.index}", assetType="testtype")
        esdl_line = esdl.Line()
        for p in navigation_line_string.line_string.coords:
            esdl_line.point.append(esdl.Point(lat=p[0], lon=p[1], CRS="WGS84"))
        cable.geometry = esdl_line
        cable.port.append(esdl.InPort(id=str(uuid.uuid4()), name="In"))
        cable.port.append(esdl.OutPort(id=str(uuid.uuid4()), name="Out"))
        return cable

    def _connect_edge_to_nodes(self, from_node, esdl_cable, to_node):
        esdl_cable.port[1].connectedTo.append(to_node.port[0])
        esdl_cable.port[0].connectedTo.append(from_node.esdl_obj.port[1])
        from_node.esdl_obj.port[1].connectedTo.append(esdl_cable.port[0])
        to_node.port[0].connectedTo.append(esdl_cable.port[1])
    
    def _get_end_coords_from_navigation_line_string(self, navigation_line_string : NavigationLineString):
        return navigation_line_string.line_string.coords[0] if navigation_line_string.first_point_end else navigation_line_string.line_string.coords[-1]

    def _add_esdl_node_and_edge(self, navigation_line_string : NavigationLineString, from_node : EsdlAssetWithMetaData, to_node : esdl.ConnectableAsset, esdl_objs : List[esdl.ConnectableAsset]) -> EsdlAssetWithMetaData:
        new_cable = self._generate_esdl_cable(navigation_line_string)
        self._connect_edge_to_nodes(from_node, new_cable, to_node)
        esdl_objs.append(new_cable)
        esdl_objs.append(to_node)
        return EsdlAssetWithMetaData(to_node, from_node.number + 1)

    def _find_last_trafo_with_building_year(self, esdl_objs):
        last_trafo_with_building_year = None
        try:
            last_trafo_with_building_year = next(esdl_obj for esdl_obj in reversed(esdl_objs) if (isinstance(esdl_obj, esdl.Transformer) or isinstance(esdl_obj, esdl.Joint)) and esdl_obj.commissioningDate != None and esdl_obj.commissioningDate != datetime.min)
        except StopIteration:
            raise ValueError(f"No building year found! ({esdl_objs[-1].geometry.lon}, {esdl_objs[-1].geometry.lat})")
        return last_trafo_with_building_year
    
    def _update_cable_types(self, year : int, esdl_objs : List[esdl.ConnectableAsset]):
        last_trafo = self._find_last_trafo_with_building_year(esdl_objs)
        trafo_year = 0
        if last_trafo != None:
            trafo_year = last_trafo.commissioningDate.year

        cable_year = max(trafo_year, year)
        for esdl_obj in reversed(esdl_objs):
            if isinstance(esdl_obj, esdl.ElectricityCable):
                esdl_obj.assetType = self.parser.define_cable_type_based_on_year(year)
                esdl_obj.eSet("commissioningDate", datetime(cable_year, 1, 1))
            if isinstance(esdl_obj, esdl.Transformer):
                break

    def _add_esdl_node_and_joint(self, navigation_line_string : NavigationLineString, from_node : EsdlAssetWithMetaData, esdl_objs : List[esdl.ConnectableAsset]):
        coords = GeometryHelperFunctions.get_end_coords(navigation_line_string)
        lat = coords[0]
        long = coords[1]
        to_node = EsdlHelperFunctions.generate_esdl_joint(lat, long, f"joint{from_node.number}")
        return self._add_esdl_node_and_edge(navigation_line_string, from_node, to_node, esdl_objs)

    def _add_esdl_node_and_transformer(self, navigation_line_string : NavigationLineString, from_node : EsdlAssetWithMetaData, esdl_objs : List[esdl.ConnectableAsset]):
        coords = GeometryHelperFunctions.get_end_coords(navigation_line_string)
        lat = coords[0]
        long = coords[1]
        building_year = self.parser.get_building_year_of_transformer_house_at_point(Point(lat, long))
        to_transformer = self._generate_new_transformer(lat, long, f"transformer{from_node.number}")
        to_node = EsdlHelperFunctions.generate_esdl_joint(lat, long, f"joint{from_node.number}")
        to_transformer.port[0].connectedTo.append(to_node.port[1])
        to_node.port[1].connectedTo.append(to_transformer.port[0])
        from_node = self._add_esdl_node_and_edge(navigation_line_string, from_node, to_node, esdl_objs)
        from_node.number += 1
        lv_transformer_node = EsdlHelperFunctions.generate_esdl_joint(lat, long, f"joint{from_node.number}")
        lv_transformer_node.port[0].connectedTo.append(to_transformer.port[1])
        esdl_objs.append(lv_transformer_node)
        esdl_objs.append(to_transformer)
        if building_year != 1:
            to_transformer.eSet("commissioningDate", datetime(building_year, 1, 1))
            to_node.eSet("commissioningDate", datetime(building_year, 1, 1))
            self._update_cable_types(building_year, esdl_objs[:-1])
        else:
            last_trafo_building_year = self._find_last_trafo_with_building_year(esdl_objs)
            to_transformer.eSet("commissioningDate", datetime(last_trafo_building_year.commissioningDate.year, 1, 1))
            to_node.eSet("commissioningDate", datetime(last_trafo_building_year.commissioningDate.year, 1, 1))
            self._update_cable_types(last_trafo_building_year.commissioningDate.year, esdl_objs[:-1])
        return from_node

    def _add_loop_back_cable(self, navigation_line_string : NavigationLineString, from_node : esdl.ConnectableAsset, ret_val : List[esdl.ConnectableAsset], station_at_end_of_line : esdl.ConnectableAsset):
        esdl_cable = self._generate_esdl_cable(navigation_line_string)
        last_added_station = self._find_last_trafo_with_building_year(ret_val)
        to_node = station_at_end_of_line
        self._connect_edge_to_nodes(from_node, esdl_cable, to_node)
        commisioning_year = max(to_node.commissioningDate.year, last_added_station.commissioningDate.year)
        esdl_cable.commissioningDate = datetime(commisioning_year, 1, 1)
        ret_val.append(esdl_cable)
        self._update_cable_types(commisioning_year, ret_val)

    def _build_mv_network_recursive(self, navigation_line_string : NavigationLineString, from_node : EsdlAssetWithMetaData, visited_lines : set, loops_mapping) -> List[esdl.ConnectableAsset]:
        ret_val = [from_node.esdl_obj]
        if navigation_line_string.index not in visited_lines:
            visited_lines.add(navigation_line_string.index)
            next_navigation_line_strings, next_navigation_line_strings_connected_to_station = self._define_next_lines(navigation_line_string, visited_lines)
            cleared = False
            while len(next_navigation_line_strings) + len(next_navigation_line_strings_connected_to_station) > 0:
                coords = GeometryHelperFunctions.get_end_coords(navigation_line_string)
                if len(next_navigation_line_strings_connected_to_station) > 1:
                    # Case the line ending has multiple branches
                    station_at_end_of_line = loops_mapping.get(coords, None)
                    if station_at_end_of_line != None:
                        # Case alogrithm has looped back to a point it has been before and next lines are found
                        self._add_loop_back_cable(navigation_line_string, from_node, ret_val, station_at_end_of_line)
                    elif all(next_line_string_end_pair.index not in visited_lines for next_line_string_end_pair in next_navigation_line_strings_connected_to_station):
                        # Case alogrithm has found a new intersection of lines
                        common_point = GeometryHelperFunctions.get_end_coords(navigation_line_string)
                        from_node = self._add_esdl_node_and_transformer(navigation_line_string, from_node, ret_val)
                        loops_mapping[common_point] = from_node.esdl_obj
                    if (station_at_end_of_line != None and self.high_voltage_trafo_name not in station_at_end_of_line.name) or station_at_end_of_line == None:
                        # Only go deeper in recursion if the algorithm has not arrived back at the high voltage station it started
                        ret_val_len_old = len(ret_val)
                        for next_navigation_line_string in next_navigation_line_strings_connected_to_station:
                            LOGGER.debug(f"Diving deeper in recursion at point {coords}")
                            new_assets = self._build_mv_network_recursive(next_navigation_line_string, from_node, visited_lines, loops_mapping)
                            ret_val.extend(new_assets[1:])
                        if ret_val_len_old == len(ret_val):
                            # Case we have only found dead ends so we do not have a medium voltage ring
                            # So we clear the asset list because we are only interested in mv rings
                            ret_val.clear()
                            cleared = True

                    next_navigation_line_strings.clear()
                    next_navigation_line_strings_connected_to_station.clear()
                    cleared = True
                elif len(next_navigation_line_strings) == 1:
                    # The line has no branches
                    from_node = self._add_esdl_node_and_joint(navigation_line_string, from_node, ret_val)
                    navigation_line_string = next_navigation_line_strings[0]
                    visited_lines.add(navigation_line_string.index)
                    next_navigation_line_strings, next_navigation_line_strings_connected_to_station = self._define_next_lines(navigation_line_string, visited_lines)

                elif len(next_navigation_line_strings_connected_to_station) == 1:
                    # The line is connected to an mv station
                    from_node = self._add_esdl_node_and_transformer(navigation_line_string, from_node, ret_val)
                    navigation_line_string = next_navigation_line_strings_connected_to_station[0]
                    visited_lines.add(navigation_line_string.index)
                    next_navigation_line_strings, next_navigation_line_strings_connected_to_station = self._define_next_lines(navigation_line_string, visited_lines)

            coords = GeometryHelperFunctions.get_end_coords(navigation_line_string)
            if len(next_navigation_line_strings) + len(next_navigation_line_strings_connected_to_station) == 0 and coords in loops_mapping and not cleared:
                # Case we have looped back to a station but no next lines are found
                visited_lines.add(navigation_line_string.index)
                self._add_loop_back_cable(navigation_line_string, from_node, ret_val, loops_mapping[coords])
            elif len(next_navigation_line_strings) == 0 and not cleared:
                # Case we have reached a dead end 
                # So we clear the asset list because we are only interested in mv rings
                visited_lines.add(navigation_line_string.index)
                ret_val.clear()

        esh = EnergySystemHandler()
        es = esh.create_empty_energy_system(name="Intermittend", es_description="Autogenerated based on gis data ",
                                            inst_title="Instance name", area_title="Area name")

        energy_system_information = esdl.EnergySystemInformation(id=str(uuid.uuid4()))
        es.energySystemInformation = energy_system_information
        if len(ret_val) > 0:
            EsdlHelperFunctions.add_new_assets_to_energy_system(es, ret_val)

            self.plot_mv_network(es)

        return ret_val

    def _remove_out_of_bounds_lines(self, next_navigation_line_strings : List[NavigationLineString]):
        out_of_bounds_strings = [next_navigation_line_string for next_navigation_line_string in next_navigation_line_strings if 
                                GeometryHelperFunctions.get_end_coords(next_navigation_line_string)[0] < self.x_bottom_left or 
                                GeometryHelperFunctions.get_end_coords(next_navigation_line_string)[1] > self.y_top_right or 
                                GeometryHelperFunctions.get_end_coords(next_navigation_line_string)[0] > self.x_top_right or 
                                GeometryHelperFunctions.get_end_coords(next_navigation_line_string)[1] < self.y_bottom_left]
        for out_of_bounds_string in out_of_bounds_strings:
            next_navigation_line_strings.remove(out_of_bounds_string)

    def _remove_duplicate_lines(self, visited_indices : set, next_navigation_line_strings : List[NavigationLineString]):
        existing_lines = [navigation_line_string for navigation_line_string in next_navigation_line_strings if navigation_line_string.index in visited_indices]
        for existing_line in existing_lines:
            next_navigation_line_strings.remove(existing_line)

    def _get_next_lines_mv_network(self, navigation_line : NavigationLineString) -> List[NavigationLineString]:
        next_navigation_line_strings = GeometryHelperFunctions.get_next_lines(self.str_tree_mv_lines, navigation_line)
        return next_navigation_line_strings

    def _define_next_lines(self, navigation_line_string, visited_indices):
        next_navigation_line_strings = self._get_next_lines_mv_network(navigation_line_string)
        coords = GeometryHelperFunctions.get_end_coords(navigation_line_string)
        next_navigation_line_strings_connected_to_station = []
        if len(next_navigation_line_strings) == 0:
            next_navigation_line_strings_connected_to_station = self._get_lines_connected_to_mv_station_at(navigation_line_string)
            if len(next_navigation_line_strings_connected_to_station) == 0:
                next_navigation_line_strings_connected_to_station = self.parser.extract_mv_lines_connected_to_hv_mv_station_at_point(Point(coords))
            if len(next_navigation_line_strings) == 0 and len(next_navigation_line_strings_connected_to_station) == 0:
                next_navigation_line_strings_connected_to_station = self.parser.extract_mv_lines_that_are_connected_at_point(Point(GeometryHelperFunctions.get_end_coords(navigation_line_string)))
        self._remove_out_of_bounds_lines(next_navigation_line_strings)
        self._remove_duplicate_lines(visited_indices, next_navigation_line_strings)
        self._remove_duplicate_lines(visited_indices, next_navigation_line_strings_connected_to_station)
        return next_navigation_line_strings, next_navigation_line_strings_connected_to_station
    
    def _initialize_starting_parameters(self):
        if len(self.starting_lines_containers) == 0:
            self.starting_lines_containers = self.parser.extract_mv_lines_connected_to_hv_mv_station()

        LOGGER.debug(f"Extracting starting lines at index: {self.starting_lines_container_index}/{len(self.starting_lines_containers)}")
        starting_line_container = self.starting_lines_containers[self.starting_lines_container_index]

        starting_line = starting_line_container.starting_lines[self.starting_line_index]
        while starting_line.index in self.all_visited_lines:
            self.starting_line_index += 1
            if self.starting_line_index >= len(starting_line_container.starting_lines):
                self.all_visited_lines.clear()
                if self.starting_lines_container_index + 1 >= len(self.starting_lines_containers):
                    raise ValueError("Explored all paths no MV network left to find")
                else:
                    self.starting_lines_container_index += 1
                self.starting_line_index = 0
                starting_line_container = self.starting_lines_containers[self.starting_lines_container_index]
            starting_line = starting_line_container.starting_lines[self.starting_line_index]

        default_loops_mapping = {}
        for sl in starting_line_container.starting_lines:
            key = sl.line_string.coords[-1] if sl.first_point_end else sl.line_string.coords[0]
            default_loops_mapping[key] = None

        return default_loops_mapping, starting_line, starting_line_container.building_year

    def generate_a_mv_network(self, name : str, save_network : bool = False) -> esdl.EnergySystem:
        network_assets = []
        while len(network_assets) == 0:
            default_loops_mapping, starting_line, building_year = self._initialize_starting_parameters()

            esh = EnergySystemHandler()
            coords = GeometryHelperFunctions.get_connected_coords(starting_line)
            trafo_commisioning_date = datetime(building_year, 1, 1)
            
            transformer = self._generate_new_transformer(coords[0], coords[1], name=self.high_voltage_trafo_name, commissioning_date=trafo_commisioning_date)
            joint = EsdlHelperFunctions.generate_esdl_joint(coords[0], coords[1], name=f"joint{self.high_voltage_trafo_name}")
            joint.commissioningDate = trafo_commisioning_date
            transformer.port[0].connectedTo.append(joint.port[1])
            joint.port[1].connectedTo.append(transformer.port[0])

            network_name = f"{name}-{self.starting_lines_container_index}.{self.starting_line_index}"
            file_name = f"{network_name}.esdl"
            es = esh.create_empty_energy_system(name=network_name, es_description="Autogenerated based on gis data " + name,
                                            inst_title="Instance name", area_title="Area name")
            for key in default_loops_mapping.keys():
                default_loops_mapping[key] = joint

            energy_system_information = esdl.EnergySystemInformation(id=str(uuid.uuid4()))
            es.energySystemInformation = energy_system_information
            loops_mapping = default_loops_mapping.copy()
            visited_lines = set()
            network_assets = self._build_mv_network_recursive(starting_line, EsdlAssetWithMetaData(joint, 0), visited_lines, loops_mapping)
            self.all_visited_lines.extend(visited_lines)
            if len(network_assets) > 0:
                EsdlHelperFunctions.add_new_assets_to_energy_system(es, network_assets)
                EsdlHelperFunctions.add_new_assets_to_energy_system(es, [transformer])
                if save_network:
                    esh.save(file_name)
        return es