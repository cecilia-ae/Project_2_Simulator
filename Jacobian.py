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

    def calc_jacobian(self):

        # ordered lists of buses by type (except slack)

        bus_list = list(self.buses.keys())
        pv_pq_buses = [b for b in bus_list if self.buses[b].bus_type in ["PV Bus", "PQ Bus"]]
        pq_buses = [b for b in bus_list if self.buses[b].bus_type == "PQ Bus"]

        # dimensions
        sizep = len(pv_pq_buses)  # PV + PQ buses for P equations
        sizeq = len(pq_buses)     # Only PQ buses for Q equations

        # Jacobian sub-matrices
        J1 = np.zeros((sizep, sizep))  # dP/dδ
        J2 = np.zeros((sizep, sizeq))  # dP/dV
        J3 = np.zeros((sizeq, sizep))  # dQ/dδ
        J4 = np.zeros((sizeq, sizeq))  # dQ/dV

        for i, bus_i in enumerate(pv_pq_buses):
            vi = self.voltages[bus_i]
            delta_i = self.angles[bus_i]
            y_row = self.ybus.loc[bus_i]

            # check if also a PQ bus (for Q equations)
            qi_idx = pq_buses.index(bus_i) if bus_i in pq_buses else None

            for j, bus_j in enumerate(pv_pq_buses):
                # Skip self-terms for now (we'll handle them separately)
                if bus_j != bus_i:
                    vj = self.voltages[bus_j]
                    delta_j = self.angles[bus_j]
                    yij = y_row[bus_j]
                    theta_ij = np.angle(yij)

                    # Calculate derivatives
                    dP_dDelta = vi * vj * abs(yij) * np.sin(delta_i - delta_j - theta_ij)
                    J1[i, j] = dP_dDelta

                    # Fill J3 if bus_i is a PQ bus
                    if qi_idx is not None:
                        dQ_dDelta = -vi * vj * abs(yij) * np.cos(delta_i - delta_j - theta_ij)
                        J3[qi_idx, j] = dQ_dDelta

                # Check if bus_j is a PQ bus (for V derivatives)
                if bus_j in pq_buses:
                    qj_idx = pq_buses.index(bus_j)
                    vj = self.voltages[bus_j]
                    delta_j = self.angles[bus_j]
                    yij = y_row[bus_j]
                    theta_ij = np.angle(yij)

                    # Skip self-terms
                    if bus_j != bus_i:
                        dP_dV = vi * abs(yij) * np.cos(delta_i - delta_j - theta_ij)
                        J2[i, qj_idx] = dP_dV

                        # Fill J4 if bus_i is a PQ bus
                        if qi_idx is not None:
                            dQ_dV = vi * abs(yij) * np.sin(delta_i - delta_j - theta_ij)
                            J4[qi_idx, qj_idx] = dQ_dV

        # full Jacobian
        J_top = np.hstack((J1, J2))
        J_bottom = np.hstack((J3, J4))
        J = np.vstack((J_top, J_bottom))

        return J

if __name__ == "__main__":
    # create test circuit
    circuit1 = Circuit("Test Circuit")

    # ADD BUSES
    circuit1.add_bus("Bus1", 230)
    circuit1.add_bus("Bus2", 230)
    circuit1.add_bus("Bus3", 230)
    circuit1.add_bus("Bus4", 230)
    circuit1.add_bus("Bus5", 230)
    circuit1.add_bus("Bus6", 230)
    circuit1.add_bus("Bus7", 230)

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


    # print jacobian
    print("\nJacobian Matrix:")
    for row in J:
        print(" | ".join(f"{val:10.4f}" for val in row))
