import numpy as np
import pandas as pd
from Circuit import Circuit
from SystemSettings import SystemSettings


class Solution:

    def __init__(self, circuit: Circuit):
        self.circuit = circuit
        self.ybus = circuit.calc_ybus() # Ybus from Circuit
        self.voltages, self.angles = self.get_voltages()  # voltage & angles in p.u. and radians
        self.zbus_pos = circuit.zbus_pos
        self.zbus_neg = circuit.zbus_neg
        self.zbus_zero = circuit.zbus_zero

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

    def newton_raphson(self, tolerance=0.001, max_iterations=50):
        for i in range(max_iterations):
            print(f"\nIteration {i + 1}:")

            # Step 1: compute mismatches
            mismatches = self.compute_power_mismatch()
            max_mismatch = np.max(np.abs(mismatches))

            print(f"\nMax mismatch = {max_mismatch:.6f}")

            # Step 2: compute Jacobian
            from Jacobian import Jacobian
            J = Jacobian(self).calc_jacobian()


            # Step 3: solve for Δx
            try:
                delta_x = np.linalg.solve(J, mismatches)
            except np.linalg.LinAlgError:
                print("The Jacobian is singular, cannot solve")
                return False

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

                print("\nFinal Power Mismatch:")
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

                # Extract the bus lists needed for labeling
                bus_list = list(self.circuit.buses.keys())
                pv_pq_buses = [b for b in bus_list if self.circuit.buses[b].bus_type in ["PV Bus", "PQ Bus"]]
                pq_buses = [b for b in bus_list if self.circuit.buses[b].bus_type == "PQ Bus"]

                # Create row and column labels
                row_labels = []
                for bus in pv_pq_buses:
                    row_labels.append(f"∂P {bus}")
                for bus in pq_buses:
                    row_labels.append(f"∂Q {bus}")

                col_labels = []
                for bus in pv_pq_buses:
                    col_labels.append(f"∂δ {bus}")
                for bus in pq_buses:
                    col_labels.append(f"∂V {bus}")

                # Calculate max width for row labels
                row_width = max(len(label) for label in row_labels) + 1
                col_width = 12

                print(" " * row_width, end="")
                for col in col_labels:
                    print(f"{col:^{col_width}}", end="")
                print()

                for i, row_label in enumerate(row_labels):
                    print(f"{row_label:{row_width}}", end="")
                    for j in range(J.shape[1]):
                        print(f"{J[i, j]:^{col_width}.6f}", end="")
                    print()

                return True


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

    def power_flow(self, tolerance=0.001, max_iterations=50):
        return self.newton_raphson(tolerance=tolerance, max_iterations=max_iterations)

    def fault_study(self):
        print("\nFAULT ANALYSIS")
        print("=" * 60)

        # Ensure latest Ybus and Zbus matrices are calculated
        self.circuit.ybus = self.circuit.calc_ybus()
        self.circuit.ybus_pos = self.circuit.calc_ybus_pos_sequence()
        self.circuit.ybus_neg = self.circuit.calc_ybus_neg_sequence()
        self.circuit.ybus_zero = self.circuit.calc_ybus_zero_sequence()
        self.circuit.zbus_pos, self.circuit.zbus_neg, self.circuit.zbus_zero = self.circuit.calc_sequence_zbuses()

        # Update the references in the Solution object
        self.ybus = self.circuit.ybus
        self.zbus_pos = self.circuit.zbus_pos
        self.zbus_neg = self.circuit.zbus_neg
        self.zbus_zero = self.circuit.zbus_zero

        print("Select fault type:")
        print("1. Three-phase fault")
        print("2. Line-to-ground fault")
        print("3. Line-to-line fault")
        print("4. Double-line-to-ground fault")

        fault_type = input("Enter choice (1-4): ")
        print("Available buses:", list(self.circuit.buses.keys()))
        fault_bus = input("Enter the bus name where the fault occurs: ").strip()

        if fault_bus not in self.circuit.buses:
            print(f"Bus '{fault_bus}' not found in the system.")
            return

        v_prefault = 1.0  # assume 1.0 p.u. prefault voltage
        Zf = 0 + 0j # assume a bolted fault

        if fault_type == "1":
            self.perform_symmetrical_fault(fault_bus, v_prefault)
        elif fault_type == "2":
            self.perform_lg_fault(fault_bus, v_prefault, Zf)
        elif fault_type == "3":
            self.perform_ll_fault(fault_bus, v_prefault, Zf)
        elif fault_type == "4":
            self.perform_llg_fault(fault_bus, v_prefault, Zf)
        else:
            print("Invalid choice.")

    def perform_symmetrical_fault(self, bus, v_prefault):
        print("\n>>> Performing symmetrical 3-phase fault analysis")

        if bus not in self.zbus_pos.keys():
            raise ValueError(f"Fault bus {bus} not found in Zbus.")

        Znn = self.zbus_pos.loc[bus, bus]
        if Znn == 0:
            raise ZeroDivisionError("Znn is zero, can't compute fault current.")

        If = v_prefault / Znn

        print(f"\nSubtransient fault current at {bus}: "
              f"{abs(If):.4f} ∠{np.angle(If, deg=True):.2f}° (in p.u.)")

        voltages_after_fault = {}
        for bus_k in self.zbus_pos.index:
            Zkn = self.zbus_pos.loc[bus_k, bus]
            Vk = (1 - Zkn/Znn) * v_prefault
            voltages_after_fault[bus_k] = Vk
            print(f"Post-fault voltage at {bus_k}: {abs(Vk):.4f} ∠{np.angle(Vk, deg=True):.2f}° (in p.u.)")

    def perform_lg_fault(self, bus, v_prefault, Zf):
        print("\n>>> Performing line‑to‑ground (LG) fault analysis")

        # Z self‑impedances of the faulted bus
        Z1_nn = self.zbus_pos.loc[bus, bus]
        Z2_nn = self.zbus_neg.loc[bus, bus]
        Z0_nn = self.zbus_zero.loc[bus, bus]

        # Total fault impedance (including fault impedance Zf)
        Z_total = Z1_nn + Z2_nn + Z0_nn + 3 * Zf

        # Fault current and sequence currents (with fault impedance Zf included)
        I1 = I2 = I0  = v_prefault / Z_total
        If = I1 + I2 + I0
        print(f"\nSubtransient fault current at {bus}: {abs(If):.4f} ∠{np.angle(If, deg=True):.2f}° (in p.u.)")

        V_post = {}  # Total phase‑to‑neutral voltages after the fault
        V1_bus = {}
        V2_bus = {}
        V0_bus = {}

        # Perform symmetrical component transformation for each bus
        for k in self.circuit.buses:  # Iterate through each bus in the network
            # Z of the faulted bus
            Z1_kn = self.zbus_pos.loc[k, bus]
            Z2_kn = self.zbus_neg.loc[k, bus]
            Z0_kn = self.zbus_zero.loc[k, bus]

            # Calculate sequence voltage contributions
            V1_k = v_prefault - Z1_kn * I1
            V2_k = -Z2_kn * I2
            V0_k = -Z0_kn * I0

            V1_bus[k] = V1_k
            V2_bus[k] = V2_k
            V0_bus[k] = V0_k
            Vk = V0_k + V1_k + V2_k  # Phase voltage

            V_post[k] = Vk

            # Printing phase-to-neutral voltages (magnitude and phase angle)
            print(f"Post-fault voltage at {k}: {abs(Vk):.4f} ∠{np.angle(Vk, deg=True):.2f}° (in p.u.)")



    def perform_ll_fault(self, bus, v_prefault, Zf):
        print("\n>>> Performing line‑to‑line fault analysis")

        # Impedances of the faulted bus (Z1nn, Z2nn)
        z1_nn = self.zbus_pos.loc[bus, bus]  # Z1nn
        z2_nn = self.zbus_neg.loc[bus, bus]  # Z2nn

        # Total fault impedance (including fault impedance Zf)
        Z_total = z1_nn + z2_nn + Zf

        # Fault current calculation
        I1 = v_prefault / Z_total  # Sequence current
        I2 = -I1
        I0 = 0
        If = np.sqrt(3) * I1  # Line current

        print(f"\nSubtransient fault current at {bus}: {abs(If):.4f} ∠{np.angle(If, deg=True):.2f}° (in p.u.)")

        V_post = {}  # Phase-A voltages after the fault

        for k in self.circuit.buses:  # Iterate over bus names
            Z1_kn = self.zbus_pos.loc[k, bus]  # Z1kn
            Z2_kn = self.zbus_neg.loc[k, bus]  # Z2kn
            Z0_nn = self.zbus_zero.loc[k, bus]   # Z0kn

            # Sequence voltage contributions
            V1_k = v_prefault - I1 * Z1_kn
            V2_k = -I2 * Z2_kn
            V0_k = -I0 * Z0_nn  # Zero sequence is 0 for LL fault

            Vk = V0_k + V1_k + V2_k
            V_post[k] = Vk

            # Printing phase-to-neutral voltages
            print(f"Post-fault voltage at {k}: {abs(Vk):.4f} ∠{np.angle(Vk, deg=True):.2f}° (in p.u.)")


    def perform_llg_fault(self, bus, v_prefault, Zf):
        print("\n>>> Performing double line-to-ground (LLG) fault analysis")

        # Self-impedances at the faulted bus
        Z1_nn = self.zbus_pos.loc[bus, bus]
        Z2_nn = self.zbus_neg.loc[bus, bus]
        Z0_nn = self.zbus_zero.loc[bus, bus]

        # Total impedance for the fault (including fault impedance Zf)
        Z_total1 = Z1_nn + ((Z2_nn * (Z0_nn + 3 * Zf)) / (Z2_nn + Z0_nn + 3 * Zf))
        Z_total2 = (Z0_nn + 3 * Zf) / (Z2_nn + Z0_nn + 3 * Zf)
        Z_total0 = (Z2_nn) / (Z2_nn + Z0_nn + 3 * Zf)

        # Positive sequence fault current
        I1 = v_prefault / Z_total1
        I2 = -1 * I1 * Z_total2
        I0 = -1 * I1 * Z_total0

        If = np.sqrt(3) * I1

        print(f"\nSubtransient fault current at {bus}: {abs(If):.4f} ∠{np.angle(If, deg=True):.2f}° (in p.u.)")

        V_post = {}
        V0_bus = {}
        V1_bus = {}
        V2_bus = {}

        for k in self.circuit.buses:
            Z1_kn = self.zbus_pos.loc[k, bus]
            Z2_kn = self.zbus_neg.loc[k, bus]
            Z0_kn = self.zbus_zero.loc[k, bus]

            # Sequence voltage contributions
            V1_k = v_prefault - I1 * Z1_kn
            V2_k = -I2 * Z2_kn
            V0_k = -I0 * Z0_kn

            V0_bus[k] = V0_k
            V1_bus[k] = V1_k
            V2_bus[k] = V2_k

            Vk = V0_k + V1_k + V2_k
            V_post[k] = Vk

            # Printing phase-to-neutral voltages
            print(f"Post-fault voltage at {k}: {abs(Vk):.4f} ∠{np.angle(Vk, deg=True):.2f}° (in p.u.)")


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
    circuit1.add_transformer("T1", "Bus1", "Bus2", 125, 8.5, 10, "y-y", 0.05)
    circuit1.add_transformer("T2", "Bus6", "Bus7", 200, 10.5, 12, "y-y", 0.05)

    # ADD GENERATORS
    circuit1.add_generator("G1", "Bus1", 20, 100, 0.05, True)
    circuit1.add_generator("G2", "Bus7", 18, 200, 0.05, True)

    # ADD LOAD
    circuit1.add_load("L1", "Bus3", 110, 50)
    circuit1.add_load("L2", "Bus4", 100, 70)
    circuit1.add_load("L3", "Bus5", 100, 65)

    print(f"Bus1 type: {circuit1.buses['Bus1'].bus_type}")  # Should print "Slack Bus"
    print(f"Bus2 type: {circuit1.buses['Bus2'].bus_type}")  # Should print "PQ Bus"
    print(f"Bus7 type: {circuit1.buses['Bus7'].bus_type}")  # Should print "PV Bus"


    solution = Solution(circuit1)

    solution.power_flow()

    solution.fault_study()




