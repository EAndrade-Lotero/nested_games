# Module with custom prompts and controls

##########################################################################################
# Imports
##########################################################################################
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from psynet.modular_page import (
    Control,
)
from psynet.utils import get_logger


logger = get_logger()
Pos = Tuple[int, int]  # (x, y)

###########################################
# Custom prompts
###########################################


###########################################
# Custom controls
###########################################

class TweakingOverheadControl(Control):
    macro = "overhead"
    external_template = "tweaking-overhead-control.html"

    def __init__(
        self,
        investment: float,
        sliders: Dict[str, float],
    ) -> None:
        super().__init__()
        if 1 <= investment <= COORDINATOR_ENDOWMENT:
            self.remaining_investment = COORDINATOR_ENDOWMENT - investment
        else:
            self.remaining_investment = COORDINATOR_ENDOWMENT - int(investment * COORDINATOR_ENDOWMENT)
        self.overhead = sliders["overhead"]
        self.wages = sliders["wages"]
        self.prerogative = sliders["prerogative"]
        self.coins = [50, 30, 20]
        self.num_foragers = NUM_FORAGERS


class TweakingSocialContract(Control):
    macro = "slider_and_coins"
    external_template = "tweaking-control.html"

    def __init__(
        self,
        investment: float,
        sliders: Dict[str, float],
        coins: List[int],
        reach_urls: List[str],
    ) -> None:
        super().__init__()
        if 1 <= investment <= COORDINATOR_ENDOWMENT:
            self.remaining_investment = COORDINATOR_ENDOWMENT - investment
        else:
            self.remaining_investment = COORDINATOR_ENDOWMENT - int(investment * COORDINATOR_ENDOWMENT)
        self.overhead = sliders["overhead"]
        self.wages = sliders["wages"]
        self.prerogative = sliders["prerogative"]
        logger.info(f"Coins shown in tweaking: {coins}")
        self.coins = coins
        self.num_foragers = NUM_FORAGERS
        self.reach_1_url = reach_urls[0]
        self.reach_2_url = reach_urls[1]
        self.reach_3_url = reach_urls[2]
        self.fuel_per_move = FUEL_PER_MOVE


class CustomSliderControl(Control):
    macro = "slider_values"
    external_template = "slider-control.html"

    def __init__(
        self,
            start_value: float,
            min_value: float,
            max_value: float,
            n_steps: int,
            use_percentage: Optional[bool] = False,
            left_label: Optional[str] = "",
            right_label: Optional[str] = "",
            integer_rule: Optional[bool] = False,
    ) -> None:
        super().__init__()

        # Sanity checks
        assert(min_value <= max_value), f"Error: min_value must be <= max_value (got {min_value} vs. {max_value})"
        assert(min_value <= start_value), f"Error: min_value must be <= start_value (got {min_value} vs. {start_value})"
        assert(start_value <= max_value), f"Error: start_value must be <= max_value (got {start_value} vs. {max_value})"
        assert(n_steps >= 1)
        if use_percentage:
            assert(min_value == 0)
            assert(max_value == 1)

        # Assign attributes
        self.start_value = start_value
        self.min_value = min_value
        self.max_value = max_value
        self.n_steps = n_steps
        self.use_percentage = use_percentage
        self.left_label = left_label
        self.right_label = right_label
        self.integer_rule = integer_rule

    def format_answer(self, raw_answer, **kwargs):
        try:
            return float(raw_answer)
        except (ValueError, AssertionError):
            return f"INVALID_RESPONSE"


