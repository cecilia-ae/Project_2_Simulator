# Project 2 - Power Systems Simulator
# ECE 2774 - Advanced Power Systems Analysis
# Group 8
# Cecilia Espadas & Maria Luiza Hermann

from Circuit import Circuit
from Solution import Solution

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
circuit1.add_transformer("T1", "Bus1", "Bus2", 125, 8.5, 10, "delta-y", 1)
circuit1.add_transformer("T2", "Bus6", "Bus7", 200, 10.5, 12, "delta-y", 999999)

# ADD GENERATORS
circuit1.add_generator("G1", "Bus1", 20, 100, 0, True)
circuit1.add_generator("G2", "Bus7", 18, 200, 1, True)

# ADD LOAD
circuit1.add_load("L1", "Bus3", 110, 50)
circuit1.add_load("L2", "Bus4", 100, 70)
circuit1.add_load("L3", "Bus5", 100, 65)

solution = Solution(circuit1)

solution.power_flow()

solution.fault_study()