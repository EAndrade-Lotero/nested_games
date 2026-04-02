from markupsafe import Markup
from typing import Union, Dict

from psynet.graphics import Prompt
from psynet.modular_page import (
    ModularPage,
    PushButtonControl,
    NullControl,
)
from psynet.timeline import (
    Page,
    Event,
)
from psynet.utils import get_logger

from .game_paramters import (
    ENDOWMENT,
    MAX_WAITING_PROPOSALS,
    MAX_WAITING_FOR_OTHER,
)
from .custom_front_end import (
    CustomControl,
    OuterPrompt,
    InnerProposalControl,
    InnerControl,
    InnerPrompt,
)


logger = get_logger()


class OuterProposalPage(ModularPage):

    def __init__(self, context: Dict[str, str]) -> None:
        prompt = Prompt(Markup(
            f"<h2>Preparation phase</h2>"
            f"<br>"
            f"<p>Choose who will take on the role of PROPOSER: </p>"
            f"<p>When you are ready, press the 'Next' button (scroll down the page if necessary). </p>"
        ))
        control = CustomControl(
            context=context,
            time_estimate=MAX_WAITING_PROPOSALS,
            external_template="outer_proposal.html",
        )
        super().__init__(
            label="outer_proposal",
            prompt=prompt,
            control=control,
            time_estimate=MAX_WAITING_PROPOSALS,
            save_answer="outer_proposal",
            events={
                "done": Event(
                    is_triggered_by="done",
                    js="psynet.submitResponse();",
                    delay=0.0,
                ),
            },
        )


class OuterProposalWaitingPage(Page):

    def __init__(
        self,
        content: str,
        wait_time: float,
        template_path:str,
        **kwargs
    ) -> None:
        self.content = content
        assert wait_time >= 0
        self.wait_time = wait_time
        with open(template_path, "r") as file:
            template = file.read()
        super().__init__(
            label="wait",
            time_estimate=wait_time,
            template_str=template,
            template_arg={"content": self.content, "wait_time": self.wait_time},
            **kwargs,
        )

    def metadata(self, **kwargs):
        return {"wait_time": self.wait_time}

    def get_bot_response(self, experiment, bot):
        return None

    def on_complete(self, experiment, participant):
        participant.total_wait_page_time += self.wait_time
        super().on_complete(experiment, participant)


class OuterAcceptancePage(ModularPage):

    def __init__(self, context: Dict[str, str], proposal: str) -> None:
        assert proposal in ["", "PROPOSER", "RESPONDER"]

        prompt = OuterPrompt(
            text=f"Do you accept your partner's proposal of you to be the {proposal}? ",
            proposal=proposal,
            context=context,
            time_estimate=MAX_WAITING_PROPOSALS,
            external_template="outer_acceptance.html",
        )
        control = PushButtonControl(
            choices=["Accept", "Reject"],
            labels=["Accept", "Reject"],
            arrange_vertically=False,
        )

        super().__init__(
            label="outer_accept_answer",
            prompt=prompt,
            control=control,
            time_estimate=5,
            save_answer="outer_accept_answer",
            events={
                "done": Event(
                    is_triggered_by="done",
                    js="psynet.submitResponse();",
                    delay=0.0,
                ),
            },
        )


class InnerProposalPage(ModularPage):

    def __init__(self, game:str, context: Dict[str, str]):
        assert game in ["ultimatum", "dictator"], f"Error: {game} is not a valid game type"

        text = f"<h2>Proposal phase</h2>\n"
        text += f"<br>\n"
        if game == "ultimatum":
            text += "<p>Proposal accepted. You are the PROPOSER. </p>\n"
        text += f"<p>Use the slider below to decide how many of the {ENDOWMENT} coins you will give to your partner: <p/>\n"
        text += f"<br>\n"

        prompt = Markup(text)
        control = InnerProposalControl(
            endowment=ENDOWMENT,
            context=context,
            time_estimate=MAX_WAITING_PROPOSALS,
        )

        super().__init__(
            label="inner_proposal",
            prompt=prompt,
            control=control,
            time_estimate=5,
            save_answer="inner_proposal",
            events={
                "done": Event(
                    is_triggered_by="done",
                    js="psynet.submitResponse();",
                    delay=0.0,
                ),
            },
        )


class InnerProposalWaitingPage(ModularPage):

    def __init__(self, context: Dict[str, str]) -> None:
        prompt = Prompt(Markup(
            f"<h2>Proposal phase</h2>"
            f"<br>"
            "<p>Waiting for your partner's offer. </p>"
        ))
        control = CustomControl(
            context=context,
            time_estimate=MAX_WAITING_PROPOSALS,
            external_template="inner_wait.html",
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


class InnerAcceptancePage(ModularPage):

    def __init__(self, context: Dict[str, str], proposal: int) -> None:

        prompt = InnerPrompt(
            text=f"<p>Do you accept your partner's proposal of {proposal} coins? </p>",
            proposal=proposal,
            endowment=ENDOWMENT,
            context=context,
            time_estimate=MAX_WAITING_PROPOSALS,
            external_template="inner_acceptance.html",
        )
        control = PushButtonControl(
            choices=["Accept", "Reject"],
            labels=["Accept", "Reject"],
            arrange_vertically=False,
        )

        super().__init__(
            label="inner_accept_answer",
            prompt=prompt,
            control=control,
            time_estimate=5,
            save_answer="inner_accept_answer",
            events={
                "done": Event(
                    is_triggered_by="done",
                    js="psynet.submitResponse();",
                    delay=0.0,
                ),
            },
        )
