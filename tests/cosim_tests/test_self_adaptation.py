from oomodelling import ModelSolver
import matplotlib.pyplot as plt
from config.config import load_config
from models.self_adaptation.self_adaptation_model import SelfAdaptationScenario
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
        std_dev = 0.01
        step_size = 3.0
        anomaly_threshold = 1.0
        ensure_anomaly_timer = 3

        m = SelfAdaptationScenario(n_samples_period, n_samples_heating,
                                   C_air,
                                   G_box,
                                   C_heater,
                                   G_heater,
                                   initial_box_temperature,
                                   initial_heat_temperature,
                                   std_dev,
                                   step_size,
                                   anomaly_threshold, ensure_anomaly_timer)

        # Wire in a custom function for the G_box input, so we can change it.
        m.physical_twin.plant.G_box = lambda: G_box if m.time() < 300 else (G_box * 10 if m.time() < 2000 else G_box)

        ModelSolver().simulate(m, 0.0, 6000, 3.0)

        fig, (ax1, ax2) = plt.subplots(2, 1)

        ax1.plot(m.signals['time'], m.physical_twin.plant.signals['T'], label=f"- T")
        ax1.plot(m.signals['time'], m.kalman.signals['out_T'], linestyle="dashed", label=f"~ T")

        ax1.legend()

        ax2.plot(m.signals['time'], [1 if b else 0 for b in m.anomaly.signals["anomaly_detected"]], label="Anomaly")

        if self.ide_mode():
            plt.show()
