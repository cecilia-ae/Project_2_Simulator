# Group 8 - Project 2
# ECE 2774
# Milestone 5

from Bus import Bus
from SystemSettings import SystemSettings
import pandas as pd

class Load:

    def __init__(self, name: str, bus: Bus, real_power: float, reactive_power: float):
        self.name = name
        self.bus = bus
        self.real_power = real_power #MW
        self.reactive_power = reactive_power #MVAR

        self.rated_voltage = bus.base_kv # in kV
        self.admittance = (self.real_power - 1j*self.reactive_power)/ (self.rated_voltage**2) # Not in per unit

        self.ybase = SystemSettings.Sbase / self.rated_voltage**2

        self.y_pu = self.admittance / self.ybase # in per unit

    def y_prim(self):
        # primitive admittance (Y = 1 / jX1) for the positive-sequence network

        Y = self.y_pu

        Yprim1 = pd.DataFrame([[Y]], index=[self.bus.name], columns=[self.bus.name])

        return Yprim1
