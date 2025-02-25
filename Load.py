# Group 8 - Project 2
# ECE 2774
# Milestone 5

from Bus import Bus

class Load:

    def __init__(self, name: str, bus: Bus, real_power: float, reactive_power: float):
        self.name = name
        self.bus = bus
        self.real_power = real_power
        self.reactive_power = reactive_power