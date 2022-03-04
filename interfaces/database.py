class IDatabase:

    def get_signals_between(self, t_start, t_end):
        raise NotImplementedError("For subclasses")

    def store_calibrated_trajectory(self, times, calibrated_sol):
        raise NotImplementedError("For subclasses")

    def update_parameters(self, C_air_new, G_box_new, C_heater, G_heater):
        raise NotImplementedError("For subclasses")

    def get_plant4_parameters(self):
        raise NotImplementedError("For subclasses")

    def get_pt_snapshot(self):
        raise NotImplementedError("For subclasses")

    def get_ctrl_parameters(self):
        raise NotImplementedError("For subclasses")
