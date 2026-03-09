import pandas as pd
from psynet.trial.static import (
    StaticTrialMaker,
    StaticTrial,
    StaticNode,
)
from psynet.modular_page import (
    ModularPage,
    PushButtonControl,
)

from .game_paramters import RNG

short_items = pd.read_csv("static/big_five_short.csv").to_dict(orient="records")
RNG.shuffle(short_items)

personality_nodes = [
    StaticNode(
        definition={
            "question_id": item["full_position"],
            "question_text": item["item"],
        },
    ) for item in short_items
]


class PersonalityTrial(StaticTrial):
    time_estimate = 3

    def show_trial(self, experiment, participant):

        question = self.definition["question"]
        text = "We are waiting for other participants.\n"
        text += "In the meantime, please Please report how accurately this describes you:\n"
        text += f"I see myself as someone who {question}?"

        return ModularPage(
            "waiting_trial",
            text,
            PushButtonControl(
                ["Very Inaccurate", "Moderately Inaccurate", "Neither Accurate Nor Inaccurate", "Moderately Accurate", "Very Accurate"],
            ),
        )
ß

class PersonalityTrialMaker(StaticTrialMaker):
    def prioritize_networks(self, networks, participant, experiment):
        previous_trials = participant.alive_trials
        items_completed = {
            trial.definition.get("order", None)
            for trial in previous_trials
            if trial.complete
        }
        network_order = {
            network.id: network.head.definition.get("order", 0) for network in networks
        }
        return sorted(
            networks,
            key=lambda x: (1 if network_order[x.id] in items_completed else 0, network_order[x.id]),
        )

    def custom_network_filter(self, candidates, participant):
        previous_trials = participant.alive_trials
        items_completed = {
            trial.definition.get("order", None)
            for trial in previous_trials
            if trial.complete
        }
        return [
            candidate
            for candidate in candidates
            if candidate.head.definition.get("order", None) not in items_completed
        ]

