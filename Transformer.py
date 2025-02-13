# Group 8 - Project 2
# ECE 2774
# Milestone 1
import numpy as np
import pandas as pd
from Bus import Bus

class Transformer:

    def __init__(self, name: str, bus1: Bus, bus2: Bus, power_rating: float,
                 impedance_percent: float, x_over_r_ratio: float):
        self.name = name
        self.bus1 = bus1
        self.bus2 = bus2
        self.power_rating = power_rating
        self.impedance_percent = impedance_percent
        self.x_over_r_ratio = x_over_r_ratio

        # Compute impedance and admittance values
        self.Rpusys, self.Xpusys = self.calc_impedance()
        self.Yseries = self.calc_admittance()
        self.yprim = self.calc_yprim()

    def calc_impedance(self):

        base_impedance = 100  # Assume 100 MVA system base
        z_base = base_impedance / self.power_rating

        # Calculate per-unit resistance and reactance
        r_pu = z_base * self.impedance_percent / (100 * np.sqrt(1 + self.x_over_r_ratio ** 2))
        x_pu = r_pu * self.x_over_r_ratio
        return r_pu, x_pu

    def calc_admittance(self):

        z_pu = complex(self.Rpusys, self.Xpusys)
        if z_pu == 0:
            return complex(0, 0)
        return 1 / z_pu

    def calc_yprim(self):

        yprim = np.array([
            [self.Yseries, -self.Yseries],
            [-self.Yseries, self.Yseries]
        ])
        yprim_df = pd.DataFrame(yprim, index=[self.bus1.name, self.bus2.name], columns=[self.bus1.name, self.bus2.name])

        return yprim_df

# Validation
if __name__ == "__main__":
    # define bus1 and bus2 before
    bus1 = Bus("Bus1", 20)
    bus2 = Bus("Bus2",230)

    transformer1 = Transformer("T1", bus1, bus2, 125, 8.5, 10)

    print("Transformer Name:", transformer1.name)
    print("Connected Buses:", transformer1.bus1, "<-->", transformer1.bus2)
    print("Power Rating:", transformer1.power_rating, "MVA")
    print("Per-unit Resistance (Rpu):", transformer1.Rpusys)
    print("Per-unit Reactance (Xpu):", transformer1.Xpusys)
    print("Series Admittance (Yseries):", transformer1.Yseries)
    print("Yprim matrix:")
    print(transformer1.yprim)