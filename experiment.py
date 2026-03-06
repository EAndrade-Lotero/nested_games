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

logger = get_logger()


class NestedDictatorTrialMaker(StaticTrialMaker):
    pass


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
                group_type="nested_ultimatum",
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
            group_type="nested_ultimatum",
            on_release=assign_roles,
        ),
        NestedDictatorTrialMaker(
            id_="nested_games",
            trial_class=NestedDictatorTrial,
            nodes=game_nodes,
            expected_trials_per_participant=1,
            max_trials_per_participant=1,
            sync_group_type="nested_ultimatum",
        ),
    )
