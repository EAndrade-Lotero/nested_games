from typing import Union
from markupsafe import Markup

from psynet.modular_page import (
    ModularPage,
    PushButtonControl,
    SliderControl,
)
from psynet.timeline import (
    join,
    conditional,
    CodeBlock,
)
from psynet.trial.chain import (
    ChainTrial,
    ChainTrialMaker,
)
from psynet.utils import get_logger

from .variable_handler import VariableHandler
from .game_paramters import (
    REWARD_SCALING_FACTOR,
    MAX_BONUS_REWARD,
    TIMEOUT_WAITING_FOR_OTHER,
    MAX_TIMEOUT_ROUNDS,
    RNG,
)
from .instructions import get_instructions
from .custom_barriers import CustomBarrier
from .custom_timeline import EndRoundPage
from .custom_pages import (
    OuterProposalPage,
    CustomWaitingPage,
    OuterAcceptancePage,
    InnerProposalPage,
    InnerAcceptancePage,
    ScorePage,
)

logger = get_logger()
variable_handler = VariableHandler()


class NestedGameTrial(ChainTrial):
    time_estimate = 5
    accumulate_answers = True

    def show_trial(self, experiment, participant):

        instructions_stage = self.instructions_stage()
        timeout_at_barrier = TIMEOUT_WAITING_FOR_OTHER * len(instructions_stage)

        return join(
            #########################################
            # INSTRUCTIONS
            #########################################
            conditional(
                label="only_first_round",
                condition=lambda participant: self.position == 0,
                logic_if_true=instructions_stage,
                logic_if_false=None
            ),
            #############################################
            # CHOOSE OUTER ROLES DEPENDING ON TREATMENT
            #############################################
            CustomBarrier(
                id_="choose_outer_roles",
                content="Please wait for your partner...",
                on_release = self.choose_new_outer_role,
                timeout_at_barrier=timeout_at_barrier,
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
            conditional(
                label="check_max_timeout",
                condition=lambda participant: self.check_max_timeout(),
                logic_if_true=CodeBlock(
                    lambda experiment, participant: experiment.timeline.redirect_to_branch(experiment, participant, "unsuccessful_end")
                ),
            )
        )  # end main join

    ######################################################
    # METHODS FOR THE INSTRUCTIONS
    ######################################################
    def instructions_stage(self):
        return get_instructions(
            outer_game=self.participant.current_trial.definition["outer_game"],
            inner_game=self.participant.current_trial.definition["inner_game"],
            transition=self.participant.current_trial.definition["transition"],
            outer_role=self.get_outer_role(self.participant),
        )

    ######################################################
    # METHODS FOR THE OUTER GAME
    ######################################################
    def outer_dictator_stage(self):
        return join(
            conditional(
                label="outer_leader",
                condition=lambda participant: self.is_the_outer_leader(participant),
                logic_if_true=OuterProposalPage(
                    accumulated_score_me=self.get_my_accumulated_score(),
                    accumulated_score_partner=self.get_partner_accumulated_score(),
                    round_=self.position + 1,
                    time_estimate=self.time_estimate,
                ),
                logic_if_false=None,
            ),
            CustomBarrier(
                id_="outer_proposal_stage",
                on_release=self.assign_inner_roles,
                active_participant=self.am_i_the_outer_leader(),
                wait_page=CustomWaitingPage(
                    accumulated_score_me=self.get_my_accumulated_score(),
                    accumulated_score_partner=self.get_partner_accumulated_score(),
                    template_path=self.context["waiting_page_path"],
                    content=Markup(
                        "<h3>Please wait</h3>"
                        "<br>"
                        "<p>Waiting for a proposal...</p>"
                    ),
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
                    proposal=self.get_outer_proposal(),
                    round_=self.position + 1,
                    accumulated_score_me=self.get_my_accumulated_score(),
                    accumulated_score_partner=self.get_partner_accumulated_score(),
                    time_estimate=self.time_estimate,
                ),
                logic_if_true=None,
            ),
            # Acceptance stage
            CustomBarrier(
                id_="outer_acceptance_stage",
                on_release=self.assign_outer_acceptance,
                active_participant=not self.am_i_the_outer_leader(),
                wait_page=CustomWaitingPage(
                    accumulated_score_me=self.get_my_accumulated_score(),
                    accumulated_score_partner=self.get_partner_accumulated_score(),
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
            # Check round failure
            self.check_round_failed()

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

        ids = [participant.id for participant in participants]
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
                logic_if_true=InnerProposalPage(
                    outer_game=self.participant.current_trial.definition['outer_game'],
                    context=self.context,
                    round_=self.position + 1,
                ),
            ),
            CustomBarrier(
                id_="inner_proposal_stage",
                on_release=self.assign_inner_proposal,
                active_participant=self.am_i_the_inner_leader(),
                wait_page=CustomWaitingPage(
                    accumulated_score_me=self.get_my_accumulated_score(),
                    accumulated_score_partner=self.get_partner_accumulated_score(),
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
                logic_if_false=InnerAcceptancePage(
                    context=self.context,
                    proposal=self.get_inner_proposal(),
                    round_=self.position + 1,
                ),
                logic_if_true=None,
            ),
            CustomBarrier(
                id_="inner_acceptance_stage",
                active_participant=not self.am_i_the_inner_leader(),
                wait_page=CustomWaitingPage(
                    accumulated_score_me=self.get_my_accumulated_score(),
                    accumulated_score_partner=self.get_partner_accumulated_score(),
                    template_path=self.context["waiting_page_path"],
                    content="Waiting for acceptance...",
                    proposer=self.am_i_the_inner_leader(),
                    # n_coins=self.get_inner_proposal(),
                )
            ),
        )

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

            # Check round failure
            self.check_round_failed()

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

    def get_inner_proposal(self) -> Union[int, str, None]:
        participants = self.participant.sync_group.participants
        assert len(participants) == 2

        # Determine proposal
        proposal = None
        for participant in participants:
            if self.is_the_inner_leader(participant):
                proposal = variable_handler.get_value(participant, 'inner_proposal')
                if proposal is not None:
                    if proposal != "No answer":
                        proposal = int(proposal)
                break

        return proposal

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
                        if proposal != "No answer":
                            proposal = int(proposal)
                            remainder = 10 - int(proposal)
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
    # def score_trial(self, participants):
    #     pass

    def show_trial_feedback(self):

        if "summary" in self.participant.current_trial.definition.keys():
            participants = self.participant.sync_group.participants
            assert len(participants) == 2

            ids = [participant.id for participant in self.participant.sync_group.participants]
            assert self.participant_id in ids
            ids.remove(self.participant_id)
            other_id = ids[0]

            accumulated_scores = self.participant.current_trial.definition["summary"]["accumulated_rewards"]
            my_accumulated_score = float(accumulated_scores[str(self.participant_id)])
            partners_accumulated_score = float(accumulated_scores[str(other_id)])

            num_rounds_failed = self.participant.current_trial.definition["summary"]["num_rounds_failed"]
        else:
            my_accumulated_score = 0
            partners_accumulated_score = 0
            num_rounds_failed = 0

        if self.did_round_fail():
            num_rounds_failed += 1

        inner_game_on = self.continue_to_inner_game()
        if not inner_game_on:

            page = ScorePage(
                outer_game_type=self.participant.current_trial.definition["outer_game"],
                inner_game_type=self.participant.current_trial.definition["inner_game"],
                proposer=True,
                proposal=0,
                remainder_=0,
                accumulated_score=my_accumulated_score,
                partners_accumulated_score=partners_accumulated_score,
                outer_accepted=False,
                inner_accepted=False,
                round_failed=self.did_round_fail(),
                num_rounds_failed=num_rounds_failed,
            )

        else:

            dict_result = self.get_inner_result()
            proposal = dict_result["proposal"]
            remainder_ = dict_result["remainder"]
            accept_answer = dict_result["accept_answer"]
            # logger.info(f"{proposal} --- {remainder} --- {accept_answer}")

            if proposal is not None:

                if accept_answer == "Reject":
                    score = 0
                    partners_score = 0
                else:
                    if proposal != "No answer":
                        if self.am_i_the_inner_leader():
                            score = remainder_
                            partners_score = proposal
                        else:
                            score = proposal
                            partners_score = remainder_
                    else:
                        score = 0
                        partners_score = 0

                # logger.info(f"{proposal} --- {remainder_} --- {accept_answer} --- {score}")
                my_accumulated_score += int(score)
                partners_accumulated_score += int(partners_score)
                page = ScorePage(
                    outer_game_type=self.participant.current_trial.definition["outer_game"],
                    inner_game_type=self.participant.current_trial.definition["inner_game"],
                    proposer=self.am_i_the_inner_leader(),
                    proposal=proposal,
                    remainder_=remainder_,
                    accumulated_score=my_accumulated_score,
                    partners_accumulated_score=partners_accumulated_score,
                    inner_accepted=accept_answer == "Accept",
                    round_failed=self.did_round_fail(),
                    num_rounds_failed=num_rounds_failed,
                )
            else:
                page = EndRoundPage(
                    label="reward",
                    prompt="OK",
                    control=PushButtonControl(
                        labels=["Next"],
                        choices=[0],
                    ),
                    save_answer="reward",
                    time_estimate=5,
                )

        return page

    def did_round_fail(self):
        participants = self.participant.sync_group.participants
        assert len(participants) == 2
        round_failed = False
        for participant in participants:
            if participant.var.has("fail_me"):
                if participant.var.fail_me:
                    round_failed = True
        return round_failed

    def check_round_failed(self):
        round_failed = self.did_round_fail()
        if round_failed:
            participants = self.participant.sync_group.participants
            for participant in participants:
                participant.var.round_failed = True

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
            participant.var.round_failed = False
            participant.var.fail_me = False

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

    def get_my_accumulated_score(self):
        my_accumulated_score = 0
        if "summary" in self.participant.current_trial.definition.keys():
            rewards = self.participant.current_trial.definition["summary"]["accumulated_rewards"]
            my_accumulated_score = rewards[self.participant_id]
        return my_accumulated_score

    def get_partner_accumulated_score(self):
        other_id = self.get_other_ide()
        partner_accumulated_score = 0
        if "summary" in self.participant.current_trial.definition.keys():
            rewards = self.participant.current_trial.definition["summary"]["accumulated_rewards"]
            partner_accumulated_score = rewards[other_id]
        return partner_accumulated_score

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

    def check_max_timeout(self):
        if "summary" in self.participant.current_trial.definition.keys():
            num_rounds_failed = self.participant.current_trial.definition["summary"]["num_rounds_failed"]

            if self.did_round_fail():
                num_rounds_failed += 1

            if num_rounds_failed >= MAX_TIMEOUT_ROUNDS:
                return True

        return False

    def get_other_ide(self):
        other_id = None
        if self.participant.sync_group is not None:
            participants = self.participant.sync_group.participants
            assert len(participants) == 2
            ids = [participant.id for participant in participants]
            assert self.participant_id in ids
            ids.remove(self.participant_id)
            other_id = ids[0]
        return other_id

class NestedGameTrialMaker(ChainTrialMaker):
    pass
