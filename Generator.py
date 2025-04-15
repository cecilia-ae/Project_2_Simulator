# Group 8 - Project 2
# ECE 2774
# Milestone 5

from Bus import Bus
from SystemSettings import SystemSettings
import pandas as pd

class Generator:

    def __init__(self,name: str, bus: Bus, voltage_setpoint: float, mw_setpoint: float, grounding_impedance: float, is_grounded: bool = True):
        self.name = name
        self.bus = bus
        self.voltage_setpoint = voltage_setpoint
        self.mw_setpoint = mw_setpoint

        # sequence reactances
        self.x1 = 0.12 # positive-sequence subtransient reactance
        self.x2 = 0.14 # negative-sequence subtransient reactance
        self.x0 = 0.05 # zero-sequence subtransient reactance

        # grounding configuration
        self.Zn = grounding_impedance #default of zero which represents a solid ground - NEED TO MAKE IN PU
        self.is_grounded = is_grounded

    def y_prim_positive_sequence(self):
        # primitive admittance (Y = 1 / jX1) for the positive-sequence network

        Y = 1 / (1j * self.x1)

        Yprim1 = pd.DataFrame([[Y]], index=[self.bus.name], columns=[self.bus.name])

        return Yprim1

    def y_prim_negative_sequence(self) -> complex:
            # primitive admittance (Y = 1 / jX2) for the negative-sequence network.

            Y = 1 / (1j * self.x2)

            Yprim2 = pd.DataFrame([[Y]], index=[self.bus.name], columns=[self.bus.name])

            return Yprim2

    def y_prim_zero_sequence(self) -> complex:
        # primitive admittance (Y = 1 / (jX0 + 3*Zn)) for the zero-sequence network.
        # if generator is ungrounded, return 0

        Znpu = self.Zn * SystemSettings.Sbase / ( (self.voltage_setpoint)**2 )

        Y= 1 / (1j * self.x0 + 3 * Znpu)

        if not self.is_grounded:
            Y = 0 + 0j

        Yprim0 = pd.DataFrame([[Y]], index=[self.bus.name], columns=[self.bus.name])

        return Yprim0

if __name__ == "__main__":

        Bus1 = Bus("Bus1", 20)
        Bus7 = Bus("Bus2", 18)

        # Grounded generator
        gen1 = Generator("G1", Bus1, 20, 100, 0, True)

        print("\nGrounded Generator:")
        print("\nPositive Sequence Yprim:")
        print(gen1.y_prim_positive_sequence())
        print("\nNegative Sequence Yprim:")
        print(gen1.y_prim_negative_sequence())
        print("\nZero Sequence Yprim:")
        print(gen1.y_prim_zero_sequence())


        # Ungrounded generator
        gen2 = Generator("G2", Bus7, 18, 200, 1, True)

        print("\nUngrounded Generator:")
        print("\nPositive Sequence Yprim:")
        print(gen2.y_prim_positive_sequence())
        print("\nNegative Sequence Yprim:")
        print(gen2.y_prim_negative_sequence())
        print("\nZero Sequence Yprim:")
        print(gen2.y_prim_zero_sequence())
