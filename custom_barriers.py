from typing import Optional, Callable

from psynet.page import WaitPage
from psynet.sync import GroupBarrier
from psynet.timeline import Page

from .game_paramters import (
    WAIT_PAGE_TIME,
    MAX_WAITING_FOR_OTHER,
)


class CustomBarrier(GroupBarrier):

    def __init__(
        self,
        id_:str,
        content:Optional[str|None]=None,
        active_participant:Optional[bool | None]=None,
        wait_page:Optional[Page|None]=None,
        on_release:Optional[Callable]=None,
    ) -> None:

        if active_participant is not None:
            if active_participant:
                wait_page = WaitPage(
                    wait_time=WAIT_PAGE_TIME,
                    content="Moving on..."
                ),

        if wait_page is None:
            if content is None:
                content = "Waiting for your partner..."
            wait_page = WaitPage(
                wait_time=WAIT_PAGE_TIME,
                content=content,
            ),

        super().__init__(
            id_=id_,
            group_type="chain",
            on_release=on_release,
            waiting_logic=wait_page,
            max_wait_time=MAX_WAITING_FOR_OTHER,
            waiting_logic_expected_repetitions=10,
            # participant_timeout=MAX_WAITING_SEEING_INFO,
            # participant_timeout_action="fail",
        )


