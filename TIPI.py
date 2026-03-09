import os
from typing import List, Optional
from psynet.modular_page import ModularPage, SurveyJSControl
from psynet.page import InfoPage
from psynet.timeline import CodeBlock, Module, Response, join
from psynet.utils import get_translator
from markupsafe import Markup


_ = get_translator()
_p = get_translator(context=True)



class Personality(Module):
    """
    Ten-Item Personality Inventory-(TIPI)
    """

    def __init__(
        self,
        label: str = "tipi",
        subscales: Optional[List] = None,
        prompt: Optional[str] = None,
        info_page: Optional[InfoPage] = None,
    ):
        self.label = label
        self.subscales = subscales
        self.prompt = prompt

        if prompt is None:
            prompt = Markup("<h5>"
                      + _p("tipi-instruction", "Here are a number of personality traits that may or may not apply to you. ")
                      + _p("tipi-instruction", "For each statement, please indicate the extent to which you agree or disagree with that statement. ")
                      + _p("tipi-instruction", "You should rate the extent to which the pair of traits applies to you, even if one characteristic applies more strongly than the other. ")
                      + "</h5>"
                     )

        if info_page is None:
            info_page = InfoPage(
                (_("On the next screens, you will answer 3 surveys. Our goal is to understand how you view yourself and the society you live in, so there are no wrong answers. Please think carefully and be as honest as possible.")
            ),
                time_estimate=3,
            )

            if self.subscales is not None:
                questions = {
                    label: question_data()[label]
                    for label, data in question_data().items()
                    if any(subscale in self.subscales for subscale in data["subscales"])
                }
            else:
                questions = question_data()

            page_labels = list(set([questions[i]["page"] for i in questions.keys()]))

            def get_nonduplicate_items(list):
                new_list = []
                for elem in list:
                    if elem not in new_list:
                        new_list.append(elem)
                return new_list[0]

            pages = {
                page: {
                    block: {
                        "questions": {
                            q: questions[q]["prompt"]
                            for q in questions.keys()
                            if questions[q]["page"] == page and questions[q]["block"] == block
                        },
                        "choices": get_nonduplicate_items([questions[q]["choices"] for q in questions.keys() if
                                                        questions[q]["page"] == page and questions[q]["block"] == block]),
                        "labels": get_nonduplicate_items([questions[q]["labels"] for q in questions.keys()
                                                          if questions[q]["page"] == page and questions[q]["block"] == block]),
                        "blockprompts": get_nonduplicate_items([[questions[q]["blockprompt"]] for q in questions.keys() if
                                                       questions[q]["page"] == page and questions[q]["block"] == block]),
                    }
                    for block in
                    sorted(list(set([questions[i]["block"] for i in questions.keys() if questions[i]["page"] == page])))
                }
                for page in page_labels
            }

            self.elts = join(
                info_page,
                [
                    TIPIPage(
                        label,
                        prompt,
                        {p: {b: pages[p][b]["blockprompts"] for b in pages[p].keys()} for p in sorted(pages.keys())},
                        {p: {b: pages[p][b]["questions"] for b in pages[p].keys()} for p in sorted(pages.keys())},
                        {p: {b: pages[p][b]["choices"] for b in pages[p].keys()} for p in sorted(pages.keys())},
                        {p: {b: pages[p][b]["labels"] for b in pages[p].keys()} for p in sorted(pages.keys())},
                        module_label=self.label,
                    )
                ],
                self.save_scores,
            )
            super().__init__(self.label, self.elts)

    @property
    def save_scores(self):
        return CodeBlock(
            lambda participant: participant.var.set(
                self.label, self.compile_results(participant)
            )
        )

    def compile_results(self, participant):
        # get all responses for the participant from the database
        responses = Response.query.filter_by(participant_id=participant.id)
        # filter to retain only tipi responses for current module
        responses = [
            response
            for response in responses
            if response.question in ["tipi"]
               and response.metadata["tipi_label"] == self.label
        ]
        # calculate score for each question
        # raw_scores = {
        #     response.question: {q: a for d in [response.answer[b] for b in response.answer.keys()]
        #                         for q, a in d.items()}
        #     for response in responses
        # }
        response_scores = {
            response.question: {q: self.calculate_score(q, a) for d in
                                [response.answer[b] for b in response.answer.keys()]
                                for q, a in d.items()}
            for response in responses
        }
        # group scores by subscale
        grouped_scores = {}
        for question, score in response_scores[self.label].items():
            subscales = question_data()[question]["subscales"]
            for subscale in subscales:
                if subscale in grouped_scores.keys():
                    grouped_scores[subscale].append(score)
                else:
                    grouped_scores[subscale] = [score]
        # calculate arithmetic mean for each subscale
        mean_scores_per_scale = {
            group[0]: round(sum(group[1]) / len(group[1]), 7)
            if all(isinstance(item, int) for item in group[1])
            else group[1][0]
            for group in grouped_scores.items()
        }
        # calculate sum score for each subscale
        sum_scores_per_scale = {
            group[0]: sum(group[1])
            if all(isinstance(item, int) for item in group[1])
            else group[1][0]
            for group in grouped_scores.items()
        }

        return {
            # "raw_scores": raw_scores[self.label],
            "response_scores": response_scores[self.label],
            "mean_scores_per_scale": mean_scores_per_scale,
            "sum_scores_per_scale": sum_scores_per_scale,
        }

    @staticmethod
    def calculate_score(question, answer):
        if isinstance(answer, str):
            answer = answer.replace('"', "")
        raw_value = int(answer)
        # if "attention_check" in question_data()[question]["subscales"]:
        #     return True if answer == question_data()[question]["correct"] else False

        # adapt for your specific questionnaire how items should be scored
        if question_data()[question]["inverted"]:
            return (8 - raw_value)
        else:
            return raw_value


