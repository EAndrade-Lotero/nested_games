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
)

logger = get_logger()

###########################################
# Custom prompts
###########################################

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

class OuterProposalControl(Control):
    macro = ""
    external_template = ""

    def __init__(
        self,
        external_template: str,
        proposal: Union[str, None] = None,
        accumulated_score_me: int = 0,
        accumulated_score_partner: int = 0,
        round_: Optional[int] = 1,
        show_next: bool = True,
    ) -> None:
        super().__init__()
        self.macro = external_template.split(".")[0]
        self.external_template = external_template
        self.accumulated_score_me = int(accumulated_score_me)
        self.accumulated_score_partner = int(accumulated_score_partner)
        self.show_next = show_next
        self.proposal = proposal
        self.round = round_


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


class InnerAcceptanceControl(Control):
    macro = "inner_acceptance"
    external_template = "inner_acceptance.html"

    def __init__(
        self,
        proposal: Union[int, None] = None,
        accumulated_score_me: int = 0,
        accumulated_score_partner: int = 0,
    ) -> None:
        super().__init__()

        # Assign attributes
        self.proposal = proposal
        self.endowment = ENDOWMENT
        self.accumulated_score_me = int(accumulated_score_me)
        self.accumulated_score_partner = int(accumulated_score_partner)
        self.show_next = False


class ScoreControl(Control):
    macro = "scores"
    external_template = "scores.html"

    def __init__(
        self,
        content: str,
        accumulated_score_me: int = 0,
        accumulated_score_partner: int = 0,
    ):
        super().__init__()
        self.content = content
        self.accumulated_score_me = int(accumulated_score_me)
        self.accumulated_score_partner = int(accumulated_score_partner)


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
