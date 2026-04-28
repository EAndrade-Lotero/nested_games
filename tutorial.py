from psynet.page import UnsuccessfulEndPage
from psynet.timeline import conditional

from .game_paramters import TIMEOUT_PROPOSALS
from .tutorial_pages import (
    OuterProposalTutorial, 
    InnerProposalTutorial, 
    ModifyScreenSize,
)

def page_not_ok(participant) -> bool:
    return participant.answer != "Tutorial_Ok"

def get_tutorial_pages():
    return [
        ModifyScreenSize(
            zoom_in_out="out",
            zoom_count=3,
            time_estimate=TIMEOUT_PROPOSALS,
        ),
        conditional(
            label="check_tutorial_failed",
            condition=lambda participant: page_not_ok(participant),
            logic_if_true=UnsuccessfulEndPage(
                failure_tags=["tutorial_failed"],
            ),
            logic_if_false=None,
        ),
        ModifyScreenSize(
            zoom_in_out="in",
            zoom_count=3,
            time_estimate=TIMEOUT_PROPOSALS,
        ),
        conditional(
            label="check_tutorial_failed",
            condition=lambda participant: page_not_ok(participant),
            logic_if_true=UnsuccessfulEndPage(
                failure_tags=["tutorial_failed"],
            ),
            logic_if_false=None,
        ),
        OuterProposalTutorial(
            avatar="me",
            time_estimate=TIMEOUT_PROPOSALS,
        ),
        conditional(
            label="check_tutorial_failed",
            condition=lambda participant: page_not_ok(participant),
            logic_if_true=UnsuccessfulEndPage(
                failure_tags=["tutorial_failed"],
            ),
            logic_if_false=None,
        ),
        OuterProposalTutorial(
            avatar="partner",
            time_estimate=TIMEOUT_PROPOSALS,
        ),
        conditional(
            label="check_tutorial_failed",
            condition=lambda participant: page_not_ok(participant),
            logic_if_true=UnsuccessfulEndPage(
                failure_tags=["tutorial_failed"],
            ),
            logic_if_false=None,
        ),
        InnerProposalTutorial(
            num_coins=5,
            time_estimate=TIMEOUT_PROPOSALS,
        ),
        conditional(
            label="check_tutorial_failed",
            condition=lambda participant: page_not_ok(participant),
            logic_if_true=UnsuccessfulEndPage(
                failure_tags=["tutorial_failed"],
            ),
            logic_if_false=None,
        ),
        InnerProposalTutorial(
            num_coins=7,
            time_estimate=TIMEOUT_PROPOSALS,
        ),
        conditional(
            label="check_tutorial_failed",
            condition=lambda participant: page_not_ok(participant),
            logic_if_true=UnsuccessfulEndPage(
                failure_tags=["tutorial_failed"],
            ),
            logic_if_false=None,
        ),
    ]