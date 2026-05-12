from markupsafe import Markup

from psynet.modular_page import (
    ModularPage,
    NullControl,
    VideoPrompt,
)
from psynet.timeline import Event

from .custom_front_end import (
    TimeoutPrompt,
    NextWithTimerControl,
)
from .game_parameters import (
    STANDARD_TIMEOUT,
    TIMEOUT_WATCH_TUTORIAL,
)

class InstructionPage(ModularPage):

    def __init__(self, time_estimate:int):
        super().__init__(
            label="initial_recommendations",
            prompt=TimeoutPrompt(
                text=Markup(
                    f"<h3>Before we start the game...</h3>"
                    f"<p>You are about to play a multi-player game with other participants in real-time.</p>"
                    f"<p>Out of respect for them, we ask you to remain active until the end of the game.</p>"
                    f"<p>If you are away from your keyboard, you will be removed from the game and your submission may be not be approved.</p>"
                    f"<p>Please click 'Next' when you are ready to start.</p>"
                ),
                timeout=STANDARD_TIMEOUT,
                use_sounds=True,
                show_rounds=False,
                ask_not_to_loose_focus=True,
            ),
            control=NullControl(),
            time_estimate=time_estimate,
            events={
                "submitEnable": Event(
                    is_triggered_by="trialStart",
                    delay=5.0
                ),
            },
        )

class TutorialVideoPage(ModularPage):

    def __init__(self, time_estimate:int):
        super().__init__(
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
            time_estimate=time_estimate,
            show_next_button=False,
        )