# Group 8 - Project 2
# ECE 2774
# Milestone 1
import numpy as np
import Bus as Bus
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
        self.zt = self.calculate_impedance()
        self.yt = self.calculate_admittance()
        self.yprim = self.y_primitive_matrix()

    def calculate_impedance(self):

        base_impedance = 100  # Assume 100 MVA system base
        z_base = base_impedance / self.power_rating
        r = z_base * self.impedance_percent / (100 * np.sqrt(1 + self.x_over_r_ratio ** 2))
        x = r * self.x_over_r_ratio
        return complex(r, x)

    def calculate_admittance(self):

        if self.zt == 0:
            return complex(0, 0)
        return 1 / self.zt

    def y_primitive_matrix(self):

        yprim = np.array([
            [self.yt, -self.yt],
            [-self.yt, self.yt]
        ])
        return yprim

# Validation
if __name__ == "__main__":
    transformer1 = Transformer("T1", "bus1", "bus2", 125,8.5,10)
    print("Transformer Name:", transformer1.name)
    print("Connected Buses:", transformer1.bus1, "<-->", transformer1.bus2)
    print("Power Rating:", transformer1.power_rating, "MVA")
    print("Impedance (zt):", transformer1.zt)
    print("Admittance (yt):", transformer1.yt)
    print("Yprim matrix:")
    print(transformer1.yprim)