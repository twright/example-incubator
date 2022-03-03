from oomodelling import Model

from models.physical_twin_models.system_model4_open_loop import SystemModel4ParametersOpenLoop
from monitoring.anomaly_detector import AnomalyDetector, AnomalyDetectorSM
from monitoring.kalman_filter_4p import KalmanFilter4P
from monitoring.noise_model import NoiseFeedthrough


class SelfAdaptationScenario(Model):
    def __init__(self,
                 # Initial Controller parameters
                 n_samples_period, n_samples_heating,
                 # Plant parameters
                 C_air,
                 G_box,
                 C_heater,
                 G_heater,
                 initial_box_temperature,
                 initial_heat_temperature,
                 # Kalman Filter
                 kalman: KalmanFilter4P,
                 # Anomaly detector
                 anomaly_detector_sm: AnomalyDetectorSM,
                 std_dev
                 ):
        super().__init__()

        self.physical_twin = SystemModel4ParametersOpenLoop(n_samples_period,
                                                            n_samples_heating,
                                                            C_air,
                                                            G_box,
                                                            C_heater,
                                                            G_heater, initial_box_temperature,
                                                            initial_heat_temperature)

        self.kalman = kalman

        self.anomaly = AnomalyDetector(anomaly_detector_sm)

        # Plant --> KF
        # self.noise_sensor = NoiseFeedthrough(std_dev)
        # self.noise_sensor.u = self.physical_twin.plant.T
        # self.kalman.in_T = self.noise_sensor.y
        self.kalman.in_T = self.physical_twin.plant.T
        self.kalman.in_heater_on = self.physical_twin.ctrl.heater_on

        # KF --> AnomalyDetector
        self.anomaly.predicted_temperature = self.kalman.out_T
        # Plant --> AnomalyDetector
        self.anomaly.real_temperature = self.physical_twin.plant.T

        self.save()
