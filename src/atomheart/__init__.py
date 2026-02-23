"""atomheart: multiple board-game environments and Valanga adapters.

The clean public API is through game-specific modules:
- atomheart.games.checkers
- atomheart.games.chess
"""

from importlib.util import find_spec

from . import games
from .games.checkers import (
    CheckersDynamics,
    CheckersReversibleDynamics,
    CheckersRules,
    CheckersState,
)

__all__ = [
    "CheckersDynamics",
    "CheckersReversibleDynamics",
    "CheckersRules",
    "CheckersState",
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
