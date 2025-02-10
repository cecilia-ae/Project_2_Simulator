# Group 8 - Project 2
# ECE 2774
# Milestone 2

from typing import Dict
from Conductor import Conductor
from Bundle import Bundle
from Geometry import Geometry
from Bus import Bus
from Transformer import Transformer
from TransmissionLine import TransmissionLine


class Circuit:

    def __init__(self, name: str):
        self.name = name  # Set the circuit name
        self.buses: Dict[str, Bus] = {}
        self.transformers: Dict[str, Transformer] = {}
        self.conductors: Dict[str, Conductor] = {}
        self.bundles: Dict[str, Bundle] = {}
        self.geometries: Dict[str, Geometry] = {}
        self.transmissionlines: Dict[str, TransmissionLine] = {}

    def add_bus(self, bus: str):

        # add a bus to the circuit

        if bus in self.buses:
            raise ValueError(f"Bus '{bus}' already exists.")
        self.buses[bus] = Bus(bus)

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

        # add a bundle type to the circuit

        if name in self.bundles:
            raise ValueError(f"Bundle '{name}' already exists.")
        if conductor_name not in self.conductors:
            raise ValueError(f"Conductor '{conductor_name}' not found.")

        conductor = self.conductors[conductor_name]
        self.bundles[name] = Bundle(name, num_conductors, spacing, conductor)

    def add_geometry(self, name: str, xa: float, ya: float, xb: float, yb: float, xc: float, yc: float):

        # add a geometry type to the circuit

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


if __name__ == "__main__":
    # Validation
    # 1 -  test the attribute initialization

    circuit1 = Circuit("Test Circuit")

    print(circuit1.name)  # Expected output: "Test Circuit"
    print(type(circuit1.name))  # Expected output: <class 'str'>

    print(circuit1.buses)  # Expected output: {}
    print(type(circuit1.buses))  # Expected output: <class 'dict'>

    print(circuit1.transformers)  # Expected output: {}
    print(type(circuit1.transformers))  # Expected output: <class 'dict'>

    print(circuit1.conductors)  # Expected output: {}
    print(type(circuit1.conductors))  # Expected output: <class 'dict'>

    print(circuit1.bundles)  # Expected output: {}
    print(type(circuit1.bundles))  # Expected output: <class 'dict'>

    print(circuit1.geometries)  # Expected output: {}
    print(type(circuit1.geometries))  # Expected output: <class 'dict'>

    print(circuit1.transmissionlines)  # Expected output: {}
    print(type(circuit1.transmissionlines))  # Expected output: <class 'dict'>

    # 2 - add and retrieve equipment components

    # conductor
    circuit1.add_conductor("Partridge", 0.642, 0.0217, 0.385, 460)
    print(type(circuit1.conductors["Partridge"]))  # expected output: <class 'Conductor'>
    print(circuit1.conductors["Partridge"].name, circuit1.conductors["Partridge"].diam,
          circuit1.conductors["Partridge"].gmr, circuit1.conductors["Partridge"].resistance,
          circuit1.conductors["Partridge"].ampacity)
    # expected output: Partridge 0.642 0.0217 0.385 460

    # bundle
    circuit1.add_bundle("Bundle1", 2, 1.5, "Partridge")
    print(type(circuit1.bundles["Bundle1"]))  # Expected output: <class 'Bundle'>
    print(circuit1.bundles["Bundle1"].name, circuit1.bundles["Bundle1"].num_conductors,
          circuit1.bundles["Bundle1"].spacing, circuit1.bundles["Bundle1"].conductor.name,
          circuit1.bundles["Bundle1"].dsl, circuit1.bundles["Bundle1"].dsc)
    # expected output: Bundle1 2 1.5 Partridge 0.18041618552668717 0.2003122562401013

    # geometry
    circuit1.add_geometry("Geometry1", 0, 0, 18.5, 0, 37, 0)
    print(type(circuit1.geometries["Geometry1"]))  # Expected output: <class 'Geometry'>
    print(circuit1.geometries["Geometry1"].name, circuit1.geometries["Geometry1"].xa,
          circuit1.geometries["Geometry1"].ya, circuit1.geometries["Geometry1"].xb, circuit1.geometries["Geometry1"].yb,
          circuit1.geometries["Geometry1"].xc, circuit1.geometries["Geometry1"].yc,
          circuit1.geometries["Geometry1"].Deq)
    # expected output: Geometry1 0 0 18.5 0 37 0 23.308539423055148

    # buses
    circuit1.buses["Bus1"] = Bus("Bus1", 230)
    circuit1.buses["Bus2"] = Bus("Bus2", 230)
    print(type(circuit1.buses["Bus1"]))  # Expected output: <class 'Bus'>
    print(circuit1.buses["Bus1"].name, circuit1.buses["Bus1"].base_kv)
    # expected output: Bus1, 230

    # transformer
    circuit1.add_transformer("Transformer1", "Bus1", "Bus2", 100, 5.0, 10.0)
    print(type(circuit1.transformers["Transformer1"]))  # Expected output: <class 'Transformer'>
    print(circuit1.transformers["Transformer1"].name, circuit1.transformers["Transformer1"].bus1.name,
          circuit1.transformers["Transformer1"].bus2.name, circuit1.transformers["Transformer1"].power_rating,
          circuit1.transformers["Transformer1"].impedance_percent, circuit1.transformers["Transformer1"].x_over_r_ratio)
    # expected output: Transformer1 Bus1 Bus2 100 5.0 10.0

    # transmission line
    circuit1.add_tline("Line1", "Bus1", "Bus2", "Bundle1", "Geometry1", 10)
    print(type(circuit1.transmissionlines["Line1"]))  # Expected output: <class 'TransmissionLine'>
    print(circuit1.transmissionlines["Line1"].name, circuit1.transmissionlines["Line1"].bus1.name,
          circuit1.transmissionlines["Line1"].bus2.name, circuit1.transmissionlines["Line1"].bundle.name,
          circuit1.transmissionlines["Line1"].geometry.name, circuit1.transmissionlines["Line1"].length,
          circuit1.transmissionlines["Line1"].zbase, circuit1.transmissionlines["Line1"].ybase,
          circuit1.transmissionlines["Line1"].zseries, circuit1.transmissionlines["Line1"].yshunt,
          circuit1.transmissionlines["Line1"].yseries, circuit1.transmissionlines["Line1"].yprim)
    # expected output: Line1 Bus1 Bus2 Bundle1 Geometry1
    # 10 529.0 0.001890359168241966 (0.0036389413988657847+0.011150810943831139j)
    # 0.03753603852127484j (26.449162856893846-81.04819020491786j)
    # [[(26.449162856893846-81.02942218565722j), (-26.449162856893846+81.04819020491786j)],
    # [(-26.449162856893846+81.04819020491786j), (26.449162856893846-81.02942218565722j)]]

    # 3. Verify Network Configuration
    print("Buses in circuit:", list(circuit1.buses.keys()))  # Expected output: ["Bus1", "Bus2"]
    print("Transformers in circuit:",list(circuit1.transformers.keys()))  # Expected output: [
    print("Conductors in circuit:", list(circuit1.conductors.keys()))  # Expected output: ["Partridge"]
    print("Bundles in circuit:", list(circuit1.bundles.keys()))  # Expected output: ["Bundle1"]
    print("Geometries in circuit:", list(circuit1.geometries.keys()))  # Expected output: ["Geometry1"]
    print("Transmission Lines in circuit:", list(circuit1.transmissionlines.keys()))  # Expected output: ["Line1"]
