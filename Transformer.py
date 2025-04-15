# Group 8 - Project 2
# ECE 2774
# Milestone 1
import numpy as np
import pandas as pd
from Bus import Bus
from SystemSettings import SystemSettings

class Transformer:

    def __init__(self, name: str, bus1: Bus, bus2: Bus, power_rating: float,
                 impedance_percent: float, x_over_r_ratio: float, connection_type: str, grounding_impedance: float):
        self.name = name
        self.bus1 = bus1
        self.bus2 = bus2
        self.power_rating = power_rating
        self.impedance_percent = impedance_percent
        self.x_over_r_ratio = x_over_r_ratio

        self.connection_type = connection_type.upper()
        self.Zn = grounding_impedance  # in ohms - NEED TO MAKE IN PU


        # impedance and admittance values
        self.Rpusys, self.Xpusys = self.calc_impedance()
        self.Yseries = self.calc_admittance()

        # sequence admittances
        self.yprim = self.calc_yprim()
        self.yprim_neg = self.calc_yprim_negative()
        self.yprim_zero = self.calc_yprim_zero()

    def calc_impedance(self):

        Sbase = SystemSettings.Sbase # Assume 100 MVA system base

        # Calculate per-unit resistance and reactance
        z_pu = (Sbase / self.power_rating) * (self.impedance_percent / 100 ) * np.exp(1j * np.arctan(self.x_over_r_ratio))
        r_pu = np.real(z_pu)
        x_pu = np.imag(z_pu)
        return r_pu, x_pu

    def calc_admittance(self):
        return 1 / (self.Rpusys + 1j * self.Xpusys)

    def calc_yprim(self):

        yprim = np.array([
            [self.Yseries, -self.Yseries],
            [-self.Yseries, self.Yseries]
        ])
        yprim_df = pd.DataFrame(yprim, index=[self.bus1.name, self.bus2.name], columns=[self.bus1.name, self.bus2.name])

        return yprim_df

    def calc_yprim_negative(self):
        # equal to positive sequence

        yprim_2 = np.array([
            [self.Yseries, -self.Yseries],
            [-self.Yseries, self.Yseries]
        ])
        yprim_neg = pd.DataFrame(yprim_2, index=[self.bus1.name, self.bus2.name], columns=[self.bus1.name, self.bus2.name])

        return yprim_neg

    def calc_yprim_zero(self):
        y = self.Yseries

        # convert grounding impedance (ohms to pu)
        zbase =  (SystemSettings.Sbase / self.power_rating) * (self.impedance_percent / 100 ) * np.exp(1j * np.arctan(self.x_over_r_ratio))
        zn_pu = self.Zn / zbase if self.Zn != 0 else 1e-6


        if self.connection_type == "Y-Y":
            yg = 1 / (3 * zn_pu)
            y11 = y + yg
            y22 = y + yg
            y12 = -y
        elif self.connection_type == "Y-DELTA":
            y11 = ( 1 / (3 * zn_pu) )
            y22 = 0
            y12 = 0
        elif self.connection_type == "DELTA-Y":
            y11 = 0
            y22 = ( 1 / (3 * zn_pu) )
            y12 = 0
        elif self.connection_type == "DELTA-DELTA":
            y11 = y22 = y12 = 0
        else:
            raise ValueError(f"Invalid connection type: {self.connection_type}")

        yprim_zero = pd.DataFrame([[y11, -y12], [-y12, y22]],
                                  index=[self.bus1.name, self.bus2.name],
                                  columns=[self.bus1.name, self.bus2.name])
        return yprim_zero


# Validation
if __name__ == "__main__":
    # define bus1 and bus2 before
    Bus6 = Bus("Bus6", 230)
    Bus7 = Bus("Bus7",18)

    transformer1 = Transformer("T2", Bus6, Bus7, 200, 10.5, 12, "delta-y", 999999)

    print("Transformer Name:", transformer1.name)
    print("Connected Buses:", transformer1.bus1, "<-->", transformer1.bus2)
    print("Power Rating:", transformer1.power_rating, "MVA")
    print("Per-unit Resistance (Rpu):", transformer1.Rpusys)
    print("Per-unit Reactance (Xpu):", transformer1.Xpusys)
    print("Series Admittance (Yseries):", transformer1.Yseries)

    print("\nPositive Sequence Yprim:")
    print(transformer1.yprim)

    print("\nNegative Sequence Yprim:")
    print(transformer1.yprim_neg)

    print("\nZero Sequence Yprim:")
    print(transformer1.yprim_zero)