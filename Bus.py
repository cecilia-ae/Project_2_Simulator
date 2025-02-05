# Group 8 - Project 2
# ECE 2774
# Milestone 1

class Bus:

    # Class variable to keep track of the number of Bus instances
    bus_count = 0

    def __init__(self, name: str, base_kv: float):
        self.name = name
        self.base_kv = base_kv
        Bus.bus_count += 1
        self.index = Bus.bus_count

# Validation
if __name__ == "__main__":

    bus1 = Bus("Bus 1", 20)
    bus2 = Bus("Bus 2", 230)
    print("Bus 1:", bus1.name, bus1.base_kv, "Index:", bus1.index)
    print("Bus 2:", bus2.name, bus2.base_kv, "Index:", bus2.index)
    print("Total Buses:", Bus.bus_count)



