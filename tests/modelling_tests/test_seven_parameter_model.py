import logging
import math
import unittest
from copy import copy

import numpy as np
import pandas
from scipy.optimize import leastsq, least_squares

from data_processing.data_processing import load_data, derive_data
from models.plant_models.model_functions import run_experiment_seven_parameter_model, construct_residual
from models.plant_models.seven_parameters_model.best_parameters import seven_param_model_params
from tests.cli_mode_test import CLIModeTest
from visualization.data_plotting import plotly_incubator_data, show_plotly


class SevenParameterModelTests(CLIModeTest):

    def test_calibrate_seven_parameter_model(self):

        NEvals = 100 if self.ide_mode() else 1
        logging.basicConfig(level=logging.INFO)

        desired_timeframe = (-math.inf, 1614867211000000000-1)
        time_unit = 'ns'
        convert_to_seconds = True

        h = 3.0

        data, events = load_data("./datasets/lid_opening_experiment_mar_2021/lid_opening_experiment_mar_2021.csv",
                                 events="./datasets/lid_opening_experiment_mar_2021/events.csv",
                                 desired_timeframe=desired_timeframe, time_unit=time_unit,
                                 normalize_time=False,
                                 convert_to_seconds=convert_to_seconds)

        T_heater_0 = data.iloc[0]["average_temperature"]

        def run_exp(params):
            m, sol = run_experiment_seven_parameter_model(data, params, T_heater_0, h=h)
            return m, sol, data

        residual = construct_residual([run_exp])
        sol = least_squares(residual, np.array(seven_param_model_params), max_nfev=NEvals)

        print(f"Cost: {sol.cost}")
        print(f"Params: {sol.x}")


    def test_calibrate_seven_parameter_model_stages(self):

        NEvals = 50 if self.ide_mode() else 1
        logging.basicConfig(level=logging.INFO)

        NStages = 8

        desired_timeframe = (-math.inf, math.inf)
        time_unit = 'ns'
        convert_to_seconds = True

        h = 3.0

        data, events = load_data("./datasets/lid_opening_experiment_mar_2021/lid_opening_experiment_mar_2021.csv",
                                 events="./datasets/lid_opening_experiment_mar_2021/events.csv",
                                 desired_timeframe=desired_timeframe, time_unit=time_unit,
                                 normalize_time=False,
                                 convert_to_seconds=convert_to_seconds)

        # Isolate sections where the calibration will be run.
        stages = []
        next_stage_start = 0
        next_stage_end = 0
        next_stage_lid_open = False
        for idx, row in data.iterrows():
            start_new_stage = ((not next_stage_lid_open) and row["lid_open"] > 0.5) or \
                              (next_stage_lid_open and row["lid_open"] < 0.5)
            if start_new_stage:
                stages.append((next_stage_lid_open, next_stage_start, next_stage_end))
                next_stage_start = next_stage_end + 1
                next_stage_end = next_stage_start
                next_stage_lid_open = row["lid_open"] > 0.5
            else:
                next_stage_end += 1

        # Run calibration for each section sequentially.
        experiments = []
        for i in range(min(NStages, len(stages))):
            (lid_open, start, end) = stages[i]
            if i == 0:
                T_heater_0 = data.iloc[0]["average_temperature"]
                last_params = seven_param_model_params
            else:
                # Run last experiment and get T_heater final.
                (last_data_stage, last_params, last_T_heater_0) = experiments[-1]
                m, sol = run_experiment_seven_parameter_model(last_data_stage, last_params, last_T_heater_0, h=h)
                T_heater_0 = m.signals["T_heater"][-1]

            # Filter data to range
            data_stage = data.iloc[range(start, end)]

            # Get best parameters so far from the experiment
            params = copy(last_params)

            if lid_open:
                def run_exp_lid(param_lid):
                    params[6] = param_lid[0]
                    m, sol = run_experiment_seven_parameter_model(data_stage, params, T_heater_0, h=h)
                    return m, sol, data_stage

                residual = construct_residual([run_exp_lid])
                sol = least_squares(residual, np.array([params[6]]), max_nfev=NEvals)

                params[6] = sol.x[0]

                print(f"Calibration for stage {i} with lid open done.")
            else:
                def run_exp_nolid(params_nolid):
                    params[0] = params_nolid[0]
                    params[1] = params_nolid[1]
                    params[2] = params_nolid[2]
                    params[3] = params_nolid[3]
                    m, sol = run_experiment_seven_parameter_model(data_stage, params, T_heater_0, h=h)
                    return m, sol, data_stage

                residual = construct_residual([run_exp_nolid])
                sol = least_squares(residual, np.array([params[i] for i in range(4)]), max_nfev=NEvals)

                params[0] = sol.x[0]
                params[1] = sol.x[1]
                params[2] = sol.x[2]
                params[3] = sol.x[3]

                print(f"Calibration for stage {i} with no lid open done.")

            print(f"Cost: {sol.cost}")
            print(f"Params: {sol.x}")

            experiments.append((data_stage, params, T_heater_0))

        print(f"Calibration done. Final results:")
        (_, last_params, _) = experiments[-1]
        print(last_params)


    def test_run_experiment_seven_parameter_model(self):
        time_unit = 'ns'

        tf = 1614867211000000000-1
        # tf = math.inf

        # CWD: Example_Digital-Twin_Incubator\software\
        data, events = load_data("./datasets/lid_opening_experiment_mar_2021/lid_opening_experiment_mar_2021.csv",
                                 events="./datasets/lid_opening_experiment_mar_2021/events.csv",
                                 desired_timeframe=(-math.inf, tf),
                                 time_unit=time_unit,
                                 normalize_time=False,
                                 convert_to_seconds=True)
        params = seven_param_model_params

        results, sol = run_experiment_seven_parameter_model(data, params, initial_heat_temperature=data.iloc[0]["average_temperature"])

        if self.ide_mode():
            print(f"Experiment time from {data.iloc[0]['timestamp']} to {data.iloc[-1]['timestamp']}")

        fig = plotly_incubator_data(data,
                                    compare_to={
                                        "T(4)": {
                                            "timestamp": pandas.to_datetime(results.signals["time"], unit='s'),
                                            "T": results.signals["T"],
                                            # "T_object": results.signals["T_object"],
                                            "in_lid_open": results.signals["in_lid_open"],
                                        }
                                    },
                                    events=events,
                                    overlay_heater=True,
                                    show_actuators=True,
                                    show_hr_time=True
                                    )

        if self.ide_mode():
            show_plotly(fig)


if __name__ == '__main__':
    unittest.main()
