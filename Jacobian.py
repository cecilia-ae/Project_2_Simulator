# Group 8 - Project 2
# ECE 2774
# Jacobian

import numpy as np
from Solution import Solution
from Circuit import Circuit


class Jacobian:
    def __init__(self, solution):
        self.solution = solution
        self.ybus = solution.ybus
        self.voltages = solution.voltages
        self.angles = solution.angles
        self.buses = solution.circuit.buses

    def calc_j1(self, pv_pq_buses, all_bus):
        sizep = len(pv_pq_buses)
        J1 = np.zeros((sizep, sizep))
        for i, bus_i in enumerate(pv_pq_buses):
            vi = self.voltages[bus_i]
            delta_i = self.angles[bus_i]
            y_row = self.ybus.loc[bus_i]
            for j, bus_j in enumerate(pv_pq_buses):
                vj = self.voltages[bus_j]
                delta_j = self.angles[bus_j]
                yij = y_row[bus_j]
                theta_ij = np.angle(yij)
                if i == j:
                    J1[i, j] = -vi * sum(self.voltages[b] * abs(y_row[b]) * np.sin(delta_i - self.angles[b] - np.angle(y_row[b]))
                        for b in all_bus if b != bus_i)
                else:
                    J1[i, j] = vi * vj * abs(yij) * np.sin(delta_i - delta_j - theta_ij)
        return J1

    def calc_j2(self, pv_pq_buses, pq_buses, all_bus):
        sizep = len(pv_pq_buses)
        sizeq = len(pq_buses)
        J2 = np.zeros((sizep, sizeq))
        for i, bus_i in enumerate(pv_pq_buses):
            vi = self.voltages[bus_i]
            delta_i = self.angles[bus_i]
            y_row = self.ybus.loc[bus_i]
            for j, bus_j in enumerate(pq_buses):
                vj = self.voltages[bus_j]
                delta_j = self.angles[bus_j]
                yij = y_row[bus_j]
                theta_ij = np.angle(yij)
                if bus_i == bus_j:
                    J2[i, j] = sum(
                        self.voltages[b] * abs(y_row[b]) *
                        np.cos(delta_i - self.angles[b] - np.angle(y_row[b]))
                        for b in all_bus) + vi * abs(y_row[bus_i]) * np.cos(np.angle(y_row[bus_i]))
                else:
                    J2[i, j] = vi * abs(y_row[bus_j]) * np.cos(delta_i - delta_j - theta_ij)
        return J2

    def calc_j3(self, pv_pq_buses, pq_buses, all_bus):
        sizep = len(pv_pq_buses)
        sizeq = len(pq_buses)
        J3 = np.zeros((sizeq, sizep))
        for i, bus_i in enumerate(pv_pq_buses):
            if bus_i not in pq_buses:
                continue
            vi = self.voltages[bus_i]
            delta_i = self.angles[bus_i]
            y_row = self.ybus.loc[bus_i]
            qi_idx = pq_buses.index(bus_i)
            for j, bus_j in enumerate(pv_pq_buses):
                vj = self.voltages[bus_j]
                delta_j = self.angles[bus_j]
                yij = y_row[bus_j]
                theta_ij = np.angle(yij)
                if i == j:
                    J3[qi_idx, j] = sum(
                        vi * self.voltages[b] * abs(y_row[b]) *
                        np.cos(delta_i - self.angles[b] - np.angle(y_row[b]))
                        for b in all_bus if b != bus_i)
                else:
                    J3[qi_idx, j] = -vi * vj * abs(yij) * np.cos(delta_i - delta_j - theta_ij)
        return J3

    def calc_j4(self, pq_buses, all_bus):
        sizeq = len(pq_buses)
        J4 = np.zeros((sizeq, sizeq))
        for i, bus_i in enumerate(pq_buses):
            vi = self.voltages[bus_i]
            delta_i = self.angles[bus_i]
            y_row = self.ybus.loc[bus_i]
            for j, bus_j in enumerate(pq_buses):
                delta_j = self.angles[bus_j]
                yij = y_row[bus_j]
                theta_ij = np.angle(yij)
                if bus_i == bus_j:
                    J4[i, j] = (sum(self.voltages[b] * abs(y_row[b]) * np.sin(delta_i - self.angles[b] - np.angle(y_row[b])) for b in all_bus)
                                - vi * abs(y_row[bus_i]) * np.sin(np.angle(y_row[bus_i])))
                else:
                    J4[i, j] = vi * abs(y_row[bus_j]) * np.sin(delta_i - delta_j - theta_ij)
        return J4

    def calc_jacobian(self):
        bus_list = list(self.buses.keys())
        pv_pq_buses = [b for b in bus_list if self.buses[b].bus_type in ["PV Bus", "PQ Bus"]]
        pq_buses = [b for b in bus_list if self.buses[b].bus_type == "PQ Bus"]
        all_bus = bus_list

        J1 = self.calc_j1(pv_pq_buses, all_bus)
        J2 = self.calc_j2(pv_pq_buses, pq_buses, all_bus)
        J3 = self.calc_j3(pv_pq_buses, pq_buses, all_bus)
        J4 = self.calc_j4(pq_buses, all_bus)

        J = np.vstack((np.hstack((J1, J2)), np.hstack((J3, J4))))

        return J


