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
)


logger = get_logger()


class OuterUltimatumProposalPage(ModularPage):
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
        else:
            prompt = Prompt(
                "Click 'Next' to see which player your partner selects as PROPOSER."
            )
            control = NullControl()
            progress_display = ProgressDisplay(
                stages=[
                    ProgressStage(
                        time=15,
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
                    delay=10,
                    js="onNextButton();",
                ),
            },
            progress_display=progress_display,
        )


class OuterAcceptancePage(ModularPage):
    def __init__(
            self,
            proposer: bool,
            proposal: str,
    ) -> None:
        assert proposal in ["", "PROPOSER", "RESPONDER"]

        if proposer:
            prompt = Prompt(
                "Press the 'Next' button to see whether your partner accepted the proposal."
            )
            control = NullControl()
            progress_display = ProgressDisplay(
                stages=[
                    ProgressStage(
                        time=15,
                        color="gray"
                    ),
                ],
            )
        else:
            prompt = Prompt(
                f"Do you accept your partner's proposal of you to be the {proposal}? "
            )
            control = PushButtonControl(
                choices=["Accept", "Reject"],
                labels=["Accept", "Reject"],
            )
            progress_display = None

        super().__init__(
            label="outer_accept_answer",
            prompt=prompt,
            control=control,
            time_estimate=5,
            save_answer="outer_accept_answer",
            events={
                "responseEnable": Event(
                    is_triggered_by="trialStart",
                    delay=10,
                    js="onNextButton();",
                ),
            },
            progress_display=progress_display,
        )


class OuterUltimatumFeedbackPage(ModularPage):
    def __init__(
        self,
        proposer: str,
        accepted: bool,
    ):
        if proposer == "self":
            text = (
                f"Proposal accepted. You are the PROPOSER. "
            )
        else:
            text = (
                f"Proposal accepted. You are the RESPONDER."
            )

        super().__init__(
            label="outer_choice",
            prompt=Prompt(text),
            control=PushButtonControl(
                labels=["Next"],
                choices=[proposer]
            ),
            time_estimate=5,
            save_answer="outer_choice",
            events={
                "responseEnable": Event(
                    is_triggered_by="trialStart",
                    delay=10,
                    js="onNextButton();",
                ),
            },
            progress_display=ProgressDisplay(
                stages=[
                    ProgressStage(
                        time=15,
                        color="gray"
                    ),
                ],
            ),
        )


class InnerUltimatumProposalPage(ModularPage):
    def __init__(
            self,
            proposer: bool,
    ) -> None:

        if proposer:
            prompt = Prompt(
                f"Decide how much of the {CURRENCY}{ENDOWMENT} you will give to your partner: "
            )
            control = NumberControl()
            progress_display = None
        else:
            prompt = Prompt(
                "Press the 'Next' button to see the proposal from your partner."
            )
            control = NullControl()
            progress_display = ProgressDisplay(
                stages=[
                    ProgressStage(
                        time=15,
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
                    delay=10,
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


class InnerAcceptancePage(ModularPage):
    def __init__(
            self,
            proposer: bool,
            proposal: int,
            remainder: int,
            accept_answer: str,
    ) -> None:

        if proposer:
            prompt = Prompt(
                "Press the 'Next' button to see whether your partner accepted the proposal."
            )
            control = NullControl()
            progress_display = ProgressDisplay(
                stages=[
                    ProgressStage(
                        time=15,
                        color="gray"
                    ),
                ],
            )
        else:
            prompt = Prompt(
                f"Do you accept your partner's proposal of {proposal} out of {10}? "
            )
            control = PushButtonControl(
                choices=["Accept", "Reject"],
                labels=["Accept", "Reject"],
            )
            progress_display = None

        super().__init__(
            label="inner_accept_answer",
            prompt=prompt,
            control=control,
            time_estimate=5,
            save_answer="inner_accept_answer",
            events={
                "responseEnable": Event(
                    is_triggered_by="trialStart",
                    delay=10,
                    js="onNextButton();",
                ),
            },
            progress_display=progress_display,
        )


class InnerUltimatumFeedbackPage(ModularPage):
    def __init__(
        self,
        proposer: bool,
        proposal: int,
        remainder: int,
        accept_answer: str,
        accumulated_score: int,
    ):
        if proposer:
            if accept_answer == 'Accept':
                acceptance = "your partner accepted"
                score = remainder
            else:
                acceptance = "your partner rejected"
                score = 0
        else:
            if accept_answer == 'Accept':
                acceptance = "you accepted"
                score = proposal
            else:
                acceptance = "you rejected"
                score = 0

        text = (
            f"The proposal was {proposal} (out of 10), which {acceptance}. "
            f"Your score is {score}. "
            f"Your accumulated score is {accumulated_score}"
        )

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
                    delay=10,
                    js="onNextButton();",
                ),
            },
            progress_display=ProgressDisplay(
                stages=[
                    ProgressStage(
                        time=15,
                        color="gray"
                    ),
                ],
            ),
        )
