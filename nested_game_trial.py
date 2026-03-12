from typing import Union

from psynet.page import WaitPage
from psynet.modular_page import (
    ModularPage,
    PushButtonControl,
    SliderControl,
)
from psynet.timeline import (
    join,
    conditional,
    switch,
    CodeBlock,
    Event,
    ProgressDisplay,
    ProgressStage,
)
from psynet.trial.chain import (
    ChainTrial,
    ChainTrialMaker,
)
from psynet.sync import GroupBarrier
from psynet.utils import get_logger

from .dictator_pages import (
    OuterDictatorProposalPage,
    OuterDictatorFeedbackPage,
    InnerDictatorProposalPage,
    InnerDictatorFeedbackPage,
)
from .ultimatum_pages import (
    OuterUltimatumProposalPage,
    OuterAcceptancePage,
    OuterUltimatumFeedbackPage,
    InnerUltimatumProposalPage,
    InnerAcceptancePage,
    InnerUltimatumFeedbackPage,
)
from .variable_handler import VariableHandler
from .game_paramters import (
    REWARD_SCALING_FACTOR,
    MAX_BONUS_REWARD,
    RNG,
)

logger = get_logger()
variable_handler = VariableHandler()


class NestedGameTrial(ChainTrial):
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
                logic_if_false=None
            ),
            GroupBarrier(
                id_="instructions_stage",
                group_type="chain",
                waiting_logic=WaitPage(
                    wait_time=1,
                    content="Please wait while other participants read the instructions..."
                ),
                max_wait_time=120,
            ),
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
                    self.show_score(),
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
                    self.show_score(),
                ),
            ),
            GroupBarrier(
                id_="overall_score",
                group_type="chain",
            ),
            # switch(
            #     label="choose_new_outer_role",
            #     function=lambda experiment, participant: participant.definition["order"],
            #     branches={
            #         "constant": None,
            #         "random": self.shuffle_roles(),
            #         "bid": self.bid(),
            #     }
            # ),
            # GroupBarrier(
            #     id_="roles_for_new_round",
            #     group_type="chain",
            # ),
        )

    ######################################################
    # METHODS FOR THE INSTRUCTIONS
    ######################################################
    def instructions_stage(self):
        return ModularPage(
            label="outer_role",
            prompt="This is going to be the instructions",
            control=PushButtonControl(
                labels=["Next"],
                choices=[self.get_outer_role(self.participant)]
            ),
            time_estimate=10,
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
            # Save to participant.var
            CodeBlock(
                lambda participant: self.assign_inner_roles()
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
        accepted = None
        proposer_id = self.get_outer_result()

        if proposer_id is not None:
            if self.participant.id == proposer_id:
                proposer = "self"
            else:
                proposer = "other"

            accept_answer = self.get_outer_acceptance()
            if accept_answer == "Accept":
                accepted = True
            else:
                accepted = False

        return OuterUltimatumFeedbackPage(
            proposer=proposer,
            accepted=accepted,
        )

    def assign_inner_roles(self):
        logger.info("Entering assignment of inner roles...")
        proposer_id = self.get_outer_result()
        logger.info(f"--> {proposer_id}")

        roles = None
        if proposer_id is not None:
            logger.info(f"The proposer is participant {proposer_id}")
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
            # Feedback stage
            InnerDictatorFeedbackPage(
                proposer=self.am_i_the_inner_leader(),
                **self.get_inner_result()
            ),
            GroupBarrier(
                id_="inner_feedback_stage",
                group_type="chain",
            ),
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
            GroupBarrier(
                id_="inner_feedback_stage",
                group_type="chain",
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

    def show_score(self):
        logger.info(f"==> Entering show score...")
        try:
            accumulated_scores = self.definition["summary"]["accumulated_rewards"]
            my_accumulated_score = accumulated_scores[str(self.participant_id)]
        except:
            my_accumulated_score = 0.0

        inner_game_on = self.continue_to_inner_game()
        if not inner_game_on:
            score = my_accumulated_score
        else:
            dict_result = self.get_inner_result()
            accept_answer = dict_result["accept_answer"]

            if accept_answer == "Reject":
                score = 0.0
            else:
                proposal = dict_result["proposal"]
                remainder = dict_result["remainder"]
                if self.am_i_the_inner_leader():
                    score = remainder
                else:
                    score = proposal

        if score is not None:
            my_accumulated_score += score

        text = f"Your score for this round is {score}. "
        text += f"Your accumulated score is {my_accumulated_score}"

        return ModularPage(
                        label="reward",
                        prompt=text,
                        control=PushButtonControl(
                            labels=["Next"],
                            choices=[score],
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

    def shuffle_roles(self):
        participants = self.participant.sync_group.participants
        outer_roles = [
            self.get_outer_role(participant) for participant in participants
        ]
        RNG.shuffle(outer_roles)

        for role, participant in zip(outer_roles, participants):
            variable_handler.set_value(
                participant=participant,
                variable="outer_role",
                value=role,
            )

    def bid(self):
        max_value = variable_handler.get_value(
            participant=self.participant,
            variable="accumulated",
        )
        if max_value is not None:
            return join(
                ModularPage(
                    label="bid_phase",
                    prompt="Please use the slider to state your bid for being the proposer on the next round:",
                    control=SliderControl(
                        start_value=0.0,
                        min_value=0.0,
                        max_value=max_value,
                        n_steps=max_value,
                    ),
                    save_answer="bid_phase"
                ),
                GroupBarrier(
                    id_="bidding_stage",
                    group_type="chain",
                ),
            )
        return None

    def score_answer(self, answer, definition) -> float:
        """
        Scores the participant's answer.
        Returns a numeric score quantifying the participant's success.
        """
        if isinstance(answer, dict):
            score = answer["reward"]
        elif isinstance(answer, str):
            try:
                score = float(answer)
            except Exception as e:
                text = f"Error with finding reward from answer: {answer}"
                text += f"\nGot error: {e}"
                score = 0.0
        else:
            logger.info(f"Warning: answer type {type(answer)} not supported.  --- value={answer}")
            score = 0.0
        logger.info(f"Score obtained: {score}")
        return score

    def compute_performance_reward(self, score) -> float:
        if score is None:
            return 0.0
        else:
            score = float(score) * REWARD_SCALING_FACTOR
            return min(max(0.0, score), MAX_BONUS_REWARD)


class NestedGameTrialMaker(ChainTrialMaker):
    pass
