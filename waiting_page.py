import pandas as pd
from psynet.trial.static import (
    StaticTrial,
    StaticNode,
)
from psynet.modular_page import (
    ModularPage,
    PushButtonControl,
)

from .game_paramters import RNG

full_items = pd.read_csv("static/big_five.csv").to_dict(orient="records")
RNG.shuffle(full_items)

waiting_nodes = [
    StaticNode(
        definition={
            "question_id": item["full_position"],
            "question_text": item["item"],
        },
    ) for item in full_items
]


class WaitingTrial(StaticTrial):
    time_estimate = 3

    def show_trial(self, experiment, participant):

        question = self.definition["question"]
        text = "We are waiting for other participants.\n"
        text += "In the meantime, please Please report how accurately this describes you:\n"
        text += f"I see myself as someone who {question}?"

        return ModularPage(
            "waiting_trial",
            text,
            PushButtonControl(
                ["Very Inaccurate", "Moderately Inaccurate", "Neither Accurate Nor Inaccurate", "Moderately Accurate", "Very Accurate"],
            ),
        )

