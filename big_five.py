import re
import pandas as pd
from markupsafe import Markup

from psynet.timeline import join
from psynet.trial.static import (
    StaticTrialMaker,
    StaticTrial,
    StaticNode,
)
from psynet.page import UnsuccessfulEndPage
from psynet.timeline import conditional
from psynet.modular_page import ModularPage
from psynet.utils import get_logger

from .game_paramters import (
    RNG,
    NUM_BIG_FIVE_QUESTIONS,
    TIME_ESTIMATE_FOR_COMPENSATION,
    STANDARD_TIMEOUT,
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
    time_estimate = TIME_ESTIMATE_FOR_COMPENSATION

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
                timeout=STANDARD_TIMEOUT,
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
    time_estimate = TIME_ESTIMATE_FOR_COMPENSATION

    def show_trial(self, experiment, participant):

        self.item = RNG.choice(full_items)
        question = self.item["item"]
        text = "<h2>Waiting...</h2>"
        text += "<br>"
        text += "<p>We are waiting for other participants. </p>"
        text += "<p>In the meantime, <span style='font-weight:700'>please report how accurate is the following statement:</span> </p>"
        text += "<br>"
        text += f"<span style='display: block; text-align: center; font-size: 14pt; font-style: italic;'>I see myself as someone who {format_text(question)}</span>"
        text += "<br>"
        text += "<br>"
        text += "<p><span style='font-weight: bold;'>Important:</span> Please do not allow the experiment to timeout.</p>"
        text += "<p>We cannot compensate you monetarily if you allow this page to timeout.</p>"
        text += "<br>"

        return [
            ModularPage(
                label="waiting_trial",
                prompt=TimeoutPrompt(
                    text=Markup(text),
                    timeout=STANDARD_TIMEOUT,
                    show_rounds=False,
                ),
                control=CustomLikertControl(
                    lowest_value="Very inaccurate",
                    highest_value="Very accurate",
                    n_steps=5,
                ),
                time_estimate=self.time_estimate
            ),
            conditional(
                label="Checking if participant timeout",
                condition=lambda participant: participant.answer == "No answer",
                logic_if_true=UnsuccessfulEndPage(
                    failure_tags=["waiting_pages_timeout"],
                ),
                logic_if_false=None,
            )
        ]

    def format_answer(self, raw_answer, **kwargs):
        return {
            "item_id": self.item["id"],
            "choice": raw_answer,
        }


class PersonalityTrialMaker(StaticTrialMaker):
    pass

    # SOMETHING ODD HAPPENS WHEN max_trials_per_participant IS REACHED
    # THE TIMELINE ENTERS AN INFINITE LOOP.
    # PROBABLY THE FOLLOWING CODE HELPS, BUT IS NOT WORKING RIGHT NOW
    # def find_networks(self, participant, experiment):
    #     result = self.find_networks(participant, experiment)
    #     if result == "exit":
    #         participant.fail(reason="Waiting_time_exceeded")
    #     return result

