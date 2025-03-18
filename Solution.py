# Group 8 - Project 2
# ECE 2774
# Solution

import numpy as np
from Circuit import Circuit
from Bus import Bus


class Solution:

    def __init__(self, circuit: Circuit):
        self.circuit = circuit
        self.ybus = circuit.ybus  # Use Ybus from Circuit
        self.voltages, self.angles = self.get_voltages()  # Extract voltage magnitudes & angles

    def get_voltages(self):

        voltages = {}
        angles = {}

        for bus_name, bus in self.circuit.buses.items():

                voltages[bus_name] = bus.vpu  # start with 1.0 per-unit
                angles[bus_name] =  bus.delta # assume flat start

        return voltages, angles

    def compute_power_injection(self):

        num_buses = len(self.circuit.buses)  # total number of buses
        P = np.zeros(num_buses)  # array for real power injections
        Q = np.zeros(num_buses)  # array for reactive power injections

        bus_list = list(self.circuit.buses.keys())  #ordered list of bus names

        for i, bus_name in enumerate(bus_list):  # iterate through each bus
            vk = self.voltages[bus_name]  # voltage magnitude at bus k
            delta_k = self.angles[bus_name]  # voltage angle at bus k
            ybus_row = self.circuit.ybus.loc[bus_name]  # get Ybus row for bus k

            pk, qk = 0, 0  # initialize power injections to be 0

            for bus_j, ykj in ybus_row.items():  # iterate through connected buses
                if bus_j in self.voltages:
                    vj = self.voltages[bus_j]  # voltage magnitude at bus j
                    delta_j = self.angles[bus_j]  # voltage angle at bus j
                    theta_kj = np.angle(ykj)  # phase angle of Ybus element

                    # compute power injections using the correct formulas
                    pk += vk * vj * abs(ykj) * np.cos(delta_k - delta_j - theta_kj)
                    qk += vk * vj * abs(ykj) * np.sin(delta_k - delta_j - theta_kj)

            P[i] = pk  # store computed real power injection
            Q[i] = qk  # store computed reactive power injection

        return P, Q

    def compute_power_mismatch(self):
        buses = self.circuit.buses
        voltages = {bus.name: bus.vpu * np.exp(1j * np.radians(bus.delta)) for bus in buses.values()}

        mismatch_vector = []

        if not set(buses.keys()).issubset(set(self.ybus.index)):
            raise ValueError("Mismatch between buses in circuit and Y-bus matrix.")

        for bus_name, bus in buses.items():
            if bus.bus_type == "Slack Bus":
                continue  # No mismatch for Slack Bus

            p_specified = 0
            q_specified = 0

            # Sum power injections from generators
            for gen in self.circuit.generators.values():
                if gen.bus.name == bus_name:
                    p_specified += gen.mw_setpoint
                    if bus.bus_type == "PQ Bus":
                        q_specified += gen.mvar_setpoint if hasattr(gen, 'mvar_setpoint') else 0

            # Sum power consumed by loads
            for load in self.circuit.loads.values():
                if load.bus == bus_name:
                    p_specified -= load.real_power
                    q_specified -= load.reactive_power

            # Calculate actual injected power using Ybus
            v_bus = voltages[bus_name]
            p_calculated = 0
            q_calculated = 0

            for other_bus_name, v_other in voltages.items():
                if bus_name in self.ybus.index and other_bus_name in self.ybus.columns:
                    y_ij = self.ybus.loc[bus_name, other_bus_name]
                    p_calculated += np.real(v_bus * np.conj(y_ij * v_other))
                    q_calculated += np.imag(v_bus * np.conj(y_ij * v_other))

            # Compute mismatches
            delta_p = p_specified - p_calculated
            delta_q = q_specified - q_calculated

            mismatch_vector.append(delta_p)
            if bus.bus_type == "PQ Bus":
                mismatch_vector.append(delta_q)

        return np.array(mismatch_vector)

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
    circuit1.add_generator("G1", "Bus1", 230, 100)
    circuit1.add_generator("G2", "Bus7", 20, 100)

    # CHANGE SLACK BUS
    circuit1.set_slack_bus("Bus7")

    # ADD LOAD
    circuit1.add_load("L1", "Bus3", 110, 50)
    circuit1.add_load("L2", "Bus4", 100, 70)
    circuit1.add_load("L3", "Bus5", 100,65)

    circuit1.calc_ybus()

    # solution object (extracts voltages from circuit)
    solution = Solution(circuit1)

    # compute power injections
    P, Q = solution.compute_power_injection()

    print("\nPower Injection Results:")
    for i, bus in enumerate(circuit1.buses.keys()):
        print(f"{bus}: P = {P[i]:.3f}, Q = {Q[i]:.3f}")

    # computer power mismatch

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

    # Check validation
    if np.allclose(mismatches, 0, atol=1e-6):
        print("\nValidation Passed: Mismatches are within tolerance.")
    else:
        print("\nValidation Failed: Check power flow calculations.")