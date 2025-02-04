# Cece Espadas
# 2-2-25
# ECE 2774: Project 2
# Transmission Line Subclass

import math
from Conductor import Conductor
from Bundle import Bundle
from Geometry import Geometry
from Bus import Bus

class TransmissionLine:

    def __init__(self, name: str, bus1: Bus, bus2: Bus, bundle: Bundle, geometry: Geometry, length: float):
        self.name = name
        self.bus1 = bus1
        self.bus2 = bus2
        self.bundle = bundle
        self.geometry = geometry
        self.length = length

        self.zbase, self.ybase = self.calc_base_values()

        self.zseries, self.yshunt, self.yseries = self.calc_admittances()

        self.yprim = self.calc_admittance_matrix()

    def calc_base_values(self):

        Vbase = self.bus2.base_kv  # [kv] same kV for each
        Sbase = 100 # [MVA] # should this be assumed or no

        #create a new class, Settings, global variables, freq, Sbase, parameters

        zbase = Vbase ** 2 / Sbase
        ybase = 1 / zbase
        return zbase, ybase

    def calc_admittances(self):
        # calculates the series impedance, shunt admittance, and series admittance

        dsl = self.bundle.dsl  # DSL for series impedance calculation
        dsc = self.bundle.dsc  # DSC for shunt susceptance calculation
        Deq = self.geometry.Deq  # equivalent conductor spacing

        f = 60  # Frequency in Hz
        ε_0 = 8.854 * 10 ** -12  # permittivity of free space (F/m)

        # resistance per unit length (Ω/mi)
        Rseries = (self.bundle.conductor.resistance)/(self.bundle.num_conductors)

        # inductive reactance per unit length (Ω/mi)
        Xseries = (2 * math.pi * f) * (2 * 10 ** -7) * (1609.34) * math.log(Deq / dsl)

        # conductance per unit length (S/mi)
        G = 0

        # shunt susceptance per unit length (S/mi)
        B = (2 * math.pi * ε_0) * (2 * math.pi * f) * (1609.34) / math.log(Deq / dsc)

        # convert to per-unit values
        zseries = complex(Rseries, Xseries) / self.zbase
        yseries = 1/zseries

        yshunt = complex(G, B) / self.ybase

        return zseries, yshunt, yseries

    def calc_admittance_matrix(self):
        # calculates the primitive admittance matrix (yprim)

        Z = self.zseries * self.length  # Total series impedance
        Y = self.yshunt * self.length  # Total shunt admittance

        # Primitive admittance matrix (2x2 for a single line)
        Y_prim = [[(1 / Z) + Y / 2, -1 / Z],
                  [-1 / Z, (1 / Z) + Y / 2]]

        return Y_prim

if __name__ == "__main__":

    conductor1 = Conductor("Partridge", 0.642, 0.0217, 0.385, 460)

    bundle1 = Bundle("Bundle 1", 2, 1.5, conductor1)

    geometry1 = Geometry("Geometry 1", 0, 0, 18.5, 0,37, 0)

    bus1 = Bus("Bus 1", 230)
    bus2 = Bus("Bus 2", 230)

    line1 = TransmissionLine("Line 1", bus1, bus2, bundle1, geometry1, 10)

    print(line1.name, line1.bus1.name, line1.bus2.name, line1.length)

    print(line1.zbase, line1.ybase)

    print(line1.zseries, line1.yshunt, line1.yseries)