# Module with custom prompts and controls

##########################################################################################
# Imports
##########################################################################################

from typing import Dict, Literal, Optional, Union

from psynet.modular_page import (
    Control, Prompt,
)
from psynet.timeline import FailedValidation
from psynet.utils import get_logger, get_translator

from .game_paramters import ENDOWMENT


logger = get_logger()

###########################################
# Custom prompts
###########################################

class ScorePrompt(Prompt):
    macro = "scores"
    external_template = "scores.html"

    def __init__(
        self,
        proposer: bool,
        proposal: int,
        remainder_: int,
        accumulated_score: int,
        partners_accumulated_score: int,
        time_estimate: int,
        accepted: Optional[bool]=True,
    ):
        super().__init__()
        self.timeout = time_estimate
        self.my_score = int(accumulated_score)
        self.partner_score = int(partners_accumulated_score)

        if accepted:
            if proposer:
                self.text = f"""
                    <p>You have given {proposal} coins to your partner. </p>
                    <p>You keep the remainder of {remainder_} coins. </p>
                """
            else:
                self.text = f"""
                    <p>Your partner has given you {proposal} coins. </p>
                """
        else:
            self.text = f"""
                <p>Proposal was not accepted. Round finished with score 0 coins. </p>
            """


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


class InnerPrompt(OuterPrompt):

    def __init__(
        self,
        text:str,
        proposal:int,
        endowment:int,
        context:Dict[str, str],
        time_estimate:int,
        external_template:str,
    ) -> None:
        super().__init__(
            text=text,
            proposal=str(proposal),
            context=context,
            time_estimate=time_estimate,
            external_template=external_template,
        )
        self.endowment = endowment


###########################################
# Custom controls
###########################################

class CustomControl(Control):
    macro = ""
    external_template = ""

    def __init__(
        self,
        context:Dict[str, str],
        time_estimate:int,
        external_template:str,
    ) -> None:
        super().__init__()
        self.coin_url = context["coin_url"]
        self.generic_url = context["generic_url"]
        self.plate_url = context["plate_url"]
        self.timeout = time_estimate
        self.macro = external_template.split(".")[0]
        self.external_template = external_template


class InnerProposalControl(Control):
    macro = "inner_proposal"
    external_template = "inner_proposal.html"

    def __init__(
        self,
        endowment:int,
        context: Dict[str, str],
        time_estimate: int,
    ) -> None:
        super().__init__()

        # Assign attributes
        self.start_value = 0
        self.min_value = 0
        self.max_value = ENDOWMENT
        self.n_steps = ENDOWMENT
        self.use_percentage = False
        self.integer_rule = False
        self.endowment = endowment
        self.coin_url = context["coin_url"]
        self.generic_url = context["generic_url"]
        self.plate_url = context["plate_url"]
        self.timeout = time_estimate


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


LikertTimeoutAnswer = Union[Literal["random"], Literal["None"], int]


class CustomLikertControl(Control):
    macro = "likert"
    external_template = "likert.html"

    def __init__(
        self,
        lowest_value: str,
        highest_value: str,
        n_steps: int,
        timeout: Optional[int] = None,
        timeout_answer: LikertTimeoutAnswer = "random",
    ) -> None:
        super().__init__()
        self.lowest_value = lowest_value
        self.highest_value = highest_value
        self.n_steps = n_steps
        if timeout is not None and int(timeout) > 0:
            self.timer_enabled = True
            self.timeout = int(timeout)
        else:
            self.timer_enabled = False
            self.timeout = 0

        if isinstance(timeout_answer, bool):
            raise ValueError("timeout_answer must not be a boolean")
        if isinstance(timeout_answer, int):
            if not (1 <= timeout_answer <= n_steps):
                raise ValueError(
                    f"timeout_answer int must be between 1 and n_steps ({n_steps}), got {timeout_answer!r}"
                )
            self.timeout_answer_mode = "fixed"
            self.timeout_answer_fixed = int(timeout_answer)
        elif timeout_answer == "random":
            self.timeout_answer_mode = "random"
            self.timeout_answer_fixed = 0
        elif timeout_answer == "None":
            self.timeout_answer_mode = "none"
            self.timeout_answer_fixed = 0
        else:
            raise ValueError(
                "timeout_answer must be 'random', 'None', or an int from 1 to n_steps"
            )

    def format_answer(self, raw_answer, **kwargs):
        if raw_answer is None or raw_answer == "":
            return None
        try:
            value = int(raw_answer)
        except (TypeError, ValueError):
            return None
        if not (1 <= value <= self.n_steps):
            return None
        return value

    def validate(self, response, **kwargs):
        if response.answer is None:
            if self.timeout_answer_mode == "none":
                return None
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
