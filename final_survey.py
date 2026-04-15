from markupsafe import Markup

from psynet.timeline import join
from psynet.modular_page import ModularPage, SurveyJSControl

from .game_paramters import (
    TIMEOUT_PROPOSALS,
)
from .custom_front_end import TimeoutPrompt

def get_final_survey():

    list_of_pages = join(
        ModularPage(
            label="Strategy",
            prompt=TimeoutPrompt(
                text=Markup("""
                    <p></p>
                """),
                timeout=TIMEOUT_PROPOSALS * 5,
            ),
            control=SurveyJSControl(
                {
                    "logoPosition": "right",
                    "pages": [
                        {
                            "name": "page1",
                            "elements": [
                                {
                                    "type": "text",
                                    "name": "verbal_strategy",
                                    "title": "In two or three sentences, please describe your strategy for the game.",
                                },
                                {
                                    "type": "rating",
                                    "name": "own_benefit",
                                    "title": "When making a decisions, how much did you take into consideration your OWN benefit?",
                                    "rateValues": [
                                        {"value": "1", "text": "1"},
                                        {"value": "2", "text": "2"},
                                        {"value": "3", "text": "3"},
                                        {"value": "4", "text": "4"},
                                        {"value": "5", "text": "5"},
                                    ],
                                    "minRateDescription": "Not at all",
                                    "maxRateDescription": "Very much",
                                },
                                {
                                    "type": "rating",
                                    "name": "other_benefit",
                                    "title": "When making a decisions, how much did you take into consideration the benefit of your PARTNER?",
                                    "rateValues": [
                                        {"value": "1", "text": "1"},
                                        {"value": "2", "text": "2"},
                                        {"value": "3", "text": "3"},
                                        {"value": "4", "text": "4"},
                                        {"value": "5", "text": "5"},
                                    ],
                                    "minRateDescription": "Not at all",
                                    "maxRateDescription": "Very much",
                                },
                            ],
                        },
                        {
                            "name": "page2",
                            "elements": [
                                {
                                    "type": "rating",
                                    "name": "importance_of_fairness",
                                    "title": "When making a decision, how much did you take into consideration the fairness of the decision?",
                                    "rateValues": [
                                        {"value": "1", "text": "1"},
                                        {"value": "2", "text": "2"},
                                        {"value": "3", "text": "3"},
                                        {"value": "4", "text": "4"},
                                        {"value": "5", "text": "5"},
                                    ],
                                    "minRateDescription": "Not at all",
                                    "maxRateDescription": "Very much",
                                },
                                {
                                    "type": "rating",
                                    "name": "assessment_of_fairness",
                                    "title": "How fair was the final result of the game?",
                                    "rateValues": [
                                        {"value": "1", "text": "1"},
                                        {"value": "2", "text": "2"},
                                        {"value": "3", "text": "3"},
                                        {"value": "4", "text": "4"},
                                        {"value": "5", "text": "5"},
                                    ],
                                    "minRateDescription": "Very unfair",
                                    "maxRateDescription": "Very fair",
                                },
                            ],
                        },
                    ],
                },
            ),
            time_estimate=TIMEOUT_PROPOSALS,
        ),
    )

    return list_of_pages
