
from psynet.trial.static import (
    StaticTrial,
    StaticTrialMaker,
)
from psynet.page import InfoPage


class TestTrialMaker(StaticTrialMaker):
    pass


class TestTrial(StaticTrial):
    time_estimate = 5
    accumulate_answers = True

    def show_trial(self, experiment, participant):
        outer_role = TestTrial.get_value_from_var(self.participant, "outer_role")
        text = "OK"
        if outer_role is not None:
            text = outer_role
        return InfoPage(
            text,
            time_estimate=5,
        )

    @staticmethod
    def get_value_from_var(participant, variable: str):
        if participant.var.has(variable):
            return getattr(participant.var, variable)
        else:
            return None
