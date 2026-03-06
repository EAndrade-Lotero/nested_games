from typing import Union

from psynet.timeline import (
    join,
    conditional,
    CodeBlock,
)
from psynet.trial.static import StaticTrial
from psynet.sync import GroupBarrier
from psynet.utils import get_logger

from .dictator_pages import (
    OuterDictatorFeedbackPage,
    OuterDictatorProposalPage,
    InnerDictatorFeedbackPage,
    InnerDictatorProposalPage,
)


logger = get_logger()


class NestedDictatorTrial(StaticTrial):
    time_estimate = 5
    accumulate_answers = True

    def show_trial(self, experiment, participant):
        return join(
            #########################################
            # OUTER GAME
            #########################################
            # Proposal stage
            self.outer_proposal_stage(),
            GroupBarrier(
                id_="outer_proposal_stage",
                group_type="nested_ultimatum",
            ),
            # Feedback stage
            self.outer_feedback_stage(),
            GroupBarrier(
                id_="outer_feedback_stage",
                group_type="nested_ultimatum",
            ),
            # Save to participant.var
            CodeBlock(
                lambda participant: self.assign_inner_roles()
            ),
            #########################################
            # INNER GAME
            #########################################
            # Proposal stage
            self.inner_proposal_stage(),
            GroupBarrier(
                id_="inner_proposal_stage",
                group_type="nested_ultimatum",
            ),
            # Feedback stage
            self.inner_feedback_stage(),
            GroupBarrier(
                id_="inner_feedback_stage",
                group_type="nested_ultimatum",
            ),
        )

    ######################################################
    # METHODS FOR THE OUTER GAME
    ######################################################
    def outer_proposal_stage(self):
        return OuterDictatorProposalPage(
            proposer=self.am_i_the_outer_leader(),
        )

    def outer_feedback_stage(self):
        # Determine proposal and accept answer
        dictator = None
        dictator_id = self.get_outer_result()

        if dictator_id is not None:
            if self.participant.id == dictator_id:
                dictator = "self"
            else:
                dictator = "other"

        return OuterDictatorFeedbackPage(
            proposer=dictator,
        )

    def assign_inner_roles(self):
        logger.info("Entering assignment of inner roles...")
        dictator_id = self.get_outer_result()
        roles = None
        if dictator_id is not None:
            if dictator_id == self.participant.id:
                roles = ["proposer", "responder"]
            else:
                roles = ["responder", "proposer"]

        if roles is not None:
            participants = self.participant.sync_group.participants
            for participant, role in zip(participants, roles):
                if participant.id == self.participant.id:
                    participant.var.inner_role = roles[0]
                else:
                    participant.var.inner_role = roles[1]
                logger.info(f"Participant {participant.id} got the role {participant.var.inner_role}")

    @staticmethod
    def get_outer_role(participant) -> Union[str, None]:
        outer_role = NestedDictatorTrial.get_value_from_var(participant, 'outer_role')
        if outer_role is not None:
            return outer_role
        return None

    def am_i_the_outer_leader(self) -> Union[bool, None]:
        my_outer_role = NestedDictatorTrial.get_outer_role(self.participant)
        if my_outer_role is not None:
            return my_outer_role == 'proposer'
        return None

    @staticmethod
    def is_the_outer_leader(participant) -> Union[bool, None]:
        outer_role = NestedDictatorTrial.get_outer_role(participant)
        if outer_role is not None:
            return outer_role == 'proposer'
        return None

    def get_outer_result(self) -> int:
        "Returns the id of the proposer "

        participants = self.participant.sync_group.participants
        assert len(participants) == 2

        ids = [participant.id for participant in self.participant.sync_group.participants]

        # Determine proposal
        dictator_id = None
        for i, participant in enumerate(participants):
            outer_proposal = NestedDictatorTrial.get_value_from_var(participant, "outer_proposal")
            if outer_proposal is not None:
                if outer_proposal == "self":
                    dictator_id = ids[i]
                else:
                    dictator_id = ids[1 - i]
                break

        return dictator_id

    ######################################################
    # METHODS FOR THE INNER GAME
    ######################################################
    def inner_proposal_stage(self):
        return InnerDictatorProposalPage(
            proposer=self.am_i_the_inner_leader(),
        )

    def inner_feedback_stage(self):
        # Determine proposal and accept answer
        proposal, remainder = self.get_inner_result()
        return InnerDictatorFeedbackPage(
            proposer=self.am_i_the_inner_leader(),
            proposal=proposal,
            remainder=remainder,
        )

    @staticmethod
    def get_inner_role(participant) -> Union[str, None]:
        inner_role = NestedDictatorTrial.get_value_from_var(participant, 'inner_role')
        if inner_role is not None:
            return inner_role
        return None

    def am_i_the_inner_leader(self) -> Union[bool, None]:
        my_inner_role = NestedDictatorTrial.get_inner_role(self.participant)
        if my_inner_role is not None:
            return my_inner_role == 'proposer'
        return None

    @staticmethod
    def is_the_inner_leader(participant) -> Union[bool, None]:
        inner_role = NestedDictatorTrial.get_inner_role(participant)
        if inner_role is not None:
            return inner_role == 'proposer'
        return None

    def get_inner_result(self):

        participants = self.participant.sync_group.participants
        assert len(participants) == 2

        # Determine proposal
        proposal = None
        remainder = None
        for participant in participants:
            inner_role = NestedDictatorTrial.get_inner_role(participant)
            if inner_role is not None:
                if inner_role == 'proposer':
                    proposal = NestedDictatorTrial.get_value_from_var(participant, 'inner_proposal')
                    if proposal is not None:
                        try:
                            proposal = int(proposal)
                            remainder = 10 - proposal
                        except:
                            pass
                    break

        return proposal, remainder

    ######################################################
    # HELPER METHODS
    ######################################################
    @staticmethod
    def get_value_from_var(participant, variable: str):
        if participant.var.has(variable):
            return getattr(participant.var, variable)
        else:
            return None
