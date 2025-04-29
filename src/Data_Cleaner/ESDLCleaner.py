import os
import esdl
from esdl.esdl_handler import EnergySystemHandler
from Topology_Generator.Logging import LOGGER
import pandas as pd

from Topology_Generator.EsdlHelperFunctions import EsdlHelperFunctions

class ESDLCleaner:

    def __init__(self, path : str):
        self.esdl_file_path = path
        self.esh = EnergySystemHandler()
        self.esh.load_file(self.esdl_file_path)
        self.esdl_file_name = os.path.basename(self.esdl_file_path)
        self.energy_system = self.esh.get_energy_system()
        self.assets = self.energy_system.instance[0].area.asset

    def clean_esdl(self, dir_to_save):
        transformers = EsdlHelperFunctions.get_all_esdl_objects_from_type(self.assets, esdl.Transformer)
        for transformer in transformers:
            out_ports = EsdlHelperFunctions.get_all_out_ports_from_esdl_obj(transformer)
            for out_port in out_ports:
                connected_out_joints = EsdlHelperFunctions.get_all_esdl_objects_from_type(out_port.connectedTo, esdl.InPort)
                if len(connected_out_joints) == 1 and isinstance(connected_out_joints[0].eContainer(), esdl.Joint):
                    transformer.geometry = connected_out_joints[0].eContainer().geometry
                    LOGGER.info(f"Transformer's new location point: ({transformer.geometry.lat}, {transformer.geometry.lon})")
        if not os.path.exists(dir_to_save):
            os.mkdir(dir_to_save)
        self.esh.save_as(f"{dir_to_save}/{self.esdl_file_name}-cleaned")

    def extract_cable_types(self):
        assets = self.energy_system.instance[0].area.asset
        cables = EsdlHelperFunctions.get_all_esdl_objects_from_type(assets, esdl.ElectricityCable)
        cable_types = set()
        for cable in cables:
            cable_types.add(cable.assetType)
        return cable_types

def main():
    dir_to_clean = "C:/Users/20180029/repos/Topology-Generator/Archetypes"
    all_cable_types = set()
    alliander_cable_types = set()
    enexis_cable_types = set()
    stedin_cable_types = set()
    for file in os.listdir(dir_to_clean):
        if file.endswith(".esdl"):
            cleaner = ESDLCleaner(f"{dir_to_clean}/{file}")
            cleaner.clean_esdl(f"{dir_to_clean}/Cleaned")
            cable_types = cleaner.extract_cable_types()
            all_cable_types.update(cable_types)
            if "Alliander" in file:
                alliander_cable_types.update(cable_types)
            elif "Enexis" in file:
                enexis_cable_types.update(cable_types)
            elif "Stedin" in file:
                stedin_cable_types.update(cable_types)
    common_cable_types = alliander_cable_types.intersection(enexis_cable_types).intersection(stedin_cable_types)

    max_length = max([len(alliander_cable_types), len(enexis_cable_types), len(stedin_cable_types), len(common_cable_types)])
    data = {
        "Alliander": list(alliander_cable_types) + [""] * (max_length - len(alliander_cable_types)),
        "Enexis": list(enexis_cable_types) + [""] * (max_length - len(enexis_cable_types)),
        "Stedin": list(stedin_cable_types) + [""] * (max_length - len(stedin_cable_types)),
        "Common": list(common_cable_types) + [""] * (max_length - len(common_cable_types))
    }

    df = pd.DataFrame(data)
    df.to_csv("CableTypes.csv")



if __name__ == "__main__":
    exit(main())