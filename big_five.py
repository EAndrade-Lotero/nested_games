import re
import pandas as pd
from markupsafe import Markup

from psynet.trial.static import (
    StaticTrialMaker,
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

short_items = pd.read_csv("static/big_five_short.csv").to_dict(orient="records")
RNG.shuffle(short_items)

personality_nodes = [
    StaticNode(
        definition={
            "question_id": item["full_position"],
            "question_text": item["item"],
        },
    ) for item in short_items
]


class PersonalityTrial(StaticTrial):
    time_estimate = 3

    def show_trial(self, experiment, participant):

        question = self.definition["question_text"]
        text = "We want to ask you some questions about your personality traits. "
        text += "Please report how accurate is the following statement: "
        text += f"<h6>I see myself as someone who {question}</h6>"

        return ModularPage(
            "waiting_trial",
            Markup(text),
            PushButtonControl(
                [
                    "Very inaccurate",
                    "Moderately inaccurate",
                    "Neither accurate nor inaccurate",
                    "Moderately accurate",
                    "Very accurate"
                ],
            ),
        )


class WaitingTrial(StaticTrial):
    time_estimate = 3

    def show_trial(self, experiment, participant):

        question = self.definition["question_text"]
        text = "We are waiting for other participants. "
        text += "In the meantime, please report how accurate is the following statement: "
        text += f"<h6>I see myself as someone who {question}</h6>"

        return ModularPage(
            "waiting_trial",
            Markup(text),
            PushButtonControl(
                [
                    "Very inaccurate",
                    "Moderately inaccurate",
                    "Neither accurate nor inaccurate",
                    "Moderately accurate",
                    "Very accurate"
                ],
            ),
        )


class PersonalityTrialMaker(StaticTrialMaker):
    pass
