import unittest

from oomodelling import ModelSolver

import matplotlib.pyplot as plt

from config.config import load_config
from models.physical_twin_models.system_model4 import SystemModel4Parameters
from models.physical_twin_models.system_model4_open_loop import SystemModel4ParametersOpenLoop
from models.plant_models.four_parameters_model.best_parameters import four_param_model_params
from physical_twin.low_level_driver_server import CTRL_EXEC_INTERVAL
from visualization.data_plotting import plotly_incubator_data, show_plotly
from tests.cli_mode_test import CLIModeTest
import pandas as pd


class CosimulationTests(CLIModeTest):

    def test_run_cosim_4param_model(self):
        C_air_num = four_param_model_params[0]
        G_box_num = four_param_model_params[1]
        C_heater_num = four_param_model_params[2]
        G_heater_num = four_param_model_params[3]

        plt.figure()

        def show_trace(heating_time):
            m = SystemModel4Parameters(C_air=C_air_num,
                                       G_box=G_box_num,
                                       C_heater=C_heater_num,
                                       G_heater=G_heater_num, heating_time=heating_time, heating_gap=2.0,
                                       temperature_desired=35, initial_box_temperature=22)
            ModelSolver().simulate(m, 0.0, 3000, CTRL_EXEC_INTERVAL, CTRL_EXEC_INTERVAL/10.0)

            plt.plot(m.signals['time'], m.plant.signals['T'], label=f"Trial_{heating_time}")

        # show_trace(0.1)
        # show_trace(1.0)
        show_trace(3.0)
        # show_trace(100.0)

        plt.legend()

        if self.ide_mode():
            plt.show()

    def test_fine_tune_controller(self):
        C_air_num = four_param_model_params[0]
        G_box_num = four_param_model_params[1]
        C_heater_num = four_param_model_params[2]
        G_heater_num = four_param_model_params[3]

        m = SystemModel4Parameters(C_air=C_air_num,
                                   G_box=G_box_num,
                                   C_heater=C_heater_num,
                                   G_heater=G_heater_num, heating_time=20.0, heating_gap=30.0,
                                   temperature_desired=35, initial_box_temperature=22)
        ModelSolver().simulate(m, 0.0, 3000, CTRL_EXEC_INTERVAL, CTRL_EXEC_INTERVAL/10.0)

        # Convert cosim data into a dataframe
        data_cosim = pd.DataFrame()
        data_cosim["time"] = m.signals['time']
        data_cosim["average_temperature"] = m.plant.signals['T']
        data_cosim["t1"] = m.plant.signals['in_room_temperature']
        data_cosim["heater_on"] = m.plant.signals['in_heater_on']

        fig = plotly_incubator_data(data_cosim, overlay_heater=True)

        if self.ide_mode():
            show_plotly(fig)

    def test_run_cosim_4param_mode_open_loop(self):

        show_heater_signal = False

        config = load_config("startup.conf")
        n_samples_period = 40
        C_air = config["digital_twin"]["models"]["plant"]["param4"]["C_air"]
        G_box = config["digital_twin"]["models"]["plant"]["param4"]["G_box"]
        C_heater = config["digital_twin"]["models"]["plant"]["param4"]["C_heater"]
        G_heater = config["digital_twin"]["models"]["plant"]["param4"]["G_heater"]
        initial_box_temperature = config["digital_twin"]["models"]["plant"]["param4"]["initial_box_temperature"]
        initial_heat_temperature = config["digital_twin"]["models"]["plant"]["param4"]["initial_heat_temperature"]

        plt.figure()

        def show_trace(n_samples_heating, n_samples_period):
            m = SystemModel4ParametersOpenLoop(n_samples_period,
                                               n_samples_heating,
                                               C_air,
                                               G_box,
                                               C_heater,
                                               G_heater, initial_box_temperature,
                                               initial_heat_temperature)
            ModelSolver().simulate(m, 0.0, 6000, CTRL_EXEC_INTERVAL, CTRL_EXEC_INTERVAL/10.0)

            plt.plot(m.signals['time'], m.plant.signals['T'], label=f"NHeating_{n_samples_heating}")
            if show_heater_signal:
                plt.plot(m.signals['time'], [30 if b else 0 for b in m.ctrl.signals["heater_on"]],
                         label=f"NHeating_{n_samples_heating}")

        for n_samples_heating in range(0, 5):
            assert n_samples_heating <= n_samples_period
            show_trace(n_samples_heating, n_samples_period)

        plt.legend()

        if self.ide_mode():
            plt.show()


if __name__ == '__main__':
    unittest.main()
