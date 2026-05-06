from typing import Optional, Callable, Literal

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
        participant_timeout_action: Literal["kick", "fail"]="fail",
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

        # expected_repetitions = timeout_at_barrier // WAIT_PAGE_TIME
        # If expected repetitions only bears on time estimate, keep at 1
        expected_repetitions = 1
        timeout_between_barriers += timeout_at_barrier

        super().__init__(
            id_=id_,
            group_type="chain",
            on_release=on_release,
            waiting_logic=wait_page,
            max_wait_time=timeout_at_barrier,
            waiting_logic_expected_repetitions=expected_repetitions,
            participant_timeout=timeout_between_barriers,
            participant_timeout_action=participant_timeout_action,
        )

        # Set fixed time credit so that time 'credit' that the participant receives will be capped
        # according to the estimate derived from ``waiting_logic`` and ``waiting_logic_expected_repetitions``
        self.fix_time_credit = True

    def can_participant_exit(self, participant: Participant) -> bool:
        super_condition = super().can_participant_exit(participant)
        round_failed = CustomBarrier.get_round_failed(participant)
        return super_condition or round_failed

    @staticmethod
    def get_round_failed(participant: Participant) -> bool:

        if participant.sync_group is None:
            return True

        participants = participant.sync_group.participants

        if len(participants) < 2:
            return True

        for p in participants:
            if p.var.has("round_failed"):
                return getattr(p.var, "round_failed")

        return False
