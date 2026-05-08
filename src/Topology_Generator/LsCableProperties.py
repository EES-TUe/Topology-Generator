from Topology_Generator.Constants import LvCableConstants

# Data required yearly usage dataset alliander
# 

class LsCableParameters:
    max_current_amp: float
    conductor_resistance_ohm_per_km: float
    conductor_reactance_ohm_per_km: float

    def __init__(self, max_current_amp: float, conductor_resistance_ohm_per_km: float, conductor_reactance_ohm_per_km: float):
        self.max_current_amp = max_current_amp
        self.conductor_resistance_ohm_per_km = conductor_resistance_ohm_per_km
        self.conductor_reactance_ohm_per_km = conductor_reactance_ohm_per_km

    def cable_length_passes_voltage_drop_check(self, length_km: float, amount_of_connections : int, nominal_voltage : float) -> bool:
        current_amp : float = 12
        voltage_drop_volt = length_km * (self.conductor_resistance_ohm_per_km + self.conductor_reactance_ohm_per_km * 1j) * current_amp
        voltage_drop_percentage = voltage_drop_volt / nominal_voltage * 100
        return voltage_drop_percentage <= LvCableConstants.ALLOWED_VOLTAGE_DROP_VOLT_PERCENTAGE