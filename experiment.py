import psynet.experiment
from psynet.sync import SimpleGrouper
from psynet.timeline import (
    Timeline,
    PageMaker,
)
from psynet.utils import get_logger

from .nested_game_node import NestedGameNode
from .nested_game_trial import (
    NestedGameTrial,
    NestedGameTrialMaker,
)
from .game_paramters import (
    MAX_NUM_WAITING_BIG_FIVE_QUESTIONS,
    TIMEOUT_WAITING_BIG_FIVE_QUESTIONS,
    TIMEOUT_PERSONALITY_TEST,
    NUMBER_OF_ROUNDS,
    RNG,
)
from .big_five import (
    PersonalityTrial,
    PersonalityTrialMaker,
    personality_nodes,
    WaitingTrial,
    waiting_nodes,
)
from .custom_barriers import CustomBarrier
from .custom_timeline import CustomTimeline
from .consent_science_of_learning import consent_cococo_science_of_learning
from .final_survey import get_final_survey

logger = get_logger()


def assign_roles(group, participants):
    assert len(participants) == 2
    ordered = sorted(participants, key=lambda p: p.id)
    outer_roles = ["proposer", "responder"]
    RNG.shuffle(outer_roles)
    for participant, role in zip(ordered, outer_roles):
        participant.var.outer_role = role
        participant.var.accumulated_reward = 0
        participant.var.round_failed = False
        participant.var.num_rounds_failed = 0


def get_start_nodes():
    return [
        NestedGameNode(
            definition={
                "outer_game": "ultimatum",  # dictator, ultimatum
                "inner_game": "ultimatum",  # dictator, ultimatum
                "transition": "random",  # constant, random, bid
            },
            context={
                "coin_url": "static/coin_url.png",
                "generic_url": "static/generic_url.png",
                "plate_url": "static/plate_url.png",
                "waiting_page_path": "templates/waiting_page.html",
            }
        )
    ]


waiting_trial_maker = PersonalityTrialMaker(
    id_="waiting",
    trial_class=WaitingTrial,
    nodes=waiting_nodes,
    expected_trials_per_participant=max(1, MAX_NUM_WAITING_BIG_FIVE_QUESTIONS // 4),
    max_trials_per_participant=MAX_NUM_WAITING_BIG_FIVE_QUESTIONS,
    allow_repeated_nodes=True,  # allow participants to cycle or a bug will occur
)

personality_trial_maker = PersonalityTrialMaker(
    id_="personality",
    trial_class=PersonalityTrial,
    nodes=personality_nodes,
    expected_trials_per_participant=1,
    max_trials_per_participant=1,
    allow_repeated_nodes=False,
)

waiting_logic = PageMaker(
    waiting_trial_maker.cue_trial, 
    time_estimate=PersonalityTrial.time_estimate
)


class Exp(psynet.experiment.Experiment):
    label = "Nested games"
    initial_recruitment_size = 1

    config = {
        "server_pem": "~/cap.pem",
        # "recruiter": "prolific",
        "recruiter": "hotair",
        "wage_per_hour": 9,
        "currency": "$",
        # **get_prolific_settings(),
        "title": "Nested games experiment (Chrome browser, ~15 minutes, $2.30)",
        "description": "This experiment is about collective behavior in nested games.",
        'initial_recruitment_size': 2,
        "auto_recruit": False,
        "show_reward": True,
        "show_progress_bar": True,
    }

    timeline = CustomTimeline(
        consent_cococo_science_of_learning(
            DURATION=15,
            PAYMENT=2.30,
        ),
        personality_trial_maker,
        waiting_trial_maker.custom(
            SimpleGrouper(
                group_type="chain",
                initial_group_size=2,
                max_group_size="initial_group_size",
                min_group_size=2,
                join_existing_groups=False,
                waiting_logic=waiting_logic,
                waiting_logic_expected_repetitions=MAX_NUM_WAITING_BIG_FIVE_QUESTIONS,
                max_wait_time=TIMEOUT_WAITING_BIG_FIVE_QUESTIONS * (MAX_NUM_WAITING_BIG_FIVE_QUESTIONS - 1),
            ),
        ),
        CustomBarrier(
            id_="assign_roles",
            content="Please wait while your partner completes the personality test...",
            on_release=assign_roles,
            timeout_between_barriers=TIMEOUT_PERSONALITY_TEST,
            participant_timeout_action="kick",
        ),
        NestedGameTrialMaker(
            id_="nested_games_trial_maker",
            trial_class=NestedGameTrial,
            node_class=NestedGameNode,
            chain_type="within",
            start_nodes=get_start_nodes,
            expected_trials_per_participant=5,
            max_trials_per_participant=5,
            chains_per_participant=1,
            # allow_repeated_nodes=True,
            target_n_participants=60,
            wait_for_networks=True,
            max_nodes_per_chain=NUMBER_OF_ROUNDS,
            trials_per_node=1,
            sync_group_type="chain",
        ),
        get_final_survey(),
    )
