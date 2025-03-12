# Group 8 - Project 2
# ECE 2774
# Solution

import numpy as np
import pandas as pd
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


if __name__ == "__main__":
    # Create test circuit
    circuit = Circuit("Test Circuit")

    # Add buses
    circuit.add_bus("Bus1", 230)
    circuit.add_bus("Bus2", 230)
    circuit.add_bus("Bus3", 230)

    # Add a generator to Bus1 and set it as PV
    circuit.add_generator("G1", "Bus1", 230, 100)

    # Let the user pick which PV bus should be the Slack bus
    user_choice = input("Enter the bus name to be the Slack bus: ")
    circuit.set_slack_bus(user_choice)  # Set the Slack bus

    circuit.calc_ybus()

    # Instantiate solution object (extracts voltages from circuit)
    solution = Solution(circuit)

    # Compute power injections
    P, Q = solution.compute_power_injection()

    print("\nPower Injection Results:")
    for i, bus in enumerate(circuit.buses.keys()):
        print(f"{bus}: P = {P[i]:.3f}, Q = {Q[i]:.3f}")