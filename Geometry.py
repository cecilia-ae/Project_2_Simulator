# Group 8 - Project 2
# ECE 2774
# Milestone 1

import math

class Geometry:

    def __init__(self, name: str , xa: float, ya: float, xb: float, yb: float, xc: float, yc: float):
        self.name = name
        self.xa = xa
        self.ya = ya
        self.xb = xb
        self.yb = yb
        self.xc = xc
        self.yc = yc
        self.Deq = self.calc_Deq() #Deq will be calculated


    def calc_Deq(self):
        #calculate the distance between each point
        Dab = math.sqrt((self.xb - self.xa) ** 2 + (self.yb - self.ya) ** 2)
        Dca = math.sqrt((self.xa - self.xc) ** 2 + (self.ya - self.yc) ** 2)
        Dbc = math.sqrt((self.xc - self.xb) ** 2 + (self.yc - self.yb) ** 2)


        #calaculate the equivalent distance
        Deq = (Dab * Dbc * Dca)**(1/3)
        return Deq


if __name__ == "__main__":
    geometry1 = Geometry("Geometry 1", 0, 0, 18.5, 0,37, 0)

    print(geometry1.name, geometry1.xa, geometry1.ya, geometry1.xb, geometry1.yb, geometry1.xc, geometry1.yc)

    print(geometry1.Deq)