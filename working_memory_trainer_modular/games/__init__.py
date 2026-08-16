from .nback import NBackGame
from .updating import UpdatingGame
from .math_memory import MathMemoryGame
from .dual_memory import DualMemoryGame

GAME_CLASSES = {
    "nback": NBackGame,
    "updating": UpdatingGame,
    "math_memory": MathMemoryGame,
    "dual": DualMemoryGame,
}
