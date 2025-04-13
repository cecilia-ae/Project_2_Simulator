# Group 8 - Project 2
# ECE 2774
# Milestone 5

from Bus import Bus

class Generator:

    def __init__(self,name: str, bus: Bus, voltage_setpoint: float, mw_setpoint: float, grounding_impedance: complex = 0 + 0j, is_grounded: bool = True):
        self.name = name
        self.bus = bus
        self.voltage_setpoint = voltage_setpoint
        self.mw_setpoint = mw_setpoint

        # sequence reactances
        self.x1 = 0.12 # positive-sequence subtransient reactance
        self.x2 = 0.14 # negative-sequence subtransient reactance
        self.x0 = 0.05 # zero-sequence subtransient reactance

        # grounding configuration
        self.Zn = grounding_impedance #default of zero which represents a solid ground
        self.is_grounded = is_grounded

    def y_prim_negative_sequence(self) -> complex:
            # primitive admittance (Y = 1 / jX2) for the negative-sequence network.

            Yprim2 = 1 / (1j * self.x2)

            return Yprim2

    def y_prim_zero_sequence(self) -> complex:
        # primitive admittance (Y = 1 / (jX0 + 3*Zn)) for the zero-sequence network.
        # if generator is ungrounded, return 0

        Yprim0 = 1 / (1j * self.x0 + 3 * self.Zn)

        if not self.is_grounded:
            return 0 + 0j
        return Yprim0