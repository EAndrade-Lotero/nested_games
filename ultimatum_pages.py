from typing import Union

from psynet.graphics import Prompt
from psynet.modular_page import (
    ModularPage,
    PushButtonControl,
    NumberControl,
    NullControl,
)
from psynet.timeline import FailedValidation
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
        else:
            prompt = Prompt(
                "Click 'Next' to see which player your partner selects as PROPOSER."
            )
            control = NullControl()

        super().__init__(
            label="outer_proposal",
            prompt=prompt,
            control=control,
            time_estimate=5,
            save_answer="outer_proposal"
        )


class OuterAcceptancePage(ModularPage):
    def __init__(
            self,
            proposer: bool,
            proposal: str,
    ) -> None:
        assert proposal in ["PROPOSER", "RESPONDER"]

        if proposer:
            prompt = Prompt(
                "Press the 'Next' button to see whether your partner accepted the proposal."
            )
            control = NullControl()
        else:
            prompt = Prompt(
                f"Do you accept your partner's proposal of for you to be the {proposal}? "
            )
            control = PushButtonControl(
                choices=["Accept", "Reject"],
                labels=["Accept", "Reject"],
            )

        super().__init__(
            label="accept_answer",
            prompt=prompt,
            control=control,
            time_estimate=5,
            save_answer="accept_answer",
        )


class OuterUltimatumFeedbackPage(ModularPage):
    def __init__(
        self,
        proposer: str,
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
        else:
            prompt = Prompt(
                "Press the 'Next' button to see the proposal from your partner."
            )
            control = NullControl()

        super().__init__(
            label="inner_proposal",
            prompt=prompt,
            control=control,
            time_estimate=5,
            save_answer="inner_proposal"
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
    ) -> None:

        if proposer:
            prompt = Prompt(
                "Press the 'Next' button to see whether your partner accepted the proposal."
            )
            control = NullControl()
        else:
            prompt = Prompt(
                f"Do you accept your partner's proposal of {proposal} out of {10}? "
            )
            control = PushButtonControl(
                choices=["Accept", "Reject"],
                labels=["Accept", "Reject"],
            )

        super().__init__(
            label="accept_answer",
            prompt=prompt,
            control=control,
            time_estimate=5,
            save_answer="accept_answer",
        )


class InnerUltimatumFeedbackPage(ModularPage):
    def __init__(
        self,
        proposer: bool,
        proposal: int,
        remainder: int,
    ):
        if proposer:
            score = remainder
            text = (
                f"You have given {CURRENCY}{proposal} to your partner. "
                f"You keep the remainder of {CURRENCY}{remainder}. "
            )
        else:
            score = proposal
            text = (
                f"Your partner has given you {CURRENCY}{proposal}."
            )

        super().__init__(
            label="inner_score",
            prompt=Prompt(text),
            control=PushButtonControl(
                labels=["Next"],
                choices=[score]
            ),
            time_estimate=5,
            save_answer="inner_score",
        )
