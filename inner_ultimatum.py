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

logger = get_logger()


class UltimatumTrialMaker(StaticTrialMaker):
    pass


class InstructionsPage(InfoPage):
    def __init__(self, proposer: bool):

        if proposer:
            text = (
                "Each round, you receive $10 and decide how much to offer your partner. "
                "If your partner accepts, you keep the remainder. "
                "If your partner rejects, both of you receive $0."
            )
        else:
            text = (
                "Each round, your partner receives $10 and decides how much to offer you. "
                "If you accept, you receive the offered amount and your partner keeps the remainder. "
                "If you reject, both of you receive $0."
            )

        super().__init__(
            text,
            time_estimate=5,
        )


class ProposalPage(ModularPage):
    def __init__(
            self,
            proposer: bool,
    ) -> None:

        if proposer:
            prompt = Prompt(
                "Decide how much of the $10 you will give to your partner: "
            )
            control = NumberControl()
        else:
            prompt = Prompt(
                "Press the 'Next' button to see the proposal from your partner."
            )
            control = NullControl()

        super().__init__(
            label="proposal",
            prompt=prompt,
            control=control,
            time_estimate=5,
            save_answer="proposal"
        )

    def format_answer(self, raw_answer, **kwargs) -> Union[float, str, None]:
        try:
            if raw_answer is None:
                return None
            answer = int(raw_answer)
            assert (0 <= answer <= 10), f"Error: Answer should be a whole number between 0 and 10 but got {answer}!"
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
            return FailedValidation(f"Your response has to be a whole number between 0 and 10!")
        logger.info(f"Validated!")
        return None


class AcceptancePage(ModularPage):
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


# definition["players assignment"]: {"proposer": participant_id, "responder": participant_id}
class UltimatumTrial(StaticTrial):
    time_estimate = 5
    accumulate_answers = True

    def show_trial(self, experiment, participant):
        return join(
            #########################################
            # INSTRUCTIONS
            #########################################
            conditional(
                label="only_first_round",
                condition=lambda participant: self.position == 0,
                logic_if_true=self.instructions_stage(),
                logic_if_false=None,
            ),
            #########################################
            # FIRST STAGE --- PROPOSAL
            #########################################
            self.first_stage(),
            GroupBarrier(
                id_="proposal_stage",
                group_type="ultimatum",
            ),
            #########################################
            # SECOND STAGE --- ACCEPTANCE
            #########################################
            self.second_stage(),
            GroupBarrier(
                id_="acceptance_stage",
                group_type="ultimatum",
                on_release=self.score_trial,
            ),
        )

    def only_first_round(self):
        logger.info(f"=> {self.position}")
        return self.position == 0

    def instructions_stage(self):
        return join(
            InstructionsPage(
                proposer=self.am_i_the_leader(),
            ),
            GroupBarrier(
                id_="instructions_stage",
                group_type="ultimatum",
            ),
        )

    def first_stage(self):
        return ProposalPage(
            proposer=self.am_i_the_leader(),
        )

    def second_stage(self):
        proposal, remainder, _ = self.get_result()

        return AcceptancePage(
            proposer=self.am_i_the_leader(),
            proposal=proposal,
            remainder=remainder,
        )

    @staticmethod
    def get_role(participant) -> Union[str, None]:
        role = UltimatumTrial.get_value_from_var(participant, 'role')
        if role is not None:
            return role
        return None

    def am_i_the_leader(self) -> Union[bool, None]:
        my_role = UltimatumTrial.get_role(self.participant)
        if my_role is not None:
            return my_role == 'proposer'
        return None

    @staticmethod
    def is_the_leader(participant) -> Union[bool, None]:
        role = UltimatumTrial.get_role(participant)
        if role is not None:
            return role == 'proposer'
        return None

    def show_feedback(self, experiment, participant):
        # Determine proposal and accept answer
        proposal, remainder, accept_answer = self.get_result()

        # Determine score
        score = UltimatumTrial.get_value_from_var(participant, 'score')

        # Determine score based on answers
        my_role = UltimatumTrial.get_role(self.participant)
        acceptance = None
        if my_role is not None:
            if accept_answer is not None:
                if my_role == 'proposer':
                    if accept_answer == 'Accept':
                        acceptance = "your partner accepted"
                    else:
                        acceptance = "your partner rejected"
                else:
                    if accept_answer == 'Accept':
                        acceptance = "you accepted"
                    else:
                        acceptance = "you rejected"

        prompt = (
            f"The proposal was {proposal} (out of 10), which {acceptance}. "
            + f"Your score is {score}."
        )

        return InfoPage(
            prompt,
            time_estimate=5,
        )

    def score_trial(self, participants: List[Participant]):
        # Determine proposal and accept answer
        proposal, remainder, accept_answer = self.get_result()

        for participant in participants:
            logger.info(participant.var)

        if accept_answer is not None:
            for participant in participants:
                if accept_answer == 'Reject':
                    participant.var.score = 0
                else:
                    # Determine role
                    my_role = UltimatumTrial.get_role(participant)
                    if my_role is not None:
                        if my_role == 'proposer':
                            participant.var.score = remainder
                        else:
                            participant.var.score = proposal

    def get_result(self):

        participants = self.participant.sync_group.participants
        assert len(participants) == 2

        # Determine proposal and accept answer
        proposal = None
        remainder = None
        accept_answer = None
        for participant in participants:
            role = UltimatumTrial.get_role(participant)
            if role is not None:
                if role == 'proposer':
                    proposal = UltimatumTrial.get_value_from_var(participant, 'proposal')
                    if proposal is not None:
                        try:
                            proposal = int(proposal)
                            remainder = 10 - proposal
                        except:
                            pass
                else:
                    accept_answer = UltimatumTrial.get_value_from_var(participant, 'accept_answer')

        return proposal, remainder, accept_answer

    @staticmethod
    def get_value_from_var(participant, variable: str):
        if participant.var.has(variable):
            return getattr(participant.var, variable)
        else:
            return None
