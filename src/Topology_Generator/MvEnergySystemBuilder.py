import uuid
from esdl import EnergySystem, esdl
from Topology_Generator import Constants
from Topology_Generator.GeometryHelperFunctions import GeometryHelperFunctions
from Topology_Generator.EsdlHelperFunctions import EsdlHelperFunctions
from Topology_Generator.LvNetworkBuilder import LvNetworkBuilder
from Topology_Generator.NeighbourhoodArchetypeHandler import NeighbourhoodArchetypeHandler
from Topology_Generator.NetworkPlotter import NetworkPlotter
from Topology_Generator.dataclasses import LineToHomeInput, NavigationLineString, NetworkTopologyInfo
from typing import List
from shapely import Point, LineString, distance, STRtree, dwithin
from shapely.ops import nearest_points
from Topology_Generator.Logging import LOGGER
from esdl.esdl_handler import EnergySystemHandler


class MvEnergySystemBuilder:

    def __init__(self, lv_network_builder : LvNetworkBuilder, archetype_handler : NeighbourhoodArchetypeHandler):
        self.archetype_handler = archetype_handler
        self.lv_network_builder = lv_network_builder
        self.home_counter = 1


    def generate_esdl_homes(self, coords : tuple[float, float], amount_of_homes : int, archetype : int) -> List[esdl.Building]:
        ret_val = []
        for i in range(0, amount_of_homes):
            esdl_home = self.generate_esdl_home(coords, archetype)
            ret_val.append(esdl_home)
        return ret_val


    def generate_esdl_home(self, coords : tuple[float, float], archetype : int) -> esdl.Building:
        building_point = EsdlHelperFunctions.generate_esdl_point(coords[0], coords[1])
        name = f"home_{self.home_counter}_arch{archetype}"
        building = esdl.Building(name=name, id=str(uuid.uuid4()))
        building.geometry = building_point
        e_connection = esdl.EConnection(name=name, id=str(uuid.uuid4()))
        e_connection.geometry = building_point
        e_connection.port.append(esdl.InPort(id=str(uuid.uuid4()), name="In"))
        electricity_demand = esdl.ElectricityDemand(name="demand", id=str(uuid.uuid4()), assetType="home_demand")
        for i in range(0, 3):

            phase = i + 1
            electricity_demand_in_port = esdl.InPort(id=str(uuid.uuid4()), name=f"In_Ph{phase}")
            electricity_demand.port.append(electricity_demand_in_port)

            electricity_network = esdl.ElectricityNetwork(name=f"ph{phase}")
            in_port_electricity_network = esdl.InPort(id=str(uuid.uuid4()), name="In")
            out_port_econnection = esdl.OutPort(id=str(uuid.uuid4()), name=f"OutPh{phase}")

            in_port_electricity_network.connectedTo.append(out_port_econnection)
            out_port_econnection.connectedTo.append(in_port_electricity_network)

            e_connection.port.append(out_port_econnection)
            electricity_network.port.append(in_port_electricity_network)
            phase_out_port = esdl.OutPort(id=str(uuid.uuid4()), name="Out")
            electricity_network.port.append(phase_out_port)
            phase_out_port.connectedTo.append(electricity_demand_in_port)
            electricity_demand_in_port.connectedTo.append(phase_out_port)

            building.asset.append(electricity_network)
        building.asset.append(electricity_demand)
        building.asset.append(e_connection)
        self.home_counter += 1
        return building


    def generate_lines_connected_to_homes(self, transformer_prefix : str, lv_network_str_tree : STRtree, network_topology_info : NetworkTopologyInfo) -> List[LineToHomeInput]:
        ret_val = []
        LOGGER.info(f"Adding lines to homes for network with connections: {network_topology_info.amount_of_connections}")

        for building_entity in network_topology_info.buildings:
            building = building_entity.geometry.iloc[0]
            closest_line_index = lv_network_str_tree.nearest(building_entity.geometry)
            closest_line = lv_network_str_tree.geometries.take(closest_line_index)[0]
            point_on_building, point_on_line = nearest_points(building, closest_line)
            new_linestring_to_home = LineString([point_on_line, point_on_building])
            amount_of_connections = building_entity["aantal_verblijfsobjecten"].iloc[0]
            if amount_of_connections == 0:
                amount_of_connections = 1
            archetype = self.archetype_handler.archetype_at_point(point_on_building)
            esdl_buildings = self.generate_esdl_homes(new_linestring_to_home.coords[-1], amount_of_connections, archetype)
            for esdl_building in esdl_buildings:
                name = f"lv_cable_{transformer_prefix}_to_{esdl_building.name}"
                length = new_linestring_to_home.length if new_linestring_to_home.length > 0.0 else 1.0
                cable_to_home = esdl.ElectricityCable(name=name, length=length, id=str(uuid.uuid4()), assetType="lv_line_to_home")
                cable_to_home.port.append(esdl.InPort(id=str(uuid.uuid4()), name="In"))
                cable_to_home.port.append(esdl.OutPort(id=str(uuid.uuid4()), name="Out"))
                cable_to_home.geometry = esdl.Line()
                cable_to_home.geometry.point.append(EsdlHelperFunctions.generate_esdl_point(new_linestring_to_home.coords[-1][0], new_linestring_to_home.coords[-1][1]))
                cable_to_home.geometry.point.append(EsdlHelperFunctions.generate_esdl_point(new_linestring_to_home.coords[0][0], new_linestring_to_home.coords[0][1]))
                esdl_building.asset[-1].port[0].connectedTo.append(cable_to_home.port[1])
                cable_to_home.port[1].connectedTo.append(esdl_building.asset[-1].port[0])

                new_line_input = LineToHomeInput(new_linestring_to_home, esdl_building, cable_to_home)
                ret_val.append(new_line_input)
            LOGGER.debug(f"Added line to home with length: {ret_val[-1].line.length}")

        return ret_val


    def list_of_points_to_linestring(self, points : esdl.Point) -> LineString:
        return LineString([(point.lat, point.lon) for point in points])
    

    def plot_line_strings(self, line_strings : List[LineString]):
        test_plotter = NetworkPlotter(1,1)
        test_plotter.plot_network(line_strings)
        test_plotter.show_plot()


    def plot_intermediate_result(self, assets_to_plot : List[esdl.ConnectableAsset]):
        line_strings = [self.list_of_points_to_linestring(cable.geometry.point) for cable in EsdlHelperFunctions.get_all_esdl_objects_from_type(assets_to_plot, esdl.ElectricityCable)]
        test_plotter = NetworkPlotter(1,1)
        test_plotter.plot_network(line_strings)
        test_plotter.show_plot()


    def plot_mv_and_lv_network(self, assets_to_plot : List[esdl.ConnectableAsset]):
        lv_line_strings = []
        mv_line_strings = []
        for cable in EsdlHelperFunctions.get_all_esdl_objects_from_type(assets_to_plot, esdl.ElectricityCable):
            if "lv" in cable.name.lower():
                lv_line_strings.append(self.list_of_points_to_linestring(cable.geometry.point))
            else:
                mv_line_strings.append(self.list_of_points_to_linestring(cable.geometry.point))
        network_plotter = NetworkPlotter(1,1)
        network_plotter.plot_mv_network_with_lv_network(mv_line_strings, lv_line_strings, mv_network_color="blue", lv_network_color="red")
        network_plotter.show_plot()


    def update_cable_and_joint_number(self):
        pass


    def generate_lv_esdl(self, network_topology_info : NetworkTopologyInfo, start_joint : esdl.Joint, transformer_prefix : str) -> esdl.EnergySystem:
        r_tree_lines = STRtree([navigation_line_string.line_string for navigation_line_string in network_topology_info.network_lines])

        log = False
        seen_indices = []
        if network_topology_info.amount_of_connections == 68:
            log = True
        lines_to_home_inputs = self.generate_lines_connected_to_homes(transformer_prefix, r_tree_lines, network_topology_info)
        joint_and_cable_number = 1
        lv_assets = []
        last_joint = start_joint
        point_last_added_joint = (start_joint.geometry.lat, start_joint.geometry.lon)
        # starting_line_new_r_tree = network_topology_info.starting_line
        # start_point = starting_line_new_r_tree.connected_point
        # start_line_index = r_tree_lines.query(Point(start_point), 'touches')
        # starting_line_new_r_tree.index = start_line_index[0]
        start_edge_data_view = network_topology_info.network_topology.edges.data(nbunch=0)
        next_lines : List[NavigationLineString] = EsdlHelperFunctions.flatten_list_of_lists([edge[2]["line_strings"] for edge in start_edge_data_view])
        while next_lines != []:
            for nav_line_string in next_lines:
                points_for_cable = []
                added_lines_to_home = False
                reversed_iteration = -1 if nav_line_string.first_point_end else 1
                for i in range(0, len(nav_line_string.line_string.coords) - 1):
                    i_start = i
                    i_end = i + 1
                    if reversed_iteration == -1:
                        i_start = reversed_iteration * (i + 1)
                        i_end = reversed_iteration * (i + 2)
                    if not added_lines_to_home:
                        point_a = nav_line_string.line_string.coords[i_start]
                        points_for_cable.append(point_a)
                    added_lines_to_home = False
                    point_b = nav_line_string.line_string.coords[i_end]
                    line_string = LineString([Point(point_a), Point(point_b)])
                    lines_to_home_input_intersects = [line_to_home_input for line_to_home_input in lines_to_home_inputs if dwithin(line_to_home_input.line, line_string, 1.0e-3)]
                    lines_to_home_input_intersects.sort(key=lambda line_to_home_input, point_a=point_a: distance(Point(line_to_home_input.line.coords[0]), Point(point_a)))
                    for line_to_home_input_intersects in lines_to_home_input_intersects:
                        lines_to_home_inputs.remove(line_to_home_input_intersects)
                        intersection_point = line_to_home_input_intersects.line.coords[0]
                        if not (last_joint.geometry.lat - 0.1 < intersection_point[0] < last_joint.geometry.lat + 0.1 and last_joint.geometry.lon - 0.1 < intersection_point[1] < last_joint.geometry.lon + 0.1):
                            points_for_cable.append(intersection_point)
                            joint_and_cable_number += 1
                            cable_name = f"lv_cable_{transformer_prefix}_{joint_and_cable_number}_main_grid"
                            joint_name = f"lv_node_{transformer_prefix}_{joint_and_cable_number}"
                            last_joint = self.generate_cable_and_joint(cable_name, joint_name, points_for_cable, last_joint, lv_assets)
                            point_last_added_joint = intersection_point
                            added_lines_to_home = True
                        line_to_home_input_intersects.cable_to_home.port[0].connectedTo.append(last_joint.port[1])
                        last_joint.port[1].connectedTo.append(line_to_home_input_intersects.cable_to_home.port[0])
                        points_for_cable = [intersection_point]
                        lv_assets.append(line_to_home_input_intersects.cable_to_home)
                        lv_assets.append(line_to_home_input_intersects.house)

                    if i == len(nav_line_string.line_string.coords) - 2 and point_last_added_joint != point_b:
                        joint_and_cable_number += 1
                        points_for_cable.append(point_b)
                        last_joint = self.generate_cable_and_joint(f"lv_cable_{transformer_prefix}_{joint_and_cable_number}_main_grid", f"lv_node_{transformer_prefix}_{joint_and_cable_number}", points_for_cable, last_joint, lv_assets)
            new_next_lines : List[NavigationLineString] = []
            for next_line in reversed(next_lines):
                new_next_lines.extend(GeometryHelperFunctions.get_next_lines_with_touch_margin(r_tree_lines, next_line, Constants.LV_CABLES_TO_MV_LV_STATION_MARGIN))
            next_lines = new_next_lines

        # self.plot_intermediate_result(lv_assets)
        return lv_assets


    def generate_cable_and_joint(self, cable_name : str, joint_name : str, points_for_cable : List[tuple[float, float]], last_joint : esdl.Joint, lv_assets : List[esdl.ConnectableAsset]) -> tuple[esdl.ElectricityCable, esdl.Joint]:
        joint_to_connect_to = esdl.Joint(id=str(uuid.uuid4()), name=joint_name)
        joint_to_connect_to.port.append(esdl.InPort(id=str(uuid.uuid4()), name="In"))
        joint_to_connect_to.port.append(esdl.OutPort(id=str(uuid.uuid4()), name="Out"))
        joint_to_connect_to.geometry = EsdlHelperFunctions.generate_esdl_point(points_for_cable[-1][0], points_for_cable[-1][1])

        part_cable = esdl.ElectricityCable(name=cable_name, length=LineString(points_for_cable).length, id=str(uuid.uuid4()), assetType="lv_line")
        part_cable.geometry = esdl.Line()
        for point in points_for_cable:
            part_cable.geometry.point.append(EsdlHelperFunctions.generate_esdl_point(point[0], point[1]))

        part_cable.port.append(esdl.InPort(id=str(uuid.uuid4()), name="In"))
        part_cable.port.append(esdl.OutPort(id=str(uuid.uuid4()), name="Out"))
        part_cable.port[1].connectedTo.append(joint_to_connect_to.port[0])
        joint_to_connect_to.port[0].connectedTo.append(part_cable.port[1])
        part_cable.port[0].connectedTo.append(last_joint.port[1])
        last_joint.port[1].connectedTo.append(part_cable.port[0])

        lv_assets.append(joint_to_connect_to)
        lv_assets.append(part_cable)
        return joint_to_connect_to


    def print_network_statistics(self, mv_network : EnergySystem, amount_of_connections_transformer : dict):
        assets = mv_network.instance[0].area.asset
        cables = EsdlHelperFunctions.get_all_esdl_objects_from_type(assets, esdl.ElectricityCable)
        joints = EsdlHelperFunctions.get_all_esdl_objects_from_type(assets, esdl.Joint)
        transformers = EsdlHelperFunctions.get_all_esdl_objects_from_type(assets, esdl.Transformer)
        buildings = EsdlHelperFunctions.get_all_esdl_objects_from_type(assets, esdl.Building)
        LOGGER.info(f"Number of cables: {len(cables)}")
        LOGGER.info(f"Number of joints: {len(joints)}")
        LOGGER.info(f"Number of transformers: {len(transformers)}")
        LOGGER.info(f"Number of connections: {len(buildings)}")
        LOGGER.info(f"Amount of connections per transformer:")
        for transformer_name, amount_of_connections in amount_of_connections_transformer.items():
            LOGGER.info(f"{transformer_name}: {amount_of_connections} connections")


    def save_lv_network_as_energy_system(self, lv_assets : List[esdl.Asset], transformer : esdl.Transformer, name : str, file_path : str):
        # Calling this function will destroy the mv grid output
        esdl_import = EsdlHelperFunctions.generate_esdl_import(f"mv_import_{name}", transformer.geometry.lat, transformer.geometry.lon, transformer.voltagePrimary)
        esdl_import_joint = EsdlHelperFunctions.generate_esdl_joint(transformer.geometry.lat, transformer.geometry.lon, f"mv_import_joint_{name}")
        esdl_import.port[0].connectedTo.append(esdl_import_joint.port[0])
        esdl_import_joint.port[0].connectedTo.append(esdl_import.port[0])

        new_transformer = EsdlHelperFunctions.generate_new_transformer(transformer.geometry.lat, transformer.geometry.lon, transformer.name, transformer.commissioningDate, transformer.voltagePrimary, transformer.voltageSecundary)
        new_transformer.port[0].connectedTo.clear()
        esdl_import_joint.port[1].connectedTo.append(new_transformer.port[0])
        new_transformer.port[0].connectedTo.append(esdl_import_joint.port[1])

        lv_joint = transformer.port[1].connectedTo[0].eContainer()
        lv_joint.port[0].connectedTo.clear()

        new_transformer.port[1].connectedTo.append(lv_joint.port[0])
        lv_joint.port[0].connectedTo.append(new_transformer.port[1])

        lv_assets.append(esdl_import)
        lv_assets.append(esdl_import_joint)
        lv_assets.append(new_transformer)
        lv_assets.append(lv_joint)

        esh = EnergySystemHandler()

        es = esh.create_empty_energy_system(name=name, es_description="Autogenerated based on gis data " + name,
                                            inst_title="Instance name", area_title="Area name")

        energy_system_information = esdl.EnergySystemInformation(id=str(uuid.uuid4()))
        es.energySystemInformation = energy_system_information
        EsdlHelperFunctions.add_new_assets_to_energy_system(es, lv_assets)
        esh.save(file_path)

    def build_mv_energy_system(self, mv_network : EnergySystem):
        assets = mv_network.instance[0].area.asset
        transfomers : List[esdl.Transformer] = EsdlHelperFunctions.get_all_esdl_objects_from_type(assets, esdl.Transformer)
        amount_of_connections_transformer = {}
        for transformer in transfomers:
            LOGGER.debug(f"Next transformer at point: {(transformer.geometry.lat, transformer.geometry.lon)}")
            transfomer_point = Point(transformer.geometry.lat, transformer.geometry.lon)
            network_topology_infos = self.lv_network_builder.extract_lv_networks_and_topologies_at_point(transfomer_point)
            if len(network_topology_infos) > 0:
                archetype = self.archetype_handler.archetype_at_point(transfomer_point)
                LOGGER.info(f"LV grid archetype: {archetype}")
                lv_assets = []
                for network_id, network_topology_info in enumerate(network_topology_infos):
                    if len(network_topology_info.buildings) > 0:
                        self.plot_line_strings([line.line_string for line in network_topology_info.network_lines])
                        lv_trafo_name = f"trafo{transformer.name}_lvnetwork{network_id}"
                        lv_joint = transformer.port[1].connectedTo[0].eContainer()
                        new_lv_assets = self.generate_lv_esdl(network_topology_info, lv_joint, lv_trafo_name)
                        amount_of_new_connections = len(EsdlHelperFunctions.get_all_esdl_objects_from_type(new_lv_assets, esdl.Building))
                        LOGGER.info(f"New connections in esdl: {amount_of_new_connections}")
                        lv_assets.extend(new_lv_assets)
                        amount_of_connections_transformer[f"transformer{transformer.name}"] = amount_of_connections_transformer.get(f"transformer{transformer.name}", 0) + network_topology_info.amount_of_connections
                self.save_lv_network_as_energy_system(lv_assets, transformer, transformer.name, f"{transformer.name}.esdl")
        self.plot_mv_and_lv_network(mv_network.instance[0].area.asset)
        self.print_network_statistics(mv_network, amount_of_connections_transformer)
        return mv_network
