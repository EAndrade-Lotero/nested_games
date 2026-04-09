from psynet.timeline import Timeline, PageMakerFinishedError
from psynet.utils import get_logger, log_time_taken
from psynet.timeline import Page, PageMaker
from psynet.modular_page import ModularPage

logger = get_logger()


class CustomTimeline(Timeline):

    can_fail_rounds = True

    def __init__(self, *args):
        super().__init__(*args)
        self.end_of_round_page_idx = self.determine_end_of_round_page_idx()

    def determine_end_of_round_page_idx(self) -> int:
        # Determine end_round page
        end_of_round_page_idx = None

        page_labels = []
        for elt in self.elts['main']:
            page_labels.append(str(type(elt)))

        if self.can_fail_rounds:


            for i, elt in enumerate(self.elts['main']):
                if isinstance(elt, ModularPage):
                    if hasattr(elt, "label"):
                        if elt.label == "end_of_round_page":
                            end_of_round_page_idx = i - 1
                            break

            if end_of_round_page_idx is None:

                error_message = "Error: can_fail_rounds = True but end_of_round_page_idx is None.\n"
                error_message += "A ModularPage with label = 'end_of_round_page' is required in the timeline."
                error_message += f"\n{page_labels}"
                raise Exception(error_message)

        logger.info(f"CustomTimeLine: end round idx is set to {end_of_round_page_idx}")

        return end_of_round_page_idx

    @staticmethod
    def get_round_failed(participant):
        if participant.var.has("round_failed"):
            return getattr(participant.var, "round_failed")
        else:
            return False

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

    @log_time_taken
    def advance_page(self, experiment, participant):

        round_failed = CustomTimeline.get_round_failed(participant)
        current_elt_id = participant.elt_id[-1]

        if round_failed and current_elt_id < self.end_of_round_page_idx:

            while participant.elt_id[-1] <= self.end_of_round_page_idx:
                new_elt = self.increase_one_page(experiment, participant)
                if new_elt is not None:
                    new_elt.consume(experiment, participant)

            participant.var.round_failed = False

        else:

            finished = False
            while not finished:
                new_elt = self.increase_one_page(experiment, participant)
                if new_elt is not None:
                    new_elt.consume(experiment, participant)

                if isinstance(new_elt, Page):
                    finished = True
