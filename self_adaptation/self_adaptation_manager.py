import numpy as np
from oomodelling import Model
from sage.all import RIF

from calibration.calibrator import Calibrator
from self_adaptation.controller_optimizer import IControllerOptimizer
from interfaces.updateable_kalman_filter import IUpdateableKalmanFilter
#from digital_twin.simulator.verified_plant_simulator import VerifiedPlantSimulator4Params


class SelfAdaptationManager:
    def __init__(self, anomaly_threshold, ensure_anomaly_timer, gather_data_timer, cool_down_timer,
                 calibrator: Calibrator,
                 kalman_filter: IUpdateableKalmanFilter,
                 controller_optimizer: IControllerOptimizer,
                 verified_monitor,
                 uncertainty_calibrator,
                 lookahead_time=0):
        assert 0 < ensure_anomaly_timer
        assert 0 < gather_data_timer
        assert 0 < anomaly_threshold
        self.current_state = "Listening"
        self.anomaly_threshold = anomaly_threshold
        self.gather_data_timer = gather_data_timer
        self.cool_down_timer = cool_down_timer
        self.ensure_anomaly_timer = ensure_anomaly_timer
        self.temperature_residual_abs = 0.0
        self.anomaly_detected = False
        self.kalman_filter = kalman_filter
        self.controller_optimizer = controller_optimizer

        # Verified monitor to detect future problems after optimizing
        # controller in response to anomolies
        self.verified_monitor = verified_monitor
        self.lookahead_time = lookahead_time

        # Uncertainty calibrator to calculate interval uncertain parameters
        self.uncertainty_calibrator = uncertainty_calibrator

        # Collect together verified traces and models
        self.anomaly_durations = []
        self.anomaly_real_temperatures = []
        self.anomaly_predicted_temperatures = []
        self.anomaly_parameters = []
        self.verified_monitoring_results = []

        # Holds the next sample for which an action has to be taken.
        self.next_action_timer = -1
        self.calibrator = calibrator
        self.time_anomaly_start = -1.0

    def reset(self):
        self.current_state = "Listening"
        self.next_action_timer = -1
        self.anomaly_detected = False
        self.time_anomaly_start = -1.0

    def step(self, real_temperature, predicted_temperature, time_s, skip_anomaly_detection=False):
        self.temperature_residual_abs = np.absolute(real_temperature - predicted_temperature)

        if self.current_state == "Listening":
            assert not self.anomaly_detected
            assert self.next_action_timer < 0
            self.anomaly_real_temperatures.append(real_temperature)
            self.anomaly_predicted_temperatures.append(predicted_temperature)
            if skip_anomaly_detection:
                self.time_anomaly_start = time_s
                self.current_state = "GatheringData"
                self.next_action_timer = self.gather_data_timer
                self.anomaly_detected = True
            else:
                if self.temperature_residual_abs >= self.anomaly_threshold:
                    self.time_anomaly_start = time_s
                    self.next_action_timer = self.ensure_anomaly_timer
                    self.current_state = "EnsuringAnomaly"
            return
        if self.current_state == "EnsuringAnomaly":
            assert not self.anomaly_detected
            assert self.next_action_timer >= 0

            if self.next_action_timer > 0:
                self.next_action_timer -= 1

            if self.temperature_residual_abs < self.anomaly_threshold:
                self.reset()
                return

            if self.next_action_timer == 0:
                assert self.temperature_residual_abs >= self.anomaly_threshold
                self.current_state = "GatheringData"
                self.next_action_timer = self.gather_data_timer
                self.anomaly_detected = True
                return

            return
        if self.current_state == "GatheringData":
            assert self.anomaly_detected
            assert self.next_action_timer >= 0
            if self.next_action_timer > 0:
                self.next_action_timer -= 1
            if self.next_action_timer == 0:
                self.current_state = "Calibrating"
                self.next_action_timer = -1
            return
        if self.current_state == "Calibrating":
            assert self.time_anomaly_start >= 0.0
            assert self.time_anomaly_start <= time_s
            success, C_air, G_box, C_heater, G_heater = self.calibrator.calibrate(self.time_anomaly_start, time_s)
            if success:
                self.kalman_filter.update_parameters(C_air, G_box, C_heater, G_heater)
                self.controller_optimizer.optimize_controller()

                # Can we insert the verified model here?
                # Retrieving the parameters for the verified twin from the database
                n_samples_heating, n_samples_period, heater_ctrl_step = self.calibrator.database.get_ctrl_parameters()
                vsignals, t_start_idx, t_end_idx = self.calibrator.database.get_plant_signals_between(
                    self.time_anomaly_start,
                    time_s,
                )
                times = vsignals["time"][t_start_idx:t_end_idx]
                print(f"running verified monitoring for anomaly between times {times[0]} and {times[-1]}")
                reference_T = vsignals["T"][t_start_idx:t_end_idx]
                ctrl_signal = vsignals["in_heater_on"][t_start_idx:t_end_idx]
                reference_T_heater = vsignals["T_heater"][t_start_idx:t_end_idx]
                room_T_range = vsignals["in_room_temperature"][t_start_idx:t_end_idx]
                room_T = RIF(min(*room_T_range), max(*room_T_range))

                if self.uncertainty_calibrator is None:
                    T0 = RIF(reference_T[0])
                    T_H0 = RIF(reference_T_heater[0])
                else:
                    T0, T_H0, C_air, G_box = self.uncertainty_calibrator.calibrate(times[0], times[-1], C_air, G_box, C_heater, G_heater)

                # Run the verified twin simulation
                monitoring_results = self.verified_monitor.verified_monitoring_results(
                    self.time_anomaly_start,
                    self.time_anomaly_start + self.lookahead_time,
                    reference_T[0],
                    reference_T_heater[0],
                    room_T,
                    heater_ctrl_step,
                    n_samples_period,
                    n_samples_heating,
                    C_air, G_box, C_heater, G_heater,
                )
                
                # Store all of the verified models and traces in a list
                self.anomaly_durations.append((times[0], times[-1]))
                self.anomaly_parameters.append((
                    self.time_anomaly_start,
                    self.time_anomaly_start + self.lookahead_time,
                    reference_T[0],
                    reference_T_heater[0],
                    room_T,
                    heater_ctrl_step,
                    n_samples_period,
                    n_samples_heating,
                    C_air, G_box, C_heater, G_heater,
                ))
                self.verified_monitoring_results.append(monitoring_results)

                self.current_state = "CoolingDown"
                self.next_action_timer = self.cool_down_timer
                self.anomaly_detected = False
            return
        if self.current_state == "CoolingDown":
            assert not self.anomaly_detected
            assert self.next_action_timer >= 0
            if self.next_action_timer > 0:
                self.next_action_timer -= 1
            if self.next_action_timer == 0:
                self.reset()
            return



class SelfAdaptationModel(Model):
    def __init__(self,
                 manager: SelfAdaptationManager
                 ):
        super().__init__()

        self.in_reset = self.input(lambda: False)
        self.real_temperature = self.input(lambda: 0.0)
        self.predicted_temperature = self.input(lambda: 0.0)
        self.state_machine = manager

        self.anomaly_detected = self.var(lambda: self.state_machine.anomaly_detected)
        self.temperature_residual_abs = self.var(lambda: self.state_machine.temperature_residual_abs)

        self.save()

    def discrete_step(self):
        self.state_machine.step(self.real_temperature(), self.predicted_temperature(), self.time())
        return super().discrete_step()
