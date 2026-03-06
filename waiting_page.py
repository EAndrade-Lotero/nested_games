from psynet.trial.static import StaticTrial
from psynet.modular_page import (
    ModularPage,
    PushButtonControl,
)

from .game_paramters import RNG


class WaitingTrial(StaticTrial):
    time_estimate = 3

    def show_trial(self, experiment, participant):

        question = self.definition["question"]

        return ModularPage(
            "waiting_trial",
            f"We are waiting for other participants. In the meantime, please answer this question: {question}?",
            PushButtonControl(
                ["Not at all", "A little", "Very much"],
            ),
        )
