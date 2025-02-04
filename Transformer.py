import numpy as np

class Transformer:

    def __init__(self, name: str, bus1: str, bus2: str, power_rating: float,
                 impedance_percent: float, x_over_r_ratio: float):
        self.name = name
        self.bus1 = bus1
        self.bus2 = bus2
        self.power_rating = power_rating
        self.impedance_percent = impedance_percent
        self.x_over_r_ratio = x_over_r_ratio

        # calculate the impedance and admittance values
        self.impedance = self.calc_impedance()
        self.admittance = self.calc_admittance()

    def calc_impedance(self):
        # calculate the impedance of the transformer
        base_impedance = 100  # assume 100 MVA system base
        z_base = base_impedance / self.power_rating
        r = z_base * self.impedance_percent / (100 * np.sqrt(1 + self.x_over_r_ratio ** 2))
        x = r * self.x_over_r_ratio
        return complex(r, x)

    def calc_admittance(self):
        if self.impedance == 0:
            return complex(0, 0)
        return 1 / self.impedance

    def calc_y_prim(self):
        y_prim = np.array([
            [self.admittance, -self.admittance],
            [-self.admittance, self.admittance]
        ])
        return y_prim

