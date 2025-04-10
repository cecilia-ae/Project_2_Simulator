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

    def add_bus(self, bus: str, base_kv: float):

        # add a bus to the circuit

        if bus in self.buses:
            raise ValueError(f"Bus '{bus}' already exists.")
        self.buses[bus] = Bus(bus, base_kv)

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

    def add_generator(self, name: str, bus: str, voltage_setpoint: float, mw_setpoint: float,
                      x1pp: float = 0.12, x2: float = 0.14, x0: float = 0.05, grounding: str = "solid", rg: float = 0.0):

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

        self.generators[name] = Generator(name, bus_obj, voltage_setpoint, mw_setpoint,
                                          x1pp=x1pp, x2=x2, x0=x0, grounding=grounding, rg=rg)




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
        self.loads[name] = Load(name, bus, real_power, reactive_power)

    def calc_ybus(self):
        # set up the zeroes data frame
        busnames = list(self.buses.keys())
        N = len(busnames)
        ybus = pd.DataFrame(np.zeros((N, N), dtype=complex), index=busnames, columns=busnames)

        # add contributions from all transmission lines
        for tline in self.transmissionlines.values():
            bus1_name = tline.bus1.name
            bus2_name = tline.bus2.name
            yprim = tline.yprim

            # Add diagonal elements
            ybus.loc[bus1_name, bus1_name] += yprim.loc[bus1_name, bus1_name]
            ybus.loc[bus2_name, bus2_name] += yprim.loc[bus2_name, bus2_name]

            # Add off-diagonal elements
            ybus.loc[bus1_name, bus2_name] += yprim.loc[bus1_name, bus2_name]
            ybus.loc[bus2_name, bus1_name] += yprim.loc[bus2_name, bus1_name]

        # add contributions from all transformers
        for xfmr in self.transformers.values():
            bus1_name = xfmr.bus1.name
            bus2_name = xfmr.bus2.name
            yprim = xfmr.yprim

            # Add diagonal elements
            ybus.loc[bus1_name, bus1_name] += yprim.loc[bus1_name, bus1_name]
            ybus.loc[bus2_name, bus2_name] += yprim.loc[bus2_name, bus2_name]

            # Add off-diagonal elements
            ybus.loc[bus1_name, bus2_name] += yprim.loc[bus1_name, bus2_name]
            ybus.loc[bus2_name, bus1_name] += yprim.loc[bus2_name, bus1_name]


        # Add generator subtransient admittances for faulted buses
        for gen in self.generators.values():
            if hasattr(gen.bus, 'fault') and gen.bus.fault:
                ybus.loc[gen.bus.name, gen.bus.name] += gen.get_subtransient_admittance()

        self.ybus = ybus

        return ybus

    def calc_zbus(self):
        if self.ybus is None or self.ybus.empty:
            raise ValueError("Ybus must be calculated before Zbus.")
        try:
            zbus = pd.DataFrame(np.linalg.inv(self.ybus.values), index=self.ybus.index, columns=self.ybus.columns)
            return zbus
        except np.linalg.LinAlgError:
            print("Error: Ybus matrix is singular and cannot be inverted.")
            return None













