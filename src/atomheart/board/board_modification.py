"""
Module that contains the BoardModification class
"""

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Protocol

import chess


class IteratorNotInitializedError(TypeError):
    def __init__(self) -> None:
        super().__init__("Iterator not initialized. Call iter() first.")


@dataclass(frozen=True)
class PieceInSquare:
    """
    Represents a piece on a chessboard square.
    """

    square: chess.Square
    piece: chess.PieceType
    color: chess.Color


class BoardModificationP(Protocol):
    """
    Represents a modification to a chessboard resulting from a move.
    """

    @property
    def removals(self) -> Iterator[PieceInSquare]:
        """Yields all piece removals from the board modification.

        Yields:
            Iterator[PieceInSquare]: An iterator over the piece removals.
        """
        ...

    @property
    def appearances(self) -> Iterator[PieceInSquare]:
        """Yields all piece appearances from the board modification.

        Returns:
            _type_: _description_

        Yields:
            Iterator[PieceInSquare]: An iterator over the piece appearances.
        """
        ...


def _piece_set() -> set[PieceInSquare]:
    return set()


@dataclass
class BoardModification:
    """
    Represents a modification to a chessboard resulting from a move.
    """

    removals_: set[PieceInSquare] = field(default_factory=_piece_set)
    appearances_: set[PieceInSquare] = field(default_factory=_piece_set)

    def add_appearance(self, appearance: PieceInSquare) -> None:
        """
        Adds a piece appearance to the board modification.

        Args:
            appearance: The PieceInSquare object representing the appearance to add.
        """
        self.appearances_.add(appearance)

    def add_removal(self, removal: PieceInSquare) -> None:
        """
        Adds a piece removal to the board modification.

        Args:
            removal: The PieceInSquare object representing the removal to add.
        """
        self.removals_.add(removal)

    @property
    def removals(self) -> Iterator[PieceInSquare]:
        """Yields all piece removals from the board modification.

        Returns:
            Iterator[PieceInSquare]: An iterator over the piece removals.
        """
        return iter(self.removals_)

    @property
    def appearances(self) -> Iterator[PieceInSquare]:
        """Yields all piece appearances from the board modification.

        Returns:
            Iterator[PieceInSquare]: An iterator over the piece appearances.
        """
        return iter(self.appearances_)


def _rust_item_set() -> set[tuple[int, int, int]]:
    return set()


@dataclass
class PieceRustIterator:
    """Iterator over PieceInSquare objects stored as tuples for Rust compatibility."""

    items_: set[tuple[int, int, int]] = field(default_factory=_rust_item_set)
    _it: Iterator[tuple[int, int, int]] | None = field(
        init=False, default=None, repr=False
    )

    def __iter__(self) -> "PieceRustIterator":
        self._it = iter(self.items_)
        return self

    def __next__(self) -> PieceInSquare:
        if self._it is None:
            raise IteratorNotInitializedError
        square, piece, color = next(self._it)
        return PieceInSquare(square=square, piece=piece, color=bool(color))


def _rust_tuple_set() -> set[tuple[int, int, int]]:
    return set()


@dataclass
class BoardModificationRust:
    """
    Represents a modification to a chessboard resulting from a move.
    """

    removals_: set[tuple[int, int, int]] = field(default_factory=_rust_tuple_set)
    appearances_: set[tuple[int, int, int]] = field(default_factory=_rust_tuple_set)

    @property
    def removals(self) -> Iterator[PieceInSquare]:
        """Yields all piece removals from the board modification.
        Returns:
            Iterator[PieceInSquare]: An iterator over the piece removals.
        """
        return PieceRustIterator(self.removals_)

    @property
    def appearances(self) -> Iterator[PieceInSquare]:
        """Yields all piece appearances from the board modification.

        Returns:
            Iterator[PieceInSquare]: An iterator over the piece appearances.
        """
        return PieceRustIterator(self.appearances_)


def compute_modifications(
    previous_pawns: chess.Bitboard,
    previous_kings: chess.Bitboard,
    previous_queens: chess.Bitboard,
    previous_rooks: chess.Bitboard,
    previous_bishops: chess.Bitboard,
    previous_knights: chess.Bitboard,
    previous_occupied_white: chess.Bitboard,
    previous_occupied_black: chess.Bitboard,
    new_pawns: chess.Bitboard,
    new_kings: chess.Bitboard,
    new_queens: chess.Bitboard,
    new_rooks: chess.Bitboard,
    new_bishops: chess.Bitboard,
    new_knights: chess.Bitboard,
    new_occupied_white: chess.Bitboard,
    new_occupied_black: chess.Bitboard,
) -> BoardModification:  # pylint: disable=all
    """Computes the board modifications between two board states.
    Args:
        previous_pawns (chess.Bitboard): Previous pawns bitboard.
        previous_kings (chess.Bitboard): Previous kings bitboard.
        previous_queens (chess.Bitboard): Previous queens bitboard.
        previous_rooks (chess.Bitboard): Previous rooks bitboard.
        previous_bishops (chess.Bitboard): Previous bishops bitboard.
        previous_knights (chess.Bitboard): Previous knights bitboard.
        previous_occupied_white (chess.Bitboard): Previous occupied white squares bitboard.
        previous_occupied_black (chess.Bitboard): Previous occupied black squares bitboard.
        new_pawns (chess.Bitboard): New pawns bitboard.
        new_kings (chess.Bitboard): New kings bitboard.
        new_queens (chess.Bitboard): New queens bitboard.
        new_rooks (chess.Bitboard): New rooks bitboard.
        new_bishops (chess.Bitboard): New bishops bitboard.
        new_knights (chess.Bitboard): New knights bitboard.
        new_occupied_white (chess.Bitboard): New occupied white squares bitboard.
        new_occupied_black (chess.Bitboard): New occupied black squares bitboard.
    Returns:
        BoardModification: The computed board modifications.
    """
    board_modifications: BoardModification = BoardModification()
    hop = [
        (previous_pawns, new_pawns, chess.PAWN),
        (previous_bishops, new_bishops, chess.BISHOP),
        (previous_rooks, new_rooks, chess.ROOK),
        (previous_knights, new_knights, chess.KNIGHT),
        (previous_queens, new_queens, chess.QUEEN),
        (previous_kings, new_kings, chess.KING),
    ]
    hip = [
        (previous_occupied_white, new_occupied_white, chess.WHITE),
        (previous_occupied_black, new_occupied_black, chess.BLACK),
    ]

    for previous_bitboard_piece, new_bitboard_piece, piece_type in hop:
        for previous_bitboard_color, new_bitboard_color, color in hip:
            removals: chess.Bitboard = (
                previous_bitboard_piece & previous_bitboard_color
            ) & ~(new_bitboard_piece & new_bitboard_color)
            if removals:
                for square in chess.scan_forward(removals):
                    board_modifications.add_removal(
                        PieceInSquare(square=square, piece=piece_type, color=color)
                    )

            appearance: chess.Bitboard = ~(
                previous_bitboard_piece & previous_bitboard_color
            ) & (new_bitboard_piece & new_bitboard_color)

            if appearance:
                for square in chess.scan_forward(appearance):
                    board_modifications.add_appearance(
                        PieceInSquare(square=square, piece=piece_type, color=color)
                    )

    return board_modifications
