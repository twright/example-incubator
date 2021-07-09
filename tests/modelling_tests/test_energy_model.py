import logging
import math
import unittest

import numpy
import numpy as np
from oomodelling import ModelSolver
from scipy.optimize import leastsq

import matplotlib.pyplot as plt

from data_processing.data_processing import load_data, derive_data
from models.plant_models.algebraic_models.energy_model import EnergyModel
from models.plant_models.model_functions import construct_residual, run_experiment_two_parameter_model
from models.plant_models.two_parameters_model.best_parameters import two_param_model_params
from physical_twin.low_level_driver_server import CTRL_EXEC_INTERVAL
from tests.cli_mode_test import CLIModeTest
import sympy as sp


class TestsModelling(CLIModeTest):

    def test_check_power_supply_enough(self):
        model = EnergyModel()
        t0 = 0.0
        tf = 4.0
        sol = ModelSolver().simulate(model, t0, tf, 0.1)

        plt.figure()

        plt.plot(model.signals["time"], model.signals["T"], label="T")
        plt.legend()

        if self.ide_mode():
            plt.show()

if __name__ == '__main__':
    unittest.main()
