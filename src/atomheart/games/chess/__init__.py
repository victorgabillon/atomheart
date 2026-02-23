"""Chess game implementation for atomheart.

This module provides a complete chess implementation with:
- State representation (ChessState)
- Game dynamics/rules (ChessDynamics)
- Board implementations (python-chess and rust-based)
- Move representations and utilities
"""

from .dynamics import ChessDynamics
from .state import ChessState

__all__ = [
    "ChessDynamics",
    "ChessState",
]

# Conditional exports for board and move when dependencies are available
try:
    from .board import (  # noqa: F401
        BoardChi,
        create_board_chi,
        create_board_chi_from_pychess_board,
    )

    __all__.extend(
        [
            "BoardChi",
            "create_board_chi",
            "create_board_chi_from_pychess_board",
        ]
    )
except ImportError:
    pass
