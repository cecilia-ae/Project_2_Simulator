# Group 8 - Project 2
# ECE 2774
# Milestone 1

class Bus:
    # Class variable to keep track of the number of Bus instances
    instance_count = 0

    def __init__(self, name: str, base_kv: float):

        self.name = name
        self.base_kv = base_kv
        self.vpu = 1
        self.delta = 0
        self.bus_type = "PQ Bus"

        Bus.instance_count += 1
        self.index = Bus.instance_count


# PQ bus = buses connected to loads (transmission lines in this case).
# PV Bus = buses connected to a generator in this case.
# Slack Bus = can be either 1 or 7 in the 7 bus circuit.


