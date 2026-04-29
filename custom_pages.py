from pathlib import Path
from markupsafe import Markup
from typing import Optional, Dict, Union

from psynet.modular_page import ModularPage
from psynet.timeline import Page
from psynet.utils import get_logger

from .game_paramters import (
    STANDARD_TIMEOUT,
    WAIT_PAGE_TIME,
    NUMBER_OF_ROUNDS,
    MAX_TIMEOUT_ROUNDS,
    ENDOWMENT,
    TIME_ESTIMATE_FOR_COMPENSATION,
)
from .custom_front_end import (
    OuterProposalControl,
    InnerProposalControl,
    InnerAcceptanceControl,
    ScoreControl,
    TimeoutPrompt,
)
from .custom_timeline import EndRoundPage


logger = get_logger()


class OuterProposalPage(ModularPage):

    def __init__(
            self,
            time_estimate: int=TIME_ESTIMATE_FOR_COMPENSATION,
            accumulated_score_me: int = 0,
            accumulated_score_partner: int = 0,
            round_: int = 1,
        ) -> None:
        round_ = int(round_)
        prompt = TimeoutPrompt(
            timeout=STANDARD_TIMEOUT,
            round_=round_,
            num_rounds=NUMBER_OF_ROUNDS,
            text=Markup(
            f"<h3>Who gets the bag of coins?</h3>"
            f"<br>"
            f"<p>Drag and drop the bag of coins onto one of the players: </p>"
        ))
        control = OuterProposalControl(
            accumulated_score_me=accumulated_score_me,
            accumulated_score_partner=accumulated_score_partner,
            external_template="outer_proposal.html",
            round_=round_,
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
            time_estimate=TIME_ESTIMATE_FOR_COMPENSATION,
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
            time_estimate: int=TIME_ESTIMATE_FOR_COMPENSATION,
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
            timeout=STANDARD_TIMEOUT,
            round_=round_,
            num_rounds=NUMBER_OF_ROUNDS,
            text=Markup(
            f"<h3>{recipient} the bag of coins</h3>"
            f"<br>"
            f"<p>Do you accept this allocation?</p>"
        ))
        control = OuterProposalControl(
            proposal=proposal,
            accumulated_score_me=accumulated_score_me,
            accumulated_score_partner=accumulated_score_partner,
            external_template="outer_acceptance.html",
            round_=round_,
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
            time_estimate: int=TIME_ESTIMATE_FOR_COMPENSATION,
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
            timeout=STANDARD_TIMEOUT,
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
            proposal:int,
            round_:Optional[int]=1,
            content:Optional[str|None] = None,
            proposer:Optional[bool|None] = None,
            **kwargs
        ) -> None:
        if content is None:
            content = "Waiting for the other player..."
        self.content = content
        self.proposer = proposer
        self.proposal = proposal
        self.accumulated_score_me = accumulated_score_me
        self.accumulated_score_partner = accumulated_score_partner
        self.round = round_
        self.num_rounds = NUMBER_OF_ROUNDS
        self.wait_time = WAIT_PAGE_TIME
        with open(template_path, "r") as file:
            template = file.read()
        super().__init__(
            label="wait",
            time_estimate=TIME_ESTIMATE_FOR_COMPENSATION,
            template_str=template,
            template_arg={
                "accumulated_score_me": int(self.accumulated_score_me),
                "accumulated_score_partner": int(self.accumulated_score_partner),
                "round": self.round,
                "num_rounds": self.num_rounds,
                "content": self.content,
                "proposer": self.proposer,
                "proposal": self.proposal,
                "wait_time": self.wait_time,
                "endowment": ENDOWMENT,
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
            proposal: int,
            round_: int,
            time_estimate: int=TIME_ESTIMATE_FOR_COMPENSATION,
            accumulated_score_me: int = 0,
            accumulated_score_partner: int = 0,
        ) -> None:
        text = Markup("")
        if proposal is not None:
            if proposal == "No answer":
                return
            if proposal == 0:
                text=Markup(
                    f"<h3>No coins have been offered to you.</h3>"
                    f"<p>Do you accept this offer?</p>"
                )
            elif proposal > 0:
                text=Markup(
                    f"<h3>You have been offered {proposal} coins.</h3>"
                    f"<p>Do you accept this offer?</p>"
                )
            else:
                text=Markup("")

        prompt = TimeoutPrompt(
            timeout=STANDARD_TIMEOUT,
            round_=round_,
            num_rounds=NUMBER_OF_ROUNDS,
            text=Markup(text)
        )
        control = InnerAcceptanceControl(
            proposal=proposal,
            accumulated_score_me=accumulated_score_me,
            accumulated_score_partner=accumulated_score_partner,
        )
        super().__init__(
            label="inner_accept_answer",
            prompt=prompt,
            control=control,
            time_estimate=time_estimate,
            save_answer="inner_accept_answer",
            show_next_button=control.show_next,
        )


class ScorePage(EndRoundPage):

    def __init__(
            self,
            outer_game_type: str,
            inner_game_type: str,
            proposer: bool,
            proposal: int,
            remainder_: int,
            round_: int,
            accumulated_score_me: int = 0,
            accumulated_score_partner: int = 0,
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

        if num_rounds_failed >= MAX_TIMEOUT_ROUNDS:
            text = f"""
                <p>Round finished with score 0 coins. </p>
                <p>Number of timeouts exceeded! Experiment failed! </p>
            """
        else:
            if round_failed:
                text = f"""
                    <p>Round failed! One of the participants timed out. Round finished with score 0 coins. </p>
                    <p>Participants have timed out {num_rounds_failed} round{"s" if num_rounds_failed > 1 else ""}. </p>
                    <p>If participants timeout more than {MAX_TIMEOUT_ROUNDS} round{"s" if MAX_TIMEOUT_ROUNDS > 1 else ""}, the experiment will fail.</p>
                """
            else:
                if outer_game_type == "ultimatum" and not outer_accepted:
                    text = f"""
                        <p>Proposal was not accepted. Round finished with score 0 coins. </p>
                    """
                else:
                    if inner_game_type == "dictator":
                        text = f"""
                            <p>You have given {proposal} coins to your partner. </p>
                            <p>You keep the remaining {remainder_} coins. </p>
                        """
                    elif inner_game_type == "ultimatum":
                        if inner_accepted:
                            if proposer:
                                text = f"""
                                    <p>You have proposed {proposal} coins to your partner. </p>
                                    <p>Your proposal was accepted. </p>
                                    <p>You keep the remaining {remainder_} coins. </p>
                                """
                            else:
                                text = f"""
                                    <p>Your partner has proposed to give you {proposal} coins. </p>
                                    <p>You accepted this proposal. You keep these {proposal} coins. </p>
                                """
                        else:
                            text = f"""
                                <p>Proposal was not accepted. Round finished with score 0 coins. </p>
                            """
                    else:
                        raise ValueError(f"{inner_game_type} is not a valid inner game type.")

        prompt = TimeoutPrompt(
            timeout=STANDARD_TIMEOUT,
            round_=round_,
            num_rounds=NUMBER_OF_ROUNDS,
            text="",
        )
        control = ScoreControl(
            content=text,
            accumulated_score_me=accumulated_score_me,
            accumulated_score_partner=accumulated_score_partner,
        )

        super().__init__(
            label="reward",
            prompt=prompt,
            control=control,
            time_estimate=TIME_ESTIMATE_FOR_COMPENSATION,
            save_answer="reward",
            show_next_button=False,
        )

    def format_answer(self, raw_answer, **kwargs):
        if self.score == "No answer" or self.score is None:
            return 0
        return int(self.score)




