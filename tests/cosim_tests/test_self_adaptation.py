from oomodelling import ModelSolver
import matplotlib.pyplot as plt

from calibration.calibrator import Calibrator
from calibration.calibrator_database import CalibratorDatabase
from config.config import load_config
from digital_twin.simulator.plant_simulator import PlantSimulator4Params
from models.plant_models.four_parameters_model.four_parameter_model import FourParameterIncubatorPlant
from models.self_adaptation.self_adaptation_model import SelfAdaptationScenario
from monitoring.anomaly_detector import AnomalyDetectorSM
from monitoring.kalman_filter_4p import KalmanFilter4P
from tests.cli_mode_test import CLIModeTest


class SelfAdaptationTests(CLIModeTest):

    def test_run_anomaly_detector(self):
        config = load_config("startup.conf")

        n_samples_period = config["physical_twin"]["controller_open_loop"]["n_samples_period"]
        n_samples_heating = config["physical_twin"]["controller_open_loop"]["n_samples_heating"]
        C_air = config["digital_twin"]["models"]["plant"]["param4"]["C_air"]
        G_box = config["digital_twin"]["models"]["plant"]["param4"]["G_box"]
        C_heater = config["digital_twin"]["models"]["plant"]["param4"]["C_heater"]
        G_heater = config["digital_twin"]["models"]["plant"]["param4"]["G_heater"]
        initial_box_temperature = config["digital_twin"]["models"]["plant"]["param4"]["initial_box_temperature"]
        initial_heat_temperature = config["digital_twin"]["models"]["plant"]["param4"]["initial_heat_temperature"]
        std_dev = 0.02
        step_size = 3.0
        anomaly_threshold = 4.0
        ensure_anomaly_timer = 10
        conv_xatol = 0.1
        conv_fatol = 0.1
        max_iterations = 200

        kalman = KalmanFilter4P(std_dev, step_size,
                                C_air, G_box, C_heater, G_heater,
                                initial_box_temperature, initial_heat_temperature, initial_box_temperature)

        database = MockDatabase()
        plant_simulator = PlantSimulator4Params()
        calibrator = Calibrator(database, plant_simulator, conv_xatol, conv_fatol, max_iterations)
        anomaly_detector = AnomalyDetectorSM(anomaly_threshold, ensure_anomaly_timer, calibrator, kalman)

        m = SelfAdaptationScenario(n_samples_period, n_samples_heating,
                                   C_air, G_box, C_heater, G_heater,
                                   initial_box_temperature,
                                   initial_heat_temperature,
                                   kalman, anomaly_detector,
                                   std_dev)

        # Inform mock db of plant _model.
        database.set_model(m.physical_twin.plant)

        # Wire in a custom function for the G_box input, so we can change it.
        m.physical_twin.plant.G_box = lambda: G_box if m.time() < 1000 else (G_box * 10 if m.time() < 2000 else G_box)

        ModelSolver().simulate(m, 0.0, 6000, 3.0)

        fig, (ax1, ax2) = plt.subplots(2, 1)

        ax1.plot(m.signals['time'], m.physical_twin.plant.signals['T'], label=f"- T")
        ax1.plot(m.signals['time'], m.kalman.signals['out_T'], linestyle="dashed", label=f"~ T")

        for (times, trajectory) in database.trajectory_history:
            ax1.plot(times, trajectory[0, :], label=f"cal T")

        ax1.legend()

        ax2.plot(m.signals['time'], [1 if b else 0 for b in m.anomaly.signals["anomaly_detected"]], label="Anomaly")

        if self.ide_mode():
            plt.show()


class MockDatabase(CalibratorDatabase):
    _model: FourParameterIncubatorPlant = None
    C_air: list[float] = []
    G_box: list[float] = []
    C_heater: list[float] = []
    G_heater: list[float] = []
    trajectory_history: list = []

    def set_model(self, model: FourParameterIncubatorPlant):
        assert len(self.C_air) == len(self.G_box) == len(self.C_heater) == len(self.G_heater) == \
               len(self.trajectory_history) == 0
        self._model = model
        self.C_air.append(model.C_air)
        self.G_box.append(model.G_box())
        self.C_heater.append(model.C_heater)
        self.G_heater.append(model.G_heater)

    def get_signals_between(self, t_start, t_end):
        signals = self._model.signals
        # Find indexes for t_start and t_end
        t_start_idx = next(i for i, t in enumerate(signals["time"]) if t >= t_start)
        t_end_idx = next(i for i, t in enumerate(signals["time"]) if t >= t_end)
        return signals, t_start_idx, t_end_idx

    def store_calibrated_trajectory(self, times, calibrated_sol):
        self.trajectory_history.append((times, calibrated_sol))

    def update_parameters(self, C_air_new, G_box_new, C_heater, G_heater):
        self.C_air.append(C_air_new)
        self.G_box.append(G_box_new)
        self.C_heater.append(C_heater)
        self.G_heater.append(G_heater)

    def get_plant4_parameters(self):
        return self.C_air[-1], self.G_box[-1], self.C_heater[-1], self.G_heater[-1]
