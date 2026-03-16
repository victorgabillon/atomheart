"""atomheart: multiple board-game environments and Valanga adapters.

The clean public API is through game-specific modules:
- atomheart.games.checkers
- atomheart.games.chess
- atomheart.games.integer_reduction
- atomheart.games.morpion
"""

from importlib.util import find_spec

from . import games
from .games.checkers import (
    CheckersDynamics,
    CheckersReversibleDynamics,
    CheckersRules,
    CheckersState,
)
from .games.integer_reduction import (
    IntegerReductionDynamics,
    IntegerReductionReversibleDynamics,
    IntegerReductionState,
    IntegerReductionUndo,
)
from .games.morpion import MorpionDynamics, MorpionState, Variant

__all__ = [
    "CheckersDynamics",
    "CheckersReversibleDynamics",
    "CheckersRules",
    "CheckersState",
    "IntegerReductionDynamics",
    "IntegerReductionReversibleDynamics",
    "IntegerReductionState",
    "IntegerReductionUndo",
    "MorpionDynamics",
    "MorpionState",
    "Variant",
    "games",
]

if find_spec("chess") is not None:
    from .games.chess import BoardChi, ChessDynamics, ChessState  # noqa: F401

    __all__.extend(
        [
            "BoardChi",
            "ChessDynamics",
            "ChessState",
        ]
    )

if find_spec("chess") is not None:
    from .games.chess import (  # noqa: F401
        create_board_chi,
        create_board_chi_from_pychess_board,
    )

    __all__.extend(
        [
            "create_board_chi",
            "create_board_chi_from_pychess_board",
        ]
    )