if __name__ == "__main__":
    # create test circuit
    circuit1 = Circuit("Test Circuit")

    # ADD BUSES
    circuit1.add_bus("Bus1", 20)
    circuit1.add_bus("Bus2", 230)
    circuit1.add_bus("Bus3", 230)
    circuit1.add_bus("Bus4", 230)
    circuit1.add_bus("Bus5", 230)
    circuit1.add_bus("Bus6", 230)
    circuit1.add_bus("Bus7", 18)

    # ADD TRANSMISSION LINES
    circuit1.add_conductor("Partridge", 0.642, 0.0217, 0.385, 460)
    circuit1.add_bundle("Bundle1", 2, 1.5, "Partridge")
    circuit1.add_geometry("Geometry1", 0, 0, 18.5, 0, 37, 0)

    circuit1.add_tline("Line1", "Bus2", "Bus4", "Bundle1", "Geometry1", 10)
    circuit1.add_tline("Line2", "Bus2", "Bus3", "Bundle1", "Geometry1", 25)
    circuit1.add_tline("Line3", "Bus3", "Bus5", "Bundle1", "Geometry1", 20)
    circuit1.add_tline("Line4", "Bus4", "Bus6", "Bundle1", "Geometry1", 20)
    circuit1.add_tline("Line5", "Bus5", "Bus6", "Bundle1", "Geometry1", 10)
    circuit1.add_tline("Line6", "Bus4", "Bus5", "Bundle1", "Geometry1", 35)

    # ADD TRANSFORMERS
    circuit1.add_transformer("T1", "Bus1", "Bus2", 125, 8.5, 10, "y-y", 0.05)
    circuit1.add_transformer("T2", "Bus6", "Bus7", 200, 10.5, 12, "y-y", 0.05)

    # ADD GENERATORS
    circuit1.add_generator("G1", "Bus1", 20, 100, 0.05, True)
    circuit1.add_generator("G2", "Bus7", 18, 200, 0.05, True)

    # ADD LOAD
    circuit1.add_load("L1", "Bus3", 110, 50)
    circuit1.add_load("L2", "Bus4", 100, 70)
    circuit1.add_load("L3", "Bus5", 100,65)

    circuit1.calc_ybus_pos_sequence()

    solution = Solution(circuit1)

    # power injections
    P, Q = solution.compute_power_injection()
    print("\nPower Injection Results:")
    for i, bus in enumerate(circuit1.buses.keys()):
        print(f"{bus}: P = {P[i]:.3f}, Q = {Q[i]:.3f}")

    # power mismatches
    mismatches = solution.compute_power_mismatch()
    print("\nPower Mismatch Results:")
    index = 0
    for bus_name, bus in circuit1.buses.items():
        if bus.bus_type == "Slack Bus":
            continue  # Skip Slack Bus in the mismatch vector

        print(f"{bus_name}: ΔP = {mismatches[index]:.4f}")
        index += 1
        if bus.bus_type == "PQ Bus":
            print(f"      ΔQ = {mismatches[index]:.4f}")
            index += 1


    jacobian = Jacobian(solution)
    J = jacobian.calc_jacobian()

    # Extract the bus lists needed for labeling
    bus_list = list(circuit1.buses.keys())
    pv_pq_buses = [b for b in bus_list if circuit1.buses[b].bus_type in ["PV Bus", "PQ Bus"]]
    pq_buses = [b for b in bus_list if circuit1.buses[b].bus_type == "PQ Bus"]

    # Create row and column labels
    row_labels = []
    for bus in pv_pq_buses:
        row_labels.append(f"∂P {bus}")
    for bus in pq_buses:
        row_labels.append(f"∂Q {bus}")

    col_labels = []
    for bus in pv_pq_buses:
        col_labels.append(f"∂δ {bus}")
    for bus in pq_buses:
        col_labels.append(f"∂V {bus}")

    # Print Jacobian matrix with labels
    print("\nJacobian Matrix:")

    # Calculate max width for row labels
    row_width = max(len(label) for label in row_labels) + 1
    col_width = 12

    print(" " * row_width, end="")
    for col in col_labels:
        print(f"{col:^{col_width}}", end="")
    print()

    for i, row_label in enumerate(row_labels):
        print(f"{row_label:{row_width}}", end="")
        for j in range(J.shape[1]):
            print(f"{J[i, j]:^{col_width}.6f}", end="")
        print()