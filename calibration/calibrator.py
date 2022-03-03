import numpy as np
from scipy.optimize import minimize

from calibration.calibrator_database import CalibratorDatabase
from digital_twin.simulator.plant_simulator import PlantSimulator4Params


def compute_error(tracked_solutions, new_state_trajectories):
    assert len(tracked_solutions) == len(new_state_trajectories), "Solutions and state trajectories appear consistent."
    return np.sum(np.sum(np.power(tracked_solutions - new_state_trajectories, 2)))


class Calibrator:
    def __init__(self, database: CalibratorDatabase, plant_simulator: PlantSimulator4Params, conv_xatol, conv_fatol, max_iterations):
        self.database = database
        self.plant_simulator = plant_simulator
        self.conv_xatol = conv_xatol
        self.conv_fatol = conv_fatol
        self.max_iterations = max_iterations

    def calibrate(self, t_start, t_end):

        signals, t_start_idx, t_end_idx = self.database.get_signals_between(t_start, t_end)
        times = signals["time"][t_start_idx:t_end_idx]
        reference_T = signals["T"][t_start_idx:t_end_idx]
        ctrl_signal = signals["in_heater_on"][t_start_idx:t_end_idx]
        reference_T_heater = signals["T_heater"][t_start_idx:t_end_idx]
        room_T = signals["in_room_temperature"][t_start_idx:t_end_idx]
        assert len(reference_T) == len(reference_T_heater) == len(times) == len(ctrl_signal)

        tracked_solutions = np.array([reference_T, reference_T_heater])

        C_air, G_box, C_heater, G_heater = self.database.get_plant4_parameters()

        def cost(p):
            C_air, G_box = p
            new_trajs, model = self.plant_simulator.run_simulation(times, reference_T[0], reference_T_heater[0], room_T, ctrl_signal,
                                                            C_air, G_box, C_heater, G_heater)
            error = compute_error(tracked_solutions, new_trajs)
            return error

        new_sol = minimize(cost, np.array([C_air, G_box]), method='Nelder-Mead',
                           options={'xatol': self.conv_xatol, 'fatol': self.conv_fatol, 'maxiter': self.max_iterations})

        assert new_sol.success, new_sol.message

        if new_sol.success:
            C_air_new, G_box_new = new_sol.x
            calibrated_sol = self.plant_simulator.run_simulation(times, reference_T[0], reference_T_heater[0],
                                                                 room_T, ctrl_signal,
                                                                 C_air_new, G_box_new, C_heater, G_heater)

            self.database.store_calibrated_trajectory(times, calibrated_sol)
            self.database.update_parameters(C_air_new, G_box_new, C_heater, G_heater)
            return True, C_air_new, G_box_new, C_heater, G_heater
        else:
            return False, C_air, G_box, C_heater, G_heater
