"""Utility functions and data structures for handling chess board states and FEN strings."""

import typing
from dataclasses import dataclass, field

import chess

from atomheart.move import MoveUci

Fen = typing.Annotated[str, "a string representing a fen"]


def _moves_factory() -> list[chess.Move]:
    return []


def _uci_factory() -> list[MoveUci]:
    return []


def _board_states_factory() -> list[chess._BoardState]:  # pyright: ignore[reportPrivateUsage]
    return []  # pyright: ignore[reportPrivateUsage]


@dataclass
class FenPlusMoves:
    """
    FenPlusMoves dataclass to hold a FEN string and subsequent moves.
    """

    original_fen: Fen
    subsequent_moves: list[chess.Move] = field(default_factory=_moves_factory)


@dataclass
class FenPlusMoveHistory:
    """
    FenPlusMoveHistory dataclass to hold a FEN string and subsequent moves in UCI format.
    """

    current_fen: Fen
    historical_moves: list[MoveUci] = field(default_factory=_uci_factory)


@dataclass
class FenPlusHistory:
    """
    FenPlusHistory dataclass to hold a FEN string, subsequent moves in UCI format
    and historical board states."""

    current_fen: Fen
    historical_moves: list[MoveUci] = field(default_factory=_uci_factory)
    historical_boards: list[chess._BoardState] = field(  # pyright: ignore[reportPrivateUsage]
        default_factory=_board_states_factory
    )

    def current_turn(self) -> chess.Color:
        """Returns the color of the player to move."""
        # copy of some code in the chess python library that cannot be easily extracted or called directly
        parts = self.current_fen.split()

        # Board part.
        try:
            _ = parts.pop(0)
        except IndexError:
            raise ValueError("empty fen") from None

        # Turn.
        try:
            turn_part = parts.pop(0)
        except IndexError:
            turn = chess.WHITE
        else:
            if turn_part == "w":
                turn = chess.WHITE
            elif turn_part == "b":
                turn = chess.BLACK
            else:
                raise ValueError(f"expected 'w' or 'b' for turn part of fen: {Fen!r}")
        return turn


def square_rotate(square: chess.Square) -> chess.Square:
    """Rotates the square 180."""
    return square ^ 0x3F


def bitboard_rotate(bitboard: chess.Bitboard) -> chess.Bitboard:
    """Rotates the square 180."""
    return chess.flip_horizontal(bb=chess.flip_vertical(bb=bitboard))
