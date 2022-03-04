import numpy as np
from scipy.optimize import minimize_scalar

from interfaces.controller import IController
from interfaces.database import IDatabase
from models.physical_twin_models.system_model4_open_loop import SystemModel4ParametersOpenLoopSimulator


class ControllerOptimizer:

    def __init__(self, database: IDatabase,
                 pt_simulator: SystemModel4ParametersOpenLoopSimulator,
                 controller: IController,
                 conv_xatol, conv_fatol, max_iterations):
        self.conv_xatol = conv_xatol
        self.conv_fatol = conv_fatol
        self.max_iterations = max_iterations
        self.database = database
        self.pt_simulator = pt_simulator
        self.controller = controller

    def optimize_controller(self):
        # Get system snapshot
        T, T_heater, room_T = self.database.get_plant_snapshot()

        # Get system parameters
        C_air, G_box, C_heater, G_heater = self.database.get_plant4_parameters()

        time_til_steady_state = 3000  # Obtained from empirical experiments

        desired_temperature = 38

        # Get current controller parameters
        n_samples_heating, n_samples_period, controller_step_size = self.database.get_ctrl_parameters()

        # Define cost function for controller
        def cost(p):
            n_samples_heating_guess = round(p)

            model = self.pt_simulator.run_simulation(time_til_steady_state, T, T_heater, room_T,
                                                     n_samples_heating_guess, n_samples_period, controller_step_size,
                                                     C_air, G_box, C_heater, G_heater)
            # Error is how far from the desired temperature the simulation is, for a few seconds in steady state.
            range_for_error = np.array(model.plant.signals['T'][-100:-1])
            error = np.sum(np.power(range_for_error - desired_temperature, 2))
            return error

        # Start optimization process - The process uses braketing
        # and therefore assumes that
        # cost(n_samples_heating) < cost(max_samples_heating) and cost(n_samples_heating) < cost(0)
        # If that's not true, then it means the best controller configuration is at the extremes.
        ca = cost(0)
        cb = cost(n_samples_heating)
        cc = cost(n_samples_period)
        n_samples_heating_new = None
        if not (cb < ca and cb < cc):
            if ca < cc:
                assert ca <= cb and ca < cc
                n_samples_heating_new = 0
            else:
                assert cc <= cb and cc <= ca
                n_samples_heating_new = n_samples_period
        else:
            new_sol = minimize_scalar(cost, bracket=[0, n_samples_heating, n_samples_period],
                                      method='Brent', tol=self.conv_xatol)

            assert new_sol.success, new_sol.message

            n_samples_heating_new = new_sol.y

        if n_samples_heating_new is not None:
            self.controller.set_new_parameters(n_samples_heating_new, n_samples_period)
            self.database.update_ctrl_parameters(n_samples_heating_new, n_samples_period)
