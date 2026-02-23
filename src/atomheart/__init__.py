"""Top-level package exports for atomheart games."""

from importlib.util import find_spec

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
]

if find_spec("chess") is not None:
    from .board.board_chi import BoardChi
    from .board.valanga_adapter import ChessDynamics, ChessState

    __all__.extend(
        [
            "BoardChi",
            "ChessDynamics",
            "ChessState",
        ]
    )

if find_spec("chess") is not None and find_spec("shakmaty_python_binding") is not None:
    from .board.factory import create_board_chi, create_board_chi_from_pychess_board

    __all__.extend(
        [
            "create_board_chi",
            "create_board_chi_from_pychess_board",
        ]
    )
