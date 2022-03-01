import numpy as np
from scipy.optimize import minimize

from calibration.calibrator_database import CalibratorDatabase
from digital_twin.simulator.plant_simulator import PlantSimulator4Params


def compute_error(tracked_solutions, new_state_trajectories):
    assert len(tracked_solutions) == len(new_state_trajectories), "Solutions and state trajectories appear consistent."
    sum = 0
    for (sol, actual) in zip(tracked_solutions, new_state_trajectories):
        sum += ((sol - actual) ** 2).sum()
    return sum


class Calibrator:
    def __init__(self, database: CalibratorDatabase, plant_simulator: PlantSimulator4Params, conv_xatol, conv_fatol, max_iterations):
        self.database = database
        self.plant_simulator = plant_simulator
        self.conv_xatol = conv_xatol
        self.conv_fatol = conv_fatol
        self.max_iterations = max_iterations

    def calibrate(self, t_start, t_end):
        times = self.database.get_time(t_start, t_end)
        reference_T = self.database.get_T(t_start, t_end)
        ctrl_signal = self.database.get_HeaterOn(t_start, t_end)
        reference_T_heater = self.database.get_T_heater(t_start, t_end)
        room_T = self.database.get_room_temperature(t_start, t_end)
        assert len(reference_T) == len(reference_T_heater) == len(times)

        tracked_solutions = [reference_T, reference_T_heater]

        C_air, G_box, C_heater, G_heater = self.database.get_plant4_parameters()

        def cost(p):
            C_air, G_box = p
            new_trajs = self.plant_simulator.run_simulation(times, reference_T[0], reference_T_heater[0], room_T, ctrl_signal,
                                                            C_air, G_box, C_heater, G_heater)
            error = compute_error(tracked_solutions, new_trajs)
            return error

        new_sol = minimize(cost, np.array([C_air, G_box]), method='Nelder-Mead',
                           options={'xatol': self.conv_xatol, 'fatol': self.conv_fatol, 'maxiter': self.max_iterations})

        assert new_sol.success, new_sol.message

        if new_sol.success:
            C_air_new, G_box_new = new_sol.x
            calibrated_sol = self.plant_simulator.run_simulation(times, reference_T[0], reference_T_heater[0], ctrl_signal,
                                                                 C_air_new, G_box_new, C_heater, G_heater)

            self.database.store_calibrated_trajectory(times, calibrated_sol)
            self.database.update_parameters(C_air_new, G_box_new, C_heater, G_heater)
            return True, C_air_new, G_box_new, C_heater, G_heater
        else:
            return False, C_air, G_box, C_heater, G_heater
