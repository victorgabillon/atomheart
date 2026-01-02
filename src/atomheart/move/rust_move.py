"""
RustMove class implementation.
"""

import shakmaty_python_binding

from .utils import MoveUci


class RustMove:
    """RustMove class wrapping a Rust-based move representation."""

    move: shakmaty_python_binding.MyMove
    uci_: MoveUci

    def __init__(self, move: shakmaty_python_binding.MyMove, uci: MoveUci) -> None:
        """Initialize a RustMove instance.
        Args:
            move (shakmaty_python_binding.MyMove): The Rust-based move representation.
            uci (MoveUci): The UCI string representation of the move.
        """
        self.move = move
        self.uci_ = uci

    def is_zeroing(self) -> bool:
        """
        Zeroing moves are moves that reset the fifty-move counter.
        Returns:
            bool: True if the move is zeroing, False otherwise.
        """
        return self.move.is_zeroing()

    def uci(self) -> MoveUci:
        """Get the UCI string representation of the move.

        Returns:
            MoveUci: The UCI string representation of the move.
        """
        return self.uci_
