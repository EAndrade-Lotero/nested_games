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


def format_text(text: str) -> str:
    if not text:
        return text

    # Remove trailing periods and trailing spaces
    text = re.sub(r"\.+\s*$", "", text.strip())

    # Keep the first letter as-is, lowercase every other capital letter,
    # except standalone pronoun "I"
    if len(text) > 1:
        first = text[0]
        rest = re.sub(
            r"\bI\b|[A-Z]",
            lambda m: m.group(0) if m.group(0) == "I" else m.group(0).lower(),
            text[1:],
        )
        text = first + rest

    return text


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
        text += f"<h6>I see myself as someone who {format_text(question)}</h6>"

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
        text += f"<h6>I see myself as someone who {format_text(question)}</h6>"

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
