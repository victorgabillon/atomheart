"""Chess board implementations and utilities."""

from importlib.util import find_spec

from .board_chi import BoardChi
from .board_modification import BoardModification, BoardModificationP
from .factory import (
    BoardFactory,
    create_board,
    create_board_chi,
    create_board_chi_from_pychess_board,
    create_board_factory,
)
from .iboard import BoardKey, IBoard
from .utils import Fen

__all__ = [
    "BoardChi",
    "BoardFactory",
    "BoardKey",
    "BoardModification",
    "BoardModificationP",
    "Fen",
    "IBoard",
    "create_board",
    "create_board_chi",
    "create_board_chi_from_pychess_board",
    "create_board_factory",
]

if find_spec("shakmaty_python_binding") is not None:
    from .rusty_board import RustyBoardChi  # noqa: F401

    __all__.append("RustyBoardChi")
