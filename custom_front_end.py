# Module with custom prompts and controls

##########################################################################################
# Imports
##########################################################################################
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from psynet.modular_page import (
    Control,
)
from psynet.utils import get_logger


logger = get_logger()
Pos = Tuple[int, int]  # (x, y)

###########################################
# Custom prompts
###########################################


###########################################
# Custom controls
###########################################

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


class OuterGameControl(Control):
    macro = "outer_proposal"
    external_template = "outer_proposal.html"

    def __init__(self, context:Dict[str, str], timeout:int) -> None:
        super().__init__()
        self.coin_url = context["coin_url"]
        self.generic_url = context["generic_url"]
        self.plate_url = context["plate_url"]
        self.timeout = timeout

###########################################
