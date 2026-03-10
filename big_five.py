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
from psynet.utils import get_logger

from .game_paramters import RNG


logger = get_logger()


def format_text(text: str) -> str:
    """Remove trailing periods and lowercase sentence starts,
    except for the pronoun 'I'."""
    if not text:
        return text

    # Remove ending periods (one or more) and surrounding spaces
    text = re.sub(r"\.*\s*$", "", text)

    # Lowercase the first character if it is uppercase and not 'I'
    text = re.sub(
        r"^([A-Z])",
        lambda m: m.group(1) if m.group(1) == "I" else m.group(1).lower(),
        text,
    )

    return text


full_items = pd.read_csv("static/big_five.csv").to_dict(orient="records")

waiting_nodes = [
    StaticNode(
        definition={
            "dummy": "ok"
        },
    )
]

short_items = pd.read_csv("static/big_five_short.csv").to_dict(orient="records")

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

        item = RNG.choice(full_items)
        question = item["item"]
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
