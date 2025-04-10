import numpy as np
from Circuit import Circuit
from SystemSettings import SystemSettings
from Generator import Generator

class Solution:

    def __init__(self, circuit: Circuit, mode="power_flow"):
        self.circuit = circuit
        self.mode = mode.lower()
        self.ybus = self.circuit.calc_ybus()
        self.zbus = self.circuit.calc_zbus()
        self.voltages, self.angles = self.get_voltages()

    def get_voltages(self):
        voltages = {}
        angles = {}

        for bus_name, bus in self.circuit.buses.items():
            voltages[bus_name] = bus.vpu  # start with 1.0 per-unit
            angles[bus_name] = bus.delta  # assume flat start

        return voltages, angles

    def run(self):
        if self.mode == "power_flow":
            return self.newton_raphson()
        elif self.mode == "fault_study":
            return self.fault_study()
        else:
            raise ValueError("Unknown mode. Choose 'power_flow' or 'fault_study'.")

    def fault_study(self, prefault_voltage=1.0):
        print("\nRunning symmetrical fault analysis...")

        # Identify all buses that are faulted
        fault_buses = [bus.name for bus in self.circuit.buses.values() if hasattr(bus, 'fault') and bus.fault]
        if not fault_buses:
            print("No faulted buses detected in the system.")
            return False

        for fault_bus_name in fault_buses:
            print(f"\nDetected fault at: {fault_bus_name}")

            ybus_faulted = self.ybus
            zbus = self.zbus

            if zbus is None:
                continue

            try:
                bus_index = list(zbus.index).index(fault_bus_name)
                z_fault = zbus.iloc[bus_index, bus_index]
                ifault = prefault_voltage / z_fault

                print(f"Fault Current at {fault_bus_name}: {abs(ifault):.4f} pu ∠{np.angle(ifault, deg=True):.2f}°")

                print("Bus Voltages during Fault:")
                for i, bus in enumerate(zbus.columns):
                    v_faulted = prefault_voltage - zbus.iloc[i, bus_index] * ifault
                    mag = abs(v_faulted)
                    angle = np.angle(v_faulted, deg=True)
                    print(f"{bus}: {mag:.4f} pu ∠{angle:.2f}°")

            except ValueError:
                print(f"Bus {fault_bus_name} not found in Zbus matrix.")
                continue

        return True
    # def fault_study(self, fault_bus_name="Bus1", prefault_voltage=1.0):
    #     print("\nRunning symmetrical fault analysis...")
    #
    #     # ybus_faulted = self.circuit.calc_ybus()
    #     zbus = self.circuit.calc_zbus()
    #
    #     if zbus is None:
    #         return False
    #
    #     bus_index = list(zbus.index).index(fault_bus_name)
    #     z_fault = zbus.iloc[bus_index, bus_index]
    #     ifault = prefault_voltage / z_fault
    #
    #     print(f"Fault Current at {fault_bus_name}: {abs(ifault):.4f} pu ∠{np.angle(ifault, deg=True):.2f}°")
    #
    #     print("\nBus Voltages during Fault:")
    #     for i, bus in enumerate(zbus.columns):
    #         v_faulted = prefault_voltage - zbus.iloc[i, bus_index] * ifault
    #         mag = abs(v_faulted)
    #         angle = np.angle(v_faulted, deg=True)
    #         print(f"{bus}: {mag:.4f} pu ∠{angle:.2f}°")
    #
    #     return True

    def newton_raphson(self, tolerance=0.001, max_iterations=50):
        for i in range(max_iterations):
            print(f"\nIteration {i + 1}:")

            # Step 1: compute mismatches
            mismatches = self.compute_power_mismatch()
            max_mismatch = np.max(np.abs(mismatches))

            print(f"\nMax mismatch = {max_mismatch:.6f}")


            if max_mismatch < tolerance:
                print("\nConverged!")

                print("\nNEWTON-RAPHSON SOLUTION SUMMARY")
                print("=" * 60)
                print(f"\nConverged in {i+1} iterations")

                print("\nFinal Bus Angles (radians):")
                for bus_name in self.circuit.buses:
                    print(f"{bus_name}: {self.angles[bus_name]:.6f} rad")

                print("\nFinal Bus Voltages (p.u.):")
                for bus_name in self.circuit.buses:
                    print(f"{bus_name}: {self.voltages[bus_name]:.6f} p.u.")

                print("\nPower Mismatch Results:")

                bus_list = list(self.circuit.buses.keys())
                p_index = 0
                q_index = len(
                    [b for b in self.circuit.buses.values() if b.bus_type != "Slack Bus"])  # start of Q mismatches

                for bus_name in bus_list:
                    bus = self.circuit.buses[bus_name]
                    if bus.bus_type == "Slack Bus":
                        continue

                    print(f"{bus_name}: ΔP = {mismatches[p_index]:.4f}")
                    p_index += 1

                for bus_name in bus_list:
                    bus = self.circuit.buses[bus_name]
                    if bus.bus_type == "PQ Bus":
                        print(f"{bus_name}: ΔQ = {mismatches[q_index]:.4f}")
                        q_index += 1

                print("\nFinal Jacobian Matrix:")
                for i_row in range(J.shape[0]):
                    for j_col in range(J.shape[1]):
                        print(f"{J[i_row, j_col]:>12.6f}", end="")
                    print()

                return True

            # Step 2: compute Jacobian
            from Jacobian import Jacobian
            J = Jacobian(self).calc_jacobian()


            # Step 3: solve for Δx
            try:
                delta_x = np.linalg.solve(J, mismatches)
            except np.linalg.LinAlgError:
                print("The Jacobian is singular, cannot solve")
                return False

            # Step 4: update x(i+1) = x(i) + Δx
            idx = 0

            # update all angles for PV and PQ buses
            for bus_name, bus in self.circuit.buses.items():
                if bus.bus_type != "Slack Bus":  # Update angles for PV and PQ buses
                    self.angles[bus_name] += delta_x[idx]
                    idx += 1

            # update voltages for PQ buses only
            for bus_name, bus in self.circuit.buses.items():
                if bus.bus_type == "PQ Bus":  # Update voltages only for PQ buses
                    self.voltages[bus_name] += delta_x[idx]
                    idx += 1

        print("Max iterations reached without convergence.")
        return False

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

                    # compute power injections
                    pk += vk * vj * abs(ykj) * np.cos(delta_k - delta_j - theta_kj)
                    qk += vk * vj * abs(ykj) * np.sin(delta_k - delta_j - theta_kj)

            P[i] = pk  # store computed real power injection
            Q[i] = qk  # store computed reactive power injection

        return P, Q

    def compute_power_mismatch(self):
        P_calc, Q_calc = self.compute_power_injection()
        bus_list = list(self.circuit.buses.keys())

        # create mappings from bus name to index
        bus_index = {name: idx for idx, name in enumerate(bus_list)}

        # first compute ΔP for all non-slack buses
        delta_p = []
        for bus_name in bus_list:
            bus = self.circuit.buses[bus_name]
            if bus.bus_type == "Slack Bus":
                continue

            p_specified = 0
            for gen in self.circuit.generators.values():
                if gen.bus.name == bus_name:
                    p_specified += gen.mw_setpoint / SystemSettings.Sbase

            for load in self.circuit.loads.values():
                if load.bus == bus_name:
                    p_specified -= load.real_power / SystemSettings.Sbase

            i = bus_index[bus_name]
            delta_p.append(p_specified - P_calc[i])

        # then compute ΔQ for only PQ buses
        delta_q = []
        for bus_name in bus_list:
            bus = self.circuit.buses[bus_name]
            if bus.bus_type != "PQ Bus":
                continue

            q_specified = 0
            for gen in self.circuit.generators.values():
                if gen.bus.name == bus_name and hasattr(gen, 'mvar_setpoint'):
                    q_specified += gen.mvar_setpoint / SystemSettings.Sbase

            for load in self.circuit.loads.values():
                if load.bus == bus_name:
                    q_specified -= load.reactive_power / SystemSettings.Sbase

            i = bus_index[bus_name]
            delta_q.append(q_specified - Q_calc[i])

        # return full mismatch vector
        return np.array(delta_p + delta_q)


