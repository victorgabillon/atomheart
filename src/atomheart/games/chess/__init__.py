"""Chess game implementation for atomheart.

Core chess state/dynamics are exposed here. Board helpers are available when
the optional ``chess`` extra is installed.
"""

from .dynamics import ChessDynamics
from .state import ChessState

__all__ = [
    "ChessDynamics",
    "ChessState",
]

try:
    from .board import (  # noqa: F401
        BoardChi,
        create_board_chi,
        create_board_chi_from_pychess_board,
    )
except ImportError:
    pass
else:
    __all__.extend(
        [
            "BoardChi",
            "create_board_chi",
            "create_board_chi_from_pychess_board",
        ]
    )
