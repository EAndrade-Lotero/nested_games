from psynet.page import UnsuccessfulEndPage
from psynet.timeline import conditional

from .game_parameters import STANDARD_TIMEOUT
from .tutorial_pages import (
    OuterProposalTutorial, 
    InnerProposalTutorial, 
    ModifyScreenSize,
    TestSizePage,
)

def page_not_ok(participant) -> bool:
    return participant.answer != "Tutorial_Ok"

def get_tutorial_pages():
    return [
        TestSizePage(),
        conditional(
            label="check_tutorial_failed",
            condition=lambda participant: page_not_ok(participant),
            logic_if_true=UnsuccessfulEndPage(
                failure_tags=["tutorial_failed"],
            ),
            logic_if_false=None,
        ),
        # ModifyScreenSize(
        #     zoom_in_out="out",
        #     zoom_count=3,
        #     timeout=STANDARD_TIMEOUT,
        # ),
        # conditional(
        #     label="check_tutorial_failed",
        #     condition=lambda participant: page_not_ok(participant),
        #     logic_if_true=UnsuccessfulEndPage(
        #         failure_tags=["tutorial_failed"],
        #     ),
        #     logic_if_false=None,
        # ),
        # ModifyScreenSize(
        #     zoom_in_out="in",
        #     zoom_count=3,
        #     timeout=STANDARD_TIMEOUT,
        # ),
        # conditional(
        #     label="check_tutorial_failed",
        #     condition=lambda participant: page_not_ok(participant),
        #     logic_if_true=UnsuccessfulEndPage(
        #         failure_tags=["tutorial_failed"],
        #     ),
        #     logic_if_false=None,
        # ),
        # OuterProposalTutorial(
        #     avatar="me",
        #     timeout=STANDARD_TIMEOUT,
        # ),
        # conditional(
        #     label="check_tutorial_failed",
        #     condition=lambda participant: page_not_ok(participant),
        #     logic_if_true=UnsuccessfulEndPage(
        #         failure_tags=["tutorial_failed"],
        #     ),
        #     logic_if_false=None,
        # ),
        # OuterProposalTutorial(
        #     avatar="partner",
        #     timeout=STANDARD_TIMEOUT,
        # ),
        # conditional(
        #     label="check_tutorial_failed",
        #     condition=lambda participant: page_not_ok(participant),
        #     logic_if_true=UnsuccessfulEndPage(
        #         failure_tags=["tutorial_failed"],
        #     ),
        #     logic_if_false=None,
        # ),
        # InnerProposalTutorial(
        #     num_coins=5,
        #     timeout=STANDARD_TIMEOUT,
        # ),
        # conditional(
        #     label="check_tutorial_failed",
        #     condition=lambda participant: page_not_ok(participant),
        #     logic_if_true=UnsuccessfulEndPage(
        #         failure_tags=["tutorial_failed"],
        #     ),
        #     logic_if_false=None,
        # ),
        # InnerProposalTutorial(
        #     num_coins=7,
        #     timeout=STANDARD_TIMEOUT,
        # ),
        # conditional(
        #     label="check_tutorial_failed",
        #     condition=lambda participant: page_not_ok(participant),
        #     logic_if_true=UnsuccessfulEndPage(
        #         failure_tags=["tutorial_failed"],
        #     ),
        #     logic_if_false=None,
        # ),
    ]