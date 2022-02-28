from oomodelling import Model

from models.controller_models.controller_open_loop import ControllerOpenLoop
from models.plant_models.four_parameters_model.four_parameter_model import FourParameterIncubatorPlant


class SystemModel4ParametersOpenLoop(Model):
    def __init__(self,
                 # Controller parameters
                 n_samples_period, n_samples_heating,
                 # Plant parameters
                 C_air,
                 G_box,
                 C_heater,
                 G_heater,
                 initial_box_temperature=35,
                 initial_heat_temperature=35):
        super().__init__()

        self.ctrl = ControllerOpenLoop(n_samples_period, n_samples_heating)
        self.plant = FourParameterIncubatorPlant(initial_box_temperature=initial_box_temperature,
                                                 initial_heat_temperature=initial_heat_temperature,
                                                 C_air=C_air,
                                                 G_box=G_box,
                                                 C_heater=C_heater,
                                                 G_heater=G_heater)

        self.plant.in_heater_on = self.ctrl.heater_on

        self.save()
