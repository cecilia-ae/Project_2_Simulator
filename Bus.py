# Group 8 - Project 2
# ECE 2774
# Milestone 1

class Bus:
    # Class variable to keep track of the number of Bus instances
    instance_count = 0

    # Acceptable bus types
    valid_bus_type = {"Slack Bus", "PQ Bus", "PV Bus"}

    def __init__(self, name: str, base_kv: float, vpu: float, delta: float, bus_type: str):
        if bus_type not in self.valid_bus_type:
            raise ValueError(f"Invalid bus type. Must be one of {self.valid_bus_type}")

        self.name = name
        self.base_kv = base_kv
        self.vpu = vpu
        self.delta = delta
        self.bus_type = bus_type

        Bus.instance_count += 1
        self.index = Bus.instance_count


# Validation
if __name__ == "__main__":
    # define bus1 and bus2 before
    bus1 = Bus("Bus1", 20, 1,0,"PV Bus")
    bus2 = Bus("Bus2", 230, 1, 0, "Slack Bus")

    print(bus1.name, bus1.base_kv, bus1.vpu, bus1.delta, bus1.bus_type, bus1.index)
    print(bus2.name, bus2.base_kv, bus2.vpu, bus2.delta, bus2.bus_type, bus2.index)


