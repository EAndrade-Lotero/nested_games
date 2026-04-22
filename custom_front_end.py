# Module with custom prompts and controls

##########################################################################################
# Imports
##########################################################################################
from markupsafe import Markup
from typing import Dict, List, Optional, Union

from psynet.modular_page import Control, Prompt
from psynet.timeline import FailedValidation
from psynet.utils import get_logger, get_translator

from .game_paramters import (
    ENDOWMENT,
    NUMBER_OF_ROUNDS,
    MAX_TIMEOUT_ROUNDS,
)

logger = get_logger()

###########################################
# Custom prompts
###########################################

class ScorePrompt(Prompt):
    macro = "scores"
    external_template = "scores.html"

    def __init__(
        self,
        outer_game_type: str,
        inner_game_type: str,
        proposer: bool,
        proposal: int,
        remainder_: int,
        accumulated_score: int,
        partners_accumulated_score: int,
        timeout: int,
        outer_accepted: Optional[bool]=True,
        inner_accepted: Optional[bool]=True,
        round_failed: Optional[bool]=False,
        num_rounds_failed: Optional[int] = 0,
    ):
        super().__init__()
        self.timeoutSeconds = timeout
        self.timeoutAnswer = "No answer"
        self.my_score = int(accumulated_score)
        self.partner_score = int(partners_accumulated_score)

        if num_rounds_failed >= MAX_TIMEOUT_ROUNDS:
            self.text = f"""
                <p>Round finished with score 0 coins. </p>
                <p>Number of timeouts exceeded! Experiment failed! </p>
            """
        else:
            if round_failed:
                self.text = f"""
                    <p>Round failed! One of the participants timed out. Round finished with score 0 coins. </p>
                """
            else:
                if outer_game_type == "ultimatum" and not outer_accepted:
                    self.text = f"""
                        <p>Proposal was not accepted. Round finished with score 0 coins. </p>
                    """
                else:
                    if inner_game_type == "dictator":
                        self.text = f"""
                            <p>You have given {proposal} coins to your partner. </p>
                            <p>You keep the remainder of {remainder_} coins. </p>
                        """
                    elif inner_game_type == "ultimatum":
                        if inner_accepted:
                            if proposer:
                                self.text = f"""
                                    <p>You have proposed {proposal} coins to your partner. </p>
                                    <p>Your proposal was accepted. </p>
                                    <p>You keep the remainder of {remainder_} coins. </p>
                                """
                            else:
                                self.text = f"""
                                    <p>Your partner has proposed to give you {proposal} coins. </p>
                                    <p>You accepted this proposal. You keep these {proposal} coins. </p>
                                """
                        else:
                            self.text = f"""
                                <p>Proposal was not accepted. Round finished with score 0 coins. </p>
                            """
                    else:
                        raise ValueError(f"{inner_game_type} is not a valid inner game type.")


class OuterPrompt(Prompt):
    macro = ""
    external_template = ""

    def __init__(
        self,
        text:str,
        proposal:str,
        context:Dict[str, str],
        time_estimate:int,
        external_template:str,
        round_:int,
    ) -> None:
        super().__init__()
        self.text = text
        self.proposal = proposal
        self.coin_url = context["coin_url"]
        self.generic_url = context["generic_url"]
        self.plate_url = context["plate_url"]
        self.timeout = time_estimate
        self.macro = external_template.split(".")[0]
        self.external_template = external_template
        self.round = round_
        self.num_rounds = NUMBER_OF_ROUNDS


class InnerPrompt(OuterPrompt):

    def __init__(
        self,
        text:str,
        proposal:int,
        endowment:int,
        context:Dict[str, str],
        time_estimate:int,
        external_template:str,
        round_:int,
    ) -> None:
        super().__init__(
            text=text,
            proposal=str(proposal),
            context=context,
            time_estimate=time_estimate,
            external_template=external_template,
            round_=round_,
        )
        self.endowment = endowment


