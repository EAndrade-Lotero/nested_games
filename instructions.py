from .game_paramters import ENDOWMENT

OBJECTIVE = f"""
    <h2>Instructions</h2>
    <br>
    <p>Welcome to the Proposals Game!</p>
    <br>
    <p>You will be paired with another participant. 
    In each round, one of you will receive an endowment of {ENDOWMENT} coins.
    This participant will be the <strong>PROPOSER</strong>. The PROPOSER may offer
    some portion of these coins to the other participant, who will be the
    <strong>RESPONDER</strong>.</p>
    <br>
    <p><em>Objective:</em> Your goal in the game is to accumulate as many coins as possible.</p>
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
