import numpy as np

from psynet.utils import get_logger
from psynet.trial.chain import ChainNode

from .variable_handler import VariableHandler

logger = get_logger()
variable_handler = VariableHandler()


class NestedGameNode(ChainNode):
    def create_initial_seed(self, experiment, participant):
        return self.seed

    def create_definition_from_seed(self, seed, experiment, participant):
        return seed

    def summarize_trials(self, trials, experiment, participant):
        ###################################
        # FILTER TRIALS
        ###################################
        filtered_trials = [
            trial for trial in trials if trial.failed is False
        ]
        assert len(filtered_trials) == 2, f"{[trial.failed_reason for trial in trials]}"

        filtered_answers = [trial.answer for trial in filtered_trials]
        assert np.all([
            answer is not None for answer in filtered_answers
        ]), f"{[answer for answer in filtered_answers]}"

        ###################################
        # ACCUMULATE REWARDS
        ###################################
        rewards = {}
        for trial in filtered_trials:
            accumulated_reward = variable_handler.get_value(
                participant=trial.participant,
                variable="accumulated_reward"
            )
            round_reward = trial.answer["reward"]
            accumulated_reward += float(round_reward)
            variable_handler.set_value(
                participant=trial.participant,
                variable="accumulated_reward",
                value=accumulated_reward,
            )
            rewards[trial.participant_id] = accumulated_reward

        ###################################
        # SANITY CHECKS
        ###################################
        outer_game = self.definition["outer_game"]
        outer_proposer, outer_responder = NestedGameNode.get_outer_proposer(filtered_trials)
        assert outer_proposer is not None
        assert outer_responder is not None

        outer_proposal, outer_acceptance = self.get_outer_proposal(
            outer_proposer, filtered_trials
        )
        assert outer_proposal is not None
        if outer_game == "ultimatum":
            assert outer_acceptance is not None

        inner_game = self.definition["inner_game"]
        inner_proposer, inner_responder = NestedGameNode.get_inner_proposer(
            outer_proposer, outer_proposal, filtered_trials
        )
        assert inner_proposer is not None
        assert inner_responder is not None

        inner_proposal, inner_acceptance = self.get_inner_proposal(
            outer_game,
            outer_acceptance,
            inner_proposer,
            filtered_trials,
        )

        if outer_acceptance != "Reject":
            assert inner_proposal is not None
            if inner_game == "ultimatum":
                assert inner_acceptance is not None

        ###################################
        # CREATE SUMMARY
        ###################################
        summary = {
            "outer_proposer": outer_proposer,
            "outer_responder": outer_responder,
            "outer_proposal": outer_proposal,
            "outer_acceptance": outer_acceptance,
            "inner_proposer": inner_proposer,
            "inner_responder": inner_responder,
            "inner_proposal": inner_proposal,
            "inner_acceptance": inner_acceptance,
            "accumulated_rewards": rewards,
        }
        self.definition["summary"] = summary

        return self.definition

    @staticmethod
    def get_outer_proposer(trials):
        participant_ids = [trial.participant_id for trial in trials]
        outer_roles = [
            variable_handler.get_value(
                participant=trial.participant,
                variable="outer_role",
            )
            for trial in trials
        ]
        assert "proposer" in outer_roles
        assert "responder" in outer_roles
        assert len(outer_roles) == 2

        if outer_roles[0] == "proposer":
            return participant_ids
        else:
            return participant_ids[::-1]

    def get_outer_proposal(self, outer_proposer, trials):
        outer_proposal = None
        outer_acceptance = None
        for idx, trial in enumerate(trials):
            if trial.participant_id == outer_proposer:
                outer_proposal = NestedGameNode.get_from_trial(
                    trial=trial,
                    variable="outer_proposal"
                )
                outer_game = self.definition["outer_game"]
                if outer_game == "ultimatum":
                    outer_acceptance = NestedGameNode.get_from_trial(
                        trial=trials[1 - idx],
                        variable="outer_accept_answer"
                    )
                break
        return outer_proposal, outer_acceptance

    @staticmethod
    def get_inner_proposer(outer_proposer, outer_proposal, trials):
        participant_ids = [trial.participant_id for trial in trials]
        if outer_proposal == "self":
            inner_proposer = outer_proposer
            inner_responder = [
                idx for idx in participant_ids
                if idx != outer_proposer
            ][0]
        else:
            inner_proposer = [
                idx for idx in participant_ids
                if idx != outer_proposer
            ][0]
            inner_responder = outer_proposer
        return inner_proposer, inner_responder

    def get_inner_proposal(self, outer_game, outer_acceptance, inner_proposer, trials):

        if outer_game == "ultimatum":
            if outer_acceptance == "Reject":
                return None, None

        inner_proposal = None
        inner_acceptance = None

        for idx, trial in enumerate(trials):

            if trial.participant_id == inner_proposer:
                inner_proposal = NestedGameNode.get_from_trial(
                    trial=trial,
                    variable="inner_proposal"
                )
                inner_game = self.definition["inner_game"]

                if inner_game == "ultimatum":
                    inner_acceptance = NestedGameNode.get_from_trial(
                        trial=trials[1 - idx],
                        variable="inner_accept_answer"
                    )
                break

        return inner_proposal, inner_acceptance

    @staticmethod
    def get_from_trial(trial, variable):
        initial_values = [
            value for key, value in trial.answer.items()
            if key.startswith(variable)
        ]
        values = [
            value for value in initial_values
            if (
                value is not None
                and str(value) != "null"
                and value != 'INVALID_RESPONSE'
            )
        ]
        err_msg = f"Error while finding a value for {variable}\n"
        err_msg += f"The observed trial answer was {trial.answer}\n"
        err_msg += f"The initial values observed were {initial_values}\n"
        err_msg += f"The non-empty values found were {values}"
        assert len(values) == 1, err_msg
        return values[0]
