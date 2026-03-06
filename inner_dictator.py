from typing import List, Union

from psynet.graphics import Prompt
from psynet.modular_page import (
    ModularPage,
    PushButtonControl,
    NumberControl,
    NullControl,
)
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.timeline import (
    join,
    conditional,
    FailedValidation,
)
from psynet.trial.static import (
    StaticTrial,
    StaticTrialMaker,
)
from psynet.sync import GroupBarrier
from psynet.utils import get_logger

from .game_paramters import (
    CURRENCY,
    ENDOWMENT,
)

logger = get_logger()


class InnerDictatorTrialMaker(StaticTrialMaker):
    pass


class FeedbackPage(ModularPage):
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


class ProposalPage(ModularPage):
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


class InnerDictatorTrial(StaticTrial):
    time_estimate = 5
    accumulate_answers = True

    def show_trial(self, experiment, participant):
        return join(
            #########################################
            # PROPOSAL
            #########################################
            self.proposal_stage(),
            GroupBarrier(
                id_="proposal_stage",
                group_type="nested_ultimatum",
            ),
            self.feedback_stage(),
            GroupBarrier(
                id_="feedback_stage",
                group_type="nested_ultimatum",
            ),
        )

    def proposal_stage(self):
        return ProposalPage(
            proposer=self.am_i_the_leader(),
        )

    def feedback_stage(self):
        # Determine proposal and accept answer
        proposal, remainder = self.get_result()
        return FeedbackPage(
            proposer=self.am_i_the_leader(),
            proposal=proposal,
            remainder=remainder,
        )

    @staticmethod
    def get_role(participant) -> Union[str, None]:
        inner_role = InnerDictatorTrial.get_value_from_var(participant, 'inner_role')
        if inner_role is not None:
            return inner_role
        return None

    def am_i_the_leader(self) -> Union[bool, None]:
        my_inner_role = InnerDictatorTrial.get_role(self.participant)
        if my_inner_role is not None:
            return my_inner_role == 'proposer'
        return None

    @staticmethod
    def is_the_leader(participant) -> Union[bool, None]:
        inner_role = InnerDictatorTrial.get_role(participant)
        if inner_role is not None:
            return inner_role == 'proposer'
        return None

    def get_result(self):

        participants = self.participant.sync_group.participants
        assert len(participants) == 2

        # Determine proposal
        proposal = None
        remainder = None
        for participant in participants:
            inner_role = InnerDictatorTrial.get_role(participant)
            if inner_role is not None:
                if inner_role == 'proposer':
                    proposal = InnerDictatorTrial.get_value_from_var(participant, 'inner_proposal')
                    if proposal is not None:
                        try:
                            proposal = int(proposal)
                            remainder = 10 - proposal
                        except:
                            pass
                    break

        return proposal, remainder

    @staticmethod
    def get_value_from_var(participant, variable: str):
        if participant.var.has(variable):
            return getattr(participant.var, variable)
        else:
            return None
