from oomodelling import Model

from incubator.models.controller_models import ControllerModel4
from incubator.models.plant_models import TwoParameterIncubatorPlant


class SystemModel(Model):
    def __init__(self):
        super().__init__()

        self.ctrl = ControllerModel4()
        self.plant = TwoParameterIncubatorPlant()

        self.ctrl.in_temperature = self.plant.T
        self.plant.in_heater_on = self.ctrl.heater_on

        self.save()
