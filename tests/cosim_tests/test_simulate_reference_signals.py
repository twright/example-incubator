from matplotlib import pyplot as plt

from digital_twin.simulator.plant_simulator import PlantSimulator4Params
from models.physical_twin_models.system_model4_open_loop import SystemModel4ParametersOpenLoopSimulator
from tests.cli_mode_test import CLIModeTest


class TestSimulateReferenceSignals(CLIModeTest):

    def test_bug_shown_by_thomas(self):
        """
        This bug occurs in the calibrator, when a simulation is run with control signals as reference.
        So to reproduce it, we run a simulation, then use those as simulation results for a second simulation
        """
        pt_simulator = SystemModel4ParametersOpenLoopSimulator()
        plant_simulator = PlantSimulator4Params()

        initial_T = 20.0
        initial_T_heater = 20.0
        initial_room_T = 21.0
        parameter = 1.0

        model = pt_simulator.run_simulation(0.0, 30.0,
                                            initial_T, initial_T_heater, initial_room_T,
                                            5, 10, 3.0,
                                            parameter, parameter, parameter, parameter)

        sol, plant_model = plant_simulator.run_simulation(model.signals["time"],
                                       initial_T, initial_T_heater,
                                       model.plant.signals['in_room_temperature'], model.ctrl.signals['heater_on'],
                                       parameter, parameter, parameter, parameter)

        fig = plt.figure()

        plt.plot(model.signals["time"], model.plant.signals['T_heater'], label='T_heater')
        plt.plot(plant_model.signals["time"], plant_model.signals['T_heater'], label='~T_heater')

        plt.show()

        plt.close(fig)

