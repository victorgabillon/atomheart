"""atomheart: board-game environments and Valanga adapters.

Core lightweight games are always available. Chess support is optional and
becomes available when the chess extra dependencies are installed.
"""

from importlib import import_module

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
from .games.nim import NimDynamics, NimReversibleDynamics, NimState, NimUndo

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
    "NimDynamics",
    "NimReversibleDynamics",
    "NimState",
    "NimUndo",
    "Variant",
    "games",
]

try:
    _chess = import_module("atomheart.games.chess")
except ImportError:
    # Optional chess dependencies are not installed.
    pass
else:
    ChessDynamics = _chess.ChessDynamics
    ChessState = _chess.ChessState
    __all__.extend(["ChessDynamics", "ChessState"])

    if hasattr(_chess, "BoardChi"):
        BoardChi = _chess.BoardChi
        create_board_chi = _chess.create_board_chi
        create_board_chi_from_pychess_board = _chess.create_board_chi_from_pychess_board
        __all__.extend(
            [
                "BoardChi",
                "create_board_chi",
                "create_board_chi_from_pychess_board",
            ]
        )