# Group 8 - Project 2
# ECE 2774
# Milestone 1

class Bus:

    # Class variable to keep track of the number of Bus instances
    instance_count = 0

    def __init__(self, name: str, base_kv: float):
        self.name = name
        self.base_kv = base_kv
        Bus.instance_count += 1
        self.index = Bus.instance_count