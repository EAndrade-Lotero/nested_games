from psynet.timeline import Timeline, PageMakerFinishedError
from psynet.utils import get_logger, log_time_taken
from psynet.timeline import Page, PageMaker
from psynet.modular_page import ModularPage

logger = get_logger()


class EndRoundPage(ModularPage):

    def __init__(self, label, prompt, control, save_answer, time_estimate, **kwargs):
        super().__init__(
            label=label,
            prompt=prompt, 
            control=control, 
            save_answer=save_answer, 
            time_estimate=time_estimate, 
        )


class CustomTimeline(Timeline):

    can_fail_rounds = True

    def __init__(self, *args):
        super().__init__(*args)

    @log_time_taken
    def advance_page(self, experiment, participant):

        round_failed = CustomTimeline.get_round_failed(participant)
        logger.info(f"Do I see round failed? {round_failed}")

        if round_failed:

            finished = False

            while not finished:
                new_elt = self.increase_one_page(experiment, participant)

                if isinstance(new_elt, EndRoundPage):
                    finished = True
                    break

                try:
                    elt_id_max = participant.elt_id_max[-1]
                except IndexError:
                    raise Exception("End of timeline reached. No end round page found.")

                if participant.elt_id[-1] == participant.elt_id_max[-1]:
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
            # round_failed = participant.var.round_failed
            round_failed = getattr(participant.var, "round_failed")
            return round_failed
        else:
            return False
