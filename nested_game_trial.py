from markupsafe import Markup
from typing import Union

from psynet.page import InfoPage
from psynet.graphics import Prompt
from psynet.modular_page import (
    ModularPage,
    PushButtonControl,
    SliderControl,
)
from psynet.timeline import (
    join,
    conditional,
    Event,
    ProgressDisplay,
    ProgressStage,
)
from psynet.trial.chain import (
    ChainTrial,
    ChainTrialMaker,
)
from psynet.utils import get_logger

from .dictator_pages import (
    OuterDictatorProposalPage,
    InnerProposalPageOuterDictator,
    InnerDictatorFeedbackPage,
)
from .ultimatum_pages import (
    OuterUltimatumProposalPage,
    InnerProposalPageOuterUltimatum,
    InnerAcceptancePage,
    InnerUltimatumFeedbackPage,
)
from .variable_handler import VariableHandler
from .game_paramters import (
    REWARD_SCALING_FACTOR,
    MAX_BONUS_REWARD,
    MAX_WAITING_SEEING_INFO,
    MAX_WAIT_TIME,
    RNG,
)
from .instructions import (
    OBJECTIVE,
    OUTER_DICTATOR_INSTRUCTION,
    OUTER_ULTIMATUM_INSTRUCTION,
    SAME_ROLE_INSTRUCTION,
    RANDOM_ROLE_INSTRUCTION,
    INNER_DICTATOR_INSTRUCTIONS,
    INNER_ULTIMATUM_INSTRUCTIONS,
    EXAMPLE_PREPARATION_PHASE,
    EXAMPLE_PROPOSAL_PHASE,
    EXAMPLE_RANDOM,
    EXAMPLE_CONSTANT,
    ADD_OUTER_ACCEPTANCE_INSTRUCTION,
    ADD_INNER_ACCEPTANCE_INSTRUCTION,
)
from .custom_barriers import CustomBarrier
from .custom_pages import (
    OuterProposalPage,
    CustomWaitingPage,
    OuterAcceptancePage,
    InnerProposalPage,
    # InnerAcceptancePage,
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
            #############################################
            # CHOOSE OUTER ROLES DEPENDING ON TREATMENT
            #############################################
            CustomBarrier(
                id_="choose_outer_roles",
                content="Please wait for your partner...",
                on_release = self.choose_new_outer_role,
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
            # DETERMINE IF GAME SHOULD CONTINUE
            #########################################
            conditional(
                label="check_continue_to_inner_gamme",
                condition=lambda participant: self.continue_to_inner_game(),
                logic_if_false=None,
                #########################################
                # INNER GAME
                #########################################
                logic_if_true=conditional(
                    label="outer_game_type",
                    condition=lambda participant: participant.current_trial.definition["inner_game"] == "dictator",
                    logic_if_true=self.inner_dictator_stage(),
                    logic_if_false=self.inner_ultimatum_stage(),
                ),
            ),
            CustomBarrier("taking_stock"),
            self.show_trial_feedback(),
        )  # end main join

    ######################################################
    # METHODS FOR THE INSTRUCTIONS
    ######################################################
    def instructions_stage(self):
        outer_game = self.participant.current_trial.definition["outer_game"]
        inner_game = self.participant.current_trial.definition["inner_game"]
        transition = self.participant.current_trial.definition["transition"]

        example_text = EXAMPLE_PREPARATION_PHASE
        if outer_game == "dictator":
            preparation_phase = OUTER_DICTATOR_INSTRUCTION
        elif outer_game == "ultimatum":
            preparation_phase = OUTER_ULTIMATUM_INSTRUCTION
            example_text += ADD_OUTER_ACCEPTANCE_INSTRUCTION
        else:
            raise ValueError("outer_game must be dictator or ultimatum")

        example_text += EXAMPLE_PROPOSAL_PHASE
        if inner_game == "dictator":
            proposal_phase = INNER_DICTATOR_INSTRUCTIONS
        elif inner_game == "ultimatum":
            proposal_phase = INNER_ULTIMATUM_INSTRUCTIONS
            example_text += ADD_INNER_ACCEPTANCE_INSTRUCTION
        else:
            raise ValueError("outer_game must be dictator or ultimatum")

        if transition == "random":
            preparation_phase += RANDOM_ROLE_INSTRUCTION
            example_text += EXAMPLE_RANDOM
        elif transition == "constant":
            preparation_phase += SAME_ROLE_INSTRUCTION
            example_text += EXAMPLE_CONSTANT
        else:
            raise ValueError("transition must be 'random' or 'constant'")

        list_of_pages = join(
            # InfoPage(
            #     Markup(OBJECTIVE),
            #     time_estimate=5,
            # ),
            # InfoPage(
            #     Markup(preparation_phase),
            #     time_estimate=5,
            # ),
            # InfoPage(
            #     Markup(proposal_phase),
            #     time_estimate=5,
            # ),
            ModularPage(
                label="outer_role",
                prompt=Prompt(Markup(example_text)),
                control=PushButtonControl(
                    labels=["Next"],
                    choices=[self.get_outer_role(self.participant)]
                ),
                time_estimate=10,
            ),
        )

        return list_of_pages

    ######################################################
    # METHODS FOR THE OUTER GAME
    ######################################################
    def outer_dictator_stage(self):
        return join(
            conditional(
                label="outer_leader",
                condition=lambda participant: self.is_the_outer_leader(participant),
                logic_if_true=OuterProposalPage(self.context),
                logic_if_false=None,
            ),
            CustomBarrier(
                id_="outer_proposal_stage",
                on_release=self.assign_inner_roles,
                active_participant=self.am_i_the_outer_leader(),
                wait_page=CustomWaitingPage(
                    template_path=self.context["waiting_page_path"],
                    content="Waiting for the leader...",
                )
            ),
        )

    def outer_ultimatum_stage(self):
        return join(
            self.outer_dictator_stage(),
            conditional(
                label="outer_responder",
                condition=lambda participant: self.is_the_outer_leader(participant),
                logic_if_false=OuterAcceptancePage(
                    context=self.context,
                    proposal=self.get_outer_proposal(),
                ),
                logic_if_true=None,
            ),
            # Acceptance stage
            CustomBarrier(
                id_="outer_acceptance_stage",
                on_release=self.assign_outer_acceptance,
                active_participant=not self.am_i_the_outer_leader(),
                wait_page=CustomWaitingPage(
                    template_path=self.context["waiting_page_path"],
                    content="Waiting for acceptance...",
                    proposer=self.am_i_the_inner_leader(),
                )
            ),
        )

    def get_outer_proposal(self):
        proposer_id = self.get_outer_result()
        proposal = None
        if proposer_id is not None:
            if self.participant.id == proposer_id:
                proposal = "PROPOSER"
            else:
                proposal = "RESPONDER"
        return proposal

    def assign_inner_roles(self):
        # logger.info("Entering assignment of inner roles...")
        proposer_id = self.get_outer_result()
        # logger.info(f"Proposer id --> {proposer_id}")

        roles = None
        if proposer_id is not None:
            # logger.info(f"The proposer is participant {proposer_id}")
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
        """Returns the id of the inner proposer"""

        participants = self.participant.sync_group.participants
        assert len(participants) == 2

        ids = [participant.id for participant in self.participant.sync_group.participants]
        assert self.participant_id in ids

        # Determine proposal
        inner_proposer_id = None
        for participant in participants:
            if self.is_the_outer_leader(participant):
                ids.remove(participant.id)
                other_id = ids[0]
                outer_proposal = variable_handler.get_value(participant, "outer_proposal")
                if outer_proposal is not None:
                    if outer_proposal == "self":
                        inner_proposer_id = participant.id
                    else:
                        inner_proposer_id = other_id
                    break

        return inner_proposer_id

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
        return join(
            conditional(
                label="inner_leader",
                condition=lambda participant: self.is_the_inner_leader(participant),
                logic_if_false=None,
                logic_if_true=conditional(
                    label="feedback_depending_on_outer_game",
                    condition=lambda participant: participant.current_trial.definition['outer_game'] == "dictator",
                    logic_if_true=InnerProposalPage("dictator", self.context),
                    logic_if_false=InnerProposalPage("ultimatum", self.context),
                ),
            ),
            CustomBarrier(
                id_="inner_proposal_stage",
                on_release=self.assign_inner_proposal,
                active_participant=self.am_i_the_inner_leader(),
                wait_page=CustomWaitingPage(
                    template_path=self.context["waiting_page_path"],
                    content="Waiting for the leader...",
                    proposer=self.am_i_the_inner_leader(),
                )
            ),
        )

    def inner_ultimatum_stage(self):
        return join(
            # Proposal stage
            self.inner_dictator_stage(),
            # Acceptance stage
            conditional(
                label="inner_responder",
                condition=lambda participant: self.is_the_inner_leader(participant),
                logic_if_false=self.inner_ultimatum_acceptance_stage(),
                logic_if_true=None,
            ),
            CustomBarrier(
                id_="inner_acceptance_stage",
                content="Waiting for the inner responder...",
            ),
        )

    def inner_ultimatum_acceptance_stage(self):
        return InnerAcceptancePage(
                proposer=self.am_i_the_inner_leader(),
                **self.get_inner_result()
            ),

        # # Check inner role and act accordingly
        # inner_role = NestedGameTrial.get_inner_role(self.participant)
        #
        # if inner_role is not None:
        #     if inner_role == "proposer":
        #         proposer = True
        #     elif inner_role == "responder":
        #         proposer = False
        #     else:
        #         raise ValueError(f"Inner role should be either proposer or responder but got {outer_role}")
        #
        #     proposer_id = self.get_inner_result()
        #     if proposer_id is not None:
        #         if self.participant.id == proposer_id:
        #             proposal = "PROPOSER"
        #         else:
        #             proposal = "RESPONDER"
        #
        #         return OuterAcceptancePage(
        #             proposer=proposer,
        #             proposal=proposal,
        #         )
        #
        # return None

    def assign_inner_proposal(self):
        participants = self.participant.sync_group.participants
        inner_proposal = None
        if self.continue_to_inner_game():
            for participant in participants:
                if self.is_the_inner_leader(participant):
                    inner_proposal = VariableHandler.get_value_from_last_answer(
                        participant, "inner_proposal"
                    )
                    break

        logger.info(f"Assigning inner proposal to {inner_proposal}")

        for participant in participants:
            variable_handler.set_value(participant, "inner_proposal", inner_proposal)

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
                    # proposal = VariableHandler.get_from_answer(
                    #     answer=participant.current_trial.answer,
                    #     variable="inner_proposal",
                    # )
                    proposal = variable_handler.get_value(participant, 'inner_proposal')
                    if proposal is not None:
                        proposal = int(proposal)
                        remainder = 10 - int(proposal)
                else:
                    # proposal = VariableHandler.get_from_answer(
                    #     answer=participant.current_trial.answer,
                    #     variable="inner_accept_answer",
                    # )
                    accept_answer = variable_handler.get_value(participant, "inner_accept_answer")

        return {
            "proposal": proposal,
            "remainder": remainder,
            "accept_answer": accept_answer
        }

    ######################################################
    # END OF ROUND METHODS
    ######################################################
    # def score_trial(self, participants):
    #     pass

    def show_trial_feedback(self):
        if "summary" in self.participant.current_trial.definition.keys():
            accumulated_scores = self.participant.current_trial.definition["summary"]["accumulated_rewards"]
            my_accumulated_score = float(accumulated_scores[str(self.participant_id)])
        else:
            my_accumulated_score = 0.0

        inner_game_on = self.continue_to_inner_game()
        if not inner_game_on:

            return ModularPage(
                label="reward",
                prompt=Prompt(Markup(
                    f"<h2>Score</h2>"
                    f"<br>"
                    "<p>Proposal was not accepted. Round finished with score 0 coins. </p>"
                    f"<p>Your accumulated score is {my_accumulated_score} coins. </p>"
                    f"<br>"
                )),
                control=PushButtonControl(
                    labels=["Next"],
                    choices=[0.0]
                ),
                time_estimate=5,
                save_answer="reward",
                events={
                    "responseEnable": Event(
                        is_triggered_by="trialStart",
                        delay=MAX_WAITING_SEEING_INFO,
                        js="onNextButton();",
                    ),
                },
                progress_display=ProgressDisplay(
                    stages=[
                        ProgressStage(
                            time=MAX_WAITING_SEEING_INFO,
                            color="gray"
                        ),
                    ],
                ),
            )

        dict_result = self.get_inner_result()
        proposal = dict_result["proposal"]
        remainder = dict_result["remainder"]
        accept_answer = dict_result["accept_answer"]
        # logger.info(f"{proposal} --- {remainder} --- {accept_answer}")

        if proposal is not None:

            if accept_answer == "Reject":
                score = 0
            else:
                if self.am_i_the_inner_leader():
                    score = remainder
                else:
                    score = proposal

            # logger.info(f"{proposal} --- {remainder} --- {accept_answer} --- {score}")
            my_accumulated_score += int(score)
            inner_game = self.participant.current_trial.definition['inner_game']
            if inner_game == "dictator":
                return InnerDictatorFeedbackPage(
                    proposer=self.am_i_the_inner_leader(),
                    proposal=proposal,
                    remainder=remainder,
                    accumulated_score=int(my_accumulated_score),
                )
            else:
                return InnerUltimatumFeedbackPage(
                    proposer=self.am_i_the_inner_leader(),
                    proposal=proposal,
                    remainder=remainder,
                    accept_answer=accept_answer,
                    accumulated_score=int(my_accumulated_score),
                )
        else:
            return ModularPage(
                label="reward",
                prompt="OK",
                control=PushButtonControl(
                    labels=["Next"],
                    choices=[0],
                ),
                save_answer="reward",
                time_estimate=5,
            )

    def choose_new_outer_role(self):
        transition = self.participant.current_trial.definition['transition']
        participants = self.participant.sync_group.participants
        ordered = sorted(participants, key=lambda p: p.id)
        outer_roles = ["proposer", "responder"]
        if transition == "constant":
            pass
        elif transition == "random":
            RNG.shuffle(outer_roles)
        elif transition == "bid":
            pass
            # return self.bid()
        else:
            raise NotImplementedError
        for participant, role in zip(ordered, outer_roles):
            participant.var.outer_role = role

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
                CustomBarrier("bidding_stage"),
            )
        return None

    def score_answer(self, answer, definition) -> float:
        """
        Scores the participant's answer.
        Returns a numeric score quantifying the participant's success.
        """
        logger.info(f"Scoring answer. I see this answer ==> {answer}")
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
            logger.info(f"Warning: answer type {type(answer)} not supported (Value={answer})")
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
