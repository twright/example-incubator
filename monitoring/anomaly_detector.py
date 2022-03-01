import numpy as np
from oomodelling import Model


class AnomalyDetectorSM():
    def __init__(self, anomaly_threshold, ensure_anomaly_timer):
        assert 0 < ensure_anomaly_timer
        assert 0 < anomaly_threshold
        self.current_state = "Listening"
        self.anomaly_threshold = anomaly_threshold
        self.ensure_anomaly_timer = ensure_anomaly_timer
        self.anomaly_detected = False
        # Holds the next sample for which an action has to be taken.
        self.next_action_timer = -1.0

    def step(self, real_temperature, predicted_temperature, reset):
        temperature_residual_abs = np.absolute(real_temperature - predicted_temperature)
        if reset:
            self.current_state = "Listening"
            self.next_action_timer = -1
            self.anomaly_detected = False
            return

        if self.current_state == "Listening":
            assert not self.anomaly_detected
            assert self.next_action_timer < 0
            if temperature_residual_abs >= self.anomaly_threshold:
                self.next_action_timer = self.ensure_anomaly_timer
                self.current_state = "EnsuringAnomaly"
            return
        if self.current_state == "EnsuringAnomaly":
            assert not self.anomaly_detected
            assert self.next_action_timer >= 0

            if self.next_action_timer > 0:
                self.next_action_timer -= 1

            if temperature_residual_abs < self.anomaly_threshold:
                self.next_action_timer = -1
                self.current_state = "Listening"
                return

            if self.next_action_timer == 0:
                assert temperature_residual_abs >= self.anomaly_threshold
                self.current_state = "AnomalyDetected"
                self.next_action_timer = -1
                self.anomaly_detected = True
            return


class AnomalyDetector(Model):
    def __init__(self,
                 anomaly_threshold,  # Threshold for which the temperature residual becomes an anomaly
                 ensure_anomaly_timer,  # Number of samples to wait until declaring a real anomaly.
                 ):
        super().__init__()

        self.anomaly_threshold = self.parameter(anomaly_threshold)
        self.ensure_anomaly_timer = self.parameter(ensure_anomaly_timer)

        self.in_reset = self.input(lambda: False)
        self.real_temperature = self.input(lambda: 0.0)
        self.predicted_temperature = self.input(lambda: 0.0)
        self.state_machine = AnomalyDetectorSM(anomaly_threshold, ensure_anomaly_timer)

        self.anomaly_detected = self.var(lambda: self.state_machine.anomaly_detected)

        self.save()

    def discrete_step(self):
        self.state_machine.step(self.real_temperature(), self.predicted_temperature(), self.in_reset())
        return super().discrete_step()
