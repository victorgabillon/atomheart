"""
init file for chess environment
"""

from .board.board_chi import BoardChi
from .board.factory import create_board_chi

__all__ = ["BoardChi", "create_board_chi"]
