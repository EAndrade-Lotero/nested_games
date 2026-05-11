import re
import pandas as pd
from markupsafe import Markup

from psynet.timeline import join
from psynet.trial.static import (
    StaticTrialMaker,
    StaticTrial,
    StaticNode,
)
from psynet.page import UnsuccessfulEndPage, InfoPage
from psynet.timeline import conditional, PageMaker
from psynet.modular_page import ModularPage
from psynet.utils import get_logger

from .game_paramters import (
    RNG,
    NUM_BIG_FIVE_QUESTIONS,
    TIME_ESTIMATE_FOR_COMPENSATION,
    STANDARD_TIMEOUT,
    MAX_FOCUS_LOSS,
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
            "item_id": idx,
            "question": item["item"],
        },
    ) for idx, item in enumerate(short_items[:NUM_BIG_FIVE_QUESTIONS])
]


class WaitingTrialLikertPage(ModularPage):
    """Calls ``WaitingTrial.increment_focus_loss`` once per ``Focus_lost`` entry in the trial event log."""

    def __init__(self, label, prompt, control, item_idx, **kwargs):
        super().__init__(label, prompt, control, **kwargs)
        self.item_idx = item_idx

    def format_answer(self, raw_answer, **kwargs):
        metadata = kwargs.get("metadata") or {}
        participant = kwargs.get("participant")
        trial = kwargs.get("trial")
        increment_focus_loss = getattr(trial, "increment_focus_loss", None)
        # logger.info(f"Trial increment_focus_loss type {type(increment_focus_loss)}")

        if participant is not None and callable(increment_focus_loss):
            # logger.info(f"Entering increment focus loss for participant {participant}")
            for entry in metadata.get("event_log") or []:
                if entry.get("eventType") == "Focus_lost":
                    # logger.info(f"Leaving event log for participant {participant}")
                    increment_focus_loss(participant)

        num_focus_loss = 0
        if participant.var.has("focus_loss"):
            num_focus_loss = participant.var.focus_loss

        return {
            "item_id": self.item_idx,
            "choice": raw_answer,
            "num_focus_loss": num_focus_loss,
        }


class PersonalityTrial(StaticTrial):
    time_estimate = TIME_ESTIMATE_FOR_COMPENSATION

    def show_trial(self, experiment, participant):
        idx = self.definition["item_id"]
        question = self.definition["question"]
        page_label = f"big_five_question_{idx}"
        text = "<h2>Before we start</h2>"
        text += "<p>We want to ask you some questions about your personality traits. </p>"
        text += "<p><span style='font-weight:700'>Please report how accurate is the following statement:</span> </p>"
        text += "<br>"
        text += f"<span style='display: block; text-align: center; font-size: 14pt; font-style: italic;'>I see myself as someone who {format_text(question)}</span>"
        text += "<br>"
        text += "<br>"
        text += "<p><span style='font-weight: bold;'>Important:</span> Please do not allow the experiment to timeout.</p>"
        text += "<p>We cannot compensate you monetarily if you allow this page to timeout.</p>"
        text += "<br>"

        return [
            WaitingTrialLikertPage(
                label=page_label,
                prompt=TimeoutPrompt(
                    text=Markup(text),
                    timeout=STANDARD_TIMEOUT,
                    show_rounds=False,
                    ask_not_to_loose_focus=True,
                ),
                control=CustomLikertControl(
                    lowest_value="Very inaccurate",
                    highest_value="Very accurate",
                    n_steps=5,
                ),
                item_idx=idx,
                time_estimate=self.time_estimate,
                save_answer=page_label
            ),
            PageMaker(
                lambda experiment, participant:
                InfoPage(
                    Markup(
                        f"{participant.answer}"
                        f"{WaitingTrial.should_fail(participant)}"
                    ),
                    time_estimate=5
                ),
                time_estimate=5
            ),
            conditional(
                label="Checking if participant timeout",
                condition=lambda participant: PersonalityTrial.should_fail(participant),
                logic_if_true=UnsuccessfulEndPage(
                    failure_tags=["personality_pages_failure"],
                ),
                logic_if_false=None,
            ),
        ]

    @staticmethod
    def increment_focus_loss(participant):
        if not participant.var.has("focus_loss"):
            participant.var.set("focus_loss", 0)
        participant.var.focus_loss += 1

    @staticmethod
    def max_num_unfocus_reached(participant):
        num_focus_loss = 0
        if participant.var.has("focus_loss"):
            num_focus_loss = participant.var.focus_loss
        if num_focus_loss > MAX_FOCUS_LOSS:
            return True
        return False

    @staticmethod
    def should_fail(participant):
        check1 = participant.answer["choice"] == "No answer"
        check2 = PersonalityTrial.max_num_unfocus_reached(participant)
        return check1 or check2


class WaitingTrial(StaticTrial):
    time_estimate = TIME_ESTIMATE_FOR_COMPENSATION
    propagate_failure = False
    item = 0

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
            WaitingTrialLikertPage(
                label="waiting_trial",
                prompt=TimeoutPrompt(
                    text=Markup(text),
                    timeout=STANDARD_TIMEOUT,
                    show_rounds=False,
                    ask_not_to_loose_focus=True,
                ),
                control=CustomLikertControl(
                    lowest_value="Very inaccurate",
                    highest_value="Very accurate",
                    n_steps=5,
                ),
                item_idx=self.item["id"],
                time_estimate=self.time_estimate,
            ),
            # conditional(
            #     label="Checking if participant timeout",
            #     condition=lambda participant: WaitingTrial.should_fail(participant),
            #     logic_if_true=UnsuccessfulEndPage(
            #         failure_tags=["waiting_pages_failure"],
            #     ),
            #     logic_if_false=None,
            # )
        ]

    @staticmethod
    def increment_focus_loss(participant):
        if not participant.var.has("focus_loss"):
            participant.var.set("focus_loss", 0)
        participant.var.focus_loss += 1

    @staticmethod
    def max_num_unfocus_reached(participant):
        num_focus_loss = 0
        if participant.var.has("focus_loss"):
            num_focus_loss = participant.var.focus_loss
        if num_focus_loss > MAX_FOCUS_LOSS:
            return True
        return False

    @staticmethod
    def should_fail(participant):
        check1 = participant.answer["choice"] == "No answer"
        check2 = PersonalityTrial.max_num_unfocus_reached(participant)
        failure = check1 or check2
        reason = ""
        if failure:
            reason = "Reason:"
            if check1:
                reason += " inactive_timeout;"
                participant.vars.no_answer = True
            if check2:
                reason += " max_loss_focus;"
                participant.vars.focus_loss = participant.var.focus_loss

        logger.info(f"Failure? {failure}; Reason: {reason}")
        return failure


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

