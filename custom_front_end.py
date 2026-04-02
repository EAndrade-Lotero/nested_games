# Module with custom prompts and controls

##########################################################################################
# Imports
##########################################################################################

from typing import Dict, Optional

from psynet.modular_page import (
    Control, Prompt,
)
from psynet.utils import get_logger

from .game_paramters import ENDOWMENT


logger = get_logger()

###########################################
# Custom prompts
###########################################

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
