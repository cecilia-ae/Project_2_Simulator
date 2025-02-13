# Group 8 - Project 2
# ECE 2774
# Milestone 1

import math
import numpy as np
import pandas as pd
from Conductor import Conductor
from Bundle import Bundle
from Geometry import Geometry
from Bus import Bus
from Global import Global

class TransmissionLine:

    def __init__(self, name: str, bus1: Bus, bus2: Bus, bundle: Bundle, geometry: Geometry, length: float):
        self.name = name
        self.bus1 = bus1
        self.bus2 = bus2
        self.bundle = bundle
        self.geometry = geometry
        self.length = length

        self.zbase, self.ybase = self.calc_base_values()

        self.Rpu = self.calc_Rpu()
        self.Xpu = self.calc_Xpu()
        self.Bpu = self.calc_Bpu()

        self.yprim = self.calc_yprim()

    def calc_base_values(self):

        Vbase = self.bus2.base_kv  # [kv] same kV for each
        Sbase = Global.Sbase # [MVA]
        #create a new class, Settings, global variables, freq, Sbase, parameters

        zbase = Vbase ** 2 / Sbase
        ybase = 1 / zbase
        return zbase, ybase

    def calc_Rpu(self):

        # resistance(Ω)
        Rseries = self.length * (self.bundle.conductor.resistance)/(self.bundle.num_conductors)

        Rpu = Rseries/self.zbase

        return Rpu

    def calc_Xpu(self):

        dsl = self.bundle.dsl  # DSL for series impedance calculation
        Deq = self.geometry.Deq  # equivalent conductor spacing

        f = Global.f  # Frequency in Hz

        # inductive reactance(Ω)
        Xseries = self.length * (2 * math.pi * f) * (2 * 10 ** -7) * (1609.34) * math.log(Deq / dsl)

        Xpu = Xseries/self.zbase

        return Xpu

    def calc_Bpu(self):
        dsc = self.bundle.dsc  # DSC for shunt susceptance calculation
        Deq = self.geometry.Deq  # equivalent conductor spacing

        f = Global.f  # Frequency in Hz
        ε_0 = Global.ε_0  # permittivity of free space (F/m)

        # shunt susceptance per unit length (S)
        B = self.length * (2 * math.pi * ε_0) * (2 * math.pi * f) * (1609.34) / math.log(Deq / dsc)

        Bpu = B / self.ybase

        return Bpu


    def calc_yprim(self):
        # calculates the primitive admittance matrix (yprim)

        G = 0

        zseries = complex(self.Rpu, self.Xpu)
        yseries = 1/zseries

        yshunt = complex(G, self.Bpu) / self.ybase

        # Primitive admittance matrix (2x2 for a single line)
        Y_prim = pd.DataFrame(
            [[yseries + yshunt / 2, -1*yseries],
             [-1*yseries, yseries + yshunt/ 2]],
            index=[self.bus1.name, self.bus2.name],
            columns=[self.bus1.name, self.bus2.name]
        )

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

    print(line1.Rpu, line1.Xpu, line1.Bpu)

    print(line1.yprim)