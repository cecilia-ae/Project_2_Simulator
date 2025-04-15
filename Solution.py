import numpy as np
from Circuit import Circuit
from SystemSettings import SystemSettings


class Solution:

    def __init__(self, circuit: Circuit):
        self.circuit = circuit
        self.ybus = circuit.calc_ybus_pos_sequence() # Ybus from Circuit
        self.voltages, self.angles = self.get_voltages()  # voltage & angles in p.u. and radians

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
        print("\nSYMMETRICAL FAULT ANALYSIS")
        print("=" * 60)
        print("Select fault type:")
        print("1. Three-phase fault")
        print("2. Line-to-ground fault")
        print("3. Line-to-line fault")
        print("4. Double-line-to-ground fault")

        fault_type = input("Enter choice (1-4): ")

        if fault_type == "1":
            self.perform_three_phase_fault()
        elif fault_type == "2":
            self.perform_line_to_ground_fault()
        elif fault_type == "3":
            self.perform_line_to_line_fault()
        elif fault_type == "4":
            self.perform_double_line_to_ground_fault()
        else:
            print("Invalid choice. Please run again and select 1-4.")

    def perform_three_phase_fault(self):
        print(">>> Performing symmetrical 3-phase fault analysis.")

    def perform_line_to_ground_fault(self):
        print(">>> Performing line-to-ground fault analysis.")

    def perform_line_to_line_fault(self):
        print(">>> Performing line-to-line fault analysis.")

    def perform_double_line_to_ground_fault(self):
        print(">>> Performing double-line-to-ground fault analysis.")



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




