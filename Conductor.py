# Group 8 - Project 2
# ECE 2774
# Milestone 1

class Conductor:

        def __init__(self, name: str, diam: float, gmr: float, resistance: float , ampacity: float):
            self.name = name
            self.diam = diam  # conductor diameter in INCHES
            self.gmr = gmr # geometric mean radius in FEET
            self.resistance = resistance  # resistance per unit length (using miles for this)
            self.ampacity = ampacity  # max current-carrying capacity


if __name__ == "__main__":
    conductor1 = Conductor("Partridge", 0.642, 0.0217, 0.385, 460)

    # print attributes
    print(conductor1.name, conductor1.diam, conductor1.gmr, conductor1.resistance, conductor1.ampacity)
