from oomodelling import Model


class ControllerOpenLoop(Model):
    def __init__(self,
                 n_samples_period,  # Total number of samples considered
                 n_samples_heating,  # Number of samples (out of n_samples_period) that the heater is on.
                 ):
        assert 0 < n_samples_period
        assert 0 <= n_samples_heating <= n_samples_period
        super().__init__()

        self.n_samples_heating = self.parameter(n_samples_heating)
        self.n_samples_period = self.parameter(n_samples_period)

        self.in_temperature = self.input(lambda: 20.0)

        self.current_state = "Initialized"
        # Holds the next sample for which an action has to be taken.
        self.next_action_timer = -1.0
        self.cached_heater_on = False

        self.heater_on = self.var(lambda: self.cached_heater_on)

        self.save()

    def discrete_step(self):
        self.ctrl_step()
        return super().discrete_step()

    def ctrl_step(self):
        if self.current_state == "Initialized":
            self.cached_heater_on = False
            if 0 < self.n_samples_heating:
                self.current_state = "Heating"
                self.next_action_timer = self.n_samples_heating
            else:
                assert self.n_samples_heating == 0
                self.current_state = "Cooling"
                self.next_action_timer = self.n_samples_period - self.n_samples_heating
            return
        if self.current_state == "Heating":
            assert self.next_action_timer >= 0
            if self.next_action_timer > 0:
                self.cached_heater_on = True
                self.next_action_timer -= 1
            if self.next_action_timer == 0:
                self.current_state = "Cooling"
                self.next_action_timer = self.n_samples_period - self.n_samples_heating
            return
        if self.current_state == "Cooling":
            assert self.next_action_timer >= 0
            if self.next_action_timer > 0:
                self.cached_heater_on = False
                self.next_action_timer -= 1
            if self.next_action_timer == 0:
                self.current_state = "Heating"
                self.next_action_timer = self.n_samples_heating
            return
