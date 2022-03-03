import numpy as np
from oomodelling import Model

from calibration.calibrator import Calibrator
from monitoring.updateable_kalman_filter import UpdateableKalmanFilter


class AnomalyDetectorSM:
    def __init__(self, anomaly_threshold, ensure_anomaly_timer,
                 calibrator: Calibrator,
                 kalman_filter: UpdateableKalmanFilter):
        assert 0 < ensure_anomaly_timer
        assert 0 < anomaly_threshold
        self.current_state = "Listening"
        self.anomaly_threshold = anomaly_threshold
        self.ensure_anomaly_timer = ensure_anomaly_timer
        self.anomaly_detected = False
        self.kalman_filter = kalman_filter
        # Holds the next sample for which an action has to be taken.
        self.next_action_timer = -1.0
        self.calibrator = calibrator
        self.time_anomaly_start = -1.0

    def reset(self):
        self.current_state = "Listening"
        self.next_action_timer = -1
        self.anomaly_detected = False
        self.time_anomaly_start = -1.0

    def step(self, real_temperature, predicted_temperature, time):
        temperature_residual_abs = np.absolute(real_temperature - predicted_temperature)

        if self.current_state == "Listening":
            assert not self.anomaly_detected
            assert self.next_action_timer < 0
            if temperature_residual_abs >= self.anomaly_threshold:
                self.time_anomaly_start = time
                self.next_action_timer = self.ensure_anomaly_timer
                self.current_state = "EnsuringAnomaly"
            return
        if self.current_state == "EnsuringAnomaly":
            assert not self.anomaly_detected
            assert self.next_action_timer >= 0

            if self.next_action_timer > 0:
                self.next_action_timer -= 1

            if temperature_residual_abs < self.anomaly_threshold:
                self.reset()
                return

            if self.next_action_timer == 0:
                assert temperature_residual_abs >= self.anomaly_threshold
                self.current_state = "AnomalyDetected"
                self.next_action_timer = -1
                self.anomaly_detected = True
                success, C_air, G_box, C_heater, G_heater = self.calibrator.calibrate(self.time_anomaly_start, time)
                if success:
                    self.kalman_filter.update_parameters(C_air, G_box, C_heater, G_heater)
                    self.reset()
                return

            return


class AnomalyDetector(Model):
    def __init__(self,
                 anomaly_detector_sm
                 ):
        super().__init__()

        self.in_reset = self.input(lambda: False)
        self.real_temperature = self.input(lambda: 0.0)
        self.predicted_temperature = self.input(lambda: 0.0)
        self.state_machine = anomaly_detector_sm

        self.anomaly_detected = self.var(lambda: self.state_machine.anomaly_detected)

        self.save()

    def discrete_step(self):
        self.state_machine.step(self.real_temperature(), self.predicted_temperature(), self.time())
        return super().discrete_step()