from typing import Optional, Callable

from psynet.page import WaitPage
from psynet.sync import GroupBarrier
from psynet.modular_page import ModularPage

from .game_paramters import WAIT_PAGE_TIME, MAX_WAITING_SEEING_INFO


class CustomBarrier(GroupBarrier):

    def __init__(
        self,
        id_:str,
        wait_page:Optional[ModularPage|None]=None,
        on_release:Optional[Callable]=None,
    ) -> None:

        if wait_page is None:
            wait_page = WaitPage(
                wait_time=WAIT_PAGE_TIME,
                content="Please wait while the other participant makes their move..."
            ),
        super().__init__(
            id_=id_,
            group_type="chain",
            on_release=on_release,
            waiting_logic=wait_page,
            max_wait_time=MAX_WAITING_SEEING_INFO,
            waiting_logic_expected_repetitions=15,
            # participant_timeout=MAX_WAITING_SEEING_INFO,
            # participant_timeout_action="fail",
        )
        pass

