# Group 8 - Project 2
# ECE 2774
# Milestone 5

from Bus import Bus
import numpy as np

class Generator:

    def __init__(self, name: str, bus: Bus, voltage_setpoint: float, mw_setpoint: float,
                 x1pp: float = 0.12, x2: float = 0.14, x0: float = 0.05,
                 grounding: str = "solid", rg: float = 0.0):
        self.name = name
        self.bus = bus
        self.voltage_setpoint = voltage_setpoint
        self.mw_setpoint = mw_setpoint

        # Subtransient reactances
        self.x1pp = x1pp
        self.x2 = x2
        self.x0 = x0

        # Grounding
        self.grounding = grounding
        self.rg = rg

        # Determine if generator introduces a fault
        self.fault = grounding in ["solid", "resistance"]
        self.bus.fault = self.fault  # Attach fault flag to bus
        if not hasattr(bus, "faulted_buses"):
            bus.faulted_buses = []
        if self.fault:
            bus.fault = True
            bus.faulted_buses.append(bus.name)

    def get_subtransient_admittance(self):
        return 1j / self.x1pp if self.x1pp != 0 else 0

    def get_ground_admittance(self):
        if self.grounding == "solid":
            return np.inf
        elif self.rg > 0:
            return 1 / self.rg
        else:
            return 0