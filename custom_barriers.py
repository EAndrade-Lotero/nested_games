from typing import Optional, Callable

from psynet.page import WaitPage
from psynet.sync import GroupBarrier
from psynet.timeline import Page

from .game_paramters import (
    WAIT_PAGE_TIME,
    TIMEOUT_WAITING_FOR_OTHER,
    TIMEOUT_BETWEEN_BARRIERS,
)


class CustomBarrier(GroupBarrier):

    def __init__(
        self,
        id_:str,
        content:Optional[str|None]=None,
        active_participant:Optional[bool | None]=None,
        expected_repetitions:Optional[int]=1,
        timeout_at_barrier:Optional[int|None]=None,
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

        if timeout_at_barrier is None:
            timeout_at_barrier = TIMEOUT_WAITING_FOR_OTHER * expected_repetitions

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


