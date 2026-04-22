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
    NUMBER_OF_ROUNDS,
)
from .custom_front_end import (
    OuterProposalControl,
    OuterPrompt,
    InnerProposalControl,
    InnerPrompt,
    ScorePrompt,
    TimeoutPrompt
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

    def __init__(
        self,
        time_estimate: int,
        accumulated_score_me: int = 0,
        accumulated_score_partner: int = 0,
        round_: int = 1,
    ) -> None:
        round_ = int(round_)
        prompt = TimeoutPrompt(
            timeout=TIMEOUT_PROPOSALS,
            round_=round_,
            num_rounds=NUMBER_OF_ROUNDS,
            text=Markup(
            f"<h3>Giving the endowment</h3>"
            f"<br>"
            f"<p>Drag and drop the coins onto one of the players: </p>"
        ))
        control = OuterProposalControl(
            accumulated_score_me=accumulated_score_me,
            accumulated_score_partner=accumulated_score_partner,
            external_template="outer_proposal.html",
            show_next=False,
        )
        super().__init__(
            label="outer_proposal",
            prompt=prompt,
            control=control,
            time_estimate=time_estimate,
            save_answer="outer_proposal",
            show_next_button=False,
        )

    def format_answer(self, raw_answer, **kwargs):
        metadata = kwargs.get("metadata") or {}
        participant = kwargs.get("participant")
        if participant is not None:
            event_log = metadata.get("event_log") or []
            if any(entry.get("eventType") == "done" for entry in event_log):
                participant.var.fail_me = True
                participant.var.num_rounds_failed += 1
        return super().format_answer(raw_answer, **kwargs)


class OuterWaitingPage(Page):

    def __init__(
        self,
        template_path:str,
        accumulated_score_me:int,
        accumulated_score_partner:int,
        round_:Optional[int]=1,
        content:Optional[str|None] = None,
        proposer:Optional[bool|None] = None,
        **kwargs
    ) -> None:
        if content is None:
            content = "Waiting for the other player..."
        self.content = content
        self.proposer = proposer
        self.accumulated_score_me = accumulated_score_me
        self.accumulated_score_partner = accumulated_score_partner
        self.round = round_
        self.num_rounds = NUMBER_OF_ROUNDS
        self.wait_time = WAIT_PAGE_TIME
        with open(template_path, "r") as file:
            template = file.read()
        super().__init__(
            label="wait",
            time_estimate=TIMEOUT_WAITING_FOR_OTHER,
            template_str=template,
            template_arg={
                "accumulated_score_me": int(self.accumulated_score_me),
                "accumulated_score_partner": int(self.accumulated_score_partner),
                "round": self.round,
                "num_rounds": self.num_rounds,
                "content": self.content,
                "proposer": self.proposer,
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

    def __init__(
        self,
        proposal: str,
        round_: int,
        time_estimate: int,
        accumulated_score_me: int = 0,
        accumulated_score_partner: int = 0,
    ) -> None:
        assert proposal in [None, "PROPOSER", "RESPONDER"]
        if proposal == "PROPOSER":
            recipient = "You have been given"
        elif proposal == "RESPONDER":
            recipient = "Your partner kept"
        else:
            recipient = None

        prompt = TimeoutPrompt(
            timeout=TIMEOUT_PROPOSALS,
            round_=round_,
            num_rounds=NUMBER_OF_ROUNDS,
            text=Markup(
            f"<h3>{recipient} the endowment</h3>"
            f"<br>"
            f"<p>Do you accept this allocation?</p>"
        ))
        control = OuterProposalControl(
            proposal=proposal,
            accumulated_score_me=accumulated_score_me,
            accumulated_score_partner=accumulated_score_partner,
            external_template="outer_acceptance.html",
            show_next=False,
        )

        super().__init__(
            label="outer_accept_answer",
            prompt=prompt,
            control=control,
            time_estimate=time_estimate,
            save_answer="outer_accept_answer",
            show_next_button=control.show_next,
        )

    def format_answer(self, raw_answer, **kwargs):
        metadata = kwargs.get("metadata") or {}
        participant = kwargs.get("participant")
        if participant is not None:
            event_log = metadata.get("event_log") or []
            if any(entry.get("eventType") == "done" for entry in event_log):
                participant.var.fail_me = True
                participant.var.num_rounds_failed += 1
        return super().format_answer(raw_answer, **kwargs)


class InnerProposalPage(ModularPage):

    def __init__(
        self,
        outer_game:str,
        round_: int,
        time_estimate: int,
        accumulated_score_me: int = 0,
        accumulated_score_partner: int = 0,
    ) -> None:
        assert outer_game in ["ultimatum", "dictator"], f"Error: {outer_game} is not a valid game type"

        text = f"<h3>Giving coins</h3>"
        text += f"<p>"

        if outer_game == "ultimatum":
            text += f"Proposal accepted. "

        text += f"Use the slider below to decide how many coins you will give "
        text += f"to your partner, then press <strong>Make the offer</strong> when you are ready. <p/>"

        round_ = int(round_)
        prompt = TimeoutPrompt(
            timeout=TIMEOUT_PROPOSALS,
            round_=round_,
            num_rounds=NUMBER_OF_ROUNDS,
            text=Markup(text)
        )
        control = InnerProposalControl(
            accumulated_score_me=accumulated_score_me,
            accumulated_score_partner=accumulated_score_partner,
        )
        super().__init__(
            label="inner_proposal",
            prompt=prompt,
            control=control,
            time_estimate=time_estimate,
            save_answer="inner_proposal",
            show_next_button=False,
        )

    def format_answer(self, raw_answer, **kwargs):
        metadata = kwargs.get("metadata") or {}
        participant = kwargs.get("participant")
        if participant is not None:
            event_log = metadata.get("event_log") or []
            if any(entry.get("eventType") == "done" for entry in event_log):
                participant.var.fail_me = True
                participant.var.num_rounds_failed += 1
        return super().format_answer(raw_answer, **kwargs)


class InnerWaitingPage(Page):

    def __init__(
        self,
        template_path:str,
        accumulated_score_me:int,
        accumulated_score_partner:int,
        round_:Optional[int]=1,
        content:Optional[str|None] = None,
        proposer:Optional[bool|None] = None,
        **kwargs
    ) -> None:
        if content is None:
            content = "Waiting for the other player..."
        self.content = content
        self.proposer = proposer
        self.accumulated_score_me = accumulated_score_me
        self.accumulated_score_partner = accumulated_score_partner
        self.round = round_
        self.num_rounds = NUMBER_OF_ROUNDS
        self.wait_time = WAIT_PAGE_TIME
        with open(template_path, "r") as file:
            template = file.read()
        super().__init__(
            label="wait",
            time_estimate=TIMEOUT_WAITING_FOR_OTHER,
            template_str=template,
            template_arg={
                "accumulated_score_me": int(self.accumulated_score_me),
                "accumulated_score_partner": int(self.accumulated_score_partner),
                "round": self.round,
                "num_rounds": self.num_rounds,
                "content": self.content,
                "proposer": self.proposer,
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


class InnerAcceptancePage(ModularPage):

    def __init__(
        self,
        context: Dict[str, str],
        proposal: int,
        round_: int,
    ) -> None:

        prompt = InnerPrompt(
            text=(
                f"<p>Do you accept your partner's proposal of {proposal} coins? </p>"
            ),
            proposal=proposal,
            endowment=ENDOWMENT,
            context=context,
            time_estimate=TIMEOUT_PROPOSALS,
            external_template="inner_acceptance.html",
            round_=round_,
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
            time_estimate=TIMEOUT_PROPOSALS,
            save_answer="inner_accept_answer",
        )


class ScorePage(EndRoundPage):

    def __init__(
        self,
        outer_game_type: str,
        inner_game_type: str,
        proposer: bool,
        proposal: int,
        remainder_: int,
        accumulated_score: int,
        partners_accumulated_score: int,
        outer_accepted: Optional[bool] = True,
        inner_accepted: Optional[bool] = True,
        round_failed: Optional[bool] = False,
        num_rounds_failed:Optional[int] = 0,
    ) -> None:

        if proposer:
            score = remainder_
        else:
            score = proposal
        self.score = score

        prompt = ScorePrompt(
            outer_game_type=outer_game_type,
            inner_game_type=inner_game_type,
            proposer=proposer,
            proposal=proposal,
            remainder_=remainder_,
            accumulated_score=accumulated_score,
            partners_accumulated_score=partners_accumulated_score,
            timeout=TIMEOUT_WAITING_FOR_OTHER,
            outer_accepted=outer_accepted,
            inner_accepted=inner_accepted,
            round_failed=round_failed,
            num_rounds_failed=num_rounds_failed,
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
        )

    def format_answer(self, raw_answer, **kwargs):
        if self.score == "No answer" or self.score is None:
            return 0
        return int(self.score)




