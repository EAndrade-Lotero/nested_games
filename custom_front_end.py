# Module with custom prompts and controls

##########################################################################################
# Imports
##########################################################################################

from typing import Dict

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
            proposal=proposal,
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

###########################################
