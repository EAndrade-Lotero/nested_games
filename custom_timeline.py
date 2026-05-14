from typing import Union

from markupsafe import Markup

from psynet.timeline import (
    Timeline,
    PageMakerFinishedError,
)
from psynet.utils import (
    get_logger,
    log_time_taken,
)
from psynet.timeline import (
    Page,
    PageMaker,
)
from psynet.modular_page import (
    ModularPage,
    Prompt,
    Control,
    NullControl,
)

logger = get_logger()


class EndExperimentPage(ModularPage):

    def __init__(
        self,
        show_failed_experiment: bool,
        **kwargs
    ) -> None:

        text = "<h3>Experiment finished</h3>"
        text += "<br>"
        text += "<p>Thank you for your participation.</p>"
        text += "<br>"

        if show_failed_experiment:
            text += "<p>(Timeout failure by one or both participants)</p>"
            text += "<br>"

        prompt = Markup(text)

        super().__init__(
            label="End of experiment",
            prompt=prompt,
            control=NullControl(),
            time_estimate=5,
        )


class EndRoundPage(ModularPage):

    def __init__(
        self,
        label: str,
        prompt: Union[Prompt | str],
        control: Control,
        save_answer: str,
        time_estimate: int,
        show_next_button: bool,
        **kwargs
    ) -> None:
        super().__init__(
            label=label,
            prompt=prompt, 
            control=control, 
            save_answer=save_answer, 
            time_estimate=time_estimate,
            show_next_button=show_next_button,
        )


class CustomTimeline(Timeline):

    can_fail_rounds = True

    def __init__(self, *args):
        super().__init__(*args)

    # @log_time_taken
    # def advance_page(self, experiment, participant):
    #     participant._in_advance_page = True
    #     try:
    #         if participant.pending_redirect:
    #             branch = participant.pending_redirect
    #             participant.pending_redirect = None
    #             self.redirect_to_branch(experiment, participant, branch)
    #
    #         finished = False
    #         while not finished:
    #             participant.elt_id[-1] += 1
    #
    #             try:
    #                 new_elt = self.get_current_elt(experiment, participant)
    #             except PageMakerFinishedError:
    #                 participant.elt_id = participant.elt_id[:-1]
    #                 participant.elt_id_max = participant.elt_id_max[:-1]
    #                 continue
    #             if isinstance(new_elt, PageMaker):
    #                 participant.elt_id.append(-1)
    #                 continue
    #
    #             new_elt.consume(experiment, participant)
    #
    #             if isinstance(new_elt, Page):
    #                 finished = True
    #     finally:
    #         participant._in_advance_page = False

    @log_time_taken
    def advance_page(self, experiment, participant):
        participant._in_advance_page = True
        try:
            if participant.pending_redirect:
                branch = participant.pending_redirect
                participant.pending_redirect = None
                self.redirect_to_branch(experiment, participant, branch)

            round_failed = CustomTimeline.get_round_failed(participant)

            if round_failed:

                finished = False
                new_elt = None

                while not finished:
                    new_elt = self.increase_one_page(experiment, participant)
                    # if new_elt is not None:
                    #     new_elt.consume(experiment, participant)

                    if isinstance(new_elt, EndRoundPage):
                        finished = True
                        break

                    try:
                        elt_id_max = participant.elt_id_max[-1]
                    except IndexError:
                        raise Exception("End of timeline reached. No end round page found.")

                    if participant.elt_id[-1] >= participant.elt_id_max[-1]:
                        raise Exception("End of timeline reached. No end round page found.")

                participant.var.round_failed = False

            else:

                finished = False
                while not finished:
                    new_elt = self.increase_one_page(experiment, participant)
                    if new_elt is not None:
                        new_elt.consume(experiment, participant)

                    if isinstance(new_elt, Page):
                        finished = True

        finally:
            participant._in_advance_page = False

    def increase_one_page(self, experiment, participant):
        participant.elt_id[-1] += 1

        try:
            new_elt = self.get_current_elt(experiment, participant)
        except PageMakerFinishedError:
            participant.elt_id = participant.elt_id[:-1]
            participant.elt_id_max = participant.elt_id_max[:-1]
            return None

        if isinstance(new_elt, PageMaker):
            participant.elt_id.append(-1)
            return None

        return new_elt

    @staticmethod
    def get_round_failed(participant):
        if participant.var.has("round_failed"):
            round_failed = getattr(participant.var, "round_failed")
            return round_failed
        else:
            return False

    # @staticmethod
    # def get_experiment_failed(participant):
    #     if participant.var.has("experiment_failed"):
    #         experiment_failed = getattr(participant.var, "experiment_failed")
    #         return experiment_failed
    #     else:
    #         return False