class PositioningControl(Control):
    macro = "positioning_area"
    external_template = "positioning-control.html"

    def __init__(
        self,
        world_path:str,
        context:Dict[str, Path],
        investment:float,
    ) -> None:
        super().__init__()
        # Create world
        self.world = World.generate_from_json(Path(world_path))
        # logger.info(f"Coins created at: {self.world.coin_positions()}")
        # Check investment (used in probability of showing a coin)
        assert investment is not None
        # Generate attributes
        logger.info(f"Trying rgb generation...")
        self.map = self.world.coordinator_view(investment)
        logger.info(f"Generated!")
        self.forager_url = context["forager_url"]
        self.map_url = self.world.map_path
        self.num_foragers = NUM_FORAGERS
        logger.info("World created successfully!")

    def format_answer(self, raw_answer, **kwargs):
        try:
            assert raw_answer is not None
            assert isinstance(raw_answer, list)
            positions_and_coins ={
                'positions': raw_answer,
                'coins': self.world.coin_positions()
            }
            logger.info(f"Coordinator decided positions: {positions_and_coins['positions']}")
            # logger.info(f"World contains coins in: {positions_and_coins['coins']}")
            return positions_and_coins
        except (ValueError, AssertionError):
            return f"INVALID_RESPONSE"


class CollectingControl(Control):
    macro = "progress"
    external_template = "progress_bars.html"

    def __init__(self, tiles_visited:List[List[Pos]], world_path:str) -> None:
        super().__init__(
            show_next_button=False
        )
        assert(len(tiles_visited) == NUM_FORAGERS)
        self.tiles_visited = [
            [list(tile) for tile in tiles]
            for tiles in tiles_visited
        ]
        self.world_w = WORLD_WIDTH
        self.world_h = WORLD_HEIGHT
        world = World.generate_from_json(Path(world_path))
        self.map = world.grid.tolist()


class InvestmentControl(Control):
    macro = "investment"
    external_template = "investment-control.html"

    def __init__(self, map_path:str) -> None:
        super().__init__(
        )
        with open(map_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.arr = data
        self.W, self.H = len(data), len(data[0])
        self.endowment = COORDINATOR_ENDOWMENT


class TestControl(Control):
    macro = "foraging_area"
    external_template = "foraging-control-test.html"

    def __init__(self) -> None:
        super().__init__(
        )

###########################################

class ForagingControl(Control):
    macro = "foraging_area"
    external_template = "foraging-control.html"

    def __init__(
        self,
        position: Tuple[int, int],
        coins: List[Tuple[int, int]],
        max_gear: int,
        context:Dict[str, Path],
    ) -> None:
        super().__init__(
            # show_next_button=False
        )
        self.pos_x = position[0]
        self.pos_y = position[1]
        logger.info("Entering page for foraging...")
        # Create world from json
        logger.info("Attempting to generate world...")
        world = World.generate_from_coins(coins)
        # logger.info(f"Coins in world: {self.world.coin_positions()}")
        self.map = world.generate_terrain()
        logger.info(f"Generated!")
        self.forager_url = context["forager_url"]
        self.coin_collected_url = context["coin_collected_url"]
        self.map_url = world.map_path
        self.num_foragers = NUM_FORAGERS
        assert(1 <= max_gear <=3), f"Error: max_gear should be between 1 and 3, but got {max_gear}"
        assert(isinstance(max_gear, int)), f"Error: max_gear should be an integer, but got {type(max_gear)}"
        self.max_gear = max_gear - 1 # to convert to index
        self.collection_chances = [COLLECTION_CHANCE(gear) for gear in range(1, 4)]
        self.enabled = ['true' if i < max_gear else 'false' for i in range(3)]
        self.fuel_per_move = FUEL_PER_MOVE
        logger.info("Ready to start foraging...")

    def format_answer(self, raw_answer, **kwargs):
        try:
            # assert raw_answer is not None
            # assert isinstance(raw_answer, list)
            # return raw_answer
            logger.info(f"Coins foraged: {raw_answer}")
            return raw_answer
        except (ValueError, AssertionError):
            return f"INVALID_RESPONSE"


class OtherForagersCollectingControl(Control):
    macro = "other_foragers_progress"
    external_template = "other_foragers_progress_bars.html"

    def __init__(self) -> None:
        super().__init__(
            show_next_button=False
        )
###########################################
