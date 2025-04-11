# Group 8 - Project 2
# ECE 2774
# Milestone 5

from Bus import Bus

class Generator:

    def __init__(self, name: str, bus: Bus, voltage_setpoint: float, mw_setpoint: float):
        self.name = name
        self.bus = bus
        self.voltage_setpoint = voltage_setpoint
        self.mw_setpoint = mw_setpoint