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
from Generator import Generator
from Load import Load
class Circuit:

    def __init__(self, name: str):
        self.name = name  # Set the circuit name
        self.buses: Dict[str, Bus] = {}
        self.transformers: Dict[str, Transformer] = {}
        self.conductors: Dict[str, Conductor] = {}
        self.bundles: Dict[str, Bundle] = {}
        self.geometries: Dict[str, Geometry] = {}
        self.transmissionlines: Dict[str, TransmissionLine] = {}
        self.generators: Dict[str, Generator] = {}
        self.loads: Dict[str, Load] = {}

        self.slack_bus = None
        self.ybus = self.calc_ybus()
        self.ybus_pos = self.calc_ybus_pos_sequence()
        self.ybus_neg = self.calc_ybus_neg_sequence()
        self.ybus_zero = self.calc_ybus_zero_sequence()
        self.zbus_pos, self.zbus_neg, self.zbus_zero = self.calc_sequence_zbuses()


    def add_bus(self, bus: str, base_kv: float):

        # add a bus to the circuit

        if bus in self.buses:
            raise ValueError(f"Bus '{bus}' already exists.")
        self.buses[bus] = Bus(bus, base_kv)

    def add_transformer(self, name: str, bus1_name: str, bus2_name: str, power_rating: float,
                        impedance_percent: float, x_over_r_ratio: float, connection_type: str, grounding_impedance: float):

        # add a transformer to the circuit

        if bus1_name not in self.buses:
            raise ValueError(f"Bus '{bus1_name}' does not exist in the circuit.")
        if bus2_name not in self.buses:
            raise ValueError(f"Bus '{bus2_name}' does not exist in the circuit.")
        if name in self.transformers:
            raise ValueError(f"Transformer '{name}' already exists.")

        bus1 = self.buses[bus1_name]
        bus2 = self.buses[bus2_name]

        self.transformers[name] = Transformer(name, bus1, bus2, power_rating, impedance_percent, x_over_r_ratio, connection_type, grounding_impedance)

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

    def add_generator(self, name: str, bus: Bus, voltage_setpoint: float, mw_setpoint: float, grounding_impedance: float, is_grounded: bool = True):

        # add a generator to the circuit

        if name in self.generators:
            raise ValueError(f"Generator '{name}' already exists.")
        if bus not in self.buses:
            raise ValueError(f"Bus '{bus}' does not exist in the circuit.")

        bus_obj = self.buses[bus]

        if len(self.generators) == 0:
            self.slack_bus = bus
            bus_obj.bus_type = "Slack Bus"
        else:
            bus_obj.bus_type = "PV Bus"

        self.generators[name] = Generator(name, bus_obj, voltage_setpoint, mw_setpoint, grounding_impedance, is_grounded)

    def set_slack_bus(self, bus_name: str):
        if bus_name not in self.buses:
            raise ValueError(f"Bus '{bus_name}' does not exist in the circuit.")
        if bus_name not in [gen.bus.name for gen in self.generators.values()]:
            raise ValueError(f"Bus '{bus_name}' is not connected to any generator.")

        # Reset current slack bus to PV bus
        if self.slack_bus and self.slack_bus in self.buses:
            self.buses[self.slack_bus].bus_type = "PV Bus"

        # Set the new slack bus
        self.slack_bus = bus_name
        self.buses[bus_name].bus_type = "Slack Bus"

    def add_load(self, name: str, bus: str, real_power: float, reactive_power: float):

        # add a generator to the circuit

        if name in self.loads:
            raise ValueError(f"Load '{name}' already exists.")
        self.loads[name] = Load(name, self.buses[bus], real_power, reactive_power)

    def calc_ybus(self):
        busnames = list(self.buses.keys())
        N = len(busnames)
        ybus = pd.DataFrame(np.zeros((N, N), dtype=complex), index=busnames, columns=busnames)

        for line in self.transmissionlines.values():
            b1, b2 = line.bus1.name, line.bus2.name
            y = line.yprim
            ybus.loc[b1, b1] += y.loc[b1, b1]
            ybus.loc[b2, b2] += y.loc[b2, b2]
            ybus.loc[b1, b2] += y.loc[b1, b2]
            ybus.loc[b2, b1] += y.loc[b2, b1]

        for xfmr in self.transformers.values():
            b1, b2 = xfmr.bus1.name, xfmr.bus2.name
            y = xfmr.yprim
            ybus.loc[b1, b1] += y.loc[b1, b1]
            ybus.loc[b2, b2] += y.loc[b2, b2]
            ybus.loc[b1, b2] += y.loc[b1, b2]
            ybus.loc[b2, b1] += y.loc[b2, b1]


        self.ybus = ybus
        return ybus


    def calc_ybus_pos_sequence(self):
        busnames = list(self.buses.keys())
        N = len(busnames)
        ybus_pos = pd.DataFrame(np.zeros((N, N), dtype=complex), index=busnames, columns=busnames)

        for line in self.transmissionlines.values():
            b1, b2 = line.bus1.name, line.bus2.name
            y = line.yprim
            ybus_pos.loc[b1, b1] += y.loc[b1, b1]
            ybus_pos.loc[b2, b2] += y.loc[b2, b2]
            ybus_pos.loc[b1, b2] += y.loc[b1, b2]
            ybus_pos.loc[b2, b1] += y.loc[b2, b1]

        for xfmr in self.transformers.values():
            b1, b2 = xfmr.bus1.name, xfmr.bus2.name
            y = xfmr.yprim
            ybus_pos.loc[b1, b1] += y.loc[b1, b1]
            ybus_pos.loc[b2, b2] += y.loc[b2, b2]
            ybus_pos.loc[b1, b2] += y.loc[b1, b2]
            ybus_pos.loc[b2, b1] += y.loc[b2, b1]

        for gen in self.generators.values():
            b = gen.bus.name
            ybus_pos.loc[b, b] += gen.y_prim_positive_sequence().loc[b, b]

        for load in self.loads.values():
            b = load.bus.name
            ybus_pos.loc[b, b] += load.y_prim().loc[b, b]

        self.ybus_pos = ybus_pos
        return ybus_pos

    def calc_ybus_neg_sequence(self):
        busnames = list(self.buses.keys())
        N = len(busnames)
        ybus_neg = pd.DataFrame(np.zeros((N, N), dtype=complex), index=busnames, columns=busnames)

        for line in self.transmissionlines.values():
            b1, b2 = line.bus1.name, line.bus2.name
            y = line.yprim_neg
            ybus_neg.loc[b1, b1] += y.loc[b1, b1]
            ybus_neg.loc[b2, b2] += y.loc[b2, b2]
            ybus_neg.loc[b1, b2] += y.loc[b1, b2]
            ybus_neg.loc[b2, b1] += y.loc[b2, b1]

        for xfmr in self.transformers.values():
            b1, b2 = xfmr.bus1.name, xfmr.bus2.name
            y = xfmr.yprim_neg
            ybus_neg.loc[b1, b1] += y.loc[b1, b1]
            ybus_neg.loc[b2, b2] += y.loc[b2, b2]
            ybus_neg.loc[b1, b2] += y.loc[b1, b2]
            ybus_neg.loc[b2, b1] += y.loc[b2, b1]

        for gen in self.generators.values():
            b = gen.bus.name
            ybus_neg.loc[b, b] += gen.y_prim_negative_sequence().loc[b, b]

        for load in self.loads.values():
            b = load.bus.name
            ybus_neg.loc[b, b] += load.y_prim().loc[b, b]

        self.ybus_neg = ybus_neg
        return ybus_neg

    def calc_ybus_zero_sequence(self):
        busnames = list(self.buses.keys())
        N = len(busnames)
        ybus_zero = pd.DataFrame(np.zeros((N, N), dtype=complex), index=busnames, columns=busnames)

        for line in self.transmissionlines.values():
            b1, b2 = line.bus1.name, line.bus2.name
            y = line.yprim_zero
            ybus_zero.loc[b1, b1] += y.loc[b1, b1]
            ybus_zero.loc[b2, b2] += y.loc[b2, b2]
            ybus_zero.loc[b1, b2] += y.loc[b1, b2]
            ybus_zero.loc[b2, b1] += y.loc[b2, b1]

        for xfmr in self.transformers.values():
            b1, b2 = xfmr.bus1.name, xfmr.bus2.name
            y = xfmr.yprim_zero
            ybus_zero.loc[b1, b1] += y.loc[b1, b1]
            ybus_zero.loc[b2, b2] += y.loc[b2, b2]
            ybus_zero.loc[b1, b2] += y.loc[b1, b2]
            ybus_zero.loc[b2, b1] += y.loc[b2, b1]

        for gen in self.generators.values():
            b = gen.bus.name
            ybus_zero.loc[b, b] += gen.y_prim_zero_sequence().loc[b, b]


        self.ybus_zero = ybus_zero
        return ybus_zero

    def calc_sequence_zbuses(self):
        busnames = list(self.buses.keys())  # DO NOT title-case them

        try:
            self.zbus_pos = pd.DataFrame(np.linalg.inv(self.ybus_pos.values), index=busnames, columns=busnames)
            self.zbus_neg = pd.DataFrame(np.linalg.inv(self.ybus_neg.values), index=busnames, columns=busnames)
            self.zbus_zero = pd.DataFrame(np.linalg.inv(self.ybus_zero.values), index=busnames, columns=busnames)

            return self.zbus_pos, self.zbus_neg, self.zbus_zero
        except np.linalg.LinAlgError:
            print("One of the Ybus matrices is singular and cannot be inverted.")
            self.zbus_pos = self.zbus_neg = self.zbus_zero = None
            return None, None, None


if __name__ == "__main__":
        #verify Ybus
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

        # PRINT CHECK
        print(f"Bus1 type: {circuit1.buses['Bus1'].bus_type}")  # Should print "Slack Bus"
        print(f"Bus7 type: {circuit1.buses['Bus7'].bus_type}")  # Should print "PV Bus"

        # YBUS CHECK
        circuit1.calc_ybus()
        circuit1.calc_ybus_pos_sequence()
        circuit1.calc_ybus_neg_sequence()
        circuit1.calc_ybus_zero_sequence()
        circuit1.calc_sequence_zbuses()

        # Recalculate all sequence Ybuses and Zbuses
        print("Ybus:\n", circuit1.ybus)

        print("Ybus Positive Sequence:\n", circuit1.ybus_pos)
        print("\nYbus Negative Sequence:\n", circuit1.ybus_neg)
        print("\nYbus Zero Sequence:\n", circuit1.ybus_zero)


        print("\nZbus Positive Sequence:\n", circuit1.zbus_pos)
        print("\nZbus Negaitve Sequence:\n", circuit1.zbus_neg)
        print("\nZbus Zero Sequence:\n", circuit1.zbus_zero)
