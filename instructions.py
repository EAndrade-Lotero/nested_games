from .game_paramters import ENDOWMENT, ASSETS_PATHS


STYLE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Welcome to the coordinator and foragers game!</title>
    <style>
        body {
            font-family: "Book Antiqua", "Palatino Linotype", Palatino, serif;
            font-size: 14pt;
            line-height: 1.5;
            max-width: 800px;
            margin: 40px auto;
            padding: 0 20px;
            background-color: #f5ecd9;
            background-image:
                radial-gradient(circle at top left, rgba(0,0,0,0.06), transparent 60%),
                radial-gradient(circle at bottom right, rgba(0,0,0,0.06), transparent 60%);
        }

        h1 {
            text-align: center;
            font-size: 2em;
            margin-bottom: 0.2em;
        }

        h2 {
            margin-top: 1.8em;
            margin-bottom: 0.4em;
            font-size: 1.3em;
        }

        p {
            margin: 0.4em 0;
            text-align: justify;
        }

        ul {
            margin: 0.4em 0 0.4em 1.5em;
        }

        li {
            margin: 0.2em 0;
        }

        .formula-block {
            margin: 0.6em 0 0.8em 1.5em;
            font-family: "Courier New", Courier, monospace;
        }

        .final-note {
            margin-top: 2em;
            font-weight: bold;
        }
    </style>
</head>
<body>

"""

OBJECTIVE = f"""
    {STYLE}
    <h2>Instructions</h2>
    <br>
    <p>Welcome to the Nested Games experiment!</p>
    <br>
    <p>You will be paired with another participant. Each round consists of two phases:
    the preparation phase and the proposal phase. In the preparation phase, 
    participants will decided which one of them receives an endowment of {ENDOWMENT} coins. 
    In the proposal phase, the proposer will decide how to split the endowment between the 
    two players.</p>
    <br>
    <p><em>Goal:</em> Your goal is to accumulate as many coins as possible across all rounds.</p>
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
    <p>The other participant will then decide whether to accept or reject this proposal. 
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
    <p>The <strong>PROPOSER</strong> offers some of their coins to the
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
    <p>The <strong>PROPOSER</strong> decides how many coins to give to the
    <strong>RESPONDER</strong> and keeps the remaining coins.</p>
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