import json
from pathlib import Path
from markupsafe import Markup
from typing import Optional, Dict, Union

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
    TIMEOUT_PROPOSALS,
    WAIT_PAGE_TIME,
    TIMEOUT_WAITING_FOR_OTHER,
)
from .custom_front_end import (
    CustomControl,
    OuterPrompt,
    InnerProposalControl,
    InnerPrompt,
    ScorePrompt,
)
from .custom_timeline import EndRoundPage


logger = get_logger()

_CUSTOM_INFO_TEMPLATE = Path(__file__).resolve().parent / "templates" / "custom_info_page.html"


class CustomInfoPage(Page):
    """
    Like ``InfoPage``: shows HTML/text and PsyNet's normal Next control, but also
    shows a countdown and calls ``psynet.nextPage()`` when it reaches zero.
    """

    def __init__(
        self,
        text: Union[str, Markup],
        *,
        time_estimate: int = 30,
        label: str = "custom_info",
        **kwargs,
    ) -> None:
        body = text if isinstance(text, Markup) else Markup(str(text))
        self._countdown_seconds = int(time_estimate)
        with open(_CUSTOM_INFO_TEMPLATE, "r", encoding="utf-8") as f:
            template_str = f.read()
        super().__init__(
            label=label,
            time_estimate=time_estimate,
            template_str=template_str,
            template_arg={
                "body": body,
                "timeout": self._countdown_seconds,
            },
            **kwargs,
        )

    def get_bot_response(self, experiment, bot):
        return None


class OuterProposalPage(ModularPage):

    def __init__(self, context: Dict[str, str], round_: int) -> None:
        prompt = Prompt(Markup(
            f"<h2>Preparation phase</h2>"
            f"<br>"
            f"<p>Choose who will take on the role of PROPOSER: </p>"
            f"<p>When you are ready, press the 'Next' button (scroll down the page if necessary). </p>"
            f"<p>(If you don't press the 'Next' button within {TIMEOUT_PROPOSALS} seconds, a random choice will be made for you). </p>"
        ))
        control = CustomControl(
            context=context,
            time_estimate=5,
            # time_estimate=TIMEOUT_PROPOSALS,
            external_template="outer_proposal.html",
            round_=round_
        )
        super().__init__(
            label="outer_proposal",
            prompt=prompt,
            control=control,
            time_estimate=TIMEOUT_PROPOSALS,
            save_answer="outer_proposal",
            events={
                "done": Event(
                    is_triggered_by="done",
                ),
            },
        )

    def format_answer(self, raw_answer, **kwargs):
        metadata = kwargs.get("metadata") or {}
        participant = kwargs.get("participant")
        if participant is not None:
            event_log = metadata.get("event_log") or []
            if any(entry.get("eventType") == "done" for entry in event_log):
                participant.var.set("fail_me", True)
        return super().format_answer(raw_answer, **kwargs)


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
            time_estimate=TIMEOUT_PROPOSALS,
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
            text=(
                f"<p>Do you accept your partner's proposal of you to be the {proposal}? </p>"
                f"<p>When you are ready, press the 'Next' button (scroll down the page if necessary). </p>"
                f"<p>(If you don't press the 'Next' button within {TIMEOUT_PROPOSALS} seconds, a random choice will be made for you). </p>"
            ),
            proposal=proposal,
            context=context,
            time_estimate=TIMEOUT_PROPOSALS,
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
        )


class InnerProposalPage(ModularPage):

    def __init__(self, game:str, context: Dict[str, str]):
        assert game in ["ultimatum", "dictator"], f"Error: {game} is not a valid game type"

        text = f"<h2>Proposal phase</h2>"
        text += f"<br>"

        if game == "ultimatum":
            text += f"<p>Proposal accepted. You are the PROPOSER. </p>"

        text += f"<p>Use the slider below to decide how many of the {ENDOWMENT} coins you will give to your partner: <p/>"
        text += f"<p>(Scroll down the page if necessary.)</p>"
        text += f"<p>(If you don't press the 'Next' button within {TIMEOUT_PROPOSALS} seconds, a random choice will be made for you). </p>"
        text += f"<br>"

        prompt = Markup(text)
        control = InnerProposalControl(
            endowment=ENDOWMENT,
            context=context,
            time_estimate=TIMEOUT_PROPOSALS,
        )
        super().__init__(
            label="inner_proposal",
            prompt=prompt,
            control=control,
            time_estimate=5,
            save_answer="inner_proposal",
        )


class InnerAcceptancePage(ModularPage):

    def __init__(self, context: Dict[str, str], proposal: int) -> None:

        prompt = InnerPrompt(
            text=(
                f"<p>Do you accept your partner's proposal of {proposal} coins? </p>"
                f"<p>(If you don't press the 'Next' button within {TIMEOUT_PROPOSALS} seconds, a random choice will be made for you.)</p>"
            ),
            proposal=proposal,
            endowment=ENDOWMENT,
            context=context,
            time_estimate=TIMEOUT_PROPOSALS,
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
        )


class ScorePage(EndRoundPage):

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
            time_estimate=TIMEOUT_WAITING_FOR_OTHER,
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



