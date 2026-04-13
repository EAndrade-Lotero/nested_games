from markupsafe import Markup

from psynet.timeline import join
from psynet.graphics import Prompt
from psynet.modular_page import (
    ModularPage,
    PushButtonControl,
    NullControl,
)

from .game_paramters import (
    ENDOWMENT,
    TIMEOUT_PROPOSALS,
    NUMBER_OF_REPEATED_GAMES,
)
from .custom_front_end import TimeoutPrompt
from .custom_pages import CustomInfoPage

OBJECTIVE = f"""
    <h2>Instructions</h2>
    <br>
    <p>Welcome to the <strong>"Who is the proposer?"</strong> experiment!</p>
    <br>
    <p>You will be paired with another participant to play {NUMBER_OF_REPEATED_GAMES} rounds.</p>
    <br>
    <p>Each round consists of two phases:</p>
    <ul>
        <li>
            <strong>Preparation phase:</strong> Both participants decide which one of them will receive an endowment of {ENDOWMENT} coins.
        </li>
        <li>
            <strong>Proposal phase:</strong> The selected proposer decides how to split the endowment between the two players.
        </li>
    </ul>
    <br>
    <p><em>Goal:</em> Your objective is to accumulate as many coins as possible across all rounds.</p>
    <br>
"""

OUTER_DICTATOR_INSTRUCTION = lambda context: f"""
    <h2>Preparation phase</h2>
    <br>
    <p>One participant will be asked to choose which of the two players
    will act as the <strong>PROPOSER</strong>.</p>
    <br>
    <img src='static/drag_and_drop.gif' alt="Drag and dop avatar" width=400px/>
"""

OUTER_ULTIMATUM_INSTRUCTION = f"""
    <h2>Preparation phase</h2>
    <br>
    <p>One participant will be asked to propose which of the two players
    will act as the <strong>PROPOSER</strong>. </p>
    <img src='static/drag_and_drop.gif' alt="Drag and dop avatar" width=400px/>
    <p>The other participant will decide whether to accept or reject this proposal. 
    If the proposal is accepted, the game continues. If it is rejected, the round ends.</p>
    <br>
"""

SAME_ROLE_INSTRUCTION = f"""
    <p>In every round, the same participant will propose who will be the
    <strong>PROPOSER</strong>.</p>
    <br>
"""

RANDOM_ROLE_INSTRUCTION = f"""
    <p>In every round, the system will randomly select which participant
    gets to propose who will be the <strong>PROPOSER</strong>.</p>
    <br>
"""

INNER_ULTIMATUM_INSTRUCTIONS = f"""
    <h2>Proposal phase</h2>
    <br>
    <p>The <strong>PROPOSER</strong> will offer some of their coins to the
    <strong>RESPONDER</strong>.</p>
    <img src='static/slider.gif' alt="Drag and dop avatar" width=400px/>
    <p>The RESPONDER may either accept or reject the
    offer. If the RESPONDER rejects the offer, neither participant receives
    any coins for that round.</p>
    <br>
"""

INNER_DICTATOR_INSTRUCTIONS = f"""
    <h2>Proposal phase</h2>
    <br>
    <p>The <strong>PROPOSER</strong> will decide how many coins to give to the
    <strong>RESPONDER</strong> and will keep the remaining coins.</p>
    <br>
"""

EXAMPLE_PREPARATION_PHASE = f"""
    <h2>Example</h2>
    <br>
    <p><strong>ROUND 1:</strong> 
    <p><em>Preparation phase:</em> Player 1 gets to propose who will receive the endowment of {ENDOWMENT} coins.
    <p>Player 1 proposes Player 2 to be the PROPOSER.</p>
"""

ADD_OUTER_ACCEPTANCE_INSTRUCTION = f"""
    <p>Player 2 accepts to be the PROPOSER.</p>
"""

EXAMPLE_PROPOSAL_PHASE = f"""
    <br>
    <p><em>Proposal phase:</em> Player 2 proposes how to split the {ENDOWMENT} coins between the two players.</p>
    <p>Player 2 proposes to give 4 coins to Player 1 and keep the remaining 6 coins.</p>
"""

ADD_INNER_ACCEPTANCE_INSTRUCTION = f"""
    <p>Player 1 accepts the 4 coins and Player 2 keeps the remaining 6 coins.</p>
"""

EXAMPLE_RANDOM = f"""
    <br>
    <p>Moving to the next round, the player that gets to propose who will be the PROPOSER is randomly selected.</p>
"""

EXAMPLE_CONSTANT = f"""
    <br>
    <p>Every round, the same player gets to propose who will be the PROPOSER.</p>
"""

def get_instructions(
        outer_game: str,
        inner_game: str,
        transition: str,
        outer_role: str,
    ):

    example_text = EXAMPLE_PREPARATION_PHASE
    if outer_game == "dictator":
        preparation_phase = OUTER_DICTATOR_INSTRUCTION
    elif outer_game == "ultimatum":
        preparation_phase = OUTER_ULTIMATUM_INSTRUCTION
        example_text += ADD_OUTER_ACCEPTANCE_INSTRUCTION
    else:
        raise ValueError("outer_game must be dictator or ultimatum")

    example_text += EXAMPLE_PROPOSAL_PHASE
    if inner_game == "dictator":
        proposal_phase = INNER_DICTATOR_INSTRUCTIONS
    elif inner_game == "ultimatum":
        proposal_phase = INNER_ULTIMATUM_INSTRUCTIONS
        example_text += ADD_INNER_ACCEPTANCE_INSTRUCTION
    else:
        raise ValueError("outer_game must be dictator or ultimatum")

    if transition == "random":
        preparation_phase += RANDOM_ROLE_INSTRUCTION
        example_text += EXAMPLE_RANDOM
    elif transition == "constant":
        preparation_phase += SAME_ROLE_INSTRUCTION
        example_text += EXAMPLE_CONSTANT
    else:
        raise ValueError("transition must be 'random' or 'constant'")

    list_of_pages = join(
        # CustomInfoPage(
        #     Markup(OBJECTIVE),
        #     time_estimate=TIMEOUT_PROPOSALS,
        # ),
        # CustomInfoPage(
        #     Markup(preparation_phase),
        #     time_estimate=TIMEOUT_PROPOSALS,
        # ),
        # CustomInfoPage(
        #     Markup(proposal_phase),
        #     time_estimate=TIMEOUT_PROPOSALS,
        # ),
        ModularPage(
            label="Instructions",
            prompt=TimeoutPrompt(
                text=Markup(example_text),
                timeout=TIMEOUT_PROPOSALS,
            ),
            control=NullControl(),
            time_estimate=TIMEOUT_PROPOSALS,
        ),
    )

    return list_of_pages
