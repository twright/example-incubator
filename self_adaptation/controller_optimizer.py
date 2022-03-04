import numpy as np
from scipy.optimize import minimize

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
        T, T_heater, room_T = self.database.get_pt_snapshot()

        # Get system parameters
        C_air, G_box, C_heater, G_heater = self.database.get_plant4_parameters()

        time_til_steady_state = 3000  # Obtained from empirical experiments

        desired_temperature = 38

        # Get current controller parameters
        n_samples_heating, n_samples_period, controller_step_size = self.database.get_ctrl_parameters()

        # Define cost function for controller
        def cost(p):
            n_samples_heating_guess, n_samples_period_guess = p
            model = self.pt_simulator.run_simulation(time_til_steady_state, T, T_heater, room_T,
                                                     n_samples_heating_guess, n_samples_period_guess, controller_step_size,
                                                     C_air, G_box, C_heater, G_heater)
            # Error is how far from the desired temperature the simulation is, for a few seconds in steady state.
            range_for_error = np.array(model.plant.signals['T'][-100:-1])
            error = np.sum(np.power(range_for_error - desired_temperature, 2))
            return error

        # Start optimization process
        new_sol = minimize(cost, np.array([n_samples_heating, n_samples_period]), method='Nelder-Mead',
                           options={'xatol': self.conv_xatol, 'fatol': self.conv_fatol, 'maxiter': self.max_iterations})

        assert new_sol.success, new_sol.message

        if new_sol.success:
            n_samples_heating_new, n_samples_period_new = new_sol.y
            self.controller.set_new_parameters(n_samples_heating_new, n_samples_period_new)
