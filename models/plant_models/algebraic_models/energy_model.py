from oomodelling import Model


class EnergyModel(Model):
    def __init__(self,
                 C_air=700,  # j kg^-1 °K^-1
                 Volume = 0.03,  # m^3
                 T0 = 20.0  # °C
                 ):
        super().__init__()

        self.C = self.parameter(C_air)

        self.Volume = self.parameter(Volume)

        self.Vol_per_Weight = self.parameter(0.04 / 0.03)

        self.Mass = self.parameter(self.Vol_per_Weight * self.Volume)  # (Kg)

        self.T0 = self.parameter(T0)  # °C

        self.T0_k = self.var(lambda: T0 / (5.0 / 9.0) + 32.0)  # °F

        self.power = self.input(lambda: 100)  # J s^-1

        self.energy = self.state(Volume * self.T0_k() * self.C)  # J

        self.T_k = self.var(lambda: self.energy() / (self.Volume * self.C))

        self.T = self.var(lambda: (self.T_k() - 32.0) * (5.0 / 9.0) )

        self.der('energy', lambda: self.power())

        self.save()
