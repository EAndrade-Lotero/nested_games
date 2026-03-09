from typing import Optional, List

from psynet.modular_page import Control


class MultiTextControl(Control):
    """
    Control with a configurable number of text inputs (like TextControl but multiple fields).
    The answer is a list of strings, one per input, in order.
    """

    macro = "multi_text"
    external_template = "multi-text-control.html"

    def __init__(
            self,
            num_inputs: int,
            labels: Optional[List[str]] = None,
            one_line: bool = True,
            width: Optional[str] = None,
            **kwargs,
    ):
        super().__init__(**kwargs)
        if num_inputs < 1:
            raise ValueError("num_inputs must be at least 1")
        self.num_inputs = num_inputs
        self.labels = labels  # optional list of length num_inputs
        self.one_line = one_line
        self.width = width

    @property
    def metadata(self):
        return {
            "num_inputs": self.num_inputs,
            "labels": self.labels,
            "one_line": self.one_line,
            "width": self.width,
        }

    def get_bot_response(self, experiment, bot, page, prompt):
        return [f"Bot response {i + 1}" for i in range(self.num_inputs)]
