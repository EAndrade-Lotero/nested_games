from typing import Optional, Callable, List

from psynet.page import WaitPage
from psynet.sync import GroupBarrier
from psynet.timeline import Page
from psynet.participant import Participant

from .game_paramters import (
    WAIT_PAGE_TIME,
    TIMEOUT_WAITING_FOR_OTHER,
    TIMEOUT_BETWEEN_BARRIERS,
)
from psynet.utils import get_logger

logger = get_logger()

class CustomBarrier(GroupBarrier):

    def __init__(
        self,
        id_:str,
        content:Optional[str|None]=None,
        active_participant:Optional[bool | None]=None,
        timeout_at_barrier:Optional[int]=TIMEOUT_WAITING_FOR_OTHER,
        timeout_between_barriers:Optional[int]=TIMEOUT_BETWEEN_BARRIERS,
        wait_page:Optional[Page|None]=None,
        on_release:Optional[Callable]=None,
    ) -> None:

        if active_participant is not None:
            if active_participant:
                wait_page = WaitPage(
                    wait_time=0.25,
                    content="Moving on..."
                ),

        if wait_page is None:
            if content is None:
                content = "Waiting for your partner..."
            wait_page = WaitPage(
                wait_time=WAIT_PAGE_TIME,
                content=content,
            ),

        expected_repetitions = timeout_at_barrier // WAIT_PAGE_TIME
        timeout_between_barriers += timeout_at_barrier

        super().__init__(
            id_=id_,
            group_type="chain",
            on_release=on_release,
            waiting_logic=wait_page,
            max_wait_time=timeout_at_barrier,
            waiting_logic_expected_repetitions=expected_repetitions,
            participant_timeout=timeout_between_barriers,
            participant_timeout_action="fail",
        )

    def choose_who_to_release(self, waiting_participants: List[Participant]) -> List[Participant]:

        participants = super().choose_who_to_release(waiting_participants)

        # round_failed = False
        # for participant in participants:
        #     if participant.var.has("round_fail"):
        #         round_failed = True
        #         break
        #
        # logger.info("-" * 60)
        # logger.info(f"Did round fail?{round_failed} ")
        # logger.info("-" * 60)
        #
        # if round_failed:
        #     for participant in waiting_participants:
        #         participant.var.set("round_fail", True)

        return participants

