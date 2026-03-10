from typing import Union

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
from psynet.page import InfoPage

from .dictator_pages import (
    OuterDictatorFeedbackPage,
    OuterDictatorProposalPage,
    InnerDictatorFeedbackPage,
    InnerDictatorProposalPage,
)
from .ultimatum_pages import (
    OuterUltimatumProposalPage,
    OuterUltimatumFeedbackPage,
    OuterAcceptancePage,
    InnerUltimatumProposalPage,
    InnerUltimatumFeedbackPage,
    InnerAcceptancePage,
)
from .variable_handler import VariableHandler

logger = get_logger()
variable_handler = VariableHandler()
variable_handler.debug = True


class NestedGameNode(ImitationChainNode):
    def create_initial_seed(self, experiment, participant):
        return {
            "outer_game": "ultimatum",  # dictator, ultimatum
            "inner_game": "ultimatum",  # dictator, ultimatum
            "order": "constant",  # constant, random, bid
        }

    def summarize_trials(self, trials, experiment, participant):
        # Keep node definition stable across repeats instead of propagating trial answers.
        return self.definition


class NestedGameTrial(ImitationChainTrial):
    time_estimate = 5
    accumulate_answers = True

    def show_trial(self, experiment, participant):

        #########################################
        # Variable initializations
        #########################################
        # variable_handler.set_value()
        # logger.info("="*60)
        # logger.info(f"==> participant vars:\n{vars(participant)}")

        return join(
            #########################################
            # OUTER GAME
            #########################################
            conditional(
                label="outer_game_type",
                condition=lambda participant: participant.current_trial.definition["outer_game"] == "dictator",
                logic_if_true=self.outer_dictator_stage(),
                logic_if_false=self.outer_ultimatum_stage(),
            ),
            #########################################
            # BETWEEN GAMES
            #########################################
            # Determine if game should continue
            conditional(
                label="check_continue_to_inner_gamme",
                condition=lambda participant: self.continue_to_inner_game(),
                logic_if_false=join(
                    InfoPage(
                        "Ok",
                        time_estimate=1,
                    ),
                    # GroupBarrier(
                    #     id_="outer_feedback_stage",
                    #     group_type="chain",
                    #     on_release=self.score_trial,
                    # ),
                ),
                logic_if_true=join(
                    #########################################
                    # INNER GAME
                    #########################################
                    conditional(
                        label="outer_game_type",
                        condition=lambda participant: participant.current_trial.definition["inner_game"] == "dictator",
                        logic_if_true=self.inner_dictator_stage(),
                        logic_if_false=self.inner_ultimatum_stage(),
                    ),
                ),
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
            # Acceptance stage
            self.outer_ultimatum_acceptance_stage(),
            GroupBarrier(
                id_="outer_acceptance_stage",
                group_type="chain",
            ),
            # Save to participant.var
            CodeBlock(
                lambda participant: self.assign_inner_roles()
            ),
            # Save to participant.var
            CodeBlock(
                lambda participant: self.assign_outer_acceptance()
            ),
            # Feedback stage
            self.outer_ultimatum_feedback_stage(),
            GroupBarrier(
                id_="outer_feedback_stage",
                group_type="chain",
            ),
        )
        return list_of_pages

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
                    role = roles[0]
                else:
                    role = roles[1]
                variable_handler.set_value(
                    participant=participant,
                    variable="inner_role",
                    value=role,
                )
                logger.info(f"Participant {participant.id} got the role {role}")

    def assign_outer_acceptance(self):
        logger.info("Entering assignment of outer acceptance...")
        accept_answer = self.get_outer_acceptance()

        if accept_answer is not None:
            participants = self.participant.sync_group.participants
            for participant in participants:
                if accept_answer == 'Accept':
                    variable_handler.set_value(participant, "continue_to_inner_game", True)
                else:
                    variable_handler.set_value(participant, "continue_to_inner_game", False)

            logger.info(f"Proposal was {accept_answer}")

    def outer_ultimatum_acceptance_stage(self):
        # Check outer role and act accordingly
        outer_role = NestedGameTrial.get_outer_role(self.participant)

        if outer_role is not None:
            proposal = ""

            if outer_role == "proposer":
                proposer = True
            elif outer_role == "responder":
                proposer = False

                # Ask responder
                proposer_id = self.get_outer_result()

                if proposer_id is not None:
                    if self.participant.id == proposer_id:
                        proposal = "PROPOSER"
                    else:
                        proposal = "RESPONDER"
            else:
                raise ValueError(f"outer_role should be either proposer or responder but got {outer_role}")

            return OuterAcceptancePage(
                proposer=proposer,
                proposal=proposal,
            )

    def outer_ultimatum_feedback_stage(self):
        # Determine proposal and accept answer
        proposer = None
        proposer_id = self.get_outer_result()

        if proposer_id is not None:
            if self.participant.id == proposer_id:
                proposer = "self"
            else:
                proposer = "other"

        return OuterUltimatumFeedbackPage(
            proposer=proposer,
        )

    @staticmethod
    def get_outer_role(participant) -> Union[str, None]:
        outer_role = variable_handler.get_value(participant, 'outer_role')
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
        """Returns the id of the proposer """

        participants = self.participant.sync_group.participants
        assert len(participants) == 2

        ids = [participant.id for participant in self.participant.sync_group.participants]

        # Determine proposal
        proposer_id = None
        for i, participant in enumerate(participants):
            outer_proposal = variable_handler.get_value(participant, "outer_proposal")
            if outer_proposal is not None:
                if outer_proposal == "self":
                    proposer_id = ids[i]
                else:
                    proposer_id = ids[1 - i]
                break

        return proposer_id

    def get_outer_acceptance(self) -> str:
        participants = self.participant.sync_group.participants
        accept_answer = None

        if self.participant.current_trial.definition["outer_game"] == "ultimatum":
            # Determine if proposal was accepted
            for participant in participants:
                accept_answer = variable_handler.get_value(participant, "outer_accept_answer")
                logger.info(f"Participant {participant.id} => {accept_answer}")
                if accept_answer is not None:
                    break

        return accept_answer

    def continue_to_inner_game(self) -> bool:
        if self.participant.current_trial.definition["outer_game"] == "dictator":
            return True
        accept_answer = self.get_outer_acceptance()
        return accept_answer == "Accept"

    ######################################################
    # METHODS FOR THE INNER GAME
    ######################################################
    def inner_dictator_stage(self):
        list_of_pages = join(
            # Proposal stage
            InnerDictatorProposalPage(
                proposer=self.am_i_the_inner_leader(),
            ),
            GroupBarrier(
                id_="inner_proposal_stage",
                group_type="chain",
            ),
            # # Feedback stage
            # InnerDictatorFeedbackPage(
            #     proposer=self.am_i_the_inner_leader(),
            #     **self.get_inner_result()
            # ),
            # GroupBarrier(
            #     id_="inner_feedback_stage",
            #     group_type="chain",
            #     on_release=self.score_trial,
            # ),
        )
        return list_of_pages

    def inner_ultimatum_stage(self):
        list_of_pages = join(
            InnerUltimatumProposalPage(
                proposer=self.am_i_the_outer_leader(),
            ),
            GroupBarrier(
                id_="inner_proposal_stage",
                group_type="chain",
            ),
            # Acceptance stage
            InnerAcceptancePage(
                proposer=self.am_i_the_inner_leader(),
                **self.get_inner_result()
            ),
            GroupBarrier(
                id_="inner_acceptance_stage",
                group_type="chain",
            ),
            # Feedback stage
            InnerUltimatumFeedbackPage(
                proposer=self.am_i_the_inner_leader(),
                **self.get_inner_result()
            ),
        )
        return list_of_pages

    @staticmethod
    def get_inner_role(participant) -> Union[str, None]:
        inner_role = variable_handler.get_value(participant, 'inner_role')
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
        accept_answer = None
        for participant in participants:
            inner_role = NestedGameTrial.get_inner_role(participant)
            if inner_role is not None:
                if inner_role == 'proposer':
                    proposal = variable_handler.get_value(participant, 'inner_proposal')
                    if proposal is not None:
                        try:
                            proposal = int(proposal)
                            remainder = 10 - proposal
                        except:
                            pass
                else:
                    accept_answer = variable_handler.get_value(participant, "inner_accept_answer")

        return {
            "proposal": proposal,
            "remainder": remainder,
            "accept_answer": accept_answer
        }

    ######################################################
    # END OF ROUND METHODS
    ######################################################

    def score_trial(self, participants):
        pass


class NestedGameTrialMaker(ImitationChainTrialMaker):
    pass
