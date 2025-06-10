import uuid
from esdl import esdl
from typing import List

class EsdlHelperFunctions:

    @staticmethod
    def get_all_in_ports_from_esdl_obj(esdl_obj) -> List[esdl.Port]:
        return [port for port in esdl_obj.port if port.name == 'In']
    
    @staticmethod
    def get_all_out_ports_from_esdl_obj(esdl_obj) -> List[esdl.Port]:
        return [port for port in esdl_obj.port if port.name == 'Out']
    
    @staticmethod
    def get_all_esdl_objects_from_type(collection, type) -> List:
        return [esdl_obj for esdl_obj in collection if isinstance(esdl_obj, type)]

    @staticmethod
    def flatten_list_of_lists(list_of_lists) -> List:
        return [list_item for list in list_of_lists for list_item in list]
    
    @staticmethod
    def add_new_assets_to_energy_system(energy_system : esdl.EnergySystem, esdl_objs : List[esdl.EnergyAsset]):
        area = energy_system.instance[0].area
        for esdl_obj in esdl_objs:
            area.asset.append(esdl_obj)

    @staticmethod
    def generate_esdl_joint(lat : float, long : float, name : str) -> esdl.Joint:
        joint = esdl.Joint(id=str(uuid.uuid4()), name=name)
        joint.geometry = esdl.Point(lat=lat, lon=long, CRS="WGS84")
        joint.port.append(esdl.InPort(id=str(uuid.uuid4()), name="In"))
        joint.port.append(esdl.OutPort(id=str(uuid.uuid4()), name="Out"))
        return joint