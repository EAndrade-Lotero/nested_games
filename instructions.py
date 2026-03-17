from .game_paramters import ENDOWMENT

OBJECTIVE = f"""
    <h2>Instructions</h2>
    <br>
    <p>Welcome to the Proposals Game!</p>
    <br>
    <p>You will be paired with another participant. Each round consists of two phases:
    the preparation phase and the proposal phase. In the preparation phase, 
    participants will decided which one of them receives an endowment of {ENDOWMENT} coins. 
    In the proposal phase, the proposer will decide how to split the endowment between the 
    two players.</p>
    <br>
    <p><em>Objective:</em> Your goal is to accumulate as many coins as possible across all rounds.</p>
    <br>
"""

OUTER_DICTATOR_INSTRUCTION = f"""
    <h2>Preparation phase</h2>
    <br>
    <p>One participant will be asked to choose which of the two players
    will act as the <strong>PROPOSER</strong>.</p>
    <br>
"""

OUTER_ULTIMATUM_INSTRUCTION = f"""
    <h2>Preparation phase</h2>
    <br>
    <p>One participant will be asked to propose which of the two players
    will act as the <strong>PROPOSER</strong>. The other participant will then
    decide whether to accept or reject this proposal. If the proposal is
    accepted, the game continues. If it is rejected, the round ends.</p>
    <br>
"""

SAME_ROLE_INSTRUCTION = f"""
    <p>In every round, the same participant will decide who will be the
    <strong>PROPOSER</strong>.</p>
    <br>
"""

RANDOM_ROLE_INSTRUCTION = f"""
    <p>In every round, the system will randomly select which participant
    decides who will be the <strong>PROPOSER</strong>.</p>
    <br>
"""

INNER_ULTIMATUM_INSTRUCTIONS = f"""
    <h2>Proposal phase</h2>
    <br>
    <p>The <strong>PROPOSER</strong> offers some of their endowment to the
    <strong>RESPONDER</strong>. The RESPONDER may either accept or reject the
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
    <p><strong>Round 1:</strong> 
    <p><em>Preparation phase:</em> Player 1 gets to propose who will receive the endowment of {ENDOWMENT} coins.
    <p>Player 1 proposes Player 2 to be the PROPOSER.</p>
"""

ADD_OUTER_ACCEPTANCE_INSTRUCTION = f"""
    <p>Player 2 accepts to be the PROPOSER.</p>
"""

EXAMPLE_PROPOSAL_PHASE = f"""
    <br>
    <p><em>Proposal phase:</em> Player 2 proposes how to split the {ENDOWMENT} coins between the two players.</p>
    <br>
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