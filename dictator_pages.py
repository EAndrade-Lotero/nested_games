from typing import Union

from psynet.graphics import Prompt
from psynet.modular_page import (
    ModularPage,
    PushButtonControl,
    NumberControl,
    NullControl,
)
from psynet.timeline import (
    FailedValidation,
    Event,
    ProgressDisplay,
    ProgressStage,
)
from psynet.utils import get_logger

from .game_paramters import (
    CURRENCY,
    ENDOWMENT,
    MAX_WAITING_PROPOSALS,
    MAX_WAITING_FOR_OTHER,
    MAX_WAITING_SEEING_INFO,
)
from .custom_front_end import CustomSliderControl


logger = get_logger()


class OuterDictatorProposalPage(ModularPage):
    def __init__(
            self,
            proposer: bool,
    ) -> None:

        if proposer:
            prompt = Prompt(
                f"Choose who will take on the role of PROPOSER: "
            )
            control = PushButtonControl(
                labels=["Myself", "My partner"],
                choices=["self", "other"],
            )
            progress_display = None
            waiting_time = MAX_WAITING_PROPOSALS
        else:
            prompt = Prompt(
                "Click 'Next' to see which player your partner selects as PROPOSER."
            )
            control = NullControl()
            waiting_time = MAX_WAITING_FOR_OTHER
            progress_display = ProgressDisplay(
                stages=[
                    ProgressStage(
                        time=waiting_time,
                        color="gray"
                    ),
                ],
            )

        super().__init__(
            label="outer_proposal",
            prompt=prompt,
            control=control,
            time_estimate=5,
            save_answer="outer_proposal",
            events={
                "responseEnable": Event(
                    is_triggered_by="trialStart",
                    delay=waiting_time,
                    js="onNextButton();",
                ),
            },
            progress_display=progress_display,
        )


class InnerProposalPageOuterDictator(ModularPage):
    def __init__(
        self,
        proposer: bool,
    ):
        if proposer:
            prompt = Prompt(
                f"You are the PROPOSER. "
                f"Decide how much of the {CURRENCY}{ENDOWMENT} you will give to your partner: "
            )
            control = CustomSliderControl(
                start_value=0,
                min_value=0,
                max_value=ENDOWMENT,
                n_steps=ENDOWMENT,
                right_label="coins",
            )
            progress_display = None
            waiting_time = MAX_WAITING_PROPOSALS
        else:
            prompt = Prompt(
                f"You are the RESPONDER. "
                "Press the 'Next' button to see the proposal from your partner."
            )
            control = NullControl()
            waiting_time = MAX_WAITING_FOR_OTHER
            progress_display = ProgressDisplay(
                stages=[
                    ProgressStage(
                        time=waiting_time,
                        color="gray"
                    ),
                ],
            )

        super().__init__(
            label="inner_proposal",
            prompt=prompt,
            control=control,
            time_estimate=5,
            save_answer="inner_proposal",
            events={
                "responseEnable": Event(
                    is_triggered_by="trialStart",
                    delay=waiting_time,
                    js="onNextButton();",
                ),
            },
            progress_display=progress_display,
        )

    def format_answer(self, raw_answer, **kwargs) -> Union[float, str, None]:
        try:
            if raw_answer is None:
                return None
            answer = int(raw_answer)
            error_txt = f"Error: Answer should be a whole number between 0 and {ENDOWMENT} but got {answer}!"
            assert (0 <= answer <= ENDOWMENT), error_txt

            return answer
        except (ValueError, AssertionError) as e:
            text = f" Incorrect answer {raw_answer}: {raw_answer}"
            text += f" {e}"
            logger.info(text)
            return f"INVALID_RESPONSE"

    def validate(self, response, **kwargs) -> Union[FailedValidation, None]:
        logger.info(f"Validating...")
        if response.answer == "INVALID_RESPONSE":
            logger.info(f"Invalid response!")
            error_txt = f"Your response has to be a whole number between 0 and {ENDOWMENT} but got {response.answer}!"
            return FailedValidation(error_txt)
        logger.info(f"Validated!")
        return None


class InnerDictatorFeedbackPage(ModularPage):
    def __init__(
        self,
        proposer: bool,
        proposal: int,
        remainder: int,
        accumulated_score: int,
    ):
        if proposer:
            score = remainder
            text = (
                f"You have given {CURRENCY}{proposal} to your partner. "
                f"You keep the remainder of {CURRENCY}{remainder}. "
                f"Your accumulated score is {accumulated_score}"
            )
        else:
            score = proposal
            text = (
                f"Your partner has given you {CURRENCY}{proposal}."
            )

        waiting_time = MAX_WAITING_SEEING_INFO

        super().__init__(
            label="reward",
            prompt=Prompt(text),
            control=PushButtonControl(
                labels=["Next"],
                choices=[score]
            ),
            time_estimate=5,
            save_answer="reward",
            events={
                "responseEnable": Event(
                    is_triggered_by="trialStart",
                    delay=waiting_time,
                    js="onNextButton();",
                ),
            },
            progress_display=ProgressDisplay(
                stages=[
                    ProgressStage(
                        time=waiting_time,
                        color="gray"
                    ),
                ],
            ),
        )

