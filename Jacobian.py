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
        # self.voltages = solution.voltages
        # self.angles = solution.angles
        self.voltages = {
            "Bus1": 1.00000,
            "Bus2": 0.93710,
            "Bus3": 0.92080,
            "Bus4": 0.93004,
            "Bus5": 0.92700,
            "Bus6": 0.93985,
            "Bus7": 0.99999}
        self.angles = {
            "Bus1": 0,
            "Bus2": -0.077492619,
            "Bus3": -0.095120444,
            "Bus4": -0.082030475,
            "Bus5": -0.084299403,
            "Bus6": -0.069115038,
            "Bus7": 0.037524579}
        self.buses = solution.circuit.buses

    def calc_jacobian(self):
        # PV and PQ buses
        bus_list = list(self.buses.keys())
        pv_pq_buses = [b for b in bus_list if self.buses[b].bus_type in ["PV Bus", "PQ Bus"]]
        pq_buses = [b for b in bus_list if self.buses[b].bus_type == "PQ Bus"]
        all_bus = [b for b in bus_list if self.buses[b].bus_type in ["PV Bus", "PQ Bus", "Slack"]]

        # dimensions for matrices
        sizep = len(pv_pq_buses)  # P equations (PV + PQ)
        sizeq = len(pq_buses)  # Q equations (PQ only)

        # sub matrices
        J1 = np.zeros((sizep, sizep))  # dP/dDelta
        J2 = np.zeros((sizep, sizeq))  # dP/dV
        J3 = np.zeros((sizeq, sizep))  # dQ/dDelta
        J4 = np.zeros((sizeq, sizeq))  # dQ/dV

        # Calculate J1 and J3 (derivatives with respect to angle)
        for i, bus_i in enumerate(pv_pq_buses):
            vi = self.voltages[bus_i]
            delta_i = self.angles[bus_i]
            y_row = self.ybus.loc[bus_i]

            # check if PQ bus for Q equations
            is_pq_bus = bus_i in pq_buses

            for j, bus_j in enumerate(pv_pq_buses):
                vj = self.voltages[bus_j]
                delta_j = self.angles[bus_j]
                yij = y_row[bus_j]
                theta_ij = np.angle(yij)  # admittance angle

                if i == j:
                    # diagonal elements of J1 (dP/dDelta)
                    J1[i, j] = -vi * sum(self.voltages[b] * abs(y_row[b]) * np.sin(delta_i - self.angles[b] - np.angle(y_row[b]))
                        for b in all_bus if b != bus_i)

                    """for b in all_bus:
                        if b != bus_i
                        equation"""

                    # diagonal elements of J3 (dQ/dDelta)
                    if is_pq_bus:
                        qi_idx = pq_buses.index(bus_i)
                        J3[qi_idx, j] = sum(vi * self.voltages[b] * abs(y_row[b]) * np.cos(
                            delta_i - self.angles[b] - np.angle(y_row[b]))
                                            for b in all_bus if b != bus_i)
                else:
                    # off-diagonal elements of J1 (dP/d delta)
                    J1[i, j] = vi * vj * abs(yij) * np.sin(delta_i - delta_j - theta_ij)

                    # off-diagonal elements of J3 (dQ/d delta)
                    if is_pq_bus:
                        qi_idx = pq_buses.index(bus_i)
                        J3[qi_idx, j] = -vi * vj * abs(yij) * np.cos(delta_i - delta_j - theta_ij)

        # Calculate J2 and J4 (derivatives with respect to voltage)
        for i, bus_i in enumerate(pv_pq_buses):
            vi = self.voltages[bus_i]
            delta_i = self.angles[bus_i]
            y_row = self.ybus.loc[bus_i]

            # check if PQ bus for Q equations
            is_pq_bus = bus_i in pq_buses

            for j, bus_j in enumerate(pq_buses):
                vj = self.voltages[bus_j]
                delta_j = self.angles[bus_j]
                yij = y_row[bus_j]
                theta_ij = np.angle(yij)

                if bus_i == bus_j:
                    # diagonal elements of J2 (dP/dV)
                    J2[i, j] = sum(
                        self.voltages[b] * abs(y_row[b]) * np.cos(delta_i - self.angles[b] - np.angle(y_row[b]))
                        for b in all_bus) + vi * abs(y_row[bus_i]) * np.cos(np.angle(y_row[bus_i]))

                    # diagonal elements of J4 (dQ/dV)
                    if is_pq_bus:
                        qi_idx = pq_buses.index(bus_i)
                        J4[qi_idx, j] = sum(
                            self.voltages[b] * abs(y_row[b]) * np.sin(delta_i - self.angles[b] - np.angle(y_row[b]))
                            for b in all_bus) - vi * abs(y_row[bus_i]) * np.sin(np.angle(y_row[bus_i]))
                else:
                    # off-diagonal elements of J2 (dP/dV)
                    J2[i, j] = vi * abs(y_row[bus_j]) * np.cos(delta_i - delta_j - theta_ij)

                    # off-diagonal elements of J4 (dQ/dV)
                    if is_pq_bus:
                        qi_idx = pq_buses.index(bus_i)
                        J4[qi_idx, j] = vi * abs(y_row[bus_j]) * np.sin(delta_i - delta_j - theta_ij)

        # Construct full Jacobian matrix
        J_top = np.hstack((J1, J2))
        J_bottom = np.hstack((J3, J4))
        J = np.vstack((J_top, J_bottom))

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

    # ADD TRANSMORMERS
    circuit1.add_transformer("T1", "Bus1", "Bus2", 125, 8.5, 10)
    circuit1.add_transformer("T2", "Bus6", "Bus7", 200, 10.5, 12)

    # ADD GENERATORS
    circuit1.add_generator("G1", "Bus1", 18, 100)
    circuit1.add_generator("G2", "Bus7", 20, 200)

    # ADD LOAD
    circuit1.add_load("L1", "Bus3", 110, 50)
    circuit1.add_load("L2", "Bus4", 100, 70)
    circuit1.add_load("L3", "Bus5", 100,65)

    circuit1.calc_ybus()

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

    # Print jacobian matrix with bus labels
    print("\nJacobian Matrix:")

    # bus labels list
    bus_list = list(circuit1.buses.keys())
    pv_pq_buses = [b for b in bus_list if circuit1.buses[b].bus_type in ["PV Bus", "PQ Bus"]]
    pq_buses = [b for b in bus_list if circuit1.buses[b].bus_type == "PQ Bus"]
    bus_labels = pv_pq_buses + pq_buses

    # header with bus labels
    print("     ", " | ".join([f"{label: <10}" for label in bus_labels]))

    # prnit each row with corresponding bus labels
    for i, row in enumerate(J):
        row_str = f"{bus_labels[i]: <5} "  # Label for the row
        row_str += " | ".join([f"{val:10.4f}" for val in row])  # Values in the row
        print(row_str)