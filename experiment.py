import random
import psynet.experiment
from psynet.sync import (
    GroupBarrier,
    SimpleGrouper,
)
from psynet.timeline import (
    Timeline,
    PageMaker,
)

from psynet.trial.static import (
    StaticNode,
    StaticTrialMaker,
)
from psynet.utils import get_logger

from .nested_game_trial import NestedDictatorTrial
from .waiting_page import WaitingTrial
from psynet.trial.imitation_chain import ImitationChainNode, ImitationChainTrialMaker

logger = get_logger()
NUMBER_OF_REPEATED_GAMES=10

class NestedDictatorTrialMaker(ImitationChainTrialMaker):
    pass

class NestedDictatorNode(ImitationChainNode):
    def create_initial_seed(self, experiment, participant):
        return {
            "outer": {
                "order": "normal",
                "type": "dictator",
            },
            "inner": {
                "order": "normal",
                "type": "dictator",
            },
        }

    def summarize_trials(self, trials, experiment, participant):
        # Keep node definition stable across repeats instead of propagating trial answers.
        return self.definition

def assign_roles(group, participants):
    assert len(participants) == 2
    ordered = sorted(participants, key=lambda p: p.id)
    outer_roles = ["proposer", "responder"]
    random.shuffle(outer_roles)
    for participant, role in zip(ordered, outer_roles):
        participant.var.outer_role = role

waiting_nodes = [
    StaticNode(
        definition={
            "question": question
        },
    ) for question in ["Question1", "Question2"]
]

game_nodes = [
    StaticNode(
        definition={
            "outer": {
                "order": outer_order,
                "type": "dictator",
            },
            "inner": {
                "order": "normal",
                "type": "dictator",
            },
        }
    )
    for outer_order in ["normal"]
]

waiting_trial_maker = StaticTrialMaker(
    id_="animals",
    trial_class=WaitingTrial,
    nodes=waiting_nodes,
    expected_trials_per_participant=len(waiting_nodes),
    max_trials_per_participant=99,
    allow_repeated_nodes=True,
)

waiting_logic = PageMaker(
    waiting_trial_maker.cue_trial, time_estimate=WaitingTrial.time_estimate
)


class Exp(psynet.experiment.Experiment):
    label = "Nested games"
    initial_recruitment_size = 1

    timeline = Timeline(
        waiting_trial_maker.custom(
            SimpleGrouper(
                group_type="chain",
                initial_group_size=2,
                max_group_size="initial_group_size",
                min_group_size=2,
                join_existing_groups=False,
                waiting_logic=waiting_logic,
                waiting_logic_expected_repetitions=len(waiting_nodes),
                max_wait_time=120,
            ),
        ),
        GroupBarrier(
            id_="assign_roles",
            group_type="chain",
            on_release=assign_roles,
        ),
        NestedDictatorTrialMaker(
            id_="nested_games_trial_maker",
            trial_class=NestedDictatorTrial,
            node_class=NestedDictatorNode,
            chain_type="within",
            start_nodes=None,
            expected_trials_per_participant=5,
            max_trials_per_participant=5,
            chains_per_participant=1,
            #allow_repeated_nodes=True,
            target_n_participants=60,
            wait_for_networks=True,
            max_nodes_per_chain=NUMBER_OF_REPEATED_GAMES,
            trials_per_node=1,
            sync_group_type="chain",

        ),
    )
