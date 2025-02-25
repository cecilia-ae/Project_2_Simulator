# Group 8 - Project 2
# ECE 2774
# Milestone 2

from typing import Dict
import numpy as np
import pandas as pd

pd.set_option('display.max_columns', None)  # show all columns
pd.set_option('display.width', 1000)  # increase width to prevent wrapping
pd.set_option('display.max_colwidth', None)  # ensure full content is displayed

from Conductor import Conductor
from Bundle import Bundle
from Geometry import Geometry
from Bus import Bus
from TransmissionLine import TransmissionLine
from Transformer import Transformer
class Circuit:


    def __init__(self, name: str):
        self.name = name  # Set the circuit name
        self.buses: Dict[str, Bus] = {}
        self.transformers: Dict[str, Transformer] = {}
        self.conductors: Dict[str, Conductor] = {}
        self.bundles: Dict[str, Bundle] = {}
        self.geometries: Dict[str, Geometry] = {}
        self.transmissionlines: Dict[str, TransmissionLine] = {}

        self.ybus = self.calc_ybus()

    def add_bus(self, bus: str, base_kv: float, vpu: float, delta: float, bus_type: str):

        # add a bus to the circuit

        if bus in self.buses:
            raise ValueError(f"Bus '{bus}' already exists.")
        self.buses[bus] = Bus(bus, base_kv, vpu, delta, bus_type)

    def add_transformer(self, name: str, bus1_name: str, bus2_name: str, power_rating: float,
                        impedance_percent: float, x_over_r_ratio: float):

        # add a transformer to the circuit

        if bus1_name not in self.buses:
            raise ValueError(f"Bus '{bus1_name}' does not exist in the circuit.")
        if bus2_name not in self.buses:
            raise ValueError(f"Bus '{bus2_name}' does not exist in the circuit.")
        if name in self.transformers:
            raise ValueError(f"Transformer '{name}' already exists.")

        bus1 = self.buses[bus1_name]
        bus2 = self.buses[bus2_name]

        self.transformers[name] = Transformer(name, bus1, bus2, power_rating, impedance_percent, x_over_r_ratio)

    def add_conductor(self, name: str, diam: float, gmr: float, resistance: float, ampacity: float):

        # add a conductor type to the circuit

        if name in self.conductors:
            raise ValueError(f"Conductor '{name}' already exists.")
        self.conductors[name] = Conductor(name, diam, gmr, resistance, ampacity)

    def add_bundle(self, name: str, num_conductors: int, spacing: float, conductor_name: str):

        #add a bundle type to the circuit

        if name in self.bundles:
            raise ValueError(f"Bundle '{name}' already exists.")
        if conductor_name not in self.conductors:
            raise ValueError(f"Conductor '{conductor_name}' not found.")

        conductor = self.conductors[conductor_name]
        self.bundles[name] = Bundle(name, num_conductors, spacing, conductor)

    def add_geometry(self, name: str, xa: float, ya: float, xb: float, yb: float, xc: float, yc: float):

        #add a geometry type to the circuit

        if name in self.geometries:
            raise ValueError(f"Geometry '{name}' already exists.")
        self.geometries[name] = Geometry(name, xa, ya, xb, yb, xc, yc)

    def add_tline(self, name: str, bus1_name: str, bus2_name: str, bundle_name: str, geometry_name: str, length: float):

        # adds a Transmission Line to the circuit using existing Buses, Bundles, and Geometry

        if bus1_name not in self.buses:
            raise ValueError(f"Bus '{bus1_name}' does not exist in the circuit.")
        if bus2_name not in self.buses:
            raise ValueError(f"Bus '{bus2_name}' does not exist in the circuit.")
        if bundle_name not in self.bundles:
            raise ValueError(f"Bundle '{bundle_name}' not found.")
        if geometry_name not in self.geometries:
            raise ValueError(f"Geometry '{geometry_name}' not found.")
        if name in self.transmissionlines:
            raise ValueError(f"Transmission Line '{name}' already exists.")

        bus1 = self.buses[bus1_name]
        bus2 = self.buses[bus2_name]
        bundle = self.bundles[bundle_name]
        geometry = self.geometries[geometry_name]

        self.transmissionlines[name] = TransmissionLine(name, bus1, bus2, bundle, geometry, length)

    def calc_ybus(self):
        # set up the zeroes data frame
        busnames = list(self.buses.keys())  # list of bus names
        N = len(busnames)
        ybus = pd.DataFrame(np.zeros((N, N), dtype=complex), index=busnames, columns=busnames)

        for tline_name, tline in self.transmissionlines.items():
            bus1_name = tline.bus1.name
            bus2_name = tline.bus2.name

            # use the yprim data from the transmission line
            yprim = tline.yprim

            # add the transmission line admittance matrix to Ybus
            ybus.loc[bus1_name, bus1_name] += yprim.loc[bus1_name, bus1_name]
            ybus.loc[bus2_name, bus2_name] += yprim.loc[bus2_name, bus2_name]
            ybus.loc[bus1_name, bus2_name] += yprim.loc[bus1_name, bus2_name]
            ybus.loc[bus2_name, bus1_name] += yprim.loc[bus2_name, bus1_name]

        for transformer_name, transformer in self.transformers.items():
            bus1_name = transformer.bus1.name
            bus2_name = transformer.bus2.name

            # use the yprim data from the transformer
            yprim = transformer.yprim

            # add the transformer admittance matrix to ybus
            ybus.loc[bus1_name, bus1_name] += yprim.loc[bus1_name, bus1_name]
            ybus.loc[bus2_name, bus2_name] += yprim.loc[bus2_name, bus2_name]
            ybus.loc[bus1_name, bus2_name] += yprim.loc[bus1_name, bus2_name]
            ybus.loc[bus2_name, bus1_name] += yprim.loc[bus2_name, bus1_name]
        self.ybus = ybus


        return ybus

if __name__ == "__main__":
        #verify Ybus
        circuit1 = Circuit("Test Circuit")

        # ADD BUSES
        circuit1.add_bus("Bus1", 230, 1, 0 ,"Slack Bus")
        circuit1.add_bus("Bus2", 230, 1, 0 ,"PV Bus")
        circuit1.add_bus("Bus3", 230, 1, 0 ,"PV Bus")
        circuit1.add_bus("Bus4", 230, 1, 0 ,"PV Bus")
        circuit1.add_bus("Bus5", 230, 1, 0 ,"PV Bus")
        circuit1.add_bus("Bus6", 230, 1, 0 ,"PV Bus")
        circuit1.add_bus("Bus7", 230, 1, 0 ,"PQ Bus")

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
        circuit1.add_transformer("T1", "Bus1", "Bus2", 125,8.5, 10)
        circuit1.add_transformer("T2", "Bus6", "Bus7", 200,10.5, 12)

        print("busnames:", list(circuit1.buses.keys()))  # Should print list of names

        circuit1.calc_ybus()

        print("Ybus DataFrame:\n", circuit1.ybus)
        print("Ybus Index:", circuit1.ybus.index)
        print("Ybus Columns:", circuit1.ybus.columns)
