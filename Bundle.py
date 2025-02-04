# Cece Espadas
# 1-30-25
# ECE 2774: Project 2
# Bundle Subclass

import math as math
from Conductor import Conductor

class Bundle:

        def __init__(self, name: str, num_conductors: float, spacing: float, conductor: Conductor):
            self.name = name
            self.num_conductors = num_conductors
            self.spacing = spacing
            self.conductor = conductor
            self.dsc =  self.calc_dsc() # DSC will be calculated
            self.dsl = self.calc_dsl() # DSL will be calculated


        def calc_dsl(self):
            N = self.num_conductors
            d = self.spacing
            GMR_c = self.conductor.gmr

            if N == 1:
                return GMR_c
            elif N == 2:
                return math.sqrt(GMR_c * d)
            elif N == 3:
                return (GMR_c * d ** 2) ** (1 / 3)
            elif N == 4:
                return 1.091 * (GMR_c * d ** 4) ** (1 / 4)
            else:
                raise ValueError("Cannot calculate DSL for N > 4")


        def calc_dsc(self):
            N = self.num_conductors
            d = self.spacing
            r_c = self.conductor.diam/(24) #radius in feet when conductor diameter is given in inches

            if N == 1:
                return r_c
            elif N == 2:
                return math.sqrt(r_c * d)
            elif N == 3:
                return (r_c * d ** 2) ** (1 / 3)
            elif N == 4:
                return 1.091 * (r_c * d ** 4) ** (1 / 4)
            else:
                raise ValueError("Cannot calculate DSC for N > 4")


if __name__ == "__main__":

    conductor1 = Conductor("Partridge", 0.642, 0.0217, 0.385, 460)

    bundle1 = Bundle("Bundle 1", 2, 1.5, conductor1)

    print(bundle1.name, bundle1.num_conductors, bundle1.spacing, bundle1.conductor.name)
    print(bundle1.dsl, bundle1.dsc)