class TIPIPage(ModularPage):
    def __init__(
        self,
        label,
        prompt,
        blockprompts,
        questions,
        choices,
        labels=None,
        module_label="tipi",
    ):
        self.label = label
        self.prompt = prompt
        self.blockprompts = blockprompts
        self.questions = questions
        self.choices = choices
        self.labels = labels
        self.time_estimate = 50
        self.module_label = module_label


        control = SurveyJSControl(
            {
                "pages": [
                    {
                        "name": p,
                        "elements": [
                            {
                                "type": "matrix",
                                "name": f"p{p}_b{b}",
                                "title": self.blockprompts[p][b][0],
                                "titleLocation": "hidden" if self.blockprompts[p][b][0] == ' ' else "default",
                                "alternateRows": True,
                                "hideNumber": True,
                                "columns": [
                                        {
                                            "value": int(self.choices[p][b][i]),
                                            "text": self.labels[p][b][i],
                                        }
                                        for i in range(len(self.choices[p][b]))
                                ],
                                "rows": [
                                        {
                                            "value": q,
                                            "text": self.questions[p][b][q],
                                        }
                                        for q in self.questions[p][b].keys()

                                ],
                                "isAllRowRequired": True
                            }
                            for b in self.questions[p].keys()
                        ]
                    }
                    for p in self.questions.keys()
                ],
            },
        )
        super().__init__(
            self.label,
            self.prompt,
            control=control,
            time_estimate=self.time_estimate,
        )

    def metadata(self, **kwargs):
        return {"tipi_label": self.module_label}


def agreement_scale():
    return {
        "choices": list(range(1, 8)),
        "labels": [
            _p("tipi-choice", "Disagree strongly"),
            _p("tipi-choice", "Disagree moderately"),
            _p("tipi-choice", "Disagree a little"),
            _p("tipi-choice", "Neither agree nor disagree"),
            _p("tipi-choice", "Agree a little"),
            _p("tipi-choice", "Agree moderately"),
            _p("tipi-choice", "Agree strongly"),
        ],
    }


def question_data():
    return {
        "q_01": {
            "prompt": _p("tipi-item", "Extraverted, enthusiastic."),
            "inverted": False,
            "subscales": ["Extraversion"],
            "choices": agreement_scale()["choices"],
            "labels": agreement_scale()["labels"],
            "page": "01",
            "block": "01",
            "blockprompt": _("I see myself as:"),
        },
        "q_02": {
            "prompt": _p("tipi-item", "Critical, quarrelsome."),
            "inverted": True,
            "subscales": ["Agreeableness"],
            "choices": agreement_scale()["choices"],
            "labels": agreement_scale()["labels"],
            "page": "01",
            "block": "01",
            "blockprompt": _("I see myself as:"),
        },
        "q_03": {
            "prompt": _p("tipi-item", "Dependable, self-disciplined."),
            "inverted": False,
            "subscales": ["Conscientiousness"],
            "choices": agreement_scale()["choices"],
            "labels": agreement_scale()["labels"],
            "page": "01",
            "block": "01",
            "blockprompt": _("I see myself as:"),
        },
        "q_04": {
            "prompt": _p("tipi-item", "Anxious, easily upset."),
            "inverted": True,
            "subscales": ["Emotional_stability"],
            "choices": agreement_scale()["choices"],
            "labels": agreement_scale()["labels"],
            "page": "01",
            "block": "01",
            "blockprompt": _("I see myself as:"),
        },
        "q_05": {
            "prompt": _p("tipi-item", "Open to new experiences, complex."),
            "inverted": False,
            "subscales": ["Openness_to_experience"],
            "choices": agreement_scale()["choices"],
            "labels": agreement_scale()["labels"],
            "page": "01",
            "block": "01",
            "blockprompt": _("I see myself as:"),
        },
        "q_06": {
            "prompt": _p("tipi-item", "Reserved, quiet."),
            "inverted": True,
            "subscales": ["Extraversion"],
            "choices": agreement_scale()["choices"],
            "labels": agreement_scale()["labels"],
            "page": "01",
            "block": "01",
            "blockprompt": _("I see myself as:"),
        },
        "q_07": {
            "prompt": _p("tipi-item", "Sympathetic, warm."),
            "inverted": False,
            "subscales": ["Agreeableness"],
            "choices": agreement_scale()["choices"],
            "labels": agreement_scale()["labels"],
            "page": "01",
            "block": "01",
            "blockprompt": _("I see myself as:"),
        },
        "q_08": {
            "prompt": _p("tipi-item", "Disorganized, careless."),
            "inverted": True,
            "subscales": ["Conscientiousness"],
            "choices": agreement_scale()["choices"],
            "labels": agreement_scale()["labels"],
            "page": "01",
            "block": "01",
            "blockprompt": _("I see myself as:"),
        },
        "q_09": {
            "prompt": _p("tipi-item", "Calm, emotionally stable."),
            "inverted": False,
            "subscales": ["Emotional_stability"],
            "choices": agreement_scale()["choices"],
            "labels": agreement_scale()["labels"],
            "page": "01",
            "block": "01",
            "blockprompt": _("I see myself as:"),
        },
        "q_10": {
            "prompt": _p("tipi-item", "Conventional, uncreative."),
            "inverted": True,
            "subscales": ["Openness_to_experience"],
            "choices": agreement_scale()["choices"],
            "labels": agreement_scale()["labels"],
            "page": "01",
            "block": "01",
            "blockprompt": _("I see myself as:"),
        },
    }
