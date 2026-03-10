from typing import Union

from psynet.page import WaitPage
from psynet.timeline import (
    join,
    conditional,
    CodeBlock,
)
from psynet.trial.imitation_chain import (
    ImitationChainNode,
    ImitationChainTrial,
    ImitationChainTrialMaker,
)
from psynet.sync import GroupBarrier
from psynet.utils import get_logger

from .dictator_pages import (
    OuterDictatorFeedbackPage,
    OuterDictatorProposalPage,
    InnerDictatorFeedbackPage,
    InnerDictatorProposalPage,
)
from .ultimatum_pages import (
    OuterUltimatumFeedbackPage,
    OuterUltimatumProposalPage,
    OuterAcceptancePage,
    InnerUltimatumFeedbackPage,
    InnerUltimatumProposalPage,
    InnerAcceptancePage,
)

logger = get_logger()


class NestedGameNode(ImitationChainNode):
    def create_initial_seed(self, experiment, participant):
        return {
            "outer_game": "ultimatum",
            "inner_game": "dictator",
            "order": "constant",
        }

    def summarize_trials(self, trials, experiment, participant):
        # Keep node definition stable across repeats instead of propagating trial answers.
        return self.definition


class NestedGameTrial(ImitationChainTrial):
    time_estimate = 5
    accumulate_answers = True

    def show_trial(self, experiment, participant):
        return join(
            #########################################
            # OUTER GAME
            #########################################
            # Proposal stage
            conditional(
                label="outer_game_role",
                condition=lambda participant: participant.current_trial.definition["outer_game"] == "dictator",
                logic_if_true=self.outer_dictator_stage(),
                logic_if_false=self.outer_ultimatum_stage(),
            ),
            #########################################
            # BETWEEN GAMES
            #########################################
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
                group_type="chain",
            ),
            # Feedback stage
            self.inner_feedback_stage(),
            GroupBarrier(
                id_="inner_feedback_stage",
                group_type="chain",
            ),
        )

    ######################################################
    # METHODS FOR THE OUTER GAME
    ######################################################
    def outer_dictator_stage(self):
        list_of_pages = join(
            OuterDictatorProposalPage(
                proposer=self.am_i_the_outer_leader(),
            ),
            GroupBarrier(
                id_="outer_proposal_stage",
                group_type="chain",
            ),
            # Feedback stage
            self.outer_dictator_feedback_stage(),
            GroupBarrier(
                id_="outer_feedback_stage",
                group_type="chain",
            ),
        )
        return list_of_pages

    def outer_dictator_feedback_stage(self):
        # Determine proposal and accept answer
        proposer = None
        proposer_id = self.get_outer_result()

        if proposer_id is not None:
            if self.participant.id == proposer_id:
                proposer = "self"
            else:
                proposer = "other"

        return OuterDictatorFeedbackPage(
            proposer=proposer,
        )

    def outer_ultimatum_stage(self):
        list_of_pages = join(
            OuterUltimatumProposalPage(
                proposer=self.am_i_the_outer_leader(),
            ),
            GroupBarrier(
                id_="outer_proposal_stage",
                group_type="chain",
            ),
            # # Feedback stage
            # self.outer_ultimatum_acceptance_stage(),
            # Feedback stage
            self.outer_dictator_feedback_stage(),
            GroupBarrier(
                id_="outer_feedback_stage",
                group_type="chain",
            ),
        )
        return list_of_pages

    def outer_ultimatum_feedback_stage(self):
        # Determine proposal and accept answer
        proposer = None
        proposer_id = self.get_outer_result()

        if proposer_id is not None:
            if self.participant.id == proposer_id:
                proposer = "self"
            else:
                proposer = "other"

        return OuterDictatorFeedbackPage(
            proposer=proposer,
        )

    def assign_inner_roles(self):
        logger.info("Entering assignment of inner roles...")
        proposer_id = self.get_outer_result()
        roles = None
        if proposer_id is not None:
            if proposer_id == self.participant.id:
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
        outer_role = NestedGameTrial.get_value_from_var(participant, 'outer_role')
        if outer_role is not None:
            return outer_role
        return None

    def am_i_the_outer_leader(self) -> Union[bool, None]:
        my_outer_role = NestedGameTrial.get_outer_role(self.participant)
        if my_outer_role is not None:
            return my_outer_role == 'proposer'
        return None

    @staticmethod
    def is_the_outer_leader(participant) -> Union[bool, None]:
        outer_role = NestedGameTrial.get_outer_role(participant)
        if outer_role is not None:
            return outer_role == 'proposer'
        return None

    def get_outer_result(self) -> int:
        "Returns the id of the proposer "

        participants = self.participant.sync_group.participants
        assert len(participants) == 2

        ids = [participant.id for participant in self.participant.sync_group.participants]

        # Determine proposal
        proposer_id = None
        for i, participant in enumerate(participants):
            outer_proposal = NestedGameTrial.get_value_from_var(participant, "outer_proposal")
            if outer_proposal is not None:
                if outer_proposal == "self":
                    proposer_id = ids[i]
                else:
                    proposer_id = ids[1 - i]
                break

        return proposer_id

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
        inner_role = NestedGameTrial.get_value_from_var(participant, 'inner_role')
        if inner_role is not None:
            return inner_role
        return None

    def am_i_the_inner_leader(self) -> Union[bool, None]:
        my_inner_role = NestedGameTrial.get_inner_role(self.participant)
        if my_inner_role is not None:
            return my_inner_role == 'proposer'
        return None

    @staticmethod
    def is_the_inner_leader(participant) -> Union[bool, None]:
        inner_role = NestedGameTrial.get_inner_role(participant)
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
            inner_role = NestedGameTrial.get_inner_role(participant)
            if inner_role is not None:
                if inner_role == 'proposer':
                    proposal = NestedGameTrial.get_value_from_var(participant, 'inner_proposal')
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


class NestedGameTrialMaker(ImitationChainTrialMaker):
    pass
