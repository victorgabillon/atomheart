"""Utility functions for converting and manipulating colors between python-chess and valanga."""

import chess
from valanga import Color as ValangaColor


def chess_color_to_valanga(color: chess.Color) -> ValangaColor:
    """Convert python-chess color (bool) to valanga Color."""
    return ValangaColor.WHITE if color == chess.WHITE else ValangaColor.BLACK


def valanga_color_to_chess(color: ValangaColor) -> chess.Color:
    """Convert valanga Color to python-chess color (bool)."""
    return chess.WHITE if color == ValangaColor.WHITE else chess.BLACK
