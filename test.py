if __name__ == "__main__":


    from Circuit import Circuit

    circuit1 = Circuit("Test Circuit")

    # ADD BUSES
    circuit1.add_bus("Bus1", 230)
    circuit1.add_bus("Bus2", 230)
    circuit1.add_bus("Bus3", 18)

    # ADD TRANSMISSION LINE
    circuit1.add_conductor("Partridge", 0.642, 0.0217, 0.385, 460)
    circuit1.add_bundle("Bundle1", 2, 1.5, "Partridge")
    circuit1.add_geometry("Geometry1", 0, 0, 18.5, 0, 37, 0)

    circuit1.add_tline("Line1", "Bus1", "Bus2", "Bundle1", "Geometry1", 10)

    # ADD TRANSMORMER
    circuit1.add_transformer("T1", "Bus2", "Bus3", 200, 10.5, 12, "delta-y", 1)

    # Build circuit

    # Calculate Ybus
    ybus = circuit1.calc_ybus()
    print("Ybus Matrix:")
    print(ybus)