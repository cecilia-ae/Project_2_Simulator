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

        # init calculated attributes
        self.zt = self.calc_impedance()
        self.yt = 1 / self.zt if self.zt != 0 else 0
        self.y_prim = self.calc_y_prim()

    def calc_impedance(self):
        # calculate the impedance angle
        theta = np.arctan(self.x_over_r_ratio)
        z_base = self.impedance_percent / 100 * np.exp(1j * theta)
        return z_base

    def calc_y_prim(self):
        ypu = self.yt
        # 2x2 admittance matrix for the transformer
        y_prim_matrix = np.array([
            [ypu, -ypu],
            [-ypu, ypu]
        ])
        return y_prim_matrix