class TimeoutPrompt(Prompt):

    macro = "timeout"
    external_template = "custom-prompt-with-timer.html"

    def __init__(
        self,
        timeout:int,
        timeout_answer:str='No answer',
        text: Union[None, str, Markup] = None,
        text_align: str = "left",
        buttons: Optional[List] = None,
        loop: bool = False,
        round_:int = 1,
        num_rounds: int = 1,
        show_rounds: bool = True,
    ):
        super().__init__(
            text=text,
            text_align=text_align,
            buttons=buttons,
            loop=loop,
        )
        self.timeoutSeconds = timeout
        self.timeoutAnswer = timeout_answer
        self.round = round_
        self.num_rounds = num_rounds
        self.show_rounds = show_rounds

###########################################
# Custom controls
###########################################

class CustomControl(Control):
    macro = ""
    external_template = ""

    def __init__(
        self,
        external_template: str,
        proposal: Union[str, None] = None,
        accumulated_score_me: int = 0,
        accumulated_score_partner: int = 0,
        show_next: bool = True,
    ) -> None:
        super().__init__()
        self.macro = external_template.split(".")[0]
        self.external_template = external_template
        self.accumulated_score_me = int(accumulated_score_me)
        self.accumulated_score_partner = int(accumulated_score_partner)
        self.show_next = show_next
        self.proposal = proposal


class InnerProposalControl(Control):
    macro = "inner_proposal"
    external_template = "inner_proposal.html"

    def __init__(
        self,
        accumulated_score_me: int = 0,
        accumulated_score_partner: int = 0,
    ) -> None:
        super().__init__()

        # Assign attributes
        self.start_value = 0
        self.min_value = 0
        self.max_value = ENDOWMENT
        self.n_steps = ENDOWMENT
        self.use_percentage = False
        self.integer_rule = False
        self.endowment = ENDOWMENT
        self.accumulated_score_me = int(accumulated_score_me)
        self.accumulated_score_partner = int(accumulated_score_partner)
        self.show_next = False


class InnerControl(CustomControl):

    def __init__(
        self,
        value:int,
        context:Dict[str, str],
        time_estimate:int,
        external_template:str,
    ) -> None:
        super().__init__(
            context=context,
            time_estimate=time_estimate,
            external_template=external_template,
        )
        self.value = value


class CustomLikertControl(Control):
    macro = "likert"
    external_template = "likert.html"

    def __init__(
        self,
        lowest_value: str,
        highest_value: str,
        n_steps: int,
    ) -> None:
        super().__init__()
        self.lowest_value = lowest_value
        self.highest_value = highest_value
        self.n_steps = n_steps

    def format_answer(self, raw_answer, **kwargs):
        if raw_answer is None or raw_answer == "":
            return None
        try:
            if isinstance(raw_answer, str):
                assert raw_answer == "No answer"
                value = raw_answer
            else:
                value = int(raw_answer)
                if not (1 <= value <= self.n_steps):
                    return None
        except (TypeError, ValueError):
            return None
        return value

    def validate(self, response, **kwargs):
        if response.answer is None:
            _p = get_translator(context=True)
            return FailedValidation(
                _p(
                    "validation",
                    "Please select a value on the scale before continuing.",
                )
            )
        return None


class CustomSliderControl(Control):
    macro = "slider_values"
    external_template = "slider-control.html"

    def __init__(
        self,
            start_value: float,
            min_value: float,
            max_value: float,
            n_steps: int,
            use_percentage: Optional[bool] = False,
            left_label: Optional[str] = "",
            right_label: Optional[str] = "",
            integer_rule: Optional[bool] = False,
    ) -> None:
        super().__init__()

        # Sanity checks
        assert(min_value <= max_value), f"Error: min_value must be <= max_value (got {min_value} vs. {max_value})"
        assert(min_value <= start_value), f"Error: min_value must be <= start_value (got {min_value} vs. {start_value})"
        assert(start_value <= max_value), f"Error: start_value must be <= max_value (got {start_value} vs. {max_value})"
        assert(n_steps >= 1)
        if use_percentage:
            assert(min_value == 0)
            assert(max_value == 1)

        # Assign attributes
        self.start_value = start_value
        self.min_value = min_value
        self.max_value = max_value
        self.n_steps = n_steps
        self.use_percentage = use_percentage
        self.left_label = left_label
        self.right_label = right_label
        self.integer_rule = integer_rule

    def format_answer(self, raw_answer, **kwargs):
        try:
            return float(raw_answer)
        except (ValueError, AssertionError):
            return f"INVALID_RESPONSE"
###########################################
