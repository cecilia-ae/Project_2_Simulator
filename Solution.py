import numpy as np
from Circuit import Circuit
from SystemSettings import SystemSettings


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
            angles[bus_name] = bus.delta  # assume flat start

        return voltages, angles

    def compute_power_injection(self):
        num_buses = len(self.circuit.buses)  # total number of buses
        P = np.zeros(num_buses)  # array for real power injections
        Q = np.zeros(num_buses)  # array for reactive power injections

        bus_list = list(self.circuit.buses.keys())  # ordered list of bus names

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
        mismatches = []

        for bus_name, bus in self.circuit.buses.items():
            if bus.bus_type == "Slack Bus":
                continue  # Skip slack bus

            # calculate specified power (generation - load) in per-unit
            p_specified = 0.0
            q_specified = 0.0

            # add generation
            for gen_name, gen in self.circuit.generators.items():
                if gen.bus.name == bus_name:
                    p_specified += gen.mw_setpoint / SystemSettings.Sbase
                    if bus.bus_type == "PQ Bus" and hasattr(gen, 'mvar_setpoint'):
                        q_specified += gen.mvar_setpoint / SystemSettings.Sbase

            # subtract load
            for load_name, load in self.circuit.loads.items():
                if load.bus == bus_name:
                    p_specified -= load.real_power / SystemSettings.Sbase
                    q_specified -= load.reactive_power / SystemSettings.Sbase

            # calculate actual power using power flow equations
            p_calculated = 0.0
            q_calculated = 0.0

            v_i = self.voltages[bus_name]
            delta_i = self.angles[bus_name]

            for bus_j, y_ij in self.ybus.loc[bus_name].items():
                if bus_j in self.voltages:
                    v_j = self.voltages[bus_j]
                    delta_j = self.angles[bus_j]
                    y_magnitude = abs(y_ij)
                    theta_ij = np.angle(y_ij)

                    angle_diff = delta_i - delta_j - theta_ij

                    p_calculated += v_i * v_j * y_magnitude * np.cos(angle_diff)
                    q_calculated += v_i * v_j * y_magnitude * np.sin(angle_diff)

            # add mismatch for real power (P_specified - P_calculated)
            delta_p = p_specified - p_calculated
            mismatches.append(delta_p)

            # add mismatch for reactive power (PQ buses only)
            if bus.bus_type == "PQ Bus":
                delta_q = q_specified - q_calculated
                mismatches.append(delta_q)

        return np.array(mismatches)

    def newton_raphson(self, tolerance=0.001, max_iterations=2):
        for i in range(max_iterations):
            print(f"\nIteration {i + 1}:")

            print("\nBus Angles (radians):")
            for bus_name in self.circuit.buses:
                print(f"{bus_name}: {self.angles[bus_name]:.6f} rad")

            print("\nBus Voltages (p.u.):")
            for bus_name in self.circuit.buses:
                print(f"{bus_name}: {self.voltages[bus_name]:.6f} p.u.")

            # Step 1: compute mismatches
            mismatches = self.compute_power_mismatch()
            max_mismatch = np.max(np.abs(mismatches))

            print(f"\nMax mismatch = {max_mismatch:.6f}")
            print("Power Mismatch Results:")
            index = 0
            for bus_name, bus in self.circuit.buses.items():
                if bus.bus_type == "Slack Bus":
                    continue  # Skip Slack Bus in the mismatch vector

                print(f"{bus_name}: ΔP = {mismatches[index]:.4f}")
                index += 1
                if bus.bus_type == "PQ Bus":
                    print(f"      ΔQ = {mismatches[index]:.4f}")
                    index += 1

            if max_mismatch < tolerance:
                print("Converged!")
                return True

            # Step 2: compute Jacobian
            from Jacobian import Jacobian
            J = Jacobian(self).calc_jacobian()

            print("\nJacobian Matrix:")
            for i_row in range(J.shape[0]):
                for j_col in range(J.shape[1]):
                    print(f"{J[i_row, j_col]:>12.6f}", end="")
                print()

            # Step 3: solve for Δx
            try:
                delta_x = np.linalg.solve(J, mismatches)
            except np.linalg.LinAlgError:
                print("The Jacobian is singular, cannot solve")
                return False

            print("\nΔx Values:")
            for val_idx, val in enumerate(delta_x):
                print(f"{val:12.6f}")

            # Step 4: update x(i+1) = x(i) + Δx
            idx = 0

            # update all angles for PV and PQ buses
            for bus_name, bus in self.circuit.buses.items():
                if bus.bus_type != "Slack Bus":  # Update angles for PV and PQ buses
                    self.angles[bus_name] -= delta_x[idx]  # Note the negative sign for correct update
                    idx += 1

            # update voltages for PQ buses only
            for bus_name, bus in self.circuit.buses.items():
                if bus.bus_type == "PQ Bus":  # Update voltages only for PQ buses
                    self.voltages[bus_name] -= delta_x[idx]  # Note the negative sign
                    idx += 1

            print("\nUpdated Bus Angles (radians):")
            for bus_name in self.circuit.buses:
                print(f"{bus_name}: {self.angles[bus_name]:.6f} rad")

            print("\nUpdated Bus Voltages (p.u.):")
            for bus_name in self.circuit.buses:
                print(f"{bus_name}: {self.voltages[bus_name]:.6f} p.u.")

        print("Max iterations reached without convergence.")
        return False


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

    # ADD TRANSFORMERS
    circuit1.add_transformer("T1", "Bus1", "Bus2", 125, 8.5, 10)
    circuit1.add_transformer("T2", "Bus6", "Bus7", 200, 10.5, 12)

    # ADD GENERATORS
    circuit1.add_generator("G1", "Bus1", 20, 100)
    circuit1.add_generator("G2", "Bus7", 18, 200)

    # ADD LOAD
    circuit1.add_load("L1", "Bus3", 110, 50)
    circuit1.add_load("L2", "Bus4", 100, 70)
    circuit1.add_load("L3", "Bus5", 100, 65)

    circuit1.calc_ybus()

    print(f"Bus1 type: {circuit1.buses['Bus1'].bus_type}")  # Should print "Slack Bus"
    print(f"Bus2 type: {circuit1.buses['Bus2'].bus_type}")  # Should print "PQ Bus"
    print(f"Bus7 type: {circuit1.buses['Bus7'].bus_type}")  # Should print "PV Bus"

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

    solution.newton_raphson()
