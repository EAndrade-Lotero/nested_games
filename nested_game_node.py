import numpy as np

from psynet.utils import get_logger
from psynet.trial.chain import ChainNode

from .game_parameters import MAX_TIMEOUT_ROUNDS
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
            (
                answer is not None
                and answer != "null"
            )
            for answer in filtered_answers
        ]), f"{[answer for answer in filtered_answers]}"

        ###################################
        # SANITY CHECKS
        ###################################
        outer_game = self.definition["outer_game"]
        outer_proposer, outer_responder = NestedGameNode.get_outer_proposer(filtered_trials)
        assert outer_proposer is not None
        assert outer_responder is not None

        round_failed = NestedGameNode.get_round_failed(trials)

        outer_proposal, outer_acceptance = self.get_outer_proposal(
            outer_proposer, filtered_trials, round_failed
        )
        assert outer_proposal is not None
        if outer_game == "ultimatum" and not round_failed:
            assert outer_acceptance is not None, f"====> Round failed: {[vars(trial) for trial in filtered_trials]}"

        inner_game = self.definition["inner_game"]
        inner_proposer, inner_responder = NestedGameNode.get_inner_proposer(
            outer_proposer, outer_proposal, filtered_trials
        )
        if not round_failed:
            assert inner_proposer is not None
            assert inner_responder is not None

        inner_proposal, inner_acceptance = self.get_inner_proposal(
            outer_game,
            outer_acceptance,
            inner_proposer,
            filtered_trials,
            round_failed,
        )

        if outer_acceptance != "Reject" and not round_failed:
            assert inner_proposal is not None
            if inner_game == "ultimatum":
                assert inner_acceptance is not None

        ###################################
        # ACCUMULATE REWARDS
        ###################################

        if "summary" in self.definition.keys():
            rewards = self.definition["summary"]["accumulated_rewards"]
        else:
            rewards = {
                str(trial.participant_id): 0 for trial in filtered_trials
            }

        if not round_failed:
            if outer_game != "ultimatum" or outer_acceptance == "Accept":
                if inner_game != "ultimatum" or inner_acceptance == "Accept":
                    for trial in filtered_trials:
                        accumulated_reward = rewards[str(trial.participant_id)]
                        round_reward = trial.answer["reward"]
                        accumulated_reward += float(round_reward)
                        variable_handler.set_value(
                            participant=trial.participant,
                            variable="accumulated_reward",
                            value=accumulated_reward,
                        )
                        rewards[str(trial.participant_id)] = accumulated_reward

        ############################
        # ACCUMULATE ROUNDS FAILED
        ############################
        if "summary" in self.definition.keys():
            num_rounds_failed = self.definition["summary"]["num_rounds_failed"]
        else:
            num_rounds_failed = 0

        if round_failed:
            num_rounds_failed += 1

        ############################
        # RECORD FOCUS LOSS
        ############################
        dict_focus_loss = {}
        for trial in filtered_trials:
            if trial.participant.var.has("focus_loss"):
                focus_loss = trial.participant.var.focus_loss
            else:
                focus_loss = 0
            dict_focus_loss[trial.participant_id] = focus_loss

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
            "round_failed": round_failed,
            "num_rounds_failed": num_rounds_failed,
            "focus_loss": dict_focus_loss,
        }

        self.definition["summary"] = summary

        return self.definition

    @staticmethod
    def get_round_failed(trials):
        answers = [trial.answer for trial in trials]
        values =[]

        for answer in answers:
            if len(answer) > 0:
                values.extend(list(answer.values()))

        check1 = any([v == "No answer" for v in values])

        failures = []
        for trial in trials:
            if trial.participant.var.has("fail_me"):
                failures.append(trial.participant.var.fail_me)
            else:
                failures.append(False)

        check2 = any(failures)

        return check1 or check2

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

    def get_outer_proposal(self, outer_proposer, trials, round_failed:bool):
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
                    if round_failed:
                        outer_acceptance = None
                    else:
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

    def get_inner_proposal(
        self,
        outer_game,
        outer_acceptance,
        inner_proposer,
        trials,
        round_failed:bool
    ):

        if outer_game == "ultimatum":
            if outer_acceptance == "Reject":
                return None, None

        inner_proposal = None
        inner_acceptance = None

        if not round_failed:
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
        if len(values) == 1:
            return values[0]
        else:
            err_msg = f"Warning while finding a value for {variable}\n"
            err_msg += f"The observed trial answer was {trial.answer}\n"
            err_msg += f"The initial values observed were {initial_values}\n"
            err_msg += f"The non-empty values found were {values}"
            logger.info(err_msg)
            return None
