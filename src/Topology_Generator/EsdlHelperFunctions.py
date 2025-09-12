import uuid
from esdl import esdl
from typing import List
from datetime import datetime

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

    @staticmethod
    def generate_esdl_import(name : str, lat : float, long : float, voltage : float) -> esdl.Import:
        esdl_import = esdl.Import(id=str(uuid.uuid4()), name=name, assetType=str(voltage))
        esdl_import.geometry = esdl.Point(lat=lat, lon=long, CRS="WGS84")
        esdl_import.port.append(esdl.OutPort(id=str(uuid.uuid4()), name="Out"))
        return esdl_import
    
    @staticmethod
    def generate_new_transformer(lat : float, long : float, name : str, commissioning_date : datetime = datetime.min, voltage_primary=10.0, voltage_secundary=0.40):
        transformer = esdl.Transformer(id=str(uuid.uuid4()), name=name, assetType="testtrafotype", voltagePrimary=voltage_primary, voltageSecundary=voltage_secundary, commissioningDate=commissioning_date)
        transformer.geometry = esdl.Point(lat=lat, lon=long, CRS="WGS84")
        transformer.port.append(esdl.InPort(id=str(uuid.uuid4()), name="In"))
        transformer.port.append(esdl.OutPort(id=str(uuid.uuid4()), name="Out"))
        return transformer