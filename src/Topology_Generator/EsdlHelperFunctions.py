import uuid
from esdl import esdl
from typing import List
from datetime import datetime
from pyproj import Transformer
from pyproj import CRS
from shapely import LineString

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
    def convert_epsg_28992_to_wgs84(lat : float, long : float) -> tuple[float, float]:
        crs = CRS(proj='utm', zone=10, ellps='WGS84')
        transformer = Transformer.from_crs("EPSG:28992", "EPSG:4326")
        wgs84_lat, wgs84_long = transformer.transform(lat, long)
        return wgs84_lat, wgs84_long
    

    @staticmethod
    def generate_new_electricity_cable(cable_name : str, asset_type : str, points_for_cable : List[tuple[float, float]]):
        part_cable = esdl.ElectricityCable(name=cable_name, length=LineString(points_for_cable).length, id=str(uuid.uuid4()), assetType=asset_type)
        part_cable.geometry = esdl.Line()
        for point in points_for_cable:
            part_cable.geometry.point.append(EsdlHelperFunctions.generate_esdl_point(point[0], point[1]))

        part_cable.port.append(esdl.InPort(id=str(uuid.uuid4()), name="In"))
        part_cable.port.append(esdl.OutPort(id=str(uuid.uuid4()), name="Out"))
        return part_cable


    @staticmethod 
    def generate_esdl_point(lat_epsg_28992 : float, long_epsg_28992 : float) -> esdl.Point:
        point = esdl.Point(lat=lat_epsg_28992, lon=long_epsg_28992, CRS="EPSG:28992")
        return point


    @staticmethod
    def generate_esdl_joint(lat : float, long : float, name : str) -> esdl.Joint:
        joint = esdl.Joint(id=str(uuid.uuid4()), name=name)
        joint.geometry = EsdlHelperFunctions.generate_esdl_point(lat, long)
        joint.port.append(esdl.InPort(id=str(uuid.uuid4()), name="In"))
        joint.port.append(esdl.OutPort(id=str(uuid.uuid4()), name="Out"))
        return joint

    @staticmethod
    def generate_esdl_import(name : str, lat : float, long : float, voltage : float) -> esdl.Import:
        esdl_import = esdl.Import(id=str(uuid.uuid4()), name=name, assetType=str(voltage))
        esdl_import.geometry = EsdlHelperFunctions.generate_esdl_point(lat, long)
        esdl_import.port.append(esdl.OutPort(id=str(uuid.uuid4()), name="Out"))
        return esdl_import
    
    @staticmethod
    def generate_new_transformer(lat : float, long : float, name : str, commissioning_date : datetime = datetime.min, voltage_primary=10.0, voltage_secundary=0.40, assetType="testtrafotype"):
        transformer = esdl.Transformer(id=str(uuid.uuid4()), name=name, assetType=assetType, voltagePrimary=voltage_primary, voltageSecundary=voltage_secundary, commissioningDate=commissioning_date)
        transformer.geometry = EsdlHelperFunctions.generate_esdl_point(lat, long)
        transformer.port.append(esdl.InPort(id=str(uuid.uuid4()), name="In"))
        transformer.port.append(esdl.OutPort(id=str(uuid.uuid4()), name="Out"))
        return transformer