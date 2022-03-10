import numpy as np
from oomodelling import Model

from self_adaptation.controller_optimizer import ControllerOptimizer


class SupervisorSM:
    def __init__(self, controller_optimizer: ControllerOptimizer,
                 desired_temperature, max_t_heater, restrict_T_heater, trigger_optimization_threshold, wait_til_supervising_timer):
        # Constants
        self.controller_optimizer = controller_optimizer
        self.desired_temperature = desired_temperature
        self.max_t_heater = max_t_heater
        # TODO Remove this unused attribute.
        self.restrict_T_heater = restrict_T_heater
        self.trigger_optimization_threshold = trigger_optimization_threshold
        self.wait_til_supervising_timer = wait_til_supervising_timer

        # Holds the next sample for which an action has to be taken.
        self.next_action_timer = -1
        self.current_state = None
        self.reset()

    def reset(self):
        self.next_action_timer = self.wait_til_supervising_timer
        self.current_state = "Waiting"

    def step(self, T, T_heater, time):
        if self.current_state == "Waiting":
            assert self.next_action_timer >= 0
            if self.next_action_timer > 0:
                self.next_action_timer -= 1

            if self.next_action_timer == 0:
                self.current_state = "Listening"
                self.next_action_timer = -1
            return
        if self.current_state == "Listening":
            assert self.next_action_timer < 0
            heater_safe = T_heater < self.max_t_heater
            temperature_residual = np.absolute(T - self.desired_temperature)
            if heater_safe and (temperature_residual > self.trigger_optimization_threshold):
                # Reoptimize controller and then go into waiting
                self.controller_optimizer.optimize_controller()
                self.reset()
                return
            else:
                pass  # Remain in listening and keep checking for deviations.
            return


class SupervisorModel(Model):
    def __init__(self, sm: SupervisorSM):
        super().__init__()

        self.state_machine = sm

        self.T = self.input(lambda: 0.0)
        self.T_heater = self.input(lambda: 0.0)

        self.save()

    def discrete_step(self):
        self.state_machine.step(self.T(), self.T_heater(), self.time())
        return super().discrete_step()
