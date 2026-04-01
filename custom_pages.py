from markupsafe import Markup
from typing import Union, Dict

from psynet.graphics import Prompt
from psynet.modular_page import (
    ModularPage,
    PushButtonControl,
    NullControl,
)
from psynet.timeline import (
    FailedValidation,
    Event,
    ProgressDisplay,
    ProgressStage,
)
from psynet.utils import get_logger

from .custom_front_end import OuterGameControl
from .game_paramters import (
    ENDOWMENT,
    MAX_WAITING_PROPOSALS,
    MAX_WAITING_FOR_OTHER,
)
from .custom_front_end import CustomSliderControl


logger = get_logger()


class OuterProposalPage(ModularPage):
    def __init__(self, context: Dict[str, str]) -> None:

        prompt = Prompt(Markup(
            f"<h2>Preparation phase</h2>"
            f"<br>"
            f"<p>Choose who will take on the role of PROPOSER: </p>"
            f"<br>"
        ))
        control = OuterGameControl(
            context=context,
            timeout=MAX_WAITING_PROPOSALS,
        )
        super().__init__(
            label="outer_proposal",
            prompt=prompt,
            control=control,
            time_estimate=5,
            save_answer="outer_proposal",
            events={
                "done": Event(
                    is_triggered_by="done",
                    js="psynet.submitResponse();",
                    delay=0.0,
                ),
            },
        )


class OuterProposalWaitingPage(ModularPage):
    def __init__(self) -> None:

        prompt = Prompt(Markup(
            f"<h2>Preparation phase</h2>"
            f"<br>"
            "<p>Click 'Next' to see which player your partner selects as PROPOSER. </p>"
        ))
        control = NullControl()
        waiting_time = MAX_WAITING_FOR_OTHER
        progress_display = ProgressDisplay(
            stages=[
                ProgressStage(
                    time=waiting_time,
                    color="gray"
                ),
            ],
        )

        super().__init__(
            label="outer_proposal",
            prompt=prompt,
            control=control,
            time_estimate=5,
            save_answer="outer_proposal",
            # events={
            #     "responseEnable": Event(
            #         is_triggered_by="trialStart",
            #         delay=waiting_time,
            #         js="onNextButton();",
            #     ),
            # },
            # progress_display=progress_display,
        )


class OuterAcceptancePage(ModularPage):

    def __init__(self, proposal: str) -> None:
        assert proposal in ["", "PROPOSER", "RESPONDER"]

        prompt = Prompt(
            f"Do you accept your partner's proposal of you to be the {proposal}? "
        )
        control = PushButtonControl(
            choices=["Accept", "Reject"],
            labels=["Accept", "Reject"],
        )
        progress_display = None
        waiting_time = MAX_WAITING_PROPOSALS

        super().__init__(
            label="outer_accept_answer",
            prompt=prompt,
            control=control,
            time_estimate=5,
            save_answer="outer_accept_answer",
            # events={
            #     "responseEnable": Event(
            #         is_triggered_by="trialStart",
            #         delay=waiting_time,
            #         js="onNextButton();",
            #     ),
            # },
            # progress_display=progress_display,
        )


class InnerProposalPage(ModularPage):
    def __init__(self, game:str):
        assert game in ["ultimatum", "dictator"], f"Error: {game} is not a valid game type"

        text = f"<h2>Proposal phase</h2>\n"
        text += f"<br>\n"
        if game == "ultimatum":
            text += "<p>Proposal accepted. You are the PROPOSER. </p>\n"
        text += f"<p>Decide how many of the {ENDOWMENT} coins you will give to your partner: <p/>\n"
        text += f"<br>\n"

        prompt = Markup(text)
        control = CustomSliderControl(
            start_value=0,
            min_value=0,
            max_value=ENDOWMENT,
            n_steps=ENDOWMENT,
            right_label="coins",
        )

        super().__init__(
            label="inner_proposal",
            prompt=prompt,
            control=control,
            time_estimate=5,
            save_answer="inner_proposal",
            # events={
            #     "responseEnable": Event(
            #         is_triggered_by="trialStart",
            #         delay=waiting_time,
            #         js="onNextButton();",
            #     ),
            # },
            # progress_display=progress_display,
        )


class InnerAcceptancePage(ModularPage):
    def __init__(self, proposal: int | None) -> None:

        prompt = Markup(
            f"<p>Do you accept your partner's proposal of {proposal} out of {ENDOWMENT}? </p>"
        )
        control = PushButtonControl(
            choices=["Accept", "Reject"],
            labels=["Accept", "Reject"],
        )

        super().__init__(
            label="inner_accept_answer",
            prompt=prompt,
            control=control,
            time_estimate=5,
            save_answer="inner_accept_answer",
            # events={
            #     "responseEnable": Event(
            #         is_triggered_by="trialStart",
            #         delay=waiting_time,
            #         js="onNextButton();",
            #     ),
            # },
            # progress_display=progress_display,
        )
