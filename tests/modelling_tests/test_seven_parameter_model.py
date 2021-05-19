import logging
import math
import unittest

import pandas
from scipy.optimize import leastsq
import matplotlib.pyplot as plt
import sympy as sp

from config.config import resource_file_path
from data_processing.data_processing import load_data
from models.plant_models.four_parameters_model.best_parameters import four_param_model_params
from models.plant_models.model_functions import construct_residual, run_experiment_four_parameter_model, \
    run_experiment_two_parameter_model, run_experiment_seven_parameter_model
from models.plant_models.seven_parameters_model.best_parameters import seven_param_model_params
from tests.cli_mode_test import CLIModeTest
from visualization.data_plotting import plotly_incubator_data, show_plotly


class SevenParameterModelTests(CLIModeTest):

    def test_run_experiment_seven_parameter_model(self):
        time_unit = 'ns'
        # CWD: Example_Digital-Twin_Incubator\software\
        data = load_data("./datasets/lid_opening_experiment_mar_2021/lid_opening_experiment_mar_2021.csv",
                         events_path="./datasets/lid_opening_experiment_mar_2021/events.csv",
                         desired_timeframe=(- math.inf, math.inf),
                         time_unit=time_unit,
                         normalize_time=False,
                         convert_to_seconds=True)
        params = seven_param_model_params

        results, sol = run_experiment_seven_parameter_model(data, params)

        if self.ide_mode():
            print(f"Experiment time from {data.iloc[0]['timestamp']} to {data.iloc[-1]['timestamp']}")

        fig = plotly_incubator_data(data,
                                    compare_to={
                                        "T(4)": {
                                            "timestamp": pandas.to_datetime(results.signals["time"], unit='s'),
                                            "T": results.signals["T"],
                                            "T_object": results.signals["T_object"],
                                        }
                                    },
                                    events=events,
                                    overlay_heater=True,
                                    # show_sensor_temperatures=True,
                                    show_hr_time=True
                                    )

        if self.ide_mode():
            show_plotly(fig)


if __name__ == '__main__':
    unittest.main()