if __name__ == "__main__":
    circuit1 = Circuit("Test Circuit")

    circuit1.add_bus("Bus1", 20)
    circuit1.add_bus("Bus2", 230)
    circuit1.add_bus("Bus3", 230)
    circuit1.add_bus("Bus4", 230)
    circuit1.add_bus("Bus5", 230)
    circuit1.add_bus("Bus6", 230)
    circuit1.add_bus("Bus7", 18)

    circuit1.add_conductor("Partridge", 0.642, 0.0217, 0.385, 460)
    circuit1.add_bundle("Bundle1", 2, 1.5, "Partridge")
    circuit1.add_geometry("Geometry1", 0, 0, 18.5, 0, 37, 0)

    circuit1.add_tline("Line1", "Bus2", "Bus4", "Bundle1", "Geometry1", 10)
    circuit1.add_tline("Line2", "Bus2", "Bus3", "Bundle1", "Geometry1", 25)
    circuit1.add_tline("Line3", "Bus3", "Bus5", "Bundle1", "Geometry1", 20)
    circuit1.add_tline("Line4", "Bus4", "Bus6", "Bundle1", "Geometry1", 20)
    circuit1.add_tline("Line5", "Bus5", "Bus6", "Bundle1", "Geometry1", 10)
    circuit1.add_tline("Line6", "Bus4", "Bus5", "Bundle1", "Geometry1", 35)

    circuit1.add_transformer("T1", "Bus1", "Bus2", 125, 8.5, 10)
    circuit1.add_transformer("T2", "Bus6", "Bus7", 200, 10.5, 12)

    circuit1.add_generator("G1", "Bus1", 20, 100, grounding="solid")
    circuit1.add_generator("G2", "Bus7", 18, 200, grounding="resistance", rg=1.0)

    circuit1.add_load("L1", "Bus3", 110, 50)
    circuit1.add_load("L2", "Bus4", 100, 70)
    circuit1.add_load("L3", "Bus5", 100, 65)

    circuit1.calc_ybus()

    print("\n--- POWER FLOW ANALYSIS ---")
    solution_pf = Solution(circuit1, mode="power_flow")
    solution_pf.run()

    print("\n--- FAULT STUDY ANALYSIS ---")
    solution_fault = Solution(circuit1, mode="fault_study")
    solution_fault.run()

