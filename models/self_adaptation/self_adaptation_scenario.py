from oomodelling import Model

from models.physical_twin_models.system_model4_open_loop import SystemModel4ParametersOpenLoop
from self_adaptation.self_adaptation_manager import SelfAdaptationModel, SelfAdaptationManager
from monitoring.kalman_filter_4p import KalmanFilter4P
from self_adaptation.supervisor import SupervisorSM, SupervisorModel


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
                 anomaly_detector_sm: SelfAdaptationManager,
                 # Supervisor
                 supervisor_sm: SupervisorSM,
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

        # Note the relative order between anomaly detector and Kalman filter.
        # We assign anomaly first so that it will step before the kalman filter does,
        # preventing the kalman filter from quickly recovering.
        self.anomaly = SelfAdaptationModel(anomaly_detector_sm)
        self.kalman = kalman
        self.supervisor = SupervisorModel(supervisor_sm)

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

        # KF --> Supervisor
        self.supervisor.T = self.kalman.out_T
        self.supervisor.T_heater = self.kalman.out_T_heater

        self.save()
