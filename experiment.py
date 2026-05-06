import json
from markupsafe import Markup

import psynet.experiment
from psynet.sync import SimpleGrouper
from psynet.timeline import PageMaker
from psynet.utils import get_logger
from psynet.modular_page import (
    ModularPage,
    VideoPrompt,
)
from psynet.page import UnsuccessfulEndPage, InfoPage
from psynet.timeline import conditional

from .nested_game_node import NestedGameNode
from .nested_game_trial import (
    NestedGameTrial,
    NestedGameTrialMaker,
)
from .game_paramters import (
    MAX_NUM_WAITING_BIG_FIVE_QUESTIONS,
    TIMEOUT_WATCH_TUTORIAL,
    TIMEOUT_WAITING_BIG_FIVE_QUESTIONS,
    STANDARD_TIMEOUT,
    TIME_ESTIMATE_FOR_COMPENSATION,
    TIME_ESTIMATE_FOR_COMPENSATION_TUTORIAL_VIDEO,
    NUMBER_OF_ROUNDS,
    CURRENCY,
    ESTIMATED_DURATION,
    PAYMENT,
    HOURLY_PAYMENT,
    TARGET_PARTICIPANTS,
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
from .custom_timeline import CustomTimeline, EndExperimentPage
from .consent_science_of_learning import consent_cococo_science_of_learning
from .final_survey import get_final_survey
from .custom_front_end import NextWithTimerControl

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
                "outer_waiting_page_path": "templates/outer_waiting_page.html",
                "inner_waiting_page_path": "templates/inner_waiting_page.html",
            }
        )
    ]

waiting_trial_maker = PersonalityTrialMaker(
    id_="waiting",
    trial_class=WaitingTrial,
    nodes=waiting_nodes,
    expected_trials_per_participant=1,
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
    time_estimate=TIME_ESTIMATE_FOR_COMPENSATION,
)

def get_prolific_settings():
    with open("qualification_prolific_en.json", "r") as f:
        qualification = json.dumps(json.load(f))
    return {
        "recruiter": "prolific",
        "base_payment": PAYMENT,
        "prolific_estimated_completion_minutes": ESTIMATED_DURATION,
        "prolific_recruitment_config": qualification,
        "auto_recruit": False,
        "wage_per_hour": HOURLY_PAYMENT,
        "currency": CURRENCY,
        "show_reward": False,
    }


class Exp(psynet.experiment.Experiment):
    label = "Nested games"
    initial_recruitment_size = 1

    config = {
        "server_pem": "~/cap.pem",
        "recruiter": "prolific",
        # "recruiter": "hotair",
        "wage_per_hour": HOURLY_PAYMENT,
        "currency": CURRENCY,
        **get_prolific_settings(),
        f"title": f"Nested games experiment (Chrome browser, ~{ESTIMATED_DURATION} minutes, {CURRENCY}{PAYMENT})",
        "description": "This experiment is about collective behavior and group outcomes.",
        'initial_recruitment_size': 2,
        "auto_recruit": False,
        "show_reward": False,
        "show_progress_bar": False,
    }

    timeline = CustomTimeline(
        consent_cococo_science_of_learning(
            DURATION=ESTIMATED_DURATION,
            PAYMENT=PAYMENT,
        ),
        ModularPage(
            label="tutorial",
            prompt=VideoPrompt(
                text=Markup(
                    "<p><span style='font-weight: bold;'>Please watch the following tutorial video.</span></p>"
                    "<br>"
                    "<p><span style='font-weight: bold;'>Important:</span> Please do not allow the experiment to timeout.</p>"
                    "<p>We cannot compensate you monetarily if you allow this page to timeout.</p>"
                    "<br>"
                ),
                text_align="center",
                video="../static/Instructions.mp4",
                controls=True,
            ),
            control=NextWithTimerControl(
                timeout=TIMEOUT_WATCH_TUTORIAL
            ),
            save_answer="tutorial",
            time_estimate=TIME_ESTIMATE_FOR_COMPENSATION_TUTORIAL_VIDEO,
            show_next_button=False,
        ),
        conditional(
            label="Checking if participant timeout",
            condition=lambda participant: participant.answer == "No answer",
            # logic_if_true=lambda participant: participant.var.set("experiment_failed", True),
            logic_if_true=UnsuccessfulEndPage(
                failure_tags=["waiting_pages_timeout"],
            ),
            logic_if_false=None,
        ),
        # personality_trial_maker,
        waiting_trial_maker.custom(
            SimpleGrouper(
                group_type="chain",
                initial_group_size=2,
                max_group_size="initial_group_size",
                min_group_size=2,
                join_existing_groups=False,
                waiting_logic=waiting_logic,
                waiting_logic_expected_repetitions=3,
                max_wait_time=TIMEOUT_WAITING_BIG_FIVE_QUESTIONS,
            ),
        ),
        CustomBarrier(
            id_="assign_roles",
            content="The experiment is loading, please wait a second...",
            on_release=assign_roles,
            timeout_between_barriers=STANDARD_TIMEOUT,
            participant_timeout_action="kick",
        ),
        NestedGameTrialMaker(
            id_="nested_games_trial_maker",
            trial_class=NestedGameTrial,
            node_class=NestedGameNode,
            chain_type="within",
            start_nodes=get_start_nodes,
            expected_trials_per_participant=NUMBER_OF_ROUNDS,
            max_trials_per_participant=NUMBER_OF_ROUNDS,
            chains_per_participant=1,
            # allow_repeated_nodes=True,
            target_n_participants=TARGET_PARTICIPANTS,
            wait_for_networks=True,
            max_nodes_per_chain=NUMBER_OF_ROUNDS,
            trials_per_node=1,
            sync_group_type="chain",
        ),
        get_final_survey(),
    )
