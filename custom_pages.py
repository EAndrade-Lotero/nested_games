import json
from markupsafe import Markup
from typing import Optional, Dict

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
    WAIT_PAGE_TIME,
    MAX_WAITING_SEEING_INFO,
    RNG,
)
from .custom_front_end import (
    CustomControl,
    OuterPrompt,
    InnerProposalControl,
    InnerPrompt,
    ScorePrompt,
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
                    js=(
                        "psynet.response.disable(); psynet.submit.disable(); "
                        f"psynet.nextPage({json.dumps(RNG.choice(['self', 'other']))});"
                    ),
                    delay=0.0,
                ),
            },
        )


class CustomWaitingPage(Page):

    def __init__(
        self,
        template_path:str,
        content:Optional[str|None] = None,
        proposer:Optional[bool|None] = None,
        n_coins:Optional[int] = 0,
        **kwargs
    ) -> None:
        if content is None:
            content = "Waiting for the other player..."
        self.content = content
        self.proposer = proposer
        self.n_coins = n_coins
        self.endowment = ENDOWMENT
        self.wait_time = WAIT_PAGE_TIME
        with open(template_path, "r") as file:
            template = file.read()
        super().__init__(
            label="wait",
            time_estimate=MAX_WAITING_PROPOSALS,
            template_str=template,
            template_arg={
                "content": self.content,
                "proposer": self.proposer,
                "n_coins": self.n_coins,
                "endowment": self.endowment,
                "wait_time": self.wait_time,
            },
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
        assert proposal in [None, "PROPOSER", "RESPONDER"]

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
                    js=(
                        "psynet.response.disable(); psynet.submit.disable(); "
                        f"psynet.nextPage({json.dumps(RNG.choice([True, False]))});"
                    ),
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
        text += f"<p>(Scroll down the page if necessary.)</p>\n"
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
                    js=(
                        "psynet.response.disable(); psynet.submit.disable(); "
                        f"psynet.nextPage({json.dumps(0)});"
                    ),
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
                    js=(
                        "psynet.response.disable(); psynet.submit.disable(); "
                        f"psynet.nextPage({json.dumps(RNG.choice([True, False]))});"
                    ),
                    delay=0.0,
                ),
            },
        )


class ScorePage(ModularPage):

    def __init__(
        self,
        proposer: bool,
        proposal: int,
        remainder_: int,
        accumulated_score: int,
        partners_accumulated_score: int,
        accepted: Optional[bool] = True,
    ) -> None:

        if proposer:
            score = remainder_
        else:
            score = proposal

        prompt = ScorePrompt(
            proposer=proposer,
            proposal=proposal,
            remainder_=remainder_,
            accumulated_score=accumulated_score,
            partners_accumulated_score=partners_accumulated_score,
            time_estimate=MAX_WAITING_SEEING_INFO,
            accepted=accepted,
        )

        super().__init__(
            label="reward",
            prompt=prompt,
            control=PushButtonControl(
                labels=["Next"],
                choices=[score],
            ),
            time_estimate=5,
            save_answer="reward",
            events={
                "done": Event(
                    is_triggered_by="done",
                    js=(
                        "psynet.response.disable(); psynet.submit.disable(); "
                        f"psynet.nextPage({json.dumps(score)});"
                    ),
                    delay=0.0,
                ),
            },
        )



