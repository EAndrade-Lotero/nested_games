# Module with the game parameters
import numpy as np

RNG = np.random.default_rng(42)

ENDOWMENT = 10
CURRENCY = "$"

# Waiting times
WAIT_PAGE_TIME = 1.25  # Refresh interval at barrier
MAX_WAITING_PROPOSALS = 45 # Max wait at a barrier
MAX_WAITING_FOR_OTHER = 1.5 * MAX_WAITING_PROPOSALS
MAX_WAIT_TIME = 45
MAX_WAITING_BIG_FIVE_QUESTIONS = 10
MAX_WAITING_SEEING_INFO = 15

# Repetitions
NUM_BIG_FIVE_QUESTIONS = 2
NUMBER_OF_REPEATED_GAMES = 2

REWARD_SCALING_FACTOR = 0.01
MAX_BONUS_REWARD = 7

ASSETS_PATHS = {
    "drag_and_drop_url": "static/drag_and_drop.gif",
}
