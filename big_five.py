import re
import pandas as pd
from markupsafe import Markup

from psynet.timeline import join
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

from .game_paramters import (
    RNG,
    NUM_BIG_FIVE_QUESTIONS,
    TIMEOUT_WAITING_BIG_FIVE_QUESTIONS,
)
from .custom_front_end import (
    CustomLikertControl,
    TimeoutPrompt,
)


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
        lambda m: m.group(1) if (m.group(1) == "I " or m.group(1) == "I'") else m.group(1).lower(),
        text,
    )

    return text


full_items = pd.read_csv("static/big_five_modified.csv").to_dict(orient="records")

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
            "dummy": "ok"
        },
    )
]


class PersonalityTrial(StaticTrial):
    time_estimate = 5

    def show_trial(self, experiment, participant):
        return join([
            PersonalityTrial.question_page(
                question=item["item"],
                idx=idx,
                time_estimate=self.time_estimate,
            )
            for idx, item in enumerate(short_items[:NUM_BIG_FIVE_QUESTIONS])
        ])

    @staticmethod
    def question_page(question: str, idx: int, time_estimate: int):
        page_label = f"big_five_question_{idx}"

        text = "<h2>Before we start</h2>"
        text += "<p>We want to ask you some questions about your personality traits. </p>"
        text += "<p><span style='font-weight:700'>Please report how accurate is the following statement:</span> </p>"
        text += "<br>"
        text += f"<h6>I see myself as someone who {format_text(question)}</h6>"
        text += "<br>"

        return ModularPage(
            label=page_label,
            prompt=TimeoutPrompt(
                text=Markup(text),
                timeout=TIMEOUT_WAITING_BIG_FIVE_QUESTIONS,
                show_rounds=False,
            ),
            control=CustomLikertControl(
                lowest_value="Very inaccurate",
                highest_value="Very accurate",
                n_steps=5,
            ),
            time_estimate=time_estimate,
            save_answer=page_label
        )


class WaitingTrial(StaticTrial):
    time_estimate = 3

    def show_trial(self, experiment, participant):

        item = RNG.choice(full_items)
        question = item["item"]
        text = "<h2>Waiting...</h2>"
        text += "<br>"
        text += "<p>We are waiting for other participants. </p>"
        text += "<p>In the meantime, <span style='font-weight:700'>please report how accurate is the following statement:</span> </p>"
        text += "<br>"
        text += f"<h6>I see myself as someone who {format_text(question)}</h6>"
        text += "<br>"

        return ModularPage(
            label="waiting_trial",
            prompt=TimeoutPrompt(
                text=Markup(text),
                timeout=TIMEOUT_WAITING_BIG_FIVE_QUESTIONS,
                show_rounds=False,
            ),
            control=CustomLikertControl(
                lowest_value="Very inaccurate",
                highest_value="Very accurate",
                n_steps=5,
            ),
            time_estimate=self.time_estimate
        )


class PersonalityTrialMaker(StaticTrialMaker):
    pass
